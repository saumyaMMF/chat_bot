"""Embedding client for schema-RAG and example retrieval.

OpenAI-compatible /embeddings endpoint. Default = Ollama nomic-embed-text
(768-dim).

PERFORMANCE NOTES:
- ``embed_text`` is the single-string hot path used inside the chat request.
  It sets ``keep_alive`` so the embedding model stays resident across calls —
  otherwise Ollama unloads after 5 minutes and the next request pays a 4s
  cold-load tax on top of inference.
- ``embed_batch`` is used by offline ingest scripts. Ollama / OpenAI both
  accept an array for ``input`` and process them in one forward pass. For 50
  examples this is ~25× faster than a per-example loop.
"""

from __future__ import annotations

from typing import Iterable

import httpx

from app.config import get_settings


class EmbedError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    settings = get_settings()
    # Prefer embed-specific key (lets you keep embeds on Ollama while LLM
    # is on a hosted provider). Fall back to LLM key.
    key = settings.embed_api_key or settings.llm_api_key
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }


def _embed_url() -> str:
    settings = get_settings()
    base = settings.embed_base_url or settings.llm_base_url
    return f"{base.rstrip('/')}/embeddings"


def _is_ollama_embed() -> bool:
    """Ollama accepts (and benefits from) `keep_alive`. Hosted OpenAI-compat
    providers reject unknown fields with 400. Detect by base URL."""
    settings = get_settings()
    url = (settings.embed_base_url or settings.llm_base_url).lower()
    return "11434" in url or "localhost" in url or "127.0.0.1" in url or "ollama" in url


# Module-level TTL LRU for embed_text. nomic-embed-text is deterministic per
# (model, input), so caching is sound until model changes. Default 1024 entries
# × 768 floats ≈ 6 MB resident — negligible.
from app.chatbot._perf_cache import TTLCache  # noqa: E402

_EMBED_CACHE: TTLCache[list[float]] = TTLCache(maxsize=2048, ttl_secs=900.0)


def _embed_cache_key(text: str) -> str:
    settings = get_settings()
    # Key on (model, text) so model swaps don't return stale vectors.
    return f"{settings.embed_model}::{text}"


async def _embed_text_uncached(text: str) -> list[float]:
    settings = get_settings()
    timeout_s = settings.embed_timeout_ms / 1000.0
    payload: dict = {
        "model": settings.embed_model,
        "input": text,
    }
    # keep_alive is Ollama-specific. OpenAI / Gemini / Groq reject it with 400.
    if _is_ollama_embed():
        payload["keep_alive"] = settings.embed_keep_alive
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            res = await client.post(_embed_url(), json=payload, headers=_headers())
    except httpx.TimeoutException as exc:
        raise EmbedError(f"embed timed out after {settings.embed_timeout_ms}ms") from exc
    if res.status_code >= 400:
        raise EmbedError(f"embed failed ({res.status_code}): {res.text[:200]}")
    data = res.json()
    try:
        vec = data["data"][0]["embedding"]
    except (KeyError, IndexError, TypeError) as exc:
        raise EmbedError("embed response missing embedding array") from exc
    if not isinstance(vec, list) or not vec:
        raise EmbedError("embed response missing embedding array")
    return [float(x) for x in vec]


async def embed_text(text: str) -> list[float]:
    """Embed a single string. Returns the raw vector.

    Cached by ``(model, text)`` for ``TTLCache.ttl_secs`` (15 min). Hot path
    inside chat — repeated/duplicate questions skip the HTTP round-trip to
    Ollama (~500 ms on CPU). The cache is in-process; multi-worker deploys
    pay per-worker fill cost but never share stale.

    ``keep_alive`` still matters on the cold path: without it the model
    unloads every 5 min and the next miss pays a ~4s cold-load tax.
    """
    return await _EMBED_CACHE.get_or_set(_embed_cache_key(text),
                                         lambda: _embed_text_uncached(text))


def embed_cache_stats() -> dict[str, int]:
    return _EMBED_CACHE.stats()


async def embed_batch(texts: Iterable[str], *, timeout_s: float = 120.0) -> list[list[float]]:
    """Embed a batch in a single HTTP round-trip.

    Used by offline ingest scripts (schema embeddings, example embeddings).
    Falls back to the single-text endpoint per-item if the provider rejects
    array input — defensive against weird hosted-provider quirks.
    """
    items = list(texts)
    if not items:
        return []

    settings = get_settings()
    payload: dict = {
        "model": settings.embed_model,
        "input": items,
    }
    if _is_ollama_embed():
        payload["keep_alive"] = settings.embed_keep_alive

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        res = await client.post(_embed_url(), json=payload, headers=_headers())

    if res.status_code >= 400:
        raise EmbedError(f"embed batch failed ({res.status_code}): {res.text[:200]}")

    data = res.json()
    try:
        rows = data["data"]
    except (KeyError, TypeError) as exc:
        raise EmbedError("embed batch response missing data array") from exc
    if not isinstance(rows, list) or len(rows) != len(items):
        raise EmbedError(
            f"embed batch returned {len(rows) if isinstance(rows, list) else '?'} "
            f"vectors for {len(items)} inputs"
        )
    out: list[list[float]] = []
    for r in rows:
        emb = r.get("embedding") if isinstance(r, dict) else None
        if not isinstance(emb, list) or not emb:
            raise EmbedError("embed batch row missing embedding")
        out.append([float(x) for x in emb])
    return out


def to_pgvector_literal(vec: list[float]) -> str:
    """pgvector accepts a text literal of the form `[0.1,0.2,...]`."""
    return "[" + ",".join(repr(float(x)) for x in vec) + "]"
