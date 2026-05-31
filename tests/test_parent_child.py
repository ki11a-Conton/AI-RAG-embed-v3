"""tests/test_parent_child.py"""
import os
import tempfile

from lib.doc_loader import load_documents, split_text_by_paragraphs


class _FakeParentStore:
    """In-memory mock of ParentStore for testing without ChromaDB network calls."""

    def __init__(self):
        self._docs: dict[str, dict] = {}  # id -> {"text": ..., "metadata": ...}
        self._counter = 0

    def rebuild(self, parent_chunks):
        self._docs.clear()
        self._counter = 0
        if parent_chunks:
            self.add_chunks(parent_chunks)

    def add_chunks(self, parent_chunks):
        for chunk in parent_chunks:
            self._counter += 1
            doc_id = f"doc_{self._counter}"
            meta = chunk.get("metadata", {})
            self._docs[doc_id] = {
                "text": chunk["text"],
                "metadata": {
                    "source": meta.get("source", "unknown"),
                    "file_type": meta.get("file_type", "unknown"),
                    "chunk_index": meta.get("chunk_index", 0),
                    "page": meta.get("page"),
                    "chunk_role": meta.get("chunk_role", "parent"),
                    "parent_id": meta.get("parent_id", ""),
                },
            }

    def get_by_parent_ids(self, parent_ids):
        if not parent_ids:
            return []
        id_set = set(parent_ids)
        results = []
        for doc in self._docs.values():
            if doc["metadata"].get("parent_id") in id_set:
                results.append(dict(doc))
        return results

    def delete_by_source(self, source):
        to_delete = [k for k, v in self._docs.items() if v["metadata"].get("source") == source]
        for k in to_delete:
            del self._docs[k]
        return len(to_delete)

    def count(self):
        return len(self._docs)


def _make_parent_store(tmp_path):
    """Create an in-memory ParentStore for testing."""
    return _FakeParentStore()


def test_child_has_parent_id(tmp_path):
    """每个子块都有 parent_id，每个父块也有 parent_id，且 parent_id 能对应上。"""
    txt = tmp_path / "doc.txt"
    txt.write_text(
        "First paragraph with enough content to form a chunk.\n\n"
        "Second paragraph with enough content to form a chunk.\n\n"
        "Third paragraph with enough content to form a chunk.\n\n"
        "Fourth paragraph with enough content to form a chunk.\n",
        encoding="utf-8",
    )

    chunks = load_documents(
        str(tmp_path),
        chunk_size=200,
        chunk_overlap=30,
        parent_chunk_size=800,
    )

    child_chunks = [c for c in chunks if c["metadata"].get("chunk_role") == "child"]
    parent_chunks = [c for c in chunks if c["metadata"].get("chunk_role") == "parent"]

    assert len(child_chunks) > 0, "Should have child chunks"
    assert len(parent_chunks) > 0, "Should have parent chunks"

    # Every child should have a parent_id
    for c in child_chunks:
        assert "parent_id" in c["metadata"], "Child chunk missing parent_id"
        assert c["metadata"]["parent_id"], "Child parent_id should not be empty"

    # Every parent should have a parent_id
    for p in parent_chunks:
        assert "parent_id" in p["metadata"], "Parent chunk missing parent_id"
        assert p["metadata"]["parent_id"], "Parent parent_id should not be empty"

    # Every child's parent_id should match some parent's parent_id
    parent_ids = {p["metadata"]["parent_id"] for p in parent_chunks}
    for c in child_chunks:
        assert c["metadata"]["parent_id"] in parent_ids, (
            f"Child parent_id {c['metadata']['parent_id']} not found in parent chunks"
        )


def test_parent_text_longer_than_child(tmp_path):
    """父块文本长度 >= 子块文本长度。"""
    txt = tmp_path / "doc.txt"
    content = "\n\n".join([f"Paragraph number {i} with some content here." for i in range(20)])
    txt.write_text(content, encoding="utf-8")

    chunks = load_documents(
        str(tmp_path),
        chunk_size=100,
        chunk_overlap=20,
        parent_chunk_size=500,
    )

    child_chunks = [c for c in chunks if c["metadata"].get("chunk_role") == "child"]
    parent_chunks = [c for c in chunks if c["metadata"].get("chunk_role") == "parent"]

    assert len(child_chunks) > 0
    assert len(parent_chunks) > 0

    avg_child_len = sum(len(c["text"]) for c in child_chunks) / len(child_chunks)
    avg_parent_len = sum(len(p["text"]) for p in parent_chunks) / len(parent_chunks)
    assert avg_parent_len >= avg_child_len, (
        f"Average parent length ({avg_parent_len}) should be >= average child length ({avg_child_len})"
    )


