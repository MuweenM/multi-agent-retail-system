import time
from fastapi import Request, HTTPException, Depends
from typing import Dict, Any

from .auth import get_current_user

class TokenBucket:
    def __init__(self, capacity: int, fill_rate: float):
        self.capacity = capacity
        self.fill_rate = fill_rate
        self.tokens = capacity
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        time_passed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + time_passed * self.fill_rate)
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

# In-memory store: tenant_id:user_id -> TokenBucket
rate_limit_store: Dict[str, TokenBucket] = {}

def get_bucket(identifier: str) -> TokenBucket:
    if identifier not in rate_limit_store:
        # Default 60 requests per minute -> 1 request per second
        rate_limit_store[identifier] = TokenBucket(capacity=60, fill_rate=1.0)
    return rate_limit_store[identifier]

async def check_rate_limit(request: Request, user: Dict[str, Any] = Depends(get_current_user)):
    """Rate limit per user and tenant."""
    identifier = f"{user.get('tenant_id')}:{user.get('sub')}"
    bucket = get_bucket(identifier)
    
    if not bucket.consume(1):
        raise HTTPException(status_code=429, detail="Too many requests")

async def verify_content_length(request: Request):
    """Enforce body size limit (413 Payload Too Large)"""
    content_length = request.headers.get('content-length')
    if content_length and int(content_length) > 1048576: # 1MB limit for demo
        raise HTTPException(status_code=413, detail="Payload Too Large")
