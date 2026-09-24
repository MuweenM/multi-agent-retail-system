"""
Centralized configuration loaded from environment variables (.env).
Every agent imports `settings` from here instead of reading os.environ directly.

This project keeps a shared `.env.example`, but local test runs and lightweight
stubs should still import cleanly even when there is no real `.env` file yet.
We therefore provide safe local defaults while still allowing real environment
values to override them.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    llm_provider: str = "openai"
    llm_api_key: str = "dev-key"
    llm_model: str = "gpt-4o-mini"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/retail"

    # Vector store
    vector_db_path: str = "./data/vector_store"
    vector_collection: str = "retail"

    # Agent MCP ports and endpoints (used by Agent 4's orchestrator)
    AGENT1_PORT: int = 8001
    AGENT2_PORT: int = 8002
    AGENT3_PORT: int = 8003
    AGENT4_PORT: int = 8004
    agent1_mcp_url: str = "http://localhost:8001/mcp"
    agent2_mcp_url: str = "http://localhost:8002/mcp"
    agent3_mcp_url: str = "http://localhost:8003/mcp"

    # Security
    jwt_secret: str = "dev-secret"
    jwt_algorithm: str = "HS256"

    # Misc
    env: str = "local"
    log_level: str = "INFO"


settings = Settings()
