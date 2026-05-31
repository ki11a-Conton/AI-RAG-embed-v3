"""Tests for eval_retrieval helpers and compare mode."""
import pytest

# ── 假对象工厂 ──────────────────────────────────


class FakeStore:
    """可配置返回文档的假向量库。"""

    def __init__(self, docs_by_query=None, default_docs=None):
        self.docs_by_query = docs_by_query or {}
        self.default_docs = default_docs or []

    def query(self, query_text, k=5):
        for key, docs in self.docs_by_query.items():
            if key in query_text:
                return docs[:k]
        return self.default_docs[:k]


class FakeReranker:
    """假重排序器：直接返回传入的结果（透传）。"""

    def rerank(self, query, results, top_n=5):
        return results[:top_n]


class FakeBM25:
    """假 BM25 索引。"""

    def __init__(self, loaded=True, docs_by_query=None, default_docs=None):
        self._loaded = loaded
        self.docs_by_query = docs_by_query or {}
        self.default_docs = default_docs or []

    def is_loaded(self):
        return self._loaded

    def query(self, query_text, k=5):
        for key, docs in self.docs_by_query.items():
            if key in query_text:
                return docs[:k]
        return self.default_docs[:k]


class FakeBM25NoIsLoaded:
    """Fake BM25 object that intentionally omits is_loaded()."""

    def query(self, query_text, k=5):
        return _make_docs("bm25 without is_loaded")[:k]


class FakeQueryEnhancer:
    """假查询增强器：透传原问题。"""

    def enhance(self, question, history=None):
        return question


# ── 帮助函数 ────────────────────────────────────


def _make_docs(*texts):
    """将多个文本转为 store/query 兼容的 dict 列表。"""
    return [{"text": t} for t in texts]


# ── 导入被测模块 ───────────────────────────────


from eval_retrieval import (
    _keyword_hit,
    _result_texts,
    _calc_fetch_k,
    _parse_judge_response,
    _retrieve_vector,
    _retrieve_hybrid,
    _eval_compare,
    _eval_full,
    _eval_keywords,
    _JUDGE_PROMPT,
)


# ── 单元测试：_keyword_hit ──────────────────────


class TestKeywordHit:
    def test_hit_when_keyword_present(self):
        texts = ["alpha smoothing is used for forecasting"]
        is_hit, matched_count = _keyword_hit(texts, ["smoothing", "forecast"])
        assert is_hit is True
        assert matched_count == 2

    def test_hit_when_one_keyword_present(self):
        texts = ["this is about time series decomposition"]
        is_hit, matched_count = _keyword_hit(texts, ["smoothing", "decomposition"])
        assert is_hit is True
        assert matched_count == 1

    def test_miss_when_no_keyword_present(self):
        texts = ["random text without relevant terms"]
        is_hit, matched_count = _keyword_hit(texts, ["smoothing", "forecast"])
        assert is_hit is False
        assert matched_count == 0

    def test_case_insensitive(self):
        texts = ["Exponential Smoothing uses ALPHA"]
        is_hit, matched_count = _keyword_hit(texts, ["alpha", "smoothing"])
        assert is_hit is True
        assert matched_count == 2

    def test_keyword_across_multiple_texts(self):
        texts = ["Document one has 'smoothing'", "Document two has 'forecast'"]
        is_hit, matched_count = _keyword_hit(texts, ["smoothing", "forecast"])
        assert is_hit is True
        assert matched_count == 2

    def test_empty_keywords(self):
        texts = ["any text here"]
        is_hit, matched_count = _keyword_hit(texts, [])
        assert is_hit is False
        assert matched_count == 0

    def test_empty_texts(self):
        is_hit, matched_count = _keyword_hit([], ["keyword"])
        assert is_hit is False
        assert matched_count == 0


# ── 单元测试：_result_texts ─────────────────────


class TestResultTexts:
    def test_dict_results(self):
        results = [{"text": "hello"}, {"text": "world"}]
        assert _result_texts(results) == ["hello", "world"]

    def test_string_results(self):
        results = ["hello", "world"]
        assert _result_texts(results) == ["hello", "world"]

    def test_mixed_results(self):
        results = [{"text": "hello"}, "plain"]
        assert _result_texts(results) == ["hello", "plain"]

    def test_empty(self):
        assert _result_texts([]) == []


