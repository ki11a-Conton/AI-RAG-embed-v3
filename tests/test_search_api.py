import json

from fastapi.testclient import TestClient
import pytest

import api
import lib.pipeline as pipeline
import rag_runner


@pytest.fixture(autouse=True)
def _isolate_knowledge_gap_log(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "_KNOWLEDGE_GAPS_PATH", str(tmp_path / "knowledge_gaps.jsonl"))


@pytest.fixture(autouse=True)
def _isolate_search_cache(monkeypatch):
    """Reset the module-level cache so every test starts with a fresh cache."""
    monkeypatch.setattr(api, "_search_cache", None)
    monkeypatch.setattr(api, "_search_cache_fingerprint", None)


@pytest.fixture(autouse=True)
def _isolate_optional_config_defaults(monkeypatch):
    """Keep tests independent from config_example.json optional defaults."""
    for key in (
        "confidence_high_threshold",
        "confidence_low_threshold",
        "retrieval_candidate_k",
    ):
        monkeypatch.delitem(api.config, key, raising=False)


class FakeStore:
    def __init__(self, *args, **kwargs):
        pass

    def count(self):
        return 1

    def query(self, question, k):
        return [
            {
                "text": f"matched: {question}",
                "source": "fake.md",
                "page": None,
                "chunk_index": 0,
                "distance": 0.1,
            }
        ]


class FakeEnhancer:
    def enhance(self, question, history=None):
        return "translated question"


def test_search_endpoint_uses_search_system_not_ask_system(monkeypatch):
    def fail_get_system(kb_name="default"):
        raise AssertionError("/search should not initialize the ask system")

    monkeypatch.setattr(api, "_get_system", fail_get_system)
    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (FakeStore(), None, FakeEnhancer(), None, None, None)
    )

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "什么是时间常数"})

    assert response.status_code == 200
    data = response.json()
    assert data["original_question"] == "什么是时间常数"
    assert data["searched_question"] == "translated question"
    assert data["confidence"] == "high"
    assert data["low_confidence"] is False
    assert data["chunks"][0]["text"] == "matched: translated question"


def test_search_endpoint_marks_low_confidence(monkeypatch):
    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (FakeStore(), None, FakeEnhancer(), None, None, None)
    )
    monkeypatch.setitem(api.config, "search_distance_threshold", 0.05)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "什么是时间常数"})

    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == "low"
    assert data["low_confidence"] is True


def test_init_search_system_offline_translate_does_not_create_llm(monkeypatch):
    class FakeEmbedEngine:
        def __init__(self, model_name):
            self.model_name = model_name

    class FailingLlmApi:
        def __init__(self, *args, **kwargs):
            raise AssertionError("search-only init should not create LlmApi")

    monkeypatch.setattr(
        pipeline,
        "_import_lib",
        lambda kb_name="default": (FakeEmbedEngine, FailingLlmApi, FakeStore),
    )

    store, parent_store, query_enhancer, multi_query_enhancer, reranker, bm25_index = rag_runner._init_search_system(
        {
            "embedding_model_name": "fake-embedding",
            "chroma_persist_dir": "./fake_chroma",
            "query_enhance_enabled": True,
            "enhancer_mode": "offline_translate",
            "translator_source_lang": "zh",
            "translator_target_lang": "en",
            "rerank_enabled": False,
        }
    )

    assert isinstance(store, FakeStore)
    assert query_enhancer.__class__.__name__ == "OfflineTranslator"
    assert reranker is None
    assert bm25_index is None  # bm25_enabled defaults to False


def test_search_numeric_string_threshold_works(monkeypatch):
    """search_distance_threshold as a numeric string like '0.05' should be
    coerced to float and compared correctly."""
    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (FakeStore(), None, FakeEnhancer(), None, None, None)
    )
    monkeypatch.setitem(api.config, "search_distance_threshold", "0.05")

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "test"})

    assert response.status_code == 200
    # FakeStore returns distance=0.1; 0.1 > 0.05 → low_confidence=True
    assert response.json()["low_confidence"] is True


def test_search_invalid_string_threshold_is_safe(monkeypatch):
    """search_distance_threshold as an invalid string like 'not-a-number'
    should behave as if no threshold is set and return False."""
    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (FakeStore(), None, FakeEnhancer(), None, None, None)
    )
    monkeypatch.setitem(api.config, "search_distance_threshold", "not-a-number")

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "test"})

    assert response.status_code == 200
    assert response.json()["low_confidence"] is False


def test_openapi_includes_search_response_schema():
    """The /openapi.json should declare SearchResponse under
    components/schemas with the expected fields."""
    client = TestClient(api.app)
    openapi = client.get("/openapi.json").json()

    schemas = openapi.get("components", {}).get("schemas", {})
    search_resp = schemas.get("SearchResponse")
    assert search_resp is not None, "SearchResponse schema missing from openapi.json"

    props = search_resp.get("properties", {})
    assert "original_question" in props
    assert "searched_question" in props
    assert "confidence" in props
    assert "low_confidence" in props
    assert "chunks" in props

    chunks_schema = props["chunks"]
    assert chunks_schema.get("type") == "array"
    # Confirm chunks items reference the ContextChunk schema
    assert "$ref" in chunks_schema.get("items", {})

    # Confirm low_confidence is boolean
    assert props["low_confidence"].get("type") == "boolean"
    # Confirm original_question is string
    assert props["original_question"].get("type") == "string"


def test_search_empty_question_returns_400(monkeypatch):
    """Empty or whitespace-only question should return HTTP 400."""
    monkeypatch.setattr(api, "_get_search_system", lambda kb_name="default": (FakeStore(), None, None, None, None, None))
    client = TestClient(api.app)

    resp = client.post("/search", json={"question": ""})
    assert resp.status_code == 400

    resp = client.post("/search", json={"question": "   "})
    assert resp.status_code == 400


