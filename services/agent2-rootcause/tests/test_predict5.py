"""
Prompt 5 tests for Agent 2: prediction, explanations, LLM fallback, and abuse risk.

Test cases (all 8 required by the spec):
1. Normal prediction returns a valid RootCauseOutput.
2. Top-3 candidate labels are valid taxonomy values.
3. Confidence is never greater than 0.95.
4. The planted P-014 battery-swelling case is handled correctly.
5. A vague/low-confidence issue triggers fallback behavior.
6. An LLM fallback response outside taxonomy is rejected or mapped safely.
7. Abuse-risk calculation does not use prohibited fields.
8. Database access is not embedded inside the pure classifier.

Privacy contract:
- No real customer information appears in any test output or fixture.
- All customer references use pseudonymous identifiers (e.g. "cust-test-001").
"""

from __future__ import annotations

import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from retail_common.schemas.rootcause import RootCauseCandidate, RootCauseOutput
from retail_common.taxonomy import ROOT_CAUSES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_pipeline(classes, proba_row):
    """Build a minimal mock pipeline that predict_top3 can consume."""
    mock = MagicMock()
    mock.predict_proba.return_value = [proba_row]
    mock.classes_ = classes

    # Minimal TF-IDF step mock
    tfidf_mock = MagicMock()
    import numpy as np
    import scipy.sparse as sp
    n_features = 10
    tfidf_mock.transform.return_value = sp.csr_matrix(
        np.zeros((1, n_features), dtype=float)
    )
    tfidf_mock.get_feature_names_out.return_value = np.array(
        [f"feat_{i}" for i in range(n_features)]
    )
    mock.named_steps = {"features": tfidf_mock, "classifier": MagicMock()}
    return mock


# ---------------------------------------------------------------------------
# 1. Normal prediction returns a valid RootCauseOutput
# ---------------------------------------------------------------------------

def test_normal_prediction_returns_valid_rootcauseoutput():
    """A clear, specific return issue should produce a valid RootCauseOutput."""
    from app.tools.analyze_root_cause import analyze_root_cause

    result = analyze_root_cause(
        product="20000 mAh Fast Charge Power Bank",
        issue="Battery started swelling after third charge cycle",
        product_id="P-014",
        customer_ref=None,
        tenant_id="test",
    )

    assert isinstance(result, RootCauseOutput)
    assert result.product == "20000 mAh Fast Charge Power Bank"
    assert result.issue == "Battery started swelling after third charge cycle"
    assert result.top_candidate in ROOT_CAUSES
    assert isinstance(result.confidence, float)
    assert isinstance(result.candidates, list)
    assert len(result.candidates) > 0


# ---------------------------------------------------------------------------
# 2. Top-3 candidate labels are valid taxonomy values
# ---------------------------------------------------------------------------

def test_top3_candidate_labels_are_valid_taxonomy():
    """All candidates in the top-3 must be labels from ROOT_CAUSES."""
    from app.tools.analyze_root_cause import analyze_root_cause

    result = analyze_root_cause(
        product="True Wireless Stereo Earbuds",
        issue="One earbud stopped working after two days of use",
        product_id="P-009",
        customer_ref=None,
        tenant_id="test",
    )

    assert len(result.candidates) <= 3
    for candidate in result.candidates:
        assert candidate.label in ROOT_CAUSES, (
            f"Candidate label {candidate.label!r} is not a valid ROOT_CAUSES value"
        )


# ---------------------------------------------------------------------------
# 3. Confidence is never greater than 0.95
# ---------------------------------------------------------------------------

def test_confidence_never_exceeds_0_95():
    """The final confidence score must always be capped at 0.95."""
    from app.ml.predict import predict_top3, MODEL_PATH, CONFIDENCE_CAP

    # Monkey-patch joblib.load to return a controlled pipeline
    import numpy as np

    classes = list(ROOT_CAUSES)
    # Manufacture artificially high probabilities (would exceed 0.95 uncapped)
    proba = [0.99] + [0.001 / (len(classes) - 1)] * (len(classes) - 1)
    # Normalise
    total = sum(proba)
    proba = [p / total for p in proba]

    mock_pipeline = _make_mock_pipeline(classes, proba)

    with patch("app.ml.predict._get_model", return_value=mock_pipeline):
        candidates, _, top_confidence = predict_top3(
            "any product", "any issue"
        )

    assert top_confidence <= CONFIDENCE_CAP, (
        f"top_confidence {top_confidence} exceeds cap {CONFIDENCE_CAP}"
    )
    for candidate in candidates:
        assert candidate.score <= CONFIDENCE_CAP, (
            f"candidate score {candidate.score} exceeds cap {CONFIDENCE_CAP}"
        )


