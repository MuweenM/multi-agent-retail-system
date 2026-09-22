from pydantic import BaseModel, Field


class AgentStep(BaseModel):
    agent: str
    tool: str
    ok: bool
    latency_ms: int
    note: str = ""


class DecisionOutput(BaseModel):
    root_cause: str
    confidence: float
    evidence_summary: str
    recommendation: str
    requires_human_review: bool = False
    # v1.1 additions
    return_id: str = ""
    decision: str = "escalate"      # approve | reject | escalate | request_info
    citations: list[str] = Field(default_factory=list)          # evidence source_ids used in the summary
    reasoning_steps: list[str] = Field(default_factory=list)    # plain-English trace shown in the UI
    human_review_reasons: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    agent_trace: list[AgentStep] = Field(default_factory=list)
    evidence_support: float = 0.0
    disclaimer: str = "AI suggestion. A person must confirm before any action."
