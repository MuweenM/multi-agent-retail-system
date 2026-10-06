import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
from retail_common.security.auth import create_access_token
token = create_access_token(data={"sub": "u_admin", "role": "admin", "tenant_id": "demo"})
print(f"ADMIN_JWT={token}")
