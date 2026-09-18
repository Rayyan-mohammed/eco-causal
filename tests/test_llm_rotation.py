import itertools

import httpx
import pytest
from google.genai import errors

from rootcause import llm


@pytest.fixture
def fake_clients():
    saved = (llm._clients, llm._rotation)
    llm._clients = ["key-a", "key-b", "key-c"]
    llm._rotation = itertools.cycle(range(3))
    yield llm._clients
    llm._clients, llm._rotation = saved


def _api_error(code: int) -> errors.APIError:
    return errors.APIError(code, {"error": {"code": code, "message": "x", "status": "X"}})


def test_timeout_on_first_key_falls_through_to_next(fake_clients):
    calls = []

    def call(client):
        calls.append(client)
        if client == "key-a":
            raise httpx.ConnectTimeout("timed out")
        return f"ok from {client}"

    assert llm._call_with_rotation(call) == "ok from key-b"
    assert calls == ["key-a", "key-b"]


def test_503_falls_through_to_next_key(fake_clients):
    def call(client):
        if client != "key-c":
            raise _api_error(503)
        return "ok"

    assert llm._call_with_rotation(call) == "ok"


def test_non_retryable_error_raises_immediately(fake_clients):
    calls = []

    def call(client):
        calls.append(client)
        raise _api_error(400)

    with pytest.raises(errors.APIError):
        llm._call_with_rotation(call)
    assert calls == ["key-a"]  # did not burn the other keys on a bad request


def test_all_keys_failing_raises_last_error(fake_clients):
    def call(client):
        raise httpx.ReadTimeout("slow")

    with pytest.raises(httpx.ReadTimeout):
        llm._call_with_rotation(call)


def test_clients_are_built_without_sdk_level_retries():
    assert llm._HTTP_OPTIONS.retry_options.attempts == 1
    assert llm._HTTP_OPTIONS.timeout == llm._PER_ATTEMPT_TIMEOUT_MS
