"""
Agent 3 (Evidence / IR) output contract.

TODO (Agent 3 owner): confirm/adjust fields to match your retrieval output.
"""
from pydantic import BaseModel


class EvidenceItem(BaseModel):
    source_type: str        # TODO: "review" | "supplier_record" | "historical_return" | "inventory"
    source_id: str
    snippet: str
    relevance_score: float


class EvidenceOutput(BaseModel):
    query: str
    evidence: list[EvidenceItem]
    total_results: int