def test_parent_store_get_by_ids(tmp_path):
    """ParentStore.get_by_parent_ids() 能正确按 parent_id 返回父块。"""
    store = _make_parent_store(tmp_path)

    parent_chunks = [
        {
            "text": "Parent chunk one text",
            "metadata": {
                "source": "test.txt",
                "file_type": "txt",
                "chunk_index": 0,
                "page": None,
                "chunk_role": "parent",
                "parent_id": "abc123",
            },
        },
        {
            "text": "Parent chunk two text",
            "metadata": {
                "source": "test.txt",
                "file_type": "txt",
                "chunk_index": 1,
                "page": None,
                "chunk_role": "parent",
                "parent_id": "def456",
            },
        },
    ]

    store.rebuild(parent_chunks)
    assert store.count() == 2

    # Get by single ID
    results = store.get_by_parent_ids(["abc123"])
    assert len(results) == 1
    assert results[0]["text"] == "Parent chunk one text"
    assert results[0]["metadata"]["parent_id"] == "abc123"

    # Get by multiple IDs
    results = store.get_by_parent_ids(["abc123", "def456"])
    assert len(results) == 2

    # Get by non-existent ID
    results = store.get_by_parent_ids(["nonexistent"])
    assert len(results) == 0

    # Get by empty list
    results = store.get_by_parent_ids([])
    assert len(results) == 0


def test_parent_store_delete_by_source(tmp_path):
    """ParentStore.delete_by_source() 能正确删除指定 source 的父块。"""
    store = _make_parent_store(tmp_path)

    chunks = [
        {
            "text": "Text from file A",
            "metadata": {
                "source": "a.txt",
                "file_type": "txt",
                "chunk_index": 0,
                "page": None,
                "chunk_role": "parent",
                "parent_id": "aaa",
            },
        },
        {
            "text": "Text from file B",
            "metadata": {
                "source": "b.txt",
                "file_type": "txt",
                "chunk_index": 0,
                "page": None,
                "chunk_role": "parent",
                "parent_id": "bbb",
            },
        },
    ]

    store.rebuild(chunks)
    assert store.count() == 2

    deleted = store.delete_by_source("a.txt")
    assert deleted == 1
    assert store.count() == 1

    # Verify remaining chunk is from file B
    results = store.get_by_parent_ids(["bbb"])
    assert len(results) == 1
    assert results[0]["metadata"]["source"] == "b.txt"


def test_disabled_mode_unchanged(tmp_path):
    """parent_chunk_size=None 时（默认），行为与改动前一致。"""
    txt = tmp_path / "doc.txt"
    txt.write_text("Hello world.\n\nSecond paragraph.", encoding="utf-8")

    chunks = load_documents(str(tmp_path), chunk_size=200, chunk_overlap=20)

    # No chunk_role or parent_id should exist
    for c in chunks:
        assert "chunk_role" not in c["metadata"]
        assert "parent_id" not in c["metadata"]


def test_split_text_by_paragraphs_returns_positions():
    """split_text_by_paragraphs 应返回 (text, char_start) 元组。"""
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    results = split_text_by_paragraphs(text, chunk_size=500, chunk_overlap=50)
    assert len(results) >= 1
    for item in results:
        assert isinstance(item, tuple)
        assert len(item) == 2
        chunk_text, char_start = item
        assert isinstance(chunk_text, str)
        assert isinstance(char_start, int)
        assert char_start >= 0


def test_parent_child_retrieve_context_chunks_replaces_child_with_parent_text():
    """Regression: real VectorDb + ParentStore returns parent text, not child text."""
    from lib.pipeline import _retrieve_context_chunks
    from lib.vector_db import ParentStore, VectorDb

    class FakeEmbedEngine:
        def embed_batch(self, texts):
            return [[1.0, 0.0, 0.0] for _ in texts]

        def get_embedding(self, text):
            return [1.0, 0.0, 0.0]

    child = {
        "text": "child snippet text",
        "metadata": {
            "source": "test.md",
            "file_type": "md",
            "chunk_index": 7,
            "page": None,
            "parent_id": "pid_abc123",
            "chunk_role": "child",
        },
    }
    parent = {
        "text": "PARENT TEXT: This is the full context paragraph.",
        "metadata": {
            "source": "test.md",
            "file_type": "md",
            "chunk_index": 0,
            "page": None,
            "chunk_role": "parent",
            "parent_id": "pid_abc123",
        },
    }

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
        store = VectorDb(tmpdir, FakeEmbedEngine())
        store.rebuild([child])
        parent_store = ParentStore(tmpdir)
        parent_store.rebuild([parent])

        raw = store.query("test question", k=1)
        assert raw[0]["parent_id"] == "pid_abc123"
        assert raw[0]["chunk_role"] == "child"

        chunks, _ = _retrieve_context_chunks(
            store, "test question", {"retrieval_k": 1}, parent_store=parent_store,
        )

        assert len(chunks) == 1
        assert chunks[0]["text"] == "PARENT TEXT: This is the full context paragraph."
        assert chunks[0]["source"] == "test.md"
        assert chunks[0]["parent_id"] == "pid_abc123"
        assert chunks[0]["chunk_role"] == "parent"
        assert chunks[0]["metadata"]["parent_id"] == "pid_abc123"


