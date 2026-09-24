from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ir_system.ir.inverted_index import InvertedIndex


def _make_corpus() -> list[dict[str, str]]:
    return [
        {"id": "d1", "source_type": "review", "product_id": "P-014", "supplier_id": "S-03", "date": "2026-09-05", "title": "Battery swelling risk", "body": "Battery swelling on the phone caused a dangerous overheating issue.", "supplier_notes": "Battery swelling and overheating were reported in QA."},
        {"id": "d2", "source_type": "review", "product_id": "P-014", "supplier_id": "S-03", "date": "2026-09-07", "title": "Great battery life", "body": "Battery life is great and the phone is very reliable.", "supplier_notes": "Battery life feedback was positive in supplier notes."},
        {"id": "d3", "source_type": "review", "product_id": "P-027", "supplier_id": "S-04", "date": "2026-09-08", "title": "Runs small", "body": "The shirt runs small and the fit is poor.", "supplier_notes": "Sizing review mentions runs small."},
        {"id": "d4", "source_type": "supplier_record", "product_id": "P-009", "supplier_id": "S-02", "date": "2026-09-09", "title": "Battery life note", "body": "Battery life is great for this model.", "supplier_notes": "Supplier note: battery life is excellent and there is no defect."},
        {"id": "d5", "source_type": "inventory", "product_id": "P-014", "supplier_id": "S-03", "date": "2026-09-10", "title": "Stock alert", "body": "Inventory check found a battery swelling issue in a batch.", "supplier_notes": "Battery swelling alert flagged by warehouse."},
        {"id": "d6", "source_type": "policy", "product_id": "P-014", "supplier_id": "S-03", "date": "2026-09-11", "title": "Defect return policy", "body": "Items with battery swelling or heat defects are eligible for refund.", "supplier_notes": "Policy covers swelling and overheat defects."},
    ]


def _term_set(doc: dict[str, str]) -> set[str]:
    text = " ".join(str(doc.get(zone, "")) for zone in ("title", "body", "supplier_notes"))
    return set(InvertedIndex()._normalize_term(token) for token in text.lower().split() if token)


def _brute_force(query: str, corpus: list[dict[str, str]]) -> set[str]:
    index = InvertedIndex(corpus)
    parsed = index.parse_query(query)

    def eval_node(node: dict, doc: dict[str, str]) -> bool:
        kind = node["kind"]
        if kind == "TERM":
            term = index._normalize_term(node["value"])
            return term in _term_set(doc)
        if kind == "PHRASE":
            terms = [index._normalize_term(part) for part in node["value"].split() if part]
            text = " ".join(str(doc.get(zone, "")) for zone in ("title", "body", "supplier_notes")).lower()
            tokens = [index._normalize_term(part) for part in text.split()]
            phrase_tokens = terms
            for idx in range(len(tokens) - len(phrase_tokens) + 1):
                if tokens[idx:idx + len(phrase_tokens)] == phrase_tokens:
                    return True
            return False
        if kind == "PROXIMITY":
            left = index._normalize_term(node["left"])
            right = index._normalize_term(node["right"])
            k = node["k"]
            text = " ".join(str(doc.get(zone, "")) for zone in ("title", "body", "supplier_notes")).lower().split()
            normalized = [index._normalize_term(part) for part in text]
            left_positions = [idx for idx, token in enumerate(normalized) if token == left]
            right_positions = [idx for idx, token in enumerate(normalized) if token == right]
            return any(abs(l - r) <= k for l in left_positions for r in right_positions)
        if kind == "NOT":
            return not eval_node(node["child"], doc)
        if kind == "AND":
            return eval_node(node["left"], doc) and eval_node(node["right"], doc)
        if kind == "OR":
            return eval_node(node["left"], doc) or eval_node(node["right"], doc)
        raise ValueError(f"Unsupported node kind: {kind}")

    matches = set()
    for doc in corpus:
        if eval_node(parsed, doc):
            matches.add(doc["id"])
    return matches


def test_boolean_queries_match_bruteforce_scan():
    corpus = _make_corpus()
    index = InvertedIndex(corpus)
    terms = ["battery", "swelling", "life", "small", "fit", "defect", "heat", "return", "quality"]
    rng = random.Random(20260925)
    for _ in range(200):
        left = rng.choice(terms)
        right = rng.choice(terms)
        op = rng.choice(["AND", "OR", "AND", "OR", "NOT"])
        suffix = f" {op} {right}" if op != "NOT" else f"{op} {right}"
        query = f"{left} {suffix}" if op != "NOT" else f"{op} {left}"
        if rng.random() < 0.35:
            query = f"({left} OR {right}) AND {rng.choice(terms)}"
        actual = set(index.search(query)["docs"])
        expected = _brute_force(query, corpus)
        assert actual == expected, f"Mismatch for {query!r}: actual={actual}, expected={expected}"


def test_phrase_and_proximity_queries():
    corpus = _make_corpus()
    index = InvertedIndex(corpus)
    assert index.phrase_query(["battery", "swelling"], zone="body") == {"d1", "d5", "d6"}
    assert index.proximity_query("battery", "swelling", 5, zone="body") == {"d1", "d5", "d6"}


def test_filters_and_disk_round_trip(tmp_path):
    corpus = _make_corpus()
    index = InvertedIndex(corpus)
    result = index.search("battery AND swelling", product_id="P-014", source_type="review", limit=10)
    assert result["docs"] == ["d1"]
    path = tmp_path / "index.pkl.gz"
    index.save(path)
    loaded = InvertedIndex.load(path)
    assert loaded.search("battery AND swelling", product_id="P-014")["docs"] == ["d1", "d5", "d6"]
