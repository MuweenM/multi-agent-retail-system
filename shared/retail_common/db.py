"""
Shared SQLAlchemy session used by any agent that needs Postgres access
(mainly Agent 2 for historical returns, Agent 3 for evidence sources).

TODO (whoever owns Agent 2 or Agent 3):
- Nothing required here for basic setup — engine/session below is ready to use.
- If you add ORM models (tables as Python classes), define them in your
  own agent and import Base from here.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
