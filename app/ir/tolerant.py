from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from shared.retail_common.taxonomy import ROOT_CAUSES
from shared.retail_common.text.analyzer import analyze


_DOMAIN_SYNONYMS = {
    "swollen": "swelling",
    "bulging": "swelling",
    "swell": "swelling",
    "swelling": "swelling",
    "overheat": "overheating",
    "overheating": "overheating",
    "heating": "overheating",
    "battery": "battery",
    "battrry": "battery",
    "drain": "draining",
    "drains": "draining",
    "draining": "draining",
    "powerbank": "powerbank",
    "power": "power",
    "pack": "battery",
    "warm": "overheating",
    "hot": "overheating",
    "sized": "fit",
    "small": "small",
    "tight": "small",
    "runssmall": "size_fit_issue",
    "bulg": "swelling",
}


def _levenshtein_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i]
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def _kgrams(word: str, k: int = 2) -> set[str]:
    token = f"${word.lower()}$"
    return {token[i : i + k] for i in range(len(token) - k + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _soundex(word: str) -> str:
    if not word:
        return "0000"
    mapped = {
        "B": "1", "F": "1", "P": "1", "V": "1",
        "C": "2", "G": "2", "J": "2", "K": "2", "Q": "2", "S": "2", "X": "2", "Z": "2",
        "D": "3", "T": "3",
        "L": "4",
        "M": "5", "N": "5",
        "R": "6",
    }
    word = word.upper()
    first = word[0]
    digits = []
    last = None
    for ch in word[1:]:
        digit = mapped.get(ch, "")
        if digit and digit != last:
            digits.append(digit)
            last = digit
        elif not digit:
            last = None
    code = first + "".join(digits)
    return (code[:4]).ljust(4, "0")


class TolerantQueryProcessor:
    """Query normalizer that applies spell correction, wildcard expansion, and synthetic synonyms."""

    def __init__(self, documents: Iterable[dict[str, Any]] | None = None):
        self.documents = list(documents) if documents is not None else self._load_default_documents()
        self.dictionary = self._build_dictionary(self.documents)
        self.df = Counter(self.dictionary)
        self.permuterm_index = self._build_permuterm_index(self.dictionary)
        self.soundex_index = defaultdict(set)
        for word in self.dictionary:
            self.soundex_index[_soundex(word)].add(word)

    @staticmethod
    def _load_default_documents() -> list[dict[str, Any]]:
        root = Path(__file__).resolve().parents[2]
        corpus_path = root / "data" / "corpus" / "corpus.jsonl"
        if not corpus_path.exists():
            return []
        rows: list[dict[str, Any]] = []
        for line in corpus_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    @staticmethod
    def _build_dictionary(documents: Iterable[dict[str, Any]]) -> set[str]:
        vocab: set[str] = set()
        for doc in documents:
            text = " ".join(str(doc.get(zone, "") or "") for zone in ("title", "body", "supplier_notes"))
            for term in analyze(text, mode="index", stem="porter"):
                vocab.add(term.term)
        vocab.update({word.lower() for word in _DOMAIN_SYNONYMS})
        vocab.update({value.lower() for value in _DOMAIN_SYNONYMS.values()})
        vocab.update({root.lower() for root in ROOT_CAUSES})
        return vocab

    @staticmethod
    def _build_permuterm_index(vocabulary: Iterable[str]) -> dict[str, set[str]]:
        index: dict[str, set[str]] = defaultdict(set)
        for term in vocabulary:
            if len(term) <= 1:
                continue
            for offset in range(len(term)):
                rotated = term[offset:] + term[:offset]
                index[rotated].add(term)
        return index

    def _expand_wildcard(self, term: str) -> list[str]:
        if not term:
            return []
        wildcard = term.strip()
        if "*" not in wildcard and "?" not in wildcard:
            return [wildcard]

        pattern = re.escape(wildcard).replace(r"\*", ".*").replace(r"\?", ".")
        direct = sorted({candidate for candidate in self.dictionary if re.fullmatch(pattern, candidate)})
        if direct:
            return direct

        stripped = wildcard.replace("*", "").replace("?", "")
        if not stripped:
            return []
        baselines = {candidate for candidate in self.dictionary if stripped in candidate}
        if baselines:
            return sorted(baselines)

        candidates = []
        for candidate in self.dictionary:
            if len(candidate) < 3:
                continue
            if _levenshtein_distance(stripped, candidate) <= 2:
                candidates.append(candidate)
        candidates = sorted(set(candidates))
        if candidates:
            return candidates
        return []

    def _tokenize(self, query: str) -> list[str]:
        tokens: list[str] = []
        for item in re.findall(r"[A-Za-z0-9*?]+|[\w]+", query):
            if item.strip():
                tokens.append(item.strip().lower())
        return tokens

    def _correct_term(self, term: str) -> tuple[str, str | None]:
        clean = term.lower().strip()
        if not clean:
            return term, None

        if clean in _DOMAIN_SYNONYMS:
            return _DOMAIN_SYNONYMS[clean], "domain_synonym"
        if clean in self.dictionary:
            return clean, None

        if "*" in clean or "?" in clean:
            matches = self._expand_wildcard(clean)
            if matches:
                return matches[0], "wildcard"

        if len(clean) <= 2:
            return clean, None

        candidate_scores: list[tuple[int, int, str]] = []
        query_kgrams = _kgrams(clean)
        for word in self.dictionary:
            if len(word) < 2:
                continue
            dist = _levenshtein_distance(clean, word)
            if dist <= 2:
                jaccard = _jaccard(query_kgrams, _kgrams(word))
                if jaccard > 0.0:
                    candidate_scores.append((dist, -self.df.get(word, 0), word))
        if candidate_scores:
            best = min(candidate_scores)
            return best[2], f"jaccard_levenshtein(dist={best[0]})"

        soundex_code = _soundex(clean)
        soundex_matches = sorted(self.soundex_index.get(soundex_code, set()))
        if soundex_matches:
            best_match = min(soundex_matches, key=lambda item: (_levenshtein_distance(clean, item), -self.df.get(item, 0)))
            return best_match, f"soundex(dist={_levenshtein_distance(clean, best_match)})"

        return clean, None

    def process(self, query: str, *, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        normalized = query.strip()
        if not normalized:
            raise ValueError("query must not be empty")
        if len(normalized) > 300:
            raise ValueError("query must be 300 characters or fewer")

        query_terms = self._tokenize(normalized)
        corrected_tokens: list[str] = []
        expanded_terms: list[str] = []
        seen: set[str] = set()
        for term in query_terms:
            corrected, method = self._correct_term(term)
            corrected_tokens.append(corrected)
            if corrected not in seen:
                expanded_terms.append(corrected)
                seen.add(corrected)
            if corrected in _DOMAIN_SYNONYMS:
                synonym = _DOMAIN_SYNONYMS.get(corrected, corrected)
                if synonym and synonym not in seen:
                    expanded_terms.append(synonym)
                    seen.add(synonym)

        hint_terms: list[str] = []
        if filters:
            hints = filters.get("hints") or []
            if isinstance(hints, str):
                hints = [hints]
            for item in hints[:2]:
                if item in ROOT_CAUSES:
                    hint_terms.append(str(item))
            if hint_terms:
                for hint in hint_terms:
                    if hint not in seen:
                        expanded_terms.append(hint)
                        seen.add(hint)

        corrected_query = " ".join(corrected_tokens)
        distinct_expanded = []
        for term in expanded_terms:
            if term and term not in distinct_expanded:
                distinct_expanded.append(str(term))
        return {
            "query": normalized,
            "corrected_query": corrected_query,
            "expanded_terms": distinct_expanded,
            "query_terms": corrected_tokens,
            "hints": hint_terms,
        }


def process_query(query: str, *, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    return TolerantQueryProcessor().process(query, filters=filters)