# ── 单元测试：_calc_fetch_k ─────────────────────


class TestCalcFetchK:
    def test_no_reranker(self):
        assert _calc_fetch_k(5, None, None) == 5

    def test_with_reranker_default(self):
        assert _calc_fetch_k(5, object(), None) == 15  # 5 * 3

    def test_with_reranker_and_candidate_k(self):
        assert _calc_fetch_k(5, object(), 20) == 20

    def test_with_reranker_and_string_candidate_k(self):
        assert _calc_fetch_k(5, object(), "20") == 20

    def test_candidate_k_zero_ignored(self):
        # _calc_fetch_k only uses candidate_k if > 0
        assert _calc_fetch_k(5, object(), 0) == 15  # falls back to 5*3


# ── 测试：_retrieve_vector ──────────────────────


class TestRetrieveVector:
    def test_basic_retrieval(self):
        store = FakeStore(default_docs=_make_docs("alpha smoothing", "forecast methods"))
        texts = _retrieve_vector(store, "what is smoothing", 3)
        assert "alpha smoothing" in texts
        assert "forecast methods" in texts

    def test_with_fake_reranker(self):
        store = FakeStore(default_docs=_make_docs("doc1", "doc2", "doc3", "doc4", "doc5"))
        reranker = FakeReranker()
        texts = _retrieve_vector(store, "query", 5, reranker=reranker, rerank_top_n=3)
        assert len(texts) == 3

    def test_empty_results(self):
        store = FakeStore(default_docs=[])
        texts = _retrieve_vector(store, "query", 5)
        assert texts == []


# ── 测试：_retrieve_hybrid ──────────────────────


class TestRetrieveHybrid:
    def test_falls_back_to_vector_when_bm25_none(self):
        store = FakeStore(default_docs=_make_docs("vector only result"))
        texts = _retrieve_hybrid(
            store, "query", 3, 3, bm25_index=None
        )
        assert "vector only result" in texts

    def test_falls_back_to_vector_when_bm25_not_loaded(self):
        store = FakeStore(default_docs=_make_docs("vector result"))
        bm25 = FakeBM25(loaded=False)
        texts = _retrieve_hybrid(
            store, "query", 3, 3, bm25_index=bm25
        )
        assert "vector result" in texts

    def test_hybrid_with_bm25_enhances_results(self):
        """混合检索应包含 BM25 返回的额外文档。"""
        store = FakeStore(
            docs_by_query={"query": _make_docs("vector doc A", "vector doc B")}
        )
        bm25 = FakeBM25(
            loaded=True,
            docs_by_query={"query": _make_docs("bm25 doc X", "bm25 doc Y")},
        )
        texts = _retrieve_hybrid(
            store, "query", 4, 3, bm25_index=bm25
        )
        # 应有来自两边的文档（RRF 融合）
        assert len(texts) > 0
        # 尽管 RRF 排名不确定，但至少两边的内容可能出现在结果中
        combined = " ".join(texts)
        assert "vector" in combined or "bm25" in combined

    def test_hybrid_with_reranker(self):
        store = FakeStore(
            docs_by_query={"q": _make_docs("v1", "v2", "v3", "v4", "v5")}
        )
        bm25 = FakeBM25(
            loaded=True,
            docs_by_query={"q": _make_docs("b1", "b2")},
        )
        reranker = FakeReranker()
        texts = _retrieve_hybrid(
            store, "q", 5, 3, bm25_index=bm25,
            reranker=reranker, rerank_top_n=4
        )
        assert 1 <= len(texts) <= 4

    def test_hybrid_when_bm25_returns_empty(self):
        """BM25 返回空结果时退化为纯向量。"""
        store = FakeStore(default_docs=_make_docs("vector only"))
        bm25 = FakeBM25(loaded=True, default_docs=[])
        texts = _retrieve_hybrid(
            store, "query", 3, 3, bm25_index=bm25
        )
        assert "vector only" in texts

    def test_hybrid_bm25_no_is_loaded_attr(self):
        """无 is_loaded 属性的假 BM25 应被视为可用。"""
        store = FakeStore(default_docs=_make_docs("v"))
        texts = _retrieve_hybrid(
            store, "query", 3, 3, bm25_index=FakeBM25NoIsLoaded()
        )
        assert "bm25 without is_loaded" in texts


