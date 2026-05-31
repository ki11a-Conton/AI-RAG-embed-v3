import os
import time

from lib.config import resolve_path
from lib.logger import get_logger
from lib.output_writer import _format_source_citation


logger = get_logger(__name__)

_SYSTEM_BASE_STRICT = (
    "You are a precise knowledge-base assistant. "
    "Answer ONLY based on the provided context. "
    "If the answer is not in the context, say 'I don't know' or '资料中未提供'. "
    "Always cite your sources at the end of your answer in the format: "
    "[Source: <filename>, Page <N>] or [Source: <filename>, Chunk <N>]."
)

_SYSTEM_BASE = (
    "You are a helpful assistant. Use the provided context as your primary source. "
    "You may supplement with general knowledge when the context is insufficient, "
    "but mark such additions with [general knowledge]. "
    "When answering, cite your sources in the format: "
    "[Source: <filename>, Page <N>] or [Source: <filename>, Chunk <N>]."
)


def _build_system_prompt(rules: str, strict_context: bool = False) -> str:
    base = _SYSTEM_BASE_STRICT if strict_context else _SYSTEM_BASE
    if not rules:
        return base
    return base + "\n\n" + rules


def _import_lib():
    from lib.embed_engine import EmbedEngine
    from lib.llm_api import LlmApi
    from lib.vector_db import VectorDb

    return EmbedEngine, LlmApi, VectorDb


def _positive_int(value, default: int) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _load_bm25_index(config: dict):
    if not config.get("bm25_enabled", False):
        return None
    try:
        from lib.bm25_index import BM25Index

        bm25_path = os.path.join(resolve_path(config, "chroma_persist_dir"), "bm25.pkl")
        if not os.path.isfile(bm25_path):
            logger.warning("bm25_enabled=True but %s not found; skipping BM25", bm25_path)
            return None
        bm25 = BM25Index()
        bm25.load(bm25_path)
        logger.info("BM25 index loaded (%d docs)", len(bm25))
        return bm25
    except Exception as exc:
        logger.warning("Failed to load BM25 index: %s; falling back to vector-only", exc)
        return None


def _clip_image_enabled(config: dict) -> bool:
    return bool(config.get("clip_image_enabled", False))


def _init_clip_image_store(config: dict):
    if not _clip_image_enabled(config):
        return None

    from lib.embed_engine import CLIPEmbedEngine
    from lib.image_vector_db import ImageVectorDb

    clip_engine = CLIPEmbedEngine(
        model_name=config.get("clip_model_name", "openai/clip-vit-base-patch32")
    )
    return ImageVectorDb(
        persist_dir=resolve_path(config, "chroma_persist_dir"),
        embed_engine=clip_engine,
    )


def _init_query_enhancer(config: dict, LlmApi=None, allow_llm: bool = True):
    query_enhancer = None
    if not config.get("query_enhance_enabled", False):
        return query_enhancer

    enhancer_mode = config.get("enhancer_mode", "llm")
    if enhancer_mode == "offline_translate":
        from lib.query_enhancer import OfflineTranslator

        return OfflineTranslator(
            from_lang=config.get("translator_source_lang", "zh"),
            to_lang=config.get("translator_target_lang", "en"),
        )

    if not allow_llm:
        return query_enhancer

    if LlmApi is None:
        _, LlmApi, _ = _import_lib()
    from lib.query_enhancer import QueryEnhancer

    enhancer_llm = LlmApi(
        api_key=config["enhancer"]["api_key"],
        base_url=config["enhancer"]["api_base_url"],
        model=config["enhancer"]["model"],
        temperature=config["enhancer"].get("temperature", 0.0),
        thinking_mode=config["enhancer"].get("thinking_mode", False),
        timeout=_positive_int(config.get("llm_timeout_seconds"), 60),
    )
    return QueryEnhancer(enhancer_llm, docs_lang=config.get("docs_lang", "en"))


def _init_reranker(config: dict):
    if not config.get("rerank_enabled", False):
        return None
    from lib.reranker import Reranker

    return Reranker(
        model_name=config.get("rerank_model_name", "BAAI/bge-reranker-base")
    )


