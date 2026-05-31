import sys
import types

from lib.embed_engine import EmbedEngine, _get_query_prefix
from lib.query_enhancer import QueryEnhancer
from rag_runner import _cleanup_output_dirs, _export_round, _retrieve_context


# EmbedEngine batch_size tests


def _install_fake_sentence_transformer(monkeypatch):
    """Return a tuple (factory, captured_dict) for monkeypatching.

    The fake module avoids importing the real sentence_transformers dependency
    stack in unit tests.
    """
    captured = {}

    class FakeEncodeResult:
        def tolist(self):
            return [[0.0] * 128]

    class FakeSentenceTransformer:
        def encode(self, texts, **kwargs):
            captured.update(kwargs)
            return FakeEncodeResult()

    fake_module = types.SimpleNamespace(
        SentenceTransformer=lambda path: FakeSentenceTransformer()
    )
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)
    return captured


def test_embed_documents_default_batch_size(monkeypatch):
    """embed_documents must pass batch_size=64 and show_progress_bar=False by default."""
    captured = _install_fake_sentence_transformer(monkeypatch)

    engine = EmbedEngine("test-model")
    result = engine.embed_documents(["hello world"])

    assert captured.get("batch_size") == 64
    assert captured.get("show_progress_bar") is False
    assert isinstance(result, list)
    assert isinstance(result[0], list)


def test_embed_documents_custom_batch_size(monkeypatch):
    """embed_documents must forward an overridden batch_size to model.encode."""
    captured = _install_fake_sentence_transformer(monkeypatch)

    engine = EmbedEngine("test-model")
    result = engine.embed_documents(["hello world"], batch_size=128)

    assert captured.get("batch_size") == 128
    assert captured.get("show_progress_bar") is False


def test_embed_batch_uses_default_batch_size(monkeypatch):
    """embed_batch must delegate to embed_documents, using batch_size=64 by default."""
    captured = _install_fake_sentence_transformer(monkeypatch)

    engine = EmbedEngine("test-model")
    result = engine.embed_batch(["hello world"])

    assert captured.get("batch_size") == 64
    assert captured.get("show_progress_bar") is False


# Existing tests


def test_query_prefix_selected_by_model_name():
    assert _get_query_prefix("mixedbread-ai/mxbai-embed-large-v1")
    assert _get_query_prefix("BAAI/bge-large-en-v1.5")
    assert _get_query_prefix("intfloat/e5-large") == "query: "
    assert _get_query_prefix("text-embedding-ada-002") == ""


def test_query_enhancer_strips_common_preamble():
    enhancer = QueryEnhancer(llm_api=None)
    cleaned = enhancer._clean_response(
        "Here's the rewritten query: What is exponential smoothing?",
        "smoothing?",
    )
    assert cleaned == "What is exponential smoothing?"


def test_retrieve_context_caps_context_length():
    class Store:
        def query(self, question, k=5):
            return [
                {"text": "A" * 100, "source": "a.md", "chunk_index": 0},
                {"text": "B" * 100, "source": "b.md", "chunk_index": 1},
            ]

    chunks, messages, _ = _retrieve_context(
        Store(),
        llm=None,
        question="question",
        system_prompt="system",
        retrieval_k=2,
        max_context_chars=80,
    )

    assert len(chunks) == 1
    user_message = messages[-1]["content"]
    assert "B" * 100 not in user_message
    assert len(user_message) < 160


def test_context_cap_includes_separators():
    """_retrieve_context must count the '\\n\\n' separator between entries
    toward max_context_chars."""
    # Citations are '[Source: s.md, Chunk <N>]' = 23 chars.
    # Each entry = citation + '\n' + text = 24 + len(text).
    class Store:
        def query(self, question, k=5):
            return [
                {"text": "A" * 25, "source": "s.md", "chunk_index": 0},
                {"text": "B" * 28, "source": "s.md", "chunk_index": 1},
            ]

    chunks, messages, _ = _retrieve_context(
        Store(),
        llm=None,
        question="q",
        system_prompt="sys",
        retrieval_k=2,
        max_context_chars=101,
    )

    # Entry 0: 24 + 25 = 49 chars  (always fits)
    # Entry 1: 24 + 28 = 52 chars
    #
    # Old check:  total_chars + len(entry1) = 49 + 52 = 101 <= 101  鈫?both included
    #            (but actual context = 49 + 2 + 52 = 103 > 101  鈫?OVER CAP)
    #
    # Fixed check: total_chars + 2 + len(entry1) = 49 + 2 + 52 = 103 > 101 鈫?entry1 excluded
    assert len(chunks) == 1, "separator cost should exclude entry 1"


