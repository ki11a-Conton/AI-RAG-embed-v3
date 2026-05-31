"""Tests for hybrid retrieval helpers – RRF fusion."""

import pytest
from lib.hybrid_retriever import reciprocal_rank_fusion


# ── helpers ────────────────────────────────────────────────────

def _v(source, ci, page, text):
    """Create a minimal vector-style chunk."""
    return {"source": source, "chunk_index": ci, "page": page, "text": text, "distance": 0.5}


def _b(source, ci, page, text, bm25=10.0):
    """Create a minimal BM25-style chunk."""
    return {"source": source, "chunk_index": ci, "page": page, "text": text, "bm25_score": bm25}


# ── basic fusion ───────────────────────────────────────────────

def test_rrf_empty_inputs():
    assert reciprocal_rank_fusion([], [], top_n=5) == []


def test_rrf_zero_top_n():
    chunks = [_v("a.md", 0, 1, "hello")]
    assert reciprocal_rank_fusion(chunks, [], top_n=0) == []


def test_rrf_vector_only():
    chunks = [
        _v("a.md", 0, 1, "alpha"),
        _v("b.md", 1, 2, "beta"),
    ]
    result = reciprocal_rank_fusion(chunks, [], top_n=2)
    assert len(result) == 2
    assert result[0]["text"] == "alpha"
    assert result[1]["text"] == "beta"
    # alpha (rank=1) should score higher than beta (rank=2)
    assert result[0]["rrf_score"] > result[1]["rrf_score"]


def test_rrf_bm25_only():
    chunks = [
        _b("a.md", 0, 1, "alpha"),
        _b("b.md", 1, 2, "beta"),
    ]
    result = reciprocal_rank_fusion([], chunks, top_n=2)
    assert len(result) == 2
    assert result[0]["text"] == "alpha"


# ── overlap boosts score ───────────────────────────────────────

def test_rrf_overlap_ranks_higher():
    """A chunk appearing in both lists should outrank a chunk appearing in only one."""
    shared = _v("shared.md", 0, 1, "shared text")
    vec_only = _v("vec.md", 0, 1, "vec only")
    bm25_shared = _b("shared.md", 0, 1, "shared text")
    bm25_only = _b("bm25.md", 0, 1, "bm25 only")

    vec_results = [shared, vec_only]
    bm25_results = [bm25_only, bm25_shared]

    result = reciprocal_rank_fusion(vec_results, bm25_results, top_n=3)
    assert len(result) == 3
    # shared gets score from rank=1 (vector) + rank=2 (BM25)
    # vec_only gets score from rank=2 (vector only)
    # bm25_only gets score from rank=1 (BM25 only)
    scores = {c["text"]: c["rrf_score"] for c in result}
    assert scores["shared text"] > scores["vec only"]
    assert scores["shared text"] > scores["bm25 only"]


def test_rrf_overlap_top_single():
    """With a shared chunk and multiple unique ones, shared should be #1."""
    shared_v = _v("s.md", 0, 1, "shared")
    shared_b = _b("s.md", 0, 1, "shared")
    v2 = _v("v.md", 0, 1, "vector2")
    b2 = _b("b.md", 0, 1, "bm25-2")

    vec = [shared_v, v2]
    bm = [shared_b, b2]
    result = reciprocal_rank_fusion(vec, bm, top_n=3)
    assert result[0]["text"] == "shared"


# ── identity: chunk_index preferred ─────────────────────────────

def test_rrf_identity_by_chunk_index():
    """Chunks with same source+chunk_index are treated as identical even if page differs."""
    v = _v("doc.md", 5, 10, "vector text")
    b = _b("doc.md", 5, 99, "bm25 text")  # different page, same chunk_index
    result = reciprocal_rank_fusion([v], [b], top_n=1)
    assert len(result) == 1
    # score should be from both lists → higher than single-list score
    single = reciprocal_rank_fusion([v], [], top_n=1)[0]["rrf_score"]
    assert result[0]["rrf_score"] > single


# ── identity: page fallback ─────────────────────────────────────

def test_rrf_identity_by_page():
    """When chunk_index is None, (source, page) identifies the chunk."""
    v = _v("doc.md", None, 3, "vector text")
    b = _b("doc.md", None, 3, "bm25 text")
    result = reciprocal_rank_fusion([v], [b], top_n=1)
    assert len(result) == 1
    single = reciprocal_rank_fusion([v], [], top_n=1)[0]["rrf_score"]
    assert result[0]["rrf_score"] > single


# ── identity: text fallback ─────────────────────────────────────

def test_rrf_identity_by_text():
    """When chunk_index and page are both None, (source, text) is the fallback identity."""
    v = {"source": "doc.md", "text": "unique text A", "distance": 0.3}
    b = {"source": "doc.md", "text": "unique text A", "bm25_score": 8.0}
    result = reciprocal_rank_fusion([v], [b], top_n=1)
    assert len(result) == 1
    single = reciprocal_rank_fusion([v], [], top_n=1)[0]["rrf_score"]
    assert result[0]["rrf_score"] > single


def test_rrf_different_text_not_merged():
    """Different text under same source without chunk_index/page are NOT merged."""
    v = {"source": "doc.md", "text": "text A", "distance": 0.3}
    b = {"source": "doc.md", "text": "text B", "bm25_score": 8.0}
    result = reciprocal_rank_fusion([v], [b], top_n=2)
    assert len(result) == 2


# ── rrf_score present on outputs ───────────────────────────────

def test_rrf_score_field_added():
    v = _v("a.md", 0, 1, "hello")
    result = reciprocal_rank_fusion([v], [], top_n=1)
    assert "rrf_score" in result[0]
    assert isinstance(result[0]["rrf_score"], float)
    # original fields preserved
    assert result[0]["source"] == "a.md"
    assert result[0]["distance"] == 0.5


def test_rrf_preserves_bm25_score():
    b = _b("a.md", 0, 1, "hello", bm25=12.5)
    result = reciprocal_rank_fusion([], [b], top_n=1)
    assert result[0]["bm25_score"] == 12.5


# ── k parameter ─────────────────────────────────────────────────

def test_rrf_custom_k():
    """Larger k reduces the score spread between ranks."""
    c1 = _v("a.md", 0, 1, "first")
    c2 = _v("a.md", 1, 1, "second")

    default = reciprocal_rank_fusion([c1, c2], [], top_n=2)  # k=60
    custom = reciprocal_rank_fusion([c1, c2], [], top_n=2, k=10)

    default_diff = default[0]["rrf_score"] - default[1]["rrf_score"]
    custom_diff = custom[0]["rrf_score"] - custom[1]["rrf_score"]
    # Larger k → smaller score difference between adjacent ranks
    assert default_diff < custom_diff


# ── chunk copy is independent ───────────────────────────────────

def test_rrf_result_is_copy():
    original = _v("a.md", 0, 1, "hello")
    result = reciprocal_rank_fusion([original], [], top_n=1)
    assert result[0] is not original
    result[0]["extra"] = "mutated"
    assert "extra" not in original


# ── top_n clamp ─────────────────────────────────────────────────

def test_rrf_top_n_larger_than_available():
    """top_n > available chunks returns all chunks."""
    chunks = [_v("a.md", i, 1, f"chunk{i}") for i in range(3)]
    result = reciprocal_rank_fusion(chunks, [], top_n=10)
    assert len(result) == 3


@pytest.mark.parametrize("top_n", [-1, -5])
def test_rrf_negative_top_n_returns_empty(top_n):
    chunks = [_v("a.md", 0, 1, "hello")]
    assert reciprocal_rank_fusion(chunks, [], top_n=top_n) == []