def test_search_empty_store_returns_empty_chunks(monkeypatch):
    """Empty search results should return chunks=[] and confidence=low."""

    class FakeEmptyStore:
        def __init__(self, *args, **kwargs):
            pass

        def count(self):
            return 0

        def query(self, question, k):
            return []

    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (FakeEmptyStore(), None, None, None, None, None)
    )
    client = TestClient(api.app)
    response = client.post("/search", json={"question": "any question"})

    assert response.status_code == 200
    data = response.json()
    assert data["chunks"] == []
    assert data["confidence"] == "low"
    assert data["low_confidence"] is True


def test_search_with_reranker_fetches_more_candidates(monkeypatch):
    """With a reranker, fetch retrieval_k*3 candidates before reranking."""

    class FakeReranker:
        def __init__(self):
            self.calls = []

        def rerank(self, question, chunks, top_n, translated_query=None):
            for chunk in chunks:
                chunk["rerank_score"] = 0.95
            self.calls.append((question, chunks, top_n, translated_query))
            return chunks

    class FakeRecordingStore(FakeStore):
        def __init__(self):
            super().__init__()
            self.last_k = None

        def query(self, question, k):
            self.last_k = k
            return super().query(question, k)

    store = FakeRecordingStore()
    reranker = FakeReranker()

    monkeypatch.setattr(api, "_get_search_system", lambda kb_name="default": (store, None, None, None, reranker, None))
    monkeypatch.setitem(api.config, "retrieval_k", 6)
    monkeypatch.setitem(api.config, "rerank_top_n", 5)
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "reranker test"})

    assert response.status_code == 200
    data = response.json()
    assert len(data["chunks"]) == 1
    assert data["chunks"][0]["text"] == "matched: reranker test"
    assert data["chunks"][0]["rerank_score"] == 0.95

    # The endpoint should have queried the store with k=retrieval_k*3=18
    assert store.last_k == 18

    # The reranker should have been called with the right arguments
    assert len(reranker.calls) == 1
    assert reranker.calls[0][0] == "reranker test"
    assert len(reranker.calls[0][1]) == 1
    assert reranker.calls[0][2] == 5
    # translated_query should be "reranker test" (same as query, no enhancer)
    assert reranker.calls[0][3] == "reranker test"

    # low_confidence should remain False (no threshold set)
    assert data["low_confidence"] is False


def test_search_numeric_string_retrieval_settings_work(monkeypatch):
    class FakeReranker:
        def __init__(self):
            self.top_n = None

        def rerank(self, question, chunks, top_n, translated_query=None):
            self.top_n = top_n
            return chunks

    class FakeRecordingStore(FakeStore):
        def __init__(self):
            super().__init__()
            self.last_k = None

        def query(self, question, k):
            self.last_k = k
            return super().query(question, k)

    store = FakeRecordingStore()
    reranker = FakeReranker()

    monkeypatch.setattr(api, "_get_search_system", lambda kb_name="default": (store, None, None, None, reranker, None))
    monkeypatch.setitem(api.config, "retrieval_k", "6")
    monkeypatch.setitem(api.config, "rerank_top_n", "5")
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "time constant"})

    assert response.status_code == 200
    assert store.last_k == 18
    assert reranker.top_n == 5


def test_ask_llm_failure_returns_502(monkeypatch):
    class FailingLlm:
        def generate(self, messages):
            raise RuntimeError("invalid api key")

    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (FakeStore(), None, FailingLlm(), None, None, "system prompt", None, None),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 1)
    monkeypatch.setitem(api.config, "max_context_chars", 6000)

    client = TestClient(api.app)
    response = client.post("/ask", json={"question": "time constant"})

    assert response.status_code == 502
    assert "LLM generation failed" in response.json()["detail"]


def test_search_init_failure_returns_json_500(monkeypatch):
    def fail_get_search_system(kb_name="default"):
        raise RuntimeError("model load failed")

    monkeypatch.setattr(api, "_get_search_system", fail_get_search_system)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "time constant"})

    assert response.status_code == 500
    assert response.json()["detail"] == "RAG search system initialization failed."


def test_ask_init_failure_returns_json_500(monkeypatch):
    def fail_get_system(kb_name="default"):
        raise RuntimeError("model load failed")

    monkeypatch.setattr(api, "_get_system", fail_get_system)

    client = TestClient(api.app)
    response = client.post("/ask", json={"question": "time constant"})

    assert response.status_code == 500
    assert response.json()["detail"] == "RAG ask system initialization failed."


def test_search_retrieval_candidate_k_overrides_k3(monkeypatch):
    """When retrieval_candidate_k is set in config and a reranker is present,
    /search must query the store with retrieval_candidate_k instead of
    retrieval_k * 3."""

    class FakeReranker:
        def rerank(self, query, items, top_n=5, translated_query=None):
            return items

    class FakeRecordingStore(FakeStore):
        def __init__(self):
            super().__init__()
            self.last_k = None

        def query(self, question, k):
            self.last_k = k
            return super().query(question, k)

    store = FakeRecordingStore()
    reranker = FakeReranker()

    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (store, None, None, None, reranker, None)
    )
    monkeypatch.setitem(api.config, "retrieval_k", 6)
    monkeypatch.setitem(api.config, "retrieval_candidate_k", 20)
    monkeypatch.setitem(api.config, "rerank_top_n", 5)
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "time constant"})

    assert response.status_code == 200
    # With retrieval_candidate_k=20, fetch_k should be 20, not 18
    assert store.last_k == 20


def test_search_retrieval_candidate_k_string_is_normalized(monkeypatch):
    class FakeReranker:
        def rerank(self, query, items, top_n=5, translated_query=None):
            return items

    class FakeRecordingStore(FakeStore):
        def __init__(self):
            super().__init__()
            self.last_k = None

        def query(self, question, k):
            self.last_k = k
            return super().query(question, k)

    store = FakeRecordingStore()
    reranker = FakeReranker()

    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (store, None, None, None, reranker, None)
    )
    monkeypatch.setitem(api.config, "retrieval_k", 6)
    monkeypatch.setitem(api.config, "retrieval_candidate_k", "20")
    monkeypatch.setitem(api.config, "rerank_top_n", 5)
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "time constant"})

    assert response.status_code == 200
    assert store.last_k == 20


