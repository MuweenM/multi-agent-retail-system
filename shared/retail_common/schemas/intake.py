"""
Agent 1 (Intake) output contract.

TODO (Agent 1 owner):
- Fill in the fields below to match what your NLP extraction actually produces.
- Everyone else (Agent 2 onward) will rely on these exact field names, so
  agree on this in the team chat BEFORE changing it.
"""
from pydantic import BaseModel


class IntakeOutput(BaseModel):
    raw_text: str
    product: str          # TODO: extracted product name
    issue: str             # TODO: extracted issue/defect description
    intent: str             # TODO: e.g. "return" | "exchange" | "refund" | "complaint" | "unknown"
    sentiment: str           # TODO: e.g. "positive" | "neutral" | "negative"
    confidence: float = 0.0