def test_context_cap_accumulates_separators_across_three_chunks():
    """With 3 chunks of identical size, the accumulated separator costs
    must be counted in total_chars so the third chunk is properly excluded.

    Each entry: citation (23) + '\\n' (1) + 40 chars text = 64 chars.

    max_context_chars=195 鈥?the buggy code (no separator in total_chars)
    allows 3 entries (64+64+64=192 < 195 with checks 64+2+64=130,
    128+2+64=194) but the real context would be 64+2+64+2+64=196 > 195.

    Fixed code correctly stops at 2 entries.
    """
    class Store:
        def query(self, question, k=5):
            return [
                {"text": "A" * 40, "source": "s.md", "chunk_index": 0},
                {"text": "B" * 40, "source": "s.md", "chunk_index": 1},
                {"text": "C" * 40, "source": "s.md", "chunk_index": 2},
            ]

    chunks, messages, _ = _retrieve_context(
        Store(),
        llm=None,
        question="q",
        system_prompt="sys",
        retrieval_k=3,
        max_context_chars=195,
    )

    assert len(chunks) == 2, (
        f"expected 2 chunks (separator cost excludes 3rd), got {len(chunks)}"
    )
    texts = [c["text"] for c in chunks]
    assert texts == ["A" * 40, "B" * 40], f"unexpected chunks: {texts}"


def test_cleanup_output_dirs_uses_modified_time(tmp_path):
    old_dir = tmp_path / "z_old"
    new_dir = tmp_path / "a_new"
    old_dir.mkdir()
    new_dir.mkdir()
    old_time = 1_700_000_000
    new_time = 1_800_000_000
    import os

    os.utime(old_dir, (old_time, old_time))
    os.utime(new_dir, (new_time, new_time))

    _cleanup_output_dirs(str(tmp_path), max_output_dirs=1)

    assert not old_dir.exists()
    assert new_dir.exists()


def test_export_round_uses_enhance_label(tmp_path):
    _export_round(
        str(tmp_path),
        1,
        question="浠€涔堟槸鏃堕棿甯告暟",
        chunks=[{"text": "time constant context", "source": "time.md", "chunk_index": 0}],
        answer="answer",
        rewritten_question="What's a time constant?",
        enhance_label="Translated Question",
    )

    text = (tmp_path / "01_round.md").read_text(encoding="utf-8")
    assert "**Translated Question:**" in text
    assert "**Enhanced Question:**" not in text


def test_retrieval_candidate_k_overrides_fallback():
    """When retrieval_candidate_k is provided with a reranker, store.query
    must use that value instead of retrieval_k * 3."""
    captured_k = []

    class Store:
        def query(self, question, k=5):
            captured_k.append(k)
            return [
                {"text": f"chunk for {question}", "source": "x.md", "chunk_index": 0}
            ]

    class FakeReranker:
        def __init__(self):
            self.calls = []

        def rerank(self, query, items, top_n=5, translated_query=None):
            self.calls.append((query, items, top_n, translated_query))
            for item in items:
                item["rerank_score"] = 0.9
            return items[:top_n]

    reranker = FakeReranker()
    _retrieve_context(
        Store(),
        llm=None,
        question="original q",
        system_prompt="sys",
        retrieval_k=5,
        reranker=reranker,
        retrieval_candidate_k=20,
    )

    # store.query should receive 20, not 5*3=15
    assert captured_k == [20]

    # reranker should receive original query + translated_query
    assert len(reranker.calls) == 1
    assert reranker.calls[0][0] == "original q"
    assert reranker.calls[0][3] == "original q"  # translated_query (same, no enhancer)


def test_retrieval_candidate_k_string_is_normalized():
    captured_k = []

    class Store:
        def query(self, question, k=5):
            captured_k.append(k)
            return [{"text": "chunk", "source": "x.md", "chunk_index": 0}]

    class FakeReranker:
        def rerank(self, query, items, top_n=5, translated_query=None):
            return items

    _retrieve_context(
        Store(),
        llm=None,
        question="q",
        system_prompt="sys",
        retrieval_k=5,
        reranker=FakeReranker(),
        retrieval_candidate_k="20",
    )

    assert captured_k == [20]


