import pytest
from fastapi import FastAPI, Depends, Request
from fastapi.testclient import TestClient
from shared.retail_common.security.auth import create_access_token
from shared.retail_common.metering import track_usage, write_usage_event, TIERS, get_usage_for_month
from shared.retail_common.db import SessionLocal
from sqlalchemy import text
from datetime import datetime

# Dummy setup
app = FastAPI()

def dummy_auth(request: Request):
    return {"tenant_id": "demo", "sub": "u_admin", "role": "admin"}

def dummy_auth_limited(request: Request):
    return {"tenant_id": "test_tenant", "sub": "u_test", "role": "admin"}

@app.get("/api/v1/dummy_unlimited")
@track_usage(event_type="api_call")
async def dummy_unlimited_route(user: dict = Depends(dummy_auth)):
    return {"status": "ok"}

@app.get("/api/v1/dummy_limited")
@track_usage(event_type="api_call")
async def dummy_limited_route(user: dict = Depends(dummy_auth_limited)):
    return {"status": "ok"}

client = TestClient(app)

def setup_db():
    db = SessionLocal()
    # Create the usage_events table manually for tests if not run via migrations
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS usage_events (
            event_id VARCHAR(50) PRIMARY KEY,
            tenant_id VARCHAR(50) NOT NULL,
            event_type VARCHAR(50) NOT NULL,
            api_call VARCHAR(100),
            llm_tokens INTEGER DEFAULT 0,
            store_id VARCHAR(50),
            quantity INTEGER DEFAULT 1,
            ts TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """))
    # Clear test tenant data
    db.execute(text("DELETE FROM usage_events WHERE tenant_id = 'test_tenant'"))
    db.commit()
    db.close()

def test_enterprise_limit():
    setup_db()
    # Demo tenant is mapped to Enterprise, which has unlimited calls (9999999)
    response = client.get("/api/v1/dummy_unlimited")
    assert response.status_code == 200
    
    # Check that a usage event was created
    db = SessionLocal()
    result = db.execute(text("SELECT COUNT(*) FROM usage_events WHERE tenant_id = 'demo'")).scalar()
    assert result > 0
    db.close()

def test_starter_limit_exceeded():
    setup_db()
    # Starter limit is 5000 API calls and 500 returns. 
    # Let's insert 501 returns manually to trip the limit.
    write_usage_event("test_tenant", "return_processed", quantity=501)
    
    # Next call should fail with 402
    response = client.get("/api/v1/dummy_limited")
    assert response.status_code == 402
    assert "Plan limit exceeded" in response.json()["detail"]

def test_api_calls_limit_exceeded():
    setup_db()
    # Let's insert 5001 api calls manually
    write_usage_event("test_tenant", "api_call", quantity=5001)
    
    response = client.get("/api/v1/dummy_limited")
    assert response.status_code == 402
    assert "API calls limit exceeded" in response.json()["detail"]
