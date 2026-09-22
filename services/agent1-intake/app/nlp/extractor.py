"""
IntakeExtractor: Combines NLP rule-based entity/sentiment/intent extraction
with optional LLM fallback for structured return case creation.
"""
import json
import logging
from typing import Optional
from retail_common.schemas.intake import IntakeOutput
from .sentiment import analyze_sentiment
from .intent import classify_intent_and_urgency
from .entity_extractor import extract_entities

logger = logging.getLogger(__name__)


class IntakeExtractor:
    def __init__(self, use_llm_fallback: bool = True):
        self.use_llm_fallback = use_llm_fallback

    def extract(self, text: str) -> IntakeOutput:
        if not text or not text.strip():
            return IntakeOutput(
                raw_text=text or '',
                product='Unknown Item',
                issue='No issue provided',
                intent='unknown',
                sentiment='neutral',
                sentiment_score=0.0,
                urgency='low',
                confidence=0.0,
                extracted_entities={},
                extraction_method='nlp_engine'
            )

        clean_text = text.strip()

        sentiment_label, sentiment_score = analyze_sentiment(clean_text)
        intent, urgency = classify_intent_and_urgency(clean_text)
        entity_res = extract_entities(clean_text)

        product = entity_res['product']
        issue = entity_res['issue']
        extracted_entities = entity_res['entities']

        confidence = 0.5
        if product != 'Unknown Item':
            confidence += 0.25
        if issue and issue != 'No issue provided':
            confidence += 0.15
        if extracted_entities.get('brand') or extracted_entities.get('order_id'):
            confidence += 0.1
        confidence = round(min(1.0, confidence), 2)

        if self.use_llm_fallback and confidence < 0.65:
            llm_result = self._try_llm_extraction(clean_text)
            if llm_result:
                return llm_result

        return IntakeOutput(
            raw_text=clean_text,
            product=product,
            issue=issue,
            intent=intent,
            sentiment=sentiment_label,
            sentiment_score=sentiment_score,
            urgency=urgency,
            confidence=confidence,
            extracted_entities=extracted_entities,
            extraction_method='nlp_engine'
        )

    def _try_llm_extraction(self, text: str) -> Optional[IntakeOutput]:
        try:
            from retail_common.llm_client import call_llm

            system_prompt = ("You are an NLP extraction agent for a retail customer return system. "
                             "Extract structured fields from the user's return text and output ONLY valid JSON "
                             "with keys: product (string), issue (string), intent (return|refund|exchange|complaint|inquiry), "
                             "sentiment (positive|neutral|negative), sentiment_score (float between -1.0 and 1.0), "
                             "urgency (low|medium|high), confidence (float between 0.0 and 1.0), "
                             "extracted_entities (object with brand, order_id, price if found).")

            prompt = f'Customer text: \"{text}\"\n\nJSON output:'
            response = call_llm(prompt=prompt, system=system_prompt, max_tokens=500)
            
            start = response.find('{')
            end = response.rfind('}')
            if start != -1 and end != -1:
                data = json.loads(response[start:end+1])
                return IntakeOutput(
                    raw_text=text,
                    product=data.get('product', 'Unknown Item'),
                    issue=data.get('issue', text[:100]),
                    intent=data.get('intent', 'return'),
                    sentiment=data.get('sentiment', 'neutral'),
                    sentiment_score=float(data.get('sentiment_score', 0.0)),
                    urgency=data.get('urgency', 'medium'),
                    confidence=float(data.get('confidence', 0.85)),
                    extracted_entities=data.get('extracted_entities', {}),
                    extraction_method='llm_fallback'
                )
        except Exception as e:
            logger.warning('LLM fallback extraction skipped or failed: %s', str(e))
        return None
