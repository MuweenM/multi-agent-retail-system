from app.tools.intake_tools import extract_return_info
from retail_common.schemas.intake import IntakeOutput


def test_extract_return_info_tool():
    text = "Returning my Dyson vacuum cleaner because the motor stopped working. Order #123456"
    output = extract_return_info(text)
    assert isinstance(output, IntakeOutput)
    assert "Dyson" in output.product or output.extracted_entities.get("brand") == "Dyson"
    assert "stop" in output.issue.lower() or "motor" in output.issue.lower()
    assert output.intent in ("return", "refund")
    assert output.confidence > 0.4
