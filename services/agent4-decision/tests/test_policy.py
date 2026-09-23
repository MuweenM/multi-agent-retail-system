import pytest
from app.policy import apply_policy
from shared.retail_common.config import settings

def test_request_info_low_intake_confidence():
    decision, req_hr, reasons = apply_policy(
        intake_confidence=0.4, product="Valid", abuse_risk=0.1, root_cause="manufacturing_defect",
        rc_confidence=0.9, flags=[], order_value=1000, evidence_support=0.9, is_inside_window=True, is_non_returnable=False
    )
    assert decision == "request_info"
    assert req_hr is True

def test_request_info_unknown_product():
    decision, req_hr, reasons = apply_policy(
        intake_confidence=0.9, product="unknown", abuse_risk=0.1, root_cause="manufacturing_defect",
        rc_confidence=0.9, flags=[], order_value=1000, evidence_support=0.9, is_inside_window=True, is_non_returnable=False
    )
    assert decision == "request_info"
    assert req_hr is True

def test_escalate_high_abuse_risk():
    decision, req_hr, reasons = apply_policy(
        intake_confidence=0.9, product="Valid", abuse_risk=0.6, root_cause="manufacturing_defect",
        rc_confidence=0.9, flags=[], order_value=1000, evidence_support=0.9, is_inside_window=True, is_non_returnable=False
    )
    assert decision == "escalate"
    assert req_hr is True

def test_escalate_policy_abuse_suspected():
    decision, req_hr, reasons = apply_policy(
        intake_confidence=0.9, product="Valid", abuse_risk=0.1, root_cause="policy_abuse_suspected",
        rc_confidence=0.9, flags=[], order_value=1000, evidence_support=0.9, is_inside_window=True, is_non_returnable=False
    )
    assert decision == "escalate"

def test_escalate_injection_suspected():
    decision, req_hr, reasons = apply_policy(
        intake_confidence=0.9, product="Valid", abuse_risk=0.1, root_cause="manufacturing_defect",
        rc_confidence=0.9, flags=["injection_suspected"], order_value=1000, evidence_support=0.9, is_inside_window=True, is_non_returnable=False
    )
    assert decision == "escalate"

def test_escalate_high_value():
    settings.high_value_lkr = 100000.0
    decision, req_hr, reasons = apply_policy(
        intake_confidence=0.9, product="Valid", abuse_risk=0.1, root_cause="manufacturing_defect",
        rc_confidence=0.9, flags=[], order_value=100000.0, evidence_support=0.9, is_inside_window=True, is_non_returnable=False
    )
    assert decision == "escalate"

def test_escalate_low_rc_confidence():
    decision, req_hr, reasons = apply_policy(
        intake_confidence=0.9, product="Valid", abuse_risk=0.1, root_cause="manufacturing_defect",
        rc_confidence=0.5, flags=[], order_value=1000, evidence_support=0.9, is_inside_window=True, is_non_returnable=False
    )
    assert decision == "escalate"

def test_escalate_weak_evidence_on_defect():
    decision, req_hr, reasons = apply_policy(
        intake_confidence=0.9, product="Valid", abuse_risk=0.1, root_cause="manufacturing_defect",
        rc_confidence=0.9, flags=["weak_evidence"], order_value=1000, evidence_support=0.3, is_inside_window=True, is_non_returnable=False
    )
    assert decision == "escalate"

def test_reject_change_of_mind_outside_window():
    decision, req_hr, reasons = apply_policy(
        intake_confidence=0.9, product="Valid", abuse_risk=0.1, root_cause="change_of_mind",
        rc_confidence=0.9, flags=[], order_value=1000, evidence_support=0.9, is_inside_window=False, is_non_returnable=False
    )
    assert decision == "reject"
    assert req_hr is True

def test_reject_non_returnable_without_defect():
    decision, req_hr, reasons = apply_policy(
        intake_confidence=0.9, product="Valid", abuse_risk=0.1, root_cause="change_of_mind",
        rc_confidence=0.9, flags=[], order_value=1000, evidence_support=0.9, is_inside_window=True, is_non_returnable=True
    )
    assert decision == "reject"
    assert req_hr is True

def test_approve_requires_human_review():
    settings.high_value_lkr = 100000.0
    decision, req_hr, reasons = apply_policy(
        intake_confidence=0.9, product="Valid", abuse_risk=0.1, root_cause="manufacturing_defect",
        rc_confidence=0.75, flags=[], order_value=1000, evidence_support=0.55, is_inside_window=True, is_non_returnable=False
    )
    assert decision == "approve"
    assert req_hr is True # Because rc_conf < 0.85 and evidence_support < 0.6

def test_approve_auto_approve():
    settings.high_value_lkr = 100000.0
    decision, req_hr, reasons = apply_policy(
        intake_confidence=0.9, product="Valid", abuse_risk=0.1, root_cause="manufacturing_defect",
        rc_confidence=0.9, flags=[], order_value=1000, evidence_support=0.7, is_inside_window=True, is_non_returnable=False
    )
    assert decision == "approve"
    assert req_hr is False
