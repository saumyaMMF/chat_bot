"""FastAPI entrypoint for the rhize chatbot backend."""

from __future__ import annotations

import asyncio
import logging
import sys

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

from app.chatbot.chat_service import ChatInput, run_chat
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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

MAX_QUESTION_LEN = 1_000


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_pool()
    await close_pool_mysql()


app = FastAPI(title="rhize-chatbot", version="0.1.0", lifespan=lifespan)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=MAX_QUESTION_LEN)
    tenant_id: int = Field(..., ge=0)
    states: list[str] = Field(default_factory=list)
    brand_name: str | None = None
    display_name: str | None = None

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
