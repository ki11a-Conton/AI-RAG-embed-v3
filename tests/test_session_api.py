from fastapi.testclient import TestClient
import pytest

import api
from lib.session_store import SessionStore


class FakeLlm:
    def __init__(self, stream_tokens=None, fail_stream=False):
        self.stream_tokens = stream_tokens or ["hello", " world"]
        self.fail_stream = fail_stream

    def generate(self, messages):
        return "answer"

    def generate_stream(self, messages):
        if self.fail_stream:
            raise RuntimeError("stream failed")
        yield from self.stream_tokens


@pytest.fixture
def session_store(monkeypatch):
    store = SessionStore(ttl_seconds=3600, max_sessions=10)
    monkeypatch.setattr(api, "_session_store", store)
    return store


@pytest.fixture(autouse=True)
def _patch_system(monkeypatch):
    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (object(), None, FakeLlm(), None, None, "system", None, None),
    )


def _patch_retrieve(monkeypatch, captured, chunks=None):
    chunks = chunks if chunks is not None else [
        {"text": "context", "source": "manual.pdf", "page": 1, "distance": 0.1}
    ]

    def fake_retrieve_context(**kwargs):
        captured.update(kwargs)
        return chunks, [{"role": "user", "content": kwargs["question"]}], "rewritten"

    monkeypatch.setattr(api, "_retrieve_context", fake_retrieve_context)


def test_ask_session_uses_stored_history_and_appends(monkeypatch, session_store):
    captured = {}
    _patch_retrieve(monkeypatch, captured)
    session_store.append_turn("sid", "previous", "previous answer")

    response = TestClient(api.app).post(
        "/ask",
        json={
            "question": "follow up",
            "session_id": "sid",
            "history": [{"role": "user", "content": "ignored"}],
        },
    )

    assert response.status_code == 200
    assert captured["messages_history"] == [
        {"role": "user", "content": "previous"},
        {"role": "assistant", "content": "previous answer"},
    ]
    assert session_store.get_history("sid")[-2:] == [
        {"role": "user", "content": "follow up"},
        {"role": "assistant", "content": "answer"},
    ]


def test_ask_without_session_keeps_request_history(monkeypatch, session_store):
    captured = {}
    _patch_retrieve(monkeypatch, captured)

    response = TestClient(api.app).post(
        "/ask",
        json={
            "question": "follow up",
            "history": [{"role": "user", "content": "provided"}],
        },
    )

    assert response.status_code == 200
    assert captured["messages_history"] == [{"role": "user", "content": "provided"}]
    assert session_store.session_count() == 0


def test_session_management_endpoints(session_store):
    session_store.append_turn("sid", "question", "answer")
    client = TestClient(api.app)

    history_response = client.get("/session/sid/history")
    assert history_response.status_code == 200
    assert history_response.json() == {
        "session_id": "sid",
        "kb_name": "default",
        "turns": 1,
        "history": [
            {"role": "user", "content": "question"},
            {"role": "assistant", "content": "answer"},
        ],
    }

    assert client.get("/sessions/stats").json() == {"active_sessions": 1}
    assert client.delete("/session/sid").json() == {
        "session_id": "sid",
        "cleared": True,
    }
    assert client.get("/session/sid/history").json()["history"] == []


def test_stream_session_appends_completed_answer(monkeypatch, session_store):
    captured = {}
    _patch_retrieve(monkeypatch, captured)

    response = TestClient(api.app).post(
        "/ask/stream",
        json={"question": "stream this", "session_id": "sid"},
    )

    assert response.status_code == 200
    assert session_store.get_history("sid")[-2:] == [
        {"role": "user", "content": "stream this"},
        {"role": "assistant", "content": "hello world"},
    ]


def test_stream_session_does_not_append_failed_generation(monkeypatch, session_store):
    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (
            object(),
            None,
            FakeLlm(fail_stream=True),
            None,
            None,
            "system",
            None,
            None,
        ),
    )
    captured = {}
    _patch_retrieve(monkeypatch, captured)

    response = TestClient(api.app).post(
        "/ask/stream",
        json={"question": "stream this", "session_id": "sid"},
    )

    assert response.status_code == 200
    assert session_store.get_history("sid") == []


