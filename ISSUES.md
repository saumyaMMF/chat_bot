# Chatbot — Open Issues

Last eval: **21/23 PASS** (p50 39s, p95 90s, qwen2.5-coder:3b CPU).
73 examples → 88 examples (55 SQL + 33 refusals = 38% refusal ratio).

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
| 3 | p50 = 39s on CPU | Ollama 3B Q4 | qwen2.5-coder:3b CPU-bound; prompt-eval = ~45s of total |
| 4 | p95 = 90s | same | Exceeds Vercel function maxDuration |
| 5 | Cold load = 14s/model | Ollama TTL | Fixed via keep_alive 15m/30m but server restart resets |
| 6 | Limited prefix cache | OpenAI-compat layer | num_keep=6000 partial hit; varies with RAG output |

## 🟠 Production blockers

| # | Issue | Where | Detail |
|---|---|---|---|
| 7 | ~~MySQL tunnel required~~ | resolved | Switched env to direct prod URL |
| 8 | rhize-intel still has old TS chatbot | `lib/chatbot/*` | Two implementations live — must delete after Python migration is verified |
| 9 | ~~No API route uses new client~~ | resolved | `app/api/chat/route.ts` now proxies to Python |
| 10 | Service token defaults to disabled | both `.env` | `CHATBOT_SERVICE_TOKEN=local-dev-secret` set both sides; rotate for prod |
| 11 | No deploy target | — | Vercel can't run Ollama. Need Fly/Hetzner/Modal for chat_bot |

## 🟡 Code quality / architecture

| # | Issue | Where | Detail |
|---|---|---|---|
| 12 | Dead string-rewrite code in TS | `rhize-intel/lib/chatbot/chatService.ts` | `canonicalizeSql`, `rewriteEqToILikeOnTextCols` — duplicates AST guard, fragile regex |
| 13 | Hand-maintained stopword lists | `chatService.ts` ENTITY_STOPWORDS | 50 words, will grow forever; embed classifier better |
| 14 | env file split confusion | rhize-intel `.env` + `.env.local` | Earlier: `${MYSQL_URL_RO}` literal value bug, embed URL missing `/v1` |
| 15 | Tests don't cover new code paths | `chat_bot/tests/` | No tests for `example_store.py`, eval harness, batched embed, parallel retrieval |
| 16 | No CI | — | Eval never runs automatically |
| 17 | aiomysql connection leak | logs show `Event loop is closed` | benign warning at shutdown |
| 18 | `--reload` deadlocks on file edits during in-flight requests | uvicorn | Workaround: `--reload-delay 1.0` |

## 🟡 Data / training corpus

| # | Issue | Where | Detail |
|---|---|---|---|
| 19 | 88 examples = small corpus | `data/examples.json` | Production NL→SQL fine-tunes use 5K-50K pairs |
| 20 | No real-traffic mining | `turn_logger` JSONL written, nothing reads | Free training data thrown away |
| 21 | 0 chat examples | examples.json | Only SQL + refusals; chat covered by fast-path regex only |
| 22 | No synthetic example generation | — | Could use LLM to generate question variants for refusal classes |

## 🟡 Retrieval / RAG

| # | Issue | Where | Detail |
|---|---|---|---|
| 23 | nomic-embed-text = 768d | embed_client | bge-m3 (1024d, hybrid) is +6 MTEB points stronger |
| 24 | No reranker | example_store | top-4 by cosine only; cross-encoder rerank improves recall |
| 25 | No hybrid BM25+dense | — | Exact brand-name matches missed by pure embedding |
| 26 | Single-vector per example | — | Late-interaction (ColBERT) better for short queries |
| 27 | Schema RAG token budget uncapped | `format_chunks_for_prompt` | Top-8 chunks could blow ctx budget on edge cases |
| 28 | Engine-aware demotion threshold hardcoded | `example_store.py`, `schema_store.py` | `+0.2` magic number; tune later |

## 🟢 Observability

| # | Issue | Where | Detail |
|---|---|---|---|
| 29 | No structured tracing | — | No Langfuse/Phoenix/Arize integration |
| 30 | No token-usage logging | `chat_complete_full` returns it, eval doesn't persist | Lost per-turn |
| 31 | No retrieval-quality metric | — | Distance logged per turn but never aggregated |
| 32 | No regression diff | `eval/baseline.json` written but no `diff` step | Manual compare only |
| 33 | No prompt drift hash | — | TS had it (`promptHash`), Py port lost it |

