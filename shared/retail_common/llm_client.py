"""
Single shared wrapper around the LLM API so all four agents call the
model the same way.

TODO (whoever sets this up first):
- Confirm LLM_PROVIDER / LLM_API_KEY / LLM_MODEL are filled in your .env
- If you switch to OpenAI instead of Anthropic, update the client below
  accordingly (swap `from anthropic import Anthropic` for the OpenAI SDK)
"""
from anthropic import Anthropic
from .config import settings
from .logging_config import get_logger

logger = get_logger(__name__)
_client = Anthropic(api_key=settings.llm_api_key) if settings.llm_api_key else None


def call_llm(
    prompt: str,
    system: str | None = None,
    max_tokens: int = 1000,
    temperature: float = 0.0,
) -> str:
    """
    Shared LLM call. Every agent should go through this function
    rather than instantiating its own client.
    """
    if _client is None:
        raise RuntimeError("LLM_API_KEY is not set. Copy .env.example to .env and fill it in.")

    logger.info("Calling LLM (model=%s, prompt_len=%d)", settings.llm_model, len(prompt))
    response = _client.messages.create(
        model=settings.llm_model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system or "",
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")
