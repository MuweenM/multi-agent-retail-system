"""
Statistical spike detection for Agent 2 root-cause intelligence.

Rule:
- Inspect daily counts over the last 7 days.
- Compare with daily counts over the previous 28 days.
- Calculate z-score: z = (mean_recent - mean_baseline) / (std_baseline / sqrt(7)).
- Flag as spike if z >= threshold_z (default 2.0) and recent count >= min_recent_count (default 3).
- Zero LLM usage: deterministic, template-based headline generation.
"""

from __future__ import annotations

import csv
import os
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

from retail_common.logging_config import get_logger

logger = get_logger(__name__)

# Paths
_SERVICE_ROOT = Path(__file__).parents[2]
_PROJECT_ROOT = _SERVICE_ROOT.parents[1]
_DEFAULT_RETURNS_CSV = _PROJECT_ROOT / "data" / "returns" / "returns.csv"

_DATASET_TODAY_DEFAULT = date(2026, 9, 22)


def get_reference_date(returns: list[dict] | None = None) -> date:
    """Determine the anchor date for time-window calculations.

    Priority:
    1. DATASET_TODAY environment variable (if set).
    2. Max return_date in the provided returns dataset.
    3. Default historical anchor (2026-09-22) or date.today().
    """
    env_today = os.getenv("DATASET_TODAY", "").strip()
    if env_today:
        try:
            return datetime.strptime(env_today, "%Y-%m-%d").date()
        except ValueError:
            pass

    if returns:
        dates: list[date] = []
        for r in returns:
            val = r.get("return_date")
            if val:
                try:
                    dates.append(date.fromisoformat(str(val).strip()))
                except ValueError:
                    pass
        if dates:
            return max(dates)

    return _DATASET_TODAY_DEFAULT


def calculate_spike_zscore(
    recent_counts: list[int | float],
    baseline_counts: list[int | float],
) -> float:
    """Calculate the z-score comparing recent daily counts against a baseline.

    Args:
        recent_counts: Daily counts for recent window (typically 7 days).
        baseline_counts: Daily counts for baseline window (typically 28 days).

    Returns:
        z-score float rounded to 4 decimals.
    """
    if not recent_counts or not baseline_counts:
        return 0.0

    mean_recent = float(np.mean(recent_counts))
    mean_baseline = float(np.mean(baseline_counts))
    std_baseline = float(np.std(baseline_counts, ddof=1)) if len(baseline_counts) > 1 else 0.0

    if std_baseline > 1e-9:
        sem = std_baseline / np.sqrt(len(recent_counts))
        z = (mean_recent - mean_baseline) / sem
    else:
        # Zero variance baseline: if recent mean exceeds baseline, scale by sqrt(n)
        diff = mean_recent - mean_baseline
        if diff > 0:
            z = diff * np.sqrt(len(recent_counts)) / max(mean_baseline, 0.5)
        else:
            z = 0.0

    return round(float(z), 4)


def _load_returns_for_product(
    product_id: str,
    returns_csv_path: Path | None = None,
) -> list[dict[str, str]]:
    csv_path = returns_csv_path or _DEFAULT_RETURNS_CSV
    if not csv_path.exists():
        return []
    records: list[dict[str, str]] = []
    try:
        with csv_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("product_id") == product_id:
                    records.append(row)
    except Exception as exc:
        logger.warning("Could not read returns from %s: %s", csv_path, exc)
    return records


def detect_spikes(
    product_id: str | None,
    returns: list[dict] | None = None,
    as_of_date: date | None = None,
    threshold_z: float = 2.0,
    min_recent_count: int = 3,
    returns_csv_path: Path | None = None,
) -> list[dict]:
    """Detect root-cause or overall volume spikes for a product.

    Compares the last 7 days against the previous 28 days.
    """
    if not product_id or not product_id.strip():
        return []

    p_rows = returns if returns is not None else _load_returns_for_product(product_id, returns_csv_path)
    if not p_rows:
        return []

    anchor = as_of_date or get_reference_date(p_rows)
    recent_dates = [anchor - timedelta(days=i) for i in range(7)]
    baseline_dates = [anchor - timedelta(days=7 + i) for i in range(28)]

    # Collect unique labels present for this product
    labels = sorted(set(r.get("root_cause_label") or r.get("root_cause_gold") or "unknown" for r in p_rows))
    # Also evaluate total product volume
    labels_to_check = ["__all__"] + labels

    findings: list[dict] = []

    for lbl in labels_to_check:
        if lbl == "__all__":
            subset = p_rows
            label_name = "total_returns"
        else:
            subset = [
                r for r in p_rows
                if (r.get("root_cause_label") or r.get("root_cause_gold")) == lbl
            ]
            label_name = lbl

        date_counts = Counter(
            r.get("return_date") for r in subset if r.get("return_date")
        )
        recent_daily = [date_counts.get(d.isoformat(), 0) for d in recent_dates]
        baseline_daily = [date_counts.get(d.isoformat(), 0) for d in baseline_dates]

        recent_sum = sum(recent_daily)
        baseline_sum = sum(baseline_daily)

        if recent_sum < min_recent_count:
            continue

        z = calculate_spike_zscore(recent_daily, baseline_daily)

        if z >= threshold_z:
            findings.append({
                "product_id": product_id,
                "label": label_name,
                "z_score": z,
                "recent_count_7d": recent_sum,
                "baseline_count_28d": baseline_sum,
                "recent_daily_rate": round(float(np.mean(recent_daily)), 3),
                "baseline_daily_rate": round(float(np.mean(baseline_daily)), 3),
            })

    # Sort spikes by highest z-score
    findings.sort(key=lambda item: item["z_score"], reverse=True)
    return findings


def is_emerging_spike(
    product_id: str | None,
    label: str | None = None,
    returns: list[dict] | None = None,
    as_of_date: date | None = None,
    threshold_z: float = 2.0,
    min_recent_count: int = 3,
    returns_csv_path: Path | None = None,
) -> bool:
    """Return True if an emerging return spike is detected for product and label.

    If label is None, checks whether ANY root-cause or overall spike is present.
    """
    if not product_id:
        return False

    spikes = detect_spikes(
        product_id=product_id,
        returns=returns,
        as_of_date=as_of_date,
        threshold_z=threshold_z,
        min_recent_count=min_recent_count,
        returns_csv_path=returns_csv_path,
    )

    if not spikes:
        return False

    if label is None:
        return len(spikes) > 0

    return any(sp["label"] == label for sp in spikes)


def generate_spike_headline(
    product_name: str,
    spike_info: dict | None,
) -> str:
    """Generate a one-sentence, template-based headline without an LLM.

    Args:
        product_name: Human-readable product name.
        spike_info: Dict returned by detect_spikes or None.

    Returns:
        A concise, deterministic one-sentence headline string.
    """
    if not spike_info:
        return f"Return volume for {product_name} remains within expected baseline parameters."

    label = spike_info.get("label", "returns")
    z_score = spike_info.get("z_score", 0.0)
    recent_count = spike_info.get("recent_count_7d", 0)

    if label in ("total_returns", "__all__"):
        return (
            f"Emerging return volume spike detected for {product_name} "
            f"with {recent_count} returns in the last 7 days (z={z_score:.2f})."
        )

    formatted_label = label.replace("_", " ")
    return (
        f"Emerging return spike detected for {product_name} driven by {formatted_label} "
        f"with {recent_count} occurrences in the last 7 days (z={z_score:.2f})."
    )
