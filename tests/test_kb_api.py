from fastapi.testclient import TestClient
import pytest

import api


class FakeStore:
    def query(self, question, k):
        return [
            {
                "text": f"matched {question}",
                "source": "kb.md",
                "distance": 0.1,
            }
        ]


class FakeLlm:
    def generate(self, messages):
        return "answer"

    def generate_stream(self, messages):
        yield "answer"


@pytest.fixture(autouse=True)
def _reset_search_cache(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "_search_cache", None)
    monkeypatch.setattr(api, "_search_cache_fingerprint", None)
    monkeypatch.setattr(api, "_KNOWLEDGE_GAPS_PATH", str(tmp_path / "knowledge_gaps.jsonl"))


def test_knowledge_bases_endpoint_returns_registry(monkeypatch):
    monkeypatch.setattr(api, "list_knowledge_bases", lambda: ["default", "project_a"])

    response = TestClient(api.app).get("/knowledge-bases")

    assert response.status_code == 200
    assert response.json() == {"knowledge_bases": ["default", "project_a"]}


def test_search_accepts_kb_name(monkeypatch):
    captured = {}

    def fake_get_search_system(kb_name="default"):
        captured["kb_name"] = kb_name
        return FakeStore(), None, None, None, None, None

    monkeypatch.setattr(api, "_get_search_system", fake_get_search_system)

    response = TestClient(api.app).post(
        "/search",
        json={"question": "time constant", "kb_name": "project_a"},
    )

    assert response.status_code == 200
    assert captured["kb_name"] == "project_a"
    assert response.json()["chunks"][0]["source"] == "kb.md"


def test_ask_accepts_kb_name(monkeypatch):
    captured = {}

    def fake_get_system(kb_name="default"):
        captured["kb_name"] = kb_name
        return object(), None, FakeLlm(), None, None, "system", None, None

    def fake_retrieve_context(**kwargs):
        return [
            {"text": "context", "source": "kb.md", "distance": 0.1}
        ], [{"role": "user", "content": kwargs["question"]}], "rewritten"

    monkeypatch.setattr(api, "_get_system", fake_get_system)
    monkeypatch.setattr(api, "_retrieve_context", fake_retrieve_context)

    response = TestClient(api.app).post(
        "/ask",
        json={"question": "time constant", "kb_name": "project_a"},
    )

    assert response.status_code == 200
    assert captured["kb_name"] == "project_a"
    assert response.json()["answer"] == "answer"


def test_ask_stream_accepts_kb_name(monkeypatch):
    captured = {}

    def fake_get_system(kb_name="default"):
        captured["kb_name"] = kb_name
        return object(), None, FakeLlm(), None, None, "system", None, None

    def fake_retrieve_context(**kwargs):
        return [
            {"text": "context", "source": "kb.md", "distance": 0.1}
        ], [{"role": "user", "content": kwargs["question"]}], "rewritten"

    monkeypatch.setattr(api, "_get_system", fake_get_system)
    monkeypatch.setattr(api, "_retrieve_context", fake_retrieve_context)

    response = TestClient(api.app).post(
        "/ask/stream",
        json={"question": "time constant", "kb_name": "project_a"},
    )

    assert response.status_code == 200
    assert captured["kb_name"] == "project_a"
    assert "data: [DONE]" in response.text


def test_invalid_kb_name_returns_400():
    response = TestClient(api.app).post(
        "/search",
        json={"question": "time constant", "kb_name": "../bad"},
    )

    assert response.status_code == 400
