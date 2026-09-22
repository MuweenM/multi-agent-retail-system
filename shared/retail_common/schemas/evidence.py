from pydantic import BaseModel, Field

class EvidenceItem(BaseModel):
    source_type: str                # see SOURCE_TYPES
    source_id: str
    snippet: str
    relevance_score: float
    # v1.1 additions
    title: str = ""
    method: str = ""                # tfidf | bm25 | dense | hybrid
    matched_terms: list[str] = Field(default_factory=list)
    zone: str = ""                  # title | body | supplier_notes
    label_hint: str | None = None   # root-cause label this passage supports, if known
    metadata: dict[str, str] = Field(default_factory=dict)

class EvidenceOutput(BaseModel):
    query: str
    evidence: list[EvidenceItem]
    total_results: int
    # v1.1 additions
    corrected_query: str = ""
    expanded_terms: list[str] = Field(default_factory=list)
    method: str = "hybrid"
    latency_ms: int = 0
