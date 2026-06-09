"""Render TableProfile to JSON + Markdown."""

from __future__ import annotations

import json
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.schema_profiler.models import ColumnProfile, TableProfile


def _to_jsonable(x: Any) -> Any:
    if isinstance(x, (datetime, date, time)):
        return x.isoformat()
    if isinstance(x, Decimal):
        return float(x)
    if isinstance(x, bytes):
        try:
            return x.decode("utf-8", errors="replace")
        except Exception:
            return repr(x)
    if isinstance(x, dict):
        return {k: _to_jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_to_jsonable(v) for v in x]
    return x


def write_json(profile: TableProfile, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{profile.engine}__{profile.table}.json"
    data = _to_jsonable(profile.to_dict())
    p.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return p


def _fmt_v(v: Any) -> str:
    if v is None:
        return "—"
    s = str(v)
    return s if len(s) <= 80 else s[:77] + "…"


def _col_md(c: ColumnProfile) -> str:
    lines: list[str] = []
    lines.append(f"### `{c.name}` — {c.inferred_kind}")
    lines.append("")
    lines.append(f"- **Declared type:** `{c.declared_type}`")
    lines.append(f"- **Nullable:** {c.nullable} · **Null %:** {c.null_pct}%")
    lines.append(
        f"- **Rows:** {c.total_rows:,} · **Distinct:** {c.distinct_count:,} "
        f"({c.distinct_pct}% of non-null)"
    )
    flags: list[str] = []
    if c.is_unique:
        flags.append("UNIQUE-LIKE")
    if c.is_low_cardinality:
        flags.append("LOW-CARDINALITY (categorical)")
    if c.notes:
        flags.extend(n.upper() for n in c.notes)
    if flags:
        lines.append(f"- **Flags:** {', '.join(flags)}")
    if c.min_value is not None or c.max_value is not None:
        lines.append(f"- **Range:** min=`{_fmt_v(c.min_value)}` · max=`{_fmt_v(c.max_value)}`")
    if c.min_length is not None:
        lines.append(
            f"- **Length:** min={c.min_length} · max={c.max_length} · avg={c.avg_length}"
        )
    if c.pattern_hints:
        lines.append(f"- **Pattern hints:** {', '.join(c.pattern_hints)}")
    if c.distinct_values is not None:
        preview = c.distinct_values[:200]
        joined = ", ".join(f"`{_fmt_v(v)}`" for v in preview)
        more = f" _(+{len(c.distinct_values) - 200} more)_" if len(c.distinct_values) > 200 else ""
        lines.append(f"- **All distinct values ({len(c.distinct_values)}):** {joined}{more}")
    elif c.top_values:
        top = ", ".join(f"`{_fmt_v(v)}` ({n:,})" for v, n in c.top_values[:20])
        lines.append(f"- **Top values:** {top}")
    return "\n".join(lines)


def render_markdown(profile: TableProfile) -> str:
    head = [
        f"# `{profile.table}` ({profile.engine})",
        "",
        f"- **Schema:** {profile.schema or '—'}",
        f"- **Rows:** {profile.row_count:,}",
        f"- **Columns:** {profile.column_count}",
    ]
    if profile.primary_key:
        head.append(f"- **Primary key:** {', '.join(f'`{k}`' for k in profile.primary_key)}")
    if profile.indexes:
        names = ", ".join(
            f"`{i['name']}`({'U' if i.get('unique') else 'N'}: {','.join(i['columns'])})"
            for i in profile.indexes
        )
        head.append(f"- **Indexes:** {names}")
    if profile.notes:
        head.append(f"- **Notes:** {', '.join(profile.notes)}")
    head.append("")
    head.append("## Columns")
    head.append("")
    body = [_col_md(c) for c in profile.columns]

    if profile.sample_rows:
        sample = ["", "## Sample rows", ""]
        cols = list(profile.sample_rows[0].keys())
        sample.append("| " + " | ".join(cols) + " |")
        sample.append("| " + " | ".join(["---"] * len(cols)) + " |")
        for r in profile.sample_rows:
            sample.append("| " + " | ".join(_fmt_v(r.get(c)) for c in cols) + " |")
    else:
        sample = []

    return "\n".join(head + ["\n\n".join(body)] + sample) + "\n"


def write_markdown(profile: TableProfile, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"{profile.engine}__{profile.table}.md"
    p.write_text(render_markdown(profile), encoding="utf-8")
    return p
