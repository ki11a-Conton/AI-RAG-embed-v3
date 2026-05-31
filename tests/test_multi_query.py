"""tests/test_multi_query.py"""
from unittest.mock import MagicMock

from lib.query_enhancer import MultiQueryEnhancer


def test_generate_queries_returns_list():
    """返回值是 list[str]，且第一个是原始问题。"""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "What is RC circuit time constant?\nHow does capacitor charge in RC circuit?\nExplain RC delay response speed"

    enhancer = MultiQueryEnhancer(mock_llm, n_queries=3, docs_lang="en")
    queries = enhancer.generate_queries("How does an RC circuit work?")

    assert isinstance(queries, list)
    assert len(queries) >= 1
    assert queries[0] == "How does an RC circuit work?"


def test_generate_queries_count():
    """返回的查询数量不超过 n+1（含原始问题）。"""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "Query A\nQuery B\nQuery C\nQuery D\nQuery E"

    enhancer = MultiQueryEnhancer(mock_llm, n_queries=3, docs_lang="en")
    queries = enhancer.generate_queries("Original question?")

    assert len(queries) <= 4  # n_queries + 1 (original)


def test_parse_response_strips_numbering():
    """能正确处理 '1. query'、'- query'、'• query' 等格式。"""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "1. First query\n- Second query\n• Third query\n* Fourth query"

    enhancer = MultiQueryEnhancer(mock_llm, n_queries=4, docs_lang="en")
    queries = enhancer.generate_queries("Original?")

    # Should strip numbering prefixes
    for q in queries[1:]:  # skip original
        assert not q.startswith("1.")
        assert not q.startswith("-")
        assert not q.startswith("•")
        assert not q.startswith("*")


def test_fallback_on_llm_failure():
    """LLM 抛异常时，generate_queries 只返回 [question]，不向上抛出。"""
    mock_llm = MagicMock()
    mock_llm.generate.side_effect = RuntimeError("API key invalid")

    enhancer = MultiQueryEnhancer(mock_llm, n_queries=3, docs_lang="en")
    queries = enhancer.generate_queries("Test question?")

    assert queries == ["Test question?"]


def test_label_property():
    """label 属性应返回 'Multi-Query'。"""
    mock_llm = MagicMock()
    enhancer = MultiQueryEnhancer(mock_llm, n_queries=3)
    assert enhancer.label == "Multi-Query"


def test_empty_llm_response_fallback():
    """LLM 返回空字符串时，应只返回原始问题。"""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = ""

    enhancer = MultiQueryEnhancer(mock_llm, n_queries=3, docs_lang="en")
    queries = enhancer.generate_queries("Some question?")

    assert queries == ["Some question?"]


def test_llm_response_with_only_original():
    """LLM 返回的内容只有原始问题时，应只返回原始问题。"""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "Some question?"

    enhancer = MultiQueryEnhancer(mock_llm, n_queries=3, docs_lang="en")
    queries = enhancer.generate_queries("Some question?")

    # The original question is filtered out by _parse_response, then added back
    assert queries[0] == "Some question?"


def test_chinese_queries():
    """中文查询应正确处理。"""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "RC电路时间常数是什么？\n电容充电过程\nRC延迟响应速度"

    enhancer = MultiQueryEnhancer(mock_llm, n_queries=3, docs_lang="zh")
    queries = enhancer.generate_queries("RC电路怎么工作？")

    assert isinstance(queries, list)
    assert queries[0] == "RC电路怎么工作？"
    assert len(queries) >= 2


def test_short_queries_filtered():
    """长度 <= 5 的查询应被过滤掉。"""
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "OK\nShort\nA proper search query here"

    enhancer = MultiQueryEnhancer(mock_llm, n_queries=3, docs_lang="en")
    queries = enhancer.generate_queries("Original question here?")

    # "OK" and "Short" should be filtered out (length <= 5)
    for q in queries[1:]:
        assert len(q) > 5


def test_multi_query_retrieves_distinct_chunks_across_variants():
    """Multiple query variants must each contribute distinct chunks; merged
    result must contain chunks from multiple distinct queries."""
    from lib.pipeline import _retrieve_context_chunks

    mock_llm = MagicMock()
    mock_llm.generate.return_value = (
        "What is exponential smoothing?\n"
        "Explain ETS model for time series\n"
        "How does Holt-Winters method work?"
    )
    enhancer = MultiQueryEnhancer(mock_llm, n_queries=3, docs_lang="en")

    # Fake store that returns different chunks per query variant
    class MultiVariantStore:
        def __init__(self):
            self.queries_seen = []

        def query(self, question, k=5):
            self.queries_seen.append(question)
            if "exponential smoothing" in question.lower():
                return [
                    {"text": "Chunk A: exponential smoothing intro", "source": "a.md", "chunk_index": 0},
                ]
            elif "ets model" in question.lower():
                return [
                    {"text": "Chunk B: ETS model details", "source": "b.md", "chunk_index": 1},
                ]
            elif "holt-winters" in question.lower():
                return [
                    {"text": "Chunk C: Holt-Winters method", "source": "c.md", "chunk_index": 2},
                ]
            return []

    store = MultiVariantStore()
    config = {"retrieval_k": 5}

    chunks, _ = _retrieve_context_chunks(
        store, "How does exponential smoothing work?",
        config, multi_query_enhancer=enhancer,
    )

    # All three generated queries + original should have been issued
    assert len(store.queries_seen) >= 3, (
        f"Expected >=3 queries seen, got {len(store.queries_seen)}"
    )

    # Merged result should contain distinct chunks from different variants
    texts = {c["text"] for c in chunks}
    assert len(texts) >= 3, (
        f"Expected >=3 distinct chunks from different queries, got {len(texts)}: {texts}"
    )
    assert "Chunk A: exponential smoothing intro" in texts
    assert "Chunk B: ETS model details" in texts
    assert "Chunk C: Holt-Winters method" in texts
    # Original question must be in the queries list
    has_original = any("How does exponential smoothing work?" in q for q in store.queries_seen)
    assert has_original, "Original question must be one of the queries issued"


