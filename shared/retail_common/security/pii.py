"""PII Redaction module for Sri Lankan Retail Returns (Lecture & Assignment Compliance)."""

from dataclasses import dataclass, field
import re
from typing import List, Tuple

try:
    import spacy
    try:
        nlp_spacy = spacy.load("en_core_web_sm")
    except Exception:
        nlp_spacy = None
except ImportError:
    nlp_spacy = None


@dataclass
class RedactResult:
    text: str
    types_found: List[str] = field(default_factory=list)
    spans: List[Tuple[int, int, str]] = field(default_factory=list)


def luhn_check(card_number_str: str) -> bool:
    """Validate payment card number using the Luhn algorithm."""
    digits = [int(d) for d in card_number_str if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += (doubled - 9) if doubled > 9 else doubled
        else:
            checksum += digit
    return checksum % 10 == 0


# Pre-compiled Regexes
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", re.IGNORECASE
)

# Sri Lankan NIC: Old (9 digits + V/X) and New (12 digits starting 19xx or 20xx)
OLD_NIC_REGEX = re.compile(r"\b[0-9]{9}[vVxX]\b")
NEW_NIC_REGEX = re.compile(r"\b(?:19|20)[0-9]{10}\b")

# Sri Lankan Phone numbers:
# +94 7X XXXXXXX, 07X XXXXXXX, +94 11 XXXXXXX, 011 XXXXXXX, etc.
PHONE_REGEX = re.compile(
    r"(?:\+94\s?|0094\s?|0)(?:7[01245678]|11|21|23|24|25|26|27|31|32|33|34|35|36|37|38|41|45|47|51|52|54|55|57|63|65|66|67|81|91)[\s\-]?[0-9]{3}[\s\-]?[0-9]{4}\b"
)

# Generic payment card candidates (13-19 digits with optional spaces or dashes)
CARD_CANDIDATE_REGEX = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

# Prefix based address captures: strictly bounded prefixes
ADDRESS_PREFIX_PATTERNS = [
    re.compile(r"(?i)\b(deliver\s+to|delivery\s+address|address|pickup\s+from|sent\s+to)(:?)\s*([^\n,]+(?:,[^\n,]+){0,2})"),
]

# Explicit standalone street addresses
STANDALONE_ADDRESS_PATTERNS = [
    re.compile(r"(?i)\bNo\.?\s*\d+[/A-Za-z0-9\-]*,?\s+[A-Za-z0-9\s]+(?:Road|Mawatha|Lane|Place|Street|Avenue|Mw)\b(?:,?\s*(?:Colombo\s*\d*|Kandy|Galle|Gampaha|Negombo|Kurunegala|Jaffna|Matara|Nugegoda|\b[0-9]{5}\b))?"),
    re.compile(r"(?i)\b(?:[A-Z][a-z]+\s+)?(?:Road|Mawatha|Lane|Place|Street|Avenue)\b(?:,?\s*(?:Colombo\s*\d*|Kandy|Galle|Gampaha|Negombo|Kurunegala|Jaffna|Matara|Nugegoda|\b[0-9]{5}\b))"),
    re.compile(r"(?i)\b(?:Flower\s+Road|Temple\s+Road|Galle\s+Road|Kandy\s+Road|Main\s+Street|High\s+Level\s+Road)(?:,?\s*(?:Colombo\s*\d*|Kandy|Galle|Gampaha|Negombo|Kurunegala|Jaffna|Matara|Nugegoda|\b[0-9]{5}\b))?"),
]

# Name intro regex
NAME_INTRO_REGEX = re.compile(
    r"(?i:\b(?:my\s+name\s+is|i\s+am|customer:\s*|buyer:\s*)\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})"
)


def redact_pii(text: str) -> RedactResult:
    """Redact PII from customer text while preserving Order IDs, Model numbers and Prices.
    
    Replaces sensitive data with:
    [PHONE], [EMAIL], [NIC], [CARD], [ADDRESS], [PERSON]
    """
    if not text:
        return RedactResult(text="", types_found=[], spans=[])

    redacted = text
    types_found = set()
    spans = []

    # 1. Emails
    for match in EMAIL_REGEX.finditer(redacted):
        types_found.add("EMAIL")
    redacted = EMAIL_REGEX.sub("[EMAIL]", redacted)

    # 2. NIC (Old and New)
    for match in OLD_NIC_REGEX.finditer(redacted):
        types_found.add("NIC")
    redacted = OLD_NIC_REGEX.sub("[NIC]", redacted)

    for match in NEW_NIC_REGEX.finditer(redacted):
        types_found.add("NIC")
    redacted = NEW_NIC_REGEX.sub("[NIC]", redacted)

    # 3. Phone Numbers
    for match in PHONE_REGEX.finditer(redacted):
        types_found.add("PHONE")
    redacted = PHONE_REGEX.sub("[PHONE]", redacted)

    # 4. Payment Cards (validate with Luhn)
    def _card_repl(m):
        raw = m.group(0)
        digits = re.sub(r"\D", "", raw)
        if len(digits) >= 13 and luhn_check(digits):
            types_found.add("CARD")
            return "[CARD]"
        return raw

    redacted = CARD_CANDIDATE_REGEX.sub(_card_repl, redacted)

    # 5. Addresses with explicit prefix
    for prefix_pat in ADDRESS_PREFIX_PATTERNS:
        for match in prefix_pat.finditer(redacted):
            if not any(ph in match.group(0) for ph in ["[PHONE]", "[EMAIL]", "[NIC]", "[CARD]"]):
                types_found.add("ADDRESS")
        redacted = prefix_pat.sub(lambda m: f"{m.group(1)}{m.group(2)} [ADDRESS]", redacted)

    # Standalone addresses
    for addr_pat in STANDALONE_ADDRESS_PATTERNS:
        for match in addr_pat.finditer(redacted):
            matched_str = match.group(0)
            if not any(ph in matched_str for ph in ["[PHONE]", "[EMAIL]", "[NIC]", "[CARD]", "[ADDRESS]"]):
                types_found.add("ADDRESS")
        redacted = addr_pat.sub("[ADDRESS]", redacted)

    # 6. Person Names
    for match in NAME_INTRO_REGEX.finditer(redacted):
        types_found.add("PERSON")

    def _name_intro_repl(m):
        full_match = m.group(0)
        name_part = m.group(1)
        return full_match.replace(name_part, "[PERSON]")

    redacted = NAME_INTRO_REGEX.sub(_name_intro_repl, redacted)

    # Use spaCy for NER Person names if available
    if nlp_spacy:
        doc = nlp_spacy(redacted)
        preserved_words = {"galaxy", "redmi", "samsung", "iphone", "power", "bank", "lkr", "rs", "ceylon", "urbanwear", "volgear"}
        person_spans = []
        for ent in doc.ents:
            if ent.label_ == "PERSON" and ent.text not in ("[PERSON]", "[EMAIL]", "[PHONE]", "[NIC]", "[CARD]", "[ADDRESS]"):
                if not any(w in ent.text.lower() for w in preserved_words) and not re.match(r"^ORD-\d+", ent.text):
                    person_spans.append((ent.start_char, ent.end_char, ent.text))
        
        for start, end, name_text in sorted(person_spans, key=lambda x: x[0], reverse=True):
            types_found.add("PERSON")
            redacted = redacted[:start] + "[PERSON]" + redacted[end:]

    return RedactResult(
        text=redacted,
        types_found=sorted(list(types_found)),
        spans=spans,
    )
