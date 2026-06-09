"""Per-turn JSONL logger for the chatbot.

One line per /chat call, appended to ``logs/chatbot-turns-<YYYY-MM-DD>.jsonl``.
Cheap append-only journal — drives offline analysis, regression triage, and
the kind/fast-path mix dashboard.

Failure mode: a logger error must NEVER break the chat path. Any I/O exception
is swallowed and printed to stderr. The directory is gitignored.

Shape mirrors the TS turnLogger so the existing scripts/chatbot-log-summary
script keeps working when fed Python-side logs.
"""

from __future__ import annotations

import datetime as _dt
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


log = logging.getLogger(__name__)

# Project root (chat_bot/) — `logs/` lives next to `app/` so the .gitignore
# entry catches it.
_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"


@dataclass
class TurnRecord:
    ts: str
    tenant_id: int
    question_raw: str
    question_norm: str | None
    fast_path: str  # 'greeting' | 'identity' | 'disambig' | 'none'
    kind: str  # 'result' | 'chat' | 'refusal' | 'clarify' | 'error'
    latency_ms: int
    session_id: str | None = None
    engine: str | None = None
    sql_llm: str | None = None
    sql_final: str | None = None
    row_count: int | None = None
    attempts: int | None = None
    guard_reason: str | None = None
    clarify_option_count: int | None = None
    error_message: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def _log_path() -> Path:
    day = _dt.datetime.now().strftime("%Y-%m-%d")
    return _LOG_DIR / f"chatbot-turns-{day}.jsonl"


def log_turn(record: TurnRecord) -> None:
    """Append one TurnRecord as a JSON line. Errors are swallowed."""
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        path = _log_path()
        payload = {k: v for k, v in asdict(record).items() if v is not None}
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
    except Exception as exc:  # never block chat
        print(f"[turn_logger] write failed: {exc}", file=sys.stderr)
