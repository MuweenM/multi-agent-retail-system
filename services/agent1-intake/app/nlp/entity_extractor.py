"""
Entity extractor for retail returns (products, defects, order IDs, brands, prices).
"""
import re
from typing import Dict, Any, List, Optional

KNOWN_BRANDS = [
    "Sony", "Apple", "Samsung", "Nike", "Adidas", "Dell", "HP", "Lenovo",
    "Bose", "Logitech", "LG", "Anker", "Dyson", "Philips", "Asus", "Acer",
    "Puma", "Zara", "Canon", "Nikon", "Microsoft", "Nintendo", "PlayStation"
]

DEFECT_KEYWORDS = [
    "stop working", "stopped working", "not working", "doesn't work", "does not work",
    "broken", "damaged", "cracked", "shattered", "scratched", "faulty", "defective",
    "not charging", "won't charge", "battery drain", "battery dead", "overheating",
    "wrong size", "too small", "too large", "too tight", "too loose",
    "wrong color", "wrong item", "different item", "missing parts", "missing accessories",
    "torn", "ripped", "stained", "faded", "loose stitching", "zipper stuck",
    "noisy", "buzzing", "screen flickering", "dead pixels", "malfunction",
    "poor quality", "leaking", "smells", "no power", "blank screen"
]


def extract_order_id(text: str) -> Optional[str]:
    patterns = [
        r"(?:order|ord|invoice|receipt)[#:\s-]*([A-Za-z0-9-_]{4,20})",
        r"#([0-9]{4,12})",
        r"\b(ORD-[0-9A-Z]{4,10})\b"
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def extract_price(text: str) -> Optional[str]:
    m = re.search(r"(\$\s*[0-9]+(?:\.[0-9]{2})?|\b[0-9]+(?:\.[0-9]{2})?\s*(?:usd|dollars|eur|gbp)\b)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def extract_brand(text: str) -> Optional[str]:
    for brand in KNOWN_BRANDS:
        if re.search(r"\b" + re.escape(brand) + r"\b", text, re.IGNORECASE):
            return brand
    return None


def extract_issue_description(text: str) -> str:
    for defect in DEFECT_KEYWORDS:
        if defect in text.lower():
            sentences = re.split(r"[.!?\n]", text)
            for s in sentences:
                if defect in s.lower():
                    clean = s.strip(" ,.-;")
                    if len(clean) > 3:
                        return clean
            return defect

    m = re.search(r"(?:because|since|but|issue is|problem is|defect is)\s+([^.!?]+)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    sentences = [s.strip() for s in re.split(r"[.!?\n]", text) if s.strip()]
    if sentences:
        return sentences[0][:120]
    return text.strip()[:100]


def extract_product_name(text: str) -> str:
    brand = extract_brand(text)

    patterns = [
        r"(?:my|the|this|bought\s+a|purchased\s+a|received\s+a)\s+([A-Z0-9][A-Za-z0-9\s-]{2,30}?)(?:\s+(?:is|was|has|stopped|doesn|came|arrived|broke|because|order)|\.|\,)",
        r"(?:for\s+(?:the|my)?\s*)([A-Z0-9][A-Za-z0-9\s-]{2,30}?)(?:\s+(?:which|that|because)|\.|\,)",
        r"([A-Z][a-zA-Z0-9-]+\s+[A-Za-z0-9-]+(?:\s+[A-Za-z0-9-]+)?)"
    ]

    for pat in patterns:
        m = re.search(pat, text)
        if m:
            candidate = m.group(1).strip()
            if candidate.lower() not in {"order", "item", "product", "package", "box", "refund", "return", "problem", "money"}:
                if brand and brand.lower() not in candidate.lower():
                    return f"{brand} {candidate}"
                return candidate

    if brand:
        m = re.search(r"\b" + re.escape(brand) + r"\s+([A-Za-z0-9\-_]{2,25}(?:\s+[A-Za-z0-9\-_]{2,20})?)", text, re.IGNORECASE)
        if m:
            return f"{brand} {m.group(1).strip()}"
        return brand

    common_items = [
        "headphones", "earbuds", "laptop", "keyboard", "mouse", "monitor", "smartwatch",
        "shoes", "sneakers", "jacket", "shirt", "pants", "dress", "sweater", "hoodie",
        "coffee maker", "blender", "vacuum cleaner", "air fryer", "toaster",
        "phone case", "charger", "cable", "tablet", "speaker"
    ]
    for item in common_items:
        if re.search(r"\b" + re.escape(item) + r"\b", text, re.IGNORECASE):
            return item.title()

    return "Unknown Item"


def extract_entities(text: str) -> Dict[str, Any]:
    brand = extract_brand(text)
    order_id = extract_order_id(text)
    price = extract_price(text)
    product = extract_product_name(text)
    issue = extract_issue_description(text)

    matched_defects = [d for d in DEFECT_KEYWORDS if d in text.lower()]

    entities = {
        "brand": brand,
        "order_id": order_id,
        "price": price,
        "matched_defects": matched_defects
    }

    return {
        "product": product,
        "issue": issue,
        "entities": {k: v for k, v in entities.items() if v is not None}
    }
