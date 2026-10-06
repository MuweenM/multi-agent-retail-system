from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Iterable

from ir_system.ir.inverted_index import InvertedIndex
from shared.retail_common.config import settings
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
    method: str = "dense"

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


class DenseRanker:
    def __init__(self, documents: Iterable[dict[str, Any]] | None = None, *, source_path: str | None = None, collection_name: str | None = None, persist_directory: str | None = None):
        self.index = InvertedIndex(documents, source_path=source_path) if documents is not None or source_path is not None else InvertedIndex([])
        self.collection_name = collection_name or getattr(settings, "vector_collection", "retail")
        self.persist_directory = persist_directory or getattr(settings, "vector_db_path", "./data/vector_store")
        self._client = None
        self._collection = None
        self._model = None

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
    def _document_text(doc: dict[str, Any]) -> str:
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

    def _ensure_model(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            self._model = None
            return None
        model_name = os.getenv("DENSE_MODEL_NAME") or os.getenv("EMBEDDING_MODEL") or "all-MiniLM-L6-v2"
        self._model = SentenceTransformer(model_name)
        return self._model

    def _ensure_collection(self):
        if self._collection is not None:
            return self._collection
        try:
            import chromadb
        except Exception:
            return None
        os.makedirs(self.persist_directory, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self.persist_directory)
        self._collection = self._client.get_or_create_collection(name=self.collection_name)
        return self._collection

    def _index_documents(self):
        collection = self._ensure_collection()
        if collection is None:
            return
        existing = set(collection.get(include=[]).get("ids", []))
        for doc_id, doc in self.index.docs.items():
            if doc_id in existing:
                continue
            text = self._document_text(doc)
            metadata = {key: str(value) for key, value in doc.items() if key not in {"title", "body", "supplier_notes"}}
            if self._ensure_model() is None:
                continue
            embedding = self._ensure_model().encode([text])[0].tolist()
            collection.add(ids=[doc_id], embeddings=[embedding], documents=[text], metadatas=[metadata])

    def rank(self, query: str, top_k: int = 10, filters: dict[str, Any] | None = None) -> list[Hit]:
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        query = query.strip()
        if not query:
            return []
        self._index_documents()
        collection = self._ensure_collection()
        query_terms = [token.term for token in analyze(query, mode="query", stem="porter")]
        if not collection or self._ensure_model() is None:
            filtered = self._filter_documents(self.index, filters)
            hits: list[Hit] = []
            for doc_id in sorted(filtered)[:top_k]:
                doc = self.index.docs[doc_id]
                matched = [term for term in query_terms if term in {token.term for token in analyze(self._document_text(doc), mode="index", stem="porter")}]
                snippet = self._snippet_for_doc(doc, matched or query_terms)
                hits.append(
                    Hit(
                        doc_id=doc_id,
                        score=1.0 if matched else 0.0,
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
            return hits

        where = None if not filters else {k: v for k, v in filters.items() if v is not None}
        q_emb = self._ensure_model().encode([query])[0].tolist()
        result = collection.query(query_embeddings=[q_emb], n_results=max(1, top_k), where=where, include=["documents", "metadatas", "distances"])
        hits: list[Hit] = []
        ids = result.get("ids", [[]])[0]
        distances = result.get("distances", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        docs = result.get("documents", [[]])[0]
        for doc_id, dist, meta, doc_text in zip(ids, distances, metadatas, docs):
            score = 1.0 / (1.0 + float(dist))
            doc = self.index.docs.get(doc_id, {})
            matched = [term for term in query_terms if term in {token.term for token in analyze(doc_text, mode="index", stem="porter")}]
            snippet = self._snippet_for_doc(doc, matched or query_terms) if doc else doc_text[:180]
            hits.append(
                Hit(
                    doc_id=str(doc_id),
                    score=score,
                    source_type=str(meta.get("source_type", doc.get("source_type", ""))),
                    product_id=meta.get("product_id") or doc.get("product_id"),
                    supplier_id=meta.get("supplier_id") or doc.get("supplier_id"),
                    date=meta.get("date") or doc.get("date"),
                    title=str(doc.get("title", "")),
                    body=str(doc.get("body", "")),
                    snippet=snippet,
                    matched_terms=matched,
                    zone="body" if "body" in doc else "title",
                    label_hint=doc.get("label_hint") if doc else None,
                    metadata={**meta, **{k: v for k, v in doc.items() if k not in {"title", "body", "supplier_notes"}}},
                )
            )
        return hits

    def rank_to_evidence(self, query: str, top_k: int = 10, filters: dict[str, Any] | None = None) -> list[EvidenceItem]:
        return [hit.to_evidence() for hit in self.rank(query, top_k=top_k, filters=filters)]