# ── 集成测试：_eval_compare ─────────────────────


class TestEvalCompare:
    """测试 compare 模式的核心流程。"""

    ITEMS = [
        {
            "question": "What is exponential smoothing?",
            "expected_keywords": ["smoothing", "alpha", "weighted"],
        },
        {
            "question": "What is ARIMA?",
            "expected_keywords": ["ARIMA", "autoregressive", "differencing"],
        },
        {
            "question": "What is a tsibble?",
            "expected_keywords": ["tsibble", "index", "tidy"],
        },
    ]

    def _run_compare(self, store, bm25_index, **kwargs):
        """运行 compare 并返回 (vec_hits, hyb_hits, total)。"""
        reranker = kwargs.get("reranker", None)
        enhancer = kwargs.get("enhancer", None) or FakeQueryEnhancer()
        retrieval_k = kwargs.get("retrieval_k", 5)
        rerank_top_n = kwargs.get("rerank_top_n", 5)
        retrieval_candidate_k = kwargs.get("retrieval_candidate_k", None)
        config = kwargs.get("config", {})

        return _eval_compare(
            config=config,
            store=store,
            query_enhancer=enhancer,
            reranker=reranker,
            retrieval_k=retrieval_k,
            rerank_top_n=rerank_top_n,
            bm25_index=bm25_index,
            retrieval_candidate_k=retrieval_candidate_k,
            items=self.ITEMS,
        )

    def test_compare_computes_totals(self):
        """compare 模式应返回 (vector_hits, hybrid_hits, total)。"""
        store = FakeStore(default_docs=_make_docs(
            "alpha smoothing is used for forecasting",
        ))
        bm25 = FakeBM25(loaded=False)

        vec_h, hyb_h, total = self._run_compare(store, bm25)

        assert total == 3
        assert isinstance(vec_h, int)
        assert isinstance(hyb_h, int)
        assert 0 <= vec_h <= total
        assert 0 <= hyb_h <= total

    def test_compare_hybrid_exceeds_vector(self):
        """场景：向量检索缺少某关键词，BM25 补充后命中率提升。"""
        # 向量库：只有 doc_v，包含 "smoothing" 和 "forecasting"（无 "ARIMA"）
        vector_docs = _make_docs("alpha smoothing is used for forecasting")
        store = FakeStore(default_docs=vector_docs)

        # BM25：包含 ARIMA 相关内容
        bm25_docs = _make_docs("ARIMA stands for autoregressive integrated moving average")
        bm25 = FakeBM25(loaded=True, default_docs=bm25_docs)

        vec_h, hyb_h, total = self._run_compare(store, bm25)

        # 向量检索无法命中 "ARIMA" 关键词 → ARIMA 问题 expected 为 miss
        # 混合检索可以命中 → ARIMA 问题 expected 为 hit
        # 所以 hybrid >= vector
        assert hyb_h >= vec_h, (
            f"Expected hybrid hits ({hyb_h}) >= vector hits ({vec_h}), "
            "but hybrid did not improve over vector-only"
        )

    def test_compare_hybrid_can_exceed_vector_specifically(self):
        """验证具体场景：vector miss 某题，hybrid 命中。"""
        # Q1 关键词: smoothing, alpha, weighted
        # Q2 关键词: ARIMA, autoregressive, differencing
        # Q3 关键词: tsibble, index, tidy

        # 向量库：只有 Q1 的关键词
        store = FakeStore(default_docs=_make_docs(
            "Exponential smoothing uses alpha and weighted averages for forecasting"
        ))

        # BM25 额外提供 Q2 的关键词
        bm25 = FakeBM25(loaded=True, default_docs=_make_docs(
            "ARIMA stands for autoregressive integrated moving average with differencing"
        ))

        vec_h, hyb_h, total = self._run_compare(store, bm25)

        # 向量库只有 Q1 的关键词 → Q1 hit，Q2 miss, Q3 miss → vec_h = 1
        # BM25 额外包含 Q2 的关键词 → Q1 hit (来自向量), Q2 hit (来自BM25), Q3 miss → hyb_h = 2
        assert vec_h == 1, f"Expected vector hits = 1, got {vec_h}"
        assert hyb_h == 2, f"Expected hybrid hits = 2, got {hyb_h}"
        assert hyb_h > vec_h, f"Hybrid ({hyb_h}) should exceed vector ({vec_h})"

    def test_compare_both_equal_when_no_bm25(self):
        """bm25_index=None 时，hybrid 退化为 vector，两者一致。"""
        store = FakeStore(default_docs=_make_docs(
            "alpha smoothing forecast"
        ))
        vec_h, hyb_h, total = self._run_compare(store, bm25_index=None)

        assert vec_h == hyb_h

    def test_compare_with_reranker(self):
        """带 reranker 的 compare 模式不应抛异常。"""
        store = FakeStore(default_docs=_make_docs(
            "alpha smoothing weighted forecast ARIMA autoregressive differencing tsibble index tidy"
        ))
        bm25 = FakeBM25(loaded=True, default_docs=_make_docs(
            "additional ARIMA details with differencing"
        ))
        reranker = FakeReranker()

        vec_h, hyb_h, total = self._run_compare(
            store, bm25, reranker=reranker
        )
        assert total == 3
        # 所有关键词都在文档中，所以两边都应命中所有题
        assert vec_h == 3
        assert hyb_h == 3

    def test_compare_all_miss(self):
        """完全没有匹配时两边都是 0。"""
        store = FakeStore(default_docs=_make_docs("completely unrelated content"))
        bm25 = FakeBM25(loaded=True, default_docs=_make_docs("also unrelated"))

        vec_h, hyb_h, total = self._run_compare(store, bm25)

        assert vec_h == 0
        assert hyb_h == 0
        assert total == 3

    def test_compare_with_query_enhancer(self):
        """query_enhancer 应被调用且不影响结果一致性。"""
        store = FakeStore(default_docs=_make_docs("smoothing alpha weighted"))

        class RecordingEnhancer:
            def __init__(self):
                self.calls = []

            def enhance(self, question, history=None):
                self.calls.append(question)
                return question  # 透传

        enhancer = RecordingEnhancer()
        bm25 = FakeBM25(loaded=True, default_docs=_make_docs("ARIMA differencing"))

        vec_h, hyb_h, total = self._run_compare(
            store, bm25, enhancer=enhancer
        )

        assert len(enhancer.calls) == total  # 每题调用一次
        assert total == 3


