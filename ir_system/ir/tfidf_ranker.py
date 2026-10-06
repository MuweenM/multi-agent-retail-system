from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field
from typing import Any, Iterable

from ir_system.ir.inverted_index import InvertedIndex
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
    method: str = "tfidf"

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


class TFIDFRanker:
    def __init__(self, documents: Iterable[dict[str, Any]] | None = None, *, source_path: str | None = None, champion_r: int = 0, use_champion_lists: bool = False):
        self.index = InvertedIndex(documents, source_path=source_path) if documents is not None or source_path is not None else InvertedIndex([])
        self.champion_r = champion_r
        self.use_champion_lists = use_champion_lists

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
    def _extract_text(doc: dict[str, Any]) -> str:
        return " ".join(str(doc.get(zone, "") or "") for zone in ("title", "body", "supplier_notes"))

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

    @staticmethod
    def _candidate_docs(index: InvertedIndex, query_terms: list[str], *, use_champion_lists: bool, champion_r: int) -> set[str]:
        if not query_terms:
            return set(index.docs)
        if not use_champion_lists or champion_r <= 0:
            return set(index.docs)
        candidates: set[str] = set()
        for term in query_terms:
            entry = index.term_index.get(term)
            if not entry:
                continue
            postings = []
            for postings_by_zone in entry.get("postings", {}).values():
                postings.extend(postings_by_zone)
            top = sorted(postings, key=lambda p: p.tf, reverse=True)[:champion_r]
            candidates.update(post.doc_id for post in top)
        return candidates or set(index.docs)

    def rank(self, query: str, top_k: int = 10, filters: dict[str, Any] | None = None) -> list[Hit]:
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        query = query.strip()
        if not query:
            return []
        query_terms = [token.term for token in analyze(query, mode="query", stem="porter")]
        if not query_terms:
            return []
        unique_terms = list(dict.fromkeys(query_terms))
        candidate_docs = self._candidate_docs(self.index, unique_terms, use_champion_lists=self.use_champion_lists, champion_r=self.champion_r or 0)
        filtered_docs = self._filter_documents(self.index, filters)
        candidate_docs &= filtered_docs

        if not candidate_docs:
            return []

        num_docs = len(self.index.docs)
        query_weights: dict[str, float] = {}
        for term in unique_terms:
            df = self.index.term_index.get(term, {}).get("df", 0)
            if df <= 0:
                continue
            query_weights[term] = (1.0 + math.log10(max(1, sum(1 for tok in query_terms if tok == term)))) * math.log10(num_docs / df)

        doc_norms: dict[str, float] = {}
        doc_scores: dict[str, float] = {}
        matched_terms_by_doc: dict[str, set[str]] = {}
        for doc_id in candidate_docs:
            doc = self.index.docs[doc_id]
            doc_term_counts: dict[str, float] = {}
            for term in unique_terms:
                entry = self.index.term_index.get(term)
                if not entry:
                    continue
                total_tf = 0.0
                for zone_postings in entry.get("postings", {}).values():
                    for posting in zone_postings:
                        if posting.doc_id == doc_id:
                            total_tf += float(posting.tf)
                if total_tf > 0:
                    df = entry.get("df", 0)
                    weight = (1.0 + math.log10(total_tf)) * math.log10(num_docs / df) if df > 0 else 0.0
                    doc_term_counts[term] = weight
            if not doc_term_counts:
                continue
            norm = math.sqrt(sum(value * value for value in doc_term_counts.values()))
            if norm == 0:
                continue
            doc_norms[doc_id] = norm
            matched_terms_by_doc[doc_id] = set(doc_term_counts)
            score = 0.0
            for term, q_weight in query_weights.items():
                d_weight = doc_term_counts.get(term, 0.0)
                if d_weight > 0:
                    score += q_weight * d_weight
            doc_scores[doc_id] = score / (math.sqrt(sum(q * q for q in query_weights.values())) * norm) if query_weights else 0.0

        heap: list[tuple[float, str]] = []
        for doc_id, score in doc_scores.items():
            item = (score, doc_id)
            if len(heap) < top_k:
                heapq.heappush(heap, item)
            elif score > heap[0][0]:
                heapq.heapreplace(heap, item)

        ranked = [doc_id for _, doc_id in sorted(heap, key=lambda pair: (-pair[0], pair[1]))]
        result: list[Hit] = []
        for doc_id in ranked:
            doc = self.index.docs[doc_id]
            matched = sorted(matched_terms_by_doc.get(doc_id, set()))
            snippet = self._snippet_for_doc(doc, matched or unique_terms)
            hit = Hit(
                doc_id=doc_id,
                score=doc_scores[doc_id],
                source_type=str(doc.get("source_type", "")),
                product_id=doc.get("product_id"),
                supplier_id=doc.get("supplier_id"),
                date=doc.get("date"),
                title=str(doc.get("title", "")),
                body=str(doc.get("body", "")),
                snippet=snippet,
                matched_terms=matched,
                zone="body" if snippet and "body" in doc else "title",
                label_hint=doc.get("label_hint"),
                metadata={k: v for k, v in doc.items() if k not in {"title", "body", "supplier_notes"}},
            )
            result.append(hit)
        return result

    def rank_to_evidence(self, query: str, top_k: int = 10, filters: dict[str, Any] | None = None) -> list[EvidenceItem]:
        return [hit.to_evidence() for hit in self.rank(query, top_k=top_k, filters=filters)]
