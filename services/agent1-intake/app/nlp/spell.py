"""Spell correction module implementing Lecture 3 Information Retrieval concepts from scratch."""

import csv
import os
import re
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute minimum edit distance between s1 and s2 using Dynamic Programming (Lecture 3)."""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # Deletion
                dp[i][j - 1] + 1,      # Insertion
                dp[i - 1][j - 1] + cost  # Substitution
            )
    return dp[m][n]


def get_kgrams(word: str, k: int = 2) -> Set[str]:
    """Extract character k-grams with boundary markers (Lecture 3)."""
    padded = f"${word.lower()}$"
    return {padded[i : i + k] for i in range(len(padded) - k + 1)}


def jaccard_coefficient(set1: Set[str], set2: Set[str]) -> float:
    """Compute Jaccard similarity coefficient |A ∩ B| / |A ∪ B| (Lecture 3)."""
    union_len = len(set1 | set2)
    if union_len == 0:
        return 0.0
    return len(set1 & set2) / union_len


def soundex(word: str) -> str:
    """Compute Soundex phonetic hash code (Lecture 3: Phonetic Correction)."""
    if not word:
        return "0000"
    word = word.upper()
    first_char = word[0]
    mapping = {
        "B": "1", "F": "1", "P": "1", "V": "1",
        "C": "2", "G": "2", "J": "2", "K": "2", "Q": "2", "S": "2", "X": "2", "Z": "2",
        "D": "3", "T": "3",
        "L": "4",
        "M": "5", "N": "5",
        "R": "6",
    }
    encoded = [first_char]
    prev_digit = mapping.get(first_char, "")

    for char in word[1:]:
        digit = mapping.get(char, "")
        if digit:
            if digit != prev_digit:
                encoded.append(digit)
                prev_digit = digit
        else:
            prev_digit = ""

    soundex_code = "".join(encoded)
    soundex_code = soundex_code.ljust(4, "0")[:4]
    return soundex_code


# Base English + Domain vocabulary
COMMON_ENGLISH_WORDS = {
    "a", "about", "above", "after", "again", "all", "am", "an", "and", "any", "are", "as",
    "at", "back", "be", "because", "been", "before", "being", "below", "between", "both",
    "bought", "but", "by", "call", "came", "can", "cannot", "come", "could", "did", "do",
    "does", "doing", "down", "during", "each", "fast", "few", "for", "from", "further",
    "get", "got", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself",
    "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off",
    "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own",
    "please", "same", "send", "sent", "she", "should", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "whom", "why", "with", "would", "you",
    "your", "yours", "yourself", "yourselves", "within", "hours", "days", "weeks", "months",
    "dies", "die", "dead", "works", "working", "stops", "stopped", "gives", "gave", "need",
    "want", "wanted", "received", "delivered", "ordered", "order", "item", "product", "goods",
}

COMMON_DOMAIN_WORDS = {
    "battery", "charging", "charger", "drains", "drain", "broken", "damaged",
    "defective", "swelling", "swollen", "cracked", "screen", "cable", "shirt",
    "dress", "shoes", "earbuds", "headphones", "phone", "smartphone", "powerbank",
    "power", "bank", "refund", "return", "exchange", "warranty", "delivery",
    "transit", "courier", "package", "arrived", "late", "small", "large", "tight",
    "loose", "color", "wrong", "size", "quality", "cotton", "wireless", "bluetooth",
    "sound", "speaker", "tea", "oil", "honey", "cashew", "cinnamon", "bottle",
    "mug", "scale", "knife", "towel", "pillow", "lamp", "heating", "leak",
    "leaking", "stitching", "torn", "blinking", "flickering", "seal", "coating",
}

BIGRAM_CONTEXT_FREQS = {
    ("bought", "from"): 50,
    ("bought", "form"): 1,
    ("sent", "from"): 40,
    ("sent", "form"): 1,
    ("return", "from"): 30,
    ("return", "form"): 5,
    ("power", "bank"): 80,
    ("power", "blank"): 1,
    ("battery", "drains"): 70,
    ("battery", "trains"): 1,
    ("screen", "cracked"): 60,
    ("not", "working"): 90,
    ("not", "walking"): 1,
}


class SpellCorrector:
    """Lecture 3 compliant Spell Corrector from scratch."""

    def __init__(self, catalog_csv_path: Optional[str] = None):
        self.vocab: Set[str] = set(COMMON_ENGLISH_WORDS) | set(COMMON_DOMAIN_WORDS)
        self.kgram_index: Dict[str, Set[str]] = defaultdict(set)
        self.soundex_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Load catalog words
        if not catalog_csv_path:
            catalog_csv_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../../data/catalog/products.csv")
            )
        
        if os.path.exists(catalog_csv_path):
            with open(catalog_csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    for field in ["name", "brand", "category"]:
                        val = row.get(field, "")
                        for word in re.findall(r"[A-Za-z]+", val):
                            self.vocab.add(word.lower())

        # Index vocabulary
        for word in self.vocab:
            for kg in get_kgrams(word, k=2):
                self.kgram_index[kg].add(word)
            s_code = soundex(word)
            self.soundex_index[s_code].add(word)

    def shortlist_candidates(self, query_word: str, jaccard_threshold: float = 0.25) -> List[Tuple[str, float]]:
        """Shortlist vocabulary candidates using k-gram overlap and Jaccard threshold (Lecture 3)."""
        q_kgrams = get_kgrams(query_word, k=2)
        candidate_words = set()
        for kg in q_kgrams:
            candidate_words.update(self.kgram_index.get(kg, set()))

        scored = []
        for cand in candidate_words:
            cand_kgrams = get_kgrams(cand, k=2)
            j_score = jaccard_coefficient(q_kgrams, cand_kgrams)
            if j_score >= jaccard_threshold:
                scored.append((cand, j_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def correct_word(
        self,
        word: str,
        prev_word: Optional[str] = None,
        next_word: Optional[str] = None,
    ) -> Tuple[str, Optional[str]]:
        """Correct an isolated or context word. Returns (corrected_word, method_used)."""
        clean_word = word.lower().strip()

        if not clean_word or any(ch.isdigit() for ch in clean_word) or len(clean_word) <= 2:
            return word, None

        # Context-sensitive Bigram check
        if prev_word:
            pair = (prev_word.lower(), clean_word)
            for (w1, w2), freq in BIGRAM_CONTEXT_FREQS.items():
                if w1 == prev_word.lower() and levenshtein_distance(clean_word, w2) == 1 and freq > 20:
                    if pair not in BIGRAM_CONTEXT_FREQS or BIGRAM_CONTEXT_FREQS[pair] < 5:
                        return w2 if word.islower() else w2.capitalize(), "bigram_context"

        # If already in vocabulary, keep unchanged
        if clean_word in self.vocab:
            return word, None

        # Shortlist via 2-gram Jaccard Index & compute Levenshtein Edit Distance
        candidates = self.shortlist_candidates(clean_word, jaccard_threshold=0.20)
        best_cand = None
        min_dist = 999

        for cand, j_score in candidates[:15]:
            dist = levenshtein_distance(clean_word, cand)
            if dist < min_dist and dist <= 2:
                min_dist = dist
                best_cand = cand

        if best_cand and min_dist <= 2:
            corrected = best_cand if word.islower() else best_cand.capitalize()
            return corrected, f"jaccard_levenshtein(dist={min_dist})"

        # Soundex Phonetic Fallback
        s_code = soundex(clean_word)
        soundex_matches = self.soundex_index.get(s_code, set())
        if soundex_matches:
            best_soundex = min(soundex_matches, key=lambda c: levenshtein_distance(clean_word, c))
            dist = levenshtein_distance(clean_word, best_soundex)
            if dist <= 2:
                corrected = best_soundex if word.islower() else best_soundex.capitalize()
                return corrected, f"soundex(dist={dist})"

        return word, None

    def correct_text(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """Spell correct text token by token without altering numbers or placeholders."""
        if not text:
            return "", []

        tokens = re.findall(r"\[[A-Z_]+\]|[A-Za-z0-9\-]+|[^\s\w]", text)
        corrected_tokens = []
        changes = []

        for i, token in enumerate(tokens):
            if token.startswith("[") and token.endswith("]"):
                corrected_tokens.append(token)
                continue

            if not token.isalpha():
                corrected_tokens.append(token)
                continue

            prev_word = tokens[i - 1] if i > 0 and tokens[i - 1].isalpha() else None
            next_word = tokens[i + 1] if i < len(tokens) - 1 and tokens[i + 1].isalpha() else None

            corr_word, method = self.correct_word(token, prev_word, next_word)
            if method:
                changes.append({"original": token, "corrected": corr_word, "method": method})
            corrected_tokens.append(corr_word)

        rebuilt = " ".join(corrected_tokens)
        rebuilt = re.sub(r"\s+([,.\?!;:])", r"\1", rebuilt)
        return rebuilt, changes
