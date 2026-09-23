"""Input sanitization and prompt injection detection."""

from dataclasses import dataclass, field
import re
from shared.retail_common.text.normalize import normalize_text


@dataclass
class SanitizeResult:
    text: str
    flags: list[str] = field(default_factory=list)


# Prompt injection detection patterns
INJECTION_PATTERNS = [
    r"(?i)\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions\b",
    r"(?i)\bignore\s+the\s+system\s+prompt\b",
    r"(?i)\bsystem\s+prompt\b",
    r"(?i)\byou\s+are\s+now\b",
    r"(?i)\bdisregard\s+(?:all\s+)?(?:previous|prior)\b",
    r"(?i)\bact\s+as\s+(?:a|an)\s+(?:unrestricted|developer|admin|dan|jailbreak)\b",
    r"(?i)<\s*/?\s*system\s*>",
    r"(?i)<\s*/?\s*assistant\s*>",
    r"(?i)```\s*(?:system|eval|exec|bash|python)",
    r"(?i)\bprompt\s+injection\b",
    r"(?i)\boverride\s+all\s+(?:rules|policies|guidelines)\b",
]

# Base64 pattern for blobs >= 200 chars: [A-Za-z0-9+/]{200,}={0,2}
BASE64_LONG_BLOB = r"[A-Za-z0-9+/]{200,}={0,2}"


def sanitize_text(text: str, max_len: int = 2000) -> SanitizeResult:
    """Sanitize customer input text and flag suspected prompt injections.
    
    Never silently deletes injection content, but sets 'injection_suspected' flag.
    """
    if not text:
        return SanitizeResult(text="", flags=[])

    flags = []

    # Check for prompt injection patterns before or after normalisation
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            flags.append("injection_suspected")
            break

    # Check for long base64 blobs
    if "injection_suspected" not in flags and re.search(BASE64_LONG_BLOB, text):
        flags.append("injection_suspected")

    # Perform normalisation
    normalized = normalize_text(text, max_len=max_len)

    return SanitizeResult(text=normalized, flags=flags)
