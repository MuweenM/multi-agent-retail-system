from retail_common.schemas.rootcause import RootCauseOutput

from app.rootcause_classifier import analyze_issue


def analyze_root_cause(product: str, issue: str) -> RootCauseOutput:
    if not product or not product.strip():
        raise ValueError("product must not be empty or whitespace-only")
    if not issue or not issue.strip():
        raise ValueError("issue must not be empty or whitespace-only")

    return analyze_issue(product, issue)