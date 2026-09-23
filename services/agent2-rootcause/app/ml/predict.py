"""
Inference module for the Agent 2 root-cause classifier.

Production model: TF-IDF + LinearSVC wrapped in CalibratedClassifierCV
(class_weight="balanced"), trained in Prompt 4 and saved as rootcause_model.joblib.

Public API
----------
predict_top3(product_name, issue_text) -> list[RootCauseCandidate]

Constraints
-----------
- Pure function: no database access, no side effects.
- Input features: product name + issue text only. No customer, district,
  gender, or protected attributes are used.
- All returned labels are validated against ROOT_CAUSES.
- Confidence is capped at 0.95.
- Returns exactly 3 candidates (or fewer if the model has fewer classes).
"""

from __future__ import annotations

import threading
from pathlib import Path

import joblib

from retail_common.schemas.rootcause import RootCauseCandidate
from retail_common.taxonomy import ROOT_CAUSES

from app.ml.explain import explain_candidates
from app.ml.features import analyze_text


MODEL_PATH = Path(__file__).parents[1] / "models" / "rootcause_model.joblib"
CONFIDENCE_CAP: float = 0.95

# ── Thread-safe lazy model load ─────────────────────────────────────────────
_model_lock = threading.Lock()
_model_cache: dict[str, object] = {}


def _get_model(model_path: Path = MODEL_PATH):
    key = str(model_path)
    if key not in _model_cache:
        with _model_lock:
            if key not in _model_cache:
                _model_cache[key] = joblib.load(model_path)
    return _model_cache[key]


# ---------------------------------------------------------------------------
# Model version string — derived from saved results when available.
# ---------------------------------------------------------------------------

def _model_version_string(model_path: Path = MODEL_PATH) -> str:
    results_path = model_path.parent / "training_results.json"
    try:
        import json
        data = json.loads(results_path.read_text(encoding="utf-8"))
        return data.get("training_date", "")
    except Exception:
        return ""


MODEL_VERSION: str = _model_version_string()


# ---------------------------------------------------------------------------
# Core prediction — NO database access.
# ---------------------------------------------------------------------------

def predict_top3(
    product_name: str,
    issue_text: str,
    model_path: Path = MODEL_PATH,
    top_k: int = 3,
) -> tuple[list[RootCauseCandidate], str, float]:
    """Classify a return and return the top-k candidates.

    Args:
        product_name: Human-readable product name (e.g. "True Wireless Stereo Earbuds").
        issue_text:   Customer-reported issue text.
        model_path:   Path to the saved .joblib pipeline.
        top_k:        Number of top candidates to return (default 3).

    Returns:
        (candidates, model_name_str, top_confidence)
        - candidates: list of RootCauseCandidate, sorted by score descending.
          - label:   validated against ROOT_CAUSES.
          - score:   probability from CalibratedClassifierCV, capped at 0.95.
          - supporting_return_count: always 0 here (set by caller with DB data).
          - top_terms: up to 5 feature names explaining this candidate.
        - model_name_str: "tfidf_linearsvc_calibrated_v1"
        - top_confidence: score of the first candidate (already capped).

    Raises:
        RuntimeError: if the model file is missing or incompatible.
    """
    pipeline = _get_model(model_path)

    # Build input text: product name + issue only (no customer/district/gender)
    combined = analyze_text(f"{product_name} {issue_text}")

    # Obtain class probabilities from CalibratedClassifierCV
    proba = pipeline.predict_proba([combined])[0]          # shape (n_classes,)
    classes = list(pipeline.classes_)                      # imblearn Pipeline exposes classes_

    # Sort by probability descending
    ranked = sorted(zip(classes, proba), key=lambda pair: -pair[1])

    # Filter to valid taxonomy labels only
    valid_ranked = [
        (label, score) for label, score in ranked if label in ROOT_CAUSES
    ]

    # Take top-k
    top_k_items = valid_ranked[:top_k]
    top_labels = [label for label, _ in top_k_items]

    # Explain each candidate
    explanations = explain_candidates(pipeline, combined, top_labels, top_n=5)

    candidates: list[RootCauseCandidate] = []
    for label, score in top_k_items:
        capped_score = min(float(score), CONFIDENCE_CAP)
        candidates.append(
            RootCauseCandidate(
                label=label,
                score=round(capped_score, 4),
                supporting_return_count=0,   # caller fills this from DB
                top_terms=explanations.get(label, []),
            )
        )

    # Pad with "unknown" if fewer than top_k valid candidates found
    while len(candidates) < top_k:
        candidates.append(
            RootCauseCandidate(
                label="unknown",
                score=0.0,
                supporting_return_count=0,
                top_terms=[],
            )
        )

    top_confidence = candidates[0].score if candidates else 0.0
    return candidates, "tfidf_linearsvc_calibrated_v1", top_confidence