# ── 单元测试：_parse_judge_response ───────────────


class TestParseJudgeResponse:
    """Test judge response parsing for both JSON and yes/no formats."""

    def test_json_valid_score_1(self):
        score, reason = _parse_judge_response(
            '{"score": 1, "reason": "covers all key points"}'
        )
        assert score == 1
        assert reason == "covers all key points"

    def test_json_valid_score_0(self):
        score, reason = _parse_judge_response(
            '{"score": 0, "reason": "misses core points"}'
        )
        assert score == 0
        assert reason == "misses core points"

    def test_json_score_as_string(self):
        """JSON with score as string "1" should be parsed as int."""
        score, reason = _parse_judge_response(
            '{"score": "1", "reason": "good"}'
        )
        assert score == 1
        assert reason == "good"

    def test_json_missing_reason(self):
        score, reason = _parse_judge_response(
            '{"score": 1}'
        )
        assert score == 1
        assert reason == ""

    def test_json_missing_score_defaults_to_0(self):
        score, reason = _parse_judge_response(
            '{"reason": "some reason"}'
        )
        assert score == 0
        assert reason == "some reason"

    def test_json_score_other_than_one_scores_0(self):
        score, reason = _parse_judge_response(
            '{"score": 2, "reason": "invalid score"}'
        )
        assert score == 0
        assert reason == "invalid score"

    def test_json_non_object_scores_0(self):
        score, reason = _parse_judge_response("[1]")
        assert score == 0
        assert "parse error" in reason.lower()

    def test_json_with_whitespace(self):
        score, reason = _parse_judge_response(
            '  \n  {"score": 0, "reason": "bad"}  \n'
        )
        assert score == 0
        assert reason == "bad"

    def test_yes_lowercase(self):
        score, reason = _parse_judge_response("yes")
        assert score == 1
        assert "yes" in reason

    def test_yes_uppercase(self):
        score, reason = _parse_judge_response("YES")
        assert score == 1

    def test_yes_mixed_case(self):
        score, reason = _parse_judge_response("Yes")
        assert score == 1

    def test_no_lowercase(self):
        score, reason = _parse_judge_response("no")
        assert score == 0
        assert "no" in reason

    def test_no_uppercase(self):
        score, reason = _parse_judge_response("NO")
        assert score == 0

    def test_yes_with_whitespace(self):
        score, reason = _parse_judge_response("  yes  ")
        assert score == 1

    def test_no_with_whitespace(self):
        score, reason = _parse_judge_response("\tno\n")
        assert score == 0

    def test_parse_error_generic_text(self):
        """Generic text that is neither JSON nor yes/no → score 0 with reason."""
        score, reason = _parse_judge_response(
            "I think the answer is mostly correct"
        )
        assert score == 0
        assert "parse error" in reason.lower()

    def test_parse_error_empty_string(self):
        score, reason = _parse_judge_response("")
        assert score == 0
        assert "parse error" in reason.lower()

    def test_json_markdown_code_fence(self):
        """JSON wrapped in markdown code fence should still parse."""
        response = '```json\n{"score": 1, "reason": "good"}\n```'
        score, reason = _parse_judge_response(response)
        assert score == 1
        assert reason == "good"

    def test_json_invalid_syntax(self):
        """Malformed JSON → score 0 with parse error."""
        score, reason = _parse_judge_response(
            '{"score": 1, reason: "missing quotes"}'
        )
        assert score == 0
        assert "parse error" in reason.lower()

    def test_partial_text_with_yes_inside(self):
        """Only exact 'yes'/'no' should match, not 'yes' embedded in a sentence."""
        score, reason = _parse_judge_response(
            "yes, the answer covers the points"
        )
        assert score == 0
        assert "parse error" in reason.lower()


