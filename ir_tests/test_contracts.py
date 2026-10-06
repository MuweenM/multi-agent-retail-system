"""
Contract verification tests for shared/retail_common.

Validates:
(a) v1.0 JSON payloads for each agent output schema still validate without errors (additive compatibility).
(b) Every model round-trips through model_dump_json and model_validate_json.
(c) Taxonomy tuples contain no duplicate entries.
"""
import json
import pytest

from shared.retail_common import CONTRACT_VERSION
import shared.retail_common.taxonomy as taxonomy
from shared.retail_common.schemas import (
    Entity,
    IntakeOutput,
    RootCauseCandidate,
    RootCauseOutput,
    EvidenceItem,
    EvidenceOutput,
    AgentStep,
    DecisionOutput,
    BulkRow,
    RowError,
    BulkJob,
    Finding,
    IssueCluster,
    BulkSummary,
    ProductRootCauseReport,
)


def test_contract_version():
    assert CONTRACT_VERSION == "1.1"


# ============================================================================
# (a) v1.0 JSON sample for each model still validates
# ============================================================================

def test_v1_0_intake_output_validates():
    v1_0_payload = {
        "raw_text": "Received a defective blender that won't turn on.",
        "product": "Kitchen Blender 500W",
        "issue": "device does not power on",
        "intent": "return",
        "sentiment": "negative",
        "confidence": 0.95,
    }
    model = IntakeOutput.model_validate_json(json.dumps(v1_0_payload))
    assert model.product == "Kitchen Blender 500W"
    assert model.issue == "device does not power on"
    assert model.confidence == 0.95
    # verify v1.1 default additions
    assert model.tenant_id == "demo"
    assert model.clean_text == ""
    assert model.entities == []
    assert model.lang == "en"
    assert model.flags == []


def test_v1_0_rootcause_output_validates():
    v1_0_payload = {
        "product": "Kitchen Blender 500W",
        "issue": "device does not power on",
        "candidates": [
            {
                "label": "manufacturing_defect",
                "score": 0.88,
                "supporting_return_count": 12,
            }
        ],
        "top_candidate": "manufacturing_defect",
        "confidence": 0.88,
    }
    model = RootCauseOutput.model_validate_json(json.dumps(v1_0_payload))
    assert model.top_candidate == "manufacturing_defect"
    assert len(model.candidates) == 1
    assert model.candidates[0].supporting_return_count == 12
    # verify v1.1 default additions
    assert model.candidates[0].top_terms == []
    assert model.is_emerging_spike is False
    assert model.abuse_risk == 0.0
    assert model.notes == []


def test_v1_0_evidence_output_validates():
    v1_0_payload = {
        "query": "blender power on failure",
        "evidence": [
            {
                "source_type": "supplier_record",
                "source_id": "sup-891",
                "snippet": "Batch B22 motor fuse wiring issue identified.",
                "relevance_score": 0.91,
            }
        ],
        "total_results": 1,
    }
    model = EvidenceOutput.model_validate_json(json.dumps(v1_0_payload))
    assert model.total_results == 1
    assert model.evidence[0].source_id == "sup-891"
    # verify v1.1 default additions
    assert model.evidence[0].title == ""
    assert model.evidence[0].metadata == {}
    assert model.method == "hybrid"
    assert model.latency_ms == 0


def test_v1_0_decision_output_validates():
    v1_0_payload = {
        "root_cause": "manufacturing_defect",
        "confidence": 0.93,
        "evidence_summary": "Batch B22 known motor fuse wiring defect.",
        "recommendation": "Authorize immediate replacement under warranty.",
        "requires_human_review": False,
    }
    model = DecisionOutput.model_validate_json(json.dumps(v1_0_payload))
    assert model.root_cause == "manufacturing_defect"
    assert model.recommendation.startswith("Authorize immediate")
    assert model.requires_human_review is False
    # verify v1.1 default additions
    assert model.decision == "escalate"
    assert model.citations == []
    assert model.agent_trace == []
    assert model.disclaimer == "AI suggestion. A person must confirm before any action."


# ============================================================================
# (b) Every model round-trips through model_dump_json and back
# ============================================================================

