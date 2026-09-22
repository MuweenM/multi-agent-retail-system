from pydantic import BaseModel, Field

class Entity(BaseModel):
    type: str                       # PRODUCT | BRAND | ORDER_ID | SKU | SIZE | COLOR | AMOUNT | DATE
    text: str
    start: int | None = None
    end: int | None = None

class IntakeOutput(BaseModel):
    raw_text: str                   # v1.0. Agent 1 returns "" here; Agent 4 keeps the original encrypted
    product: str
    issue: str
    intent: str
    sentiment: str
    confidence: float
    # v1.1 additions
    return_id: str = ""
    tenant_id: str = "demo"
    clean_text: str = ""            # sanitised, spell-corrected, PII-redacted. Only this may reach an LLM
    summary: str = ""               # one sentence, at most 20 words
    product_id: str | None = None
    product_match_score: float = 0.0
    entities: list[Entity] = Field(default_factory=list)
    lang: str = "en"                # en | si | si-rom
    pii_types_found: list[str] = Field(default_factory=list)   # types only, never values
    flags: list[str] = Field(default_factory=list)  # injection_suspected, spelling_corrected, llm_fallback, translated
