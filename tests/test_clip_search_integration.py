from fastapi.testclient import TestClient

import api


class FakeTextStore:
    def query(self, question, k):
        return [
            {
                "text": f"text hit: {question}",
                "source": "doc.md",
                "file_type": "md",
                "page": None,
                "chunk_index": 0,
                "distance": 0.1,
            }
        ]


class FakeImageStore:
    def __init__(self):
        self.calls = []

    def query(self, question, k):
        self.calls.append((question, k))
        return [
            {
                "text": "image hit: flowchart",
                "source": "paper.pdf",
                "file_type": "clip_image",
                "page": 4,
                "image_index": 2,
                "chunk_index": None,
                "distance": 0.05,
                "retrieval_path": "clip_image",
            }
        ]


def test_search_appends_clip_image_hits_when_enabled(monkeypatch):
    image_store = FakeImageStore()

    monkeypatch.setattr(api, "_get_search_system", lambda kb_name="default": (FakeTextStore(), None, None, None, None, None))
    monkeypatch.setattr(api, "_get_clip_search_system", lambda kb_name="default": image_store)
    monkeypatch.setitem(api.config, "clip_image_enabled", True)
    monkeypatch.setitem(api.config, "clip_retrieval_k", 2)
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "show the flowchart"})

    assert response.status_code == 200
    data = response.json()
    assert image_store.calls == [("show the flowchart", 2)]
    assert len(data["chunks"]) == 2
    assert data["chunks"][0]["retrieval_path"] == "vector"
    assert data["chunks"][1]["retrieval_path"] == "clip_image"
    assert data["chunks"][1]["file_type"] == "clip_image"
    assert data["chunks"][1]["image_index"] == 2


def test_search_does_not_touch_clip_when_disabled(monkeypatch):
    def fail_clip(kb_name="default"):
        raise AssertionError("clip search should not run when disabled")

    monkeypatch.setattr(api, "_get_search_system", lambda kb_name="default": (FakeTextStore(), None, None, None, None, None))
    monkeypatch.setattr(api, "_get_clip_search_system", fail_clip)
    monkeypatch.setitem(api.config, "clip_image_enabled", False)
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "plain text search"})

    assert response.status_code == 200
    data = response.json()
    assert len(data["chunks"]) == 1
    assert data["chunks"][0]["retrieval_path"] == "vector"