def test_retrieval_candidate_k_absent_falls_back_to_k3():
    """When retrieval_candidate_k is None but reranker is present,
    store.query must fall back to retrieval_k * 3."""
    captured_k = []

    class Store:
        def query(self, question, k=5):
            captured_k.append(k)
            return [
                {"text": "chunk", "source": "x.md", "chunk_index": 0}
            ]

    class FakeReranker:
        def rerank(self, query, items, top_n=5, translated_query=None):
            return items[:top_n]

    _retrieve_context(
        Store(),
        llm=None,
        question="q",
        system_prompt="sys",
        retrieval_k=5,
        reranker=FakeReranker(),
        retrieval_candidate_k=None,  # absent
    )

    assert captured_k == [15]  # 5 * 3


def test_retrieval_candidate_k_no_reranker_ignored():
    """When no reranker is present, retrieval_candidate_k is ignored
    and retrieval_k is used directly."""
    captured_k = []

    class Store:
        def query(self, question, k=5):
            captured_k.append(k)
            return [
                {"text": "chunk", "source": "x.md", "chunk_index": 0}
            ]

    _retrieve_context(
        Store(),
        llm=None,
        question="q",
        system_prompt="sys",
        retrieval_k=5,
        retrieval_candidate_k=20,  # should be ignored
    )

    assert captured_k == [5]


# 鈹€鈹€ LlmApi timeout tests 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€


def test_llmapi_accepts_timeout_parameter():
    """LlmApi must accept timeout as __init__ parameter and
    use it in the OpenAI call timeout."""
    from lib.llm_api import LlmApi

    api = LlmApi(
        api_key="test-key",
        base_url="http://test",
        model="test-model",
        timeout=120,
    )
    assert api._timeout == 120


def test_llmapi_default_timeout_is_60():
    """LlmApi must default timeout to 60 when no timeout is provided."""
    from lib.llm_api import LlmApi

    api = LlmApi(
        api_key="test-key",
        base_url="http://test",
        model="test-model",
    )
    assert api._timeout == 60


def test_llmapi_passes_timeout_to_openai(monkeypatch):
    """LlmApi.generate_stream must pass self._timeout to
    OpenAI.chat.completions.create as the timeout kwarg."""
    from lib.llm_api import LlmApi

    captured = {}

    class FakeResponse:
        def __init__(self):
            self.choices = []

        def __iter__(self):
            return iter([])

    def fake_create(*args, **kwargs):
        captured["timeout"] = kwargs.get("timeout")
        return FakeResponse()

    monkeypatch.setattr(
        "lib.llm_api.OpenAI",
        lambda api_key, base_url: type(
            "FakeClient",
            (object,),
            {
                "chat": type(
                    "FakeChat",
                    (object,),
                    {
                        "completions": type(
                            "FakeCompletions",
                            (object,),
                            {"create": staticmethod(fake_create)},
                        )
                    },
                )()
            },
        )(),
    )

    api = LlmApi(api_key="x", base_url="http://x", model="x", timeout=99)

    # consume the generator to trigger the OpenAI call
    for _ in api.generate_stream([{"role": "user", "content": "hi"}]):
        pass

    assert captured.get("timeout") == 99


def test_init_ask_chat_passes_llm_timeout_seconds(monkeypatch):
    """_init_ask_chat must read llm_timeout_seconds from config and
    pass it to LlmApi as timeout."""
    from rag_runner import _init_ask_chat

    captured = {}

    class FakeLlmApi:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    class FakeEmbedEngine:
        def __init__(self, model_name):
            self.model_name = model_name

    class FakeVectorDb:
        def __init__(self, persist_dir, embed_engine):
            pass

        def count(self):
            return 0

    monkeypatch.setattr(
        "lib.pipeline._import_lib",
        lambda: (FakeEmbedEngine, FakeLlmApi, FakeVectorDb),
    )

    config = {
        "embedding_model_name": "test",
        "chroma_persist_dir": "/tmp/fake",
        "llm": {
            "api_key": "key",
            "api_base_url": "http://test",
            "model": "m",
            "temperature": 0.3,
            "thinking_mode": False,
        },
        "llm_timeout_seconds": 120,
    }

    _init_ask_chat(config)

    assert captured.get("timeout") == 120