def test_parent_child_flat_result_replaces_child_with_parent_text():
    """Flat VectorDb-style chunks still work when tested without Chroma."""
    from lib.pipeline import _retrieve_context_chunks

    parent_store = _FakeParentStore()
    parent_store.add_chunks([
        {
            "text": "PARENT TEXT: This is the full context paragraph.",
            "metadata": {
                "source": "test.md",
                "file_type": "md",
                "chunk_index": 0,
                "page": None,
                "chunk_role": "parent",
                "parent_id": "pid_abc123",
            },
        },
    ])

    class FlatStore:
        def query(self, question, k=5):
            return [
                {
                    "text": "child snippet text",
                    "source": "test.md",
                    "file_type": "md",
                    "chunk_index": 7,
                    "page": None,
                    "distance": 0.15,
                    "parent_id": "pid_abc123",
                    "chunk_role": "child",
                }
            ]

    config = {"retrieval_k": 5}
    chunks, _ = _retrieve_context_chunks(
        FlatStore(), "test question", config, parent_store=parent_store,
    )

    assert len(chunks) == 1
    # Must return parent text, not child text
    assert chunks[0]["text"] == "PARENT TEXT: This is the full context paragraph."
    assert chunks[0]["source"] == "test.md"
    assert chunks[0]["parent_id"] == "pid_abc123"
    assert chunks[0]["metadata"]["parent_id"] == "pid_abc123"
    assert chunks[0]["metadata"]["chunk_role"] == "parent"


def test_parent_child_with_nested_metadata_format():
    """Parent-child expansion also works with nested metadata (load_documents format)."""
    from lib.pipeline import _retrieve_context_chunks

    parent_store = _FakeParentStore()
    parent_store.add_chunks([
        {
            "text": "PARENT FULL CONTEXT.",
            "metadata": {
                "source": "doc.md",
                "file_type": "md",
                "chunk_index": 0,
                "page": None,
                "chunk_role": "parent",
                "parent_id": "pid_nested_1",
            },
        },
    ])

    class NestedStore:
        def query(self, question, k=5):
            return [
                {
                    "text": "child fragment",
                    "source": "doc.md",
                    "file_type": "md",
                    "chunk_index": 1,
                    "page": None,
                    "distance": 0.2,
                    "metadata": {
                        "source": "doc.md",
                        "file_type": "md",
                        "chunk_index": 1,
                        "page": None,
                        "parent_id": "pid_nested_1",
                        "chunk_role": "child",
                    },
                }
            ]

    config = {"retrieval_k": 5}
    chunks, _ = _retrieve_context_chunks(
        NestedStore(), "q", config, parent_store=parent_store,
    )

    assert len(chunks) == 1
    assert chunks[0]["text"] == "PARENT FULL CONTEXT."


def test_parent_id_unique_across_pages(tmp_path, monkeypatch):
    """parent_ids are unique when parent_index restarts on each page."""
    fake_pdf = tmp_path / "multipage.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 fake")

    def fake_read_file_pages(filepath, chunk_size=800):
        assert os.path.basename(filepath) == "multipage.pdf"
        return [
            {
                "text": "Page one alpha content.\n\nPage one beta content.",
                "page": 1,
            },
            {
                "text": "Page two alpha content.\n\nPage two beta content.",
                "page": 2,
            },
        ]

    import lib.doc_loader as doc_loader

    monkeypatch.setattr(doc_loader, "read_file_pages", fake_read_file_pages)
    chunks = load_documents(
        str(tmp_path),
        chunk_size=30,
        chunk_overlap=5,
        parent_chunk_size=100,
    )

    parent_chunks = [c for c in chunks if c["metadata"].get("chunk_role") == "parent"]
    child_chunks = [c for c in chunks if c["metadata"].get("chunk_role") == "child"]
    parent_ids = [c["metadata"]["parent_id"] for c in parent_chunks]

    assert {c["metadata"]["page"] for c in parent_chunks} == {1, 2}
    assert len(parent_ids) == len(set(parent_ids))
    assert {c["metadata"]["parent_id"] for c in child_chunks}.issubset(set(parent_ids))
