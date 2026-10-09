"""Agent 1 NLP Pipeline combining Sanitization, PII Redaction, Normalization, Sinhala Pivot, Spell Correction, Product Matching, NER, LLM Extraction, and Confidence Scoring."""

import json
import os
import re
import sys
from typing import Optional

# Support local and root path imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from retail_common.security.sanitize import sanitize_text
from retail_common.security.pii import redact_pii
from retail_common.text.normalize import normalize_text
from retail_common.schemas.intake import IntakeOutput, Entity
from retail_common.llm import call_llm
from app.nlp.spell import SpellCorrector
from app.nlp.product_match import ProductMatcher
from app.nlp.ner import extract_entities
from app.nlp.sentiment import analyze_sentiment
from app.nlp.sinhala import detect_language, translate_to_english_pivot

# Singleton instances
spell_corrector = SpellCorrector()
product_matcher = ProductMatcher()

# Load system prompt
PROMPT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../prompts/extract_system.md"))
SYSTEM_PROMPT = ""
if os.path.exists(PROMPT_PATH):
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()


def calculate_confidence(
    llm_self_conf: float,
    product_match_score: float,
    entities_count: int,
    total_tokens: int,
    corrected_tokens_count: int,
) -> float:
    """Calculate composite confidence score per Blueprint formula.
    
    Confidence = 0.4 * llm_self_conf + 0.3 * product_match_score + 0.2 * entity_coverage + 0.1 * (1 - fraction_corrected)
    """
    entity_coverage = min(1.0, entities_count / 3.0)
    fraction_corrected = (corrected_tokens_count / total_tokens) if total_tokens > 0 else 0.0
    token_quality = max(0.0, 1.0 - fraction_corrected)

    conf = (
        (0.4 * llm_self_conf)
        + (0.3 * product_match_score)
        + (0.2 * entity_coverage)
        + (0.1 * token_quality)
    )
    return round(min(0.98, max(0.10, conf)), 2)


