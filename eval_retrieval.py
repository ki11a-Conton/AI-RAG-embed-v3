"""
eval_retrieval.py
RAG 检索命中率 + 端到端回答质量评测脚本。
用法：
  python eval_retrieval.py                    # 仅测检索命中率
  python eval_retrieval.py --full             # 端到端：检索 + LLM 回答 + LLM-as-judge 评分
  python eval_retrieval.py --compare          # 对比向量检索 vs 混合检索命中率
"""
import json
import sys
import os

from rag_runner import load_config, _init_ask_chat, _init_search_system, _retrieve_context

_JUDGE_PROMPT = """You are an answer quality evaluator. Rate whether the answer covers the key points of the expected answer.

Scoring:
- 1 = Answer covers the core points of the expected answer
- 0 = Answer misses the core points or is irrelevant

Respond with ONLY a JSON object: {{"score": 0 or 1, "reason": "brief explanation"}}

Expected answer: {expected}
Actual answer: {actual}
"""


# Shared helpers.

def _keyword_hit(texts, expected_keywords):
    """检查关键词是否出现在检索文本中。
    返回 (is_hit: bool, matched_count: int)。
    """
    joined = "\n".join(texts).lower()
    matched = [kw for kw in expected_keywords if kw.lower() in joined]
    return len(matched) > 0, len(matched)


def _result_texts(results):
    """将 store.query / bm25.query 返回的 dict 列表转为纯文本列表。"""
    return [r["text"] if isinstance(r, dict) else r for r in results]


def _calc_fetch_k(retrieval_k, reranker, retrieval_candidate_k):
    """计算 vector query 的 k 值，与 _retrieve_context 保持一致。"""
    if reranker:
        try:
            candidate_k = int(retrieval_candidate_k)
        except (TypeError, ValueError):
            candidate_k = 0
        if candidate_k > 0:
            return candidate_k
        return retrieval_k * 3
    return retrieval_k


def _parse_judge_response(response_text: str):
    """Parse judge response. Accepts both JSON and yes/no formats.

    JSON style:  {"score": 0 or 1, "reason": "..."}
    Yes/no style:  "yes" / "no" (case-insensitive)

    Returns (score: int, reason: str).  Score is always 0 or 1.
    Parse errors score 0 with a useful reason.
    """
    text = response_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()

    # Try JSON first
    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("judge JSON response must be an object")
        score = int(data.get("score", 0))
        score = 1 if score == 1 else 0
        reason = data.get("reason", "")
        return score, reason
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    # Try yes/no format
    lower = text.lower()
    if lower == "yes":
        return 1, "judge responded yes"
    if lower == "no":
        return 0, "judge responded no"

    # Fallback – parse error
    return 0, f"judge parse error: unexpected response format: {text[:100]}"


# ──────────────────────────────────────────────
# 检索策略（供 compare 模式复用）
# ──────────────────────────────────────────────

def _retrieve_vector(store, rewritten, fetch_k, reranker=None, rerank_top_n=None):
    """纯向量检索（无 BM25）。返回文本列表。"""
    results = store.query(rewritten, k=fetch_k)
    if reranker and results:
        results = reranker.rerank(rewritten, results, top_n=rerank_top_n)
    return _result_texts(results)


def _retrieve_hybrid(store, rewritten, fetch_k, retrieval_k,
                     bm25_index, reranker=None, rerank_top_n=None):
    """混合检索：向量 + BM25 + RRF 融合。
    bm25_index 为 None 时退化为纯向量检索。
    """
    vector_results = store.query(rewritten, k=fetch_k)

    bm25_available = False
    if bm25_index is not None:
        if hasattr(bm25_index, "is_loaded"):
            bm25_available = bm25_index.is_loaded()
        else:
            bm25_available = True  # 测试用的假对象

    if not bm25_available:
        if reranker and vector_results:
            vector_results = reranker.rerank(rewritten, vector_results, top_n=rerank_top_n)
        return _result_texts(vector_results)

    bm25_chunks = bm25_index.query(rewritten, k=fetch_k)
    if not bm25_chunks:
        if reranker and vector_results:
            vector_results = reranker.rerank(rewritten, vector_results, top_n=rerank_top_n)
        return _result_texts(vector_results)

    from lib.hybrid_retriever import reciprocal_rank_fusion

    rrf_top = fetch_k if reranker else retrieval_k
    fused = reciprocal_rank_fusion(vector_results, bm25_chunks, top_n=rrf_top)

    if reranker:
        fused = reranker.rerank(rewritten, fused, top_n=rerank_top_n)

    return _result_texts(fused)


# ──────────────────────────────────────────────
# 评测模式
# ──────────────────────────────────────────────

