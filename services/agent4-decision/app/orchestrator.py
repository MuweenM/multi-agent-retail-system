
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

import uuid
import json
import os
from typing import Optional, List

from shared.retail_common.config import settings
from shared.retail_common.schemas import DecisionOutput, IntakeOutput, RootCauseOutput, EvidenceOutput, AgentStep
from shared.retail_common.logging_config import get_logger
from shared.retail_common.llm_client import call_llm
from .mcp_clients import call_agent
from .policy import apply_policy

logger = get_logger("orchestrator")

SYNTHESIZE_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "synthesize.md")

async def run_orchestrator(return_text: str, tenant_id: str, order_id: Optional[str] = None) -> DecisionOutput:
    """
    v1 orchestrator: Explicit state machine with graceful degradation, reflection, and policy mapping.
    """
    trace: List[AgentStep] = []
    reasoning: List[str] = []
    risk_flags: List[str] = []
    
    # Defaults
    intake_confidence = 0.0
    product = "unknown"
    product_id = None
    issue = "unknown"
    flags = []
    
    rc_confidence = 0.0
    abuse_risk = 0.0
    root_cause = "unknown"
    top_candidates = []
    
    evidence_support = 0.0
    evidence_summary = "No evidence retrieved."
    citations = []
    
    is_inside_window = True 
    is_non_returnable = False
    order_value = 1000.0 
    
    # ---------------------------------------------------------
    # STEP 1: Intake
    # ---------------------------------------------------------
    reasoning.append(f"Starting intake for order {order_id}...")
    intake_data, step1 = await call_agent(
        url=settings.agent1_mcp_url,
        tool="extract_return_info",
        arguments={"text": return_text, "tenant_id": tenant_id},
        agent_name="agent1-intake"
    )
    trace.append(step1)
    
    if not step1.ok or not intake_data:
        risk_flags.append("agent_unavailable:agent1-intake")
        reasoning.append("Agent 1 failed or timed out. Degrading to escalate.")
        return fallback_decision(trace, reasoning, risk_flags)
        
    try:
        intake = IntakeOutput.model_validate(intake_data)
        product = intake.product
        product_id = intake.product_id
        issue = intake.issue
        intake_confidence = intake.confidence
        flags.extend(intake.flags)
        reasoning.append(f"Intake success. Product: {product}, Issue: {issue}, Confidence: {intake_confidence}")
    except Exception as e:
        logger.error(f"Error parsing Agent 1 output: {e}")
        risk_flags.append("agent_unavailable:agent1-intake")
        return fallback_decision(trace, reasoning, risk_flags)

    # Policy Check 1
    if intake_confidence < 0.5 or product.lower() == "unknown":
        reasoning.append("Intake validation failed. Requesting more info.")
        return DecisionOutput(
            root_cause="unknown",
            confidence=intake_confidence,
            evidence_summary="",
            recommendation="Could you please provide more details about the product and the issue you are facing?",
            requires_human_review=True,
            return_id=str(uuid.uuid4()),
            decision="request_info",
            citations=[],
            reasoning_steps=reasoning,
            human_review_reasons=["Low confidence or unknown product on intake."],
            risk_flags=risk_flags,
            agent_trace=trace,
            evidence_support=0.0
        )

    # ---------------------------------------------------------
    # STEP 2: Root Cause
    # ---------------------------------------------------------
    reasoning.append(f"Requesting root cause analysis...")
    rc_data, step2 = await call_agent(
        url=settings.agent2_mcp_url,
        tool="analyze_root_cause",
        arguments={"product": product, "issue": issue},
        agent_name="agent2-rootcause"
    )
    trace.append(step2)
    
    if not step2.ok or not rc_data:
        risk_flags.append("agent_unavailable:agent2-rootcause")
        reasoning.append("Agent 2 failed or timed out. Degrading to escalate.")
        return fallback_decision(trace, reasoning, risk_flags)
        
    try:
        rc = RootCauseOutput.model_validate(rc_data)
        root_cause = rc.top_candidate
        rc_confidence = rc.confidence
        abuse_risk = rc.abuse_risk
        top_candidates = [c.label for c in rc.candidates[:2]]
        reasoning.append(f"Root cause identified: {root_cause} (conf: {rc_confidence}, abuse_risk: {abuse_risk})")
    except Exception as e:
        logger.error(f"Error parsing Agent 2 output: {e}")
        risk_flags.append("agent_unavailable:agent2-rootcause")
        return fallback_decision(trace, reasoning, risk_flags)

    # ---------------------------------------------------------
    # STEP 3-5: Retrieval & Reflection
    # ---------------------------------------------------------
    ev_data = None
    ev_output = None
    for attempt in range(2):
        query_terms = [product, issue] + top_candidates
        if attempt == 1:
            reasoning.append("Reflecting: Evidence support too low. Retrying retrieval with expanded terms.")
            if len(top_candidates) > 1:
                query_terms = [product, issue, top_candidates[1], "alternative"]
        
        query = " ".join(query_terms)
        
        filters = {}
        if top_candidates:
            filters["hints"] = top_candidates
        if product_id:
            filters["product_id"] = product_id
            
        ev_data, step3 = await call_agent(
            url=settings.agent3_mcp_url,
            tool="retrieve_evidence",
            arguments={"query": query, "top_k": 5, "method": "hybrid", "filters": filters},
            agent_name="agent3-retrieval"
        )
        trace.append(step3)
        
        if not step3.ok or not ev_data:
            risk_flags.append("agent_unavailable:agent3-retrieval")
            reasoning.append("Agent 3 failed or timed out. Degrading to escalate.")
            return fallback_decision(trace, reasoning, risk_flags)
            
        try:
            ev_output = EvidenceOutput.model_validate(ev_data)
            
            if not ev_output.evidence:
                evidence_support = 0.0
                break
                
            top_5 = ev_output.evidence[:5]
            total_relevance = sum(e.relevance_score for e in top_5)
            if total_relevance > 0:
                matching_relevance = sum(e.relevance_score for e in top_5 if e.label_hint == root_cause)
                evidence_support = matching_relevance / total_relevance
            else:
                evidence_support = 0.0
                
            reasoning.append(f"Retrieval success. Found {ev_output.total_results} items. Support: {evidence_support:.2f}")
            
            if evidence_support >= 0.4:
                break
                
        except Exception as e:
            logger.error(f"Error parsing Agent 3 output: {e}")
            risk_flags.append("agent_unavailable:agent3-retrieval")
            return fallback_decision(trace, reasoning, risk_flags)

    if evidence_support < 0.4:
        flags.append("weak_evidence")
        reasoning.append("Evidence support remained weak after reflection.")

    # ---------------------------------------------------------
    # STEP 6: Synthesize
    # ---------------------------------------------------------
    reasoning.append("Synthesizing evidence via LLM...")
    try:
        if os.path.exists(SYNTHESIZE_PROMPT_PATH):
            with open(SYNTHESIZE_PROMPT_PATH, "r") as f:
                sys_prompt = f.read()
        else:
            sys_prompt = "You are a helpful assistant. Output JSON with { 'evidence_summary': '...', 'citations': [] }"
            
        evidence_snippets = "\n".join([f"[{item.source_id}] {item.snippet}" for item in (ev_output.evidence if ev_output else [])])
        
        prompt = sys_prompt.replace("{issue}", issue)
        prompt = prompt.replace("{candidate_labels}", ", ".join(top_candidates))
        prompt = prompt.replace("{evidence}", evidence_snippets)
        
        synth_result = None
        for attempt in range(2):
            try:
                response = call_llm(prompt=prompt)
                
                # Cleanup markdown formatting blocks if any
                if response.startswith("```json"):
                    response = response.replace("```json", "", 1).strip()
                if response.endswith("```"):
                    response = response[:-3].strip()
                    
                synth_json = json.loads(response)
                
                valid_ids = {e.source_id for e in (ev_output.evidence if ev_output else [])}
                cited_ids = synth_json.get("citations", [])
                
                if all(c in valid_ids for c in cited_ids):
                    synth_result = synth_json
                    break
                else:
                    reasoning.append(f"LLM hallucinated citations on attempt {attempt+1}. Retrying...")
            except Exception as e:
                logger.warning(f"Synthesis parsing failed: {e}")
                pass
                
        if synth_result:
            evidence_summary = synth_result.get("evidence_summary", "")
            citations = synth_result.get("citations", [])
            reasoning.append("Synthesis successful.")
        else:
            reasoning.append("LLM synthesis failed. Using deterministic fallback.")
            evidence_summary = f"Based on '{issue}', root cause seems to be '{root_cause}'."
            citations = []
            
    except Exception as e:
        logger.error(f"Synthesis step failed completely: {e}")
        evidence_summary = f"Based on '{issue}', root cause seems to be '{root_cause}'."

    # ---------------------------------------------------------
    # STEP 7: Policy Mapping
    # ---------------------------------------------------------
    decision, req_hr, hr_reasons = apply_policy(
        intake_confidence=intake_confidence,
        product=product,
        abuse_risk=abuse_risk,
        root_cause=root_cause,
        rc_confidence=rc_confidence,
        flags=flags,
        order_value=order_value,
        evidence_support=evidence_support,
        is_inside_window=is_inside_window,
        is_non_returnable=is_non_returnable
    )
    
    recommendation = f"Decision: {decision}. Summary: {evidence_summary}"
    reasoning.append(f"Policy applied: {decision}. Human review: {req_hr}.")

    return DecisionOutput(
        root_cause=root_cause,
        confidence=rc_confidence,
        evidence_summary=evidence_summary,
        recommendation=recommendation,
        requires_human_review=req_hr,
        return_id=str(uuid.uuid4()),
        decision=decision,
        citations=citations,
        reasoning_steps=reasoning,
        human_review_reasons=hr_reasons,
        risk_flags=risk_flags,
        agent_trace=trace,
        evidence_support=evidence_support
    )

def fallback_decision(trace: List[AgentStep], reasoning: List[str], risk_flags: List[str]) -> DecisionOutput:
    """Safely degrade when an agent fails."""
    return DecisionOutput(
        root_cause="unknown",
        confidence=0.0,
        evidence_summary="System error during processing.",
        recommendation="An internal service was unavailable. Escalating for manual review.",
        requires_human_review=True,
        return_id=str(uuid.uuid4()),
        decision="escalate",
        citations=[],
        reasoning_steps=reasoning,
        human_review_reasons=["Service degradation or timeout."],
        risk_flags=risk_flags,
        agent_trace=trace,
        evidence_support=0.0
    )