def _init_base_system(config: dict):
    """Load embedding model and vector store, shared by _init_ask_chat
    and _init_search_system."""
    EmbedEngine, _, VectorDb = _import_lib()

    t0 = time.perf_counter()
    print(">> Loading embedding model... ", end="", flush=True)
    embed_engine = EmbedEngine(model_name=config["embedding_model_name"])
    logger.info("Embedding model loaded: %s", config["embedding_model_name"])
    print(f"\r\033[K>> Loading embedding model... done  [{time.perf_counter() - t0:.1f}s]")

    t0 = time.perf_counter()
    print(">> Loading vector index... ", end="", flush=True)
    store = VectorDb(
        persist_dir=resolve_path(config, "chroma_persist_dir"),
        embed_engine=embed_engine,
    )
    logger.info("Vector store loaded, %d chunks", store.count())
    print(f"\r\033[K>> Loading vector index... done  [{time.perf_counter() - t0:.1f}s]")

    parent_store = None
    if config.get("parent_child_enabled", False):
        from lib.vector_db import ParentStore
        parent_store = ParentStore(persist_dir=resolve_path(config, "chroma_persist_dir"))
        logger.info("Parent store loaded, %d parent chunks", parent_store.count())

    return store, parent_store


def _init_multi_query_enhancer(config: dict, LlmApi=None):
    """Initialize multi-query enhancer if enabled. Returns None when disabled."""
    if not config.get("multi_query_enabled", False):
        return None
    if LlmApi is None:
        _, LlmApi, _ = _import_lib()
    from lib.query_enhancer import MultiQueryEnhancer

    llm = LlmApi(
        api_key=config["enhancer"]["api_key"],
        base_url=config["enhancer"]["api_base_url"],
        model=config["enhancer"]["model"],
        temperature=0.7,  # 多样性需要更高温度
        timeout=_positive_int(config.get("llm_timeout_seconds"), 60),
    )
    return MultiQueryEnhancer(
        llm_api=llm,
        n_queries=config.get("multi_query_n", 3),
        docs_lang=config.get("docs_lang", "en"),
    )


def _init_ask_chat(config: dict):
    store, parent_store = _init_base_system(config)
    _, LlmApi, _ = _import_lib()

    t0 = time.perf_counter()
    print(">> Initializing LLM... ", end="", flush=True)
    llm = LlmApi(
        api_key=config["llm"]["api_key"],
        base_url=config["llm"]["api_base_url"],
        model=config["llm"]["model"],
        temperature=config["llm"].get("temperature", 0.3),
        thinking_mode=config["llm"].get("thinking_mode", False),
        timeout=_positive_int(config.get("llm_timeout_seconds"), 60),
    )
    print(f"\r\033[K>> Initializing LLM... done  [{time.perf_counter() - t0:.1f}s]")

    query_enhancer = _init_query_enhancer(config, LlmApi=LlmApi, allow_llm=True)
    multi_query_enhancer = _init_multi_query_enhancer(config, LlmApi=LlmApi)
    reranker = _init_reranker(config)
    bm25_index = _load_bm25_index(config)

    system_prompt = _build_system_prompt(
        config.get("system_rules", ""), config.get("strict_context", False)
    )

    return store, parent_store, llm, query_enhancer, multi_query_enhancer, system_prompt, reranker, bm25_index


def _init_search_system(config: dict):
    store, parent_store = _init_base_system(config)

    query_enhancer = _init_query_enhancer(config, allow_llm=False)
    multi_query_enhancer = _init_multi_query_enhancer(config)
    reranker = _init_reranker(config)
    bm25_index = _load_bm25_index(config)

    return store, parent_store, query_enhancer, multi_query_enhancer, reranker, bm25_index


