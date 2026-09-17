from google import genai
from google.genai import types

from rootcause.config import GEMINI_API_KEY, MODEL

_client = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else genai.Client()
    return _client


def _to_gemini_contents(messages: list[dict]) -> list[dict]:
    """Anthropic-style {"role": "user"|"assistant", "content": str} -> Gemini's
    {"role": "user"|"model", "parts": [str]}."""
    return [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [m["content"]]}
        for m in messages
    ]


def chat(messages: list[dict], system: str | None = None, max_tokens: int = 2000) -> str:
    client = get_client()
    response = client.models.generate_content(
        model=MODEL,
        contents=_to_gemini_contents(messages),
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text or ""


def parse_structured(messages: list[dict], output_model, system: str | None = None, max_tokens: int = 2000):
    client = get_client()
    response = client.models.generate_content(
        model=MODEL,
        contents=_to_gemini_contents(messages),
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
            response_json_schema=output_model.model_json_schema(),
        ),
    )
    return output_model.model_validate_json(response.text)
