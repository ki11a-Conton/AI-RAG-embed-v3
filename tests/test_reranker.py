"""Tests for reranker behavior."""
import sys
import types


class TestReranker:
    """Tests for Reranker.rerank with translated_query support."""

    def _install_fake_sentence_transformers(self, monkeypatch, fake_cls):
        fake_module = types.SimpleNamespace(CrossEncoder=fake_cls)
        monkeypatch.setitem(sys.modules, "sentence_transformers", fake_module)
        sys.modules.pop("lib.reranker", None)

    def test_uses_translated_query_in_pairs_when_provided(self, monkeypatch):
        """When translated_query is provided, CrossEncoder predict pairs
        should use translated_query, not the original query."""
        captured_pairs = []

        # We must patch before importing Reranker so that the CrossEncoder
        # import inside the class body succeeds (no real model download).
        class FakeCrossEncoder:
            def __init__(self, model_name):
                self.model_name = model_name

            def predict(self, pairs):
                captured_pairs.extend(pairs)
                return [0.9] * len(pairs)

        self._install_fake_sentence_transformers(monkeypatch, FakeCrossEncoder)

        from lib.reranker import Reranker

        reranker = Reranker(model_name="fake-model")
        items = [
            {"text": "document chunk one", "source": "a.md"},
            {"text": "document chunk two", "source": "b.md"},
        ]

        result = reranker.rerank(
            "original question",
            items,
            top_n=5,
            translated_query="enhanced translated question",
        )

        assert len(captured_pairs) == 2
        # Each pair should use translated_query as the first element
        assert captured_pairs[0][0] == "enhanced translated question"
        assert captured_pairs[1][0] == "enhanced translated question"
        assert captured_pairs[0][1] == "document chunk one"
        assert captured_pairs[1][1] == "document chunk two"

        # Verify rerank_score is attached
        assert result[0]["rerank_score"] == 0.9
        assert result[1]["rerank_score"] == 0.9

    def test_uses_query_when_translated_query_not_provided(self, monkeypatch):
        """When translated_query is NOT provided, CrossEncoder predict pairs
        should use the original query string."""
        captured_pairs = []

        class FakeCrossEncoder:
            def __init__(self, model_name):
                self.model_name = model_name

            def predict(self, pairs):
                captured_pairs.extend(pairs)
                return [0.85, 0.75]

        self._install_fake_sentence_transformers(monkeypatch, FakeCrossEncoder)

        from lib.reranker import Reranker

        reranker = Reranker(model_name="fake-model")
        items = [
            {"text": "chunk A", "source": "a.md"},
            {"text": "chunk B", "source": "b.md"},
        ]

        result = reranker.rerank("plain query", items, top_n=2)

        assert len(captured_pairs) == 2
        assert captured_pairs[0][0] == "plain query"
        assert captured_pairs[1][0] == "plain query"

        assert result[0]["rerank_score"] == 0.85
        assert result[1]["rerank_score"] == 0.75

    def test_translated_query_none_uses_query(self, monkeypatch):
        """When translated_query is explicitly None, fall back to query."""
        captured_pairs = []

        class FakeCrossEncoder:
            def __init__(self, model_name):
                pass

            def predict(self, pairs):
                captured_pairs.extend(pairs)
                return [0.5]

        self._install_fake_sentence_transformers(monkeypatch, FakeCrossEncoder)

        from lib.reranker import Reranker

        reranker = Reranker(model_name="fake-model")
        reranker.rerank("fallback query", [{"text": "text"}], translated_query=None)

        assert captured_pairs[0][0] == "fallback query"

    def test_empty_items_returns_empty_list(self, monkeypatch):
        """Empty items should return empty list without calling model."""
        class FakeCrossEncoder:
            def __init__(self, model_name):
                pass

            def predict(self, pairs):
                raise AssertionError("predict should not be called for empty items")

        self._install_fake_sentence_transformers(monkeypatch, FakeCrossEncoder)

        from lib.reranker import Reranker

        reranker = Reranker(model_name="fake-model")
        result = reranker.rerank("query", [], translated_query="enhanced")
        assert result == []

    def test_scores_are_sorted_descending(self, monkeypatch):
        """Results should be sorted by rerank_score descending."""
        class FakeCrossEncoder:
            def __init__(self, model_name):
                pass

            def predict(self, pairs):
                return [0.3, 0.9, 0.6]

        self._install_fake_sentence_transformers(monkeypatch, FakeCrossEncoder)

        from lib.reranker import Reranker

        reranker = Reranker(model_name="fake-model")
        items = [
            {"text": "low"},
            {"text": "high"},
            {"text": "mid"},
        ]
        result = reranker.rerank("q", items, top_n=3)

        scores = [c["rerank_score"] for c in result]
        assert scores == [0.9, 0.6, 0.3]

    def test_top_n_truncation(self, monkeypatch):
        """Results should be truncated to top_n."""
        class FakeCrossEncoder:
            def __init__(self, model_name):
                pass

            def predict(self, pairs):
                return [0.5] * 10

        self._install_fake_sentence_transformers(monkeypatch, FakeCrossEncoder)

        from lib.reranker import Reranker

        reranker = Reranker(model_name="fake-model")
        items = [{"text": f"chunk_{i}"} for i in range(10)]
        result = reranker.rerank("q", items, top_n=3)
        assert len(result) == 3
