"""
Per-product root-cause investigation tool for Agent 2.

Public API:
analyze_product_root_cause(
    product_id: str,
    window_days: int = 90,
    tenant_id: str = "demo",
) -> ProductRootCauseReport

Workflow:
1. Input validation (product_id, window_days, tenant_id).
2. Load returns for requested product, window_days, tenant_id.
3. Classify unlabeled returns using the trained Agent 2 classifier (pure ML).
4. Calculate label distribution using valid ROOT_CAUSES taxonomy only.
5. Calculate deterministic week-by-week trends (ISO weeks).
6. Calculate supplier share using catalog metadata.
7. Calculate batch share.
8. Calculate top TF-IDF terms per label using analyze_text & fitted vectorizer.
9. Statistical suspicious batch detection using Fisher's exact test (scipy).
10. Statistical spike detection (app.ml.spike).
11. Deterministic, template-based headline generation (zero LLM calls).
12. Fixed rule table recommended actions traceable to data findings.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from scipy.stats import fisher_exact

from retail_common.logging_config import get_logger
from retail_common.schemas.bulk import Finding, ProductRootCauseReport
from retail_common.taxonomy import ROOT_CAUSES

from app.ml.features import analyze_text
from app.ml.predict import _get_model, predict_top3
from app.ml.spike import detect_spikes, get_reference_date

logger = get_logger(__name__)

# Paths
_SERVICE_ROOT = Path(__file__).parents[2]
_PROJECT_ROOT = _SERVICE_ROOT.parents[1]
_RETURNS_CSV = _PROJECT_ROOT / "data" / "returns" / "returns.csv"
_PRODUCTS_CSV = _PROJECT_ROOT / "data" / "catalog" / "products.csv"

_catalog_cache: dict[str, dict[str, str]] | None = None


def load_catalog(catalog_path: Path | None = None) -> dict[str, dict[str, str]]:
    """Load product catalog: product_id -> row dict."""
    global _catalog_cache
    if catalog_path is None and _catalog_cache is not None:
        return _catalog_cache

    path = catalog_path or _PRODUCTS_CSV
    result: dict[str, dict[str, str]] = {}
    if path.exists():
        try:
            with path.open(newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    pid = row.get("product_id", "").strip()
                    if pid:
                        result[pid] = row
        except Exception as exc:
            logger.warning("Failed to load catalog from %s: %s", path, exc)
    if catalog_path is None:
        _catalog_cache = result
    return result


def load_product_returns(
    product_id: str,
    window_days: int = 90,
    tenant_id: str = "demo",
    returns_csv_path: Path | None = None,
    as_of_date: date | None = None,
) -> list[dict[str, str]]:
    """Load and window-filter returns for product_id and tenant_id."""
    csv_path = returns_csv_path or _RETURNS_CSV
    if not csv_path.exists():
        return []

    raw_rows: list[dict[str, str]] = []
    try:
        with csv_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("product_id") != product_id:
                    continue
                # In CSV synthetic data, tenant defaults to 'demo' if not specified
                row_tenant = row.get("tenant_id", "demo")
                if row_tenant != tenant_id:
                    continue
                raw_rows.append(row)
    except Exception as exc:
        logger.error("Error reading returns CSV %s: %s", csv_path, exc)
        return []

    if not raw_rows:
        return []

    anchor = as_of_date or get_reference_date(raw_rows)
    cutoff = anchor - timedelta(days=window_days)

    filtered: list[dict[str, str]] = []
    for r in raw_rows:
        date_str = r.get("return_date", "").strip()
        if not date_str:
            continue
        try:
            ret_d = date.fromisoformat(date_str)
            if cutoff <= ret_d <= anchor:
                filtered.append(dict(r))
        except ValueError:
            continue

    return filtered


def classify_unlabeled_returns(
    returns: list[dict[str, str]],
    catalog: dict[str, dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Classify returns lacking a valid taxonomy label using the saved model."""
    cat = catalog if catalog is not None else load_catalog()
    for row in returns:
        label = row.get("root_cause_label") or row.get("root_cause_gold") or ""
        label = label.strip()
        if not label or label not in ROOT_CAUSES or label == "unlabeled":
            pid = row.get("product_id", "")
            prod_name = cat.get(pid, {}).get("name", pid)
            text = row.get("text", "").strip()
            try:
                candidates, _, _ = predict_top3(prod_name, text)
                top_label = candidates[0].label if candidates else "unknown"
                row["root_cause_label"] = top_label
            except Exception as exc:
                logger.debug("Failed to classify unlabeled return: %s", exc)
                row["root_cause_label"] = "unknown"
    return returns


