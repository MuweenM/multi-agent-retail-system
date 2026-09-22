"""
Agent 1 (Intake) output contract.
Defines the schema for structured return case data extracted from customer text.
"""
from typing import Any, Dict
from pydantic import BaseModel, Field


class IntakeOutput(BaseModel):
    raw_text: str = Field(description="Original customer return text or complaint")
    product: str = Field(description="Extracted product name or item description")
    issue: str = Field(description="Extracted issue, defect, or return reason")
    intent: str = Field(
        default="return",
        description="Customer intent e.g. return, refund, exchange, complaint, inquiry, unknown",
    )
    sentiment: str = Field(
        default="neutral",
        description="Sentiment classification: positive, neutral, negative",
    )
    sentiment_score: float = Field(
        default=0.0,
        description="Sentiment polarity score from -1.0 (most negative) to 1.0 (most positive)",
    )
    urgency: str = Field(
        default="medium",
        description="Urgency level: low, medium, high",
    )
    confidence: float = Field(
        default=0.0,
        description="Confidence score of the extraction between 0.0 and 1.0",
    )
    extracted_entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured entities like order_id, brand, price, defect_keywords, etc.",
    )
    extraction_method: str = Field(
        default="nlp_engine",
        description="Method used for extraction: nlp_engine or llm_fallback",
    )