def test_init_ask_chat_default_timeout_when_config_absent(monkeypatch):
    """When llm_timeout_seconds is absent from config, LlmApi must
    get the default timeout of 60."""
    from rag_runner import _init_ask_chat

    captured = {}

    class FakeLlmApi:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    class FakeEmbedEngine:
        def __init__(self, model_name):
            self.model_name = model_name

    class FakeVectorDb:
        def __init__(self, persist_dir, embed_engine):
            pass

        def count(self):
            return 0

    monkeypatch.setattr(
        "lib.pipeline._import_lib",
        lambda: (FakeEmbedEngine, FakeLlmApi, FakeVectorDb),
    )

    config = {
        "embedding_model_name": "test",
        "chroma_persist_dir": "/tmp/fake",
        "llm": {
            "api_key": "key",
            "api_base_url": "http://test",
            "model": "m",
            "temperature": 0.3,
            "thinking_mode": False,
        },
        # no llm_timeout_seconds
    }

    _init_ask_chat(config)

    assert captured.get("timeout") == 60


def test_init_query_enhancer_passes_llm_timeout_seconds(monkeypatch):
    """_init_query_enhancer must read llm_timeout_seconds from config and
    pass it to LlmApi as timeout."""
    from rag_runner import _init_query_enhancer

    captured = {}

    class FakeLlmApi:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    class FakeEmbedEngine:
        def __init__(self, model_name):
            self.model_name = model_name

    class FakeVectorDb:
        def __init__(self, persist_dir, embed_engine):
            pass

    # _init_query_enhancer gets LlmApi via _import_lib when LlmApi is None
    monkeypatch.setattr(
        "lib.pipeline._import_lib",
        lambda: (FakeEmbedEngine, FakeLlmApi, FakeVectorDb),
    )

    config = {
        "query_enhance_enabled": True,
        "enhancer_mode": "llm",
        "enhancer": {
            "api_key": "key",
            "api_base_url": "http://test",
            "model": "m",
            "temperature": 0.0,
            "thinking_mode": False,
        },
        "llm_timeout_seconds": 90,
    }

    _init_query_enhancer(config, allow_llm=True)

    assert captured.get("timeout") == 90


def test_config_example_includes_llm_timeout_seconds():
    """config_example.json must include llm_timeout_seconds with default 60."""
    import json, os

    config_path = os.path.join(
        os.path.dirname(__file__), "..", "config_example.json"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    assert "llm_timeout_seconds" in config
    assert config["llm_timeout_seconds"] == 60


def test_cmd_list_sources_uses_chroma_directly(capsys, monkeypatch):
    """cmd_list_sources must not use VectorDb; reads Chroma directly."""
    import chromadb

    def guard_import_lib():
        raise RuntimeError(
            "cmd_list_sources must not call _import_lib (i.e. VectorDb)"
        )

    monkeypatch.setattr("rag_runner._import_lib", guard_import_lib)

    # Fake Chroma collection returning two sources
    fake_metadatas = [
        {"source": "report.pdf"},
        {"source": "report.pdf"},
        {"source": "notes.md"},
    ]

    class FakeCollection:
        def get(self, include=None):
            return {"metadatas": fake_metadatas}

    class FakeClient:
        def get_collection(self, name):
            return FakeCollection()

    monkeypatch.setattr(
        chromadb, "PersistentClient", lambda path, settings: FakeClient()
    )

    from rag_runner import cmd_list_sources

    config = {"chroma_persist_dir": "./fake_path"}
    cmd_list_sources(config)

    captured = capsys.readouterr()
    assert "Indexed 2 files" in captured.out
    assert "report.pdf" in captured.out
    assert "notes.md" in captured.out
    assert "report.pdf" in captured.out
    assert "2 chunks" in captured.out
    assert "1 chunks" in captured.out


def test_cmd_retrieve_passes_enhanced_query_to_store(capsys, monkeypatch):
    """cmd_retrieve must reuse _init_search_system and _retrieve_context_chunks,
    passing the enhanced query through the shared pipeline."""
    captured_queries = []

    class FakeStore:
        def query(self, question, k=5):
            captured_queries.append(question)
            return [{"text": "dummy", "source": "dummy.md", "chunk_index": 0}]

    class FakeEnhancer:
        label = "Test Enhanced"
        def enhance(self, question, history=None):
            return "enhanced: " + question

    def fake_init_search_system(config):
        return (FakeStore(), None, FakeEnhancer(), None, None, None)

    monkeypatch.setattr("rag_runner._init_search_system", fake_init_search_system)

    config = {
        "embedding_model_name": "test-model",
        "chroma_persist_dir": "./fake_path",
        "retrieval_k": 5,
    }

    from rag_runner import cmd_retrieve

    cmd_retrieve(config, "original question")

    # store.query must be called with the enhanced question
    assert captured_queries == ["enhanced: original question"]
    captured = capsys.readouterr()
    assert "Test Enhanced: enhanced: original question" in captured.out
    assert "Generating..." not in captured.out
    assert "Question: original question" in captured.out