def test_search_retrieval_candidate_k_absent_falls_back(monkeypatch):
    """When retrieval_candidate_k is not set, /search falls back to
    retrieval_k * 3 for the fetch_k."""

    class FakeReranker:
        def rerank(self, query, items, top_n=5, translated_query=None):
            return items

    class FakeRecordingStore(FakeStore):
        def __init__(self):
            super().__init__()
            self.last_k = None

        def query(self, question, k):
            self.last_k = k
            return super().query(question, k)

    store = FakeRecordingStore()
    reranker = FakeReranker()

    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (store, None, None, None, reranker, None)
    )
    monkeypatch.setitem(api.config, "retrieval_k", 6)
    # No retrieval_candidate_k set
    monkeypatch.setitem(api.config, "rerank_top_n", 5)
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "time constant"})

    assert response.status_code == 200
    assert store.last_k == 18  # 6 * 3


def test_search_reranker_receives_translated_query_from_enhancer(monkeypatch):
    """When both an enhancer and a reranker are present, the reranker must
    receive the enhanced/translated query as translated_query."""

    class FakeReranker:
        def __init__(self):
            self.query_arg = None
            self.translated_arg = None

        def rerank(self, query, items, top_n=5, translated_query=None):
            self.query_arg = query
            self.translated_arg = translated_query
            return items

    class FakeEnhancer:
        def enhance(self, question, history=None):
            return "ENHANCED: " + question

    store = FakeStore()
    reranker = FakeReranker()

    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (store, None, FakeEnhancer(), None, reranker, None)
    )
    monkeypatch.setitem(api.config, "retrieval_k", 6)
    monkeypatch.setitem(api.config, "rerank_top_n", 5)
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "什么是时间常数"})

    assert response.status_code == 200
    # After refactoring /search to use _retrieve_context_chunks, both
    # query and translated_query are the enhanced question (the store was
    # queried with it), matching the /ask behaviour.
    assert reranker.query_arg == "ENHANCED: 什么是时间常数"
    # translated_query = enhanced version (same as /ask flow)
    assert reranker.translated_arg == "ENHANCED: 什么是时间常数"


# ── retrieval_path tests ──────────────────────────────────────────


class FakeBm25Index:
    """Fake BM25 index that returns at least one chunk so RRF fusion fires."""

    def __init__(self):
        pass

    def is_loaded(self):
        return True

    def query(self, question, k):
        return [
            {
                "text": f"bm25: {question}",
                "source": "fake.md",
                "page": None,
                "chunk_index": 1,
                "bm25_score": 10.0,
            }
        ]


def test_search_retrieval_path_vector_only(monkeypatch):
    """Vector-only search (no BM25, no reranker) → retrieval_path='vector'."""
    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (FakeStore(), None, None, None, None, None)
    )
    monkeypatch.setitem(api.config, "retrieval_k", 6)
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)
    resp = client.post("/search", json={"question": "test"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["chunks"]) > 0
    assert data["chunks"][0]["retrieval_path"] == "vector"


def test_search_retrieval_path_vector_rerank(monkeypatch):
    """Vector + reranker (no BM25) → retrieval_path='vector+rerank'."""

    class FakeReranker:
        def rerank(self, query, items, top_n=5, translated_query=None):
            for item in items:
                item["rerank_score"] = 0.9
            return items

    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (FakeStore(), None, None, None, FakeReranker(), None)
    )
    monkeypatch.setitem(api.config, "retrieval_k", 6)
    monkeypatch.setitem(api.config, "rerank_top_n", 5)
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)
    resp = client.post("/search", json={"question": "rerank test"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["chunks"]) > 0
    assert data["chunks"][0]["retrieval_path"] == "vector+rerank"
    assert data["chunks"][0]["rerank_score"] == 0.9


def test_search_retrieval_path_vector_bm25(monkeypatch):
    """Vector + BM25 (no reranker) → retrieval_path='vector+bm25'."""
    monkeypatch.setattr(
        api, "_get_search_system",
        lambda kb_name="default": (FakeStore(), None, None, None, None, FakeBm25Index()),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 6)
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)
    resp = client.post("/search", json={"question": "bm25 test"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["chunks"]) > 0
    assert data["chunks"][0]["retrieval_path"] == "vector+bm25"


def test_search_retrieval_path_vector_bm25_rerank(monkeypatch):
    """Vector + BM25 + reranker → retrieval_path='vector+bm25+rerank'."""

    class FakeReranker:
        def rerank(self, query, items, top_n=5, translated_query=None):
            for item in items:
                item["rerank_score"] = 0.95
            return items

    monkeypatch.setattr(
        api, "_get_search_system",
        lambda kb_name="default": (FakeStore(), None, None, None, FakeReranker(), FakeBm25Index()),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 6)
    monkeypatch.setitem(api.config, "rerank_top_n", 5)
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)
    resp = client.post("/search", json={"question": "full pipeline"})

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["chunks"]) > 0
    assert data["chunks"][0]["retrieval_path"] == "vector+bm25+rerank"
    assert data["chunks"][0]["rerank_score"] == 0.95


