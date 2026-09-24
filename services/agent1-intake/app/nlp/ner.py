"""Named Entity Recognition module combining spaCy and domain EntityRuler / Regexes (NLP Assignment Component)."""

import os
import re
import sys
from typing import List, Optional

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from retail_common.schemas.intake import Entity

try:
    import spacy
    try:
        nlp = spacy.load("en_core_web_sm")
    except Exception:
        nlp = None
except ImportError:
    nlp = None


# Regex patterns for domain entities
ORDER_ID_REGEX = re.compile(r"\bORD-\d+\b", re.IGNORECASE)
SKU_REGEX = re.compile(r"\b(?:SKU-\d+|P-\d{3})\b", re.IGNORECASE)
SIZE_REGEX = re.compile(
    r"\b(?:size\s+(?:XS|S|M|L|XL|XXL|XXXL|\d+)|XS|S|M|L|XL|XXL|XXXL|EU\s*\d+|UK\s*\d+|US\s*\d+)\b",
    re.IGNORECASE,
)
COLOR_REGEX = re.compile(
    r"\b(?:black|white|blue|red|green|yellow|pink|navy|grey|gray|brown|silver|gold|purple|orange|beige)\b",
    re.IGNORECASE,
)
AMOUNT_REGEX = re.compile(
    r"\b(?:Rs\.?\s*[\d,]+(?:\.\d{2})?|LKR\s*[\d,]+(?:\.\d{2})?|[\d,]+\s*(?:LKR|Rs\.?))\b",
    re.IGNORECASE,
)
DATE_REGEX = re.compile(
    r"\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b"
)


def extract_entities(text: str) -> List[Entity]:
    """Extract domain and standard entities from clean text."""
    if not text:
        return []

    entities: List[Entity] = []
    seen_spans = set()

    # 1. Regex Entity Matching
    regex_map = [
        ("ORDER_ID", ORDER_ID_REGEX),
        ("SKU", SKU_REGEX),
        ("SIZE", SIZE_REGEX),
        ("COLOR", COLOR_REGEX),
        ("AMOUNT", AMOUNT_REGEX),
        ("DATE", DATE_REGEX),
    ]

    for ent_type, pattern in regex_map:
        for match in pattern.finditer(text):
            span = (match.start(), match.end())
            if not any(s <= span[0] and span[1] <= e for s, e in seen_spans):
                seen_spans.add(span)
                entities.append(
                    Entity(
                        type=ent_type,
                        text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                    )
                )

    # 2. spaCy NER (if available) for PERSON, ORG, DATE
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            span = (ent.start_char, ent.end_char)
            if not any(s <= span[0] and span[1] <= e for s, e in seen_spans):
                if ent.label_ in ("ORG", "PRODUCT") and ent.text not in ("[ADDRESS]", "[PHONE]", "[EMAIL]", "[NIC]", "[CARD]"):
                    seen_spans.add(span)
                    entities.append(
                        Entity(
                            type="PRODUCT" if ent.label_ == "PRODUCT" else "BRAND",
                            text=ent.text,
                            start=ent.start_char,
                            end=ent.end_char,
                        )
                    )
                elif ent.label_ == "DATE" and not any(e.type == "DATE" for e in entities):
                    seen_spans.add(span)
                    entities.append(
                        Entity(
                            type="DATE",
                            text=ent.text,
                            start=ent.start_char,
                            end=ent.end_char,
                        )
                    )

    return sorted(entities, key=lambda x: (x.start if x.start is not None else 0))