# ---------------------------------------------------------------------------
# 4. Planted P-014 battery-swelling case is handled correctly
# ---------------------------------------------------------------------------

def test_planted_p014_battery_swelling():
    """P-014 battery swelling should resolve to manufacturing_defect.

    This is the planted pattern documented in data/PLANTED.md:
    'P-014 from S-03, batch B-2026-07: battery swelling, a manufacturing_defect
    spike in the last 3 weeks.'
    """
    from app.tools.analyze_root_cause import analyze_root_cause

    result = analyze_root_cause(
        product="20000 mAh Fast Charge Power Bank",
        issue="Battery swelling on the power bank after charging",
        product_id="P-014",
        customer_ref=None,
        tenant_id="test",
    )

    assert isinstance(result, RootCauseOutput)
    assert result.top_candidate == "manufacturing_defect", (
        f"Expected manufacturing_defect for P-014 battery swelling, got {result.top_candidate!r}"
    )
    # Supplier should resolve from catalog (P-014 → S-03)
    assert result.supplier_id == "S-03", (
        f"Expected supplier_id='S-03' for P-014, got {result.supplier_id!r}"
    )
    # supporting_return_count should be populated from historical data
    top_candidate_obj = result.candidates[0]
    assert top_candidate_obj.supporting_return_count >= 0  # non-negative


# ---------------------------------------------------------------------------
# 5. Vague / low-confidence issue triggers fallback behaviour
# ---------------------------------------------------------------------------

def test_vague_issue_triggers_fallback_behaviour():
    """An ambiguous issue should trigger the LLM fallback path when top
    probability is below the threshold or margin is too small."""
    from app.tools import analyze_root_cause as arc_module
    from app.tools.analyze_root_cause import _FALLBACK_TOP_PROB, _FALLBACK_GAP

    import numpy as np

    n_classes = len(ROOT_CAUSES)
    # Uniform distribution: every class has equal probability → gap < threshold
    uniform_proba = [1.0 / n_classes] * n_classes
    classes = list(ROOT_CAUSES)

    mock_pipeline = _make_mock_pipeline(classes, uniform_proba)
    fallback_was_called = []

    def mock_llm_fallback(product, issue):
        fallback_was_called.append((product, issue))
        return "unknown"  # valid taxonomy label

    with (
        patch("app.ml.predict._get_model", return_value=mock_pipeline),
        patch.object(arc_module, "_call_llm_fallback", side_effect=mock_llm_fallback),
    ):
        result = arc_module.analyze_root_cause(
            product="desk chair",
            issue="I don't know, something is wrong but I can't describe it",
            product_id=None,
            customer_ref=None,
            tenant_id="test",
        )

    # Fallback must have been called
    assert len(fallback_was_called) == 1, "LLM fallback was not triggered"
    assert isinstance(result, RootCauseOutput)
    assert result.top_candidate in ROOT_CAUSES


# ---------------------------------------------------------------------------
# 6. LLM fallback response outside taxonomy is rejected / mapped safely
# ---------------------------------------------------------------------------