def test_ask_includes_retrieval_path_from_retrieved_chunks(monkeypatch):
    """When _retrieve_context sets retrieval_path on chunks, /ask forwards it."""

    class FakeLlm:
        def generate(self, messages):
            return "test answer"

    class FakeStoreWithPath:
        def __init__(self, *args, **kwargs):
            pass

        def count(self):
            return 1

        def query(self, question, k):
            return [
                {
                    "text": f"matched: {question}",
                    "source": "fake.md",
                    "page": None,
                    "chunk_index": 0,
                    "distance": 0.1,
                }
            ]

    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (FakeStoreWithPath(), None, FakeLlm(), None, None, "system prompt", None, None),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 1)
    monkeypatch.setitem(api.config, "max_context_chars", 6000)

    client = TestClient(api.app)
    resp = client.post("/ask", json={"question": "test"})

    assert resp.status_code == 200
    data = resp.json()
    contexts = data.get("contexts", [])
    assert len(contexts) > 0
    # _retrieve_context with no BM25, no reranker → retrieval_path='vector'
    assert contexts[0]["retrieval_path"] == "vector"


@pytest.mark.parametrize(
    ("distance", "expected"),
    [
        (0.1, "high"),
        (0.3, "medium"),
        (0.5, "low"),
    ],
)
def test_search_confidence_levels(monkeypatch, distance, expected):
    class DistanceStore(FakeStore):
        def query(self, question, k):
            chunk = super().query(question, k)[0]
            chunk["distance"] = distance
            return [chunk]

    monkeypatch.setattr(api, "_get_search_system", lambda kb_name="default": (DistanceStore(), None, None, None, None, None))
    monkeypatch.setitem(api.config, "confidence_high_threshold", 0.2)
    monkeypatch.setitem(api.config, "confidence_low_threshold", 0.4)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "confidence test"})

    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] == expected
    assert data["low_confidence"] is (expected == "low")


def test_search_with_history_passes_history_to_enhancer(monkeypatch):
    class RecordingEnhancer:
        def __init__(self):
            self.history = None

        def enhance(self, question, history=None):
            self.history = history
            return "standalone followup"

    enhancer = RecordingEnhancer()
    monkeypatch.setattr(api, "_get_search_system", lambda kb_name="default": (FakeStore(), None, enhancer, None, None, None))

    client = TestClient(api.app)
    response = client.post(
        "/search",
        json={
            "question": "它怎么用",
            "history": [{"role": "user", "content": "ETS模型"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["searched_question"] == "standalone followup"
    assert enhancer.history == [{"role": "user", "content": "ETS模型"}]


def test_search_cache_fingerprint_changes_cause_miss(monkeypatch):
    """When a retrieval-affecting config field changes, the cache must miss
    because the SearchCache is recreated with a new fingerprint."""

    class RecordingStore:
        def __init__(self, *args, **kwargs):
            self.query_count = 0

        def count(self):
            return 1

        def query(self, question, k):
            self.query_count += 1
            return [
                {
                    "text": f"matched: {question}",
                    "source": "fake.md",
                    "page": None,
                    "chunk_index": 0,
                    "distance": 0.1,
                }
            ]

    store = RecordingStore()
    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (store, None, None, None, None, None)
    )
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    # Set initial retrieval config values
    monkeypatch.setitem(api.config, "retrieval_k", 6)
    monkeypatch.setitem(api.config, "bm25_enabled", False)

    client = TestClient(api.app)

    # First call — cache miss, populates cache
    resp1 = client.post("/search", json={"question": "fingerprint test"})
    assert resp1.status_code == 200
    assert store.query_count == 1

    # Change a retrieval-affecting field → fingerprint changes
    monkeypatch.setitem(api.config, "retrieval_k", 10)
    # Second call — must be a cache miss (new fingerprint, empty cache)
    resp2 = client.post("/search", json={"question": "fingerprint test"})
    assert resp2.status_code == 200
    assert store.query_count == 2  # store was called again


def test_search_cache_fingerprint_same_config_still_hits(monkeypatch):
    """When no retrieval config changed, the cache must still hit normally
    even with a fingerprint present."""

    class RecordingStore:
        def __init__(self, *args, **kwargs):
            self.query_count = 0

        def count(self):
            return 1

        def query(self, question, k):
            self.query_count += 1
            return [
                {
                    "text": f"matched: {question}",
                    "source": "fake.md",
                    "page": None,
                    "chunk_index": 0,
                    "distance": 0.1,
                }
            ]

    store = RecordingStore()
    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (store, None, None, None, None, None)
    )
    monkeypatch.setitem(api.config, "search_distance_threshold", None)
    monkeypatch.setitem(api.config, "retrieval_k", 6)

    client = TestClient(api.app)

    # First call — cache miss
    resp1 = client.post("/search", json={"question": "same config test"})
    assert resp1.status_code == 200
    assert store.query_count == 1

    # Second call with same config — must hit cache
    resp2 = client.post("/search", json={"question": "same config test"})
    assert resp2.status_code == 200
    assert store.query_count == 1  # still 1, cache hit


# ── Search cache integration tests ─────────────────────────────


def test_search_cache_hit_avoids_store_query(monkeypatch):
    """First /search stores results; second call with same effective
    searched_question reuses cache and does not call store again."""

    class RecordingStore:
        def __init__(self, *args, **kwargs):
            self.query_count = 0

        def count(self):
            return 1

        def query(self, question, k):
            self.query_count += 1
            return [
                {
                    "text": f"matched: {question}",
                    "source": "fake.md",
                    "page": None,
                    "chunk_index": 0,
                    "distance": 0.1,
                }
            ]

    store = RecordingStore()
    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (store, None, None, None, None, None)
    )
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)

    # First call queries the store
    resp1 = client.post("/search", json={"question": "cache test query"})
    assert resp1.status_code == 200
    assert store.query_count == 1
    data1 = resp1.json()

    # Second call with same question must hit cache, not the store
    resp2 = client.post("/search", json={"question": "cache test query"})
    assert resp2.status_code == 200
    assert store.query_count == 1  # still 1 — store was not called again
    data2 = resp2.json()

    # Responses must be identical
    assert data1["chunks"] == data2["chunks"]
    assert data1["confidence"] == data2["confidence"]
    assert data1["low_confidence"] == data2["low_confidence"]


