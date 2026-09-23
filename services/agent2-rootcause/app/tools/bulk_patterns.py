"""
Bulk pattern analysis, clustering, and impact ranking tool for Agent 2.

Public API:
analyze_bulk_patterns(
    job_id: str,
    tenant_id: str = "demo",
) -> BulkSummary

Calculations:
1. Counts by root cause, product, supplier, and courier.
2. Product impact ranking: (number of returns) * (average order value).
3. TF-IDF + KMeans clustering with silhouette-based k selection (4..12).
4. Emerging cluster identification (growth >= 2x vs previous period).
5. Statistical suspicious batch screening across batches.
6. Value at risk aggregation and structured executive summary.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from retail_common.logging_config import get_logger
from retail_common.schemas.bulk import BulkSummary, Finding, IssueCluster
from retail_common.taxonomy import ROOT_CAUSES

from app.ml.cluster import cluster_issue_texts
from app.ml.spike import detect_spikes, get_reference_date
from app.tools.product_report import (
    classify_unlabeled_returns,
    detect_suspicious_batches,
    load_catalog,
)

logger = get_logger(__name__)

# Paths
_SERVICE_ROOT = Path(__file__).parents[2]
_PROJECT_ROOT = _SERVICE_ROOT.parents[1]
_RETURNS_CSV = _PROJECT_ROOT / "data" / "returns" / "returns.csv"
_PRODUCTS_CSV = _PROJECT_ROOT / "data" / "catalog" / "products.csv"


def load_bulk_returns(
    job_id: str,
    tenant_id: str = "demo",
    returns_csv_path: Path | None = None,
) -> list[dict[str, str]]:
    """Load returns for a bulk job and tenant context."""
    csv_path = returns_csv_path or _RETURNS_CSV
    if not csv_path.exists():
        return []

    raw_rows: list[dict[str, str]] = []
    try:
        with csv_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                row_tenant = row.get("tenant_id", "demo")
                if row_tenant != tenant_id:
                    continue

                # If the dataset row has an explicit job_id, respect it
                if "job_id" in row and row["job_id"] and row["job_id"] != job_id:
                    continue

                raw_rows.append(row)
    except Exception as exc:
        logger.error("Failed to load bulk returns from %s: %s", csv_path, exc)
        return []

    # Handle special sample job_ids for testing/benchmarking
    if job_id.startswith("sample-") or job_id == "sample_200":
        try:
            sample_size = int(job_id.split("-")[-1]) if "-" in job_id else 200
            return raw_rows[:sample_size]
        except ValueError:
            return raw_rows[:200]

    return raw_rows


def calculate_bulk_counts(
    returns: list[dict[str, str]],
) -> dict[str, dict[str, int]]:
    """Calculate counts by root cause, product, supplier, and courier."""
    by_root_cause: dict[str, int] = {label: 0 for label in ROOT_CAUSES}
    by_product: Counter[str] = Counter()
    by_supplier: Counter[str] = Counter()
    by_courier: Counter[str] = Counter()

    for r in returns:
        lbl = r.get("root_cause_label") or r.get("root_cause_gold") or "unknown"
        if lbl in by_root_cause:
            by_root_cause[lbl] += 1
        else:
            by_root_cause["unknown"] += 1

        pid = r.get("product_id", "").strip()
        if pid:
            by_product[pid] += 1

        sid = r.get("supplier_id", "").strip()
        if sid:
            by_supplier[sid] += 1

        courier = r.get("courier", "").strip()
        if courier:
            by_courier[courier] += 1

    return {
        "by_root_cause": by_root_cause,
        "by_product": dict(by_product),
        "by_supplier": dict(by_supplier),
        "by_courier": dict(by_courier),
    }


def rank_products_by_impact(
    returns: list[dict[str, str]],
    catalog: dict[str, dict[str, str]] | None = None,
    top_n: int = 10,
) -> list[Finding]:
    """Rank products explicitly by (number of returns * average order value).

    Returns top_n Finding objects of kind='product'.
    """
    if not returns:
        return []

    cat = catalog if catalog is not None else load_catalog()

    product_values: dict[str, list[float]] = defaultdict(list)
    for r in returns:
        pid = r.get("product_id", "").strip()
        if not pid:
            continue
        try:
            val = float(r.get("order_value_lkr", 0.0))
        except (ValueError, TypeError):
            val = 0.0
        product_values[pid].append(val)

    rankings: list[tuple[str, int, float, float]] = []
    for pid, values in product_values.items():
        n_returns = len(values)
        avg_val = sum(values) / n_returns if n_returns > 0 else 0.0
        # Explicit formula: number of returns * average order value
        impact = n_returns * avg_val
        rankings.append((pid, n_returns, avg_val, impact))

    rankings.sort(key=lambda item: item[3], reverse=True)

    findings: list[Finding] = []
    for pid, count, avg_val, impact in rankings[:top_n]:
        prod_info = cat.get(pid, {})
        prod_name = prod_info.get("name", pid)
        supp_id = prod_info.get("supplier_id")

        finding = Finding(
            kind="product",
            title=f"High impact product: {prod_name}",
            detail=(
                f"Product {pid} ({prod_name}) had {count} returns with average "
                f"order value {avg_val:,.2f} LKR, totaling {impact:,.2f} LKR value at risk."
            ),
            return_count=count,
            value_at_risk_lkr=round(impact, 2),
            p_value=None,
            product_id=pid,
            supplier_id=supp_id,
        )
        findings.append(finding)

    return findings


def generate_bulk_executive_summary(
    total_returns: int,
    total_value_at_risk: float,
    by_root_cause: dict[str, int],
    impact_findings: list[Finding],
    clusters: list[IssueCluster],
    suspicious_batches: list[Finding],
    needs_review: int,
) -> str:
    """Generate a structured, deterministic executive summary without an LLM."""
    if total_returns == 0:
        return "Bulk analysis completed. No returns found for the specified job."

    # Top root causes
    sorted_causes = sorted(
        by_root_cause.items(), key=lambda item: item[1], reverse=True
    )
    top_cause, top_cause_count = sorted_causes[0]
    top_cause_share = top_cause_count / total_returns if total_returns > 0 else 0.0

    # Top impact product
    top_product_str = ""
    if impact_findings:
        top_p = impact_findings[0]
        top_product_str = (
            f" Top financial risk is concentrated in {top_p.product_id} "
            f"({top_p.value_at_risk_lkr:,.2f} LKR at risk across {top_p.return_count} returns)."
        )

    # Emerging clusters
    emerging_clusters = [
        c for c in clusters if c.growth_vs_prev is not None and c.growth_vs_prev >= 2.0
    ]
    emerging_str = ""
    if emerging_clusters:
        top_em = emerging_clusters[0]
        emerging_str = (
            f" Identified {len(emerging_clusters)} emerging cluster(s), led by "
            f"Cluster {top_em.cluster_id} ({top_em.dominant_root_cause.replace('_', ' ')}, "
            f"growth={top_em.growth_vs_prev:.1f}x)."
        )

    # Suspicious batches
    batch_str = ""
    if suspicious_batches:
        bf = suspicious_batches[0]
        p_val_str = (
            f"{bf.p_value:.2e}"
            if (bf.p_value is not None and bf.p_value < 0.001)
            else f"{bf.p_value:.4f}"
        )
        batch_str = (
            f" Flagged suspicious batch {bf.batch_id} for supplier {bf.supplier_id} (p={p_val_str})."
        )

    summary = (
        f"Analyzed {total_returns} returns representing {total_value_at_risk:,.2f} LKR total value at risk. "
        f"Primary root cause is {top_cause.replace('_', ' ')} ({top_cause_share:.1%} of returns, {top_cause_count} total)."
        f"{top_product_str}"
        f"{emerging_str}"
        f"{batch_str}"
        f" {needs_review} return(s) flagged for manual review."
    )
    return summary


def analyze_bulk_patterns(
    job_id: str,
    tenant_id: str = "demo",
    returns: list[dict[str, str]] | None = None,
    returns_csv_path: Path | None = None,
    catalog_path: Path | None = None,
) -> BulkSummary:
    """Perform comprehensive bulk pattern analysis and clustering."""
    # Input validation
    if not isinstance(job_id, str) or not job_id.strip():
        return BulkSummary(
            job_id=job_id if isinstance(job_id, str) else "",
            executive_summary="job_id must not be empty or whitespace-only",
        )

    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return BulkSummary(
            job_id=job_id,
            executive_summary="tenant_id must not be empty or whitespace-only",
        )

    catalog = load_catalog(catalog_path)

    # 1. Load returns
    raw_returns = (
        returns
        if returns is not None
        else load_bulk_returns(
            job_id=job_id,
            tenant_id=tenant_id,
            returns_csv_path=returns_csv_path,
        )
    )

    if not raw_returns:
        return BulkSummary(
            job_id=job_id,
            total=0,
            decisions={},
            by_root_cause={lbl: 0 for lbl in ROOT_CAUSES},
            findings=[],
            clusters=[],
            needs_review=0,
            est_value_at_risk_lkr=0.0,
            executive_summary=f"No returns found for job {job_id} under tenant {tenant_id}.",
        )

    # 2. Classify any unlabelled returns
    classified_returns = classify_unlabeled_returns(raw_returns, catalog=catalog)
    total_returns = len(classified_returns)

    # 3. Calculate bulk counts
    counts_data = calculate_bulk_counts(classified_returns)
    by_root_cause = counts_data["by_root_cause"]

    # 4. Product impact ranking (explicit returns * average order value)
    impact_findings = rank_products_by_impact(classified_returns, catalog=catalog, top_n=10)

    # 5. Calculate total value at risk
    total_value_at_risk = sum(
        float(r.get("order_value_lkr", 0.0))
        for r in classified_returns
        if r.get("order_value_lkr")
    )

    # 6. Clustering on issue texts
    texts = [r.get("text", "") for r in classified_returns]
    labels = [
        r.get("root_cause_label") or r.get("root_cause_gold") or "unknown"
        for r in classified_returns
    ]
    dates = [r.get("return_date", "") for r in classified_returns]

    try:
        clusters, best_k, silhouette, _, _ = cluster_issue_texts(
            texts=texts,
            labels=labels,
            dates=dates,
            k_range=range(4, 13),
            random_state=3041,
        )
    except Exception as exc:
        logger.error("Clustering failed: %s", exc)
        clusters = []

    # 7. Screen for suspicious batches across products
    suspicious_batches: list[Finding] = []
    by_product_returns: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in classified_returns:
        pid = r.get("product_id", "")
        if pid:
            by_product_returns[pid].append(r)

    for pid, p_returns in by_product_returns.items():
        if len(p_returns) >= 8:
            batch_f = detect_suspicious_batches(
                returns=p_returns,
                product_id=pid,
                catalog=catalog,
                min_returns=8,
                rate_multiplier=3.0,
            )
            suspicious_batches.extend(batch_f)

    # 8. Consolidate findings: top product impacts + suspicious batches + emerging clusters
    all_findings: list[Finding] = []
    # Add top 10 product impact findings
    all_findings.extend(impact_findings)

    # Add suspicious batch findings
    all_findings.extend(suspicious_batches)

    # Add emerging cluster findings
    for c in clusters:
        if c.growth_vs_prev is not None and c.growth_vs_prev >= 2.0:
            top_term_str = ", ".join(c.top_terms[:3])
            c_finding = Finding(
                kind="cluster",
                title=f"Emerging issue cluster {c.cluster_id}: {c.dominant_root_cause}",
                detail=(
                    f"Cluster {c.cluster_id} ({c.dominant_root_cause.replace('_', ' ')}) "
                    f"grew {c.growth_vs_prev:.1f}x vs previous period ({c.size} returns total). "
                    f"Top terms: {top_term_str}."
                ),
                return_count=c.size,
                value_at_risk_lkr=0.0,
                p_value=None,
            )
            all_findings.append(c_finding)

    # 9. Needs review count
    needs_review = (
        by_root_cause.get("unknown", 0)
        + by_root_cause.get("policy_abuse_suspected", 0)
        + sum(f.return_count for f in suspicious_batches)
    )

    # 10. Executive summary
    executive_summary = generate_bulk_executive_summary(
        total_returns=total_returns,
        total_value_at_risk=total_value_at_risk,
        by_root_cause=by_root_cause,
        impact_findings=impact_findings,
        clusters=clusters,
        suspicious_batches=suspicious_batches,
        needs_review=needs_review,
    )

    return BulkSummary(
        job_id=job_id,
        total=total_returns,
        decisions={},
        by_root_cause=by_root_cause,
        findings=all_findings[:20],  # Return consolidated top findings
        clusters=clusters,
        needs_review=needs_review,
        est_value_at_risk_lkr=round(total_value_at_risk, 2),
        executive_summary=executive_summary,
    )