def _retrieve_context_chunks(
    store,
    question: str,
    config: dict,
    query_enhancer=None,
    messages_history=None,
    reranker=None,
    bm25_index=None,
    parent_store=None,
    multi_query_enhancer=None,
    final_status: str = "Generating...",
):
    """Retrieve relevant chunks from the store without building LLM messages.

    Parameters
    ----------
    store : VectorDb
        Vector store with a ``query(question, k)`` method.
    question : str
        User's original question.
    config : dict
        Configuration dict that may include ``retrieval_k``, ``rerank_top_n``,
        ``retrieval_candidate_k``.
    query_enhancer : optional
        Enhancer with an ``enhance(question, history)`` method.
    messages_history : optional
        Previous chat messages (list of dicts) passed to the query enhancer.
    reranker : optional
        Reranker with a ``rerank(query, items, top_n, translated_query)`` method.
    bm25_index : optional
        BM25 index with ``is_loaded()`` and ``query(question, k)`` methods.

    Returns
    -------
    tuple[list[dict], str]
        (chunks, rewritten_question).  Chunks may be empty when nothing is found.
        Each chunk dict includes a ``retrieval_path`` label when non-empty.
    """
    rewritten_question = question

    print(">> Processing... ", end="", flush=True)
    logger.info("Question: %s", question)

    if query_enhancer:
        rewritten_question = query_enhancer.enhance(question, messages_history)
        if rewritten_question != question:
            logger.info("Enhanced question: %s", rewritten_question)

    print("\r\033[K>> Retrieving... ", end="", flush=True)

    retrieval_k = int(config.get("retrieval_k", 5))
    rerank_top_n = int(config.get("rerank_top_n", 5))
    retrieval_candidate_k = config.get("retrieval_candidate_k")

    fetch_k = _positive_int(retrieval_candidate_k, retrieval_k * 3) if reranker else retrieval_k

    # ── Multi-query retrieval ──
    bm25_applied = False
    if multi_query_enhancer is not None:
        queries = multi_query_enhancer.generate_queries(rewritten_question)
        logger.info("Multi-query: %d queries generated", len(queries))

        all_chunks: list[dict] = []
        seen_texts: set[str] = set()

        if bm25_index is not None and bm25_index.is_loaded():
            # Multi-query + BM25: RRF fusion per query, then global dedup
            from lib.hybrid_retriever import reciprocal_rank_fusion

            for q in queries:
                q_chunks = store.query(q, k=fetch_k)
                bm25_chunks = bm25_index.query(q, k=fetch_k)
                fused = reciprocal_rank_fusion(q_chunks, bm25_chunks, top_n=fetch_k)
                for chunk in fused:
                    text_key = chunk.get("text", "")[:100]
                    if text_key not in seen_texts:
                        seen_texts.add(text_key)
                        all_chunks.append(chunk)
            bm25_applied = True
            logger.info(
                "Multi-query hybrid RRF: %d unique fused chunks across %d queries",
                len(all_chunks), len(queries),
            )
        else:
            # Vector-only multi-query (unchanged)
            for q in queries:
                q_chunks = store.query(q, k=fetch_k)
                for chunk in q_chunks:
                    text_key = chunk.get("text", "")[:100]
                    if text_key not in seen_texts:
                        seen_texts.add(text_key)
                        all_chunks.append(chunk)

        chunks = all_chunks
        logger.info("Multi-query merged: %d unique chunks", len(chunks))
    else:
        # ── Single-query retrieval (original path) ──
        chunks = store.query(rewritten_question, k=fetch_k)

        if bm25_index is not None and bm25_index.is_loaded():
            bm25_chunks = bm25_index.query(rewritten_question, k=fetch_k)
            if bm25_chunks:
                from lib.hybrid_retriever import reciprocal_rank_fusion

                n_vector = len(chunks)
                rrf_top = fetch_k if reranker else retrieval_k
                chunks = reciprocal_rank_fusion(chunks, bm25_chunks, top_n=rrf_top)
                bm25_applied = True
                logger.info(
                    "Hybrid RRF: %d vector + %d BM25 -> %d fused",
                    n_vector,
                    len(bm25_chunks),
                    len(chunks),
                )

    if not chunks:
        print("\r\033[K>> No relevant chunks found. Skipping.\n")
        logger.warning("No relevant chunks found.")
        return [], rewritten_question

    if reranker:
        chunks = reranker.rerank(
            question, chunks, top_n=rerank_top_n, translated_query=rewritten_question
        )
        retrieval_path = "vector+bm25+rerank" if bm25_applied else "vector+rerank"
    else:
        retrieval_path = "vector+bm25" if bm25_applied else "vector"

    for chunk in chunks:
        chunk["retrieval_path"] = retrieval_path

    # ── Parent-child: replace child text with parent text ──
    if parent_store is not None and chunks:
        parent_ids = []
        seen_parent_ids = set()
        for chunk in chunks:
            # Support both flat (VectorDb.query) and nested (load_documents) formats.
            meta = chunk.get("metadata", {})
            pid = chunk.get("parent_id") or meta.get("parent_id")
            if pid and pid not in seen_parent_ids:
                parent_ids.append(pid)
                seen_parent_ids.add(pid)

        if parent_ids:
            parent_chunks = parent_store.get_by_parent_ids(parent_ids)
            pid_to_parent = {p["metadata"]["parent_id"]: p for p in parent_chunks}
            expanded_chunks = []
            for chunk in chunks:
                meta = chunk.get("metadata", {})
                pid = chunk.get("parent_id") or meta.get("parent_id")
                if pid and pid in pid_to_parent:
                    parent = pid_to_parent[pid]
                    merged = dict(parent)
                    parent_meta = parent.get("metadata", {})
                    merged["source"] = parent_meta.get("source", chunk.get("source", "unknown"))
                    merged["file_type"] = parent_meta.get("file_type", chunk.get("file_type"))
                    merged["chunk_index"] = parent_meta.get("chunk_index", chunk.get("chunk_index"))
                    merged["page"] = parent_meta.get("page", chunk.get("page"))
                    merged["parent_id"] = parent_meta.get("parent_id", pid)
                    merged["chunk_role"] = parent_meta.get("chunk_role", "parent")
                    merged["retrieval_path"] = chunk.get("retrieval_path", "")
                    merged["distance"] = chunk.get("distance")
                    if "rerank_score" in chunk:
                        merged["rerank_score"] = chunk["rerank_score"]
                    if "rrf_score" in chunk:
                        merged["rrf_score"] = chunk["rrf_score"]
                    expanded_chunks.append(merged)
                else:
                    expanded_chunks.append(chunk)
            chunks = expanded_chunks
            logger.info("Parent-child: expanded %d child chunks to parent context", len(chunks))

    suffix = f" {final_status}" if final_status else ""
    print(f"\r\033[K>> Retrieved {len(chunks)} chunks.{suffix}")
    logger.info("Retrieved %d chunks", len(chunks))

    return chunks, rewritten_question


