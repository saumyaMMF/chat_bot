# Bootstrap order

## One-time setup

1. **Apply SQL migrations** (need writer role):
   ```
   psql "$DATABASE_URL_ADMIN" -f sql/005_pgvector_examples.sql
   psql "$DATABASE_URL_ADMIN" -f sql/006_schema_embeddings.sql
   ```

2. **Pull Ollama models**:
   ```
   ollama pull qwen2.5-coder:3b
   ollama pull nomic-embed-text
   ```

3. **Set `.env`** at `D:\Projects\Rhize Dashboard\chat_bot\.env`:
   ```
   DATABASE_URL_RO=postgresql://chatbot_ro:...@host:25060/defaultdb?sslmode=require
   DATABASE_URL_ADMIN=postgresql://doadmin:...@host:25060/defaultdb?sslmode=require
   CHATBOT_MYSQL_RO_URL=mysql://chatbot_ro:...@host:25060/scraperdb?ssl=true

   CHATBOT_LLM_BASE_URL=http://localhost:11434/v1
   CHATBOT_LLM_MODEL=qwen2.5-coder:3b
   CHATBOT_LLM_API_KEY=ollama
   CHATBOT_LLM_NUM_CTX=16384
   CHATBOT_LLM_NUM_PREDICT=512
   CHATBOT_LLM_SEED=42
   CHATBOT_LLM_KEEP_ALIVE=15m

   CHATBOT_EMBED_MODEL=nomic-embed-text
   CHATBOT_EMBED_KEEP_ALIVE=30m
   CHATBOT_EMBED_DISTANCE_THRESHOLD=0.65

   CHATBOT_SERVICE_TOKEN=<shared-secret-with-rhize-intel>
   ```

4. **Embed schema + examples** (offline, ~30s):
   ```
   python -m scripts.ingest_schema
   python -m scripts.embed_examples
   ```

## Run the service

```
python -m app.main
```

Exposes:
- `GET  /health` — liveness
- `POST /chat`   — main endpoint, Bearer-token guarded

## Run eval

```
python -m eval.run
```

Writes `eval/baseline.json` for run-to-run diffing.

## Connect from rhize-intel

In `rhize-intel/.env.local`:
```
CHATBOT_SERVICE_URL=http://127.0.0.1:8000
CHATBOT_SERVICE_TOKEN=<same-secret>
CHATBOT_SERVICE_TIMEOUT_MS=60000
```

In your Next.js API route, import `callChatbot` from `lib/chatbot-client.ts`.
