import anthropic

from rootcause.config import ANTHROPIC_API_KEY, MODEL

_client = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else anthropic.Anthropic()
    return _client


def chat(messages: list[dict], system: str | None = None, max_tokens: int = 2000) -> str:
    client = get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    return "".join(block.text for block in response.content if block.type == "text")


def parse_structured(messages: list[dict], output_model, system: str | None = None, max_tokens: int = 2000):
    client = get_client()
    response = client.messages.parse(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
        output_format=output_model,
    )
    return response.parsed_output