# ── 集成测试：_eval_full 指标统计（无真实网络/API） ──


class FakeLLMQueue:
    """Fake LLM that returns responses from a queue, one per generate() call."""

    def __init__(self, responses):
        self.responses = list(responses)
        self._idx = 0
        self.call_count = 0

    def generate(self, messages):
        self.call_count += 1
        if self._idx < len(self.responses):
            resp = self.responses[self._idx]
            self._idx += 1
            return resp
        return ""


class TestEvalFullMetricAccounting:
    """Test _eval_full metric accounting with mocked LLM and retrieval."""

    ITEMS = [
        {
            "question": "What is exponential smoothing?",
            "expected_keywords": ["smoothing", "alpha"],
            "expected_answer": "Exponential smoothing uses weighted averages.",
        },
        {
            "question": "What is ARIMA?",
            "expected_keywords": ["ARIMA", "autoregressive"],
            "expected_answer": "ARIMA is autoregressive integrated moving average.",
        },
    ]

    @staticmethod
    def _fake_retrieve_context(store, llm, question, system_prompt, retrieval_k,
                               query_enhancer=None, reranker=None, rerank_top_n=5,
                               max_context_chars=6000, bm25_index=None,
                               retrieval_candidate_k=None, **kwargs):
        # Return chunks that only match item 1 keywords
        if "smoothing" in question.lower() or "exponential" in question.lower():
            chunks = [{"text": "Exponential smoothing uses alpha and weighted averages for forecasting."}]
        else:
            chunks = [{"text": "unrelated content about vegetables"}]
        messages = [{"role": "user", "content": question}]
        return chunks, messages, question

    def test_full_mode_outputs_both_metric_labels(self, monkeypatch, capsys):
        """--full mode output must include 'Retrieval hit rate' and 'Answer quality rate'."""
        from eval_retrieval import _retrieve_context

        monkeypatch.setattr(
            "eval_retrieval._retrieve_context",
            self._fake_retrieve_context,
        )

        # Queue: answer_q1, judge_q1, answer_q2, judge_q2
        fake_llm = FakeLLMQueue([
            "Exponential smoothing is a forecasting method.",          # answer Q1
            '{"score": 1, "reason": "covers key points"}',            # judge Q1 → 1
            "Vegetables are healthy.",                                 # answer Q2
            '{"score": 0, "reason": "irrelevant"}',                   # judge Q2 → 0
        ])

        _eval_full(
            config={},
            store=None,
            llm=fake_llm,
            query_enhancer=None,
            system_prompt="You are a helpful assistant.",
            reranker=None,
            bm25_index=None,
            items=self.ITEMS,
        )

        captured = capsys.readouterr().out

        assert "Retrieval hit rate:" in captured
        assert "Answer quality rate:" in captured
        # Item 1 has "smoothing" and "alpha" in chunks → keyword hit
        # Item 2 has no matching keywords → keyword miss
        # So retrieval: 1/2 = 50%
        assert "1/2" in captured

    def test_full_mode_uses_parse_judge_response(self, monkeypatch, capsys):
        """Judge scoring should go through _parse_judge_response for both JSON and yes/no."""
        monkeypatch.setattr(
            "eval_retrieval._retrieve_context",
            self._fake_retrieve_context,
        )

        # Use yes/no style judge responses
        fake_llm = FakeLLMQueue([
            "Answer about smoothing.",   # answer Q1
            "yes",                        # judge Q1 → 1
            "Unrelated.",                 # answer Q2
            "no",                         # judge Q2 → 0
        ])

        _eval_full(
            config={},
            store=None,
            llm=fake_llm,
            query_enhancer=None,
            system_prompt="You are a helpful assistant.",
            reranker=None,
            bm25_index=None,
            items=self.ITEMS,
        )

        captured = capsys.readouterr().out
        assert "Retrieval hit rate:" in captured
        assert "Answer quality rate:" in captured
        # yes → 1, no → 0, so quality should be 1/2
        assert "1/2" in captured

    def test_full_mode_judge_parse_error_scores_0(self, monkeypatch, capsys):
        """Judge parse errors → score 0 with reason, quality rate reflects 0."""
        monkeypatch.setattr(
            "eval_retrieval._retrieve_context",
            self._fake_retrieve_context,
        )

        # Both judge responses are unparseable
        fake_llm = FakeLLMQueue([
            "Answer about smoothing.",   # answer Q1
            "garbled nonsense !!!",       # judge Q1 → parse error → 0
            "Unrelated.",                 # answer Q2
            "also broken ###",            # judge Q2 → parse error → 0
        ])

        _eval_full(
            config={},
            store=None,
            llm=fake_llm,
            query_enhancer=None,
            system_prompt="You are a helpful assistant.",
            reranker=None,
            bm25_index=None,
            items=self.ITEMS,
        )

        captured = capsys.readouterr().out
        assert "Answer quality rate:" in captured
        # Both parse errors → quality = 0/2
        assert "0/2" in captured

    def test_full_mode_no_chunks_handled_gracefully(self, monkeypatch, capsys):
        """When _retrieve_context returns no chunks, the item is skipped."""
        def fake_retrieve_no_chunks(*args, **kwargs):
            return [], [], ""

        monkeypatch.setattr(
            "eval_retrieval._retrieve_context",
            fake_retrieve_no_chunks,
        )

        fake_llm = FakeLLMQueue([])
        single_item = [self.ITEMS[0]]

        _eval_full(
            config={},
            store=None,
            llm=fake_llm,
            query_enhancer=None,
            system_prompt="",
            reranker=None,
            bm25_index=None,
            items=single_item,
        )

        captured = capsys.readouterr().out
        # No chunks → item skipped, total is 1 but keyword_hit and score_sum are 0
        assert "无检索结果" in captured
        # ZeroDivisionError should NOT happen; print line still runs
        assert "Retrieval hit rate:" in captured


