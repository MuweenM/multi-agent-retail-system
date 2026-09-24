import os
import sys

# Setup environment to run from project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from retail_common.db import SessionLocal, engine
from sqlalchemy import text
from retail_common.security.auth import get_password_hash

def init_sqlite():
    db = SessionLocal()
    
    # 1. users
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            user_id VARCHAR(50) PRIMARY KEY,
            tenant_id VARCHAR(50) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            role VARCHAR(50) NOT NULL,
            password_hash TEXT
        )
    """))
    
    # Seed users
    demo_pass = '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjIQqiRQYq'
    db.execute(text(f"""
        INSERT OR REPLACE INTO users (user_id, tenant_id, email, role, password_hash)
        VALUES 
            ('u_admin', 'demo', 'admin@demo.com', 'admin', '{demo_pass}'),
            ('u_reviewer', 'demo', 'reviewer@demo.com', 'reviewer', '{demo_pass}'),
            ('u_viewer', 'demo', 'viewer@demo.com', 'viewer', '{demo_pass}')
    """))
    
    # 2. usage_events
    db.execute(text("""
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
    
    # 3. bulk_jobs
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS bulk_jobs (
            job_id VARCHAR(50) PRIMARY KEY,
            tenant_id VARCHAR(50) NOT NULL,
            user_id VARCHAR(50),
            status VARCHAR(20) DEFAULT 'queued',
            total_rows INTEGER DEFAULT 0,
            processed_rows INTEGER DEFAULT 0,
            failed_rows INTEGER DEFAULT 0,
            summary_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    # 4. returns
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS returns (
            return_id VARCHAR(50) PRIMARY KEY,
            tenant_id VARCHAR(50) DEFAULT 'demo',
            job_id VARCHAR(100),
            decision VARCHAR(50),
            confidence NUMERIC(5, 2),
            root_cause_pred VARCHAR(100),
            raw_text_enc TEXT,
            clean_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    db.commit()
    db.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_sqlite()