def calculate_label_distribution(returns: list[dict[str, str]]) -> dict[str, int]:
    """Calculate counts per valid taxonomy label in ROOT_CAUSES."""
    counts: dict[str, int] = {label: 0 for label in ROOT_CAUSES}
    for row in returns:
        lbl = row.get("root_cause_label") or row.get("root_cause_gold") or "unknown"
        if lbl in counts:
            counts[lbl] += 1
        else:
            counts["unknown"] += 1
    return counts


def calculate_weekly_trend(returns: list[dict[str, str]]) -> list[dict]:
    """Calculate deterministic ISO weekly counts: [{"week": "2026-W36", "counts": {label: n}}]."""
    weekly_map: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in returns:
        date_str = row.get("return_date", "").strip()
        if not date_str:
            continue
        try:
            d = date.fromisoformat(date_str)
            iso_year, iso_week, _ = d.isocalendar()
            week_str = f"{iso_year}-W{iso_week:02d}"
            lbl = row.get("root_cause_label") or row.get("root_cause_gold") or "unknown"
            if lbl not in ROOT_CAUSES:
                lbl = "unknown"
            weekly_map[week_str][lbl] += 1
        except ValueError:
            continue

    trend = [
        {"week": week, "counts": dict(counts)}
        for week, counts in sorted(weekly_map.items())
    ]
    return trend


def calculate_supplier_share(
    returns: list[dict[str, str]],
    catalog: dict[str, dict[str, str]] | None = None,
) -> dict[str, float]:
    """Calculate the share of returns per supplier (0.0 to 1.0)."""
    if not returns:
        return {}
    cat = catalog if catalog is not None else load_catalog()
    supplier_counts: Counter[str] = Counter()
    for row in returns:
        s_id = row.get("supplier_id", "").strip()
        if not s_id:
            pid = row.get("product_id", "")
            s_id = cat.get(pid, {}).get("supplier_id", "unknown")
        supplier_counts[s_id] += 1

    total = len(returns)
    return {s_id: round(cnt / total, 4) for s_id, cnt in supplier_counts.most_common()}


def calculate_batch_share(returns: list[dict[str, str]]) -> dict[str, float]:
    """Calculate the share of returns per batch."""
    if not returns:
        return {}
    batch_counts: Counter[str] = Counter()
    for row in returns:
        b_id = row.get("batch_id", "").strip()
        if b_id:
            batch_counts[b_id] += 1

    total = len(returns)
    return {b_id: round(cnt / total, 4) for b_id, cnt in batch_counts.most_common()}


def calculate_top_tfidf_terms(
    returns: list[dict[str, str]],
    top_n: int = 5,
) -> dict[str, list[str]]:
    """Extract top TF-IDF terms per root-cause label using existing pipeline features."""
    if not returns:
        return {}

    try:
        pipeline = _get_model()
        tfidf = pipeline.named_steps.get("features")
        if tfidf is None:
            return {}
        feature_names = np.array(tfidf.get_feature_names_out())
    except Exception as exc:
        logger.debug("Could not load TF-IDF model for top terms: %s", exc)
        return {}

    label_texts: dict[str, list[str]] = defaultdict(list)
    for row in returns:
        lbl = row.get("root_cause_label") or row.get("root_cause_gold") or "unknown"
        text = analyze_text(row.get("text", ""))
        if text:
            label_texts[lbl].append(text)

    top_terms: dict[str, list[str]] = {}
    for lbl, texts in label_texts.items():
        if not texts:
            top_terms[lbl] = []
            continue
        try:
            vecs = tfidf.transform(texts).toarray()
            mean_vec = vecs.mean(axis=0)
            top_indices = np.argsort(mean_vec)[::-1][:top_n]
            top_terms[lbl] = [
                str(feature_names[idx])
                for idx in top_indices
                if mean_vec[idx] > 0
            ]
        except Exception:
            top_terms[lbl] = []

    return top_terms


