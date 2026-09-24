"""
Shared SQLAlchemy session used by any agent that needs Postgres access
(mainly Agent 2 for historical returns, Agent 3 for evidence sources).

TODO (whoever owns Agent 2 or Agent 3):
- Nothing required here for basic setup — engine/session below is ready to use.
- If you add ORM models (tables as Python classes), define them in your
  own agent and import Base from here.
"""
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=pool.StaticPool,
    )
    # Automatically create the required table for tests using SQLite
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS usage_events (
                event_id VARCHAR(50) PRIMARY KEY,
                tenant_id VARCHAR(50) NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                api_call VARCHAR(100),
                llm_tokens INTEGER DEFAULT 0,
                store_id VARCHAR(50),
                quantity INTEGER DEFAULT 1,
                ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
else:
    engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