def test_search_cache_uses_enhanced_question_as_key(monkeypatch):
    """Cache key must be the searched_question (after enhancement), not the
    original question.  Two different inputs that enhance to the same string
    should share the cache entry."""

    class StaticEnhancer:
        def enhance(self, question, history=None):
            return "always-the-same"

    class RecordingStore:
        def __init__(self, *args, **kwargs):
            self.query_count = 0

        def count(self):
            return 1

        def query(self, question, k):
            self.query_count += 1
            return [
                {
                    "text": f"matched: {question}",
                    "source": "fake.md",
                    "page": None,
                    "chunk_index": 0,
                    "distance": 0.1,
                }
            ]

    store = RecordingStore()
    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (store, None, StaticEnhancer(), None, None, None)
    )
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)

    # First request with any question
    resp1 = client.post("/search", json={"question": "question A"})
    assert resp1.status_code == 200
    assert store.query_count == 1

    # Second request with a different original question, but same enhanced output
    resp2 = client.post("/search", json={"question": "question B"})
    assert resp2.status_code == 200
    assert store.query_count == 1  # cache hit, store not called again

    # Both responses should be identical
    assert resp1.json()["chunks"] == resp2.json()["chunks"]


def test_search_cache_stats_endpoint(monkeypatch):
    """GET /cache/stats reports cached_queries count correctly."""
    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (FakeStore(), None, None, None, None, None)
    )
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)

    # Initially empty
    stats = client.get("/cache/stats").json()
    assert stats["kb_name"] == "default"
    assert stats["cached_queries"] == 0
    assert "max_size" in stats
    assert "ttl_seconds" in stats

    # One search populates the cache
    client.post("/search", json={"question": "stats test"})
    stats = client.get("/cache/stats").json()
    assert stats["cached_queries"] == 1

    # Same question again — still 1 entry
    client.post("/search", json={"question": "stats test"})
    stats = client.get("/cache/stats").json()
    assert stats["cached_queries"] == 1

    # Different question adds a second entry
    client.post("/search", json={"question": "stats test 2"})
    stats = client.get("/cache/stats").json()
    assert stats["cached_queries"] == 2


def test_search_cache_clear_endpoint(monkeypatch):
    """POST /cache/clear empties the cache so the next /search calls the store
    again."""

    class RecordingStore:
        def __init__(self, *args, **kwargs):
            self.query_count = 0

        def count(self):
            return 1

        def query(self, question, k):
            self.query_count += 1
            return [
                {
                    "text": f"matched: {question}",
                    "source": "fake.md",
                    "page": None,
                    "chunk_index": 0,
                    "distance": 0.1,
                }
            ]

    store = RecordingStore()
    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (store, None, None, None, None, None)
    )
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)

    # First search populates cache
    client.post("/search", json={"question": "clear test"})
    assert store.query_count == 1

    # Clear the cache
    clear_resp = client.post("/cache/clear")
    assert clear_resp.status_code == 200
    assert clear_resp.json() == {"status": "cleared", "kb_name": "default"}

    # Stats should be zero
    stats = client.get("/cache/stats").json()
    assert stats["cached_queries"] == 0

    # Same question again must now call the store (cache miss after clear)
    client.post("/search", json={"question": "clear test"})
    assert store.query_count == 2


def test_search_cache_endpoints_accept_kb_name(monkeypatch):
    """Cache stats and clear operate on the requested knowledge-base cache."""

    class RecordingStore:
        def __init__(self):
            self.queries: list[tuple[str, str]] = []

        def count(self):
            return 1

        def query(self, question, k):
            self.queries.append((question, str(k)))
            return [
                {
                    "text": f"matched: {question}",
                    "source": "fake.md",
                    "page": None,
                    "chunk_index": 0,
                    "distance": 0.1,
                }
            ]

    stores: dict[str, RecordingStore] = {}

    def fake_get_search_system(kb_name="default"):
        stores.setdefault(kb_name, RecordingStore())
        return stores[kb_name], None, None, None, None, None

    monkeypatch.setattr(api, "_get_search_system", fake_get_search_system)
    monkeypatch.setitem(api.config, "search_distance_threshold", None)

    client = TestClient(api.app)
    client.post("/search", json={"question": "project cache", "kb_name": "project_a"})

    project_stats = client.get("/cache/stats?kb_name=project_a").json()
    assert project_stats["kb_name"] == "project_a"
    assert project_stats["cached_queries"] == 1

    default_stats = client.get("/cache/stats").json()
    assert default_stats["kb_name"] == "default"
    assert default_stats["cached_queries"] == 0

    clear_resp = client.post("/cache/clear?kb_name=project_a")
    assert clear_resp.status_code == 200
    assert clear_resp.json() == {"status": "cleared", "kb_name": "project_a"}

    project_stats = client.get("/cache/stats?kb_name=project_a").json()
    assert project_stats["cached_queries"] == 0


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/cache/stats?kb_name=../bad"),
        ("POST", "/cache/clear?kb_name=../bad"),
    ],
)
def test_cache_management_invalid_kb_name_returns_400(method, path):
    client = TestClient(api.app)

    if method == "GET":
        response = client.get(path)
    elif method == "POST":
        response = client.post(path)
    else:
        raise AssertionError(f"Unsupported method: {method}")

    assert response.status_code == 400
    assert "Invalid knowledge-base name" in response.json()["detail"]


def test_search_cache_preserves_confidence_and_low_confidence(monkeypatch):
    """On cache hit, confidence / low_confidence / knowledge-gap logging must
    still be computed from the cached chunks."""
    monkeypatch.setattr(
        api, "_get_search_system", lambda kb_name="default": (FakeStore(), None, None, None, None, None)
    )
    # Set threshold so FakeStore's distance=0.1 is "high"
    monkeypatch.setitem(api.config, "confidence_high_threshold", 0.2)
    monkeypatch.setitem(api.config, "confidence_low_threshold", 0.4)

    client = TestClient(api.app)

    # First call — cache miss
    resp1 = client.post("/search", json={"question": "conf cache test"})
    assert resp1.status_code == 200
    assert resp1.json()["confidence"] == "high"
    assert resp1.json()["low_confidence"] is False

    # Second call — cache hit
    resp2 = client.post("/search", json={"question": "conf cache test"})
    assert resp2.status_code == 200
    assert resp2.json()["confidence"] == "high"
    assert resp2.json()["low_confidence"] is False


