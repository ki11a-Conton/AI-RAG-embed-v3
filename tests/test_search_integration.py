"""Integration test: /search with a real VectorDb and fake embeddings.

Uses a bag-of-words embedding over a small fixed vocabulary so that
related texts produce similar vectors and retrieval order is deterministic.
"""

import pytest
from fastapi.testclient import TestClient

import api
from lib.vector_db import VectorDb


class FakeEmbedEngine:
    """Deterministic bag-of-words embedder over a fixed vocabulary."""

    VOCAB = [
        "time",
        "constant",
        "rc",
        "capacitor",
        "pasta",
        "carbonara",
        "souffle",
        "recipe",
    ]

    def get_embedding(self, text):
        lower = text.lower()
        vec = [float(lower.count(token)) for token in self.VOCAB]
        norm = sum(value * value for value in vec) ** 0.5
        if norm:
            vec = [value / norm for value in vec]
        return vec

    def embed_batch(self, texts):
        return [self.get_embedding(text) for text in texts]


@pytest.fixture
def real_store(tmp_path):
    store = VectorDb(
        persist_dir=str(tmp_path / "chroma"),
        embed_engine=FakeEmbedEngine(),
    )

    store.rebuild(
        [
            {
                "text": (
                    "The time constant tau is a parameter characterizing "
                    "the response of a first-order RC circuit."
                ),
                "source": "control_theory.md",
                "page": 5,
                "chunk_index": 0,
            },
            {
                "text": (
                    "In RC circuits, the time constant tau = R x C determines "
                    "the charging rate of the capacitor."
                ),
                "source": "electronics.md",
                "page": 12,
                "chunk_index": 1,
            },
            {
                "text": "Spaghetti carbonara is a classic Italian pasta dish.",
                "source": "cooking.md",
                "page": 3,
                "chunk_index": 0,
            },
        ]
    )
    return store


def test_search_retrieves_from_real_vector_db(monkeypatch, real_store):
    monkeypatch.setattr(api, "_get_search_system", lambda kb_name="default": (real_store, None, None, None, None, None))
    monkeypatch.setitem(api.config, "retrieval_k", 2)
    monkeypatch.setitem(api.config, "search_distance_threshold", None)
    monkeypatch.setitem(api.config, "confidence_low_threshold", 0.5)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "time constant"})

    assert response.status_code == 200
    data = response.json()

    assert data["searched_question"] == "time constant"
    assert data["low_confidence"] is False
    assert data["chunks"]

    top = data["chunks"][0]
    assert "time constant" in top["text"].lower()
    assert top["source"] in {"control_theory.md", "electronics.md"}
