from retail_common.schemas.intake import IntakeOutput
from ..nlp.extractor import IntakeExtractor

_extractor = IntakeExtractor()

def extract_return_info(text: str) -> IntakeOutput:
    return _extractor.extract(text)
