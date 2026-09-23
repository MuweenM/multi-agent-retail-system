"""Test data contracts and backwards compatibility."""

from shared.retail_common import CONTRACT_VERSION
from shared.retail_common.taxonomy import (
    DECISIONS,
    INTENTS,
    ROOT_CAUSES,
    SENTIMENTS,
    SOURCE_TYPES,
)
from shared.retail_common.schemas.intake import IntakeOutput, Entity
from shared.retail_common.schemas.bulk import BulkRow, BulkJob, BulkSummary
from shared.retail_common.schemas.rootcause import RootCauseOutput
from shared.retail_common.schemas.evidence import EvidenceOutput
from shared.retail_common.schemas.decision import DecisionOutput


def test_contract_version():
    assert CONTRACT_VERSION == "1.1"


def test_taxonomy_uniqueness():
    assert len(ROOT_CAUSES) == len(set(ROOT_CAUSES))
    assert len(INTENTS) == len(set(INTENTS))
    assert len(SENTIMENTS) == len(set(SENTIMENTS))
    assert len(DECISIONS) == len(set(DECISIONS))
    assert len(SOURCE_TYPES) == len(set(SOURCE_TYPES))


def test_v10_compatibility_intake():
    # v1.0 payload missing new v1.1 fields must still validate
    v10_payload = {
        "raw_text": "phone screen is broken",
        "product": "Galaxy A15",
        "issue": "broken screen",
        "intent": "refund",
        "sentiment": "negative",
        "confidence": 0.85,
    }
    model = IntakeOutput.model_validate(v10_payload)
    assert model.product == "Galaxy A15"
    assert model.tenant_id == "demo"
    assert model.flags == []
    assert model.entities == []


def test_model_roundtrip_json():
    out = IntakeOutput(
        raw_text="",
        clean_text="Samsung Galaxy A15 battery drains fast",
        product="Samsung Galaxy A15",
        issue="battery drains fast",
        intent="return",
        sentiment="negative",
        confidence=0.92,
        entities=[Entity(type="PRODUCT", text="Samsung Galaxy A15", start=0, end=18)],
        flags=["spelling_corrected"],
    )
    json_str = out.model_dump_json()
    reloaded = IntakeOutput.model_validate_json(json_str)
    assert reloaded.confidence == 0.92
    assert len(reloaded.entities) == 1
    assert reloaded.flags == ["spelling_corrected"]
