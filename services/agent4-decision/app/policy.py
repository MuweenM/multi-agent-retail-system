from typing import List, Tuple
from retail_common.config import settings

def apply_policy(
    intake_confidence: float,
    product: str,
    abuse_risk: float,
    root_cause: str,
    rc_confidence: float,
    flags: List[str],
    order_value: float,
    evidence_support: float,
    is_inside_window: bool,
    is_non_returnable: bool
) -> Tuple[str, bool, List[str]]:
    """
    Evaluates the explicit business rules and maps to a decision.
    
    Returns:
        decision (str): "request_info", "escalate", "approve", "reject"
        requires_human_review (bool)
        human_review_reasons (List[str])
    """
    requires_human_review = True
    human_review_reasons = []

    # 1. request_info
    if intake_confidence < 0.5 or product.lower() == "unknown":
        human_review_reasons.append("Low confidence or unknown product on intake.")
        return "request_info", True, human_review_reasons

    # 2. escalate
    defect_claims = ["manufacturing_defect", "damaged_in_transit", "wrong_item_shipped", "not_as_described"]
    is_defect_claim = root_cause in defect_claims
    
    escalate_reasons = []
    if abuse_risk >= 0.6:
        escalate_reasons.append("High abuse risk detected (>= 0.6).")
    if root_cause == "policy_abuse_suspected":
        escalate_reasons.append("Root cause is suspected policy abuse.")
    if "injection_suspected" in flags:
        escalate_reasons.append("Prompt injection suspected.")
    if order_value >= settings.high_value_lkr:
        escalate_reasons.append(f"Order value exceeds high value threshold ({settings.high_value_lkr}).")
    if rc_confidence < 0.6:
        escalate_reasons.append(f"Root cause confidence is low ({rc_confidence} < 0.6).")
    if "weak_evidence" in flags and is_defect_claim:
        escalate_reasons.append("Weak evidence for a defect claim.")
        
    if escalate_reasons:
        human_review_reasons.extend(escalate_reasons)
        return "escalate", True, human_review_reasons

    # 3. reject
    reject_reasons = []
    if root_cause == "change_of_mind" and not is_inside_window:
        reject_reasons.append("Change of mind outside of the return window.")
    elif is_non_returnable and not is_defect_claim:
        reject_reasons.append("Non-returnable item without a defect claim.")
        
    if reject_reasons:
        human_review_reasons.extend(reject_reasons)
        return "reject", True, human_review_reasons

    # 4. approve
    if is_defect_claim and rc_confidence >= 0.7 and evidence_support >= 0.5 and is_inside_window:
        # Check auto-approve requirements
        if rc_confidence >= 0.85 and evidence_support >= 0.6 and order_value < settings.high_value_lkr:
            requires_human_review = False
        else:
            if rc_confidence < 0.85:
                human_review_reasons.append("Confidence below auto-approve threshold (0.85).")
            if evidence_support < 0.6:
                human_review_reasons.append("Evidence support below auto-approve threshold (0.6).")
            requires_human_review = True
            
        return "approve", requires_human_review, human_review_reasons

    # 5. Default fallback
    human_review_reasons.append("Case did not meet strict approve or reject criteria.")
    return "escalate", True, human_review_reasons
