"""
tests/test_bm25.py
Unit tests for BM25Index in lib/bm25_index.py.
"""
import os
import sys
import tempfile

import pytest

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

from lib.bm25_index import BM25Index, _tokenize


# ── helpers ────────────────────────────────────────────

def _make_chunk(source: str, text: str, page: int = 1,
                chunk_index: int = 0, file_type: str = "md") -> dict:
    return {
        "metadata": {
            "source": source,
            "file_type": file_type,
            "chunk_index": chunk_index,
            "page": page,
        },
        "text": text,
    }


_MOCK_CHUNKS = [
    _make_chunk("intro.md", "This document introduces forecasting methods.", page=1),
    _make_chunk("ch1.md", "Chapter one covers time series graphics and plots.", page=2),
    _make_chunk("ch2.md", "Chapter two discusses decomposition of time series.", page=3),
    _make_chunk("appendix.md", "The appendix provides mathematical proofs and references.", page=10),
]

_MOCK_CHUNKS_CN = [
    _make_chunk("cn_intro.md", "时间序列分析是预测方法的核心组成部分。", page=1, file_type="md"),
    _make_chunk("cn_ch1.md", "本章介绍了时间序列分解与图形可视化技术。", page=2, file_type="md"),
    _make_chunk("cn_ml.md", "机器学习在时间序列预测中的应用越来越广泛。", page=3, file_type="md"),
]


# ── tokenizer ──────────────────────────────────────────

def test_tokenize_lower_split():
    tokens = _tokenize("Hello World! This is BM25.")
    assert "hello" in tokens
    assert "world" in tokens
    assert "this" in tokens
    assert "is" in tokens
    assert "bm25" in tokens
    assert "!" not in str(tokens)


def test_tokenize_numbers_kept():
    tokens = _tokenize("Model V3.1 released in 2024.")
    assert "v3" in tokens
    assert "1" in tokens  # split tail
    assert "2024" in tokens


def test_tokenize_empty():
    assert _tokenize("") == []
    assert _tokenize("!@#$%") == []


def test_chinese_tokenizer_segmentation():
    """Chinese text should be segmented by jieba into meaningful words."""
    tokens = _tokenize("这是一段中文文本，用于测试分词功能。")
    assert len(tokens) >= 3, f"Expected jieba to segment into multiple tokens, got: {tokens}"
    # common jieba segmentations
    token_set = set(tokens)
    assert any(w in token_set for w in ("中文", "文本", "测试", "分词"))


def test_chinese_tokenizer_mixed_eng_chn():
    """Mixed Chinese-English text should be segmented by jieba."""
    tokens = _tokenize("hello世界, 你好world!")
    assert len(tokens) > 0
    assert "hello" in tokens or "world" in tokens  # jieba may or may not split English
    token_set = set(tokens)
    assert any(w in token_set for w in ("世界", "你好"))


def test_chinese_tokenizer_whitespace_only():
    """Chinese text with only whitespace/punctuation should return empty."""
    tokens = _tokenize("， 。 ！ ？")
    assert tokens == []


# ── build & query ─────────────────────────────────────

