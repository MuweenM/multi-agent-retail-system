"""
Intent and urgency classification for customer return requests.
"""
import re
from typing import Tuple

def classify_intent_and_urgency(text: str) -> Tuple[str, str]:
    """
    Classifies customer intent (refund, exchange, return, complaint, inquiry, unknown)
    and urgency (low, medium, high).
    """
    if not text or not text.strip():
        return 'unknown', 'low'

    lower = text.lower()

    detected_intent = 'return'
    if re.search(r'\b(refund|money\s*back|reimburse|refunding)\b', lower):
        detected_intent = 'refund'
    elif re.search(r'\b(exchange|swap|replace|replacement|different\s*size|different\s*color)\b', lower):
        detected_intent = 'exchange'
    elif re.search(r'\b(unacceptable|file\s+a\s+complaint|complaint|lawyer|scam|fraud|disgusted|terrible\s+service)\b', lower):
        detected_intent = 'complaint'
    elif re.search(r'\b(return|send\s+back|take\s+back|ship\s+back)\b', lower):
        detected_intent = 'return'
    elif re.search(r'\b(how\s+do\s+i|can\s+i|what\s+is\s+the\s+policy|warranty\s+coverage|status\s+of|inquire)\b', lower):
        detected_intent = 'inquiry'

    urgency = 'medium'
    if re.search(r'\b(urgent|immediately|asap|lawsuit|danger|dangerous|fire|smoke|exploded|injury|furious|demand|right\s+now)\b', lower):
        urgency = 'high'
    elif re.search(r'\b(no\s+rush|no\s+hurry|whenever|just\s+wondering|curious)\b', lower):
        urgency = 'low'

    return detected_intent, urgency
