import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from retail_common.config import settings
from retail_common.schemas.evidence import EvidenceItem, EvidenceOutput
from retail_common.taxonomy import ROOT_CAUSES


def _agent3_port() -> int:
    value = getattr(settings, "AGENT3_PORT", None)
    if value is None:
        value = os.getenv("AGENT3_PORT", "8003")
    return int(value)


server = FastMCP(
    name="agent3-retrieval",
    host="0.0.0.0",
    port=_agent3_port(),
    streamable_http_path="/",
)


def _fake_evidence_items() -> list[EvidenceItem]:
    return [
        EvidenceItem(
            source_type="review",
            source_id="rev-7842",
            snippet="Customer review says the battery drains within 2 hours and the back panel gets unusually warm during use.",
            relevance_score=0.96,
            title="Battery drain complaint",
            method="hybrid",
            matched_terms=["battery", "drain", "warm"],
            zone="body",
            label_hint="quality_durability",
            metadata={"channel": "review", "sku": "SM-A15-128"},
        ),
        EvidenceItem(
            source_type="supplier_record",
            source_id="sup-2217",
            snippet="Supplier QA log: batch B12 power-management board showed elevated heat under load and premature cell discharge.",
            relevance_score=0.91,
            title="Supplier QA batch alert",
            method="hybrid",
            matched_terms=["power", "heat", "cell", "discharge"],
            zone="supplier_notes",
            label_hint="manufacturing_defect",
            metadata={"batch": "B12", "supplier": "BlueCell"},
        ),
        EvidenceItem(
            source_type="policy",
            source_id="pol-44",
            snippet="Return policy covers latent battery failures when the product overheats or fails to hold charge within the first 30 days.",
            relevance_score=0.87,
            title="Return eligibility guideline",
            method="hybrid",
            matched_terms=["battery", "overheat", "charge"],
            zone="title",
            label_hint="policy_abuse_suspected",
            metadata={"policy": "returns-2026", "jurisdiction": "LK"},
        ),
    ]


@server.tool()
def retrieve_evidence(
    query: str,
    top_k: int = 5,
    method: str = "hybrid",
    filters: dict | None = None,
    source_types: list[str] | None = None,
    tenant_id: str = "demo",
) -> EvidenceOutput:
    """Return a small set of fake evidence items for retrieval service stubs."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")

    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("query must not be empty")
    if len(normalized_query) > 300:
        raise ValueError("query must be 300 characters or fewer")

    if top_k is None:
        top_k = 5
    if not isinstance(top_k, int) or isinstance(top_k, bool):
        raise ValueError("top_k must be an integer")
    cap = min(max(top_k, 1), 20)

    items = _fake_evidence_items()
    if filters:
        items = [item for item in items if all(item.metadata.get(key) == value for key, value in filters.items() if key in item.metadata)]
    if source_types:
        items = [item for item in items if item.source_type in source_types]

    items = sorted(items, key=lambda item: item.relevance_score, reverse=True)[:cap]
    evidence = [
        EvidenceItem(
            source_type=item.source_type,
            source_id=item.source_id,
            snippet=item.snippet,
            relevance_score=item.relevance_score,
            title=item.title,
            method=method or "hybrid",
            matched_terms=item.matched_terms,
            zone=item.zone,
            label_hint=item.label_hint if item.label_hint in ROOT_CAUSES else None,
            metadata=item.metadata,
        )
        for item in items
    ]

    return EvidenceOutput(
        query=normalized_query,
        evidence=evidence,
        total_results=len(evidence),
        corrected_query=normalized_query,
        expanded_terms=["battery", "heat", "charge"],
        method=method or "hybrid",
        latency_ms=12,
    )


@server.tool()
def reindex_corpus(tenant_id: str = "demo") -> dict:
    """Admin-only corpus reindexing stub. Returns zeroed counts for now."""
    if not tenant_id or not isinstance(tenant_id, str):
        raise ValueError("tenant_id must be a non-empty string")
    return {
        "tenant_id": tenant_id,
        "documents_indexed": 0,
        "documents_updated": 0,
        "documents_deleted": 0,
        "errors": 0,
    }


@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> Response:
    del request
    return JSONResponse({"status": "ok", "service": "agent3-retrieval"})


from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from retail_common.config import settings

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

if __name__ == "__main__":
    import uvicorn
    port = _agent3_port()
    uvicorn.run(app, host="0.0.0.0", port=port)
