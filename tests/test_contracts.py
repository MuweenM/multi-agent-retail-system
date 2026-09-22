import json
import pytest

from retail_common import CONTRACT_VERSION
from retail_common.taxonomy import (
    DECISIONS,
    INTENTS,
    ROOT_CAUSES,
    SENTIMENTS,
    SOURCE_TYPES,
)
from retail_common.schemas import (
    AgentStep,
    BulkJob,
    BulkRow,
    BulkSummary,
    DecisionOutput,
    Entity,
    EvidenceItem,
    EvidenceOutput,
    Finding,
    IntakeOutput,
    IssueCluster,
    ProductRootCauseReport,
    RootCauseCandidate,
    RootCauseOutput,
    RowError,
)


def test_contract_version():
    assert CONTRACT_VERSION == "1.1"


def test_v1_0_samples_validate():
    """Ensure v1.0 JSON payloads validate against v1.1 models with correct defaults."""

    # 1. IntakeOutput v1.0 sample
    intake_v1_json = json.dumps({
        "raw_text": "I bought a shirt and it ripped at the seam",
        "product": "shirt",
        "issue": "ripped at the seam",
        "intent": "return",
        "sentiment": "negative",
        "confidence": 0.95,
    })
    intake_obj = IntakeOutput.model_validate_json(intake_v1_json)
    assert intake_obj.product == "shirt"
    assert intake_obj.confidence == 0.95
    # Check v1.1 defaults
    assert intake_obj.tenant_id == "demo"
    assert intake_obj.clean_text == ""
    assert intake_obj.entities == []
    assert intake_obj.lang == "en"

    # 2. RootCauseOutput v1.0 sample
    rootcause_v1_json = json.dumps({
        "product": "shirt",
        "issue": "ripped at the seam",
        "candidates": [
            {
                "label": "manufacturing_defect",
                "score": 0.88,
                "supporting_return_count": 5,
            }
        ],
        "top_candidate": "manufacturing_defect",
        "confidence": 0.88,
    })
    rc_obj = RootCauseOutput.model_validate_json(rootcause_v1_json)
    assert rc_obj.top_candidate == "manufacturing_defect"
    assert len(rc_obj.candidates) == 1
    assert rc_obj.candidates[0].supporting_return_count == 5
    # Check v1.1 defaults
    assert rc_obj.candidates[0].top_terms == []
    assert rc_obj.model_name == ""
    assert rc_obj.is_emerging_spike is False
    assert rc_obj.abuse_risk == 0.0

    # 3. EvidenceOutput v1.0 sample
    evidence_v1_json = json.dumps({
        "query": "shirt ripped seam batch 2026",
        "evidence": [
            {
                "source_type": "review",
                "source_id": "rev-884",
                "snippet": "Seam unraveled on first wear.",
                "relevance_score": 0.91,
            }
        ],
        "total_results": 1,
    })
    ev_obj = EvidenceOutput.model_validate_json(evidence_v1_json)
    assert ev_obj.query == "shirt ripped seam batch 2026"
    assert ev_obj.total_results == 1
    assert len(ev_obj.evidence) == 1
    assert ev_obj.evidence[0].source_id == "rev-884"
    # Check v1.1 defaults
    assert ev_obj.method == "hybrid"
    assert ev_obj.corrected_query == ""
    assert ev_obj.latency_ms == 0
    assert ev_obj.evidence[0].matched_terms == []

    # 4. DecisionOutput v1.0 sample
    decision_v1_json = json.dumps({
        "root_cause": "manufacturing_defect",
        "confidence": 0.88,
        "evidence_summary": "Multiple returns cite unraveling seam.",
        "recommendation": "Approve refund without requiring return shipment.",
        "requires_human_review": False,
    })
    dec_obj = DecisionOutput.model_validate_json(decision_v1_json)
    assert dec_obj.root_cause == "manufacturing_defect"
    assert dec_obj.requires_human_review is False
    # Check v1.1 defaults
    assert dec_obj.decision == "escalate"
    assert dec_obj.citations == []
    assert dec_obj.reasoning_steps == []
    assert dec_obj.agent_trace == []
    assert dec_obj.disclaimer == "AI suggestion. A person must confirm before any action."


