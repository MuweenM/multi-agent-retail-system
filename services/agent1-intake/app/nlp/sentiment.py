"""
Sentiment analysis module for retail customer return texts.
Calculates sentiment score and assigns positive, neutral, or negative labels.
"""
import re
from typing import Tuple

POSITIVE_WORDS = {
    'good', 'great', 'excellent', 'amazing', 'wonderful', 'love', 'liked',
    'perfect', 'satisfied', 'helpful', 'fast', 'quick', 'appreciate', 'thank',
    'thanks', 'pleased', 'superb', 'awesome', 'decent', 'fine'
}

NEGATIVE_WORDS = {
    'terrible', 'horrible', 'awful', 'broken', 'damaged', 'defective', 'worst',
    'poor', 'hate', 'hated', 'disappointed', 'disappointing', 'useless', 'junk',
    'trash', 'failed', 'failure', 'stopped', 'never', 'unacceptable', 'ridiculous',
    'waste', 'angry', 'upset', 'faulty', 'scam', 'scammed', 'furious', 'wrong',
    'missing', 'unusable', 'dead', 'shattered', 'glitch', 'error', 'defect', 'flawed'
}

INTENSIFIERS = {
    'very', 'extremely', 'really', 'completely', 'totally', 'absolutely', 'highly', 'so'
}

NEGATIONS = {
    'not', 'no', 'never', 'without', 'hardly', 'barely', 'nt'
}



def analyze_sentiment(text: str) -> Tuple[str, float]:
    """
    Analyzes sentiment of customer text.
    Returns (label, score) where score is between -1.0 and 1.0.
    """
    if not text or not text.strip():
        return 'neutral', 0.0

    cleaned = text.lower().replace("n't", " nt")
    tokens = re.findall(r"\b[a-z]+\b", cleaned)
    if not tokens:
        return 'neutral', 0.0

    pos_score = 0.0
    neg_score = 0.0
    negation_active = False
    intensifier_mult = 1.0

    for token in tokens:
        if token in NEGATIONS:
            negation_active = True
            continue

        if token in INTENSIFIERS:
            intensifier_mult = 1.5
            continue

        weight = 1.0 * intensifier_mult

        if token in POSITIVE_WORDS:
            if negation_active:
                neg_score += weight * 0.8
            else:
                pos_score += weight
            negation_active = False
            intensifier_mult = 1.0
        elif token in NEGATIVE_WORDS:
            if negation_active:
                pos_score += weight * 0.5
            else:
                neg_score += weight
            negation_active = False
            intensifier_mult = 1.0

    total_matches = pos_score + neg_score
    if total_matches == 0:
        return 'neutral', 0.0

    polarity = (pos_score - neg_score) / (total_matches + 1.0)
    polarity = max(-1.0, min(1.0, polarity))

    if polarity <= -0.15:
        label = 'negative'
    elif polarity >= 0.15:
        label = 'positive'
    else:
        label = 'neutral'

    return label, round(polarity, 3)
