"""FastAPI entrypoint for the rhize chatbot backend."""

from __future__ import annotations

import asyncio
import logging
import re
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

from collections import deque
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.chatbot.chat_service import ChatInput, PrevTurn, run_chat
from app.chatbot.readonly_db import close_pool
from app.chatbot.readonly_db_mysql import close_pool as close_pool_mysql
from app.config import get_settings


# Optional HMAC body-sig auth (rolling out via CHATBOT_HMAC_REQUIRED). Two
# headers: X-Chat-Timestamp (unix-seconds) + X-Chat-Signature (hex sha256
# HMAC over `<ts>.<raw_body>` using CHATBOT_SERVICE_TOKEN). Verified before
# bearer so a forged bearer alone is not enough once enforcement turns on.
# Reuses the existing service_token as the shared secret (no new env var
# while rolling out). Skew window = 5 minutes.
HMAC_SKEW_SECONDS = 300


async def require_hmac(request: Request) -> None:
    """If the client sent HMAC headers, validate them. Optional unless
    CHATBOT_HMAC_REQUIRED=1 (env). Constant-time compare on the digest."""
    import hashlib
    import hmac as _hmac
    import os

    sig = request.headers.get("x-chat-signature")
    ts = request.headers.get("x-chat-timestamp")
    required = os.environ.get("CHATBOT_HMAC_REQUIRED", "").strip() == "1"

    if not sig or not ts:
        if required:
            raise HTTPException(status_code=401, detail="HMAC headers required")
        return

    secret = get_settings().service_token
    if not secret:
        # No secret configured — can't validate. Refuse rather than skip.
        raise HTTPException(status_code=500, detail="Server HMAC secret unconfigured")

    try:
        ts_i = int(ts)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid X-Chat-Timestamp") from exc

    import time as _t
    now = int(_t.time())
    if abs(now - ts_i) > HMAC_SKEW_SECONDS:
        raise HTTPException(status_code=401, detail="Timestamp skew exceeds window")

    body = await request.body()  # cached by starlette; subsequent Body() reads reuse it
    msg = f"{ts}.".encode("utf-8") + body
    expected = _hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    if not _hmac.compare_digest(sig.lower(), expected):
        raise HTTPException(status_code=403, detail="HMAC signature mismatch")


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
class _ShortName(logging.Filter):
    """Trim noisy module paths so log lines fit on a screen."""
    def filter(self, record: logging.LogRecord) -> bool:
        n = record.name
        if n.startswith("app.chatbot."):
            record.name = n.rsplit(".", 1)[-1]
        elif n == "app.chatbot":
            record.name = "chatbot"
        elif n.startswith("uvicorn"):
            record.name = n.replace("uvicorn.", "uv.").replace("uvicorn", "uv")
        return True

_LOG_FMT = "%(asctime)s %(levelname).1s %(name)-12s | %(message)s"
_DATE_FMT = "%H:%M:%S"
_file_handler = logging.FileHandler(_LOG_DIR / "chatbot.log", encoding="utf-8")
_file_handler.setFormatter(logging.Formatter(_LOG_FMT, datefmt=_DATE_FMT))
_file_handler.addFilter(_ShortName())
_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(logging.Formatter(_LOG_FMT, datefmt=_DATE_FMT))
_stream_handler.addFilter(_ShortName())
logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _stream_handler], force=True)
# httpx logs every embed/LLM call — drowns the real signal. Bump to WARNING.
for _quiet in ("httpx", "httpcore", "watchfiles"):
    logging.getLogger(_quiet).setLevel(logging.WARNING)
# Pipe uvicorn's loggers into the same handlers so HTTP access lines land in
# the file too — uvicorn installs its own handlers in lifespan startup.
for _n in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    _lg = logging.getLogger(_n)
    _lg.handlers = [_file_handler, _stream_handler]
    _lg.propagate = False

