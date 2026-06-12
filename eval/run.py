"""Eval harness — mirror of rhize-intel/chatbot/eval/run.ts.

Drives every case in cases.json through run_chat and scores three layered
gates:

  1. kind match           — did the bot classify correctly?
  2. message_match regex  — does the reply text contain expected substrings?
  3. sql_match regex      — does the generated SQL hit the right table/clause?

For SQL cases that produce a query, the runner executes the SQL via the same
chatbot_ro role + RLS path the API uses. DML phrasings ("delete X") are
scored at the classification gate only — the runner never executes them.

Pre-warms both LLM and embed model so the first case doesn't pay a 4s cold
load tax that distorts p50.

USAGE:
    python -m eval.run                  # local Ollama
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

# Load env BEFORE pulling in settings cache.
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

from app.chatbot import prompt_builder  # noqa: E402 (LAST_BUILD_INFO breadcrumbs)
from app.chatbot.chat_service import ChatInput, run_chat  # noqa: E402
from app.config import get_settings  # noqa: E402

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("eval")


async def warm_models() -> None:
    """Pre-load both models so the first eval case doesn't include cold-start
    latency. Uses Ollama's native /api/* endpoints because the OpenAI-compat
    shim ignores keep_alive in the body — confirmed via ``ollama ps`` after
    each warmup."""
    settings = get_settings()
    base = settings.llm_base_url.rstrip("/").removesuffix("/v1")
    print("warming models... ", end="", flush=True)
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            await asyncio.gather(
                client.post(
                    f"{base}/api/chat",
                    json={
                        "model": settings.llm_model,
                        "messages": [{"role": "user", "content": "hi"}],
                        "stream": False,
                        "keep_alive": settings.llm_keep_alive,
                        "options": {
                            "num_ctx": settings.llm_num_ctx,
                            "num_predict": 1,
                        },
                    },
                ),
                client.post(
                    f"{base}/api/embeddings",
                    json={
                        "model": settings.embed_model,
                        "prompt": "warmup",
                        "keep_alive": settings.embed_keep_alive,
                    },
                ),
            )
        print("ok")
    except Exception as exc:
        print(f"warning ({exc}) — continuing anyway")


async def run_one(case: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        result = await run_chat(
            ChatInput(
                tenant_id=cfg["tenant_id"],
                states=cfg["states"],
                question=case["question"],
                brand_name=cfg.get("brand_name"),
                display_name=cfg.get("display_name"),
            )
        )
        dt_ms = int((time.perf_counter() - t0) * 1000)
    except Exception as exc:  # surface as fail, don't crash the loop
        return {
            "id": case["id"],
            "tag": case["tag"],
            "pass": False,
            "reason": f"threw: {exc}",
            "dt_ms": int((time.perf_counter() - t0) * 1000),
            "kind": None,
            "build_info": dict(prompt_builder.LAST_BUILD_INFO),
        }

    info_snapshot = dict(prompt_builder.LAST_BUILD_INFO)

    # Gate 1 — kind. expected_kind accepts pipe alternatives ("result|chat")
    # because terminal single-value answers intentionally come back as chat
    # with sql_executed set — both kinds can be correct for SQL cases.
    if result.kind not in str(case["expected_kind"]).split("|"):
        return {
            "id": case["id"],
            "tag": case["tag"],
            "pass": False,
            "reason": f"kind mismatch: expected {case['expected_kind']}, got {result.kind}",
            "dt_ms": dt_ms,
            "kind": result.kind,
            "message": result.message[:200],
            "sql": (result.sql or getattr(result, "sql_executed", None) or "")[:300],
            "build_info": info_snapshot,
        }

    # Gate 2 — message regex (chat / refusal / error)
    if case.get("message_match"):
        rx = re.compile(case["message_match"], re.I)
        target = result.message
        if not rx.search(target or ""):
            return {
                "id": case["id"],
                "tag": case["tag"],
                "pass": False,
                "reason": f"message did not match {case['message_match']!r}",
                "dt_ms": dt_ms,
                "kind": result.kind,
                "message": (target or "")[:200],
                "sql": (result.sql or getattr(result, "sql_executed", None) or "")[:300],
                "build_info": info_snapshot,
            }

    # Gate 3 — SQL shape regex. Terminal chat answers carry their SQL in
    # sql_executed — check whichever is present so chat-kind passes are
    # still shape-validated.
    if case.get("sql_match") and result.kind in ("result", "chat"):
        rx = re.compile(case["sql_match"])
        _sql = result.sql or getattr(result, "sql_executed", None) or ""
        if not rx.search(_sql):
            return {
                "id": case["id"],
                "tag": case["tag"],
                "pass": False,
                "reason": f"sql shape did not match {case['sql_match']!r}",
                "dt_ms": dt_ms,
                "kind": result.kind,
                "sql": (result.sql or getattr(result, "sql_executed", None) or "")[:300],
                "build_info": info_snapshot,
            }

    return {
        "id": case["id"],
        "tag": case["tag"],
        "pass": True,
        "reason": "ok",
        "dt_ms": dt_ms,
        "kind": result.kind,
        "sql": (result.sql or getattr(result, "sql_executed", None) or "")[:500],
        "message": (result.message or "")[:300],
        "build_info": info_snapshot,
    }


async def main() -> int:
    cases_path = Path(__file__).resolve().parent / "cases.json"
    raw = json.loads(cases_path.read_text(encoding="utf-8"))

    cfg = {
        "tenant_id": raw["tenant_id"],
        "states": raw["states"],
        "brand_name": raw.get("brand_name"),
        "display_name": raw.get("display_name"),
    }
    cases = raw["cases"]

    settings = get_settings()
    print()
    print("=== chatbot eval ===")
    print(f"model:          {settings.llm_model}")
    print(f"num_ctx:        {settings.llm_num_ctx}")
    print(f"num_predict:    {settings.llm_num_predict}")
    print(f"seed:           {settings.llm_seed}")
    print(f"top_k examples: {settings.top_k}")
    print(f"distance thr:   {settings.embed_distance_threshold}")
    print(f"tenant/states:  {cfg['tenant_id']} / {cfg['states']}")
    print(f"cases:          {len(cases)}")
    print()

    await warm_models()

    verdicts: list[dict[str, Any]] = []
    for c in cases:
        print(f"  {c['id']:<34} ", end="", flush=True)
        v = await run_one(c, cfg)
        verdicts.append(v)
        marker = "PASS" if v["pass"] else "FAIL"
        print(f"{marker}  {v['dt_ms']}ms  {v['reason'] if not v['pass'] else ''}")
        # Always surface SQL + message so the user can eyeball what the bot
        # actually generated, not just pass/fail.
        if v.get("sql"):
            print(f"        sql: {v['sql']!r}")
        if v.get("message"):
            print(f"        msg: {v['message']!r}")
        if not v["pass"]:
            bi = v.get("build_info", {})
            if not bi.get("example_retrieval_ok"):
                print(f"        ! example retrieval FELL BACK: {bi.get('example_retrieval_reason')}")
            if not bi.get("schema_retrieval_ok"):
                print(f"        ! schema retrieval FELL BACK: {bi.get('schema_retrieval_reason')}")

    # ── Summary ────────────────────────────────────────────────────────────────
    passes = sum(1 for v in verdicts if v["pass"])
    fails = len(verdicts) - passes
    latencies = sorted(v["dt_ms"] for v in verdicts)
    by_tag: Counter[str] = Counter()
    tag_total: Counter[str] = Counter()
    for v in verdicts:
        tag_total[v["tag"]] += 1
        if v["pass"]:
            by_tag[v["tag"]] += 1

    # Only count fallback for cases that actually invoked the LLM (kind not from
    # a fast-path). Greeting/identity short-circuit before build_messages runs.
    llm_verdicts = [v for v in verdicts if v["tag"] not in ("greeting", "identity")]
    schema_fb = sum(1 for v in llm_verdicts if not v["build_info"].get("schema_retrieval_ok"))
    example_fb = sum(1 for v in llm_verdicts if not v["build_info"].get("example_retrieval_ok"))

    def pct(i: int) -> int:
        if not latencies:
            return 0
        return latencies[min(i, len(latencies) - 1)]

    print()
    print("=== summary ===")
    print(f"pass: {passes}/{len(verdicts)}   fail: {fails}")
    print(f"p50: {pct(len(latencies) // 2)}ms   p95: {pct(int(len(latencies) * 0.95))}ms   max: {pct(-1)}ms")
    print(f"schema retrieval fallback rate:  {schema_fb}/{len(llm_verdicts)} (LLM-only)")
    print(f"example retrieval fallback rate: {example_fb}/{len(llm_verdicts)} (LLM-only)")
    print()
    print("by tag:")
    for tag in sorted(tag_total):
        marker = "OK" if by_tag[tag] == tag_total[tag] else "FAIL"
        print(f"  [{marker}]  {tag:<24} {by_tag[tag]}/{tag_total[tag]}")

    # Persist baseline for diffing across runs.
    out = Path(__file__).resolve().parent / "baseline.json"
    out.write_text(
        json.dumps({"verdicts": verdicts, "summary": {
            "pass": passes, "fail": fails,
            "p50": pct(len(latencies) // 2),
            "p95": pct(int(len(latencies) * 0.95)),
            "schema_fallback": schema_fb,
            "example_fallback": example_fb,
        }}, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"\nbaseline written to {out}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