# ── 边界问题测试 ──────────────────────────────────


class TestBoundaryQuestions:
    """边界问题应从 hit-rate 分母中排除，单独报告。"""

    ITEMS_WITH_BOUNDARY = [
        {
            "question": "What is exponential smoothing?",
            "expected_keywords": ["smoothing", "alpha"],
        },
        {
            "question": "How do I deploy Kubernetes pods?",
            "expected_keywords": ["Kubernetes", "pod"],
            "is_boundary": True,
        },
    ]

    def test_boundary_excluded_from_denominator(self, capsys):
        """边界问题不计入 hit-rate 分母。"""
        store = FakeStore(default_docs=_make_docs("alpha smoothing"))
        enhancer = FakeQueryEnhancer()

        hit, total = _eval_keywords(
            store=store,
            query_enhancer=enhancer,
            reranker=None,
            retrieval_k=5,
            rerank_top_n=5,
            bm25_index=None,
            retrieval_candidate_k=None,
            items=self.ITEMS_WITH_BOUNDARY,
        )

        # total 应为 1（只有非边界问题）
        assert total == 1
        assert hit == 1

    def test_boundary_hit_warns(self, capsys):
        """边界问题意外命中关键词时应发出警告。"""
        # Store that returns different docs depending on query content
        store = FakeStore(
            docs_by_query={
                "smoothing": _make_docs("alpha smoothing for forecasting"),
                "Kubernetes": _make_docs("Kubernetes pod deployment replicas"),
            },
            default_docs=_make_docs("unrelated"),
        )
        enhancer = FakeQueryEnhancer()

        import warnings as _warnings
        with _warnings.catch_warnings(record=True) as w:
            _warnings.simplefilter("always")
            hit, total = _eval_keywords(
                store=store,
                query_enhancer=enhancer,
                reranker=None,
                retrieval_k=5,
                rerank_top_n=5,
                bm25_index=None,
                retrieval_candidate_k=None,
                items=self.ITEMS_WITH_BOUNDARY,
            )

        assert total == 1
        assert hit == 1
        # 应有关于边界问题意外命中的警告
        boundary_warnings = [
            ww for ww in w
            if "boundary" in str(ww.message).lower()
        ]
        assert len(boundary_warnings) >= 1

    def test_boundary_correctly_rejected_reported(self, capsys):
        """边界问题正确拒绝时应显示 boundary correctly rejected 计数。"""
        # 文档不含 Kubernetes 关键词 → 边界问题正确拒绝
        store = FakeStore(default_docs=_make_docs("alpha smoothing forecast"))
        enhancer = FakeQueryEnhancer()

        hit, total = _eval_keywords(
            store=store,
            query_enhancer=enhancer,
            reranker=None,
            retrieval_k=5,
            rerank_top_n=5,
            bm25_index=None,
            retrieval_candidate_k=None,
            items=self.ITEMS_WITH_BOUNDARY,
        )

        captured = capsys.readouterr().out
        assert "Domain retrieval hit rate:" in captured
        assert "Boundary questions:" in captured
        assert "correctly rejected" in captured
        assert "1/1" in captured

    def test_compare_boundary_excluded_from_totals(self, capsys):
        """compare 模式：边界问题从 totals 中排除。"""
        store = FakeStore(default_docs=_make_docs("alpha smoothing"))
        bm25 = FakeBM25(loaded=False)

        vec_h, hyb_h, total = _eval_compare(
            config={},
            store=store,
            query_enhancer=FakeQueryEnhancer(),
            reranker=None,
            retrieval_k=5,
            rerank_top_n=5,
            bm25_index=bm25,
            retrieval_candidate_k=None,
            items=self.ITEMS_WITH_BOUNDARY,
        )

        # total 应为 1（边界问题排除）
        assert total == 1
        assert vec_h == 1
        assert hyb_h == 1

    def test_compare_boundary_rows_displayed(self, capsys):
        """compare 模式：边界问题行仍显示但标记为 boundary。"""
        store = FakeStore(default_docs=_make_docs("alpha smoothing"))
        bm25 = FakeBM25(loaded=False)

        _eval_compare(
            config={},
            store=store,
            query_enhancer=FakeQueryEnhancer(),
            reranker=None,
            retrieval_k=5,
            rerank_top_n=5,
            bm25_index=bm25,
            retrieval_candidate_k=None,
            items=self.ITEMS_WITH_BOUNDARY,
        )

        captured = capsys.readouterr().out
        assert "Boundary questions" in captured

    def test_zero_domain_total_keywords_no_zero_division(self, capsys):
        """当所有问题都是边界问题时，_eval_keywords 不应抛出 ZeroDivisionError。"""
        all_boundary = [
            {
                "question": "How do I deploy Kubernetes pods?",
                "expected_keywords": ["Kubernetes", "pod"],
                "is_boundary": True,
            },
        ]
        store = FakeStore(default_docs=_make_docs("unrelated"))

        hit, total = _eval_keywords(
            store=store,
            query_enhancer=FakeQueryEnhancer(),
            reranker=None,
            retrieval_k=5,
            rerank_top_n=5,
            bm25_index=None,
            retrieval_candidate_k=None,
            items=all_boundary,
        )

        assert total == 0
        assert hit == 0
        captured = capsys.readouterr().out
        assert "Domain retrieval hit rate:" in captured
        assert "0.00%" in captured

    def test_full_boundary_excluded_from_denominator(self, monkeypatch, capsys):
        """_eval_full 应跳过边界问题，不计入 total/denominator。"""
        items_with_boundary = [
            {
                "question": "What is exponential smoothing?",
                "expected_keywords": ["smoothing", "alpha"],
                "expected_answer": "Exponential smoothing uses weighted averages.",
            },
            {
                "question": "How do I deploy Kubernetes pods?",
                "expected_keywords": ["Kubernetes", "pod"],
                "expected_answer": "Use kubectl apply.",
                "is_boundary": True,
            },
            {
                "question": "What is ARIMA?",
                "expected_keywords": ["ARIMA", "autoregressive"],
                "expected_answer": "ARIMA is autoregressive integrated moving average.",
            },
        ]

        def fake_retrieve_context(store, llm, question, system_prompt, retrieval_k,
                                   query_enhancer=None, reranker=None, rerank_top_n=5,
                                   max_context_chars=6000, bm25_index=None,
                                   retrieval_candidate_k=None, **kwargs):
            if "smoothing" in question.lower():
                chunks = [{"text": "Exponential smoothing uses alpha and weighted averages."}]
            elif "ARIMA" in question:
                chunks = [{"text": "ARIMA is autoregressive integrated moving average with differencing."}]
            else:
                chunks = [{"text": "unrelated"}]
            messages = [{"role": "user", "content": question}]
            return chunks, messages, question

        monkeypatch.setattr(
            "eval_retrieval._retrieve_context",
            fake_retrieve_context,
        )

        fake_llm = FakeLLMQueue([
            "Exponential smoothing is a forecasting method.",    # answer Q1
            '{"score": 1, "reason": "covers key points"}',      # judge Q1 → 1
            "ARIMA is autoregressive integrated moving average.", # answer Q3
            '{"score": 1, "reason": "correct"}',                 # judge Q3 → 1
        ])

        _eval_full(
            config={},
            store=None,
            llm=fake_llm,
            query_enhancer=None,
            system_prompt="You are a helpful assistant.",
            reranker=None,
            bm25_index=None,
            items=items_with_boundary,
        )

        captured = capsys.readouterr().out

        # Boundary item should be printed with skip line
        assert "boundary question, skipped" in captured
        # Only 2 non-boundary items → denominators should be 2
        assert "Retrieval hit rate:  2/2" in captured
        assert "Answer quality rate: 2/2" in captured
        # Boundary item must NOT appear in hit rate denominator as /3
        assert "/3" not in captured

    def test_zero_domain_total_compare_no_zero_division(self, capsys):
        """当所有问题都是边界问题时，_eval_compare 不应抛出 ZeroDivisionError。"""
        all_boundary = [
            {
                "question": "How do I deploy Kubernetes pods?",
                "expected_keywords": ["Kubernetes", "pod"],
                "is_boundary": True,
            },
        ]
        store = FakeStore(default_docs=_make_docs("unrelated"))
        bm25 = FakeBM25(loaded=False)

        vec_h, hyb_h, total = _eval_compare(
            config={},
            store=store,
            query_enhancer=FakeQueryEnhancer(),
            reranker=None,
            retrieval_k=5,
            rerank_top_n=5,
            bm25_index=bm25,
            retrieval_candidate_k=None,
            items=all_boundary,
        )

        assert total == 0
        captured = capsys.readouterr().out
        assert "0.00%" in captured
