"""
Abuse-risk scoring for Agent 2.

Features used (behavioural only — no customer name, district, gender, or
protected attributes):
  - recent_return_count:     number of returns by customer_ref in the last 60 days
  - change_of_mind_share:    fraction of those returns labelled change_of_mind
  - order_value_percentile:  percentile rank of this order's value in the dataset
  - days_to_return:          calendar days between purchase_date and return_date

Each feature is normalised to [0, 1] and blended into a final risk score.

The function signature keeps DB access out of the pure classifier layer:
callers supply precomputed values or a path to the CSV dataset.
"""

from __future__ import annotations

import csv
import re
from datetime import date, timedelta
from pathlib import Path


# Weights for each behavioural feature (must sum to 1.0)
_WEIGHT_RETURN_FREQ: float = 0.35
_WEIGHT_COM_SHARE: float = 0.30
_WEIGHT_ORDER_VALUE: float = 0.20
_WEIGHT_DAYS_TO_RETURN: float = 0.15

# Normalisation caps
_MAX_RETURNS_60D: int = 10          # ≥10 returns → score component = 1.0
_FAST_RETURN_DAYS: int = 3          # ≤3 days → score component = 1.0
_SLOW_RETURN_DAYS: int = 30         # ≥30 days → score component = 0.0

# Reference date for "last 60 days" when no anchor is provided
_LOOKBACK_DAYS: int = 60


def _parse_date(value: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return date.fromisoformat(value.strip()) if fmt == "%Y-%m-%d" else None
        except ValueError:
            pass
    try:
        return date.fromisoformat(value.strip())
    except Exception:
        return None


def _load_customer_history(
    customer_ref: str,
    anchor_date: date,
    returns_csv_path: Path,
) -> tuple[int, float]:
    """
    Count this customer's returns in the 60 days before anchor_date and
    compute their change_of_mind share.  No protected attributes are read.

    Returns:
        (recent_return_count, change_of_mind_share)
    """
    cutoff = anchor_date - timedelta(days=_LOOKBACK_DAYS)
    recent_total = 0
    recent_com = 0

    try:
        with returns_csv_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if row.get("customer_ref", "") != customer_ref:
                    continue
                ret_date = _parse_date(row.get("return_date", ""))
                if ret_date is None or ret_date < cutoff or ret_date > anchor_date:
                    continue
                recent_total += 1
                if row.get("root_cause_label", "") == "change_of_mind":
                    recent_com += 1
    except Exception:
        return 0, 0.0

    com_share = recent_com / recent_total if recent_total > 0 else 0.0
    return recent_total, com_share


def _order_value_percentile(order_value: float, returns_csv_path: Path) -> float:
    """Percentile rank (0–1) of this order's value within the dataset."""
    try:
        values: list[float] = []
        with returns_csv_path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                try:
                    values.append(float(row["order_value_lkr"]))
                except (KeyError, ValueError):
                    pass
        if not values:
            return 0.5
        values.sort()
        below = sum(1 for v in values if v < order_value)
        return below / len(values)
    except Exception:
        return 0.5


def compute_abuse_risk(
    *,
    customer_ref: str | None,
    order_value_lkr: float | None,
    purchase_date: date | str | None,
    return_date: date | str | None,
    returns_csv_path: Path,
) -> float:
    """Compute a behavioural abuse-risk score in [0, 1].

    Args:
        customer_ref:       Anonymised customer reference (e.g. "cust-1234").
                            Must NOT be a real customer name.
        order_value_lkr:    Order value in LKR.
        purchase_date:      Date the item was purchased.
        return_date:        Date the return was initiated.
        returns_csv_path:   Path to the historical returns CSV for frequency lookup.

    Returns:
        float in [0.0, 1.0].  Higher = higher behavioural risk.

    Prohibited inputs (never accessed inside this function):
        customer name, district, gender, ethnicity, or any protected attribute.
    """
    # ------------------------------------------------------------------ #
    # 1. Days-to-return feature                                            #
    # ------------------------------------------------------------------ #
    if isinstance(purchase_date, str):
        purchase_date = _parse_date(purchase_date)
    if isinstance(return_date, str):
        return_date = _parse_date(return_date)

    anchor = return_date if isinstance(return_date, date) else date.today()

    if isinstance(purchase_date, date) and isinstance(return_date, date):
        days_delta = (return_date - purchase_date).days
    else:
        days_delta = _SLOW_RETURN_DAYS  # neutral when unknown

    # Shorter gap → higher risk (rapid returner)
    if days_delta <= _FAST_RETURN_DAYS:
        days_score = 1.0
    elif days_delta >= _SLOW_RETURN_DAYS:
        days_score = 0.0
    else:
        days_score = 1.0 - (days_delta - _FAST_RETURN_DAYS) / (_SLOW_RETURN_DAYS - _FAST_RETURN_DAYS)

    # ------------------------------------------------------------------ #
    # 2. Return-frequency and change-of-mind features                     #
    # ------------------------------------------------------------------ #
    if customer_ref:
        recent_count, com_share = _load_customer_history(
            customer_ref, anchor, returns_csv_path
        )
    else:
        recent_count, com_share = 0, 0.0

    freq_score = min(recent_count / _MAX_RETURNS_60D, 1.0)

    # ------------------------------------------------------------------ #
    # 3. Order-value percentile feature                                    #
    # ------------------------------------------------------------------ #
    if order_value_lkr is not None:
        value_score = _order_value_percentile(float(order_value_lkr), returns_csv_path)
    else:
        value_score = 0.5  # neutral when unknown

    # ------------------------------------------------------------------ #
    # 4. Blend into final score                                           #
    # ------------------------------------------------------------------ #
    risk = (
        _WEIGHT_RETURN_FREQ * freq_score
        + _WEIGHT_COM_SHARE * com_share
        + _WEIGHT_ORDER_VALUE * value_score
        + _WEIGHT_DAYS_TO_RETURN * days_score
    )
    return round(min(max(risk, 0.0), 1.0), 4)
