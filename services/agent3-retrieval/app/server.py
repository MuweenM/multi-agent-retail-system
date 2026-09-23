import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from mcp.server.fastmcp import FastMCP
from shared.retail_common.schemas.evidence import EvidenceOutput, EvidenceItem

server = FastMCP(
    name="agent3-retrieval",
    host="0.0.0.0",
    port=8003,
    streamable_http_path="/mcp",
)

@server.tool()
def retrieve_evidence(
    query: str,
    top_k: int = 3,
    method: str = "hybrid"
) -> EvidenceOutput:
    """Retrieve evidence from the knowledge base."""
    # Stub implementation for Phase 1
    return EvidenceOutput(
        query=query,
        evidence=[
            EvidenceItem(
                source_type="doc",
                source_id="doc-123",
                snippet="battery drain issue reported for this product.",
                relevance_score=0.95
            )
        ],
        total_results=1,
        method=method
    )

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    from contextlib import asynccontextmanager
    from shared.retail_common.config import settings
    
    port = int(os.getenv("AGENT3_PORT", "8003"))
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _ = server.streamable_http_app()
        async with server.session_manager.run():
            yield
            
    app = FastAPI(title="Agent 3 Retrieval", lifespan=lifespan)
    
    @app.middleware("http")
    async def verify_service_secret(request: Request, call_next):
        if request.url.path.startswith("/"):
            secret = request.headers.get("X-Service-Secret")
            if secret != settings.service_secret:
                return JSONResponse(status_code=403, content={"detail": "Invalid service secret"})
        return await call_next(request)
        
    app.mount("/mcp", server.streamable_http_app())
    
    uvicorn.run(app, host="0.0.0.0", port=port)