def test_models_roundtrip():
    """Ensure every model serializes to JSON and round-trips back identically."""

    models = [
        Entity(type="PRODUCT", text="Linen Shirt", start=0, end=11),
        IntakeOutput(
            raw_text="Customer text",
            product="Linen Shirt",
            issue="Loose button",
            intent="exchange",
            sentiment="neutral",
            confidence=0.85,
            return_id="RET-001",
            clean_text="Customer text sanitised",
            summary="Customer wants to exchange linen shirt due to loose button.",
            entities=[Entity(type="PRODUCT", text="Linen Shirt", start=0, end=11)],
            flags=["spelling_corrected"],
        ),
        RootCauseCandidate(
            label="manufacturing_defect",
            score=0.9,
            supporting_return_count=12,
            top_terms=["button", "stitch"],
        ),
        RootCauseOutput(
            product="Linen Shirt",
            issue="Loose button",
            candidates=[
                RootCauseCandidate(
                    label="manufacturing_defect",
                    score=0.9,
                    supporting_return_count=12,
                    top_terms=["button", "stitch"],
                )
            ],
            top_candidate="manufacturing_defect",
            confidence=0.9,
            model_name="tfidf_logreg_v3",
            is_emerging_spike=True,
        ),
        EvidenceItem(
            source_type="review",
            source_id="REV-12",
            snippet="Buttons fell off immediately.",
            relevance_score=0.87,
            title="Poor stitching",
            method="hybrid",
            matched_terms=["button", "stitching"],
            zone="body",
            metadata={"rating": "1"},
        ),
        EvidenceOutput(
            query="linen shirt button issue",
            evidence=[
                EvidenceItem(
                    source_type="review",
                    source_id="REV-12",
                    snippet="Buttons fell off immediately.",
                    relevance_score=0.87,
                )
            ],
            total_results=1,
            corrected_query="linen shirt button defect",
            latency_ms=45,
        ),
        AgentStep(
            agent="Agent1-Intake",
            tool="extract_return_info",
            ok=True,
            latency_ms=120,
            note="Extracted entities and sentiment",
        ),
        DecisionOutput(
            root_cause="manufacturing_defect",
            confidence=0.9,
            evidence_summary="Multiple button defects reported in batch 12.",
            recommendation="Issue immediate replacement",
            requires_human_review=False,
            return_id="RET-001",
            decision="approve",
            citations=["REV-12"],
            reasoning_steps=["Intake extracted defect", "Root cause confirmed defect pattern"],
            agent_trace=[
                AgentStep(agent="Agent1", tool="extract", ok=True, latency_ms=100)
            ],
        ),
        BulkRow(
            return_id="RET-101",
            text="Defective zipper",
            order_id="ORD-99",
            product_id="PROD-5",
            order_value_lkr=4500.0,
        ),
        RowError(row=5, field="text", reason="Text cannot be empty"),
        BulkJob(job_id="JOB-1", status="done", total=10, processed=9, failed=1),
        Finding(
            kind="root_cause",
            title="Defect Spike in Batch B3",
            detail="P-value < 0.01 indicating anomaly",
            return_count=20,
            value_at_risk_lkr=150000.0,
            p_value=0.005,
        ),
        IssueCluster(
            cluster_id=1,
            size=15,
            top_terms=["zipper", "stuck", "broken"],
            dominant_root_cause="manufacturing_defect",
            growth_vs_prev=0.25,
        ),
        BulkSummary(
            job_id="JOB-1",
            total=100,
            decisions={"approve": 80, "escalate": 15, "reject": 5},
            by_root_cause={"manufacturing_defect": 60, "size_fit_issue": 40},
            executive_summary="Batch B3 shows higher defect rate.",
        ),
        ProductRootCauseReport(
            product_id="PROD-5",
            window_days=30,
            total_returns=45,
            label_distribution={"manufacturing_defect": 35, "size_fit_issue": 10},
            weekly_trend=[{"week": "2026-W36", "counts": {"manufacturing_defect": 12}}],
            suppliers=[
                Finding(
                    kind="supplier",
                    title="Supplier S1 defect concentration",
                    detail="Elevated defect count",
                    return_count=30,
                    p_value=0.002,
                )
            ],
            headline="High defect concentration from Supplier S1",
            recommended_actions=["Halt batch dispatch from Supplier S1"],
        ),
    ]

    for model_instance in models:
        json_str = model_instance.model_dump_json()
        model_cls = type(model_instance)
        restored = model_cls.model_validate_json(json_str)
        assert restored == model_instance, f"Roundtrip failed for {model_cls.__name__}"


def test_taxonomy_no_duplicates():
    """Ensure taxonomy tuples contain no duplicate values."""
    taxonomy_tuples = {
        "ROOT_CAUSES": ROOT_CAUSES,
        "INTENTS": INTENTS,
        "SENTIMENTS": SENTIMENTS,
        "DECISIONS": DECISIONS,
        "SOURCE_TYPES": SOURCE_TYPES,
    }

    for name, items in taxonomy_tuples.items():
        assert len(items) == len(set(items)), f"Duplicates found in taxonomy {name}"