def test_model_round_trip_serialization():
    # 1. IntakeOutput
    intake = IntakeOutput(
        raw_text="The screen on this phone is cracked",
        product="Smart Phone X",
        issue="cracked screen",
        intent="refund",
        sentiment="negative",
        confidence=0.91,
        return_id="ret-001",
        tenant_id="tenant-lk",
        clean_text="The screen on this phone is cracked",
        summary="Customer reports cracked phone screen.",
        product_id="prod-123",
        product_match_score=0.98,
        entities=[Entity(type="PRODUCT", text="Smart Phone X", start=18, end=31)],
        lang="en",
        pii_types_found=[],
        flags=["spelling_corrected"],
    )
    intake_json = intake.model_dump_json()
    assert IntakeOutput.model_validate_json(intake_json) == intake

    # 2. RootCauseOutput
    rc = RootCauseOutput(
        product="Smart Phone X",
        issue="cracked screen",
        candidates=[
            RootCauseCandidate(
                label="damaged_in_transit",
                score=0.85,
                supporting_return_count=7,
                top_terms=["box", "crushed", "glass"],
            )
        ],
        top_candidate="damaged_in_transit",
        confidence=0.85,
        product_id="prod-123",
        supplier_id="sup-44",
        model_name="tfidf_logreg_v3",
        model_version="1.2.0",
        is_emerging_spike=True,
        abuse_risk=0.05,
        notes=["Courier package damage reported on route."],
    )
    rc_json = rc.model_dump_json()
    assert RootCauseOutput.model_validate_json(rc_json) == rc

    # 3. EvidenceOutput
    evidence = EvidenceOutput(
        query="cracked screen packaging damage",
        evidence=[
            EvidenceItem(
                source_type="review",
                source_id="rev-500",
                snippet="Package arrived bent with shattered display.",
                relevance_score=0.94,
                title="Customer Review #500",
                method="hybrid",
                matched_terms=["package", "shattered"],
                zone="body",
                label_hint="damaged_in_transit",
                metadata={"courier": "Certis Lanka"},
            )
        ],
        total_results=1,
        corrected_query="cracked screen package damage",
        expanded_terms=["transit", "courier", "shattered"],
        method="hybrid",
        latency_ms=42,
    )
    ev_json = evidence.model_dump_json()
    assert EvidenceOutput.model_validate_json(ev_json) == evidence

    # 4. DecisionOutput
    decision = DecisionOutput(
        root_cause="damaged_in_transit",
        confidence=0.89,
        evidence_summary="Multiple reports of courier transit damage for batch.",
        recommendation="Refund customer and claim transit insurance.",
        requires_human_review=False,
        return_id="ret-001",
        decision="approve",
        citations=["rev-500"],
        reasoning_steps=["Intake flagged courier damage", "IR found corroborating reviews"],
        human_review_reasons=[],
        risk_flags=[],
        agent_trace=[
            AgentStep(agent="agent1", tool="extract_return_info", ok=True, latency_ms=120, note="clean"),
            AgentStep(agent="agent2", tool="analyze_root_cause", ok=True, latency_ms=85, note="transit"),
        ],
        evidence_support=0.94,
        disclaimer="AI suggestion. A person must confirm before any action.",
    )
    dec_json = decision.model_dump_json()
    assert DecisionOutput.model_validate_json(dec_json) == decision

    # 5. Bulk models
    row = BulkRow(return_id="ret-1", text="item torn", order_id="ord-99", order_value_lkr=4500.0)
    assert BulkRow.model_validate_json(row.model_dump_json()) == row

    row_err = RowError(row=1, field="text", reason="missing return description")
    assert RowError.model_validate_json(row_err.model_dump_json()) == row_err

    job = BulkJob(job_id="job-1", status="done", total=10, processed=10, failed=0, errors=[])
    assert BulkJob.model_validate_json(job.model_dump_json()) == job

    finding = Finding(
        kind="spike",
        title="Surge in transit damages",
        detail="Courier X shows 40% damage rate",
        return_count=15,
        value_at_risk_lkr=65000.0,
        p_value=0.012,
    )
    assert Finding.model_validate_json(finding.model_dump_json()) == finding

    cluster = IssueCluster(
        cluster_id=1,
        size=8,
        top_terms=["sole", "glue", "detached"],
        dominant_root_cause="manufacturing_defect",
        growth_vs_prev=0.25,
    )
    assert IssueCluster.model_validate_json(cluster.model_dump_json()) == cluster

    summary = BulkSummary(
        job_id="job-1",
        total=10,
        decisions={"approve": 8, "escalate": 2},
        by_root_cause={"manufacturing_defect": 6, "damaged_in_transit": 4},
        findings=[finding],
        clusters=[cluster],
        needs_review=2,
        est_value_at_risk_lkr=85000.0,
        executive_summary="Quality defects elevated in batch 4.",
    )
    assert BulkSummary.model_validate_json(summary.model_dump_json()) == summary

    report = ProductRootCauseReport(
        product_id="prod-123",
        window_days=30,
        total_returns=40,
        label_distribution={"manufacturing_defect": 30, "size_fit_issue": 10},
        weekly_trend=[{"week": "2026-W36", "counts": {"manufacturing_defect": 12}}],
        suppliers=[finding],
        headline="Defect rate spiked for supplier S1",
        recommended_actions=["Halt intake of batch B3", "Request supplier audit"],
    )
    assert ProductRootCauseReport.model_validate_json(report.model_dump_json()) == report


# ============================================================================
# (c) Taxonomy tuples have no duplicates
# ============================================================================

@pytest.mark.parametrize(
    "tuple_name,taxonomy_tuple",
    [
        ("ROOT_CAUSES", taxonomy.ROOT_CAUSES),
        ("INTENTS", taxonomy.INTENTS),
        ("SENTIMENTS", taxonomy.SENTIMENTS),
        ("DECISIONS", taxonomy.DECISIONS),
        ("SOURCE_TYPES", taxonomy.SOURCE_TYPES),
    ],
)
def test_taxonomy_tuples_have_no_duplicates(tuple_name, taxonomy_tuple):
    assert len(taxonomy_tuple) == len(set(taxonomy_tuple)), (
        f"Taxonomy tuple {tuple_name} contains duplicates: {taxonomy_tuple}"
    )