def _eval_keywords(store, query_enhancer, reranker, retrieval_k, rerank_top_n,
                   bm25_index=None, retrieval_candidate_k=None, items=None):
    """默认模式：按当前配置评测检索关键词命中率。"""
    total = 0
    hit = 0
    boundary_total = 0
    boundary_correct_rejected = 0

    for item in items:
        question = item["question"]
        expected_keywords = item["expected_keywords"]
        is_boundary = item.get("is_boundary", False)

        rewritten = question
        if query_enhancer:
            try:
                rewritten = query_enhancer.enhance(question, history=None)
            except Exception:
                pass

        fetch_k = _calc_fetch_k(retrieval_k, reranker, retrieval_candidate_k)
        texts = _retrieve_hybrid(
            store, rewritten, fetch_k, retrieval_k,
            bm25_index, reranker, rerank_top_n
        )

        is_hit, _ = _keyword_hit(texts, expected_keywords)

        if is_boundary:
            boundary_total += 1
            if not is_hit:
                boundary_correct_rejected += 1
                status = "✅"
            else:
                status = "⚠️"
                import warnings
                warnings.warn(
                    f"Boundary question unexpectedly hit keywords: {question}",
                    stacklevel=2,
                )
            print(f"{status} [B{boundary_total}] {question}")
            if is_hit:
                print(f"     ⚠️  边界问题意外命中关键词：{expected_keywords}")
            continue

        total += 1
        status = "✅" if is_hit else "❌"
        print(f"{status} [{total}] {question}")
        if not is_hit:
            print(f"     期望关键词：{expected_keywords}")
        if is_hit:
            hit += 1

    print()
    if total > 0:
        print(f"Domain retrieval hit rate: {hit}/{total} = {hit / total:.2%}")
    else:
        print(f"Domain retrieval hit rate: {hit}/{total} = 0.00%")
    if boundary_total:
        print(f"Boundary questions: {boundary_correct_rejected}/{boundary_total} correctly rejected")
    return hit, total


def _eval_full(config, store, llm, query_enhancer, system_prompt, reranker,
               bm25_index, parent_store=None, multi_query_enhancer=None, items=None):
    retrieval_k = config.get("retrieval_k", 5)
    rerank_top_n = config.get("rerank_top_n", 5)

    total = 0
    score_sum = 0
    keyword_hit = 0
    boundary_skipped = 0

    for item in items:
        question = item["question"]
        expected_keywords = item.get("expected_keywords", [])
        expected_answer = item.get("expected_answer", "")

        is_boundary = item.get("is_boundary", False)
        if is_boundary:
            boundary_skipped += 1
            print(f"⏭️  [B{boundary_skipped}] {question} — boundary question, skipped")
            continue

        total += 1

        # 检索 + 生成回答
        chunks, messages, rewritten = _retrieve_context(
            store, llm, question, system_prompt, retrieval_k,
            query_enhancer,
            reranker=reranker,
            rerank_top_n=rerank_top_n,
            max_context_chars=config.get("max_context_chars", 6000),
            bm25_index=bm25_index,
            retrieval_candidate_k=config.get("retrieval_candidate_k"),
            parent_store=parent_store,
            multi_query_enhancer=multi_query_enhancer,
        )

        if not chunks:
            print(f"❌ [{total}] {question} — 无检索结果")
            continue

        # 关键词命中
        joined = "\n".join(c["text"] for c in chunks).lower()
        kw_matched = [kw for kw in expected_keywords if kw.lower() in joined]
        if kw_matched:
            keyword_hit += 1

        # LLM 生成回答
        try:
            answer = llm.generate(messages)
        except Exception as e:
            print(f"❌ [{total}] {question}")
            print(f"     关键词命中：{len(kw_matched)}/{len(expected_keywords)} | 回答评分：0 | generation error: {e}")
            continue

        # LLM-as-judge 评分
        judge_prompt = _JUDGE_PROMPT.format(expected=expected_answer, actual=answer)
        judge_messages = [{"role": "user", "content": judge_prompt}]
        try:
            judge_response = llm.generate(judge_messages)
            score, reason = _parse_judge_response(judge_response)
        except Exception as e:
            score = 0
            reason = f"judge error: {e}"

        score_sum += score
        status = "✅" if score else "❌"
        print(f"{status} [{total}] {question}")
        print(f"     关键词命中：{len(kw_matched)}/{len(expected_keywords)} | 回答评分：{score} | {reason}")

    print()
    if total > 0:
        print(f"Retrieval hit rate:  {keyword_hit}/{total} = {keyword_hit / total:.2%}")
        print(f"Answer quality rate: {score_sum}/{total} = {score_sum / total:.2%}")
    else:
        print(f"Retrieval hit rate:  {keyword_hit}/{total} = 0.00%")
        print(f"Answer quality rate: {score_sum}/{total} = 0.00%")


