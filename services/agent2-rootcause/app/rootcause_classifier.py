import re

from retail_common.schemas.rootcause import RootCauseCandidate, RootCauseOutput
from retail_common.taxonomy import ROOT_CAUSES

LABELS = list(ROOT_CAUSES)


def assert_valid_label(label: str) -> None:
    if label not in ROOT_CAUSES:
        raise ValueError(f"invalid root-cause label: {label}")

RULES = [
    (
        "manufacturing_defect",
        [
            "stopped working",
            "not working",
            "failed after",
            "broke after",
            "malfunction",
            "malfunctioning",
            "poor assembly",
            "broken on arrival",
            "cracked",
            "manufacturing issue",
            "faulty product",
            "defective product",
        ],
    ),
    (
        "damaged_in_transit",
        [
            "damaged in transit",
            "shipping damage",
            "package damage",
            "crushed",
            "dented",
            "torn box",
            "broken packaging",
            "arrived damaged",
            "chipped in transit",
        ],
    ),
    (
        "wrong_item_shipped",
        [
            "wrong item",
            "wrong product",
            "wrong order",
            "wrong pair",
            "incorrect item",
            "different product",
            "different model",
            "not the model i ordered",
            "sent the wrong thing",
        ],
    ),
    (
        "size_fit_issue",
        [
            "too small",
            "too large",
            "does not fit",
            "wrong size",
            "size issue",
            "tight fit",
            "loose fit",
            "ill fitting",
        ],
    ),
    (
        "quality_durability",
        [
            "poor quality",
            "low quality",
            "material issue",
            "fabric poor",
            "flimsy",
            "cheap material",
            "poor stitching",
            "quality problem",
        ],
    ),
    (
        "not_as_described",
        [
            "missing parts",
            "missing accessories",
            "missing charger",
            "missing cable",
            "incomplete package",
            "no parts",
            "accessory missing",
        ],
    ),
    (
        "change_of_mind",
        [
            "changed their mind",
            "changed my mind",
            "prefers different color",
            "different color",
            "customer preference",
            "doesn't like the style",
            "not what i wanted",
            "prefers another option",
        ],
    ),
]


def _normalize_text(value: str) -> str:
    if value is None:
        return ""
    text = str(value)
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _score_label(label: str, issue_text: str) -> float:
    assert_valid_label(label)
    for rule_label, keywords in RULES:
        assert_valid_label(rule_label)
        if rule_label != label:
            continue

        hits = 0
        for keyword in keywords:
            if keyword in issue_text:
                hits += 1

        if hits == 0:
            return 0.0

        # Stronger matches yield a higher score, but never exceed 1.0.
        score = min(1.0, 0.35 + (hits / max(len(keywords), 1)) * 0.65)
        return round(score, 4)

    return 0.0


def analyze_issue(product: str, issue: str) -> RootCauseOutput:
    product_text = _normalize_text(product)
    issue_text = _normalize_text(issue)
    combined_text = " ".join(part for part in [product_text, issue_text] if part).strip()

    if not combined_text:
        assert_valid_label("unknown")
        unknown_candidate = RootCauseCandidate(
            label="unknown",
            score=0.0,
            supporting_return_count=0,
        )
        return RootCauseOutput(
            product=product or "",
            issue=issue or "",
            candidates=[unknown_candidate],
            top_candidate="unknown",
            confidence=0.0,
        )

    candidate_scores = []
    for label in LABELS:
        assert_valid_label(label)
        score = _score_label(label, combined_text)
        candidate_scores.append(
            RootCauseCandidate(
                label=label,
                score=round(max(0.0, min(1.0, score)), 4),
                supporting_return_count=1 if score > 0 else 0,
            )
        )

    candidate_scores.sort(key=lambda item: (-item.score, item.label))

    top_candidate = candidate_scores[0].label if candidate_scores else "unknown"
    assert_valid_label(top_candidate)
    top_score = candidate_scores[0].score if candidate_scores else 0.0

    if top_score == 0.0:
        # Ensure unknown is included and returned when nothing matched the rules.
        for candidate in candidate_scores:
            if candidate.label == "unknown":
                candidate.score = 0.0
                candidate.supporting_return_count = 0
                break
        top_candidate = "unknown"
        assert_valid_label(top_candidate)
        top_score = 0.0

    return RootCauseOutput(
        product=product or "",
        issue=issue or "",
        candidates=candidate_scores,
        top_candidate=top_candidate,
        confidence=round(max(0.0, min(1.0, top_score)), 4),
    )
