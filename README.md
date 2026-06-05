# rhize-chatbot (Python backend)

Python port of the rhize-intel NL→SQL chatbot. FastAPI backend, no UI.

Same four-gate security model as the TS original:

- **Gate A** — connection uses a dedicated read-only Postgres role (`chatbot_ro`).
- **Gate B** — Row-Level Security on every scoped table; `app.tenant_id` and `app.states` are set via `SET LOCAL` per request.
- **Gate C** — SQL guard (sqlglot) parses each model-generated statement, enforces single-SELECT, table allow-list, no DDL/DML, no dangerous functions.
- **Gate D** — `LIMIT 500` appended + `statement_timeout = 5s`, all inside a `BEGIN READ ONLY` transaction that is always rolled back.

## Layout

```
app/
  main.py              FastAPI POST /chat
  config.py            env loader
  chatbot/
    llm_client.py
    prompt_builder.py
    normalize_question.py
    sql_guard.py       Gate C
    readonly_db.py     Gates A/B/D
    chat_service.py    orchestrator
data/
  schema_context.md    injected into every prompt
  examples.json        few-shot pairs
sql/                   migrations (RO role, RLS, MV, pgvector)
tests/
  test_sql_guard.py
```

## Run

```bash
python -m venv .venv
.venv\Scripts\activate           # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env           # then edit DATABASE_URL_RO
ollama serve
ollama pull qwen2.5-coder:3b
uvicorn app.main:app --reload
```

## Endpoint

`POST /chat`

Request:
```json
{
  "question": "Top brands in the market.",
  "tenant_id": 42,
  "states": ["VT", "MA"],
  "brand_name": "Acme",
  "display_name": "Acme Cannabis"
}
```

Response (success):
```json
{ "ok": true, "sql": "SELECT ...", "row_count": 10, "rows": [...] }
```

Response (chat / refusal / error):
```json
{ "ok": true, "chat": true, "message": "..." }
{ "ok": false, "refused": true, "message": "..." }
{ "ok": false, "error": "..." }
```

## Auth note

Dev mode trusts `tenant_id` + `states` in the request body. Production must
swap `app/auth.py` to verify a JWT (or whatever scheme rhize-intel exposes)
and derive these server-side. Never accept them from an untrusted client.

## SQL migrations

Run the SQL in `sql/` against Postgres BEFORE pointing the bot at it:

1. `001_chatbot_ro_role.sql` — create the read-only role.
2. `002_rls_policies.sql` — enable RLS on every scoped table.
3. `003_mv_market_daily_view.sql` — security_barrier view over the MV.

These are copies of `rhize-intel/chatbot/sql/`. Keep them in sync.
