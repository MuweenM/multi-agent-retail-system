import asyncio
import json
import os
import uuid
from typing import List
from retail_common.schemas.bulk import BulkRow
from retail_common.db import SessionLocal
from retail_common.logging_config import get_logger
from sqlalchemy import text
from app.orchestrator import run_orchestrator
from retail_common.security.encryption import encrypt_text
from retail_common.metering import write_usage_event
from app.mcp_clients import call_agent

logger = get_logger("jobs")

LLM_MAX_CALLS_PER_BULK_JOB = int(os.getenv("LLM_MAX_CALLS_PER_BULK_JOB", "50"))

async def _process_single_row(
    row: BulkRow, 
    tenant_id: str, 
    user_id: str, 
    job_id: str, 
    semaphore: asyncio.Semaphore,
    llm_calls_made: list # Using a list as a mutable reference for the counter
) -> bool:
    async with semaphore:
        try:
            # We want to skip LLM synthesis if we're out of budget.
            # We pass the budget state to the orchestrator.
            budget_remaining = LLM_MAX_CALLS_PER_BULK_JOB - llm_calls_made[0]
            
            result = await run_orchestrator(
                return_text=row.text, 
                tenant_id=tenant_id, 
                order_id=row.order_id,
                is_bulk=True,
                budget_remaining=budget_remaining
            )
            
            # If the orchestrator actually made an LLM call (we'll assume it sets a flag or we can just infer)
            # We will handle the exact accounting inside orchestrator, but here we can just update our local counter 
            # if we wanted to. To keep it simple, we let orchestrator check the shared budget object, 
            # but since orchestrator is stateless per request, passing the mutable list works!
            
            if "Synthesizing evidence via LLM..." in result.reasoning_steps:
                llm_calls_made[0] += 1
                
            db = SessionLocal()
            try:
                raw_text_enc = encrypt_text(row.text)
                customer_ref_enc = encrypt_text(row.customer_ref) if row.customer_ref else None
                
                stmt = text("""
                    INSERT INTO returns (return_id, bulk_job_id, tenant_id, raw_text_enc, customer_ref_hash, root_cause_pred, issue, order_value_lkr)
                    VALUES (:id, :job, :tenant, :raw_enc, :ref_enc, :rc, :issue, :order_val)
                    ON CONFLICT (return_id) DO NOTHING
                """)
                db.execute(stmt, {
                    "id": result.return_id,
                    "job": job_id,
                    "tenant": tenant_id,
                    "raw_enc": raw_text_enc,
                    "ref_enc": customer_ref_enc,
                    "rc": result.root_cause,
                    "issue": row.text[:100],
                    "order_val": row.order_value_lkr
                })
                
                stmt_dec = text("""
                    INSERT INTO decisions (decision_id, bulk_job_id, tenant_id, return_id, root_cause, confidence, evidence_summary, recommendation, decision, requires_human_review)
                    VALUES (:did, :job, :tenant, :rid, :rc, :conf, :ev_sum, :rec, :dec, :rhr)
                """)
                db.execute(stmt_dec, {
                    "did": str(uuid.uuid4()),
                    "job": job_id,
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
                
                write_usage_event(tenant_id, "bulk_row", quantity=1)
                
            except Exception as e:
                db.rollback()
                logger.error(f"Failed saving bulk row {row.return_id}: {e}")
                return False
            finally:
                db.close()
                
            return True
        except Exception as e:
            logger.error(f"Error processing row {row.return_id}: {e}")
            return False

async def process_bulk_job(job_id: str, tenant_id: str, user_id: str, rows: List[BulkRow]):
    logger.info(f"Starting bulk job {job_id} for tenant {tenant_id} with {len(rows)} rows.")
    
    db = SessionLocal()
    try:
        stmt = text("""
            INSERT INTO bulk_jobs (job_id, tenant_id, user_id, status, total_rows)
            VALUES (:id, :tid, :uid, 'processing', :total)
        """)
        db.execute(stmt, {"id": job_id, "tid": tenant_id, "uid": user_id, "total": len(rows)})
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Could not create bulk job {job_id}: {e}")
        db.close()
        return
        
    semaphore = asyncio.Semaphore(8)
    llm_calls_made = [0]
    
    tasks = []
    for row in rows:
        tasks.append(_process_single_row(row, tenant_id, user_id, job_id, semaphore, llm_calls_made))
        
    results = await asyncio.gather(*tasks)
    
    processed = sum(1 for r in results if r)
    failed = len(rows) - processed
    
    # Run Agent 2 bulk patterns
    bulk_patterns = "Pattern analysis unavailable."
    agent2_url = os.getenv("AGENT2_URL", "http://agent2-rootcause:8002/mcp")
    try:
        b_res, _ = await call_agent(agent2_url, "analyze_bulk_patterns", {"job_id": job_id, "tenant_id": tenant_id}, "Agent2")
        if b_res and "executive_summary" in b_res:
            bulk_patterns = b_res["executive_summary"]
    except Exception as e:
        logger.error(f"Failed to call analyze_bulk_patterns: {e}")
        
    # Generate final summary locally (mocked LLM call for now, could use a real model if hooked up)
    # The prompt explicitly asks for aggregate numbers only.
    summary_text = f"Bulk processing complete. Total: {len(rows)}, Processed: {processed}, Failed: {failed}. Trends: {bulk_patterns[:200]}"
    
    summary_json = {
        "total_processed": processed,
        "failed": failed,
        "executive_summary": summary_text
    }
    
    try:
        stmt = text("""
            UPDATE bulk_jobs 
            SET status = 'completed', processed_rows = :p, failed_rows = :f, summary_json = :s, updated_at = CURRENT_TIMESTAMP
            WHERE job_id = :id
        """)
        db.execute(stmt, {"p": processed, "f": failed, "s": json.dumps(summary_json), "id": job_id})
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to finalize bulk job {job_id}: {e}")
    finally:
        db.close()
        
    logger.info(f"Completed bulk job {job_id}")
