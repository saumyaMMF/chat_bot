from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url_ro: str | None = Field(default=None, alias="DATABASE_URL_RO")
    # Privileged URL used ONLY by offline ingest scripts (writes to the
    # chatbot_schema_embeddings / chatbot_example_embeddings reference tables).
    # The runtime chat path never uses this — only DATABASE_URL_RO.
    database_url_admin: str | None = Field(default=None, alias="DATABASE_URL_ADMIN")
    mysql_ro_url: str | None = Field(default=None, alias="CHATBOT_MYSQL_RO_URL")
    valid_tenant_ids_csv: str = Field(default="1,3,99", alias="CHATBOT_VALID_TENANT_IDS")

    @property
    def valid_tenant_ids(self) -> frozenset[int]:
        return frozenset(
            int(x.strip()) for x in self.valid_tenant_ids_csv.split(",") if x.strip()
        )

    # ── LLM (chat generation) ─────────────────────────────────────────────────
    llm_base_url: str = Field(default="http://localhost:11434/v1", alias="CHATBOT_LLM_BASE_URL")
    llm_model: str = Field(default="qwen2.5-coder:3b", alias="CHATBOT_LLM_MODEL")
    llm_api_key: str = Field(default="ollama", alias="CHATBOT_LLM_API_KEY")
    llm_timeout_ms: int = Field(default=120_000, alias="CHATBOT_LLM_TIMEOUT_MS")

    # Inference tuning — these MUST be set or Ollama defaults truncate the
    # 7K-token system prompt and the model emits 1-3 char garbage. See audit.
    llm_num_ctx: int = Field(default=16_384, alias="CHATBOT_LLM_NUM_CTX")
    llm_num_predict: int = Field(default=512, alias="CHATBOT_LLM_NUM_PREDICT")
    llm_seed: int = Field(default=42, alias="CHATBOT_LLM_SEED")
    llm_top_p: float = Field(default=0.1, alias="CHATBOT_LLM_TOP_P")
    llm_repeat_penalty: float = Field(default=1.05, alias="CHATBOT_LLM_REPEAT_PENALTY")
    llm_keep_alive: str = Field(default="15m", alias="CHATBOT_LLM_KEEP_ALIVE")
    # Ollama prefix cache. Tells the runner to KEEP the first N tokens of the
    # KV cache between requests. Set to the size of your system prompt
    # (~6000 tokens for RESTRICTION_RULES + schema RAG + user context). The
    # system prompt is identical across turns within a session, so re-using
    # the cached prefix skips re-evaluating ~80% of the input. On CPU this is
    # the difference between 30s prompt-eval and 5s.
    llm_num_keep: int = Field(default=6_000, alias="CHATBOT_LLM_NUM_KEEP")

    # ── Retrieval ─────────────────────────────────────────────────────────────
    top_k: int = Field(default=4, alias="CHATBOT_TOP_K")
    row_limit: int = Field(default=500, alias="CHATBOT_ROW_LIMIT")
    statement_timeout_ms: int = Field(default=5_000, alias="CHATBOT_STATEMENT_TIMEOUT_MS")

    embed_model: str = Field(default="nomic-embed-text", alias="CHATBOT_EMBED_MODEL")
    embed_timeout_ms: int = Field(default=8_000, alias="CHATBOT_EMBED_TIMEOUT_MS")
    embed_keep_alive: str = Field(default="30m", alias="CHATBOT_EMBED_KEEP_ALIVE")
    # Optional split — when CHATBOT_LLM_BASE_URL points at a hosted provider
    # (Gemini/Groq/etc) the embeddings must stay on local Ollama because
    # our pgvector rows are nomic-embed-text 768-dim. Empty = fall back to LLM url.
    embed_base_url: str = Field(default="", alias="CHATBOT_EMBED_BASE_URL")
    embed_api_key: str = Field(default="", alias="CHATBOT_EMBED_API_KEY")
    schema_top_k: int = Field(default=8, alias="CHATBOT_SCHEMA_TOP_K")

    # Cosine-distance threshold for retrieval. pgvector cosine ∈ [0, 2]:
    # 0 = identical, 1 = orthogonal, 2 = opposite. Anything > 0.6 is usually
    # noise for nomic-embed-text. Tuned conservatively to keep recall high.
    embed_distance_threshold: float = Field(default=0.65, alias="CHATBOT_EMBED_DISTANCE_THRESHOLD")

    # Fast-path cache (chatbot_fast_path_embeddings). Stricter than the schema /
    # example RAG threshold — a hit triggers SKIPPING the LLM entirely, so we
    # want near-paraphrase matches only. cosine in [0, 2]; 0.18 ≈ similarity 0.91.
    fast_path_distance_threshold: float = Field(default=0.18, alias="CHATBOT_FAST_PATH_DISTANCE_THRESHOLD")
    fast_path_enabled: bool = Field(default=True, alias="CHATBOT_FAST_PATH_ENABLED")

    # ── Server ────────────────────────────────────────────────────────────────
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    log_level: str = Field(default="info", alias="LOG_LEVEL")

    # ── Service auth (when called from rhize-intel) ───────────────────────────
    service_token: str | None = Field(default=None, alias="CHATBOT_SERVICE_TOKEN")

    # ── Privacy ───────────────────────────────────────────────────────────────
    # When true, the prompt builder swaps brand/display names for opaque tokens
    # and drops executed-row text from history. Designed for the day someone
    # points CHATBOT_LLM_BASE_URL at a hosted LLM (Gemini/OpenAI/etc) without
    # also remembering to redact PII. Default false because the local Ollama
    # path keeps everything on-box.
    redact_pii: bool = Field(default=False, alias="CHATBOT_REDACT_PII")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
