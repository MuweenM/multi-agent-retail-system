"""Sinhala and Singlish language detection and translation module (Phase 5 behind ENABLE_SI)."""

import os
import re
from typing import Tuple

# Common Singlish romanised lexicon
SINGLISH_KEYWORDS = {
    "wada", "karanne", "na", "naha", "damma", "hoda", "awul", "kiyala", "karanna",
    "gatta", "awilla", "baha", "puluwan", "dapan", "mata", "me", "eka", "denna",
    "kadila", "thiyenne", "salli", "dawas", "gahala", "kade", "apahu",
}


def detect_language(text: str) -> str:
    """Detect language: 'si' (Sinhala Unicode), 'si-rom' (Singlish), or 'en' (English)."""
    if not text:
        return "en"

    # Check for Sinhala Unicode characters (U+0D80 to U+0DFF)
    if re.search(r"[\u0d80-\u0dff]", text):
        return "si"

    # Check for Singlish keywords in Latin script
    words = set(re.findall(r"[A-Za-z]+", text.lower()))
    singlish_matches = words & SINGLISH_KEYWORDS
    if len(singlish_matches) >= 2:
        return "si-rom"

    return "en"


def translate_to_english_pivot(text: str, lang: str) -> Tuple[str, bool]:
    """Translate Sinhala or Singlish text to English pivot if ENABLE_SI is active."""
    enable_si = os.getenv("ENABLE_SI", "false").lower() in ("true", "1", "yes")
    if not enable_si or lang == "en":
        return text, False

    # Simple dictionary pivot replacements for common phrases
    translations = {
        "wada karanne na": "not working",
        "wada na": "not working",
        "kadila": "broken",
        "salli apahu denna": "refund the money",
        "maru karanna": "exchange",
        "hoda na": "not good",
        "බැටරිය බහිනවා": "battery draining fast",
        "වැඩ කරන්නේ නෑ": "not working",
        "කැඩිලා": "broken",
        "මුදල් ආපසු දෙන්න": "refund money",
        "මාරු කරන්න": "exchange item",
    }

    translated_text = text
    for src, dst in translations.items():
        translated_text = translated_text.replace(src, dst)

    return translated_text, True
