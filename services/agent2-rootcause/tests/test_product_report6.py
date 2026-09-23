"""
Tests for Prompt 6: Per-product root-cause investigation & spike detection.
"""

from __future__ import annotations

import re
from datetime import date

import pytest
from retail_common.schemas.bulk import Finding, ProductRootCauseReport
from retail_common.taxonomy import ROOT_CAUSES

from app.ml.spike import (
    calculate_spike_zscore,
    detect_spikes,
    generate_spike_headline,
    is_emerging_spike,
)
from app.tools.product_report import (
    analyze_product_root_cause,
    calculate_batch_share,
    calculate_label_distribution,
    calculate_supplier_share,
    calculate_top_tfidf_terms,
    calculate_weekly_trend,
    classify_unlabeled_returns,
    detect_suspicious_batches,
)


# ---------------------------------------------------------------------------
# 1. P-014 Flags Supplier S-03 and Batch B-2026-07 with Real p-value
# ---------------------------------------------------------------------------


def test_p014_flags_supplier_and_suspicious_batch():
    report = analyze_product_root_cause("P-014", window_days=90, tenant_id="demo")

    assert isinstance(report, ProductRootCauseReport)
    assert report.product_id == "P-014"
    assert report.total_returns > 0

    # 1. Flag supplier S-03
    supplier_findings = [f for f in report.suppliers if f.supplier_id == "S-03"]
    assert len(supplier_findings) >= 1, "Supplier S-03 must be flagged in report findings"

    # 2. Flag batch B-2026-07
    batch_findings = [f for f in report.suppliers if f.batch_id == "B-2026-07"]
    assert len(batch_findings) >= 1, "Batch B-2026-07 must be flagged as suspicious"

    # 3. Include a real calculated p-value (Fisher's exact test)
    bf = batch_findings[0]
    assert bf.p_value is not None, "p-value must be calculated and not None"
    assert isinstance(bf.p_value, float)
    assert 0.0 < bf.p_value < 0.05, f"Expected statistically significant p-value (<0.05), got {bf.p_value}"

    # 4. Headline is informative and mentions the batch
    assert "B-2026-07" in report.headline
    assert "S-03" in report.headline

    # 5. Recommended actions address batch and supplier
    actions_text = " ".join(report.recommended_actions)
    assert "B-2026-07" in actions_text
    assert "S-03" in actions_text


# ---------------------------------------------------------------------------
# 2. P-027 Shows size_fit_issue as Largest Root-Cause Label
# ---------------------------------------------------------------------------


def test_p027_shows_size_fit_issue_as_largest_label():
    report = analyze_product_root_cause("P-027", window_days=90, tenant_id="demo")

    assert isinstance(report, ProductRootCauseReport)
    assert report.product_id == "P-027"
    assert report.total_returns > 0

    # size_fit_issue must be the largest root-cause label
    top_label = max(report.label_distribution, key=report.label_distribution.get)
    assert top_label == "size_fit_issue", (
        f"Expected size_fit_issue as largest label, got {top_label} "
        f"with counts {report.label_distribution}"
    )

    size_fit_count = report.label_distribution["size_fit_issue"]
    assert size_fit_count >= 30, f"Expected >= 30 size_fit_issue returns, got {size_fit_count}"

    # Actions must include fit / sizing guidance
    actions_text = " ".join(report.recommended_actions).lower()
    assert "sizing" in actions_text or "fit" in actions_text


# ---------------------------------------------------------------------------
# 3. Weekly Trend Generation
# ---------------------------------------------------------------------------


def test_weekly_trend_generation():
    report = analyze_product_root_cause("P-014", window_days=90, tenant_id="demo")

    assert len(report.weekly_trend) > 0, "Weekly trend must not be empty"

    week_regex = re.compile(r"^\d{4}-W\d{2}$")
    weeks = [entry["week"] for entry in report.weekly_trend]

    # Verify formatting and chronological sorting
    for entry in report.weekly_trend:
        assert week_regex.match(entry["week"]), f"Invalid ISO week format: {entry['week']}"
        assert isinstance(entry["counts"], dict)
        for lbl, count in entry["counts"].items():
            assert lbl in ROOT_CAUSES, f"Non-taxonomy label in trend: {lbl}"
            assert isinstance(count, int)
            assert count >= 0

    assert weeks == sorted(weeks), "Weekly trend must be sorted chronologically"


# ---------------------------------------------------------------------------
# 4. Supplier Share Calculation
# ---------------------------------------------------------------------------


def test_supplier_share_calculation():
    sample_returns = [
        {"product_id": "P-TEST", "supplier_id": "S-01"},
        {"product_id": "P-TEST", "supplier_id": "S-01"},
        {"product_id": "P-TEST", "supplier_id": "S-02"},
        {"product_id": "P-TEST", "supplier_id": "S-01"},
    ]
    shares = calculate_supplier_share(sample_returns)
    assert shares["S-01"] == 0.75
    assert shares["S-02"] == 0.25

    # Full product test
    report = analyze_product_root_cause("P-014", window_days=90)
    # S-03 is the sole supplier for P-014 in the catalog
    p014_supplier_findings = [f for f in report.suppliers if f.kind == "supplier"]
    assert any(f.supplier_id == "S-03" for f in p014_supplier_findings)


# ---------------------------------------------------------------------------
# 5. Batch Share Calculation
# ---------------------------------------------------------------------------


