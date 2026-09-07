"""
Auto-detects the best available model for the configured provider.
Supports OpenAI and AIML API.
"""
import os

OPENAI_PRIORITY = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
AIML_PRIORITY   = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo",
                   "meta-llama/Llama-3.3-70B-Instruct-Turbo", "google/gemma-3-27b-it"]
FALLBACK = "gpt-3.5-turbo"

_cache: dict[str, str] = {}


def resolve_model(api_key: str) -> str:
    """Returns the best model available for this API key."""
    if not api_key:
        return FALLBACK

    cached = _cache.get(api_key[:12])
    if cached:
        return cached

    # Detect AIML API key (starts with known prefix or env var set)
    aiml_key = os.environ.get("AIML_API_KEY", "")
    is_aiml = (api_key == aiml_key and aiml_key) or api_key.startswith("aiml")

    try:
        from openai import OpenAI
        if is_aiml:
            client = OpenAI(api_key=api_key, base_url="https://api.aimlapi.com/v1")
            priority = AIML_PRIORITY
        else:
            client = OpenAI(api_key=api_key)
            priority = OPENAI_PRIORITY

        available = {m.id for m in client.models.list().data}
        for model in priority:
            if model in available:
                _cache[api_key[:12]] = model
                return model
    except Exception:
        pass

    _cache[api_key[:12]] = FALLBACK
    return FALLBACK


def get_active_model() -> str:
    """Get the best model from currently configured API keys."""
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    aiml_key   = os.environ.get("AIML_API_KEY", "")
    key = openai_key or aiml_key
    if not key:
        return FALLBACK
    return resolve_model(key)