def test_llm_fallback_invalid_label_is_rejected():
    """If the LLM returns a label not in ROOT_CAUSES, it must be discarded
    and the system must still return a valid RootCauseOutput."""
    from app.tools import analyze_root_cause as arc_module

    import numpy as np

    n_classes = len(ROOT_CAUSES)
    # Trigger fallback with uniform distribution
    uniform_proba = [1.0 / n_classes] * n_classes
    classes = list(ROOT_CAUSES)
    mock_pipeline = _make_mock_pipeline(classes, uniform_proba)

    def bad_llm_fallback(product, issue):
        # Returns a label completely outside the taxonomy
        return "totally_invalid_label_xyz"

    with (
        patch("app.ml.predict._get_model", return_value=mock_pipeline),
        patch.object(arc_module, "_call_llm_fallback", side_effect=bad_llm_fallback),
    ):
        result = arc_module.analyze_root_cause(
            product="some product",
            issue="vague issue text",
            product_id=None,
            customer_ref=None,
            tenant_id="test",
        )

    # Output must be a valid schema regardless
    assert isinstance(result, RootCauseOutput)
    assert result.top_candidate in ROOT_CAUSES
    # model_name should NOT be llm_fallback when the LLM label was invalid
    assert result.model_name != "llm_fallback", (
        "model_name should not be 'llm_fallback' when the LLM label was invalid"
    )
    for candidate in result.candidates:
        assert candidate.label in ROOT_CAUSES


# ---------------------------------------------------------------------------
# 7. Abuse-risk calculation does not use prohibited fields
# ---------------------------------------------------------------------------

def test_abuse_risk_does_not_use_prohibited_fields():
    """The abuse risk module must not accept or use customer name, district,
    gender, or any protected attribute as a feature."""
    from app.ml.abuse import compute_abuse_risk
    import inspect

    # Inspect the function signature: prohibited parameter names must be absent
    sig = inspect.signature(compute_abuse_risk)
    param_names = set(sig.parameters.keys())

    prohibited = {"name", "customer_name", "district", "gender", "ethnicity", "race"}
    violations = prohibited & param_names
    assert not violations, (
        f"compute_abuse_risk accepts prohibited parameters: {violations}"
    )

    # Verify the function runs with allowed parameters only
    result = compute_abuse_risk(
        customer_ref="cust-test-001",        # pseudonymous ID only
        order_value_lkr=7500.0,
        purchase_date="2026-09-01",
        return_date="2026-09-10",
        returns_csv_path=Path("data/returns/returns.csv"),
    )

    assert isinstance(result, float)
    assert 0.0 <= result <= 1.0, f"Abuse risk {result} is out of [0, 1] range"


def test_abuse_risk_source_code_does_not_reference_district():
    """The abuse risk module source code must not reference district, gender,
    or customer name as model features."""
    import app.ml.abuse as abuse_module
    import inspect

    source = inspect.getsource(abuse_module)
    # These are flagged only if they appear as dict key lookups on row data
    prohibited_patterns = [
        'row["district"]',
        "row['district']",
        'row["gender"]',
        "row['gender']",
        'row["customer_name"]',
    ]
    for pattern in prohibited_patterns:
        assert pattern not in source, (
            f"Prohibited pattern {pattern!r} found in abuse.py source"
        )


# ---------------------------------------------------------------------------
# 8. Database access is not embedded inside the pure classifier
# ---------------------------------------------------------------------------

def test_pure_classifier_has_no_db_access():
    """The predict module must not import or use any database layer."""
    import app.ml.predict as predict_module
    import inspect

    source = inspect.getsource(predict_module)

    # These imports indicate DB access in the wrong layer
    db_indicators = [
        "from retail_common.db",
        "import sqlalchemy",
        "SessionLocal",
        "get_db",
        "csv.DictReader",
        "open(",
    ]
    for indicator in db_indicators:
        assert indicator not in source, (
            f"DB/IO indicator {indicator!r} found in pure predict module"
        )


def test_predict_top3_does_not_call_open(tmp_path):
    """predict_top3 must not open any files during a normal call."""
    from app.ml.predict import predict_top3

    import numpy as np

    classes = list(ROOT_CAUSES)
    proba = [1.0 / len(classes)] * len(classes)
    mock_pipeline = _make_mock_pipeline(classes, proba)

    open_calls = []
    original_open = open

    def tracking_open(*args, **kwargs):
        open_calls.append(args)
        return original_open(*args, **kwargs)

    with patch("app.ml.predict._get_model", return_value=mock_pipeline):
        # predict_top3 should not call open() during inference
        import builtins
        with patch.object(builtins, "open", side_effect=tracking_open):
            try:
                candidates, model_name, top_conf = predict_top3(
                    "some product", "some issue"
                )
            except Exception:
                pass  # If it fails, the open_calls check still applies

    assert open_calls == [], (
        f"predict_top3 opened files during inference: {open_calls}"
    )
