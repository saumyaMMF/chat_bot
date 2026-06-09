"""FastAPI entrypoint for the rhize chatbot backend."""

from __future__ import annotations

import asyncio
import logging
import sys
import time as _time

# Windows + Python 3.12 + asyncio ProactorEventLoop + SSL = WinError 87
# crash during MySQL TLS handshake. Force SelectorEventLoop on Windows so
# aiomysql's SSL connect to DigitalOcean managed MySQL actually works.
# No-op on Linux/macOS where the default already works.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.chatbot.chat_service import ChatInput, PrevTurn, run_chat
from app.chatbot.readonly_db import close_pool
from app.chatbot.readonly_db_mysql import close_pool as close_pool_mysql
from app.config import get_settings


async def require_service_token(authorization: str | None = Header(default=None)) -> None:
    """Bearer-token check so only the rhize-intel app can hit /chat.

    No-op when ``CHATBOT_SERVICE_TOKEN`` isn't configured (local dev). In
    production set the env on BOTH sides — see lib/chatbot-client.ts in
    rhize-intel. Constant-time compare prevents timing-side-channel leaks of
    the secret length."""
    import hmac
    expected = get_settings().service_token
    if not expected:
        return
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    provided = authorization.split(" ", 1)[1].strip()
    if not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=403, detail="Invalid token")

_LOG_DIR = __import__("pathlib").Path(__file__).resolve().parents[1] / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FMT = "%(asctime)s %(levelname)s %(name)s %(message)s"
_file_handler = logging.FileHandler(_LOG_DIR / "chatbot.log", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter(_LOG_FMT))
_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(logging.Formatter(_LOG_FMT))
logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _stream_handler], force=True)
# Pipe uvicorn's loggers into the same handlers so HTTP access lines land in
# the file too — uvicorn installs its own handlers in lifespan startup.
for _n in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    _lg = logging.getLogger(_n)
    _lg.handlers = [_file_handler, _stream_handler]
    _lg.propagate = False

MAX_QUESTION_LEN = 1_000


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_pool()
    await close_pool_mysql()


app = FastAPI(title="rhize-chatbot", version="0.1.0", lifespan=lifespan)


class HistoryTurn(BaseModel):
    question: str = Field(..., min_length=1, max_length=MAX_QUESTION_LEN)
    answer: str = ""
    sql: str | None = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=MAX_QUESTION_LEN)
    tenant_id: int = Field(..., ge=0)
    states: list[str] = Field(default_factory=list)
    brand_name: str | None = None
    display_name: str | None = None
    session_id: str | None = None
    # Cap at 10 to bound prompt growth — chat_service trims to last 5 anyway.
    history: list[HistoryTurn] = Field(default_factory=list, max_length=10)

    @field_validator("question")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question is required")
        return v

    @field_validator("states")
    @classmethod
    def _states(cls, v: list[str]) -> list[str]:
        cleaned = [s.strip().upper() for s in v if s and s.strip()]
        return cleaned


class ClarifyOptionOut(BaseModel):
    kind: str
    value: str


class ChatResponse(BaseModel):
    ok: bool
    chat: bool | None = None
    refused: bool | None = None
    clarify: bool | None = None
    message: str | None = None
    error: str | None = None
    sql: str | None = None
    row_count: int | None = None
    rows: list[dict[str, Any]] | None = None
    options: list[ClarifyOptionOut] | None = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/warmup", dependencies=[Depends(require_service_token)])
async def warmup() -> dict[str, Any]:
    """Pre-load the LLM, embed model, and snapshots so the first user-facing
    request does NOT pay cold-load tax (~17s + first-token latency).

    Triggered by the Next.js login route via ``after()`` — runs in the
    background, response not blocked. Idempotent + cheap if already warm.

    Steps:
      1. embed_text("warmup") -> loads nomic-embed-text into Ollama + warms
         our TTLCache. Forces fast_path/schema/example snapshots to load
         since each calls _maybe_refresh() on first knn().
      2. LLM ping with min tokens -> loads qwen2.5-coder model into Ollama.
         keep_alive in our payload already keeps it resident across calls;
         this just primes it.
    """
    import asyncio as _aio
    from app.chatbot.embed_client import embed_text
    from app.chatbot.fast_path_store import _SNAPSHOT as _FP_SNAP
    from app.chatbot.example_store import _SNAPSHOT as _EX_SNAP
    from app.chatbot.schema_store import _SNAPSHOT as _SC_SNAP
    from app.chatbot.llm_client import chat_complete, ChatMessage

    t0 = _time.perf_counter()
    errors: list[str] = []

    async def _warm_embed_and_snaps() -> None:
        try:
            vec = await embed_text("warmup")
            # Force snapshot loads by issuing a 1-NN query against each.
            await _aio.gather(
                _FP_SNAP.knn(vec, k=1),
                _EX_SNAP.knn(vec, k=1),
                _SC_SNAP.knn(vec, k=1),
                return_exceptions=True,
            )
        except Exception as exc:
            errors.append(f"embed/snapshot: {exc}")

    async def _warm_llm() -> None:
        try:
            await chat_complete(
                [ChatMessage(role="user", content="ok")],
                max_tokens=1,
                temperature=0.0,
            )
        except Exception as exc:
            errors.append(f"llm: {exc}")

    await _aio.gather(_warm_embed_and_snaps(), _warm_llm())
    elapsed_ms = int((_time.perf_counter() - t0) * 1000)
    return {
        "ok": not errors,
        "elapsed_ms": elapsed_ms,
        "fast_path_rows": _FP_SNAP.size(),
        "example_rows": _EX_SNAP.size(),
        "schema_rows": _SC_SNAP.size(),
        "errors": errors,
    }


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_service_token)])
async def chat(req: ChatRequest) -> ChatResponse:
    try:
        result = await run_chat(
            ChatInput(
                tenant_id=req.tenant_id,
                states=req.states,
                question=req.question,
                brand_name=req.brand_name,
                display_name=req.display_name,
                session_id=req.session_id,
                history=[
                    PrevTurn(question=h.question, answer=h.answer, sql=h.sql)
                    for h in req.history
                ],
            )
        )
    except Exception as exc:
        logging.exception("[chat] unexpected error")
        raise HTTPException(status_code=500, detail="Internal error") from exc

    if result.kind == "result":
        return ChatResponse(
            ok=True,
            sql=result.sql,
            row_count=result.row_count,
            rows=result.rows,
        )
    if result.kind == "chat":
        return ChatResponse(ok=True, chat=True, message=result.message)
    if result.kind == "refusal":
        return ChatResponse(ok=False, refused=True, message=result.message)
    if result.kind == "clarify":
        return ChatResponse(
            ok=True,
            clarify=True,
            message=result.message,
            options=[ClarifyOptionOut(kind=o.kind, value=o.value) for o in result.options],
        )

    # error
    logging.error("[chat] generation/execution failed: %s | %s", result.message, result.sql or "")
    friendly = (
        result.message
        if result.message and "temporarily unavailable" in result.message.lower()
        else "Sorry, I couldn't work that one out. Try asking about brands, prices, categories, or market trends."
    )
    return ChatResponse(ok=False, error=friendly)


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=False,
    )
