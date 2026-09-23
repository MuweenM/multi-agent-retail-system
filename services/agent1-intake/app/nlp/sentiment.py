"""Sentiment analysis module for customer complaints."""

import re

POSITIVE_WORDS = {
    "great", "good", "excellent", "fast", "helpful", "polite", "quick", "thanks", "thank",
    "love", "perfect", "satisfied", "happy", "awesome", "best", "wonderful", "prompt",
}

NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "broken", "damaged", "poor", "worst", "waste", "useless",
    "defect", "defective", "horrible", "angry", "disappointed", "hate", "slow", "fail",
    "failed", "drain", "drains", "scam", "cheat", "fake", "stolen", "unacceptable", "late",
    "never", "not", "ruined", "tight", "loose", "dirty", "scratch", "scratched",
}


def analyze_sentiment(text: str) -> str:
    """Classify sentiment as positive, neutral, or negative."""
    if not text:
        return "neutral"

    words = re.findall(r"[A-Za-z]+", text.lower())
    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)

    if neg_count > pos_count:
        return "negative"
    elif pos_count > neg_count and neg_count == 0:
        return "positive"
    return "neutral"