## 🟢 Security / safety

| # | Issue | Where | Detail |
|---|---|---|---|
| 34 | No rate limit on `/chat` | FastAPI | One bad client can OOM the box |
| 35 | No CORS config | FastAPI | Fine if API-only via rhize-intel; needed if frontend ever calls direct |
| 36 | Service token only env-checked | `main.py` | No rotation, no per-tenant scoping |
| 37 | Logs may leak SQL with literals | `chat_service.py:325-327` | Tenant queries logged at INFO; should redact |
| 38 | MySQL SSL CERT_NONE in dev | `readonly_db_mysql.py` | Off by default; CHATBOT_MYSQL_SSL_STRICT=1 re-enables. Acceptable for now since traffic still TLS-encrypted, just unverified |
| 39 | UI renders 401 as chat bubble | rhize-intel chat component | Should detect 401 and redirect to login or show toast |

## 🟢 Inference / model

| # | Issue | Where | Detail |
|---|---|---|---|
| 40 | No model fallback chain | `llm_client.py` | Single provider; outage = full downtime |
| 41 | No structured output | parse `CHAT:`/`REFUSE:`/SQL via regex | Outlines/SGLang would force `{"kind":...}` JSON |
| 42 | No fine-tuning pipeline | — | SQLCoder-7b fine-tuned on Rhize schema would beat 3B base |
| 43 | qwen-coder is base, not instruct (caps: completion,tools,insert) | — | Works via Ollama chat template but instruct variant better |
| 44 | No streaming | `chat_complete` | UX would feel faster with token-by-token; total time unchanged |

## 🟢 Misc / housekeeping

| # | Issue | Where | Detail |
|---|---|---|---|
| 45 | Unicode crash on Windows cp1252 | eval/run.py | FIXED — swapped `✓` for `[OK]` |
| 46 | `DATABASE_URL_ADMIN ` has trailing space | `.env` | Loads OK but unclean |
| 47 | examples.json has both `examples` + lots of comments | data dir | No schema validation on JSON shape |
| 48 | `BOOTSTRAP.md` written, no `Makefile` | repo root | Common commands not codified |
| 49 | No version pin on Ollama models | docs say `qwen2.5-coder:3b` | `:latest` could shift behavior |
| 50 | `Event loop is closed` warning on shutdown | aiomysql pool | Benign, ignore |

---

## Totals

- 🔴 Critical: **2** (eval fails)
- 🟠 High (prod blockers): **8** (2 resolved this session)
- 🟡 Medium (debt): **18**
- 🟢 Low (polish): **22**
- **TOTAL OPEN: 48**

## Closed this session

| # | Issue | Resolution |
|---|---|---|
| ✓ | refusal-other-state | Added training examples; eval passes |
| ✓ | revenue→market routing bias | Engine-aware demotion (+0.2 cosine for market when no market keyword) |
| ✓ | "my country" → SQL hallucination | AUTHENTICATED USER CONTEXT block in prompt |
| ✓ | Default-engine ambiguity | DEFAULT SCOPE rule added |
| ✓ | Market data granularity | DATA-GRANULARITY block added |
| ✓ | MySQL connect: ProactorEventLoop + SSL | Forced SelectorEventLoop on Windows |
| ✓ | MySQL SSL CA mismatch | CERT_NONE in dev, opt-in strict |
| ✓ | num_ctx not set | options.num_ctx=16384 |
| ✓ | num_keep not set | options.num_keep=6000 |
| ✓ | seed/top_p/repeat_penalty unset | All set in options |
| ✓ | keep_alive missing | Set on chat + embed |
| ✓ | Sequential retrieval | asyncio.gather schema + examples |
| ✓ | Sequential embed in offline ingest | embed_batch added |
| ✓ | example_store dead code | Wired into prompt_builder |
| ✓ | Eval Unicode crash | `✓` → `[OK]` |
| ✓ | Fast-path retrieval-fallback misreporting | Excluded greeting/identity from fallback count |
| ✓ | Service auth | Bearer token + hmac.compare_digest |
| ✓ | rhize-intel route not wired | Proxies to Python service with abort forwarding |

## Recommended next 3 actions

1. **Move LLM off CPU** — Groq free tier or Hetzner CX22 GPU spot ($0.20/hr) → sub-second responses
2. **Fix refusal-joke + sql-sales-by-store** — get to 23/23 (1 hr)
3. **Delete `rhize-intel/lib/chatbot/*`** once Python service verified in staging (2 hrs)