def detect_suspicious_batches(
    returns: list[dict[str, str]],
    product_id: str,
    catalog: dict[str, dict[str, str]] | None = None,
    min_returns: int = 8,
    rate_multiplier: float = 3.0,
) -> list[Finding]:
    """Detect suspicious batches using the 3x baseline + >=8 returns + Fisher's exact test rule."""
    if not returns:
        return []

    cat = catalog if catalog is not None else load_catalog()
    default_supplier = cat.get(product_id, {}).get("supplier_id")

    batch_defects: Counter[str] = Counter()
    batch_totals: Counter[str] = Counter()
    batch_supplier: dict[str, str] = {}
    batch_value_at_risk: Counter[str] = Counter()
    total_defects = 0

    for row in returns:
        b_id = row.get("batch_id", "").strip()
        if not b_id:
            continue
        batch_totals[b_id] += 1
        s_id = row.get("supplier_id", "").strip() or default_supplier or "unknown"
        batch_supplier[b_id] = s_id

        val = 0.0
        try:
            val = float(row.get("order_value_lkr", 0.0))
        except (ValueError, TypeError):
            pass

        lbl = row.get("root_cause_label") or row.get("root_cause_gold") or ""
        if lbl == "manufacturing_defect":
            batch_defects[b_id] += 1
            total_defects += 1
            batch_value_at_risk[b_id] += val

    total_returns = len(returns)
    findings: list[Finding] = []

    for b_id, b_total in batch_totals.items():
        if b_total < min_returns:
            continue

        b_defect = batch_defects[b_id]
        b_rate = b_defect / b_total

        # Baseline across all other batches for this product
        other_total = total_returns - b_total
        other_defects = total_defects - b_defect
        other_non_defects = other_total - other_defects
        b_non_defects = b_total - b_defect
        baseline_rate = other_defects / other_total if other_total > 0 else 0.0

        # Rule check: defect rate >= 3x baseline
        if baseline_rate > 0 and b_rate < (rate_multiplier * baseline_rate):
            continue
        if baseline_rate == 0 and b_rate < 0.20:
            continue

        # 2x2 contingency table for Fisher's exact test (alternative='greater')
        # [[batch_defects, batch_non_defects],
        #  [other_defects, other_non_defects]]
        table = [
            [b_defect, b_non_defects],
            [max(0, other_defects), max(0, other_non_defects)],
        ]
        try:
            _, p_value = fisher_exact(table, alternative="greater")
            p_val_float = float(p_value)
        except Exception as exc:
            logger.warning("Fisher exact test failed for batch %s: %s", b_id, exc)
            continue

        # Confirmed suspicious batch
        if p_val_float < 0.05:
            supp = batch_supplier.get(b_id, default_supplier)
            ratio = (b_rate / baseline_rate) if baseline_rate > 0 else 0.0
            p_str = f"{p_val_float:.2e}" if p_val_float < 0.001 else f"{p_val_float:.4f}"

            finding = Finding(
                kind="batch",
                title=f"Suspicious batch: {b_id}",
                detail=(
                    f"Batch {b_id} exhibits a defect rate of {b_rate:.1%} "
                    f"({b_defect}/{b_total} returns), which is {ratio:.1f}x the baseline "
                    f"rate ({baseline_rate:.1%}). Confirmed via Fisher's exact test (p={p_str})."
                ),
                return_count=b_total,
                value_at_risk_lkr=round(batch_value_at_risk[b_id], 2),
                p_value=p_val_float,
                product_id=product_id,
                supplier_id=supp,
                batch_id=b_id,
            )
            findings.append(finding)

    findings.sort(key=lambda f: f.p_value if f.p_value is not None else 1.0)
    return findings


