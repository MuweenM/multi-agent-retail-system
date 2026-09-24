import importlib.util
from pathlib import Path

import pytest

from retail_common.taxonomy import ROOT_CAUSES


SERVICE_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = SERVICE_ROOT / "app" / "server.py"
SPEC = importlib.util.spec_from_file_location("agent3_retrieval_server", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)

reindex_corpus = MODULE.reindex_corpus
retrieve_evidence = MODULE.retrieve_evidence


def test_retrieve_evidence_returns_three_items_sorted_by_score():
    result = retrieve_evidence("battery drains quickly and motor overheats", top_k=5, tenant_id="demo")

    assert len(result.evidence) == 3
    assert [item.source_type for item in result.evidence] == [
        "review",
        "supplier_record",
        "policy",
    ]
    assert result.evidence[0].relevance_score >= result.evidence[1].relevance_score >= result.evidence[2].relevance_score
    assert all(item.label_hint in ROOT_CAUSES for item in result.evidence if item.label_hint)


def test_retrieve_evidence_caps_top_k_at_20():
    result = retrieve_evidence("battery issue", top_k=50)
    assert len(result.evidence) == 3
    assert result.total_results == 3


def test_retrieve_evidence_rejects_queries_longer_than_300_chars():
    long_query = "x" * 301
    with pytest.raises(ValueError, match="300 characters"):
        retrieve_evidence(long_query)


def test_reindex_corpus_returns_zero_counts():
    result = reindex_corpus(tenant_id="demo")
    assert result["tenant_id"] == "demo"
    assert result["documents_indexed"] == 0
    assert result["documents_updated"] == 0
    assert result["errors"] == 0
