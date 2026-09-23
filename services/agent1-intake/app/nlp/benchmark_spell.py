"""Benchmark script for spell correction ablation study (Prompt 1.3 requirement).

Generates 100 misspelled product mentions via character mutations (insertions, deletions, substitutions)
and measures top-1 retrieval accuracy across:
1. Levenshtein Edit Distance only (Lecture 3: Dynamic Programming)
2. 2-gram Jaccard Index only (Lecture 3: k-gram inverted index)
3. Soundex phonetic hashing only (Lecture 3: Phonetic correction)
4. Combined Hybrid Approach (Combined scoring and shortlisting)
"""

import os
import random
import sys

# Support local and root path imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from app.nlp.spell import (
    SpellCorrector,
    levenshtein_distance,
    soundex,
    get_kgrams,
    jaccard_coefficient,
)


def mutate_word(word: str, num_mutations: int = 1) -> str:
    """Introduce synthetic character errors (delete, insert, substitute)."""
    chars = list(word.lower())
    if len(chars) <= 3:
        return word
    for _ in range(num_mutations):
        op = random.choice(["del", "ins", "sub"])
        pos = random.randint(0, len(chars) - 1)
        if op == "del" and len(chars) > 3:
            chars.pop(pos)
        elif op == "ins":
            chars.insert(pos, random.choice("abcdefghijklmnopqrstuvwxyz"))
        elif op == "sub":
            chars[pos] = random.choice("abcdefghijklmnopqrstuvwxyz")
    return "".join(chars)


def run_benchmark():
    random.seed(42)
    corrector = SpellCorrector()
    target_words = list(corrector.vocab)[:50]

    # Generate 100 misspelled word test pairs (original, misspelled)
    test_cases = []
    for _ in range(100):
        orig = random.choice(target_words)
        mis = mutate_word(orig, num_mutations=1)
        while mis == orig:
            mis = mutate_word(orig, num_mutations=1)
        test_cases.append((orig, mis))

    # Evaluate each method
    correct_edit_only = 0
    correct_jaccard_only = 0
    correct_soundex_only = 0
    correct_combined = 0

    all_vocab = list(corrector.vocab)

    for orig, mis in test_cases:
        # 1. Edit Distance only (brute force minimum edit distance)
        best_edit = min(all_vocab, key=lambda w: levenshtein_distance(mis, w))
        if best_edit == orig:
            correct_edit_only += 1

        # 2. 2-gram Jaccard only
        mis_kg = get_kgrams(mis, k=2)
        best_jaccard = max(all_vocab, key=lambda w: jaccard_coefficient(mis_kg, get_kgrams(w, k=2)))
        if best_jaccard == orig:
            correct_jaccard_only += 1

        # 3. Soundex only
        s_code = soundex(mis)
        candidates = corrector.soundex_index.get(s_code, set())
        if orig in candidates:
            correct_soundex_only += 1

        # 4. Combined Approach
        corr_word, _ = corrector.correct_word(mis)
        if corr_word.lower() == orig.lower():
            correct_combined += 1

    print("\n=======================================================")
    print("      SPELL CORRECTION ABLATION BENCHMARK (N=100)      ")
    print("=======================================================")
    print(f"{'Method / Configuration':<35} | {'Top-1 Accuracy':<15}")
    print("-------------------------------------------------------")
    print(f"{'Levenshtein Edit Distance only':<35} | {correct_edit_only / 100 * 100:.1f}%")
    print(f"{'2-gram Jaccard Index only':<35} | {correct_jaccard_only / 100 * 100:.1f}%")
    print(f"{'Soundex Phonetic Match only':<35} | {correct_soundex_only / 100 * 100:.1f}%")
    print(f"{'Combined Hybrid (Jaccard + DP + Soundex)':<35} | {correct_combined / 100 * 100:.1f}%")
    print("=======================================================\n")

    return {
        "edit_only": correct_edit_only,
        "jaccard_only": correct_jaccard_only,
        "soundex_only": correct_soundex_only,
        "combined": correct_combined,
    }


if __name__ == "__main__":
    run_benchmark()
