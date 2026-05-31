from fastapi.testclient import TestClient
import pytest

import api


class FakeStore:
    def query(self, question, k):
        return [
            {
                "text": "context",
                "source": "manual.md",
                "distance": 0.1,
            }
        ]


@pytest.fixture(autouse=True)
def _patch_search(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "_API_KEYS", {})
    monkeypatch.setattr(api, "_API_KEYS_CONFIG_INVALID", False)
    monkeypatch.setattr(api, "_search_cache", None)
    monkeypatch.setattr(api, "_search_cache_fingerprint", None)
    monkeypatch.setattr(api, "_KNOWLEDGE_GAPS_PATH", str(tmp_path / "knowledge_gaps.jsonl"))
    monkeypatch.setattr(
        api,
        "_get_search_system",
        lambda kb_name="default": (FakeStore(), None, None, None, None, None),
    )


def test_no_auth_when_key_not_configured(monkeypatch):
    monkeypatch.setattr(api, "_API_KEY", "")

    response = TestClient(api.app).post("/search", json={"question": "test"})

    assert response.status_code == 200


def test_multi_user_key_accepted(monkeypatch):
    monkeypatch.setattr(api, "_API_KEY", "")
    monkeypatch.setattr(
        api,
        "_API_KEYS",
        {"alice": "alice-secret-123", "bob": "bob-secret-123"},
    )

    response = TestClient(api.app).post(
        "/search",
        headers={"X-API-Key": "alice-secret-123"},
        json={"question": "test"},
    )

    assert response.status_code == 200


def test_multi_user_missing_key_rejected(monkeypatch):
    monkeypatch.setattr(api, "_API_KEY", "")
    monkeypatch.setattr(
        api,
        "_API_KEYS",
        {"alice": "alice-secret-123", "bob": "bob-secret-123"},
    )

    response = TestClient(api.app).get("/index/status")

    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid or missing API key."}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/cache/stats"),
        ("POST", "/cache/clear"),
        ("GET", "/index/status"),
        ("GET", "/sessions/stats"),
        ("GET", "/knowledge-bases"),
    ],
)
def test_multi_user_key_allows_management_endpoints(monkeypatch, method, path):
    monkeypatch.setattr(api, "_API_KEY", "")
    monkeypatch.setattr(api, "_API_KEYS", {"alice": "alice-secret-123"})
    client = TestClient(api.app)
    headers = {"X-API-Key": "alice-secret-123"}

    if method == "GET":
        response = client.get(path, headers=headers)
    elif method == "POST":
        response = client.post(path, headers=headers)
    else:
        raise AssertionError(f"Unsupported method: {method}")

    assert response.status_code == 200


def test_valid_key_accepted(monkeypatch):
    monkeypatch.setattr(api, "_API_KEY", "test-secret-123")

    response = TestClient(api.app).post(
        "/search",
        headers={"X-API-Key": "test-secret-123"},
        json={"question": "test"},
    )

    assert response.status_code == 200


def test_invalid_key_rejected_with_403(monkeypatch):
    monkeypatch.setattr(api, "_API_KEY", "test-secret-123")

    response = TestClient(api.app).post(
        "/search",
        headers={"X-API-Key": "wrong-key"},
        json={"question": "test"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid or missing API key."}


def test_missing_key_header_rejected_with_403(monkeypatch):
    monkeypatch.setattr(api, "_API_KEY", "test-secret-123")

    response = TestClient(api.app).post("/search", json={"question": "test"})

    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid or missing API key."}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/cache/clear"),
        ("DELETE", "/session/test-session-123"),
        ("GET", "/session/test-session-123/history"),
        ("GET", "/sessions/stats"),
        ("GET", "/cache/stats"),
        ("GET", "/index/status"),
        ("GET", "/knowledge-bases"),
    ],
)
def test_management_endpoints_protected_when_key_configured(monkeypatch, method, path):
    monkeypatch.setattr(api, "_API_KEY", "test-secret-123")
    client = TestClient(api.app)

    if method == "GET":
        response = client.get(path)
    elif method == "POST":
        response = client.post(path)
    elif method == "DELETE":
        response = client.delete(path)
    else:
        raise AssertionError(f"Unsupported method: {method}")

    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid or missing API key."}


def test_health_check_not_protected(monkeypatch):
    monkeypatch.setattr(api, "_API_KEY", "test-secret-123")

    response = TestClient(api.app).get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
