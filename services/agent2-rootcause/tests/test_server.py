import asyncio

from retail_common.schemas.bulk import BulkSummary, ProductRootCauseReport
from retail_common.schemas.rootcause import RootCauseOutput
from retail_common.taxonomy import ROOT_CAUSES

from app.server import (
    analyze_bulk_patterns,
    analyze_product_root_cause,
    analyze_root_cause,
    server,
)


def test_exactly_three_public_tools_are_exposed():
    tools = asyncio.run(server.list_tools())

    assert {tool.name for tool in tools} == {
        "analyze_root_cause",
        "analyze_product_root_cause",
        "analyze_bulk_patterns",
    }


def test_analyze_root_cause_returns_schema_and_valid_labels():
    result = analyze_root_cause(
        "wireless earbuds",
        "one earbud stopped working",
        product_id="P-009",
        customer_ref="customer-1",
    )

    assert isinstance(result, RootCauseOutput)
    assert len(result.candidates) == 3
    assert all(candidate.label in ROOT_CAUSES for candidate in result.candidates)
    assert result.top_candidate in ROOT_CAUSES
    assert result.product_id == "P-009"


def test_product_and_bulk_tools_return_shared_schemas():
    product_result = analyze_product_root_cause("P-009")
    bulk_result = analyze_bulk_patterns("JOB-001")

    assert isinstance(product_result, ProductRootCauseReport)
    assert set(product_result.label_distribution).issubset(ROOT_CAUSES)
    assert isinstance(bulk_result, BulkSummary)


def test_tools_return_structured_models_for_invalid_input():
    root_result = analyze_root_cause("", "issue")
    product_result = analyze_product_root_cause("", 0)
    bulk_result = analyze_bulk_patterns("")

    assert isinstance(root_result, RootCauseOutput)
    assert root_result.top_candidate == "unknown"
    assert isinstance(product_result, ProductRootCauseReport)
    assert isinstance(bulk_result, BulkSummary)