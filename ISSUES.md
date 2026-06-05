# Chatbot — Open Issues

Generated from session audit. Last eval: **21/23 PASS** (p50 39s, p95 90s, qwen2.5-coder:3b CPU).

Severity: 🔴 critical · 🟠 high · 🟡 medium · 🟢 low

---

## 🔴 Active failures (eval 2/23 fail)

| # | Issue | Where | Symptom |
|---|---|---|---|
| 1 | `refusal-joke` misclassified as chat | system prompt CHAT category | "tell me a joke" → joke text instead of REFUSE |
| 2 | `sql-sales-by-store` hallucinates column | LLM output | invents `rhize_orders.company_name` (doesn't exist) |

## 🟠 Latency (won't meet Vercel 60s cap)

| # | Issue | Where | Detail |
|---|---|---|---|
| 3 | p50 = 39s on CPU | Ollama 3B Q4 | qwen2.5-coder:3b CPU-bound |
| 4 | p95 = 90s | same | Exceeds Vercel function maxDuration |
| 5 | Cold load = 14s/model | Ollama TTL | Fixed via keep_alive 15m/30m but server restart resets |
| 6 | No prefix cache | OpenAI-compat layer | 7K-token system prompt re-tokenized every call |

## 🟠 Production blockers

| # | Issue | Where | Detail |
|---|---|---|---|
| 7 | MySQL tunnel required | `.env` `CHATBOT_MYSQL_RO_URL=127.0.0.1:13306` | User must run SSH tunnel manually |
| 8 | rhize-intel still has old TS chatbot | `lib/chatbot/*` | Two implementations live — must delete after migration |
| 9 | No API route uses new client yet | `app/api/chat/route.ts` | `callChatbot()` written, not wired |
| 10 | Service token not set | both `.env` | `CHATBOT_SERVICE_TOKEN` empty → auth disabled |
| 11 | No deploy target | — | Vercel can't run Ollama. No Docker, no Fly/Modal config |

## 🟡 Code quality / architecture

| # | Issue | Where | Detail |
|---|---|---|---|
| 12 | Dead string-rewrite code in TS | `rhize-intel/lib/chatbot/chatService.ts` | `canonicalizeSql`, `rewriteEqToILikeOnTextCols` — duplicates AST guard, fragile regex |
| 13 | Hand-maintained stopword lists | `chatService.ts` ENTITY_STOPWORDS | 50 words, will grow forever; embed classifier better |
| 14 | env file split confusion | rhize-intel `.env` + `.env.local` | Earlier: `${MYSQL_URL_RO}` literal value bug, embed URL missing `/v1` |
| 15 | Tests don't cover new code paths | `chat_bot/tests/` | No tests for `example_store.py`, eval harness, batched embed |
| 16 | No CI | — | Eval never runs automatically |
| 17 | aiomysql connection leak | logs show `Event loop is closed` | benign warning at shutdown |

## 🟡 Data / training corpus

| # | Issue | Where | Detail |
|---|---|---|---|
| 18 | 73 examples = small corpus | `data/examples.json` | Production NL→SQL fine-tunes use 5K-50K pairs |
| 19 | No real-traffic mining | `turn_logger` JSONL written, nothing reads | Free training data thrown away |
| 20 | 0 chat examples | examples.json | Only 52 SQL + 21 refusals; chat covered by fast-path regex only |
| 21 | No synthetic example generation | — | Could use LLM to generate question variants for refusal classes |

## 🟡 Retrieval / RAG

| # | Issue | Where | Detail |
|---|---|---|---|
| 22 | nomic-embed-text = 768d | embed_client | bge-m3 (1024d, hybrid) is +6 MTEB points stronger |
| 23 | No reranker | example_store | top-4 by cosine only; cross-encoder rerank improves recall |
| 24 | No hybrid BM25+dense | — | Exact brand-name matches missed by pure embedding |
| 25 | Single-vector per example | — | Late-interaction (ColBERT) better for short queries |
| 26 | Schema RAG token budget uncapped | `format_chunks_for_prompt` | Top-8 chunks could blow ctx budget on edge cases |

## 🟢 Observability

| # | Issue | Where | Detail |
|---|---|---|---|
| 27 | No structured tracing | — | No Langfuse/Phoenix/Arize integration |
| 28 | No token-usage logging | `chat_complete_full` returns it, eval doesn't persist | Lost per-turn |
| 29 | No retrieval-quality metric | — | Distance logged per turn but never aggregated |
| 30 | No regression diff | `eval/baseline.json` written but no `diff` step | Manual compare only |
| 31 | No prompt drift hash | — | TS had it (`promptHash`), Py port lost it |

## 🟢 Security / safety

| # | Issue | Where | Detail |
|---|---|---|---|
| 32 | No rate limit on `/chat` | FastAPI | One bad client can OOM the box |
| 33 | No CORS config | FastAPI | Fine if API-only via rhize-intel; needed if frontend ever calls direct |
| 34 | Service token only env-checked | `main.py` | No rotation, no per-tenant scoping |
| 35 | Logs may leak SQL with literals | `chat_service.py:325-327` | Tenant queries logged at INFO; should redact |

## 🟢 Inference / model

| # | Issue | Where | Detail |
|---|---|---|---|
| 36 | No model fallback chain | `llm_client.py` | Single provider; outage = full downtime |
| 37 | No structured output | parse `CHAT:`/`REFUSE:`/SQL via regex | Outlines/SGLang would force `{"kind":...}` JSON |
| 38 | No fine-tuning pipeline | — | SQLCoder-7b fine-tuned on Rhize schema would beat 3B base |
| 39 | qwen-coder is base, not instruct (caps: completion,tools,insert) | — | Works via Ollama chat template but instruct variant better |

## 🟢 Misc / housekeeping

| # | Issue | Where | Detail |
|---|---|---|---|
| 40 | Unicode crash on Windows cp1252 | eval/run.py (fixed) | `✓` char → swapped to `[OK]`/`[FAIL]` |
| 41 | `DATABASE_URL_ADMIN ` has trailing space | `.env` | Loads OK but unclean |
| 42 | examples.json has both `examples` + lots of comments | data dir | No schema validation on JSON shape |
| 43 | `BOOTSTRAP.md` written, no `Makefile` | repo root | Common commands not codified |
| 44 | No version pin on Ollama models | docs say `qwen2.5-coder:3b` | `:latest` could shift behavior |

---

## Totals

- 🔴 Critical: **2** (eval fails)
- 🟠 High (prod blockers): **9**
- 🟡 Medium (debt): **18**
- 🟢 Low (polish): **15**
- **TOTAL: 44**

## Recommended next 3 actions

1. **Fix refusal-joke + sql-sales-by-store** — get to 100% on current eval (1-2 hrs)
2. **Wire `callChatbot()` into rhize-intel API route** — kill TS chatbot dir (2 hrs)
3. **Move inference off CPU** — Groq free tier or Modal T4 (1 hr setup); p95 90s → sub-second
