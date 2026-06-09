from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class ColumnProfile:
    name: str
    declared_type: str
    inferred_kind: str            # numeric | integer | float | date | datetime | text | bool | json | unknown
    nullable: bool
    total_rows: int
    null_count: int
    null_pct: float
    distinct_count: int
    distinct_pct: float           # distinct / non-null
    is_unique: bool
    is_low_cardinality: bool      # ≤ 50 distinct → categorical
    min_value: Any = None
    max_value: Any = None
    min_length: int | None = None
    max_length: int | None = None
    avg_length: float | None = None
    pattern_hints: list[str] = field(default_factory=list)
    distinct_values: list[Any] | None = None           # only when ≤ threshold
    top_values: list[tuple[Any, int]] = field(default_factory=list)  # value, freq
    sample_values: list[Any] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # tuples → lists for JSON
        d["top_values"] = [[v, n] for v, n in self.top_values]
        return d


@dataclass
class TableProfile:
    engine: str                   # mysql | postgres
    schema: str | None
    table: str
    row_count: int
    column_count: int
    primary_key: list[str] = field(default_factory=list)
    indexes: list[dict[str, Any]] = field(default_factory=list)
    columns: list[ColumnProfile] = field(default_factory=list)
    sample_rows: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "schema": self.schema,
            "table": self.table,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "primary_key": self.primary_key,
            "indexes": self.indexes,
            "columns": [c.to_dict() for c in self.columns],
            "sample_rows": self.sample_rows,
            "notes": self.notes,
        }