def process_intake_pipeline(
    text: str,
    tenant_id: str = "demo",
    lang_hint: Optional[str] = None,
) -> IntakeOutput:
    """Execute complete intake pipeline."""
    if not text or not text.strip():
        return IntakeOutput(
            raw_text="",
            clean_text="",
            product="unknown",
            issue="empty complaint text",
            intent="unknown",
            sentiment="neutral",
            confidence=0.0,
            tenant_id=tenant_id,
            flags=["empty_input"],
        )

    flags = []

    # 1. Sanitize
    sanitized_res = sanitize_text(text)
    if sanitized_res.flags:
        flags.extend(sanitized_res.flags)

    # 2. PII Redaction
    redact_res = redact_pii(sanitized_res.text)
    pii_types_found = redact_res.types_found

    # 3. Language Detection & Sinhala/Singlish Pivot (Phase 5)
    detected_lang = lang_hint or detect_language(redact_res.text)
    working_text, was_translated = translate_to_english_pivot(redact_res.text, detected_lang)
    if was_translated:
        flags.append("translated")

    # 4. Normalize
    normalized = normalize_text(working_text)

    # 5. Spell Correction (Disabled due to Jaccard hallucination)
    corrected_text = normalized
    spell_changes = []

    # 6. Product Matching
    matched_products = product_matcher.match(corrected_text, top_k=3)
    best_product_id = matched_products[0][0] if matched_products else None
    best_product_name = matched_products[0][1] if matched_products else "unknown"
    best_product_score = matched_products[0][2] if matched_products else 0.0

    # 7. NER
    entities = extract_entities(corrected_text)

    # 8. Intent & Sentiment
    lower_t = corrected_text.lower()
    inferred_intent = "return"
    if "refund" in lower_t:
        inferred_intent = "refund"
    elif "exchange" in lower_t or "replace" in lower_t or "swap" in lower_t:
        inferred_intent = "exchange"
    elif any(w in lower_t for w in ["defect", "broken", "damaged", "fail", "crackling", "leak", "leaked", "chip", "stale"]):
        inferred_intent = "complaint"

    inferred_sentiment = analyze_sentiment(corrected_text)

    # LLM Extraction attempt
    candidates_json = json.dumps(
        [{"id": pid, "name": name, "score": score} for pid, name, score in matched_products],
        indent=2,
    )
    user_prompt = f"Candidate products:\n{candidates_json}\n\n<complaint>\n{corrected_text}\n</complaint>"

    llm_extracted = None
    try:
        raw_llm_response = call_llm(user_prompt, system_prompt=SYSTEM_PROMPT, temperature=0.1)
        json_match = re.search(r"\{.*\}", raw_llm_response, re.DOTALL)
        if json_match:
            llm_extracted = json.loads(json_match.group(0))
    except Exception:
        llm_extracted = None

    if not llm_extracted or not isinstance(llm_extracted, dict):
        flags.append("llm_fallback")

    # Product resolution (Strict Catalog Enforcement to prevent LLM Hallucination)
    if best_product_score >= 0.35:
        resolved_product_id = best_product_id
        resolved_product_name = best_product_name
    elif (
        llm_extracted 
        and float(llm_extracted.get("self_confidence", 0.0)) >= 0.70
        and llm_extracted.get("product_id") in [pid for pid, _, _ in matched_products]
    ):
        resolved_product_id = llm_extracted.get("product_id")
        resolved_product_name = llm_extracted.get("product")
    else:
        llm_prod = llm_extracted.get("product") if llm_extracted else None
        llm_conf = float(llm_extracted.get("self_confidence", 0.0)) if llm_extracted else 0.0
        
        candidate_names = [name.lower() for _, name, _ in matched_products]
        is_novel_product = llm_prod and str(llm_prod).lower() not in candidate_names

        # Anti-Hallucination: Ensure the LLM didn't just invent a product not mentioned in the text
        llm_prod_words = set(re.findall(r'\b\w{3,}\b', str(llm_prod).lower())) if llm_prod else set()
        text_words = set(re.findall(r'\b\w{3,}\b', corrected_text.lower()))
        has_overlap = bool(llm_prod_words & text_words)

        if is_novel_product and str(llm_prod).lower() != "unknown" and llm_conf >= 0.70 and has_overlap:
            import csv
            import uuid
            from pathlib import Path
            new_id = f"P-DYN-{uuid.uuid4().hex[:6].upper()}"
            products_csv = Path(__file__).parents[4] / "data" / "catalog" / "products.csv"
            try:
                with open(products_csv, "a", newline="", encoding="utf-8") as fh:
                    writer = csv.writer(fh)
                    writer.writerow([new_id, llm_prod, "auto_injected", "SUP-999", "0.00"])
                resolved_product_id = new_id
                resolved_product_name = llm_prod
                flags.append("dynamically_injected")
            except Exception:
                resolved_product_id = None
                resolved_product_name = "Unknown Product (Not in Catalog)"
                flags.append("out_of_catalog")
        else:
            resolved_product_id = None
            resolved_product_name = "Unknown Product (Not in Catalog)"
            flags.append("out_of_catalog")

    # Issue extraction
    sentences = re.split(r"[.!?]\s+", corrected_text)
    issue_sentence = sentences[0] if sentences else corrected_text

    final_intent = inferred_intent if inferred_intent != "return" else (llm_extracted.get("intent", "return") if llm_extracted else "return")
    final_sentiment = inferred_sentiment if inferred_sentiment != "neutral" else (llm_extracted.get("sentiment", "neutral") if llm_extracted else "neutral")

    # Composite Confidence
    total_tokens = len(normalized.split())
    corrected_count = len(spell_changes)
    confidence = calculate_confidence(
        llm_self_conf=float(llm_extracted.get("self_confidence", 0.85) if llm_extracted else 0.75),
        product_match_score=best_product_score,
        entities_count=len(entities),
        total_tokens=total_tokens,
        corrected_tokens_count=corrected_count,
    )

    return IntakeOutput(
        raw_text="",
        clean_text=corrected_text,
        product=resolved_product_name,
        product_id=resolved_product_id,
        product_match_score=best_product_score,
        issue=issue_sentence[:500].strip(),
        intent=final_intent,
        sentiment=final_sentiment,
        confidence=confidence,
        summary=f"Customer requested {final_intent} for {resolved_product_name}.",
        tenant_id=tenant_id,
        entities=entities,
        lang=detected_lang,
        pii_types_found=pii_types_found,
        flags=sorted(list(set(flags))),
    )
