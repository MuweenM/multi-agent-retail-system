from pydantic import BaseModel, Field

class BulkRow(BaseModel):
    return_id: str = ""
    text: str
    order_id: str | None = None
    product_id: str | None = None
    customer_ref: str | None = None
    order_value_lkr: float | None = None
    purchase_date: str | None = None
    return_date: str | None = None
    store_id: str | None = None
    courier: str | None = None

class RowError(BaseModel):
    row: int
    field: str
    reason: str

class BulkJob(BaseModel):
    job_id: str
    status: str = "queued"          # queued | running | done | failed
    total: int = 0
    processed: int = 0
    failed: int = 0
    errors: list[RowError] = Field(default_factory=list)

class Finding(BaseModel):
    kind: str                       # root_cause | product | supplier | batch | cluster | spike
    title: str
    detail: str
    return_count: int = 0
    value_at_risk_lkr: float = 0.0
    p_value: float | None = None
    product_id: str | None = None
    supplier_id: str | None = None
    batch_id: str | None = None

class IssueCluster(BaseModel):
    cluster_id: int
    size: int
    top_terms: list[str]
    dominant_root_cause: str
    growth_vs_prev: float | None = None

class BulkSummary(BaseModel):
    job_id: str
    total: int = 0
    decisions: dict[str, int] = Field(default_factory=dict)
    by_root_cause: dict[str, int] = Field(default_factory=dict)
    findings: list[Finding] = Field(default_factory=list)
    clusters: list[IssueCluster] = Field(default_factory=list)
    needs_review: int = 0
    est_value_at_risk_lkr: float = 0.0
    executive_summary: str = ""

class ProductRootCauseReport(BaseModel):
    product_id: str
    window_days: int
    total_returns: int
    label_distribution: dict[str, int]
    weekly_trend: list[dict]        # {"week": "2026-W36", "counts": {label: n}}
    suppliers: list[Finding]        # concentration findings, with p_value
    headline: str
    recommended_actions: list[str]
