from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Token:
    term: str
    position: int
    start: int
    end: int


_NEGATIONS = {"not", "no", "never", "without"}
_WORD_CHARS = r"[\w\u0D80-\u0DFF\u0300-\u036F]"
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_ORDER_RE = re.compile(r"(?i)ord-?\d+")
_HYPHEN_RE = re.compile(rf"{_WORD_CHARS}+(?:-{_WORD_CHARS}+)+", re.UNICODE)
_WORD_RE = re.compile(rf"{_WORD_CHARS}+", re.UNICODE)


def _stopwords() -> set[str]:
    stopwords_path = Path(__file__).resolve().parents[3] / "data" / "stopwords.txt"
    if not stopwords_path.exists():
        return set()
    return {line.strip().lower() for line in stopwords_path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _stem_word(term: str, stem: str) -> str:
    if stem == "none":
        return term
    if stem == "porter":
        try:
            from nltk.stem import PorterStemmer

            return PorterStemmer().stem(term)
        except Exception:
            return term
    if stem == "lemma":
        try:
            import spacy

            if not hasattr(_stem_word, "_nlp"):
                try:
                    _stem_word._nlp = spacy.load("en_core_web_sm")
                except Exception:
                    _stem_word._nlp = None
            if _stem_word._nlp is not None:
                lemma = _stem_word._nlp(term)[0].lemma_.lower()
                if lemma and lemma != "-pronom":
                    return lemma
        except Exception:
            pass
        try:
            from nltk.stem import WordNetLemmatizer

            lemma = WordNetLemmatizer().lemmatize(term, pos="v")
            if lemma:
                return lemma.lower()
        except Exception:
            pass
    raise ValueError(f"Unsupported stem mode: {stem!r}")


def _hyphen_entries(value: str, start: int) -> list[tuple[str, int, int]]:
    parts = value.split("-")
    entries: list[tuple[str, int, int]] = [(value, start, start + len(value))]
    cursor = start
    for index, part in enumerate(parts):
        if not part:
            continue
        if index == 0:
            part_start = cursor
            part_end = cursor + len(part)
        else:
            part_start = cursor + 1
            part_end = part_start + len(part)
        entries.append((part, part_start, part_end))
        cursor = part_end
    return entries


def analyze(text: str, mode: str = "index", stem: str = "porter") -> list[Token]:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if mode not in {"index", "query"}:
        raise ValueError("mode must be either 'index' or 'query'")
    if stem not in {"porter", "lemma", "none"}:
        raise ValueError("stem must be one of 'porter', 'lemma', or 'none'")

    normalized = unicodedata.normalize("NFKC", text).lower()
    if not normalized:
        return []

    stopwords = _stopwords()
    candidates: list[tuple[str, int, int]] = []
    i = 0
    while i < len(normalized):
        if normalized[i].isspace():
            i += 1
            continue

        email_match = _EMAIL_RE.match(normalized, i)
        if email_match:
            value = email_match.group(0)
            candidates.append((value, email_match.start(), email_match.end()))
            i = email_match.end()
            continue

        order_match = _ORDER_RE.match(normalized, i)
        if order_match:
            value = order_match.group(0)
            candidates.append((value, order_match.start(), order_match.end()))
            i = order_match.end()
            continue

        hyphen_match = _HYPHEN_RE.match(normalized, i)
        if hyphen_match:
            value = hyphen_match.group(0)
            start = hyphen_match.start()
            end = hyphen_match.end()
            for term, term_start, term_end in _hyphen_entries(value, start):
                candidates.append((term, term_start, term_end))
            i = end
            continue

        word_match = _WORD_RE.match(normalized, i)
        if word_match:
            value = word_match.group(0)
            candidates.append((value, word_match.start(), word_match.end()))
            i = word_match.end()
            continue

        i += 1

    tokens: list[Token] = []
    for position, (term, start, end) in enumerate(candidates):
        if "-" in term and _HYPHEN_RE.fullmatch(term):
            final_terms = [term]
            for piece in term.split("-"):
                if piece:
                    final_terms.append(piece)
        else:
            final_terms = [term]

        for final_term in final_terms:
            normalized_term = final_term.strip()
            if not normalized_term:
                continue
            lower_term = normalized_term.lower()
            if lower_term in stopwords and lower_term not in _NEGATIONS:
                continue
            stemmed = _stem_word(lower_term, stem)
            if stemmed in stopwords and stemmed not in _NEGATIONS:
                continue
            if not stemmed:
                continue
            tokens.append(Token(term=stemmed, position=len(tokens), start=start if final_term == term else start, end=end if final_term == term else end))

    return tokens
