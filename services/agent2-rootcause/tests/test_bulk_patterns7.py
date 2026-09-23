"""
Tests for Prompt 7: Bulk pattern analysis, issue text clustering, and impact ranking.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest
from retail_common.schemas.bulk import BulkSummary, Finding, IssueCluster
from retail_common.taxonomy import ROOT_CAUSES

from app.ml.cluster import (
    assign_to_nearest_cluster,
    cluster_issue_texts,
    evaluate_clustering_purity,
    select_best_k,
    verify_planted_patterns,
)
from app.tools.bulk_patterns import (
    analyze_bulk_patterns,
    calculate_bulk_counts,
    rank_products_by_impact,
)

_PROJECT_ROOT = Path(__file__).parents[3]
_RETURNS_CSV = _PROJECT_ROOT / "data" / "returns" / "returns.csv"


# ---------------------------------------------------------------------------
# 1. Bulk Counts Calculation
# ---------------------------------------------------------------------------


def test_bulk_counts():
    sample_returns = [
        {"root_cause_label": "manufacturing_defect", "product_id": "P-001", "supplier_id": "S-01", "courier": "C-1"},
        {"root_cause_label": "manufacturing_defect", "product_id": "P-001", "supplier_id": "S-01", "courier": "C-2"},
        {"root_cause_label": "size_fit_issue", "product_id": "P-002", "supplier_id": "S-02", "courier": "C-1"},
    ]
    counts = calculate_bulk_counts(sample_returns)

    assert "by_root_cause" in counts
    assert "by_product" in counts
    assert "by_supplier" in counts
    assert "by_courier" in counts

    assert counts["by_root_cause"]["manufacturing_defect"] == 2
    assert counts["by_root_cause"]["size_fit_issue"] == 1
    assert all(lbl in ROOT_CAUSES for lbl in counts["by_root_cause"])

    assert counts["by_product"]["P-001"] == 2
    assert counts["by_supplier"]["S-01"] == 2
    assert counts["by_courier"]["C-1"] == 2


# ---------------------------------------------------------------------------
# 2. Product Impact Ranking Formula (Returns * Average Order Value)
# ---------------------------------------------------------------------------


def test_product_impact_ranking():
    sample_returns = [
        {"product_id": "P-CHEAP", "order_value_lkr": "1000.0"},
        {"product_id": "P-CHEAP", "order_value_lkr": "1000.0"},
        {"product_id": "P-CHEAP", "order_value_lkr": "1000.0"},  # 3 * 1000 = 3000
        {"product_id": "P-EXPENSIVE", "order_value_lkr": "50000.0"},  # 1 * 50000 = 50000
    ]
    findings = rank_products_by_impact(sample_returns, top_n=2)

    assert len(findings) == 2
    # P-EXPENSIVE should rank higher due to impact (50,000 > 3,000)
    assert findings[0].product_id == "P-EXPENSIVE"
    assert findings[0].value_at_risk_lkr == 50000.0
    assert findings[1].product_id == "P-CHEAP"
    assert findings[1].value_at_risk_lkr == 3000.0


# ---------------------------------------------------------------------------
# 3. KMeans Clustering & Silhouette-Based k Selection
# ---------------------------------------------------------------------------


def test_kmeans_clustering_and_k_selection():
    with _RETURNS_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))[:200]

    texts = [r["text"] for r in rows]
    labels = [r["root_cause_label"] for r in rows]
    dates = [r["return_date"] for r in rows]

    clusters, best_k, silhouette, vectorizer, km = cluster_issue_texts(
        texts=texts,
        labels=labels,
        dates=dates,
        k_range=range(4, 13),
        random_state=3041,
    )

    # Best k must be in [4..12]
    assert 4 <= best_k <= 12
    # Silhouette score must be calculated and positive for well-separated sample
    assert silhouette > 0.5

    # Check cluster properties
    assert len(clusters) == best_k
    for c in clusters:
        assert isinstance(c, IssueCluster)
        assert c.size > 0
        assert len(c.top_terms) <= 5
        assert c.dominant_root_cause in ROOT_CAUSES


# ---------------------------------------------------------------------------
# 4. Nearest Cluster Assignment via Cosine Similarity
# ---------------------------------------------------------------------------


def test_nearest_cluster_assignment():
    with _RETURNS_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))[:200]

    texts = [r["text"] for r in rows]
    labels = [r["root_cause_label"] for r in rows]

    clusters, best_k, _, vectorizer, km = cluster_issue_texts(
        texts=texts,
        labels=labels,
        k_range=range(4, 13),
        random_state=3041,
    )

    # Test battery swelling assignment
    new_text = "The battery on the power bank is swelling and overheating."
    assigned_cid = assign_to_nearest_cluster(new_text, vectorizer, km)

    assert 0 <= assigned_cid < best_k
    assigned_cluster = next(c for c in clusters if c.cluster_id == assigned_cid)
    # Assigned cluster should relate to manufacturing defect or battery
    assert (
        assigned_cluster.dominant_root_cause == "manufacturing_defect"
        or "battery" in assigned_cluster.top_terms
        or "swelling" in assigned_cluster.top_terms
    )


# ---------------------------------------------------------------------------
# 5. Emerging Issue Growth Calculation
# ---------------------------------------------------------------------------


def test_emerging_issue_growth():
    with _RETURNS_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))[:200]

    texts = [r["text"] for r in rows]
    labels = [r["root_cause_label"] for r in rows]
    dates = [r["return_date"] for r in rows]

    clusters, _, _, _, _ = cluster_issue_texts(
        texts=texts,
        labels=labels,
        dates=dates,
        k_range=range(4, 13),
        random_state=3041,
    )

    # At least one cluster should have growth_vs_prev calculated
    valid_growths = [c.growth_vs_prev for c in clusters if c.growth_vs_prev is not None]
    assert len(valid_growths) > 0
    # Emerging clusters have growth >= 2.0
    emerging = [c for c in clusters if c.growth_vs_prev is not None and c.growth_vs_prev >= 2.0]
    assert len(emerging) > 0


# ---------------------------------------------------------------------------
# 6. Planted Pattern Evaluation on 200-Row Sample
# ---------------------------------------------------------------------------


def test_planted_pattern_evaluation_on_200_sample():
    with _RETURNS_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))[:200]

    texts = [r["text"] for r in rows]
    labels = [r["root_cause_label"] for r in rows]

    clusters, best_k, silhouette, _, _ = cluster_issue_texts(
        texts=texts,
        labels=labels,
        k_range=range(4, 13),
        random_state=3041,
    )

    # Verify recovery of battery swelling pattern
    recovery_status = verify_planted_patterns(clusters, rows)
    assert recovery_status["battery_swelling_p014"] == "recovered"
    assert recovery_status["size_fit_p027"] == "recovered"
    assert recovery_status["transit_damage_courier_c2"] == "recovered"


# ---------------------------------------------------------------------------
# 7. MCP Bulk Tool Execution and Schema Validation
# ---------------------------------------------------------------------------


def test_analyze_bulk_patterns_returns_valid_schema():
    summary = analyze_bulk_patterns("sample-200")

    assert isinstance(summary, BulkSummary)
    assert summary.job_id == "sample-200"
    assert summary.total == 200
    assert summary.est_value_at_risk_lkr > 0
    assert len(summary.clusters) > 0
    assert len(summary.findings) > 0
    assert len(summary.executive_summary) > 0

    # Test Pydantic round-trip JSON serialization
    assert BulkSummary.model_validate_json(summary.model_dump_json()) == summary


# ---------------------------------------------------------------------------
# 8. Invalid Input Handling
# ---------------------------------------------------------------------------


def test_invalid_bulk_job_and_tenant_handling():
    # Empty job_id
    res1 = analyze_bulk_patterns("")
    assert isinstance(res1, BulkSummary)
    assert res1.job_id == ""
    assert "job_id" in res1.executive_summary

    # Whitespace job_id
    res2 = analyze_bulk_patterns("   ")
    assert isinstance(res2, BulkSummary)
    assert res2.job_id == "   "

    # Non-string job_id
    res3 = analyze_bulk_patterns(None)  # type: ignore[arg-type]
    assert isinstance(res3, BulkSummary)

    # Empty tenant_id
    res4 = analyze_bulk_patterns("JOB-1", tenant_id="")
    assert isinstance(res4, BulkSummary)
    assert "tenant_id" in res4.executive_summary


# ---------------------------------------------------------------------------
# 9. Privacy: No Customer PII in Bulk Findings or Summary
# ---------------------------------------------------------------------------


def test_no_customer_pii_in_bulk_output():
    summary = analyze_bulk_patterns("sample-200")

    assert "cust-" not in summary.executive_summary.lower()
    for f in summary.findings:
        assert "cust-" not in f.detail.lower()
        assert "colombo" not in f.detail.lower()
        assert "kandy" not in f.detail.lower()
