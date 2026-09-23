"""Feature preparation using issue text and product name only."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from sklearn.model_selection import train_test_split


SERVICE_ROOT = Path(__file__).parents[2]
PROJECT_ROOT = SERVICE_ROOT.parents[1]
RETURNS_PATH = PROJECT_ROOT / "data" / "returns" / "returns.csv"
PRODUCTS_PATH = PROJECT_ROOT / "data" / "catalog" / "products.csv"

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "i", "in", "is", "it", "my", "of", "on", "or", "the", "this", "to", "was",
    "with",
}


def analyze_text(text: str) -> str:
    """Temporary Lecture 6 tokenization and stopword removal until shared analyzer exists."""
    try:
        from retail_common.text.analyzer import analyze_text as shared_analyzer
    except ImportError:
        shared_analyzer = None
    if shared_analyzer is not None:
        return shared_analyzer(text)
    tokens = re.findall(r"[a-z0-9]+", str(text).lower())
    return " ".join(token for token in tokens if token not in STOPWORDS)


def load_records(returns_path: Path = RETURNS_PATH, products_path: Path = PRODUCTS_PATH) -> list[dict[str, str]]:
    with products_path.open(newline="", encoding="utf-8") as file:
        products = {row["product_id"]: row["name"] for row in csv.DictReader(file)}
    with returns_path.open(newline="", encoding="utf-8") as file:
        records = list(csv.DictReader(file))
    for record in records:
        record["model_text"] = analyze_text(
            f"{products.get(record['product_id'], record['product_id'])} {record['text']}"
        )
    return records


def make_dataset(records: list[dict[str, str]]):
    """Build X/y from only product name plus issue text; no metadata is model input."""
    return [record["model_text"] for record in records], [record["root_cause_label"] for record in records]


def split_dataset(texts, labels, test_size: float = 0.2, random_state: int = 3041):
    return train_test_split(texts, labels, test_size=test_size, random_state=random_state, stratify=labels)