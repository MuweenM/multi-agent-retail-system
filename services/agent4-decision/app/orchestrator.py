
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import uuid
from typing import Optional
from shared.retail_common.config import settings
from shared.retail_common.schemas import DecisionOutput, IntakeOutput, RootCauseOutput, EvidenceOutput
from shared.retail_common.logging_config import get_logger
from .mcp_clients import call_agent

logger = get_logger("orchestrator")

async def run_orchestrator(return_text: str, tenant_id: str, order_id: Optional[str] = None) -> DecisionOutput:
    """
    v0 orchestrator: calls Agent 1, 2, 3 in sequence, handles errors gracefully, 
    and returns a final DecisionOutput.
    """
    trace = []
    
    # 1. Agent 1 - Intake
    intake_data, step1 = await call_agent(
        url=settings.agent1_mcp_url,
        tool="extract_return_info",
        arguments={"text": return_text, "tenant_id": tenant_id},
        agent_name="agent1-intake"
    )
    trace.append(step1)
    
    product = "Unknown Product"
    issue = "Unknown Issue"
    if step1.ok and intake_data:
        try:
            intake = IntakeOutput.model_validate(intake_data)
            product = intake.product
            issue = intake.issue
        except Exception as e:
            logger.error(f"Error parsing Agent 1 output: {e}")
            step1.ok = False
            step1.note = "failed to parse IntakeOutput"

    # 2. Agent 2 - Root Cause
    rc_data, step2 = await call_agent(
        url=settings.agent2_mcp_url,
        tool="analyze_root_cause",
        arguments={"product": product, "issue": issue},
        agent_name="agent2-rootcause"
    )
    trace.append(step2)
    
    root_cause = "unknown"
    confidence = 0.0
    if step2.ok and rc_data:
        try:
            rc = RootCauseOutput.model_validate(rc_data)
            root_cause = rc.top_candidate
            confidence = rc.confidence
        except Exception as e:
            logger.error(f"Error parsing Agent 2 output: {e}")
            step2.ok = False
            step2.note = "failed to parse RootCauseOutput"

    # 3. Agent 3 - Retrieval
    query = f"{product} {issue}"
    ev_data, step3 = await call_agent(
        url=settings.agent3_mcp_url,
        tool="retrieve_evidence",
        arguments={"query": query, "top_k": 3, "method": "hybrid"},
        agent_name="agent3-retrieval"
    )
    trace.append(step3)
    
    evidence_summary = "No evidence retrieved."
    if step3.ok and ev_data:
        try:
            ev = EvidenceOutput.model_validate(ev_data)
            if ev.evidence:
                evidence_summary = f"Found {ev.total_results} evidence items. Top snippet: {ev.evidence[0].snippet}"
        except Exception as e:
            logger.error(f"Error parsing Agent 3 output: {e}")
            step3.ok = False
            step3.note = "failed to parse EvidenceOutput"

    # 4. Final Decision Generation (v0 template)
    decision = "escalate"
    requires_human_review = True
    if confidence > 0.8:
        decision = "approve"
        requires_human_review = False
        
    recommendation = f"Based on '{issue}', root cause seems to be '{root_cause}'. Recommendation: {decision}."

    return DecisionOutput(
        root_cause=root_cause,
        confidence=confidence,
        evidence_summary=evidence_summary,
        recommendation=recommendation,
        requires_human_review=requires_human_review,
        return_id=str(uuid.uuid4()),
        decision=decision,
        agent_trace=trace,
        reasoning_steps=[
            f"Extracted info: {product} / {issue}",
            f"Determined root cause: {root_cause}",
            f"Evidence: {evidence_summary}"
        ]
    )
