import sys
import os
sys.path.insert(0, os.path.abspath('shared'))
from retail_common.security.auth import create_access_token
from retail_common.config import settings

token = create_access_token({"sub": "admin", "role": "admin", "tenant_id": "demo"})
print("export ADMIN_JWT=" + token)
