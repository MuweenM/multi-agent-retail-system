import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
import uuid
import io
import csv
import json

from retail_common.schemas import DecisionOutput
from retail_common.logging_config import get_logger
from retail_common.db import SessionLocal
from sqlalchemy import text

from retail_common.security.auth import verify_password, create_access_token, get_current_user
from retail_common.security.rbac import RequireRole
from retail_common.security.ratelimit import check_rate_limit, verify_content_length
from retail_common.security.audit import log_audit_event
from retail_common.security.encryption import encrypt_text
from retail_common.metering import track_usage, write_usage_event, get_usage_for_month, get_tenant_tier, TIERS
from retail_common.bulk_io import load_and_validate_csv, sanitize_csv_cell
from datetime import datetime

from .orchestrator import run_orchestrator
from .jobs import process_bulk_job

logger = get_logger("server")

# 1. MCP Setup
mcp = FastMCP("Agent4 Decision")

@mcp.tool()
async def generate_final_recommendation(return_text: str, tenant_id: str = "demo", order_id: Optional[str] = None) -> str:
    """
    Analyzes a return request and generates a final decision using the agent swarm.
    """
    logger.info(f"Generating recommendation for tenant {tenant_id}, order {order_id}")
    result = await run_orchestrator(return_text=return_text, tenant_id=tenant_id, order_id=order_id)
    return result.model_dump_json()

# 2. FastAPI Setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = mcp.streamable_http_app()
    async with mcp.session_manager.run():
        yield

app = FastAPI(title="Agent 4 Decision API", lifespan=lifespan)

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Mount MCP and REST routes
app.mount("/mcp", mcp.streamable_http_app())

@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "agent4-decision"}


