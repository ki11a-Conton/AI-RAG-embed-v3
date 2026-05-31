"""Tests for VectorDb."""

import tempfile

from lib.vector_db import VectorDb


class FakeEmbedEngine:
    """Fake embed engine that records calls and returns dummy embeddings."""
    def __init__(self):
        self.get_embedding_called = False
        self.embed_batch_called = False

    def get_embedding(self, text: str) -> list[float]:
        self.get_embedding_called = True
        return [0.0] * 128

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self.embed_batch_called = True
        return [[0.0] * 128 for _ in texts]


class FakeCollection:
    """Fake Chroma collection that records query calls."""
    def __init__(self, count: int = 5):
        self._count = count
        self.query_called = False

    def count(self) -> int:
        return self._count

    def query(self, **kwargs):
        self.query_called = True
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]],
        }

    def get(self, **kwargs):
        return {"metadatas": []}


class DeletableCollection:
    def __init__(self):
        self.items = {
            "1": {"source": "A"},
            "2": {"source": "A"},
            "3": {"source": "B"},
        }
        self.deleted_ids = []

    def get(self, **kwargs):
        where = kwargs.get("where") or {}
        source = where.get("source")
        ids = [item_id for item_id, meta in self.items.items() if meta["source"] == source]
        return {"ids": ids, "metadatas": [self.items[item_id] for item_id in ids]}

    def delete(self, ids):
        self.deleted_ids.extend(ids)
        for item_id in ids:
            self.items.pop(item_id, None)


def make_vector_db(collection_count: int = 5):
    """Construct a bare VectorDb instance with fake dependencies (no real Chroma)."""
    fake_embed = FakeEmbedEngine()
    fake_collection = FakeCollection(count=collection_count)

    # Bypass __init__ to avoid real Chroma client creation
    db = object.__new__(VectorDb)
    db._embed_engine = fake_embed
    db._collection = fake_collection
    return db, fake_embed, fake_collection


# ── Tests ───────────────────────────────────────────────────────────

class TestQueryInvalidK:
    """query(k) must return [] immediately when k <= 0, without calling downstream."""

    def test_k_zero_returns_empty_list(self):
        db, embed, coll = make_vector_db(collection_count=5)
        result = db.query("some question", k=0)
        assert result == []
        assert not embed.get_embedding_called, "get_embedding should not be called"
        assert not coll.query_called, "collection.query should not be called"

    def test_k_negative_returns_empty_list(self):
        db, embed, coll = make_vector_db(collection_count=5)
        result = db.query("some question", k=-1)
        assert result == []
        assert not embed.get_embedding_called, "get_embedding should not be called"
        assert not coll.query_called, "collection.query should not be called"

    def test_positive_k_still_works(self):
        """Positive k with non-empty collection should proceed normally."""
        db, embed, coll = make_vector_db(collection_count=5)
        result = db.query("some question", k=3)
        assert isinstance(result, list)
        assert embed.get_embedding_called, "get_embedding should be called for k > 0"
        assert coll.query_called, "collection.query should be called for k > 0"

    def test_positive_k_empty_collection_returns_empty(self):
        """k > 0 but empty collection should still return []."""
        db, embed, coll = make_vector_db(collection_count=0)
        result = db.query("some question", k=3)
        assert result == []
        # embed should NOT be called when collection is empty
        assert not embed.get_embedding_called, (
            "get_embedding should not be called on empty collection"
        )
        assert not coll.query_called, (
            "collection.query should not be called on empty collection"
        )


def test_delete_by_source():
    db = object.__new__(VectorDb)
    db._collection = DeletableCollection()

    deleted = db.delete_by_source("A")

    assert deleted == 2
    assert db._collection.deleted_ids == ["1", "2"]
    assert set(db._collection.items) == {"3"}


def test_add_chunks_after_delete_does_not_reuse_ids():
    """Regression: after delete_by_source, add_chunks must use unique IDs
    so that all surviving + new chunks are present in the collection."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        embed = FakeEmbedEngine()
        db = VectorDb(persist_dir=tmpdir, embed_engine=embed)

        # Add initial chunks from two sources
        db.add_chunks([
            {"text": "a1", "metadata": {"source": "srcA", "file_type": "txt", "chunk_index": 0, "page": 1}},
            {"text": "a2", "metadata": {"source": "srcA", "file_type": "txt", "chunk_index": 1, "page": 1}},
            {"text": "b1", "metadata": {"source": "srcB", "file_type": "txt", "chunk_index": 0, "page": 1}},
        ])
        assert db.count() == 3, f"Expected 3 after first add, got {db.count()}"

        # Delete one source
        deleted = db.delete_by_source("srcA")
        assert deleted == 2
        assert db.count() == 1, f"Expected 1 after delete, got {db.count()}"

        # Add new chunks from a third source
        db.add_chunks([
            {"text": "c1", "metadata": {"source": "srcC", "file_type": "txt", "chunk_index": 0, "page": 1}},
            {"text": "c2", "metadata": {"source": "srcC", "file_type": "txt", "chunk_index": 1, "page": 1}},
        ])

        # Final count must be 1 (surviving srcB) + 2 (new srcC) = 3
        assert db.count() == 3, (
            f"Expected 3 (1 surviving + 2 new), got {db.count()}. "
            "This likely means IDs were reused and Chroma silently dropped new chunks."
        )
