from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from retail_common.schemas.bulk import BulkSummary, ProductRootCauseReport
from retail_common.schemas.rootcause import RootCauseCandidate, RootCauseOutput
from retail_common.taxonomy import ROOT_CAUSES

from app.tools.analyze_root_cause import analyze_root_cause as classify_root_cause
from app.tools.product_report import analyze_product_root_cause as generate_product_report
from app.tools.bulk_patterns import analyze_bulk_patterns as generate_bulk_summary


server = FastMCP(
    name="agent2-rootcause",
    host="0.0.0.0",
    port=8002,
    streamable_http_path="/mcp",
)


def _error_root_cause(product: str, issue: str, message: str) -> RootCauseOutput:
    return RootCauseOutput(
        product=product if isinstance(product, str) else "",
        issue=issue if isinstance(issue, str) else "",
        candidates=[RootCauseCandidate(label="unknown", score=0.0)],
        top_candidate="unknown",
        confidence=0.0,
        model_name="phase1_stub",
        notes=[message],
    )


def _validate_text(value: str, field_name: str) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return f"{field_name} must not be empty or whitespace-only"
    return None


def _validate_tenant(tenant_id: str) -> str | None:
    return _validate_text(tenant_id, "tenant_id")


@server.tool()
def analyze_root_cause(
    product: str,
    issue: str,
    product_id: str | None = None,
    customer_ref: str | None = None,
    tenant_id: str = "demo",
) -> RootCauseOutput:
    """Classify one return using the trained ML pipeline with LLM fallback."""
    validation_error = _validate_text(product, "product") or _validate_text(issue, "issue")
    validation_error = validation_error or _validate_tenant(tenant_id)
    if validation_error:
        return _error_root_cause(product, issue, validation_error)

    try:
        result = classify_root_cause(
            product=product,
            issue=issue,
            product_id=product_id,
            customer_ref=customer_ref,
            tenant_id=tenant_id,
        )
        # Ensure only valid taxonomy labels pass through and limit to 3 candidates
        result.candidates = [
            candidate for candidate in result.candidates if candidate.label in ROOT_CAUSES
        ][:3]
        return result
    except Exception as exc:
        return _error_root_cause(product, issue, f"root-cause analysis failed: {exc}")


@server.tool()
def analyze_product_root_cause(
    product_id: str,
    window_days: int = 90,
    tenant_id: str = "demo",
) -> ProductRootCauseReport:
    """Perform per-product root-cause investigation."""
    validation_error = _validate_text(product_id, "product_id") or _validate_tenant(tenant_id)
    if not isinstance(window_days, int) or isinstance(window_days, bool) or window_days <= 0:
        validation_error = validation_error or "window_days must be a positive integer"

    if validation_error:
        return ProductRootCauseReport(
            product_id=product_id if isinstance(product_id, str) else "",
            window_days=window_days if isinstance(window_days, int) and not isinstance(window_days, bool) else 0,
            total_returns=0,
            label_distribution={"unknown": 0},
            weekly_trend=[],
            suppliers=[],
            headline=validation_error,
            recommended_actions=[],
        )

    try:
        return generate_product_report(
            product_id=product_id,
            window_days=window_days,
            tenant_id=tenant_id,
        )
    except Exception as exc:
        return ProductRootCauseReport(
            product_id=product_id,
            window_days=window_days,
            total_returns=0,
            label_distribution={"unknown": 0},
            weekly_trend=[],
            suppliers=[],
            headline=f"product analysis failed: {exc}",
            recommended_actions=[],
        )


@server.tool()
def analyze_bulk_patterns(job_id: str, tenant_id: str = "demo") -> BulkSummary:
    """Perform bulk pattern analysis, issue clustering, and impact ranking."""
    validation_error = _validate_text(job_id, "job_id") or _validate_tenant(tenant_id)
    if validation_error:
        return BulkSummary(
            job_id=job_id if isinstance(job_id, str) else "",
            executive_summary=validation_error,
        )

    try:
        return generate_bulk_summary(
            job_id=job_id,
            tenant_id=tenant_id,
        )
    except Exception as exc:
        return BulkSummary(
            job_id=job_id,
            executive_summary=f"bulk analysis failed: {exc}",
        )


@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> Response:
    del request
    return JSONResponse({"status": "ok", "service": "agent2-rootcause"})


if __name__ == "__main__":
    import os
    import uvicorn
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    from contextlib import asynccontextmanager
    from shared.retail_common.config import settings
    
    port = int(os.getenv("AGENT2_PORT", "8002"))
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        _ = server.streamable_http_app()
        async with server.session_manager.run():
            yield
            
    app = FastAPI(title="Agent 2 Root Cause", lifespan=lifespan)
    
    @app.middleware("http")
    async def verify_service_secret(request: Request, call_next):
        if request.url.path.startswith("/"):
            secret = request.headers.get("X-Service-Secret")
            if secret != settings.service_secret:
                return JSONResponse(status_code=403, content={"detail": "Invalid service secret"})
        return await call_next(request)
        
    app.mount("/mcp", server.streamable_http_app())
    
    uvicorn.run(app, host="0.0.0.0", port=port)