class TestBM25Index:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.idx = BM25Index()
        self.idx.build(_MOCK_CHUNKS)

    def test_empty_index_query_returns_empty(self):
        empty = BM25Index()
        assert empty.query("anything") == []
        assert len(empty) == 0
        assert not empty.is_loaded()

    def test_build_empty_chunks_stays_queryable(self):
        empty = BM25Index()
        empty.build([])
        assert empty.query("anything") == []
        assert len(empty) == 0
        assert not empty.is_loaded()

    def test_build_populates_index(self):
        assert len(self.idx) == 4
        assert self.idx.is_loaded()

    def test_query_exact_keywords(self):
        results = self.idx.query("forecasting methods", k=3)
        assert len(results) >= 1
        # first result should be the intro chunk
        top = results[0]
        assert "forecasting" in top["text"].lower()
        assert top["source"] == "intro.md"

    def test_query_returns_bm25_score(self):
        results = self.idx.query("time series", k=2)
        assert len(results) >= 1
        for r in results:
            assert "bm25_score" in r
            assert isinstance(r["bm25_score"], float)
            assert r["bm25_score"] >= 0.0

    def test_query_respects_k(self):
        results = self.idx.query("time series", k=2)
        assert len(results) <= 2

    def test_query_k_zero_returns_empty(self):
        results = self.idx.query("time series", k=0)
        assert results == []

    def test_query_k_negative_returns_empty(self):
        results = self.idx.query("time series", k=-5)
        assert results == []

    def test_query_empty_question_returns_results(self):
        # BM25 with empty tokens returns zero scores for all docs
        results = self.idx.query("", k=2)
        # but we cap at k max; docs may come back with 0.0 score
        assert len(results) <= 2
        for r in results:
            assert r["bm25_score"] == 0.0

    # ── metadata / text preservation ──────────────────

    def test_metadata_preserved(self):
        results = self.idx.query("mathematical proofs", k=1)
        assert len(results) == 1
        r = results[0]
        assert r["source"] == "appendix.md"
        assert r["file_type"] == "md"
        assert r["chunk_index"] == 0
        assert r["page"] == 10

    def test_text_preserved(self):
        results = self.idx.query("time series graphics", k=1)
        assert len(results) == 1
        r = results[0]
        assert "time series graphics" in r["text"].lower()
        assert r["source"] == "ch1.md"

    def test_all_chunk_keys_present(self):
        results = self.idx.query("decomposition", k=1)
        r = results[0]
        for key in ("source", "file_type", "chunk_index", "page", "text", "bm25_score"):
            assert key in r, f"missing key: {key}"

    # ── save / load roundtrip ─────────────────────────

    def test_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "bm25_test.pkl")
            self.idx.save(path)
            assert os.path.isfile(path)

            loaded = BM25Index()
            loaded.load(path)

            assert len(loaded) == len(self.idx)
            assert loaded.is_loaded()

            # query should give same top result
            orig = self.idx.query("forecasting methods", k=1)
            rest = loaded.query("forecasting methods", k=1)
            assert len(orig) == len(rest)
            assert orig[0]["source"] == rest[0]["source"]
            assert orig[0]["text"] == rest[0]["text"]
            assert orig[0]["bm25_score"] == pytest.approx(rest[0]["bm25_score"])

    def test_load_before_build_returns_empty(self):
        loaded = BM25Index()
        assert loaded.query("anything") == []
        assert not loaded.is_loaded()
        assert len(loaded) == 0

    def test_delete_by_source(self):
        deleted = self.idx.delete_by_source("ch1.md")

        assert deleted == 1
        assert len(self.idx) == len(_MOCK_CHUNKS) - 1
        sources = [r["source"] for r in self.idx.query("time series graphics", k=10)]
        assert "ch1.md" not in sources

    def test_delete_by_source_until_empty(self):
        idx = BM25Index()
        idx.build([_make_chunk("only.md", "one document")])

        deleted = idx.delete_by_source("only.md")

        assert deleted == 1
        assert len(idx) == 0
        assert not idx.is_loaded()
        assert idx.query("document") == []


# ── Chinese BM25 integration ───────────────────────────

class TestBM25Chinese:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.idx = BM25Index()
        self.idx.build(_MOCK_CHUNKS_CN)

    def test_chinese_query_returns_chinese_chunks(self):
        results = self.idx.query("时间序列分析", k=3)
        assert len(results) >= 1
        # top hit should be cn_intro which mentions 时间序列分析
        sources = [r["source"] for r in results]
        assert "cn_intro.md" in sources[:2], f"Expected cn_intro in top results, got: {sources}"

    def test_chinese_query_returns_bm25_score(self):
        results = self.idx.query("机器学习", k=1)
        assert len(results) == 1
        r = results[0]
        assert "bm25_score" in r
        assert isinstance(r["bm25_score"], float)
        assert r["bm25_score"] >= 0.0

    def test_chinese_index_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "bm25_cn_test.pkl")
            self.idx.save(path)
            assert os.path.isfile(path)

            loaded = BM25Index()
            loaded.load(path)

            assert len(loaded) == len(self.idx)
            assert loaded.is_loaded()

            orig = self.idx.query("时间序列", k=1)
            rest = loaded.query("时间序列", k=1)
            assert len(orig) == len(rest)
            assert orig[0]["source"] == rest[0]["source"]
            assert orig[0]["bm25_score"] == pytest.approx(rest[0]["bm25_score"])

    def test_chinese_k_zero_returns_empty(self):
        assert self.idx.query("时间序列", k=0) == []

    def test_chinese_empty_build_returns_empty(self):
        empty = BM25Index()
        empty.build([])
        assert empty.query("时间序列") == []


