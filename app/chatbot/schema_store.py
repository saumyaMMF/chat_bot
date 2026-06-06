"""Schema-RAG store: load curated definitions, embed, upsert, retrieve.

Ingest path (offline, scripts/ingest_schema.py):
  load data/schema_definitions.json → embed each item → upsert into
  chatbot_schema_embeddings → ANALYZE.

Retrieval path (per request, app/chatbot/prompt_builder.py):
  embed question → cosine KNN top-k → return SchemaChunk[] with definition
  + restrictions for prompt injection.

Retrieval reads through the chatbot_ro pool (same as the SQL guard's
downstream execution). The schema embeddings table is reference data, NOT
tenant-scoped, so RLS does not need a policy on it; the GRANT SELECT in
sql/006 is sufficient.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from app.chatbot.embed_client import embed_text, to_pgvector_literal
from app.chatbot.readonly_db import get_pool
from app.chatbot._perf_cache import VectorSnapshot
from app.config import get_settings

# Market-scope signals (mirrors prompt_builder DEFAULT SCOPE).
_MARKET_SIGNALS = re.compile(
    r"\b(market|competitor|competitors|competing|rival|rivals|industry|"
    r"compared to others|vs others|scrape|scraped|across the market)\b",
    re.I,
)
_MARKET_TABLES = {
    "chatbot_mv_market_daily",
    "complete_market_scrapper_dataset",
    "chatbot_market",
}


_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
_DEFINITIONS_FILE = _DATA_DIR / "schema_definitions.json"


@dataclass
class SchemaItem:
    id: str
    kind: str
    table_name: str
    column_name: str | None
    data_type: str | None
    definition: str
    restrictions: str

    @property
    def embed_text(self) -> str:
        """Text that gets embedded. Includes table + column + restriction so the
        vector reflects all three dimensions the question might match on."""
        col = f".{self.column_name}" if self.column_name else ""
        dt = f" ({self.data_type})" if self.data_type else ""
        restr = f"\nRestrictions: {self.restrictions}" if self.restrictions else ""
        return (
            f"{self.kind.upper()} {self.table_name}{col}{dt}\n"
            f"{self.definition}{restr}"
        )


@dataclass
class SchemaChunk:
    """Retrieval result. Distance is cosine in [0, 2]."""
    id: str
    kind: str
    table_name: str
    column_name: str | None
    data_type: str | None
    definition: str
    restrictions: str
    distance: float


def load_definitions(path: Path = _DEFINITIONS_FILE) -> list[SchemaItem]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    out: list[SchemaItem] = []
    for raw in parsed.get("items") or []:
        out.append(SchemaItem(
            id=raw["id"],
            kind=raw["kind"],
            table_name=raw["table_name"],
            column_name=raw.get("column_name"),
            data_type=raw.get("data_type"),
            definition=raw["definition"],
            restrictions=raw.get("restrictions", "") or "",
        ))
    return out


async def upsert_item(
    item: SchemaItem,
    embedding: list[float],
    conn: "object | None" = None,
) -> None:
    """Upsert a single schema item with its embedding.

    If ``conn`` is provided (e.g. an admin asyncpg connection), the statement
    runs through it directly — used by offline ingest scripts that need
    INSERT/UPDATE on the embeddings table. Without ``conn`` the RO pool is
    used (only meaningful when the runtime role has INSERT on this table).
    """
    lit = to_pgvector_literal(embedding)
    sql = """
        INSERT INTO chatbot_schema_embeddings
            (id, kind, table_name, column_name, data_type, definition, restrictions, embedding, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8::vector, now())
        ON CONFLICT (id) DO UPDATE SET
            kind         = EXCLUDED.kind,
            table_name   = EXCLUDED.table_name,
            column_name  = EXCLUDED.column_name,
            data_type    = EXCLUDED.data_type,
            definition   = EXCLUDED.definition,
            restrictions = EXCLUDED.restrictions,
            embedding    = EXCLUDED.embedding,
            updated_at   = now()
        """
    params = (
        item.id,
        item.kind,
        item.table_name,
        item.column_name,
        item.data_type,
        item.definition,
        item.restrictions,
        lit,
    )
    if conn is not None:
        await conn.execute(sql, *params)  # type: ignore[attr-defined]
        return
    pool = await get_pool()
    async with pool.acquire() as ro_conn:
        await ro_conn.execute(sql, *params)


async def analyze_table(conn: "object | None" = None) -> None:
    """Run ANALYZE after ingest so the ivfflat index has stats. Cheap.
    Accepts an admin connection like ``upsert_item``."""
    if conn is not None:
        await conn.execute("ANALYZE chatbot_schema_embeddings")  # type: ignore[attr-defined]
        return
    pool = await get_pool()
    async with pool.acquire() as ro_conn:
        await ro_conn.execute("ANALYZE chatbot_schema_embeddings")


# ── In-memory snapshot of chatbot_schema_embeddings ─────────────────────────
# Reference data (~50-200 rows). Loaded once at startup, refreshed on
# updated_at watermark change (every 60s peek). Saves a per-request KNN round
# trip to Postgres (~30 ms) and removes the embedding-payload transit cost.


class _SchemaSnapshot(VectorSnapshot):
    def _row_to_payload(self, raw):  # type: ignore[override]
        return {
            "id": raw["id"],
            "kind": raw["kind"],
            "table_name": raw["table_name"],
            "column_name": raw["column_name"],
            "data_type": raw["data_type"],
            "definition": raw["definition"],
            "restrictions": raw["restrictions"] or "",
        }


_SNAPSHOT = _SchemaSnapshot(
    table_name="chatbot_schema_embeddings",
    select_sql=(
        "SELECT id, kind, table_name, column_name, data_type, definition, "
        "restrictions, embedding FROM chatbot_schema_embeddings"
    ),
)


async def retrieve_top_k(question: str, k: int | None = None) -> list[SchemaChunk]:
    """Embed the question and return the top-k nearest schema chunks by cosine
    distance. Always pins the parent table row for any retrieved column so the
    model sees the table-level context as well — small models forget which
    table a column belongs to without it.
    """
    settings = get_settings()
    if k is None:
        k = settings.schema_top_k

    has_market_signal = bool(_MARKET_SIGNALS.search(question))

    vec = await embed_text(question)

    # In-process KNN. Oversample so the diversity / parent-table guard has
    # headroom (matches the prior +4 / floor=12 behaviour).
    oversample = max(k + 4, 12)
    hits = await _SNAPSHOT.knn(vec, k=oversample)

    chunks = [
        SchemaChunk(
            id=p["id"],
            kind=p["kind"],
            table_name=p["table_name"],
            column_name=p["column_name"],
            data_type=p["data_type"],
            definition=p["definition"],
            restrictions=p["restrictions"],
            distance=d,
        )
        for (p, d) in hits
    ]

    # Engine-aware re-rank. If question lacks market signal, demote market
    # table chunks by +0.2 cosine so own-data (rhize_*) wins ties.
    if not has_market_signal:
        for c in chunks:
            if c.table_name in _MARKET_TABLES:
                c.distance += 0.2
        chunks.sort(key=lambda c: c.distance)

    top = chunks[:k]

    # Parent-table guard: if any retrieved column's table is NOT in top,
    # promote the parent table row (best-effort, capped at +2 extras). Pull
    # from the in-memory snapshot — no DB round-trip.
    present_tables = {c.table_name for c in top if c.kind in {"table", "view"}}
    needed_tables = {c.table_name for c in top if c.kind == "column"} - present_tables
    if needed_tables:
        extras_seen = 0
        for c in chunks:
            if extras_seen >= 2:
                break
            if c.table_name in needed_tables and c.kind in {"table", "view"} and c not in top:
                top.append(c)
                extras_seen += 1
        if extras_seen < 2:
            # snapshot may have a parent row that didn't make oversample top.
            # Do one targeted scan over all rows (still in-memory).
            for row in _SNAPSHOT._rows:  # noqa: SLF001 — same module family
                if extras_seen >= 2:
                    break
                p = row.payload
                if p["table_name"] in needed_tables and p["kind"] in {"table", "view"}:
                    if not any(c.id == p["id"] for c in top):
                        top.append(SchemaChunk(
                            id=p["id"], kind=p["kind"], table_name=p["table_name"],
                            column_name=p["column_name"], data_type=p["data_type"],
                            definition=p["definition"], restrictions=p["restrictions"],
                            distance=0.0,
                        ))
                        extras_seen += 1

    return top


def format_chunks_for_prompt(chunks: list[SchemaChunk]) -> str:
    """Render retrieved chunks into a deterministic, compact text block for the
    system prompt. Tables/views first, then columns grouped by their table."""
    if not chunks:
        return "(no schema context retrieved)"

    # group: tables first
    tables = [c for c in chunks if c.kind in {"table", "view"}]
    columns = [c for c in chunks if c.kind == "column"]

    lines: list[str] = []
    for t in tables:
        lines.append(f"### {t.table_name} ({t.kind.upper()})")
        lines.append(t.definition)
        if t.restrictions:
            lines.append(f"RESTRICT: {t.restrictions}")
        lines.append("")

    # columns grouped by table_name (preserve retrieval order within a table)
    grouped: dict[str, list[SchemaChunk]] = {}
    for c in columns:
        grouped.setdefault(c.table_name, []).append(c)

    for tname, cols in grouped.items():
        lines.append(f"### {tname} — columns")
        for c in cols:
            dt = f" ({c.data_type})" if c.data_type else ""
            lines.append(f"- **{c.column_name}**{dt}: {c.definition}")
            if c.restrictions:
                lines.append(f"  RESTRICT: {c.restrictions}")
        lines.append("")

    return "\n".join(lines).rstrip()


def collect_restrictions(chunks: list[SchemaChunk]) -> list[str]:
    """Flat unique list of non-empty restriction strings from retrieved chunks.
    The prompt builder appends these to the always-on rules header so the
    model sees them prominently — not just buried in the schema dump."""
    seen: set[str] = set()
    out: list[str] = []
    for c in chunks:
        r = (c.restrictions or "").strip()
        if r and r not in seen:
            seen.add(r)
            out.append(r)
    return out