def _eval_compare(config, store, query_enhancer, reranker, retrieval_k, rerank_top_n,
                  bm25_index, retrieval_candidate_k, items):
    """对比模式：逐题对比向量检索 vs 混合检索命中率。"""
    vector_hits = 0
    hybrid_hits = 0
    total = 0
    rows = []  # (question, vec_hit, hyb_hit, is_boundary)
    boundary_rows = []

    for item in items:
        question = item["question"]
        expected_keywords = item["expected_keywords"]
        is_boundary = item.get("is_boundary", False)

        rewritten = question
        if query_enhancer:
            try:
                rewritten = query_enhancer.enhance(question, history=None)
            except Exception:
                pass

        fetch_k = _calc_fetch_k(retrieval_k, reranker, retrieval_candidate_k)

        # 向量检索
        vec_texts = _retrieve_vector(store, rewritten, fetch_k, reranker, rerank_top_n)
        vec_is_hit, _ = _keyword_hit(vec_texts, expected_keywords)

        # 混合检索
        hyb_texts = _retrieve_hybrid(
            store, rewritten, fetch_k, retrieval_k,
            bm25_index, reranker, rerank_top_n
        )
        hyb_is_hit, _ = _keyword_hit(hyb_texts, expected_keywords)

        if is_boundary:
            boundary_rows.append((question, vec_is_hit, hyb_is_hit))
            continue

        total += 1
        if vec_is_hit:
            vector_hits += 1
        if hyb_is_hit:
            hybrid_hits += 1

        rows.append((question, vec_is_hit, hyb_is_hit))

    # ── 打印对比表格 ──
    max_q = max((len(r[0]) for r in rows), default=8)
    max_q = max(max_q, 8)
    col_w = 8  # Vector / Hybrid 列宽
    sep = f"+{'-' * (max_q + 2)}+{'-' * (col_w + 2)}+{'-' * (col_w + 2)}+"

    print(sep)
    print(f"| {'Question'.ljust(max_q)} | {'Vector'.center(col_w)} | {'Hybrid'.center(col_w)} |")
    print(sep)
    for q, v, h in rows:
        v_mark = "✅" if v else "❌"
        h_mark = "✅" if h else "❌"
        print(f"| {q.ljust(max_q)} | {v_mark.center(col_w - 2)} | {h_mark.center(col_w - 2)} |")
    print(sep)
    total_vec = f"{vector_hits}/{total}"
    total_hyb = f"{hybrid_hits}/{total}"
    print(f"| {'Total'.ljust(max_q)} | {total_vec.center(col_w)} | {total_hyb.center(col_w)} |")
    print(sep)

    if boundary_rows:
        print()
        print("Boundary questions (excluded from hit-rate totals):")
        print(sep)
        print(f"| {'Question'.ljust(max_q)} | {'Vector'.center(col_w)} | {'Hybrid'.center(col_w)} |")
        print(sep)
        for q, v, h in boundary_rows:
            v_mark = "⚠️" if v else "✅"
            h_mark = "⚠️" if h else "✅"
            print(f"| {q.ljust(max_q)} | {v_mark.center(col_w - 2)} | {h_mark.center(col_w - 2)} |")
        print(sep)

    print()
    if total > 0:
        print(f"Keyword hit rate (Vector): {vector_hits}/{total} = {vector_hits / total:.2%}")
        print(f"Keyword hit rate (Hybrid): {hybrid_hits}/{total} = {hybrid_hits / total:.2%}")
    else:
        print(f"Keyword hit rate (Vector): {vector_hits}/{total} = 0.00%")
        print(f"Keyword hit rate (Hybrid): {hybrid_hits}/{total} = 0.00%")

    return vector_hits, hybrid_hits, total


# ──────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────

def main():
    config = load_config()

    eval_path = os.path.join(os.path.dirname(__file__), "evals", "questions.jsonl")
    if not os.path.exists(eval_path):
        print(f"评测文件不存在：{eval_path}")
        sys.exit(1)

    with open(eval_path, "r", encoding="utf-8") as f:
        items = [json.loads(line.strip()) for line in f if line.strip()]

    if not items:
        print("评测文件为空")
        sys.exit(1)

    full_mode = "--full" in sys.argv
    compare_mode = "--compare" in sys.argv

    if compare_mode:
        store, parent_store, query_enhancer, multi_query_enhancer, reranker, bm25_index = _init_search_system(config)
        retrieval_k = config.get("retrieval_k", 5)
        rerank_top_n = config.get("rerank_top_n", 5)
        retrieval_candidate_k = config.get("retrieval_candidate_k")
        print("=== 检索方式对比模式（Vector vs Hybrid）===\n")
        _eval_compare(
            config, store, query_enhancer, reranker, retrieval_k, rerank_top_n,
            bm25_index, retrieval_candidate_k, items
        )
    elif full_mode:
        print("=== 端到端评测模式 ===\n")
        store, parent_store, llm, query_enhancer, multi_query_enhancer, system_prompt, reranker, bm25_index = _init_ask_chat(config)
        _eval_full(config, store, llm, query_enhancer, system_prompt, reranker,
                   bm25_index, parent_store, multi_query_enhancer, items)
    else:
        retrieval_k = config.get("retrieval_k", 5)
        rerank_top_n = config.get("rerank_top_n", 5)
        retrieval_candidate_k = config.get("retrieval_candidate_k")
        store, parent_store, query_enhancer, multi_query_enhancer, reranker, bm25_index = _init_search_system(config)
        _eval_keywords(store, query_enhancer, reranker, retrieval_k, rerank_top_n,
                       bm25_index=bm25_index, retrieval_candidate_k=retrieval_candidate_k,
                       items=items)

if __name__ == "__main__":
    main()
