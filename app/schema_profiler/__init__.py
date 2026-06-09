"""Deep schema profiler.

Scans every column of every requested table, builds per-column statistics
(types, null %, distinct count, min/max, length stats, top-N value frequencies,
full-distinct lists when cardinality is small, regex pattern hints), and emits
markdown + JSON ready for chatbot prompt enrichment.

Entry points:
    from app.schema_profiler import profile_mysql, profile_postgres
    asyncio.run(profile_mysql(["rhize_orders"]))
"""

from app.schema_profiler.models import ColumnProfile, TableProfile
from app.schema_profiler.mysql import profile_mysql
from app.schema_profiler.pg import profile_postgres

__all__ = ["ColumnProfile", "TableProfile", "profile_mysql", "profile_postgres"]
