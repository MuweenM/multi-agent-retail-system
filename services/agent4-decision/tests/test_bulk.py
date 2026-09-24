import pytest
from fastapi.testclient import TestClient
from shared.retail_common.security.auth import create_access_token
from app.server import app

import io
from shared.retail_common.db import SessionLocal
from sqlalchemy import text

client = TestClient(app)

def setup_db():
    db = SessionLocal()
    # Create bulk_jobs table for tests
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS bulk_jobs (
            job_id VARCHAR(50) PRIMARY KEY,
            tenant_id VARCHAR(50) NOT NULL,
            user_id VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'queued',
            total_rows INTEGER NOT NULL DEFAULT 0,
            processed_rows INTEGER NOT NULL DEFAULT 0,
            failed_rows INTEGER NOT NULL DEFAULT 0,
            summary_json JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS returns (
            return_id VARCHAR(50) PRIMARY KEY,
            bulk_job_id VARCHAR(50),
            tenant_id VARCHAR(50) NOT NULL,
            raw_text_enc TEXT NOT NULL,
            customer_ref_hash VARCHAR(64),
            root_cause_pred VARCHAR(50),
            issue TEXT,
            order_value_lkr DECIMAL(10,2),
            status VARCHAR(20) DEFAULT 'processed'
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS decisions (
            decision_id VARCHAR(50) PRIMARY KEY,
            bulk_job_id VARCHAR(50),
            tenant_id VARCHAR(50) NOT NULL,
            return_id VARCHAR(50) NOT NULL,
            root_cause VARCHAR(50) NOT NULL,
            confidence FLOAT NOT NULL,
            evidence_summary TEXT,
            recommendation TEXT,
            decision VARCHAR(50) NOT NULL,
            requires_human_review BOOLEAN NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.commit()
    db.close()

def get_token():
    return create_access_token({"sub": "u_admin", "tenant_id": "demo", "role": "admin"})

def test_bulk_upload_validation_failure():
    token = get_token()
    
    # Missing required text column
    csv_content = "order_id,product_id\n123,ABC"
    files = {"file": ("test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    
    response = client.post(
        "/api/v1/bulk",
        headers={"Authorization": f"Bearer {token}"},
        files=files
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "validation_failed"
    assert "Required column 'text'" in str(data["errors"])

def test_bulk_export_csv():
    setup_db()
    token = get_token()
    
    # Mock some data in decisions table for export
    db = SessionLocal()
    job_id = "bulk-test-123"
    try:
        db.execute(text("""
            INSERT INTO decisions (decision_id, bulk_job_id, tenant_id, return_id, root_cause, confidence, evidence_summary, recommendation, decision, requires_human_review)
            VALUES ('d1', :job_id, 'demo', '=RET-1', 'unknown', 0.9, 'test', 'rec', 'approve', false)
        """), {"job_id": job_id})
        db.commit()
    except Exception as e:
        db.rollback()
    finally:
        db.close()

    response = client.get(
        f"/api/v1/bulk/{job_id}/export.csv",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    
    # Verify injection sanitization
    csv_str = response.content.decode("utf-8")
    assert "'=RET-1" in csv_str # The equals sign should be prepended with a quote