# ── add_chunks incremental tests ───────────────────────

class TestBM25AddChunks:
    """Tests for BM25Index.add_chunks — incremental index updates."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.idx = BM25Index()
        self.idx.build([_make_chunk("initial.md", "Initial document about forecasting.", page=1)])

    def test_add_chunks_extends_index(self):
        """Adding chunks should increase len and make new content queryable."""
        assert len(self.idx) == 1

        new = [_make_chunk("extra.md", "Extra document about time series decomposition.", page=2)]
        self.idx.add_chunks(new)

        assert len(self.idx) == 2
        assert self.idx.is_loaded()

        # Query old content still works
        results = self.idx.query("forecasting", k=5)
        assert any(r["source"] == "initial.md" for r in results)

        # Query new content also works
        results = self.idx.query("decomposition", k=5)
        assert any(r["source"] == "extra.md" for r in results)

    def test_add_chunks_persists_across_save_load(self):
        """Chunks added via add_chunks must survive a save/load roundtrip."""
        new = [_make_chunk("extra.md", "Extra document about time series decomposition.", page=2)]
        self.idx.add_chunks(new)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "bm25_add_persist.pkl")
            self.idx.save(path)

            loaded = BM25Index()
            loaded.load(path)

            assert len(loaded) == 2
            assert loaded.is_loaded()

            # Old content
            results = loaded.query("forecasting", k=5)
            assert any(r["source"] == "initial.md" for r in results)

            # New content persisted
            results = loaded.query("decomposition", k=5)
            assert any(r["source"] == "extra.md" for r in results)

    def test_add_chunks_empty_list_noop(self):
        """Adding an empty list should not change the index."""
        self.idx.add_chunks([])
        assert len(self.idx) == 1
        assert self.idx.is_loaded()
        results = self.idx.query("forecasting", k=5)
        assert len(results) >= 1
        assert results[0]["source"] == "initial.md"

    def test_add_chunks_then_build_again_preserves_all(self):
        """Calling build() after add_chunks() should use only the new
        chunks passed to build, replacing the previous state."""
        self.idx.add_chunks([
            _make_chunk("temp.md", "Temporary doc.", page=99),
        ])
        assert len(self.idx) == 2

        # Now rebuild from a fresh list
        self.idx.build([_make_chunk("replaced.md", "Completely replaced index.", page=1)])
        results = self.idx.query("replaced", k=5)
        assert any(r["source"] == "replaced.md" for r in results)
        # Old chunks no longer there
        results = self.idx.query("forecasting", k=5)
        assert not any(r["source"] == "initial.md" for r in results)

    def test_delete_then_add_chunks_cycle(self):
        """Simulate incremental build: delete old source, add new version."""
        # Start with two sources
        idx = BM25Index()
        idx.build([
            _make_chunk("doc.md", "Original content about forecasting.", page=1),
            _make_chunk("other.md", "Other document.", page=1),
        ])
        assert len(idx) == 2

        # "Modify" doc.md: delete old, add new
        deleted = idx.delete_by_source("doc.md")
        assert deleted == 1
        assert len(idx) == 1

        idx.add_chunks([
            _make_chunk("doc.md", "Updated content about time series decomposition.", page=1),
        ])
        assert len(idx) == 2

        # Old content gone
        results = idx.query("forecasting", k=5)
        assert not any(r["source"] == "doc.md" and "forecasting" in r["text"].lower()
                       for r in results), "Old version should be gone"

        # New content present
        results = idx.query("decomposition", k=5)
        assert any(r["source"] == "doc.md" for r in results)

        # Other doc unaffected
        results = idx.query("other", k=5)
        assert any(r["source"] == "other.md" for r in results)
