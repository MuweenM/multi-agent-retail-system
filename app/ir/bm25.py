from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Any, Iterable

from app.ir.inverted_index import InvertedIndex
from shared.retail_common.schemas.evidence import EvidenceItem
from shared.retail_common.text.analyzer import analyze


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
    method: str = "bm25"

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


class BM25Ranker:
    k1 = 1.5
    b = 0.75

    def __init__(self, documents: Iterable[dict[str, Any]] | None = None, *, source_path: str | None = None):
        self.index = InvertedIndex(documents, source_path=source_path) if documents is not None or source_path is not None else InvertedIndex([])

    @staticmethod
    def _filter_documents(index: InvertedIndex, filters: dict[str, Any] | None) -> set[str]:
        doc_ids = set(index.docs)
        if not filters:
            return doc_ids
        for key, value in filters.items():
            if value is None:
                continue
            doc_ids = {doc_id for doc_id in doc_ids if str(index.docs.get(doc_id, {}).get(key)) == str(value)}
        return doc_ids

    @staticmethod
    def _doc_tokens(doc: dict[str, Any]) -> list[str]:
        chunks = [str(doc.get(zone, "") or "") for zone in ("title", "body", "supplier_notes")]
        tokens: list[str] = []
        for chunk in chunks:
            tokens.extend(token.term for token in analyze(chunk, mode="index", stem="porter"))
        return tokens

    @staticmethod
    def _snippet_for_doc(doc: dict[str, Any], query_terms: list[str]) -> str:
        words: list[str] = []
        for zone in ("title", "body", "supplier_notes"):
            words.extend(str(doc.get(zone, "") or "").split())
        if not words:
            return ""
        norm = {term.lower() for term in query_terms}
        for idx, word in enumerate(words):
            if word.lower() in norm:
                start = max(0, idx - 15)
                end = min(len(words), idx + 15)
                return " ".join(words[start:end])
        return " ".join(words[:30])

    def rank(self, query: str, top_k: int = 10, filters: dict[str, Any] | None = None) -> list[Hit]:
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        query = query.strip()
        if not query:
            return []
        q_tokens = [token.term for token in analyze(query, mode="query", stem="porter")]
        if not q_tokens:
            return []
        query_terms = list(dict.fromkeys(q_tokens))
        candidate_docs = self._filter_documents(self.index, filters)
        if not candidate_docs:
            return []

        N = len(self.index.docs)
        doc_lengths = {doc_id: len(self._doc_tokens(doc)) for doc_id, doc in self.index.docs.items()}
        avgdl = sum(doc_lengths.values()) / max(1, N)

        idfs: dict[str, float] = {}
        for term in query_terms:
            df = self.index.term_index.get(term, {}).get("df", 0)
            if df <= 0:
                continue
            idfs[term] = math.log((N - df + 0.5) / (df + 0.5) + 1.0)

        scores: dict[str, float] = {}
        term_matches: dict[str, set[str]] = {term: set() for term in query_terms}
        for doc_id in candidate_docs:
            doc = self.index.docs[doc_id]
            doc_tokens = self._doc_tokens(doc)
            doc_freq = {}
            for token in doc_tokens:
                doc_freq[token] = doc_freq.get(token, 0) + 1
            total = 0.0
            matched = set()
            for term in query_terms:
                if term not in idfs:
                    continue
                tf = doc_freq.get(term, 0)
                if tf <= 0:
                    continue
                matched.add(term)
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (len(doc_tokens) / avgdl if avgdl > 0 else 1.0))
                total += idfs[term] * (numerator / denominator)
            if total > 0:
                scores[doc_id] = total
                term_matches[doc_id] = matched

        if not scores:
            return []

        heap: list[tuple[float, str]] = []
        for doc_id, score in scores.items():
            item = (score, doc_id)
            if len(heap) < top_k:
                heapq.heappush(heap, item)
            elif score > heap[0][0]:
                heapq.heapreplace(heap, item)

        ranked = [doc_id for _, doc_id in sorted(heap, key=lambda pair: (-pair[0], pair[1]))]
        results: list[Hit] = []
        for doc_id in ranked:
            doc = self.index.docs[doc_id]
            matched = sorted(term_matches.get(doc_id, set()))
            snippet = self._snippet_for_doc(doc, matched or query_terms)
            results.append(
                Hit(
                    doc_id=doc_id,
                    score=scores[doc_id],
                    source_type=str(doc.get("source_type", "")),
                    product_id=doc.get("product_id"),
                    supplier_id=doc.get("supplier_id"),
                    date=doc.get("date"),
                    title=str(doc.get("title", "")),
                    body=str(doc.get("body", "")),
                    snippet=snippet,
                    matched_terms=matched,
                    zone="body" if "body" in doc else "title",
                    label_hint=doc.get("label_hint"),
                    metadata={k: v for k, v in doc.items() if k not in {"title", "body", "supplier_notes"}},
                )
            )
        return results

    def rank_to_evidence(self, query: str, top_k: int = 10, filters: dict[str, Any] | None = None) -> list[EvidenceItem]:
        return [hit.to_evidence() for hit in self.rank(query, top_k=top_k, filters=filters)]
