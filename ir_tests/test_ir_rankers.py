import math

import pytest

from ir_system.ir.bm25 import BM25Ranker
from ir_system.ir.tfidf_ranker import TFIDFRanker


@pytest.fixture
def corpus():
    return [
        {
            "id": "d1",
            "source_type": "review",
            "product_id": "P-014",
            "supplier_id": "S-03",
            "date": "2026-09-05",
            "title": "Battery swelling risk",
            "body": "Battery swelling on the phone caused a dangerous overheating issue.",
            "supplier_notes": "Battery swelling and overheating were reported in QA.",
        },
        {
            "id": "d2",
            "source_type": "review",
            "product_id": "P-014",
            "supplier_id": "S-03",
            "date": "2026-09-07",
            "title": "Great battery life",
            "body": "Battery life is great and the phone is very reliable.",
            "supplier_notes": "Battery life feedback was positive in supplier notes.",
        },
        {
            "id": "d3",
            "source_type": "review",
            "product_id": "P-027",
            "supplier_id": "S-04",
            "date": "2026-09-08",
            "title": "Runs small",
            "body": "The shirt runs small and the fit is poor.",
            "supplier_notes": "Sizing review mentions runs small.",
        },
        {
            "id": "d4",
            "source_type": "supplier_record",
            "product_id": "P-009",
            "supplier_id": "S-02",
            "date": "2026-09-09",
            "title": "Battery life note",
            "body": "Battery life is great for this model.",
            "supplier_notes": "Supplier note: battery life is excellent and there is no defect.",
        },
    ]


def test_tfidf_ranking_returns_top_hits(corpus):
    r = TFIDFRanker(corpus)
    hits = r.rank("battery swelling", top_k=3, filters={})
    assert [h.doc_id for h in hits][:2] == ["d1", "d2"] or [h.doc_id for h in hits][0] == "d1"
    assert hits[0].score >= 0


def test_bm25_scores_match_rank_bm25(corpus):
    rank_bm25 = pytest.importorskip("rank_bm25")
    r = BM25Ranker(corpus)
    query = "battery swelling"
    hits = r.rank(query, top_k=10, filters={})
    scores = {h.doc_id: h.score for h in hits}

    # rank_bm25 library is only a check; compare values within 1e-6.
    tokenized = [doc["title"].lower().split() + doc["body"].lower().split() for doc in corpus]
    model = rank_bm25.BM25Okapi(tokenized)
    lib_scores = model.get_scores(query.lower().split())
    for doc_id, doc in zip([doc["id"] for doc in corpus], corpus):
        idx = [doc["id"] for doc in corpus].index(doc_id)
        if doc_id in scores:
            assert math.isclose(scores[doc_id], lib_scores[idx], rel_tol=0.0, abs_tol=1e-6), (doc_id, scores[doc_id], lib_scores[idx])