def test_sessions_are_isolated_by_kb_name(monkeypatch, session_store):
    captured = {}

    def fake_get_system(kb_name="default"):
        return object(), None, FakeLlm(stream_tokens=[f"{kb_name} answer"]), None, None, "system", None, None

    def fake_retrieve_context(**kwargs):
        captured.setdefault("histories", []).append(kwargs["messages_history"])
        return [
            {"text": "context", "source": "manual.pdf", "page": 1, "distance": 0.1}
        ], [{"role": "user", "content": kwargs["question"]}], "rewritten"

    monkeypatch.setattr(api, "_get_system", fake_get_system)
    monkeypatch.setattr(api, "_retrieve_context", fake_retrieve_context)

    client = TestClient(api.app)

    default_response = client.post(
        "/ask",
        json={"question": "default question", "session_id": "sid"},
    )
    project_response = client.post(
        "/ask",
        json={
            "question": "project question",
            "session_id": "sid",
            "kb_name": "project_a",
        },
    )
    followup_response = client.post(
        "/ask",
        json={
            "question": "project followup",
            "session_id": "sid",
            "kb_name": "project_a",
        },
    )

    assert default_response.status_code == 200
    assert project_response.status_code == 200
    assert followup_response.status_code == 200
    assert captured["histories"] == [
        None,
        None,
        [
            {"role": "user", "content": "project question"},
            {"role": "assistant", "content": "answer"},
        ],
    ]

    default_history = client.get("/session/sid/history").json()
    project_history = client.get("/session/sid/history?kb_name=project_a").json()

    assert default_history["kb_name"] == "default"
    assert [item["content"] for item in default_history["history"]] == [
        "default question",
        "answer",
    ]
    assert project_history["kb_name"] == "project_a"
    assert [item["content"] for item in project_history["history"]] == [
        "project question",
        "answer",
        "project followup",
        "answer",
    ]


def test_sessions_are_isolated_by_authenticated_user(monkeypatch, session_store):
    captured = {}
    monkeypatch.setattr(api, "_API_KEY", "")
    monkeypatch.setattr(
        api,
        "_API_KEYS",
        {"alice": "alice-secret-123", "bob": "bob-secret-123"},
    )
    monkeypatch.setattr(api, "_API_KEYS_CONFIG_INVALID", False)

    def fake_retrieve_context(**kwargs):
        captured.setdefault("histories", []).append(kwargs["messages_history"])
        return [
            {"text": "context", "source": "manual.pdf", "page": 1, "distance": 0.1}
        ], [{"role": "user", "content": kwargs["question"]}], "rewritten"

    monkeypatch.setattr(api, "_retrieve_context", fake_retrieve_context)
    client = TestClient(api.app)

    alice_headers = {"X-API-Key": "alice-secret-123"}
    bob_headers = {"X-API-Key": "bob-secret-123"}

    assert client.post(
        "/ask",
        headers=alice_headers,
        json={"question": "alice first", "session_id": "sid"},
    ).status_code == 200
    assert client.post(
        "/ask",
        headers=bob_headers,
        json={"question": "bob first", "session_id": "sid"},
    ).status_code == 200
    assert client.post(
        "/ask",
        headers=alice_headers,
        json={"question": "alice followup", "session_id": "sid"},
    ).status_code == 200

    assert captured["histories"] == [
        None,
        None,
        [
            {"role": "user", "content": "alice first"},
            {"role": "assistant", "content": "answer"},
        ],
    ]

    alice_history = client.get(
        "/session/sid/history", headers=alice_headers
    ).json()["history"]
    bob_history = client.get(
        "/session/sid/history", headers=bob_headers
    ).json()["history"]

    assert [item["content"] for item in alice_history] == [
        "alice first",
        "answer",
        "alice followup",
        "answer",
    ]
    assert [item["content"] for item in bob_history] == [
        "bob first",
        "answer",
    ]


def test_delete_session_only_clears_requested_kb_history(session_store):
    session_store.append_turn("sid", "default question", "default answer")
    session_store.append_turn(
        api._session_store_key("project_a", "sid"),
        "project question",
        "project answer",
    )

    client = TestClient(api.app)
    response = client.delete("/session/sid?kb_name=project_a")

    assert response.status_code == 200
    assert response.json() == {"session_id": "sid", "cleared": True}
    assert client.get("/session/sid/history?kb_name=project_a").json()["history"] == []
    assert client.get("/session/sid/history").json()["history"] == [
        {"role": "user", "content": "default question"},
        {"role": "assistant", "content": "default answer"},
    ]
