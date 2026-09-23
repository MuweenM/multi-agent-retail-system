#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SHARED_ROOT = PROJECT_ROOT / "shared"
if str(SHARED_ROOT) not in sys.path:
    sys.path.insert(0, str(SHARED_ROOT))

from retail_common.text.analyzer import analyze


SAMPLE_WORDS = [
    "return", "returned", "returns", "broken", "battery", "batteries", "charger", "charging",
    "screen", "repair", "damaged", "late", "delay", "deliver", "delivery", "wireless", "warranty",
    "refund", "refunds", "refunded", "not", "no", "never", "without", "quality", "defective",
    "stuck", "slow", "leak", "stop", "stopped", "purchase", "ordered", "shipping", "follow", "failed",
    "faulty", "wrong", "missing", "lost", "damage", "swollen", "heat", "overheating", "explode",
    "crack", "cracked", "smell", "odor", "odorless", "noise", "rattle", "faded", "wear", "tear",
    "size", "small", "large", "fit", "tight", "loose", "color", "fabric", "stitch", "button",
    "zip", "pocket", "material", "scent", "flavor", "taste", "sweet", "sour", "soggy", "dirty",
    "dust", "scratch", "malfunction", "unusable", "legal", "refund", "return", "cancelled", "cancel",
    "arrived", "late", "expensive", "replace", "replacement", "issue", "issue", "issues", "resolved",
    "problem", "problems", "support", "customer", "complaint", "complaints", "frustrated",
    "service", "courier", "delivery", "order", "incorrect", "wrong", "missing", "sent"
]


def _porter_stem(word: str) -> str:
    from nltk.stem import PorterStemmer

    return PorterStemmer().stem(word)


def _lemma_stem(word: str) -> str:
    try:
        import spacy

        try:
            nlp = spacy.load("en_core_web_sm")
        except Exception:
            return word
        doc = nlp(word)
        if doc and len(doc) > 0:
            lemma = doc[0].lemma_.lower()
            if lemma and lemma != "-pronom":
                return lemma
    except Exception:
        pass
    try:
        from nltk.stem import WordNetLemmatizer

        return WordNetLemmatizer().lemmatize(word, pos="v").lower()
    except Exception:
        return word


def main() -> None:
    sample_tokens = []
    for word in SAMPLE_WORDS:
        sample_tokens.append(word)
    while len(sample_tokens) < 200:
        sample_tokens.extend(SAMPLE_WORDS)
    chosen = sample_tokens[:200]

    print(f"{'token':<20} {'porter':<12} {'lemma':<12}")
    print("-" * 52)
    for word in chosen:
        porter = _porter_stem(word)
        lemma = _lemma_stem(word)
        print(f"{word:<20} {porter:<12} {lemma:<12}")

    processed_dir = PROJECT_ROOT / "data" / "processed"
    if processed_dir.exists():
        porter_count = 0
        lemma_count = 0
        for file_path in sorted(processed_dir.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in {".txt", ".md", ".csv"}:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
                porter_count += len({token.term for token in analyze(text, stem="porter")})
                lemma_count += len({token.term for token in analyze(text, stem="lemma")})
        print(f"\nIndex size delta: {porter_count - lemma_count}")
    else:
        print("\nIndex size delta: unavailable (no processed corpus yet)")


if __name__ == "__main__":
    main()
