"""
Agent 2 (Root Cause Analysis) output contract.

TODO (Agent 2 owner): confirm/adjust fields to match your clustering logic.
"""
from pydantic import BaseModel


class RootCauseCandidate(BaseModel):
    label: str              # TODO: e.g. "manufacturing defect"
    score: float
    supporting_return_count: int = 0


class RootCauseOutput(BaseModel):
    product: str
    issue: str
    candidates: list[RootCauseCandidate]
    top_candidate: str
    confidence: float