# ── Thread-safe lazy global cache tests ───────────────────────────


def test_get_system_double_check(monkeypatch):
    """_get_system must call _init_ask_chat exactly once across multiple calls."""
    monkeypatch.setattr(api, "_system_cache", None)
    call_count = 0

    def fake_init(config):
        nonlocal call_count
        call_count += 1
        return object()

    monkeypatch.setattr(api, "_init_ask_chat", fake_init)

    r1 = api._get_system()
    r2 = api._get_system()

    assert call_count == 1
    assert r1 is r2


def test_get_search_system_double_check(monkeypatch):
    """_get_search_system must call _init_search_system exactly once."""
    monkeypatch.setattr(api, "_search_system_cache", None)
    call_count = 0

    def fake_init(config):
        nonlocal call_count
        call_count += 1
        return object()

    monkeypatch.setattr(api, "_init_search_system", fake_init)

    r1 = api._get_search_system()
    r2 = api._get_search_system()

    assert call_count == 1
    assert r1 is r2


def test_get_search_cache_double_check(monkeypatch):
    """_get_search_cache must create SearchCache exactly once."""
    monkeypatch.setattr(api, "_search_cache", None)
    call_count = 0

    class FakeSearchCache:
        def __init__(self, max_size=200, ttl_seconds=3600, config_fingerprint=""):
            nonlocal call_count
            call_count += 1

    monkeypatch.setattr(api, "SearchCache", FakeSearchCache)

    r1 = api._get_search_cache()
    r2 = api._get_search_cache()

    assert call_count == 1
    assert r1 is r2


