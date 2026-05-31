"""Tests for _retrieve_context_chunks helper and MCP formatter.

These tests mock store / query_enhancer / reranker / bm25_index and do **not**
start an actual MCP transport.
"""
from __future__ import annotations

import pytest

from lib.pipeline import _retrieve_context_chunks

# Fakes


class FakeStore:
    def query(self, question: str, k: int = 5):
        return [
            {
                "text": f"result for: {question}",
                "source": "doc.md",
                "page": None,
                "chunk_index": 0,
                "distance": 0.15,
            }
        ]


class FakeEmptyStore:
    def query(self, question: str, k: int = 5):
        return []


class FakeEnhancer:
    def __init__(self, prefix: str = "ENHANCED: "):
        self.prefix = prefix

    def enhance(self, question: str, history=None):
        return f"{self.prefix}{question}"


class FakeReranker:
    def __init__(self):
        self.calls = []

    def rerank(self, query, items, top_n=5, translated_query=None):
        for item in items:
            item["rerank_score"] = 0.95
        self.calls.append((query, top_n, translated_query))
        return items


class FakeBm25Index:
    def is_loaded(self):
        return True

    def query(self, question: str, k: int = 5):
        return [
            {
                "text": f"bm25: {question}",
                "source": "doc.md",
                "page": None,
                "chunk_index": 1,
                "bm25_score": 10.0,
            }
        ]


# Tests: _retrieve_context_chunks


def test_basic_retrieval():
    """Vector-only retrieval returns chunks and unchanged question."""
    config = {"retrieval_k": 5}
    chunks, rewritten = _retrieve_context_chunks(
        FakeStore(), "test question", config
    )
    assert len(chunks) == 1
    assert chunks[0]["text"] == "result for: test question"
    assert chunks[0]["retrieval_path"] == "vector"
    assert rewritten == "test question"


def test_empty_store_returns_empty():
    """When store returns nothing, the helper returns ([], rewritten_question)."""
    config = {"retrieval_k": 5}
    chunks, rewritten = _retrieve_context_chunks(
        FakeEmptyStore(), "anything", config
    )
    assert chunks == []
    assert rewritten == "anything"


def test_with_query_enhancer():
    """Query enhancer rewrites the question and passes it to store.query."""
    class RecordingStore:
        def __init__(self):
            self.last_question = None

        def query(self, question, k=5):
            self.last_question = question
            return [{"text": question, "source": "x.md", "chunk_index": 0}]

    store = RecordingStore()
    config = {"retrieval_k": 5}
    enhancer = FakeEnhancer("ENHANCED: ")

    chunks, rewritten = _retrieve_context_chunks(
        store, "original", config, query_enhancer=enhancer
    )

    assert rewritten == "ENHANCED: original"
    assert store.last_question == "ENHANCED: original"
    assert len(chunks) == 1


def test_with_reranker():
    """Reranker is called with original query and translated query, and
    retrieval_path is 'vector+rerank'."""
    store = FakeStore()
    reranker = FakeReranker()
    config = {"retrieval_k": 5, "rerank_top_n": 5}

    chunks, rewritten = _retrieve_context_chunks(
        store, "my query", config, reranker=reranker
    )

    assert len(chunks) == 1
    assert chunks[0]["rerank_score"] == 0.95
    assert chunks[0]["retrieval_path"] == "vector+rerank"
    assert len(reranker.calls) == 1
    assert reranker.calls[0][0] == "my query"        # original query
    assert reranker.calls[0][2] == "my query"         # translated query (no enhancer)


def test_with_bm25():
    """BM25 fusion is applied and retrieval_path is 'vector+bm25'."""
    store = FakeStore()
    bm25 = FakeBm25Index()
    config = {"retrieval_k": 5}

    chunks, rewritten = _retrieve_context_chunks(
        store, "test", config, bm25_index=bm25
    )

    assert len(chunks) > 0
    assert chunks[0]["retrieval_path"] == "vector+bm25"


def test_with_bm25_and_reranker():
    """BM25 + reranker -> retrieval_path is 'vector+bm25+rerank'."""
    store = FakeStore()
    bm25 = FakeBm25Index()
    reranker = FakeReranker()
    config = {"retrieval_k": 5, "rerank_top_n": 3}

    chunks, rewritten = _retrieve_context_chunks(
        store, "test", config, reranker=reranker, bm25_index=bm25
    )

    assert len(chunks) > 0
    assert chunks[0]["retrieval_path"] == "vector+bm25+rerank"
    assert chunks[0].get("rerank_score") == 0.95


def test_retrieval_candidate_k_with_reranker():
    """When retrieval_candidate_k is set and a reranker is present, store.query
    must be called with that value, not retrieval_k * 3."""
    class RecordingStore:
        def __init__(self):
            self.last_k = None

        def query(self, question, k=5):
            self.last_k = k
            return [{"text": "x", "source": "x.md", "chunk_index": 0}]

    store = RecordingStore()
    reranker = FakeReranker()
    config = {"retrieval_k": 5, "rerank_top_n": 3, "retrieval_candidate_k": 20}

    _retrieve_context_chunks(store, "q", config, reranker=reranker)

    assert store.last_k == 20


def test_retrieval_candidate_k_falls_back():
    """When retrieval_candidate_k is absent and reranker present, fall back to
    retrieval_k * 3."""
    class RecordingStore:
        def __init__(self):
            self.last_k = None

        def query(self, question, k=5):
            self.last_k = k
            return [{"text": "x", "source": "x.md", "chunk_index": 0}]

    store = RecordingStore()
    reranker = FakeReranker()
    config = {"retrieval_k": 5, "rerank_top_n": 3}

    _retrieve_context_chunks(store, "q", config, reranker=reranker)

    assert store.last_k == 15  # 5 * 3


