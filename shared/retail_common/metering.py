import uuid
from typing import Optional, Any, Callable
from functools import wraps
from datetime import datetime
from fastapi import Request, HTTPException
from retail_common.db import SessionLocal
from sqlalchemy import text

TIERS = {
    "pay_as_you_go": {
        "name": "Pay as you go",
        "included_returns": 0,
        "included_api_calls": 0,
        "price_per_return": 15,
        "price_per_month": 0
    },
    "starter": {
        "name": "Starter",
        "included_returns": 500,
        "included_api_calls": 5000,
        "price_per_return": 15,
        "price_per_month": 6000
    },
    "business": {
        "name": "Business",
        "included_returns": 3000,
        "included_api_calls": 50000,
        "price_per_return": 6,
        "price_per_month": 22500
    },
    "enterprise": {
        "name": "Enterprise",
        "included_returns": 9999999,
        "included_api_calls": 99999999,
        "price_per_return": 0,
        "price_per_month": 0
    }
}

def get_tenant_tier(tenant_id: str) -> str:
    # In a real system, this would query a tenants table. 
    # For now, we'll default everyone to "starter" except "demo" which gets "enterprise"
    if tenant_id == "demo":
        return "enterprise"
    return "starter"

def get_usage_for_month(tenant_id: str, year: int, month: int) -> dict:
    db = SessionLocal()
    try:
        # Get start and end of month as datetime objects
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
            
        stmt = text("""
            SELECT event_type, SUM(quantity) as total_qty, SUM(llm_tokens) as total_tokens
            FROM usage_events
            WHERE tenant_id = :tenant_id 
              AND ts >= :start_date 
              AND ts < :end_date
            GROUP BY event_type
        """)
        
        results = db.execute(stmt, {
            "tenant_id": tenant_id, 
            "start_date": start_date, 
            "end_date": end_date
        }).fetchall()
        
        usage = {
            "return_processed": 0,
            "bulk_row": 0,
            "api_call": 0,
            "llm_tokens": 0
        }
        
        for row in results:
            event_type = row.event_type
            qty = row.total_qty or 0
            tokens = row.total_tokens or 0
            
            if event_type in usage:
                usage[event_type] = qty
            usage["llm_tokens"] += tokens
                
        # Total returns = single returns + bulk rows
        usage["total_returns"] = usage["return_processed"] + usage["bulk_row"]
        return usage
    finally:
        db.close()

def check_plan_limits(tenant_id: str):
    tier_id = get_tenant_tier(tenant_id)
    tier = TIERS.get(tier_id, TIERS["starter"])
    
    now = datetime.utcnow()
    usage = get_usage_for_month(tenant_id, now.year, now.month)
    
    # Check returns limit
    if usage["total_returns"] >= tier["included_returns"] and tier["included_returns"] > 0:
        raise HTTPException(
            status_code=402, 
            detail=f"Plan limit exceeded. You have processed {usage['total_returns']} returns this month. "
                   f"Your {tier['name']} plan includes {tier['included_returns']} returns. "
                   f"Please upgrade your plan at /billing/upgrade to continue."
        )
        
    # Check API limit
    if usage["api_call"] >= tier["included_api_calls"] and tier["included_api_calls"] > 0:
        raise HTTPException(
            status_code=402, 
            detail=f"API calls limit exceeded for {tier['name']} plan. Please upgrade."
        )

def write_usage_event(
    tenant_id: str, 
    event_type: str, 
    api_call: Optional[str] = None, 
    llm_tokens: int = 0, 
    store_id: Optional[str] = None, 
    quantity: int = 1
):
    db = SessionLocal()
    try:
        stmt = text("""
            INSERT INTO usage_events (event_id, tenant_id, event_type, api_call, llm_tokens, store_id, quantity)
            VALUES (:eid, :tid, :etype, :api, :tokens, :store, :qty)
        """)
        db.execute(stmt, {
            "eid": str(uuid.uuid4()),
            "tid": tenant_id,
            "etype": event_type,
            "api": api_call,
            "tokens": llm_tokens,
            "store": store_id,
            "qty": quantity
        })
        db.commit()
    except Exception as e:
        db.rollback()
        # In a real app we might log this, but we don't want metering failure to break the app completely
        print(f"Failed to write usage event: {e}")
    finally:
        db.close()

def track_usage(event_type: str = "api_call"):
    """
    Decorator to track API usage and check limits before execution.
    Requires the wrapped function to have `user: Dict[str, Any]` injected by RequireRole.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user dict to get tenant_id
            user = kwargs.get('user')
            if not user or not isinstance(user, dict) or 'tenant_id' not in user:
                # If we can't find the tenant, we just proceed (or we could fail securely)
                return await func(*args, **kwargs)
                
            tenant_id = user['tenant_id']
            
            # 1. Enforce Plan Limits
            check_plan_limits(tenant_id)
            
            # 2. Write the API call event
            api_path = func.__name__ # simple fallback
            
            # If the request is passed, we can extract the path
            request: Optional[Request] = kwargs.get('request')
            if request:
                api_path = request.url.path
                
            write_usage_event(
                tenant_id=tenant_id,
                event_type=event_type,
                api_call=api_path,
                quantity=1
            )
            
            # 3. Execute the function
            return await func(*args, **kwargs)
        return wrapper
    return decorator
