import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
from shared.retail_common.schemas import DecisionOutput
from shared.retail_common.logging_config import get_logger
from .orchestrator import run_orchestrator

logger = get_logger("server")

# 1. MCP Setup
mcp = FastMCP("Agent4 Decision")

@mcp.tool()
async def generate_final_recommendation(return_text: str, tenant_id: str = "demo", order_id: Optional[str] = None) -> str:
    """
    Analyzes a return request and generates a final decision using the agent swarm.
    (Note: FastMCP tools currently serialize return models to JSON string automatically,
    but returning the Pydantic model directly works in recent versions if supported).
    """
    logger.info(f"Generating recommendation for tenant {tenant_id}, order {order_id}")
    result = await run_orchestrator(return_text=return_text, tenant_id=tenant_id, order_id=order_id)
    return result.model_dump_json()

# 2. FastAPI Setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the Starlette app to create the session manager
    _ = mcp.streamable_http_app()
    # Now mcp.session_manager is available, we must enter its context
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

class ReturnRequest(BaseModel):
    text: str
    order_id: Optional[str] = None
    tenant_id: str = "demo"

@app.post("/api/v1/returns", response_model=DecisionOutput)
async def process_return(req: ReturnRequest):
    return await run_orchestrator(return_text=req.text, tenant_id=req.tenant_id, order_id=req.order_id)

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("AGENT4_PORT", "8004"))
    uvicorn.run("app.server:app", host="0.0.0.0", port=port)
