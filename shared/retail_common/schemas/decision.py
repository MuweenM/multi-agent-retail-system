"""
Agent 4 (Decision & Prevention) output contract.

TODO (Agent 4 owner): confirm/adjust fields to match your recommendation output.
"""
from pydantic import BaseModel


class DecisionOutput(BaseModel):
    root_cause: str
    confidence: float
    evidence_summary: str
    recommendation: str
    requires_human_review: bool = False
