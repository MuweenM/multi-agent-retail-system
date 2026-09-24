from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Any, Iterable

from app.ir.bm25 import BM25Ranker
from app.ir.dense import DenseRanker
from shared.retail_common.schemas.evidence import EvidenceItem


@dataclass
class Hit:
    doc_id: str
    score: float
    source_type: str = ""
    product_id: str | None = None
    supplier_id: str | None = None
    date: str | None = None
    title: str = ""
    body: str = ""
    snippet: str = ""
    matched_terms: list[str] = field(default_factory=list)
    zone: str = "all"
    label_hint: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    method: str = "hybrid"

    def to_evidence(self) -> EvidenceItem:
        return EvidenceItem(
            source_type=self.source_type,
            source_id=self.doc_id,
            snippet=self.snippet,
            relevance_score=max(0.0, min(1.0, float(self.score))),
            title=self.title,
            method=self.method,
            matched_terms=self.matched_terms,
            zone=self.zone,
            label_hint=self.label_hint,
            metadata={k: str(v) for k, v in self.metadata.items()},
        )


class HybridRanker:
    def __init__(self, documents: Iterable[dict[str, Any]] | None = None, *, source_path: str | None = None, k: int = 60):
        self.documents = list(documents) if documents is not None else []
        self.k = k
        self.bm25 = BM25Ranker(self.documents or None, source_path=source_path)
        self.dense = DenseRanker(self.documents or None, source_path=source_path)

    @staticmethod
    def _normalise_scores(hits: list[dict[str, Any]]) -> dict[str, float]:
        if not hits:
            return {}
        max_score = max(hit["score"] for hit in hits)
        min_score = min(hit["score"] for hit in hits)
        if max_score == min_score:
            return {hit["doc_id"]: 1.0 for hit in hits}
        return {hit["doc_id"]: (hit["score"] - min_score) / (max_score - min_score) for hit in hits}

    def rank(self, query: str, top_k: int = 10, filters: dict[str, Any] | None = None, method: str = "rrf", weight_bm25: float = 0.5, weight_dense: float = 0.5) -> list[Hit]:
        bm25_hits = self.bm25.rank(query, top_k=max(top_k, 20), filters=filters)
        dense_hits = self.dense.rank(query, top_k=max(top_k, 20), filters=filters)
        bm25_by_doc = {hit.doc_id: hit for hit in bm25_hits}
        dense_by_doc = {hit.doc_id: hit for hit in dense_hits}

        if method == "weighted_sum":
            merged: dict[str, float] = {}
            for doc_id, hit in bm25_by_doc.items():
                merged[doc_id] = weight_bm25 * hit.score
            for doc_id, hit in dense_by_doc.items():
                merged[doc_id] = merged.get(doc_id, 0.0) + weight_dense * hit.score
        else:
            merged: dict[str, float] = {}
            for rank_index, hit in enumerate(bm25_hits, start=1):
                merged[hit.doc_id] = merged.get(hit.doc_id, 0.0) + 1.0 / (self.k + rank_index)
            for rank_index, hit in enumerate(dense_hits, start=1):
                merged[hit.doc_id] = merged.get(hit.doc_id, 0.0) + 1.0 / (self.k + rank_index)

        heap: list[tuple[float, str]] = []
        for doc_id, score in merged.items():
            item = (score, doc_id)
            if len(heap) < top_k:
                heapq.heappush(heap, item)
            elif score > heap[0][0]:
                heapq.heapreplace(heap, item)

        ranked_doc_ids = [doc_id for _, doc_id in sorted(heap, key=lambda pair: (-pair[0], pair[1]))]
        results: list[Hit] = []
        for doc_id in ranked_doc_ids:
            doc = self.bm25.index.docs.get(doc_id) or self.dense.index.docs.get(doc_id)
            if doc is None:
                continue
            matched_terms = set()
            for system in (bm25_by_doc.get(doc_id), dense_by_doc.get(doc_id)):
                if system is not None:
                    matched_terms.update(system.matched_terms)
            snippet = doc.get("body") or doc.get("title") or ""
            if len(snippet.split()) > 30:
                words = snippet.split()
                snippet = " ".join(words[:30])
            results.append(
                Hit(
                    doc_id=doc_id,
                    score=merged.get(doc_id, 0.0),
                    source_type=str(doc.get("source_type", "")),
                    product_id=doc.get("product_id"),
                    supplier_id=doc.get("supplier_id"),
                    date=doc.get("date"),
                    title=str(doc.get("title", "")),
                    body=str(doc.get("body", "")),
                    snippet=snippet,
                    matched_terms=sorted(matched_terms),
                    zone="body" if "body" in doc else "title",
                    label_hint=doc.get("label_hint"),
                    metadata={k: v for k, v in doc.items() if k not in {"title", "body", "supplier_notes"}},
                    method="hybrid",
                )
            )
        return results

    def rank_to_evidence(self, query: str, top_k: int = 10, filters: dict[str, Any] | None = None, method: str = "rrf", weight_bm25: float = 0.5, weight_dense: float = 0.5) -> list[EvidenceItem]:
        return [hit.to_evidence() for hit in self.rank(query, top_k=top_k, filters=filters, method=method, weight_bm25=weight_bm25, weight_dense=weight_dense)]