def _retrieve_context(
    store,
    llm,
    question: str,
    system_prompt: str,
    retrieval_k: int,
    query_enhancer=None,
    messages_history=None,
    reranker=None,
    rerank_top_n: int = 5,
    max_context_chars: int = 6000,
    bm25_index=None,
    retrieval_candidate_k: int | None = None,
    parent_store=None,
    multi_query_enhancer=None,
):
    # Delegate retrieval to the new helper
    config = {
        "retrieval_k": retrieval_k,
        "rerank_top_n": rerank_top_n,
        "retrieval_candidate_k": retrieval_candidate_k,
    }
    chunks, rewritten_question = _retrieve_context_chunks(
        store,
        question,
        config,
        query_enhancer=query_enhancer,
        messages_history=messages_history,
        reranker=reranker,
        bm25_index=bm25_index,
        parent_store=parent_store,
        multi_query_enhancer=multi_query_enhancer,
    )

    if not chunks:
        return [], None, rewritten_question

    context_parts = []
    used_chunks = []
    total_chars = 0
    max_context_chars = max(1, int(max_context_chars))
    for item in chunks:
        citation = _format_source_citation(item)
        entry = f"{citation}\n{item['text']}"
        if context_parts and total_chars + 2 + len(entry) > max_context_chars:
            break
        if not context_parts and len(entry) > max_context_chars:
            entry = entry[:max_context_chars]
        context_parts.append(entry)
        used_chunks.append(item)
        # Accumulate separator cost (\n\n between entries) for all but the first entry
        separator = 2 if len(context_parts) > 1 else 0
        total_chars += len(entry) + separator
    context = "\n\n".join(context_parts)

    messages = [{"role": "system", "content": system_prompt}]
    if messages_history:
        messages.extend(messages_history)
    messages.append(
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        }
    )

    return used_chunks, messages, rewritten_question