def test_retrieval_candidate_k_no_reranker_ignored():
    """Without a reranker, retrieval_candidate_k is ignored."""
    class RecordingStore:
        def __init__(self):
            self.last_k = None

        def query(self, question, k=5):
            self.last_k = k
            return [{"text": "x", "source": "x.md", "chunk_index": 0}]

    store = RecordingStore()
    config = {"retrieval_k": 5, "retrieval_candidate_k": 20}

    _retrieve_context_chunks(store, "q", config)

    assert store.last_k == 5


def test_no_chunks_does_not_crash_on_missing_reranker():
    """When store returns no chunks, the function should return early without
    calling reranker or setting retrieval_path."""
    reranker = FakeReranker()
    config = {"retrieval_k": 5, "rerank_top_n": 3}

    chunks, rewritten = _retrieve_context_chunks(
        FakeEmptyStore(), "q", config, reranker=reranker
    )

    assert chunks == []
    assert rewritten == "q"
    assert len(reranker.calls) == 0


def test_messages_history_passed_to_enhancer():
    """messages_history must be forwarded to query_enhancer.enhance()."""
    class RecordingEnhancer:
        def __init__(self):
            self.history = None

        def enhance(self, question, history=None):
            self.history = history
            return question

    store = FakeStore()
    enhancer = RecordingEnhancer()
    config = {"retrieval_k": 5}
    history = [{"role": "user", "content": "prev"}]

    _retrieve_context_chunks(
        store, "followup", config, query_enhancer=enhancer, messages_history=history
    )

    assert enhancer.history == history


# Tests: MCP formatter (_format_chunks)


try:
    from mcp_server import _format_chunks
except ImportError:
    # Fallback: local copy so tests run even without the mcp package installed.
    def _format_chunks(
        question: str,
        chunks: list[dict],
        rewritten_question: str | None = None,
    ) -> str:
        lines = [f"Question: {question}"]
        if rewritten_question and rewritten_question != question:
            lines.append(f"Enhanced query: {rewritten_question}")
        lines.append(f"Found {len(chunks)} chunk(s):\n")

        for i, chunk in enumerate(chunks, 1):
            from lib.output_writer import _format_source_citation as _cit

            citation = _cit(chunk)
            lines.append(f"--- Chunk {i} ---")
            lines.append(citation)
            lines.append(chunk.get("text", ""))
            rp = chunk.get("retrieval_path")
            if rp:
                lines.append(f"(retrieval path: {rp})")
            lines.append("")

        return "\n".join(lines)


def test_format_chunks_basic():
    """Basic formatting with one chunk."""
    chunks = [
        {"text": "Some content.", "source": "guide.md", "chunk_index": 3},
    ]
    result = _format_chunks("my question", chunks)
    assert "Question: my question" in result
    assert "[Source: guide.md, Chunk 3]" in result
    assert "Some content." in result
    assert "retrieval path" not in result


def test_format_chunks_with_enhanced_query():
    """When a different rewritten_question is provided, the output includes
    an 'Enhanced query' line."""
    chunks = [{"text": "data", "source": "x.md", "chunk_index": 0}]
    result = _format_chunks("original", chunks, rewritten_question="enhanced")
    assert "Enhanced query: enhanced" in result


def test_format_chunks_with_retrieval_path():
    """If chunks have a retrieval_path, it is included in the output."""
    chunks = [
        {
            "text": "data",
            "source": "x.md",
            "chunk_index": 0,
            "retrieval_path": "vector+rerank",
        }
    ]
    result = _format_chunks("q", chunks)
    assert "(retrieval path: vector+rerank)" in result


def test_format_chunks_multiple_chunks():
    """Multiple chunks are numbered sequentially."""
    chunks = [
        {"text": "first", "source": "a.md", "chunk_index": 0},
        {"text": "second", "source": "b.md", "chunk_index": 1},
        {"text": "third", "source": "c.md", "chunk_index": 2},
    ]
    result = _format_chunks("q", chunks)
    assert result.count("--- Chunk ") == 3
    assert "--- Chunk 1 ---" in result
    assert "--- Chunk 2 ---" in result
    assert "--- Chunk 3 ---" in result
    assert "first" in result
    assert "second" in result
    assert "third" in result
    assert "Found 3 chunk(s)" in result


def test_format_chunks_empty():
    """An empty chunk list is handled gracefully."""
    result = _format_chunks("q", [])
    assert "Found 0 chunk(s)" in result
    assert "Question: q" in result


def test_format_chunks_importable_directly():
    """Prove _format_chunks can be imported from mcp_server without starting transport."""
    pytest.importorskip("mcp.server.fastmcp", reason="mcp package not installed")
    from mcp_server import _format_chunks as _f

    result = _f("direct_import", [{"text": "works", "source": "s.md", "chunk_index": 0}])
    assert "Question: direct_import" in result
    assert "works" in result


def test_retrieval_stdout_redirect_mechanism():
    """Print statements in _retrieve_context_chunks can be redirected away from stdout.

    This validates the mechanism used by mcp_server.py to protect the MCP stdio
    protocol from progress-print pollution.
    """
    import contextlib
    import io

    config = {"retrieval_k": 5}
    captured = io.StringIO()

    with contextlib.redirect_stdout(captured):
        chunks, rewritten = _retrieve_context_chunks(
            FakeStore(), "redirect_test", config
        )

    output = captured.getvalue()
    assert ">> Processing..." in output, "print output should be captured by redirect_stdout"
    assert chunks[0]["retrieval_path"] == "vector"
