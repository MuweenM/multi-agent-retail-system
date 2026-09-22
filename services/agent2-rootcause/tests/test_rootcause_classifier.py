import pytest

from retail_common.schemas.rootcause import RootCauseOutput
from app.rootcause_classifier import analyze_issue
from app.tools import rootcause


@pytest.mark.parametrize(
    ("product", "issue", "expected_label"),
    [
        ("wireless earbuds", "one earbud stopped working after two days", "manufacturing defect"),
        (
            "ceramic coffee mug set",
            "box arrived crushed and the mug was chipped in transit",
            "shipping or packaging damage",
        ),
        ("running shoes", "received the wrong pair and not the model I ordered", "wrong item fulfilled"),
        ("jeans", "too small around the waist and does not fit", "size or fit issue"),
        ("cotton shirt", "fabric feels flimsy and poor quality after first wash", "quality or material issue"),
        ("tablet", "missing charger and case from the package", "missing parts or accessories"),
        ("lamp", "customer changed their mind and prefers a different color", "customer preference"),
    ],
)
def test_known_issue_classifications(product, issue, expected_label):
    result = analyze_issue(product, issue)

    assert isinstance(result, RootCauseOutput)
    assert result.product == product
    assert result.issue == issue
    assert result.top_candidate == expected_label
    assert result.candidates
    assert result.candidates[0].label == expected_label
    assert 0.0 <= result.confidence <= 1.0


def test_unknown_fallback_when_no_rule_matches():
    result = analyze_issue("desk chair", "customer is frustrated but did not describe a clear defect")

    assert result.top_candidate == "unknown"
    assert "unknown" in {candidate.label for candidate in result.candidates}
    assert 0.0 <= result.confidence <= 1.0


def test_whitespace_normalization():
    result = analyze_issue("  wireless earbuds  ", "   one   earbud   stopped   working   after   two   days   ")

    assert result.top_candidate == "manufacturing defect"
    assert result.product == "  wireless earbuds  "
    assert result.issue == "   one   earbud   stopped   working   after   two   days   "


def test_case_insensitive_matching():
    result = analyze_issue("tablet", "MISSING CHARGER AND CASE FROM THE PACKAGE")

    assert result.top_candidate == "missing parts or accessories"


def test_deterministic_candidate_ordering():
    result = analyze_issue("coffee mug set", "box was crushed and arrived damaged in transit")

    labels = [candidate.label for candidate in result.candidates]
    assert labels == sorted(labels, key=lambda label: (-next(candidate.score for candidate in result.candidates if candidate.label == label), label))
    assert result.candidates[0].score >= result.candidates[1].score


def test_confidence_range_and_output_shape():
    result = analyze_issue("lamp", "the product arrived damaged in transit")

    assert isinstance(result, RootCauseOutput)
    assert set(type(result).model_fields.keys()) == {"product", "issue", "candidates", "top_candidate", "confidence"}
    assert all(0.0 <= candidate.score <= 1.0 for candidate in result.candidates)
    assert all(candidate.supporting_return_count >= 0 for candidate in result.candidates)
    assert 0.0 <= result.confidence <= 1.0


def test_valid_rootcause_output_fields_for_unknown_case():
    result = analyze_issue("", "")

    assert isinstance(result, RootCauseOutput)
    assert result.product == ""
    assert result.issue == ""
    assert result.top_candidate == "unknown"
    assert result.candidates[0].label == "unknown"
    assert result.confidence == 0.0


@pytest.mark.parametrize("product", ["", "   "])
def test_public_tool_rejects_empty_product(product):
    with pytest.raises(ValueError, match="product must not be empty or whitespace-only"):
        rootcause.analyze_root_cause(product, "stopped working")


@pytest.mark.parametrize("issue", ["", "   "])
def test_public_tool_rejects_empty_issue(issue):
    with pytest.raises(ValueError, match="issue must not be empty or whitespace-only"):
        rootcause.analyze_root_cause("wireless earbuds", issue)


def test_public_tool_delegates_and_returns_rootcause_output(monkeypatch):
    expected = RootCauseOutput(
        product="wireless earbuds",
        issue="stopped working",
        candidates=[],
        top_candidate="manufacturing defect",
        confidence=0.9,
    )
    calls = []

    def fake_analyze_issue(product, issue):
        calls.append((product, issue))
        return expected

    monkeypatch.setattr(rootcause, "analyze_issue", fake_analyze_issue)

    result = rootcause.analyze_root_cause("wireless earbuds", "stopped working")

    assert result is expected
    assert calls == [("wireless earbuds", "stopped working")]
