"""
Main orchestration tool for Agent 2 root-cause analysis.

Flow
----
1. Validate inputs.
2. Run pure ML classifier (predict_top3) — no DB access inside.
3. Check LLM fallback conditions:
      top_prob < 0.55  OR  gap(top1, top2) < 0.10
4. If fallback: call LLM, validate label against ROOT_CAUSES.
5. Enrich candidates with supporting_return_count from CSV/DB.
6. Compute abuse_risk (behavioural features only).
7. Resolve supplier_id from catalog.
8. Determine is_emerging_spike (delegate to spike module if available).
9. Assemble and return RootCauseOutput.

DB / IO access
--------------
All database and file access happens in *this* layer only.
The prediction layer (app.ml.predict) and explanation layer (app.ml.explain)
are kept free of IO.
"""

from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path

from retail_common.logging_config import get_logger
from retail_common.schemas.rootcause import RootCauseCandidate, RootCauseOutput
from retail_common.taxonomy import ROOT_CAUSES

from app.ml.predict import MODEL_VERSION, predict_top3
from app.ml.abuse import compute_abuse_risk

logger = get_logger(__name__)

# ── Paths ────────────────────────────────────────────────────────────────────
_SERVICE_ROOT = Path(__file__).parents[2]
_PROJECT_ROOT = _SERVICE_ROOT.parents[1]
_RETURNS_CSV = _PROJECT_ROOT / "data" / "returns" / "returns.csv"
_PRODUCTS_CSV = _PROJECT_ROOT / "data" / "catalog" / "products.csv"
_PROMPT_PATH = _SERVICE_ROOT / "app" / "prompts" / "fallback_label.md"

# ── Thresholds ───────────────────────────────────────────────────────────────
_FALLBACK_TOP_PROB: float = 0.55
_FALLBACK_GAP: float = 0.10

# ── Catalog cache ────────────────────────────────────────────────────────────
_catalog_cache: dict[str, dict[str, str]] | None = None


def _load_catalog() -> dict[str, dict[str, str]]:
    """product_id → {name, supplier_id, price_lkr, ...}"""
    global _catalog_cache
    if _catalog_cache is not None:
        return _catalog_cache
    result: dict[str, dict[str, str]] = {}
    try:
        with _PRODUCTS_CSV.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                pid = row.get("product_id", "").strip()
                if pid:
                    result[pid] = row
    except Exception as exc:
        logger.warning("Could not load product catalog: %s", exc)
    _catalog_cache = result
    return result


def _resolve_supplier_id(product_id: str | None) -> str | None:
    """Look up supplier_id from the shared catalog. Never invent supplier IDs."""
    if not product_id:
        return None
    catalog = _load_catalog()
    row = catalog.get(product_id)
    if row is None:
        return None
    return row.get("supplier_id") or None


def _supporting_return_count(product_id: str | None, label: str) -> int:
    """Count historical returns for (product_id, label) from CSV.

    This is the DB/IO layer. The pure classifier does not call this.
    """
    if not product_id:
        return 0
    count = 0
    try:
        with _RETURNS_CSV.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                if (
                    row.get("product_id", "") == product_id
                    and row.get("root_cause_label", "") == label
                ):
                    count += 1
    except Exception as exc:
        logger.warning("Could not count historical returns: %s", exc)
    return count


def _check_emerging_spike(product_id: str | None, label: str) -> bool:
    """Delegate to the spike module when available; default to False."""
    try:
        from app.ml.spike import is_emerging_spike  # type: ignore[import]
        return bool(is_emerging_spike(product_id, label))
    except ImportError:
        return False
    except Exception as exc:
        logger.debug("Spike check failed: %s", exc)
        return False


def _load_fallback_prompt() -> str:
    try:
        return _PROMPT_PATH.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Could not load fallback prompt: %s", exc)
        return (
            "You are a root-cause classifier. "
            "Reply with exactly one label from: "
            + ", ".join(ROOT_CAUSES)
            + "\nProduct: {product}\nIssue: {issue}"
        )


def _call_llm_fallback(product: str, issue: str) -> str | None:
    """Call LLM and return a validated taxonomy label, or None on failure.

    Catches all LLM errors internally; never surfaces raw errors to callers.
    Returns None if LLM is unavailable or returns an invalid label.
    """
    try:
        from retail_common.llm_client import call_llm

        template = _load_fallback_prompt()
        prompt = template.replace("{product}", product).replace("{issue}", issue)
        raw = call_llm(prompt, max_tokens=50, temperature=0.0).strip()
        # Extract first word-like token (handles stray punctuation)
        candidate = re.split(r"\s+", raw)[0].rstrip(".,;:!?\"'").lower()
        # Replace spaces with underscore (in case model returns "manufacturing defect")
        candidate = candidate.replace(" ", "_")
        if candidate in ROOT_CAUSES:
            return candidate
        logger.warning("LLM fallback returned out-of-taxonomy label: %r", raw)
        return None
    except RuntimeError as exc:
        # LLM key not configured — silent degradation
        logger.info("LLM fallback skipped (not configured): %s", exc)
        return None
    except Exception as exc:
        logger.warning("LLM fallback error (suppressed): %s", exc)
        return None


