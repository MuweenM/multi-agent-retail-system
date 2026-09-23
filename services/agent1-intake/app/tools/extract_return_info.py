"""Tool wrapper for single return info extraction."""

from shared.retail_common.schemas.intake import IntakeOutput
from app.nlp.pipeline import process_intake_pipeline


def run_extract_return_info(
    text: str,
    tenant_id: str = "demo",
    lang_hint: str | None = None,
) -> IntakeOutput:
    """Extract return info using full NLP pipeline."""
    return process_intake_pipeline(text=text, tenant_id=tenant_id, lang_hint=lang_hint)
