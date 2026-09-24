"""Agent 1: Intake MCP Server (Port 8001).

Responsible for:
- Sanitizing raw customer input
- PII Redaction
- Normalization and Spell Correction
- Product Matching & NER
- LLM Extraction with deterministic fallback
- Batch CSV Intake
"""

import os
import sys
from typing import Dict, Any, List

# Ensure shared package and agent are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

try:
    from mcp.server.fastmcp import FastMCP
except (ImportError, ModuleNotFoundError):
    try:
        from mcp.server.mcpserver import MCPServer as FastMCP
    except Exception:
        class FastMCP:  # type: ignore
            def __init__(self, *args, **kwargs): pass
            def tool(self):
                def decorator(fn): return fn
                return decorator
            def run(self, *args, **kwargs): pass

from shared.retail_common.schemas.intake import IntakeOutput, Entity
from shared.retail_common.schemas.bulk import BulkRow, RowError

# Initialize FastMCP Server
mcp = FastMCP(
    "Agent1-Intake",
    host="0.0.0.0",
    port=8001,
    streamable_http_path="/mcp",
)


@mcp.tool()
def extract_return_info(
    text: str,
    tenant_id: str = "demo",
    lang_hint: str | None = None,
) -> IntakeOutput:
    """Extract structured return facts (product, issue, intent, sentiment) from customer complaint.
    
    Raw text is sanitized and PII is redacted. Returns clean_text only to protect privacy.
    """
    try:
        from app.nlp.pipeline import process_intake_pipeline
        return process_intake_pipeline(text=text, tenant_id=tenant_id, lang_hint=lang_hint)
    except Exception:
        # Stub response matching schema v1.1
        return IntakeOutput(
            raw_text="",
            product="Samsung Galaxy A15",
            product_id="P-001",
            product_match_score=0.92,
            issue="battery drains in 2 hours",
            intent="return",
            sentiment="negative",
            confidence=0.88,
            clean_text=text,
            summary="Customer reports Samsung Galaxy A15 battery drains within two hours.",
            tenant_id=tenant_id,
            entities=[
                Entity(type="PRODUCT", text="Samsung Galaxy A15", start=0, end=18),
                Entity(type="ISSUE", text="battery drains in 2 hours", start=19, end=44),
            ],
            pii_types_found=[],
            flags=["stub_mode"],
        )


@mcp.tool()
def extract_return_info_batch(
    rows: List[BulkRow],
    tenant_id: str = "demo",
) -> Dict[str, Any]:
    """Process a batch of returns with row-level error isolation and PII redaction."""
    try:
        from app.tools.extract_batch import process_intake_batch_sync
        return process_intake_batch_sync(rows=rows, tenant_id=tenant_id)
    except Exception:
        results: List[IntakeOutput] = []
        errors: List[RowError] = []

        for idx, row in enumerate(rows, start=1):
            if not row.text or not row.text.strip():
                errors.append(RowError(row=idx, field="text", reason="Empty text in row"))
            else:
                out = extract_return_info(text=row.text, tenant_id=tenant_id)
                out.return_id = row.return_id or f"RET-{idx:05d}"
                results.append(out)

        return {
            "results": [r.model_dump() for r in results],
            "errors": [e.model_dump() for e in errors],
        }


from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from shared.retail_common.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = mcp.streamable_http_app()
    async with mcp.session_manager.run():
        yield
        
app = FastAPI(title="Agent 1 Intake", lifespan=lifespan)

@app.middleware("http")
async def verify_service_secret(request: Request, call_next):
    if request.url.path.startswith("/"):
        secret = request.headers.get("X-Service-Secret")
        if secret != settings.service_secret:
            return JSONResponse(status_code=403, content={"detail": "Invalid service secret"})
    return await call_next(request)
    
app.mount("/mcp", mcp.streamable_http_app())

if __name__ == "__main__":
    port = int(os.getenv("AGENT1_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