# --- Auth Routes ---
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/v1/auth/login")
async def login(req: LoginRequest):
    db = SessionLocal()
    try:
        stmt = text("SELECT user_id, tenant_id, role, password_hash FROM users WHERE email = :email")
        result = db.execute(stmt, {"email": req.email}).fetchone()
        
        if not result:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        user_id, tenant_id, role, password_hash = result
        
        if not verify_password(req.password, password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        access_token = create_access_token(
            data={"sub": user_id, "tenant_id": tenant_id, "role": role}
        )
        return {"access_token": access_token, "token_type": "bearer"}
    finally:
        db.close()


# --- Returns API ---
class ReturnRequest(BaseModel):
    text: str
    order_id: Optional[str] = None

@app.post(
    "/api/v1/returns", 
    response_model=DecisionOutput,
    dependencies=[Depends(verify_content_length), Depends(check_rate_limit)]
)
@track_usage(event_type="api_call")
async def process_return(
    req: ReturnRequest,
    user: Dict[str, Any] = Depends(RequireRole(["reviewer", "admin"]))
):
    tenant_id = user["tenant_id"]
    user_id = user["sub"]
    
    # 1. Run the swarm
    result = await run_orchestrator(return_text=req.text, tenant_id=tenant_id, order_id=req.order_id)
    
    # 2. Save encrypted return payload to DB
    db = SessionLocal()
    try:
        raw_text_enc = encrypt_text(req.text)
        customer_ref_enc = encrypt_text(req.order_id) if req.order_id else None
        
        stmt = text("""
            INSERT INTO returns (return_id, tenant_id, raw_text_enc, customer_ref_hash, root_cause_pred, issue, order_value_lkr)
            VALUES (:id, :tenant, :raw_enc, :ref_enc, :rc, :issue, :order_val)
        """)
        db.execute(stmt, {
            "id": result.return_id,
            "tenant": tenant_id,
            "raw_enc": raw_text_enc,
            "ref_enc": customer_ref_enc,
            "rc": result.root_cause,
            "issue": req.text[:100],  # snippet
            "order_val": 1000.0  # mocked for now
        })
        
        # Also store decision
        stmt_dec = text("""
            INSERT INTO decisions (decision_id, tenant_id, return_id, root_cause, confidence, evidence_summary, recommendation, decision, requires_human_review)
            VALUES (:did, :tenant, :rid, :rc, :conf, :ev_sum, :rec, :dec, :rhr)
        """)
        db.execute(stmt_dec, {
            "did": str(uuid.uuid4()),
            "tenant": tenant_id,
            "rid": result.return_id,
            "rc": result.root_cause,
            "conf": result.confidence,
            "ev_sum": result.evidence_summary,
            "rec": result.recommendation,
            "dec": result.decision,
            "rhr": result.requires_human_review
        })
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save return to DB: {e}")
    finally:
        db.close()
        
    # 3. Audit Logging and Usage
    models_used = [s.agent for s in result.agent_trace]
    log_audit_event(tenant_id, user_id, "process_return", result.return_id, result.decision, models_used)
    
    # Write usage for processing a return
    write_usage_event(tenant_id, "return_processed", quantity=1)
    # Mock some LLM tokens for now
    write_usage_event(tenant_id, "llm_tokens", llm_tokens=1250 * len(models_used))
    
    return result

@app.get("/api/v1/usage")
async def get_usage(
    user: Dict[str, Any] = Depends(RequireRole(["viewer", "reviewer", "admin"]))
):
    tenant_id = user["tenant_id"]
    now = datetime.utcnow()
    usage = get_usage_for_month(tenant_id, now.year, now.month)
    tier_id = get_tenant_tier(tenant_id)
    tier = TIERS.get(tier_id, TIERS["starter"])
    
    # Calculate estimated invoice
    estimated_invoice = tier["price_per_month"]
    if usage["total_returns"] > tier["included_returns"]:
        extra_returns = usage["total_returns"] - tier["included_returns"]
        estimated_invoice += (extra_returns * tier["price_per_return"])
        
    return {
        "tenant_id": tenant_id,
        "month": f"{now.year}-{now.month:02d}",
        "tier": tier["name"],
        "usage": usage,
        "plan_limits": {
            "included_returns": tier["included_returns"],
            "included_api_calls": tier["included_api_calls"]
        },
        "estimated_invoice_lkr": estimated_invoice
    }

@app.post("/api/v1/bulk")
@track_usage(event_type="api_call")
async def process_bulk(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(RequireRole(["reviewer", "admin"]))
):
    tenant_id = user["tenant_id"]
    user_id = user["sub"]
    
    content = await file.read()
    valid_rows, errors = load_and_validate_csv(content)
    
    if not valid_rows:
        return {"status": "validation_failed", "errors": [e.model_dump() for e in errors]}
        
    job_id = f"bulk-{uuid.uuid4().hex[:8]}"
    
    # Run in background
    background_tasks.add_task(process_bulk_job, job_id, tenant_id, user_id, valid_rows)
    
    return {"status": "accepted", "job_id": job_id, "rows": len(valid_rows), "errors": [e.model_dump() for e in errors]}

@app.get("/api/v1/bulk/{job_id}")
async def get_bulk_status(
    job_id: str,
    user: Dict[str, Any] = Depends(RequireRole(["viewer", "reviewer", "admin"]))
):
    db = SessionLocal()
    try:
        stmt = text("SELECT status, total_rows, processed_rows, failed_rows, summary_json FROM bulk_jobs WHERE job_id = :job_id AND tenant_id = :tenant_id")
        result = db.execute(stmt, {"job_id": job_id, "tenant_id": user["tenant_id"]}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Job not found")
            
        return {
            "job_id": job_id,
            "status": result.status,
            "total_rows": result.total_rows,
            "processed_rows": result.processed_rows,
            "failed_rows": result.failed_rows,
            "summary": result.summary_json if result.summary_json else None
        }
    finally:
        db.close()

@app.get("/api/v1/bulk/{job_id}/results")
async def get_bulk_results(
    job_id: str,
    page: int = 1,
    size: int = 50,
    user: Dict[str, Any] = Depends(RequireRole(["viewer", "reviewer", "admin"]))
):
    db = SessionLocal()
    try:
        offset = (page - 1) * size
        stmt = text("""
            SELECT d.return_id, d.decision, d.root_cause, d.confidence, d.recommendation
            FROM decisions d
            WHERE d.bulk_job_id = :job_id AND d.tenant_id = :tenant_id
            LIMIT :limit OFFSET :offset
        """)
        results = db.execute(stmt, {"job_id": job_id, "tenant_id": user["tenant_id"], "limit": size, "offset": offset}).fetchall()
        
        return {
            "job_id": job_id,
            "page": page,
            "size": size,
            "results": [dict(r._mapping) for r in results]
        }
    finally:
        db.close()

@app.get("/api/v1/bulk/{job_id}/export.csv")
async def export_bulk_csv(
    job_id: str,
    user: Dict[str, Any] = Depends(RequireRole(["viewer", "reviewer", "admin"]))
):
    db = SessionLocal()
    try:
        stmt = text("""
            SELECT d.return_id, d.decision, d.root_cause, d.confidence, d.recommendation
            FROM decisions d
            WHERE d.bulk_job_id = :job_id AND d.tenant_id = :tenant_id
        """)
        results = db.execute(stmt, {"job_id": job_id, "tenant_id": user["tenant_id"]}).fetchall()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["return_id", "decision", "root_cause", "confidence", "recommendation"])
        
        for row in results:
            writer.writerow([
                sanitize_csv_cell(row.return_id),
                sanitize_csv_cell(row.decision),
                sanitize_csv_cell(row.root_cause),
                row.confidence,
                sanitize_csv_cell(row.recommendation)
            ])
            
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=results_{job_id}.csv"}
        )
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("AGENT4_PORT", "8004"))
    uvicorn.run("app.server:app", host="0.0.0.0", port=port)
