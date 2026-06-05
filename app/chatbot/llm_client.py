"""LLM client.

Provider-agnostic OpenAI-compatible Chat Completions API. Works with local
Ollama (http://localhost:11434/v1) and any hosted OpenAI-compatible provider.
Switch with env vars only.

OLLAMA NOTE: Ollama's OpenAI-compat shim accepts an `options` object alongside
the standard `messages` / `temperature` keys, and forwards every field inside
it to the native llama.cpp runner. Without `options.num_ctx`, Ollama silently
truncates prompts > 2048 tokens. We MUST set it or the 7K-token system prompt
gets clipped and the model emits 1-3 char garbage. Hosted providers ignore
unknown keys, so this is safe to ship to OpenAI / Groq / DeepSeek too.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import httpx

from app.config import get_settings

Role = Literal["system", "user", "assistant"]


@dataclass
class ChatMessage:
    role: Role
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class LLMError(RuntimeError):
    pass


@dataclass
class ChatUsage:
    """Token-usage snapshot returned alongside text. Optional — providers may
    not report it. Eval harness uses this for per-turn cost / saturation."""
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    finish_reason: str | None = None


@dataclass
class ChatResponse:
    content: str
    usage: ChatUsage


async def chat_complete_full(
    messages: list[ChatMessage],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> ChatResponse:
    """Send messages and return both content + usage stats.

    Deterministic by default (temperature 0 + fixed seed) — eval reproducibility
    requires this. Tuning knobs live in app.config so they can move via env.
    """
    settings = get_settings()
    base_url = settings.llm_base_url.rstrip("/")
    timeout_s = settings.llm_timeout_ms / 1000.0

    payload = {
        "model": settings.llm_model,
        "messages": [m.to_dict() for m in messages],
        "temperature": temperature if temperature is not None else 0.0,
        "max_tokens": max_tokens if max_tokens is not None else settings.llm_num_predict,
        "stream": False,
        # Ollama-specific — hosted providers ignore. See module docstring.
        "keep_alive": settings.llm_keep_alive,
        "options": {
            "num_ctx": settings.llm_num_ctx,
            "num_predict": max_tokens if max_tokens is not None else settings.llm_num_predict,
            "temperature": temperature if temperature is not None else 0.0,
            "top_p": settings.llm_top_p,
            "repeat_penalty": settings.llm_repeat_penalty,
            "seed": settings.llm_seed,
            # Ollama prefix cache — keep the first N tokens (the system prompt)
            # cached across requests. Skips re-prompt-eval on every turn.
            "num_keep": settings.llm_num_keep,
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.llm_api_key}",
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            res = await client.post(
                f"{base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
    except httpx.TimeoutException as exc:
        raise LLMError(f"LLM request timed out after {settings.llm_timeout_ms}ms") from exc

    if res.status_code >= 400:
        body = res.text[:300]
        raise LLMError(f"LLM request failed ({res.status_code}): {body}")

    data = res.json()
    try:
        choice = data["choices"][0]
        content = choice["message"]["content"]
        finish = choice.get("finish_reason")
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError("LLM response had no message content") from exc

    if not isinstance(content, str):
        raise LLMError("LLM response had no message content")

    usage_obj = data.get("usage") or {}
    usage = ChatUsage(
        prompt_tokens=usage_obj.get("prompt_tokens"),
        completion_tokens=usage_obj.get("completion_tokens"),
        total_tokens=usage_obj.get("total_tokens"),
        finish_reason=finish,
    )
    return ChatResponse(content=content, usage=usage)


async def chat_complete(
    messages: list[ChatMessage],
    *,
    temperature: float = 0.0,
    max_tokens: int = 512,
) -> str:
    """Backwards-compat wrapper. Returns just the text content.

    New code should call ``chat_complete_full`` to capture token usage and
    finish-reason for eval / cost telemetry.
    """
    res = await chat_complete_full(
        messages, temperature=temperature, max_tokens=max_tokens
    )
    return res.content
