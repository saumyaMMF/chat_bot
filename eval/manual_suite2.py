"""Manual eval suite 2 — fresh queries testing SQL gen breadth.

Run:
    python -u -m eval.manual_suite2 > eval/manual_run3.txt 2>&1
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request

URL = "http://127.0.0.1:8000/chat"
TENANT = 1
STATES = ["CA"]
BRAND = "Rhize"


CASES: list[tuple[str, str, list]] = [
    # — orders / customers —
    ("orders", "top 10 customers by revenue", []),
    ("orders", "list pending wholesale orders", []),
    ("orders", "open balance total", []),
    ("orders", "orders by status this month", []),
    ("orders", "customers with open balance over 1000", []),
    ("orders", "best selling products by quantity this week", []),
    ("orders", "average order value last 7 days", []),
    # — inventory —
    ("inventory", "low stock items", []),
    ("inventory", "inventory by category", []),
    ("inventory", "out of stock products", []),
    # — lots —
    ("lots", "expiring lots in next 30 days", []),
    ("lots", "lots with low remaining quantity", []),
    # — brands (own) —
    ("brands", "what is my brand", []),
    ("brands", "list my brands", []),
    # — market (PG) —
    ("market", "top 5 brands in the market last 30 days", []),
    ("market", "competitor brand revenue today", []),
    ("market", "market share by company today", []),
    ("market", "industry wide category revenue today", []),
    ("market", "skus added to market today", []),
    ("market", "products removed from market today", []),
    ("market", "top stores in the market this week", []),
    # — drill-downs —
    ("drilldown", "show me brand Zizzle market performance", []),
    ("drilldown", "company Sweetspot revenue", []),
    ("drilldown", "category flower revenue this week", []),
    ("drilldown", "category preroll market share", []),
    # — date arithmetic —
    ("dates", "revenue yesterday", []),
    ("dates", "sales this week", []),
    ("dates", "orders in last 14 days", []),
    # — edge / ambiguous —
    ("ambiguous", "Zizzle", []),
    ("ambiguous", "show me Sunset", []),
    ("ambiguous", "performance", []),
    # — refusal —
    ("refusal", "delete all orders", []),
    ("refusal", "update inventory", []),
    ("refusal", "drop the brands table", []),
    # — out of scope —
    ("oos", "what is the weather today", []),
    ("oos", "tell me a joke", []),
    # — typos —
    ("typo", "lwo stock prodcts", []),
    ("typo", "tpo brnads last 30 days", []),
    ("typo", "compitior anlysis", []),
]


def ask(q: str, history: list) -> dict:
    payload = json.dumps({
        "question": q,
        "tenant_id": TENANT,
        "states": STATES,
        "brand_name": BRAND,
        "history": history,
    }).encode()
    req = urllib.request.Request(URL, data=payload, headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=200) as r:
            body = json.loads(r.read().decode())
    except Exception as e:
        body = {"error": f"REQ FAIL: {e}"}
    latency = time.perf_counter() - t0
    return {"body": body, "latency": latency}


def main() -> int:
    for cat, q, hist in CASES:
        r = ask(q, hist)
        b = r["body"]
        msg = b.get("message") or b.get("error") or ""
        sql = b.get("sql") or ""
        rc = b.get("row_count")
        kind = (
            "result" if b.get("rows") is not None and rc
            else "chat" if b.get("chat")
            else "clarify" if b.get("clarify")
            else "refused" if b.get("refused")
            else "unknown"
        )
        print(f"\n=== [{cat}] {q}")
        print(f"    latency: {r['latency']:.2f}s  kind={kind}  row_count={rc}")
        if sql:
            print(f"    sql: {' '.join(sql.split())[:300]}")
        if msg:
            print(f"    msg: {msg[:300]}")
        sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