def generate_recommended_actions(
    findings: list[Finding],
    label_distribution: dict[str, int],
    total_returns: int,
    supplier_shares: dict[str, float] | None = None,
) -> list[str]:
    """Generate actions from a fixed rule table, directly traceable to calculated findings."""
    actions: list[str] = []

    # 1. Suspicious batch actions
    batch_findings = [f for f in findings if f.kind == "batch" and f.batch_id]
    for bf in batch_findings:
        actions.append(f"Halt intake and quarantine inventory for batch {bf.batch_id}")
        if bf.supplier_id:
            actions.append(
                f"Issue formal quality audit request to supplier {bf.supplier_id} for batch {bf.batch_id}"
            )

    # 2. Dominant root cause actions
    if total_returns > 0:
        top_label = max(label_distribution, key=label_distribution.get)
        top_count = label_distribution[top_label]
        top_share = top_count / total_returns

        if top_label == "size_fit_issue" and top_share >= 0.25:
            actions.append("Update sizing chart and fit guidance on product page")
            actions.append("Review garment size measurements with manufacturing specifications")
        elif top_label == "damaged_in_transit" and top_share >= 0.25:
            actions.append("Audit courier transit packaging and fragile-item cushioning")
        elif top_label == "wrong_item_shipped" and top_share >= 0.20:
            actions.append("Audit warehouse pick-and-pack barcode scanning accuracy")
        elif top_label == "not_as_described" and top_share >= 0.20:
            actions.append("Review product listing imagery and specifications against physical inventory")
        elif top_label == "quality_durability" and top_share >= 0.20:
            actions.append("Conduct material durability testing with supplier")

    # 3. Spike action
    spike_findings = [f for f in findings if f.kind == "spike"]
    for sf in spike_findings:
        actions.append(f"Initiate priority investigation into emerging spike ({sf.title})")

    # 4. Supplier concentration
    if supplier_shares:
        for s_id, share in supplier_shares.items():
            if share >= 0.80 and not any(bf.supplier_id == s_id for bf in batch_findings):
                actions.append(f"Review supplier quality performance agreement with {s_id}")

    # Fallback default
    if not actions:
        actions.append("Continue routine return rate monitoring and standard quality inspections")

    # Deduplicate while preserving order
    seen = set()
    deduped: list[str] = []
    for act in actions:
        if act not in seen:
            seen.add(act)
            deduped.append(act)
    return deduped


def generate_headline(
    findings: list[Finding],
    label_distribution: dict[str, int],
    total_returns: int,
    product_name: str,
    spike_info: dict | None = None,
) -> str:
    """Generate a deterministic, 1-sentence headline without an LLM."""
    # 1. Suspicious batch finding takes highest priority
    batch_findings = [f for f in findings if f.kind == "batch" and f.batch_id]
    if batch_findings:
        bf = batch_findings[0]
        p_val = bf.p_value
        p_str = f"{p_val:.2e}" if (p_val is not None and p_val < 0.001) else f"{p_val:.4f}"
        supp_text = f" from supplier {bf.supplier_id}" if bf.supplier_id else ""
        return (
            f"Suspicious batch {bf.batch_id} detected with elevated defect rate{supp_text} "
            f"(p={p_str})."
        )

    # 2. Spike finding takes second priority
    if spike_info:
        lbl = spike_info.get("label", "returns").replace("_", " ")
        z_score = spike_info.get("z_score", 0.0)
        recent_cnt = spike_info.get("recent_count_7d", 0)
        return (
            f"Emerging return spike detected for {product_name} driven by {lbl} "
            f"with {recent_cnt} returns in the last 7 days (z={z_score:.2f})."
        )

    # 3. Dominant root cause
    if total_returns > 0:
        top_label = max(label_distribution, key=label_distribution.get)
        top_cnt = label_distribution[top_label]
        top_share = top_cnt / total_returns
        if top_share >= 0.30:
            formatted_lbl = top_label.replace("_", " ").capitalize()
            return (
                f"{formatted_lbl} is the primary driver of returns for {product_name}, "
                f"accounting for {top_share:.1%} of returns."
            )

    # 4. Baseline normal
    return f"Return patterns for {product_name} remain within normal operational baselines."


