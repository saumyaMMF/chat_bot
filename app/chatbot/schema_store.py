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
    lit = to_pgvector_literal(vec)

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Oversample so the diversity / parent-table guard has headroom.
        oversample = max(k + 4, 12)
        rows = await conn.fetch(
            """
            SELECT id, kind, table_name, column_name, data_type, definition,
                   restrictions,
                   (embedding <=> $1::vector)::float8 AS distance
              FROM chatbot_schema_embeddings
             ORDER BY embedding <=> $1::vector
             LIMIT $2
            """,
            lit,
            oversample,
        )

        chunks = [
            SchemaChunk(
                id=r["id"],
                kind=r["kind"],
                table_name=r["table_name"],
                column_name=r["column_name"],
                data_type=r["data_type"],
                definition=r["definition"],
                restrictions=r["restrictions"] or "",
                distance=r["distance"],
            )
            for r in rows
        ]

        # Engine-aware re-rank. If question lacks market signal, demote market
        # table chunks by +0.2 cosine so own-data (rhize_*) wins ties.
        # Without this, "revenue" matches market+own equally on the embedding,
        # but the prompt's DEFAULT SCOPE says own data → bias retrieval too.
        if not has_market_signal:
            for c in chunks:
                if c.table_name in _MARKET_TABLES:
                    c.distance += 0.2
            chunks.sort(key=lambda c: c.distance)

        top = chunks[:k]

        # Parent-table guard: if any retrieved column's table is NOT in top,
        # promote the parent table row (best-effort, capped at +2 extras).
        present_tables = {c.table_name for c in top if c.kind in {"table", "view"}}
        needed_tables = {c.table_name for c in top if c.kind == "column"} - present_tables
        if needed_tables:
            extra = await conn.fetch(
                """
                SELECT id, kind, table_name, column_name, data_type, definition,
                       restrictions, 0::float8 AS distance
                  FROM chatbot_schema_embeddings
                 WHERE table_name = ANY($1::text[])
                   AND kind IN ('table','view')
                 LIMIT 2
                """,
                list(needed_tables),
            )
            for r in extra:
                top.append(SchemaChunk(
                    id=r["id"],
                    kind=r["kind"],
                    table_name=r["table_name"],
                    column_name=r["column_name"],
                    data_type=r["data_type"],
                    definition=r["definition"],
                    restrictions=r["restrictions"] or "",
                    distance=r["distance"],
                ))

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
