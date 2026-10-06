from fastapi import Depends, HTTPException
from typing import List, Dict, Any
from .auth import get_current_user

class RequireRole:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = user.get("role")
        if user_role not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Operation not permitted")
        return user