def analyze_product_root_cause(
    product_id: str,
    window_days: int = 90,
    tenant_id: str = "demo",
    returns_csv_path: Path | None = None,
    catalog_path: Path | None = None,
    as_of_date: date | None = None,
) -> ProductRootCauseReport:
    """Perform full per-product root-cause investigation."""
    # Input validation
    if not isinstance(product_id, str) or not product_id.strip():
        return ProductRootCauseReport(
            product_id=product_id if isinstance(product_id, str) else "",
            window_days=window_days if isinstance(window_days, int) and not isinstance(window_days, bool) else 0,
            total_returns=0,
            label_distribution={"unknown": 0},
            weekly_trend=[],
            suppliers=[],
            headline="product_id must not be empty or whitespace-only",
            recommended_actions=[],
        )

    if not isinstance(window_days, int) or isinstance(window_days, bool) or window_days <= 0:
        return ProductRootCauseReport(
            product_id=product_id,
            window_days=0,
            total_returns=0,
            label_distribution={"unknown": 0},
            weekly_trend=[],
            suppliers=[],
            headline="window_days must be a positive integer",
            recommended_actions=[],
        )

    if not isinstance(tenant_id, str) or not tenant_id.strip():
        return ProductRootCauseReport(
            product_id=product_id,
            window_days=window_days,
            total_returns=0,
            label_distribution={"unknown": 0},
            weekly_trend=[],
            suppliers=[],
            headline="tenant_id must not be empty or whitespace-only",
            recommended_actions=[],
        )

    # 1. Load catalog & resolve product name
    catalog = load_catalog(catalog_path)
    product_info = catalog.get(product_id, {})
    product_name = product_info.get("name", product_id)
    supplier_from_catalog = product_info.get("supplier_id")

    # 2. Load returns
    returns = load_product_returns(
        product_id=product_id,
        window_days=window_days,
        tenant_id=tenant_id,
        returns_csv_path=returns_csv_path,
        as_of_date=as_of_date,
    )

    if not returns:
        return ProductRootCauseReport(
            product_id=product_id,
            window_days=window_days,
            total_returns=0,
            label_distribution={label: 0 for label in ROOT_CAUSES},
            weekly_trend=[],
            suppliers=[],
            headline=f"No returns found for product {product_id} within {window_days} days.",
            recommended_actions=["Continue routine return rate monitoring and standard quality inspections"],
        )

    # 3. Classify unlabeled returns using the trained Agent 2 classifier
    returns = classify_unlabeled_returns(returns, catalog=catalog)

    # 4. Label distribution
    label_distribution = calculate_label_distribution(returns)
    total_returns = len(returns)

    # 5. Week-by-week trend
    weekly_trend = calculate_weekly_trend(returns)

    # 6. Supplier & batch shares
    supplier_shares = calculate_supplier_share(returns, catalog=catalog)
    batch_shares = calculate_batch_share(returns)

    # 7. Suspicious batch detection
    batch_findings = detect_suspicious_batches(
        returns=returns,
        product_id=product_id,
        catalog=catalog,
    )

    # 8. Spike detection
    ref_date = as_of_date or get_reference_date(returns)
    spikes = detect_spikes(
        product_id=product_id,
        returns=returns,
        as_of_date=ref_date,
    )
    primary_spike = spikes[0] if spikes else None

    # 9. Supplier concentration findings
    all_findings: list[Finding] = []
    # Add batch findings
    all_findings.extend(batch_findings)

    # Add supplier concentration findings
    for s_id, share in supplier_shares.items():
        s_count = sum(1 for r in returns if (r.get("supplier_id") or supplier_from_catalog) == s_id)
        s_val = sum(
            float(r.get("order_value_lkr", 0.0))
            for r in returns
            if (r.get("supplier_id") or supplier_from_catalog) == s_id
        )
        finding = Finding(
            kind="supplier",
            title=f"Supplier concentration: {s_id}",
            detail=f"Supplier {s_id} accounts for {share:.1%} ({s_count}/{total_returns}) of returns for {product_id}.",
            return_count=s_count,
            value_at_risk_lkr=round(s_val, 2),
            p_value=None,
            product_id=product_id,
            supplier_id=s_id,
        )
        all_findings.append(finding)

    # Add spike findings if any
    for sp in spikes:
        sp_lbl = sp.get("label", "")
        all_findings.append(
            Finding(
                kind="spike",
                title=f"Emerging spike: {sp_lbl}",
                detail=(
                    f"Emerging spike in {sp_lbl} with {sp.get('recent_count_7d')} returns "
                    f"in the last 7 days (z={sp.get('z_score', 0.0):.2f})."
                ),
                return_count=sp.get("recent_count_7d", 0),
                p_value=None,
                product_id=product_id,
                supplier_id=supplier_from_catalog,
            )
        )

    # 10. Template-based headline (zero LLM calls)
    headline = generate_headline(
        findings=all_findings,
        label_distribution=label_distribution,
        total_returns=total_returns,
        product_name=product_name,
        spike_info=primary_spike,
    )

    # 11. Recommended actions (fixed rule table)
    recommended_actions = generate_recommended_actions(
        findings=all_findings,
        label_distribution=label_distribution,
        total_returns=total_returns,
        supplier_shares=supplier_shares,
    )

    return ProductRootCauseReport(
        product_id=product_id,
        window_days=window_days,
        total_returns=total_returns,
        label_distribution=label_distribution,
        weekly_trend=weekly_trend,
        suppliers=all_findings,
        headline=headline,
        recommended_actions=recommended_actions,
    )
