import pytest
from app.nlp.sentiment import analyze_sentiment
from app.nlp.intent import classify_intent_and_urgency
from app.nlp.entity_extractor import extract_entities, extract_order_id, extract_brand
from app.nlp.extractor import IntakeExtractor


def test_sentiment_negative_defect():
    text = "The headphones are completely broken and terrible! I hate this awful product."
    label, score = analyze_sentiment(text)
    assert label == "negative"
    assert score < 0.0


def test_sentiment_positive_exchange():
    text = "I really love the quality and great material, but I just need a different size please. Thanks!"
    label, score = analyze_sentiment(text)
    assert label == "positive"
    assert score > 0.0


def test_intent_and_urgency_refund():
    text = "Order #98721 arrived damaged. This is urgent, refund my money immediately!"
    intent, urgency = classify_intent_and_urgency(text)
    assert intent == "refund"
    assert urgency == "high"


def test_intent_exchange():
    text = "The Nike shoes are too small, can I exchange them for size 10? No rush."
    intent, urgency = classify_intent_and_urgency(text)
    assert intent == "exchange"
    assert urgency == "low"


def test_entity_extraction_sony_headphones():
    text = "My Sony WH-1000XM5 headphones stopped working after 2 days. Order #ORD-88219, cost was $349.99."
    entities = extract_entities(text)
    assert "Sony" in entities["product"] or entities["entities"].get("brand") == "Sony"
    assert entities["entities"].get("order_id") == "ORD-88219" or "88219" in str(entities["entities"].get("order_id"))
    assert "stop" in entities["issue"].lower() or "working" in entities["issue"].lower()


def test_intake_extractor_end_to_end():
    extractor = IntakeExtractor(use_llm_fallback=False)
    text = "I received a defective Apple MacBook Pro with screen flickering. Order #55442. Please process a refund ASAP."
    result = extractor.extract(text)
    assert result.raw_text == text
    assert "Apple" in result.product or "MacBook" in result.product
    assert "flicker" in result.issue.lower() or "defective" in result.issue.lower()
    assert result.intent in ("refund", "return")
    assert result.sentiment in ("negative", "neutral")
    assert result.urgency in ("high", "medium")
    assert result.confidence > 0.5
    assert result.extracted_entities.get("order_id") is not None


def test_empty_input_handling():
    extractor = IntakeExtractor(use_llm_fallback=False)
    result = extractor.extract("")
    assert result.confidence == 0.0
    assert result.intent == "unknown"


def test_apparel_exchange_with_pricing():
    extractor = IntakeExtractor(use_llm_fallback=False)
    text = "The Zara jacket I bought for $89.99 has loose stitching on the sleeve. Can I exchange for another item?"
    result = extractor.extract(text)
    assert "Zara" in result.product or result.extracted_entities.get("brand") == "Zara"
    assert result.intent == "exchange"
    assert result.extracted_entities.get("price") == "$89.99" or "89.99" in str(result.extracted_entities.get("price"))


def test_kitchen_appliance_return():
    extractor = IntakeExtractor(use_llm_fallback=False)
    text = "My Philips coffee maker is leaking water from the base. Order #PH-9021. I want to return this defective unit."
    result = extractor.extract(text)
    assert "Philips" in result.product or "coffee" in result.product.lower()
    assert "leak" in result.issue.lower() or "defective" in result.issue.lower()
    assert result.intent == "return"
    assert result.sentiment in ("negative", "neutral")


def test_inquiry_intent():
    extractor = IntakeExtractor(use_llm_fallback=False)
    text = "What is the warranty coverage for Samsung monitors? Just wondering before my return period ends."
    result = extractor.extract(text)
    assert "Samsung" in result.product or result.extracted_entities.get("brand") == "Samsung"
    assert result.intent in ("inquiry", "return")
    assert result.urgency == "low"
