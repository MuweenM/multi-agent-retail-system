from pydantic import BaseModel, Field

class RootCauseCandidate(BaseModel):
    label: str
    score: float
    supporting_return_count: int = 0
    top_terms: list[str] = Field(default_factory=list)   # words that pushed this label up

class RootCauseOutput(BaseModel):
    product: str
    issue: str
    candidates: list[RootCauseCandidate]
    top_candidate: str
    confidence: float
    # v1.1 additions
    product_id: str | None = None
    supplier_id: str | None = None
    model_name: str = ""            # e.g. tfidf_logreg_v3, or llm_fallback
    model_version: str = ""
    is_emerging_spike: bool = False
    abuse_risk: float = 0.0         # 0..1, behavioural features only
    notes: list[str] = Field(default_factory=list)