def test_get_system_thread_safe(monkeypatch):
    """Concurrent threads calling _get_system must trigger init exactly once."""
    import threading

    monkeypatch.setattr(api, "_system_cache", None)
    call_count = 0
    # Use a barrier so all threads start at roughly the same time
    N = 5
    start_barrier = threading.Barrier(N)

    def fake_init(config):
        nonlocal call_count
        call_count += 1
        return object()

    monkeypatch.setattr(api, "_init_ask_chat", fake_init)

    results = []

    def worker():
        start_barrier.wait()  # synchronise start
        r = api._get_system()
        results.append(r)

    threads = [threading.Thread(target=worker) for _ in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert call_count == 1
    assert len(results) == N
    first = results[0]
    for r in results[1:]:
        assert r is first


def test_get_search_cache_thread_safe(monkeypatch):
    """Concurrent threads calling _get_search_cache must create SearchCache exactly once."""
    import threading

    monkeypatch.setattr(api, "_search_cache", None)
    call_count = 0

    class FakeSearchCache:
        def __init__(self, max_size=200, ttl_seconds=3600, config_fingerprint=""):
            nonlocal call_count
            call_count += 1

    monkeypatch.setattr(api, "SearchCache", FakeSearchCache)

    N = 5
    start_barrier = threading.Barrier(N)

    def worker():
        start_barrier.wait()
        api._get_search_cache()

    threads = [threading.Thread(target=worker) for _ in range(N)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert call_count == 1


# ── /ask/stream SSE endpoint tests ─────────────────────────────────


class FakeStreamingLlm:
    """Fake LLM with generate_stream for /ask/stream tests."""

    def __init__(self, tokens=None):
        self._tokens = tokens or ["Hello", " ", "world!"]

    def generate(self, messages):
        return "".join(self._tokens)

    def generate_stream(self, messages):
        for token in self._tokens:
            yield token


class FailingStreamingLlm:
    """Fake LLM whose generate_stream raises."""

    def generate_stream(self, messages):
        raise RuntimeError("stream failure")


def test_ask_stream_endpoint_exists_and_content_type(monkeypatch):
    """POST /ask/stream must return 200 with text/event-stream content type."""
    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (FakeStore(), None, FakeStreamingLlm(), None, None, "system prompt", None, None),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 1)
    monkeypatch.setitem(api.config, "max_context_chars", 6000)

    client = TestClient(api.app)
    response = client.post("/ask/stream", json={"question": "hello"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")


def test_ask_stream_streams_token_events_and_done(monkeypatch):
    """Stream must yield token JSON events followed by [DONE]."""
    tokens = ["alpha", "beta", "gamma"]
    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (FakeStore(), None, FakeStreamingLlm(tokens), None, None, "system prompt", None, None),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 1)
    monkeypatch.setitem(api.config, "max_context_chars", 6000)

    client = TestClient(api.app)
    response = client.post("/ask/stream", json={"question": "test"})

    body = response.text
    lines = body.strip().split("\n\n")

    # Last non-empty line should be "data: [DONE]"
    assert lines[-1].strip() == "data: [DONE]"

    payloads = [
        json.loads(line[len("data: "):])
        for line in lines
        if line.strip() != "data: [DONE]" and line.strip()
    ]
    assert payloads[0]["type"] == "metadata"

    token_payloads = [payload for payload in payloads if payload["type"] == "token"]
    assert len(token_payloads) == len(tokens)
    for expected_token, payload in zip(tokens, token_payloads):
        assert payload["token"] == expected_token


def test_ask_stream_empty_question_returns_400(monkeypatch):
    """Empty or whitespace-only question must return HTTP 400."""
    monkeypatch.setattr(
        api, "_get_system",
        lambda kb_name="default": (FakeStore(), None, FakeStreamingLlm(), None, None, "system prompt", None, None),
    )
    client = TestClient(api.app)

    resp = client.post("/ask/stream", json={"question": ""})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "question 不能为空"

    resp = client.post("/ask/stream", json={"question": "   "})
    assert resp.status_code == 400


def test_ask_stream_init_failure_returns_500(monkeypatch):
    """Init failure must return HTTP 500, not an SSE stream."""
    def fail_get_system(kb_name="default"):
        raise RuntimeError("model load failed")

    monkeypatch.setattr(api, "_get_system", fail_get_system)

    client = TestClient(api.app)
    response = client.post("/ask/stream", json={"question": "test"})

    assert response.status_code == 500
    assert response.json()["detail"] == "RAG ask system initialization failed."


def test_ask_stream_no_chunks_returns_message_then_done(monkeypatch):
    """When retrieval returns no chunks, stream a message then DONE (no crash)."""

    class EmptyStore:
        def __init__(self, *args, **kwargs):
            pass

        def count(self):
            return 0

        def query(self, question, k):
            return []

    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (EmptyStore(), None, FakeStreamingLlm(), None, None, "system prompt", None, None),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 1)
    monkeypatch.setitem(api.config, "max_context_chars", 6000)

    client = TestClient(api.app)
    response = client.post("/ask/stream", json={"question": "nonexistent topic"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    body = response.text
    lines = body.strip().split("\n\n")

    # First event should contain metadata, even when no chunks are found.
    first = lines[0].strip()
    assert first.startswith("data: ")
    payload = json.loads(first[len("data: "):])
    assert payload["type"] == "metadata"
    assert payload["confidence"] == "low"
    assert payload["sources"] == []

    second = lines[1].strip()
    assert second.startswith("data: ")
    payload = json.loads(second[len("data: "):])
    assert payload["type"] == "token"
    assert "没有检索到相关内容" in payload["token"]

    # Last event must be DONE
    assert lines[-1].strip() == "data: [DONE]"


def test_ask_stream_generation_error_emits_error_then_done(monkeypatch):
    """Mid-stream LLM failure must emit an error JSON event then DONE."""
    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (FakeStore(), None, FailingStreamingLlm(), None, None, "system prompt", None, None),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 1)
    monkeypatch.setitem(api.config, "max_context_chars", 6000)

    client = TestClient(api.app)
    response = client.post("/ask/stream", json={"question": "break me"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    body = response.text
    lines = body.strip().split("\n\n")

    # Should have an error event
    error_lines = [l for l in lines if "error" in l and l.strip() != "data: [DONE]"]
    assert len(error_lines) >= 1
    error_payload = json.loads(error_lines[0][len("data: "):])
    assert error_payload["type"] == "error"
    assert "error" in error_payload
    assert "LLM generation failed" in error_payload["error"]

    # Must end with DONE
    assert lines[-1].strip() == "data: [DONE]"


# ── /ask confidence field tests ─────────────────────────────────


def test_ask_response_includes_confidence_high(monkeypatch):
    """When FakeStore returns chunks with distance=0.1, /ask must include
    confidence='high'."""

    class FakeLlm:
        def generate(self, messages):
            return "test answer"

    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (FakeStore(), None, FakeLlm(), None, None, "system prompt", None, None),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 1)
    monkeypatch.setitem(api.config, "max_context_chars", 6000)

    client = TestClient(api.app)
    response = client.post("/ask", json={"question": "test confidence"})

    assert response.status_code == 200
    data = response.json()
    assert "confidence" in data
    assert data["confidence"] == "high"
    assert data["answer"] != ""
    assert data["rewritten_question"] != ""
    assert isinstance(data["contexts"], list)


def test_ask_response_includes_confidence_low_when_no_chunks(monkeypatch):
    """When store returns no chunks, /ask must include confidence='low'."""

    class FakeLlm:
        def generate(self, messages):
            return "should not be called"

    class EmptyStore:
        def __init__(self, *args, **kwargs):
            pass

        def count(self):
            return 0

        def query(self, question, k):
            return []

    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (EmptyStore(), None, FakeLlm(), None, None, "system prompt", None, None),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 1)
    monkeypatch.setitem(api.config, "max_context_chars", 6000)

    client = TestClient(api.app)
    response = client.post("/ask", json={"question": "nonexistent topic"})

    assert response.status_code == 200
    data = response.json()
    assert "confidence" in data
    assert data["confidence"] == "low"
    assert data["answer"] == "没有检索到相关内容。"
    assert data["contexts"] == []


# ── History forwarding tests ─────────────────────────────────────


def test_ask_forwards_history_to_retrieve_context(monkeypatch):
    """POST /ask must pass messages_history to _retrieve_context."""

    captured = {}

    def spy_retrieve_context(**kwargs):
        captured.update(kwargs)
        return [], [{"role": "user", "content": "test"}], "standalone"

    monkeypatch.setattr(api, "_retrieve_context", spy_retrieve_context)
    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (FakeStore(), None, object(), None, None, "system prompt", None, None),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 1)
    monkeypatch.setitem(api.config, "max_context_chars", 6000)

    client = TestClient(api.app)
    response = client.post(
        "/ask",
        json={
            "question": "followup",
            "history": [{"role": "user", "content": "previous question"}],
        },
    )

    assert response.status_code == 200
    assert captured.get("messages_history") == [
        {"role": "user", "content": "previous question"}
    ]


def test_ask_forwards_empty_history_as_none(monkeypatch):
    """POST /ask must pass messages_history=None when history is empty."""

    captured = {}

    def spy_retrieve_context(**kwargs):
        captured.update(kwargs)
        return [], [{"role": "user", "content": "test"}], "standalone"

    monkeypatch.setattr(api, "_retrieve_context", spy_retrieve_context)
    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (FakeStore(), None, object(), None, None, "system prompt", None, None),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 1)
    monkeypatch.setitem(api.config, "max_context_chars", 6000)

    client = TestClient(api.app)
    response = client.post("/ask", json={"question": "no history"})

    assert response.status_code == 200
    assert captured.get("messages_history") is None


