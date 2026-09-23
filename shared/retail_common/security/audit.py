import json
from sqlalchemy import text
from shared.retail_common.db import SessionLocal
from typing import List

def log_audit_event(
    tenant_id: str,
    user_id: str,
    action: str,
    entity_id: str,
    decision: str,
    models: List[str]
):
    """
    Log an event to the audit_log table.
    We explicitly DO NOT log raw text here.
    """
    db = SessionLocal()
    try:
        details = json.dumps({
            "decision": decision,
            "models_used": models
        })
        
        stmt = text("""
            INSERT INTO audit_log (tenant_id, user_id, action, entity_type, entity_id, details)
            VALUES (:tenant, :user, :action, 'return', :entity, :details)
        """)
        
        db.execute(stmt, {
            "tenant": tenant_id,
            "user": user_id,
            "action": action,
            "entity": entity_id,
            "details": details
        })
        db.commit()
    except Exception as e:
        db.rollback()
        # In a real app we'd log this internally, but we shouldn't fail the return processing
        pass
    finally:
        db.close()