MAX_QUESTION_LEN = 1_000
MAX_IDENTITY_LEN = 80
MAX_HISTORY_ANSWER_LEN = 4_000

# Prompt-injection heuristic: catches "X:\nSYSTEM OVERRIDE", "X\n\nIGNORE PRIOR",
# Markdown section breaks, or "X: KIND value" patterns the model might treat as
# a new directive. Applied to identity strings AND history fields.
_INJECTION_RX = re.compile(
    r"[\r\n]"                                     # any newline = inject break
    r"|[\x00-\x08\x0b-\x1f]"                     # control chars
    r"|:\s*[A-Z][A-Z0-9_ ]{2,}\b"                # ": SYSTEM OVERRIDE" pattern
    r"|\b(ignore|disregard|override|forget)\b\s+(prior|previous|above|all)"
    r"|^[\s\-=*_#]{3,}",                          # markdown section break
    re.IGNORECASE,
)


def _sanitize_identity(value: str | None, *, field: str) -> str | None:
    """Strip newlines, cap length, reject if structure suggests prompt injection.

    Identity strings (brand_name, display_name) land inside SECTION 2 of the
    system prompt verbatim. A `\\n\\nSYSTEM: ...` string would be interpreted
    by the LLM as a new directive. We reject those rather than escape, because
    a legitimate brand name doesn't contain newlines or "ignore prior" text.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    v = value.strip()
    if not v:
        return None
    if len(v) > MAX_IDENTITY_LEN:
        raise ValueError(f"{field} exceeds {MAX_IDENTITY_LEN} chars")
    if _INJECTION_RX.search(v):
        raise ValueError(f"{field} contains disallowed control or directive pattern")
    return v


def _sanitize_history_text(value: str, *, field: str, max_len: int) -> str:
    """Same idea, applied to history.question / history.answer / history.sql.
    history.sql is also passed through this so a malicious client can't sneak
    a fake assistant turn carrying directives in the SQL slot."""
    if not isinstance(value, str):
        return ""
    v = value.replace("\r", "").strip()
    if len(v) > max_len:
        v = v[:max_len]
    if _INJECTION_RX.search(v):
        # Don't reject — just neutralize. Stripping newlines defangs the
        # multi-line directive pattern. Strip any " IGNORE PRIOR " phrase.
        v = re.sub(r"[\r\n]+", " ", v)
        v = _INJECTION_RX.sub(" ", v)
    return v


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Self-warmup on boot: same work as POST /warmup (embed model, snapshot
    # loads, LLM prime) but without waiting for a login to trigger it. Runs
    # as a background task so the server accepts requests immediately;
    # first question after a restart no longer pays the ~22s cold tax.
    warm_task = asyncio.create_task(_boot_warmup())
    yield
    warm_task.cancel()
    await close_pool()
    await close_pool_mysql()


async def _boot_warmup() -> None:
    try:
        result = await warmup()
        logging.getLogger("warmup").info(
            "[warmup] boot warmup done: %s", result)
    except Exception as exc:  # never crash boot over a warmup failure
        logging.getLogger("warmup").warning("[warmup] boot warmup failed: %s", exc)


# In-house sliding-window rate limiter — no deps, single-process. Keyed by
# (X-Forwarded-For first hop OR direct client IP). Behind a reverse proxy
# Cloudflare/Nginx MUST forward XFF. /chat is the only expensive endpoint
# (Ollama 40-90s CPU per call) so we cap it at 10 req/min/IP. For multi-worker
# deployments swap this for Redis-backed; single-worker is fine here.
_RATE_LIMIT_WINDOW_S = 60.0
_RATE_LIMIT_MAX = 10
_rate_buckets: dict[str, deque[float]] = {}


def _client_ip(req: Request) -> str:
    xff = req.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",", 1)[0].strip()
    return req.client.host if req.client else "unknown"


def rate_limit(req: Request) -> None:
    """Reject if this client exceeded `_RATE_LIMIT_MAX` /chat calls in the
    last `_RATE_LIMIT_WINDOW_S` seconds."""
    ip = _client_ip(req)
    now = _time.monotonic()
    bucket = _rate_buckets.setdefault(ip, deque())
    cutoff = now - _RATE_LIMIT_WINDOW_S
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= _RATE_LIMIT_MAX:
        retry_after = int(_RATE_LIMIT_WINDOW_S - (now - bucket[0])) + 1
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({_RATE_LIMIT_MAX}/{int(_RATE_LIMIT_WINDOW_S)}s). Retry in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )
    bucket.append(now)


app = FastAPI(title="rhize-chatbot", version="0.1.0", lifespan=lifespan)


class HistoryTurn(BaseModel):
    question: str = Field(..., min_length=1, max_length=MAX_QUESTION_LEN)
    answer: str = Field(default="", max_length=MAX_HISTORY_ANSWER_LEN)
    sql: str | None = Field(default=None, max_length=MAX_HISTORY_ANSWER_LEN)

    @field_validator("question")
    @classmethod
    def _q(cls, v: str) -> str:
        return _sanitize_history_text(v, field="history.question", max_len=MAX_QUESTION_LEN)

    @field_validator("answer")
    @classmethod
    def _a(cls, v: str) -> str:
        return _sanitize_history_text(v, field="history.answer", max_len=MAX_HISTORY_ANSWER_LEN)

    @field_validator("sql")
    @classmethod
    def _s(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return _sanitize_history_text(v, field="history.sql", max_len=MAX_HISTORY_ANSWER_LEN)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=MAX_QUESTION_LEN)
    tenant_id: int = Field(..., ge=0)
    states: list[str] = Field(default_factory=list)
    brand_name: str | None = Field(default=None, max_length=MAX_IDENTITY_LEN)
    display_name: str | None = Field(default=None, max_length=MAX_IDENTITY_LEN)
    session_id: str | None = Field(default=None, max_length=128)
    # Cap at 10 to bound prompt growth — chat_service trims to last 5 anyway.
    history: list[HistoryTurn] = Field(default_factory=list, max_length=10)

    @field_validator("question")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question is required")
        # Question goes into the LAST user-role slot — not the system prompt —
        # so it's lower-risk than identity strings. Just neutralize newlines.
        return _sanitize_history_text(v, field="question", max_len=MAX_QUESTION_LEN)

    @field_validator("states")
    @classmethod
    def _states(cls, v: list[str]) -> list[str]:
        cleaned: list[str] = []
        for s in v:
            if not s or not isinstance(s, str):
                continue
            s2 = s.strip().upper()
            # US state codes are 2 alpha chars. Reject anything else — prevents
            # `app.states` from carrying smuggled tokens to set_config().
            if re.fullmatch(r"[A-Z]{2}", s2):
                cleaned.append(s2)
        return cleaned

    @field_validator("brand_name")
    @classmethod
    def _brand(cls, v: str | None) -> str | None:
        return _sanitize_identity(v, field="brand_name")

    @field_validator("display_name")
    @classmethod
    def _display(cls, v: str | None) -> str | None:
        return _sanitize_identity(v, field="display_name")

    @field_validator("session_id")
    @classmethod
    def _sid(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v2 = v.strip()
        if not v2:
            return None
        # Session id ends up in turn-log only; still constrain to safe chars.
        if not re.fullmatch(r"[A-Za-z0-9_\-:.]{1,128}", v2):
            raise ValueError("session_id contains disallowed characters")
        return v2


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


@app.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[
        Depends(require_hmac),
        Depends(require_service_token),
        Depends(rate_limit),
    ],
)
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
        # Ship the executed SQL even for terminal chat answers: the client
        # stores it in history, and the pronoun-anchor fast-path needs it to
        # bind "of them" follow-ups to THIS turn instead of an older one.
        return ChatResponse(ok=True, chat=True, message=result.message,
                            sql=result.sql_executed or result.sql)
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
