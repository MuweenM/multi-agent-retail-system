import re

from retail_common.schemas.rootcause import RootCauseCandidate, RootCauseOutput

LABELS = [
    "manufacturing defect",
    "shipping or packaging damage",
    "wrong item fulfilled",
    "size or fit issue",
    "quality or material issue",
    "missing parts or accessories",
    "customer preference",
    "unknown",
]

RULES = [
    (
        "manufacturing defect",
        [
            "defect",
            "defective",
            "faulty",
            "broken on arrival",
            "manufacturing issue",
            "poor assembly",
            "malfunction",
        ],
    ),
    (
        "shipping or packaging damage",
        [
            "damaged in transit",
            "shipping damage",
            "package damage",
            "crushed",
            "dented",
            "torn box",
            "broken packaging",
            "arrived damaged",
        ],
    ),
    (
        "wrong item fulfilled",
        [
            "wrong item",
            "wrong product",
            "wrong order",
            "incorrect item",
            "different product",
            "different model",
            "sent the wrong thing",
        ],
    ),
    (
        "size or fit issue",
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
        "quality or material issue",
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
        "missing parts or accessories",
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
        "customer preference",
        [
            "changed mind",
            "prefers different color",
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
    for rule_label, keywords in RULES:
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
    top_score = candidate_scores[0].score if candidate_scores else 0.0

    if top_score == 0.0:
        # Ensure unknown is included and returned when nothing matched the rules.
        for candidate in candidate_scores:
            if candidate.label == "unknown":
                candidate.score = 0.0
                candidate.supporting_return_count = 0
                break
        top_candidate = "unknown"
        top_score = 0.0

    return RootCauseOutput(
        product=product or "",
        issue=issue or "",
        candidates=candidate_scores,
        top_candidate=top_candidate,
        confidence=round(max(0.0, min(1.0, top_score)), 4),
    )