def test_ask_stream_forwards_history_to_retrieve_context(monkeypatch):
    """POST /ask/stream must pass messages_history to _retrieve_context."""

    captured = {}

    def spy_retrieve_context(**kwargs):
        captured.update(kwargs)
        return [], [{"role": "user", "content": "test"}], "standalone"

    monkeypatch.setattr(api, "_retrieve_context", spy_retrieve_context)
    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (FakeStore(), None, FakeStreamingLlm(), None, None, "system prompt", None, None),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 1)
    monkeypatch.setitem(api.config, "max_context_chars", 6000)

    client = TestClient(api.app)
    response = client.post(
        "/ask/stream",
        json={
            "question": "followup",
            "history": [{"role": "user", "content": "previous question"}],
        },
    )
    # Consume the stream to trigger generator execution
    _ = response.text

    assert captured.get("messages_history") == [
        {"role": "user", "content": "previous question"}
    ]


def test_ask_stream_forwards_empty_history_as_none(monkeypatch):
    """POST /ask/stream must pass messages_history=None when history is empty."""

    captured = {}

    def spy_retrieve_context(**kwargs):
        captured.update(kwargs)
        return [], [{"role": "user", "content": "test"}], "standalone"

    monkeypatch.setattr(api, "_retrieve_context", spy_retrieve_context)
    monkeypatch.setattr(
        api,
        "_get_system",
        lambda kb_name="default": (FakeStore(), None, FakeStreamingLlm(), None, None, "system prompt", None, None),
    )
    monkeypatch.setitem(api.config, "retrieval_k", 1)
    monkeypatch.setitem(api.config, "max_context_chars", 6000)

    client = TestClient(api.app)
    response = client.post("/ask/stream", json={"question": "no history"})
    _ = response.text

    assert captured.get("messages_history") is None


# ── /index/status endpoint tests ──────────────────────────────────


def test_index_status_returns_expected_shape(monkeypatch):
    """GET /index/status must return 200 with the full expected JSON schema
    when the index directory does not exist (exists=False, zero stats)."""
    monkeypatch.setitem(
        api.config, "chroma_persist_dir", "/tmp/_test_rag_nonexistent_idx"
    )
    client = TestClient(api.app)
    response = client.get("/index/status")

    assert response.status_code == 200
    data = response.json()

    # All expected top-level fields
    assert "exists" in data
    assert "persist_dir" in data
    assert "total_chunks" in data
    assert "source_count" in data
    assert "sources" in data
    assert "file_index_exists" in data
    assert "indexed_files" in data
    assert "total_file_chunks" in data

    # Correct types
    assert isinstance(data["exists"], bool)
    assert isinstance(data["total_chunks"], int)
    assert isinstance(data["source_count"], int)
    assert isinstance(data["sources"], dict)
    assert isinstance(data["indexed_files"], int)
    assert isinstance(data["total_file_chunks"], int)

    # Non-existent directory → zero/false values
    assert data["exists"] is False
    assert data["total_chunks"] == 0
    assert data["source_count"] == 0
    assert data["sources"] == {}
    assert data["file_index_exists"] is False
    assert data["indexed_files"] == 0
    assert data["total_file_chunks"] == 0


def test_index_status_empty_directory(monkeypatch, tmp_path):
    """When the persist directory exists but has no Chroma collection,
    should return exists=True with total_chunks=0."""
    monkeypatch.setitem(api.config, "chroma_persist_dir", str(tmp_path))
    client = TestClient(api.app)
    response = client.get("/index/status")

    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert data["total_chunks"] == 0
    assert data["source_count"] == 0
    assert data["sources"] == {}
    assert data["file_index_exists"] is False
    assert data["indexed_files"] == 0
    assert data["total_file_chunks"] == 0


def test_index_status_file_index_metadata(monkeypatch, tmp_path):
    """When file_index.json exists, the endpoint should report its stats."""
    import json as _json

    file_index = {
        "intro.md": {"sha256": "abc", "chunk_count": 5},
        "guide.md": {"sha256": "def", "chunk_count": 3},
    }
    with open(str(tmp_path / "file_index.json"), "w", encoding="utf-8") as f:
        _json.dump(file_index, f)

    monkeypatch.setitem(api.config, "chroma_persist_dir", str(tmp_path))
    client = TestClient(api.app)
    response = client.get("/index/status")

    assert response.status_code == 200
    data = response.json()
    assert data["exists"] is True
    assert data["file_index_exists"] is True
    assert data["indexed_files"] == 2
    assert data["total_file_chunks"] == 8  # 5 + 3


def test_index_status_accepts_kb_name(monkeypatch, tmp_path):
    """GET /index/status?kb_name=... reports the selected KB index path."""
    import json as _json

    kb_index = tmp_path / "project_a_chroma"
    kb_index.mkdir()
    with open(str(kb_index / "file_index.json"), "w", encoding="utf-8") as f:
        _json.dump({"kb.md": {"chunk_count": 4}}, f)

    def fake_get_config_for_kb(kb_name):
        assert kb_name == "project_a"
        cfg = dict(api.config)
        cfg["chroma_persist_dir"] = str(kb_index)
        return cfg

    monkeypatch.setattr(api, "_get_config_for_kb", fake_get_config_for_kb)

    response = TestClient(api.app).get("/index/status?kb_name=project_a")

    assert response.status_code == 200
    data = response.json()
    assert data["kb_name"] == "project_a"
    assert data["persist_dir"] == str(kb_index)
    assert data["exists"] is True
    assert data["file_index_exists"] is True
    assert data["indexed_files"] == 1
    assert data["total_file_chunks"] == 4


def test_index_status_invalid_kb_name_returns_400():
    response = TestClient(api.app).get("/index/status?kb_name=../bad")

    assert response.status_code == 400
    assert "Invalid knowledge-base name" in response.json()["detail"]
