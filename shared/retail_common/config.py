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

    # Misc
    env: str
    log_level: str


settings = Settings()