def test_batch_share_calculation():
    sample_returns = [
        {"batch_id": "B-2026-01"},
        {"batch_id": "B-2026-01"},
        {"batch_id": "B-2026-02"},
        {"batch_id": "B-2026-03"},
    ]
    shares = calculate_batch_share(sample_returns)
    assert shares["B-2026-01"] == 0.5
    assert shares["B-2026-02"] == 0.25
    assert shares["B-2026-03"] == 0.25

    report = analyze_product_root_cause("P-014", window_days=90)
    # Total batch returns must correspond to total returns
    assert report.total_returns > 0


# ---------------------------------------------------------------------------
# 6. Spike Calculation & Statistical Testing
# ---------------------------------------------------------------------------


def test_spike_calculation_zscore():
    # Baseline identical to recent: z-score should be ~0
    z_zero = calculate_spike_zscore([2, 2, 2, 2, 2, 2, 2], [2] * 28)
    assert abs(z_zero) < 0.01

    # Recent spike: recent mean = 10, baseline mean = 1, std = 0.5
    z_spike = calculate_spike_zscore([10, 10, 10, 10, 10, 10, 10], [1, 1.5, 0.5, 1] * 7)
    assert z_spike > 5.0, f"Expected high z-score for obvious spike, got {z_spike}"

    # P-014 damaged_in_transit spike
    is_spike = is_emerging_spike("P-014", "damaged_in_transit")
    assert is_spike is True

    # P-014 non-spiking label
    is_no_spike = is_emerging_spike("P-014", "quality_durability")
    assert is_no_spike is False


def test_spike_headline_template_without_llm():
    spike_info = {
        "product_id": "P-009",
        "label": "damaged_in_transit",
        "z_score": 5.04,
        "recent_count_7d": 4,
    }
    headline = generate_spike_headline("Wireless Noise Cancelling Headphones", spike_info)

    # One sentence, template-based, zero LLM
    assert headline.count(".") == 1 or headline.endswith(".")
    assert "Wireless Noise Cancelling Headphones" in headline
    assert "damaged in transit" in headline
    assert "5.04" in headline


# ---------------------------------------------------------------------------
# 7. Invalid Input & Edge Case Handling
# ---------------------------------------------------------------------------


def test_invalid_product_id_handling():
    res1 = analyze_product_root_cause("")
    assert isinstance(res1, ProductRootCauseReport)
    assert res1.total_returns == 0
    assert "product_id" in res1.headline

    res2 = analyze_product_root_cause("   ")
    assert isinstance(res2, ProductRootCauseReport)
    assert res2.total_returns == 0

    res3 = analyze_product_root_cause(None)  # type: ignore[arg-type]
    assert isinstance(res3, ProductRootCauseReport)
    assert res3.total_returns == 0


def test_window_days_validation():
    # 0 or negative
    res1 = analyze_product_root_cause("P-014", window_days=0)
    assert isinstance(res1, ProductRootCauseReport)
    assert res1.total_returns == 0
    assert "window_days" in res1.headline

    res2 = analyze_product_root_cause("P-014", window_days=-30)
    assert isinstance(res2, ProductRootCauseReport)
    assert res2.total_returns == 0

    # bool is not allowed as int
    res3 = analyze_product_root_cause("P-014", window_days=True)  # type: ignore[arg-type]
    assert isinstance(res3, ProductRootCauseReport)
    assert res3.total_returns == 0


def test_tenant_id_handling():
    # Invalid empty tenant
    res_empty = analyze_product_root_cause("P-014", tenant_id="")
    assert res_empty.total_returns == 0
    assert "tenant_id" in res_empty.headline

    # Unknown tenant: should return 0 returns for demo dataset
    res_unknown = analyze_product_root_cause("P-014", tenant_id="non_existent_tenant")
    assert res_unknown.total_returns == 0
    assert "No returns found" in res_unknown.headline


# ---------------------------------------------------------------------------
# 8. Classification of Unlabeled Returns Reuses Saved Model
# ---------------------------------------------------------------------------


def test_classification_of_unlabeled_returns():
    unlabeled_data = [
        {
            "product_id": "P-014",
            "text": "Battery swelling on the Power Bank after charging.",
            "root_cause_label": "",  # unlabeled
        },
        {
            "product_id": "P-027",
            "text": "This shirt runs small even though the listed size is correct.",
            "root_cause_label": "unlabeled",
        },
    ]

    classified = classify_unlabeled_returns(unlabeled_data)
    assert classified[0]["root_cause_label"] == "manufacturing_defect"
    assert classified[1]["root_cause_label"] == "size_fit_issue"


# ---------------------------------------------------------------------------
# 9. Top TF-IDF Terms per Root Cause
# ---------------------------------------------------------------------------


def test_top_tfidf_terms_extraction():
    sample = [
        {"product_id": "P-014", "text": "battery swelling after charge", "root_cause_label": "manufacturing_defect"},
        {"product_id": "P-014", "text": "battery expanded and hot", "root_cause_label": "manufacturing_defect"},
    ]
    terms = calculate_top_tfidf_terms(sample, top_n=3)
    assert "manufacturing_defect" in terms
    assert isinstance(terms["manufacturing_defect"], list)


# ---------------------------------------------------------------------------
# 10. Privacy & Protected Attributes Protection
# ---------------------------------------------------------------------------


def test_customer_pii_never_exposed_in_findings_or_report():
    report = analyze_product_root_cause("P-014", window_days=90)

    # Check headline
    assert "cust-" not in report.headline.lower()
    assert "colombo" not in report.headline.lower()
    assert "kandy" not in report.headline.lower()

    # Check actions
    for act in report.recommended_actions:
        assert "cust-" not in act.lower()
        assert "colombo" not in act.lower()

    # Check findings details
    for f in report.suppliers:
        assert "cust-" not in f.detail.lower()
        assert "colombo" not in f.detail.lower()
        assert "galle" not in f.detail.lower()
