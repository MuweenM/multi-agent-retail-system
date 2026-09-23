"""Test Agent 1 Intake contract compliance."""

import os
import sys

# Ensure agent directory and project root are in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from shared.retail_common.schemas.intake import IntakeOutput
from shared.retail_common.schemas.bulk import BulkRow
from app.server import extract_return_info, extract_return_info_batch


def test_agent1_extract_return_info_contract():
    res = extract_return_info(text="Galaxy A15 battery dies fast", tenant_id="demo")
    assert isinstance(res, IntakeOutput)
    assert res.product != ""
    assert res.issue != ""
    assert res.intent in ("return", "exchange", "refund", "complaint", "unknown")
    assert res.raw_text == ""  # raw_text must be empty per contract security


def test_agent1_extract_batch_contract():
    rows = [
        BulkRow(return_id="RET-01", text="broken power bank P-014"),
        BulkRow(return_id="RET-02", text=""),
    ]
    res = extract_return_info_batch(rows=rows, tenant_id="demo")
    assert "results" in res
    assert "errors" in res
    assert len(res["results"]) == 1
    assert len(res["errors"]) == 1
    assert res["errors"][0]["row"] == 2
