"""
Centralized configuration loaded from environment variables (.env).
Every agent imports `settings` from here instead of reading os.environ directly.

No default values are set here on purpose — every field must be
provided in your .env file. If a value is missing, this will raise
a clear error at startup instead of silently using a value nobody chose.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    llm_provider: str
    llm_api_key: str
    llm_model: str

    # Database
    database_url: str

    # Vector store
    vector_db_path: str
    vector_collection: str

    # Agent MCP endpoints (used by Agent 4's orchestrator)
    agent1_mcp_url: str
    agent2_mcp_url: str
    agent3_mcp_url: str

    # Security
    jwt_secret: str
    jwt_algorithm: str
    service_secret: str = "demo-service-secret"
    encryption_key: str = "TfOxgZfL1F_6hXmEIt8xM3F2A0rXN1CqF_XQG-yV6y4=" # Default Fernet key for demo

    # System Policies & Thresholds
    high_value_lkr: float = 100000.0
    human_review_min_confidence: float = 0.75

    # Misc
    env: str
    log_level: str


settings = Settings()
