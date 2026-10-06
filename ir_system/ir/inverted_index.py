from __future__ import annotations

import gzip
import json
import math
import os
import pickle
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from shared.retail_common.text.analyzer import analyze


@dataclass
class Posting:
    """Lecture concept: posting list entry storing document evidence and positions."""

    doc_id: str
    tf: int
    positions: list[int] = field(default_factory=list)


class InvertedIndex:
    """Lecture concept: positional inverted index with boolean, phrase, and proximity search."""

    VALID_ZONES = ("title", "body", "supplier_notes")

    def __init__(self, documents: Iterable[dict[str, Any]] | None = None, *, source_path: str | Path | None = None):
        self.docs: dict[str, dict[str, Any]] = {}
        self.term_index: dict[str, dict[str, Any]] = {}
        self.doc_id_order: list[str] = []
        self.stats: dict[str, Any] = {"build_time": 0.0, "index_bytes": 0, "index_size_bytes": 0, "comparisons_saved": 0}
        if documents is not None:
            self.build(documents)
        elif source_path is not None:
            loaded = type(self).load(source_path)
            self.__dict__.update(loaded.__dict__)

    def build(self, documents: Iterable[dict[str, Any]]) -> "InvertedIndex":
        """Lecture concept: index construction and document-frequency accumulation."""
        start = time.perf_counter()
        self.docs = {}
        self.term_index = {}
        self.doc_id_order = []

        for raw in documents:
            doc = dict(raw)
            doc_id = str(doc.get("id") or doc.get("doc_id") or len(self.doc_id_order))
            self.docs[doc_id] = doc
            self.doc_id_order.append(doc_id)

        for doc_id in self.doc_id_order:
            doc = self.docs[doc_id]
            for zone in self.VALID_ZONES:
                text = str(doc.get(zone) or "")
                if not text:
                    continue
                counts: dict[str, int] = defaultdict(int)
                positions: dict[str, list[int]] = defaultdict(list)
                for token in analyze(text, mode="index", stem="porter"):
                    term = token.term
                    counts[term] += 1
                    positions[term].append(token.position)
                for term, tf in counts.items():
                    entry = self.term_index.setdefault(term, {"df": 0, "postings": {}})
                    entry["postings"].setdefault(zone, []).append(Posting(doc_id=doc_id, tf=tf, positions=positions[term]))

        for term, entry in self.term_index.items():
            all_postings: list[Posting] = []
            updated_postings: dict[str, list[Posting]] = {}
            for zone, postings in entry["postings"].items():
                postings = sorted(postings, key=lambda p: p.doc_id)
                updated_postings[zone] = postings
                all_postings.extend(postings)
                if len(postings) > 64:
                    entry["skip_stride"] = max(1, int(math.sqrt(len(postings))))
            entry["df"] = len({p.doc_id for p in all_postings})
            entry["postings"] = updated_postings
            entry["all_postings"] = sorted(all_postings, key=lambda p: p.doc_id)

        self.stats["build_time"] = time.perf_counter() - start
        self.stats["index_bytes"] = self._estimate_size()
        self.stats["index_size_bytes"] = self.stats["index_bytes"]
        return self

    def search(
        self,
        query: str,
        *,
        product_id: str | None = None,
        supplier_id: str | None = None,
        source_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        zone: str = "all",
        limit: int | None = None,
    ) -> dict[str, Any]:
        """Lecture concept: boolean query evaluation with metadata filtering and final ordering."""
        if not query or not query.strip():
            raise ValueError("query must not be empty")
        parsed = self.parse_query(query)
        result = self._eval_node(parsed, zone=zone)
        result = self._apply_filters(
            result,
            product_id=product_id,
            supplier_id=supplier_id,
            source_type=source_type,
            start_date=start_date,
            end_date=end_date,
        )
        docs = sorted(result)
        if limit is not None:
            docs = docs[:limit]
        return {
            "docs": docs,
            "comparisons_saved": self.stats.get("comparisons_saved", 0),
            "build_time": self.stats.get("build_time", 0.0),
            "index_size_bytes": self.stats.get("index_size_bytes", 0),
        }

    def parse_query(self, query: str) -> Any:
        """Lecture concept: recursive-descent parsing with boolean precedence and positional operators."""
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        tokens = self._tokenize_query(query)
        if not tokens:
            raise ValueError("Empty query")
        pos = 0

        def peek() -> str | None:
            return tokens[pos] if pos < len(tokens) else None

        def advance() -> str | None:
            nonlocal pos
            if pos >= len(tokens):
                return None
            value = tokens[pos]
            pos += 1
            return value

        def parse_or() -> Any:
            left = parse_and()
            while peek() == "OR":
                advance()
                right = parse_and()
                left = {"kind": "OR", "left": left, "right": right}
            return left

        def parse_and() -> Any:
            left = parse_not()
            while peek() == "AND":
                advance()
                right = parse_not()
                left = {"kind": "AND", "left": left, "right": right}
            return left

        def parse_not() -> Any:
            if peek() == "NOT":
                advance()
                return {"kind": "NOT", "child": parse_not()}
            return parse_primary()

        def parse_primary() -> Any:
            token = peek()
            if token is None:
                raise ValueError("Empty query")
            if token == "(":
                advance()
                node = parse_or()
                if peek() != ")":
                    raise ValueError(f"Unbalanced parentheses in query: {query!r}")
                advance()
                return node
            if token in {"AND", "OR", "NOT", ")"}:
                raise ValueError(f"Unexpected token {token!r} in query: {query!r}")

            if token.startswith("ZONE:"):
                zone, operand = token.split(":", 1)
                advance()
                return {"kind": "TERM", "value": operand, "zone": zone.lower()}

            if token.startswith('"'):
                value = token[1:-1]
                advance()
                return {"kind": "PHRASE", "value": value, "zone": "all"}

            first = advance()
            if first is None:
                raise ValueError("Empty query")
            next_token = peek()
            if next_token is not None and next_token.startswith("/"):
                k_token = advance()
                k_value = int(k_token[1:] or "1")
                right = peek()
                if right is None or right in {"AND", "OR", "NOT", ")", "("}:
                    raise ValueError(f"Missing term after proximity operator in query: {query!r}")
                second = advance()
                return {"kind": "PROXIMITY", "left": first, "right": second, "k": k_value, "zone": "all"}

            values = [first]
            while True:
                nxt = peek()
                if nxt is None or nxt in {"AND", "OR", "NOT", ")", "("}:
                    break
                if nxt.startswith("/"):
                    break
                values.append(advance())
            if len(values) == 1:
                return {"kind": "TERM", "value": values[0], "zone": "all"}
            return {"kind": "PHRASE", "value": " ".join(values), "zone": "all"}

        parsed = parse_or()
        if pos != len(tokens):
            raise ValueError(f"Unable to parse query: {query!r}")
        return parsed

    def _tokenize_query(self, query: str) -> list[str]:
        """Lecture concept: lexical query tokenization for boolean and positional operators."""
        tokens: list[str] = []
        i = 0
        while i < len(query):
            ch = query[i]
            if ch.isspace():
                i += 1
                continue
            if ch in "()":
                tokens.append(ch)
                i += 1
                continue
            if ch == '"':
                end = query.find('"', i + 1)
                if end == -1:
                    raise ValueError(f"Unterminated phrase in query: {query!r}")
                tokens.append('"' + query[i + 1:end] + '"')
                i = end + 1
                continue
            if ch == '/':
                match = re.match(r"/\d+", query[i:])
                if match:
                    tokens.append(match.group(0))
                    i += len(match.group(0))
                    continue
            if ch.isalnum() or ch in {"_", "-", ":"}:
                match = re.match(r"(?:ZONE:[A-Za-z_]+|[A-Za-z0-9_\-]+|[A-Za-z0-9_\-]+:[A-Za-z0-9_\-]+)", query[i:], re.IGNORECASE)
                if match:
                    token = match.group(0)
                    upper = token.upper()
                    if upper in {"AND", "OR", "NOT"}:
                        tokens.append(upper)
                    else:
                        tokens.append(token)
                    i += len(token)
                    continue
            raise ValueError(f"Unsupported query token near: {query[i:i + 20]!r}")
        return tokens

    def _eval_node(self, node: dict[str, Any], *, zone: str = "all") -> set[str]:
        """Lecture concept: recursive boolean evaluation over document sets."""
        kind = node["kind"]
        if kind == "TERM":
            term = self._normalize_term(node["value"])
            return self._term_docs(term, zone=node.get("zone", zone))
        if kind == "PHRASE":
            terms = [self._normalize_term(part) for part in node["value"].split() if part]
            return self.phrase_query(terms, zone=node.get("zone", zone))
        if kind == "PROXIMITY":
            left_term = self._normalize_term(node["left"])
            right_term = self._normalize_term(node["right"])
            return self.proximity_query(left_term, right_term, int(node["k"]), zone=node.get("zone", zone))
        if kind == "NOT":
            child = self._eval_node(node["child"], zone=zone)
            return set(self.docs) - child
        if kind == "AND":
            left = self._eval_node(node["left"], zone=zone)
            right = self._eval_node(node["right"], zone=zone)
            return self._merge_and([left, right])
        if kind == "OR":
            left = self._eval_node(node["left"], zone=zone)
            right = self._eval_node(node["right"], zone=zone)
            return left | right
        raise ValueError(f"Unsupported node kind: {kind!r}")

    def _normalize_term(self, term: str) -> str:
        if not isinstance(term, str):
            return str(term).lower()
        tokens = analyze(term, mode="query", stem="porter")
        if not tokens:
            return term.lower()
        return tokens[0].term

    def _zone_postings(self, term: str, *, zone: str = "all") -> list[Posting]:
        normalized = self._normalize_term(term)
        entry = self.term_index.get(normalized)
        if entry is None:
            return []
        if zone == "all":
            return list(entry.get("all_postings", []))
        return list(entry.get("postings", {}).get(zone, []))

    def _term_docs(self, term: str, *, zone: str = "all") -> set[str]:
        """Lecture concept: term-to-document resolution using postings lists."""
        return {p.doc_id for p in self._zone_postings(term, zone=zone)}

    def _merge_and(self, sets: list[set[str]]) -> set[str]:
        """Lecture concept: merge-based AND using set intersection."""
        if not sets:
            return set()
        current = set(sets[0])
        for other in sets[1:]:
            current &= other
        return current

    def phrase_query(self, terms: list[str], *, zone: str = "all") -> set[str]:
        """Lecture concept: positional phrase matching over term positions."""
        if not terms:
            return set()
        normalized = [self._normalize_term(term) for term in terms]
        candidate_sets = [self._term_docs(term, zone=zone) for term in normalized]
        candidates = set.intersection(*candidate_sets) if len(candidate_sets) > 1 else candidate_sets[0]
        matches: set[str] = set()
        for doc_id in sorted(candidates):
            positions_by_term: dict[str, list[int]] = {}
            for term in normalized:
                positions: list[int] = []
                for posting in self._zone_postings(term, zone=zone):
                    if posting.doc_id == doc_id:
                        positions.extend(posting.positions)
                positions_by_term[term] = sorted(positions)
            if any(not positions_by_term[term] for term in normalized):
                continue
            first_positions = positions_by_term[normalized[0]]
            for pos in first_positions:
                ok = True
                for offset, term in enumerate(normalized[1:], start=1):
                    target_positions = positions_by_term[term]
                    if not any(pos + offset == target for target in target_positions):
                        ok = False
                        break
                if ok:
                    matches.add(doc_id)
                    break
        return matches

    def proximity_query(self, left: str, right: str, k: int, *, zone: str = "all") -> set[str]:
        """Lecture concept: proximity search using positional indexes."""
        left_norm = self._normalize_term(left)
        right_norm = self._normalize_term(right)
        left_postings = self._zone_postings(left_norm, zone=zone)
        right_postings = self._zone_postings(right_norm, zone=zone)
        left_map: dict[str, list[int]] = defaultdict(list)
        right_map: dict[str, list[int]] = defaultdict(list)
        for posting in left_postings:
            left_map[posting.doc_id].extend(posting.positions)
        for posting in right_postings:
            right_map[posting.doc_id].extend(posting.positions)
        matches: set[str] = set()
        for doc_id in sorted(set(left_map) & set(right_map)):
            for lp in left_map[doc_id]:
                for rp in right_map[doc_id]:
                    if abs(lp - rp) <= k:
                        matches.add(doc_id)
                        break
                if doc_id in matches:
                    break
        return matches

    def _apply_filters(
        self,
        doc_ids: set[str],
        *,
        product_id: str | None = None,
        supplier_id: str | None = None,
        source_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> set[str]:
        """Lecture concept: parametric filtering on metadata."""
        filtered = set(doc_ids)
        if product_id is not None:
            filtered = {doc_id for doc_id in filtered if self.docs.get(doc_id, {}).get("product_id") == product_id}
        if supplier_id is not None:
            filtered = {doc_id for doc_id in filtered if self.docs.get(doc_id, {}).get("supplier_id") == supplier_id}
        if source_type is not None:
            filtered = {doc_id for doc_id in filtered if self.docs.get(doc_id, {}).get("source_type") == source_type}
        if start_date is not None or end_date is not None:
            start = start_date or "0000-00-00"
            end = end_date or "9999-12-31"
            filtered = {
                doc_id
                for doc_id in filtered
                if start <= str(self.docs.get(doc_id, {}).get("date", "0000-00-00")) <= end
            }
        return filtered

    def _zone_text(self, doc: dict[str, Any], zone: str) -> str:
        if zone == "all":
            return " ".join(str(doc.get(k) or "") for k in ("title", "body", "supplier_notes"))
        if zone == "supplier_notes":
            return str(doc.get("supplier_notes") or doc.get("body") or "")
        return str(doc.get(zone) or "")

    def _estimate_size(self) -> int:
        return len(pickle.dumps({"terms": self.term_index, "docs": self.docs}, protocol=pickle.HIGHEST_PROTOCOL))

    def save(self, path: str | Path, *, compress: bool = True) -> str:
        """Lecture concept: persistent storage and serialization."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {"docs": self.docs, "term_index": self.term_index, "doc_id_order": self.doc_id_order, "stats": self.stats}
        if compress:
            with gzip.open(str(target), "wb") as handle:
                pickle.dump(payload, handle, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            with open(target, "wb") as handle:
                pickle.dump(payload, handle, protocol=pickle.HIGHEST_PROTOCOL)
        return str(target)

    @classmethod
    def load(cls, path: str | Path) -> "InvertedIndex":
        """Lecture concept: deserialization from disk."""
        target = Path(path)
        opener = gzip.open if target.suffix == ".gz" else open
        with opener(str(target), "rb") as handle:
            payload = pickle.load(handle)
        index = cls()
        index.docs = payload["docs"]
        index.term_index = payload["term_index"]
        index.doc_id_order = payload.get("doc_id_order", sorted(index.docs))
        index.stats = payload.get("stats", {})
        return index

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "InvertedIndex":
        """Lecture concept: corpus ingestion from JSONL documents."""
        rows: list[dict[str, Any]] = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rows.append(json.loads(line))
        index = cls(rows)
        index.stats["index_bytes"] = os.path.getsize(path)
        return index

    @classmethod
    def from_disk(cls, path: str | Path) -> "InvertedIndex":
        return cls.load(path)
