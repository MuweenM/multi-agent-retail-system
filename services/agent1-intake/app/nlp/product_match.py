"""Product matching algorithm implementing IR character 3-grams, edit similarity and token overlap."""

import csv
import os
import sys
import re
from typing import List, Tuple, Set, Optional

# Support local and parent imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.nlp.spell import levenshtein_distance, jaccard_coefficient

# Configurable weights for scoring formula
WEIGHT_3GRAM_JACCARD = 0.50
WEIGHT_EDIT_SIMILARITY = 0.30
WEIGHT_TOKEN_OVERLAP = 0.20


def get_char_3grams(text: str) -> Set[str]:
    """Extract character 3-grams from text for n-gram indexing."""
    clean = re.sub(r"[^\w\s]", "", text.lower()).strip()
    if len(clean) < 3:
        return {clean} if clean else set()
    return {clean[i : i + 3] for i in range(len(clean) - 2)}


def normalized_edit_similarity(s1: str, s2: str) -> float:
    """Compute normalized edit similarity: 1 - (edit_dist / max_len)."""
    clean1 = s1.lower().strip()
    clean2 = s2.lower().strip()
    max_l = max(len(clean1), len(clean2))
    if max_l == 0:
        return 1.0
    dist = levenshtein_distance(clean1, clean2)
    return max(0.0, 1.0 - (dist / max_l))


def token_overlap_score(phrase_toks: Set[str], target_toks: Set[str]) -> float:
    """Compute token overlap coefficient."""
    if not phrase_toks or not target_toks:
        return 0.0
    return len(phrase_toks & target_toks) / len(target_toks)


class ProductMatcher:
    """Matches freeform customer text phrases to catalog product IDs."""

    def __init__(self, catalog_csv_path: Optional[str] = None):
        if not catalog_csv_path:
            catalog_csv_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../../data/catalog/products.csv")
            )
        self.products: List[dict] = []
        if os.path.exists(catalog_csv_path):
            with open(catalog_csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name_toks = set(re.findall(r"\w+", row["name"].lower()))
                    search_toks = set(re.findall(r"\w+", f"{row['name']} {row.get('brand', '')} {row.get('category', '')}".lower()))
                    self.products.append({
                        "product_id": row["product_id"],
                        "name": row["name"],
                        "brand": row.get("brand", ""),
                        "category": row.get("category", ""),
                        "name_tokens": name_toks,
                        "search_tokens": search_toks,
                        "3grams": get_char_3grams(f"{row['name']} {row.get('brand', '')}"),
                    })

    def match(self, phrase: str, top_k: int = 5) -> List[Tuple[str, str, float]]:
        """Rank catalog products for a given complaint phrase.
        
        Formula (Lecture IR & Course Blueprint):
        score = 0.5 * Jaccard_3gram + 0.3 * Normalized_Edit_Sim + 0.2 * Token_Overlap
        """
        if not phrase or not self.products:
            return []

        phrase_clean = phrase.lower().strip()
        phrase_3grams = get_char_3grams(phrase_clean)
        phrase_tokens = set(re.findall(r"\w+", phrase_clean))
        ranked = []

        for prod in self.products:
            # 1. Jaccard on character 3-grams
            jaccard_score = jaccard_coefficient(phrase_3grams, prod["3grams"])

            # 2. Normalized edit similarity
            edit_sim = normalized_edit_similarity(phrase_clean, prod["name"])

            # 3. Token overlap with product search tokens
            token_score = token_overlap_score(phrase_tokens, prod["name_tokens"])

            # If key product tokens present in phrase (e.g. "galaxy", "a15")
            if prod["name_tokens"].issubset(phrase_tokens) or (len(prod["name_tokens"] & phrase_tokens) >= 2):
                token_score = max(token_score, 0.90)
                edit_sim = max(edit_sim, 0.85)

            # Combined weighted score
            final_score = (
                (WEIGHT_3GRAM_JACCARD * jaccard_score)
                + (WEIGHT_EDIT_SIMILARITY * edit_sim)
                + (WEIGHT_TOKEN_OVERLAP * token_score)
            )

            # Exact product ID citation (e.g. P-014, P-001)
            if prod["product_id"].lower() in phrase_tokens:
                final_score = 1.0

            ranked.append((prod["product_id"], prod["name"], round(final_score, 4)))

        ranked.sort(key=lambda x: x[2], reverse=True)
        return ranked[:top_k]
