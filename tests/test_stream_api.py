import json

from fastapi.testclient import TestClient
import pytest

import api


class FakeLlm:
    def __init__(self, tokens=None, fail=False):
        self.tokens = tokens or ["hello", " world"]
        self.fail = fail

    def generate_stream(self, messages):
        if self.fail:
            raise RuntimeError("boom")
        yield from self.tokens


@pytest.fixture(autouse=True)
def _patch_system(monkeypatch):
    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (object(), None, FakeLlm(), None, None, "system", None, None),
    )


def _stream_data(response_text: str) -> list[str]:
    events = []
    for raw in response_text.split("\n\n"):
        raw = raw.strip()
        if raw.startswith("data: "):
            events.append(raw.removeprefix("data: "))
    return events


def _json_events(response_text: str) -> list[dict]:
    return [
        json.loads(data)
        for data in _stream_data(response_text)
        if data != "[DONE]"
    ]


def _patch_retrieve(monkeypatch, chunks):
    def fake_retrieve_context(**kwargs):
        return chunks, [{"role": "user", "content": kwargs["question"]}], "rewritten"

    monkeypatch.setattr(api, "_retrieve_context", fake_retrieve_context)


def test_stream_first_event_is_metadata(monkeypatch):
    _patch_retrieve(
        monkeypatch,
        [{"text": "context", "source": "manual.pdf", "page": 3, "distance": 0.1}],
    )

    response = TestClient(api.app).post(
        "/ask/stream", json={"question": "时间常数是什么"}
    )
    events = _json_events(response.text)

    assert response.status_code == 200
    assert events[0]["type"] == "metadata"


def test_stream_metadata_contains_required_fields(monkeypatch):
    _patch_retrieve(
        monkeypatch,
        [
            {"text": "a", "source": "manual.pdf", "page": 3, "distance": 0.1},
            {"text": "b", "source": "manual.pdf", "page": 4, "distance": 0.2},
            {"text": "c", "source": "notes.md", "page": None, "distance": 0.3},
        ],
    )

    response = TestClient(api.app).post(
        "/ask/stream", json={"question": "时间常数是什么"}
    )
    metadata = _json_events(response.text)[0]

    assert metadata["confidence"] == "high"
    assert metadata["rewritten_question"] == "rewritten"
    assert metadata["sources"] == [
        {"source": "manual.pdf", "page": 3},
        {"source": "notes.md", "page": None},
    ]


def test_stream_token_events_have_type_field(monkeypatch):
    _patch_retrieve(
        monkeypatch,
        [{"text": "context", "source": "manual.pdf", "page": 3, "distance": 0.1}],
    )

    response = TestClient(api.app).post(
        "/ask/stream", json={"question": "时间常数是什么"}
    )
    events = _json_events(response.text)
    token_events = [event for event in events if event["type"] == "token"]

    assert token_events
    assert all(event["type"] == "token" for event in token_events)
    assert [event["token"] for event in token_events] == ["hello", " world"]


def test_stream_ends_with_done(monkeypatch):
    _patch_retrieve(
        monkeypatch,
        [{"text": "context", "source": "manual.pdf", "page": 3, "distance": 0.1}],
    )

    response = TestClient(api.app).post(
        "/ask/stream", json={"question": "时间常数是什么"}
    )

    assert _stream_data(response.text)[-1] == "[DONE]"


def test_stream_empty_result_still_sends_metadata(monkeypatch):
    _patch_retrieve(monkeypatch, [])

    response = TestClient(api.app).post(
        "/ask/stream", json={"question": "知识库没有的问题"}
    )
    events = _json_events(response.text)

    assert events[0] == {
        "type": "metadata",
        "confidence": "low",
        "rewritten_question": "rewritten",
        "sources": [],
    }
    assert events[1] == {"type": "token", "token": "没有检索到相关内容。"}
    assert _stream_data(response.text)[-1] == "[DONE]"


def test_stream_llm_error_has_type_and_done(monkeypatch):
    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (object(), None, FakeLlm(fail=True), None, None, "system", None, None),
    )
    _patch_retrieve(
        monkeypatch,
        [{"text": "context", "source": "manual.pdf", "page": 3, "distance": 0.1}],
    )

    response = TestClient(api.app).post(
        "/ask/stream", json={"question": "时间常数是什么"}
    )
    events = _json_events(response.text)

    assert events[-1] == {"type": "error", "error": "LLM generation failed."}
    assert _stream_data(response.text)[-1] == "[DONE]"