def test_multi_query_deduplicates_identical_chunks():
    """When different query variants return the same chunk, it must be deduplicated."""
    from lib.pipeline import _retrieve_context_chunks

    mock_llm = MagicMock()
    mock_llm.generate.return_value = "query A\nquery B"
    enhancer = MultiQueryEnhancer(mock_llm, n_queries=2, docs_lang="en")

    class IdenticalStore:
        def __init__(self):
            self.call_count = 0

        def query(self, question, k=5):
            self.call_count += 1
            return [
                {"text": "Same chunk repeated", "source": "s.md", "chunk_index": 0},
            ]

    store = IdenticalStore()
    config = {"retrieval_k": 5}

    chunks, _ = _retrieve_context_chunks(
        store, "original", config, multi_query_enhancer=enhancer,
    )

    # Multiple queries were issued (original + 2 generated = 3 total)
    assert store.call_count == 3, f"Expected 3 queries, got {store.call_count}"

    # Only one unique chunk after dedup
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Same chunk repeated"


def test_multi_query_with_bm25_applies_rrf_per_query():
    """Multi-query + BM25 applies RRF per query; rrf_score survives into output
    and overlapping chunks rank higher than non-overlapping ones."""
    from lib.pipeline import _retrieve_context_chunks

    mock_llm = MagicMock()
    mock_llm.generate.return_value = "alternative phrasing one\nalternative phrasing two"
    enhancer = MultiQueryEnhancer(mock_llm, n_queries=2, docs_lang="en")

    class Store:
        def __init__(self):
            self.query_count = 0

        def query(self, question, k=5):
            self.query_count += 1
            base = self.query_count * 100
            return [
                {"text": f"vector result {base}", "source": "doc.md",
                 "chunk_index": base, "distance": 0.1},
                {"text": f"vector result {base+1}", "source": "doc.md",
                 "chunk_index": base + 1, "distance": 0.2},
            ]

    class BM25:
        def __init__(self):
            self.query_count = 0

        def is_loaded(self):
            return True

        def query(self, question, k=5):
            self.query_count += 1
            base = self.query_count * 100
            return [
                # Overlaps with vector chunk_index=base (same text, same identity)
                {"text": f"vector result {base}", "source": "doc.md",
                 "chunk_index": base, "bm25_score": 14.0},
                # Unique BM25 chunk
                {"text": f"bm25 result {base+2}", "source": "doc.md",
                 "chunk_index": base + 2, "bm25_score": 10.0},
            ]

    store = Store()
    bm25 = BM25()
    config = {"retrieval_k": 5}

    chunks, _ = _retrieve_context_chunks(
        store, "original question",
        config, multi_query_enhancer=enhancer, bm25_index=bm25,
    )

    # Both vector and BM25 were queried for each of the 3 queries
    assert store.query_count >= 3
    assert bm25.query_count >= 3

    # All chunks must have rrf_score and correct retrieval_path
    for c in chunks:
        assert "rrf_score" in c, f"Missing rrf_score: {c}"
        assert isinstance(c["rrf_score"], float), f"rrf_score not float: {c}"
        assert c["retrieval_path"] == "vector+bm25"

    # Build scores by chunk_index to check RRF ordering.
    # For the first query (self.query_count=1 → base=100):
    #   vector rank=1:  chunk_index=100
    #   vector rank=2:  chunk_index=101
    #   bm25   rank=1:  chunk_index=100  (overlap)
    #   bm25   rank=2:  chunk_index=102
    # RRF: score(100) = 1/(60+1)+1/(60+1) = 2/61 ≈ 0.0328
    #      score(101) = 1/(60+2)         = 1/62 ≈ 0.0161
    #      score(102) = 1/(60+2)         = 1/62 ≈ 0.0161
    scores = {}
    for c in chunks:
        ci = c.get("chunk_index")
        if ci is not None:
            scores[ci] = c["rrf_score"]

    # Overlapping chunk (100) must outrank both the vector-only (101) and
    # BM25-only (102) chunks from the same query.
    assert 100 in scores, f"Expected chunk_index=100 in scores: {scores}"
    assert 101 in scores, f"Expected chunk_index=101 in scores: {scores}"
    assert 102 in scores, f"Expected chunk_index=102 in scores: {scores}"
    assert scores[100] > scores[101], (
        f"Overlapping chunk (100, score={scores[100]}) should outrank "
        f"vector-only (101, score={scores[101]})"
    )
    assert scores[100] > scores[102], (
        f"Overlapping chunk (100, score={scores[100]}) should outrank "
        f"BM25-only (102, score={scores[102]})"
    )