def analyze_root_cause(
    product: str,
    issue: str,
    product_id: str | None = None,
    customer_ref: str | None = None,
    tenant_id: str = "demo",
) -> RootCauseOutput:
    """Full root-cause analysis pipeline.

    Args:
        product:      Product name (required, non-empty).
        issue:        Customer-reported issue text (required, non-empty).
        product_id:   Optional product ID for catalog and history lookup.
        customer_ref: Anonymised customer reference for abuse-risk scoring.
                      Must NOT be a real customer name.
        tenant_id:    Tenant context (recorded in notes).

    Returns:
        RootCauseOutput conforming to the shared schema.

    Raises:
        ValueError: if product or issue is empty/whitespace.
    """
    if not product or not product.strip():
        raise ValueError("product must not be empty or whitespace-only")
    if not issue or not issue.strip():
        raise ValueError("issue must not be empty or whitespace-only")

    notes: list[str] = [f"tenant_id={tenant_id}"]
    model_used: str = "tfidf_linearsvc_calibrated_v1"
    used_fallback = False

    # ── 1. Pure ML prediction ─────────────────────────────────────────────
    try:
        candidates, model_used, top_confidence = predict_top3(product, issue)
    except Exception as exc:
        logger.error("ML prediction failed: %s", exc)
        # Graceful degradation: return unknown
        return RootCauseOutput(
            product=product,
            issue=issue,
            candidates=[RootCauseCandidate(label="unknown", score=0.0)],
            top_candidate="unknown",
            confidence=0.0,
            product_id=product_id,
            supplier_id=_resolve_supplier_id(product_id),
            model_name="error_fallback",
            model_version=MODEL_VERSION,
            notes=notes + [f"prediction_error: {exc}"],
        )

    # ── 2. LLM fallback check ─────────────────────────────────────────────
    second_score = candidates[1].score if len(candidates) > 1 else 0.0
    gap = top_confidence - second_score

    needs_fallback = (top_confidence < _FALLBACK_TOP_PROB) or (gap < _FALLBACK_GAP)

    if needs_fallback:
        logger.info(
            "Triggering LLM fallback (top=%.3f, gap=%.3f)", top_confidence, gap
        )
        llm_label = _call_llm_fallback(product, issue)
        if llm_label and llm_label in ROOT_CAUSES:
            # Promote LLM label to top; rebuild candidates list
            llm_candidate = RootCauseCandidate(
                label=llm_label,
                score=round(min(top_confidence, 0.95), 4),
                supporting_return_count=0,
                top_terms=[],
            )
            # Keep remaining candidates but move promoted one to front
            remaining = [c for c in candidates if c.label != llm_label]
            candidates = [llm_candidate] + remaining[:2]
            model_used = "llm_fallback"
            used_fallback = True
            notes.append(f"llm_fallback_label={llm_label}")
        else:
            notes.append("llm_fallback=unavailable_or_invalid")

    # ── 3. Enrich with supporting_return_count (DB/IO layer) ─────────────
    for candidate in candidates:
        candidate.supporting_return_count = _supporting_return_count(
            product_id, candidate.label
        )

    # ── 4. Abuse risk ─────────────────────────────────────────────────────
    abuse_risk = compute_abuse_risk(
        customer_ref=customer_ref,
        order_value_lkr=None,       # not available at this call level
        purchase_date=None,
        return_date=None,
        returns_csv_path=_RETURNS_CSV,
    )

    # ── 5. Supplier resolution ────────────────────────────────────────────
    supplier_id = _resolve_supplier_id(product_id)

    # ── 6. Spike check ───────────────────────────────────────────────────
    top_label = candidates[0].label if candidates else "unknown"
    is_spike = _check_emerging_spike(product_id, top_label)

    # ── 7. Assemble output ────────────────────────────────────────────────
    final_confidence = round(min(candidates[0].score, 0.95), 4) if candidates else 0.0

    return RootCauseOutput(
        product=product,
        issue=issue,
        candidates=candidates[:3],
        top_candidate=top_label,
        confidence=final_confidence,
        product_id=product_id,
        supplier_id=supplier_id,
        model_name=model_used,
        model_version=MODEL_VERSION,
        is_emerging_spike=is_spike,
        abuse_risk=abuse_risk,
        notes=notes,
    )
