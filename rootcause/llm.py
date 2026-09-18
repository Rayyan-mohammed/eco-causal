import itertools

import httpx
from google import genai
from google.genai import errors, types

from rootcause.config import GEMINI_API_KEYS, MODEL

_clients: list[genai.Client] = []
_rotation = None

# The SDK's default is to retry each request several times with exponential
# backoff *on the same key* before raising. With several keys available that's
# the wrong order: one congested key can burn 30-60s before rotation ever
# gets a turn (observed live: an identical request took 2s, 2s, then 51s).
# So: no in-SDK retries, a hard per-attempt timeout, and let rotation across
# keys be the retry strategy — a failing key costs seconds, not a minute.
_PER_ATTEMPT_TIMEOUT_MS = 30_000
_HTTP_OPTIONS = types.HttpOptions(
    timeout=_PER_ATTEMPT_TIMEOUT_MS,
    retry_options=types.HttpRetryOptions(attempts=1),
)


def _get_clients() -> list[genai.Client]:
    global _clients, _rotation
    if not _clients:
        _clients = [
            genai.Client(api_key=key, http_options=_HTTP_OPTIONS) for key in GEMINI_API_KEYS
        ] or [genai.Client(http_options=_HTTP_OPTIONS)]
        _rotation = itertools.cycle(range(len(_clients)))
    return _clients


_RETRYABLE_CODES = {429, 500, 503}  # rate limit, and transient server overload


def _call_with_rotation(call):
    """Round-robins across all configured Gemini keys on every call, and falls
    back to the next key within the same call on a rate limit (429), transient
    server overload (500/503), or a timeout/connection failure, so many
    personal accounts add up to higher effective throughput without any single
    one being pinned as 'the' key."""
    clients = _get_clients()
    last_error = None
    for _ in range(len(clients)):
        client = clients[next(_rotation)]
        try:
            return call(client)
        except errors.APIError as e:
            if e.code in _RETRYABLE_CODES:
                last_error = e
                continue
            raise
        except httpx.TransportError as e:  # timeouts, dropped connections
            last_error = e
            continue
    raise last_error


def _to_gemini_contents(messages: list[dict]) -> list[dict]:
    """Anthropic-style {"role": "user"|"assistant", "content": str} -> Gemini's
    {"role": "user"|"model", "parts": [{"text": str}]}."""
    return [
        {"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]}
        for m in messages
    ]


def chat(messages: list[dict], system: str | None = None, max_tokens: int = 4096) -> str:
    # Gemini 3.x thinks by default and thinking tokens draw from max_output_tokens,
    # so a generous ceiling here is what keeps the visible answer from being
    # starved out entirely on harder prompts.
    contents = _to_gemini_contents(messages)
    config = types.GenerateContentConfig(system_instruction=system, max_output_tokens=max_tokens)

    def _call(client: genai.Client) -> str:
        response = client.models.generate_content(model=MODEL, contents=contents, config=config)
        return response.text or ""

    return _call_with_rotation(_call)


def parse_structured(
    messages: list[dict],
    output_model,
    system: str | None = None,
    max_tokens: int = 2000,
    disable_thinking: bool = True,
):
    # Mechanical extraction (parsing free text into fields, or a recommendation
    # into a causal chain) doesn't benefit from reasoning, so thinking is
    # disabled by default: faster, cheaper, and avoids the thinking-tokens-
    # starve-the-JSON failure mode entirely. The recommendation draft itself is
    # the one structured call where reasoning quality matters, so it opts back
    # in with disable_thinking=False.
    contents = _to_gemini_contents(messages)
    config_kwargs = dict(
        system_instruction=system,
        max_output_tokens=max_tokens,
        response_mime_type="application/json",
        response_json_schema=output_model.model_json_schema(),
    )
    if disable_thinking:
        config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
    config = types.GenerateContentConfig(**config_kwargs)

    def _call(client: genai.Client):
        response = client.models.generate_content(model=MODEL, contents=contents, config=config)
        return output_model.model_validate_json(response.text)

    return _call_with_rotation(_call)
