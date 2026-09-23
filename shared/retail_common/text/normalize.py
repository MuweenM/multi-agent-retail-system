"""Text normalization module (Lecture 2 & Sinhala-safe handling)."""

import re
import unicodedata


def normalize_text(text: str, max_len: int = 2000) -> str:
    """Normalize unicode, strip control characters, preserve Sinhala ZWJ, collapse whitespace.
    
    Preserves U+200D (Zero Width Joiner) when sitting between Sinhala characters
    (U+0D80 to U+0DFF) as required for correct Sinhala conjunct rendering.
    """
    if not text:
        return ""

    # Unicode NFKC normalization
    text = unicodedata.normalize("NFKC", text)

    # Protect Sinhala ZWJ
    # Replace valid Sinhala ZWJ with a temporary placeholder
    sinhala_zwj_placeholder = "___SINHALA_ZWJ___"
    text = re.sub(
        r"([\u0d80-\u0dff])\u200d([\u0d80-\u0dff])",
        r"\1" + sinhala_zwj_placeholder + r"\2",
        text,
    )

    # Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Strip non-printable control characters & remaining zero-width chars (except newlines, tabs)
    # \u200B-\u200F, \uFEFF, control chars 0x00-0x1F except 0x09, 0x0A, 0x0D
    cleaned_chars = []
    for ch in text:
        code = ord(ch)
        if ch in ("\n", "\t", "\r"):
            cleaned_chars.append(" ")
        elif (0x00 <= code <= 0x1F) or (0x7F <= code <= 0x9F):
            continue
        elif 0x200B <= code <= 0x200F or code == 0xFEFF or code == 0x200D:
            continue
        else:
            cleaned_chars.append(ch)

    text = "".join(cleaned_chars)

    # Restore protected Sinhala ZWJ
    text = text.replace(sinhala_zwj_placeholder, "\u200d")

    # Collapse multiple whitespace characters into single space
    text = re.sub(r"\s+", " ", text).strip()

    # Truncate to max length
    if len(text) > max_len:
        text = text[:max_len].strip()

    return text
