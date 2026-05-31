"""
rag_runner.py
CLI entrypoint for building, retrieving, asking, and chatting with the RAG index.
"""
import json
import os
import sys
import time

from lib.config import PROJECT_DIR as _PROJECT_DIR
from lib.config import apply_kb_overlay
from lib.config import load_config
from lib.config import resolve_path as _resolve_path
from lib.config import validate_kb_name
from lib.doc_loader import load_documents
from lib.file_index import (
    _build_and_save_file_index,
    _compute_sha256,
    _load_file_index,
    _save_file_index,
    _walk_supported_files,
)
from lib.image_indexing import _init_image_captioner, _rebuild_clip_image_index
from lib.kb_status import print_doctor_report
from lib.logger import get_logger
from lib.output_writer import (
    _cleanup_output_dirs,
    _export_round,
    _format_source_citation,
    _get_enhance_label,
    _init_output_dir,
    _sanitize_chunk,
    _sanitize_name,
)
from lib.pipeline import (
    _build_system_prompt,
    _import_lib,
    _init_ask_chat,
    _init_clip_image_store,
    _init_query_enhancer,
    _init_reranker,
    _init_search_system,
    _load_bm25_index,
    _positive_int,
    _retrieve_context,
    _retrieve_context_chunks,
)

logger = get_logger(__name__)

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")
def cmd_build(config: dict) -> None:
    EmbedEngine, _, VectorDb = _import_lib()
    t0 = time.perf_counter()

    docs_dir = _resolve_path(config, "docs_dir")
    persist_dir = _resolve_path(config, "chroma_persist_dir")
    model_name = config["embedding_model_name"]

    if not os.path.isdir(docs_dir):
        print(f">> Error: documents directory not found: {docs_dir}")
        sys.exit(1)

    image_captioner = _init_image_captioner(config)
    current_sources = {
        os.path.relpath(path, docs_dir)
        for path in _walk_supported_files(docs_dir)
    }

    print(">> Loading and chunking documents... ", end="", flush=True)
    t1 = time.perf_counter()

    parent_child_enabled = config.get("parent_child_enabled", False)
    if parent_child_enabled:
        child_chunk_size = config.get("child_chunk_size", 200)
        parent_chunk_size = config.get("chunk_size", 800)
        all_chunks = load_documents(
            docs_dir,
            chunk_size=child_chunk_size,
            chunk_overlap=config.get("child_chunk_overlap", 30),
            show_progress=True,
            image_captioner=image_captioner,
            docs_lang=config.get("docs_lang", "zh"),
            parent_chunk_size=parent_chunk_size,
        )
    else:
        all_chunks = load_documents(
            docs_dir,
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"],
            show_progress=True,
            image_captioner=image_captioner,
            docs_lang=config.get("docs_lang", "zh"),
        )

    if not all_chunks:
        print("\r\033[K>> No supported files found in documents directory.")
        sys.exit(1)

    if parent_child_enabled:
        chunks = [c for c in all_chunks if c["metadata"].get("chunk_role") == "child"]
        parent_chunks = [c for c in all_chunks if c["metadata"].get("chunk_role") == "parent"]
    else:
        chunks = all_chunks
        parent_chunks = []

    sources = {c["metadata"]["source"] for c in chunks}
    print(
        f"\r\033[K>> Loaded {len(chunks)} chunks from {len(sources)} files"
        f"  [{time.perf_counter() - t1:.1f}s]"
    )
    logger.info(f"Loaded {len(chunks)} chunks from {len(sources)} files")

    print(">> Loading embedding model... ", end="", flush=True)
    t2 = time.perf_counter()
    embed_engine = EmbedEngine(model_name=model_name)
    print(f"\r\033[K>> Loading embedding model... done  [{time.perf_counter() - t2:.1f}s]")

    print(">> Building vector index... ", end="", flush=True)
    t3 = time.perf_counter()
    store = VectorDb(persist_dir=persist_dir, embed_engine=embed_engine)
    store.rebuild(chunks)
    print(f"\r\033[K>> Building vector index... done  [{time.perf_counter() - t3:.1f}s]")

    # Build parent store when parent-child mode is enabled.
    if parent_child_enabled and parent_chunks:
        from lib.vector_db import ParentStore
        print(">> Building parent chunk index... ", end="", flush=True)
        t_pc = time.perf_counter()
        parent_store = ParentStore(persist_dir=persist_dir)
        parent_store.rebuild(parent_chunks)
        print(
            f"\r\033[K>> Building parent chunk index... done  [{time.perf_counter() - t_pc:.1f}s]"
            f"  ({len(parent_chunks)} parents)"
        )
        logger.info("Parent store built with %d parent chunks", len(parent_chunks))

    # Build the BM25 keyword index alongside the vector index.
    if config.get("bm25_enabled", False):
        from lib.bm25_index import BM25Index

        print(">> Building BM25 index... ", end="", flush=True)
        t4 = time.perf_counter()
        bm25 = BM25Index()
        bm25.build(chunks)
        bm25_path = os.path.join(persist_dir, "bm25.pkl")
        os.makedirs(persist_dir, exist_ok=True)
        bm25.save(bm25_path)
        print(
            f"\r\033[K>> Building BM25 index... done  [{time.perf_counter() - t4:.1f}s]"
            f"  ({len(bm25)} docs)"
        )
        logger.info(f"BM25 index saved to {bm25_path} ({len(bm25)} docs)")

    # Save source fingerprints for future incremental builds.
    _build_and_save_file_index(persist_dir, docs_dir, chunks)

    _rebuild_clip_image_index(config, docs_dir, persist_dir)

    print(f"\r\033[K>> Build complete  [{time.perf_counter() - t0:.1f}s total]")
    logger.info("Build complete")


def cmd_ask(config: dict, question: str) -> None:
    store, parent_store, llm, query_enhancer, multi_query_enhancer, system_prompt, reranker, bm25_index = _init_ask_chat(config)

    chunks, messages, rewritten_question = _retrieve_context(
        store, llm, question, system_prompt,
        config.get("retrieval_k", 5),
        query_enhancer,
        reranker=reranker,
        rerank_top_n=config.get("rerank_top_n", 5),
        max_context_chars=config.get("max_context_chars", 6000),
        bm25_index=bm25_index,
        retrieval_candidate_k=config.get("retrieval_candidate_k"),
        parent_store=parent_store,
        multi_query_enhancer=multi_query_enhancer,
    )
    if not chunks:
        return

    answer = ""
    for token in llm.generate_stream(messages):
        print(token, end="", flush=True)
        answer += token
    print()

    print("\n-- Source Citations --")
    seen = set()
    for chunk in chunks:
        citation = _format_source_citation(chunk)
        if citation not in seen:
            print(f"  {citation}")
            seen.add(citation)

    out_dir = _init_output_dir(question, config.get("max_output_dirs", 50))
    _export_round(
        out_dir,
        1,
        question,
        chunks,
        answer,
        rewritten_question,
        _get_enhance_label(query_enhancer),
    )
    print(f"\nSaved to {out_dir}")
    logger.info(f"Answer saved to {out_dir}")


def cmd_retrieve(config: dict, question: str) -> None:
    if not question.strip():
        print(">> Error: retrieve question cannot be empty.")
        sys.exit(1)

    store, parent_store, query_enhancer, multi_query_enhancer, reranker, bm25_index = (
        _init_search_system(config)
    )

    chunks, rewritten_question = _retrieve_context_chunks(
        store,
        question,
        config,
        query_enhancer=query_enhancer,
        reranker=reranker,
        bm25_index=bm25_index,
        parent_store=parent_store,
        multi_query_enhancer=multi_query_enhancer,
        final_status="",
    )

    if not chunks:
        print(">> No relevant chunks found. Build the index with: python rag_runner.py --build")
        return

    if query_enhancer:
        if rewritten_question != question:
            label = _get_enhance_label(query_enhancer)
            print(f">> {label}: {rewritten_question}")
        else:
            print(">> (enhancer applied, no change)")

    print(f"\nQuestion: {question}\n")
    for i, chunk in enumerate(chunks, start=1):
        citation = _format_source_citation(chunk)
        rrf_score = chunk.get("rrf_score")
        rerank_score = chunk.get("rerank_score")
        distance = chunk.get("distance")
        score_parts = []
        if rrf_score is not None:
            score_parts.append(f"rrf_score={rrf_score:.4f}")
        if rerank_score is not None:
            score_parts.append(f"rerank_score={rerank_score:.4f}")
        if distance is not None:
            score_parts.append(f"distance={distance}")
        score_info = " | " + " | ".join(score_parts) if score_parts else ""
        text = _sanitize_chunk(chunk.get("text", ""))
        print(f"## Chunk {i} {citation}{score_info}\n")
        print("```text")
        print(text)
        print("```\n")


def cmd_chat(config: dict) -> None:
    store, parent_store, llm, query_enhancer, multi_query_enhancer, system_prompt, reranker, bm25_index = _init_ask_chat(config)

    print("\nReady. Type your question (or /exit /quit /q to quit).\n")

    out_dir = None
    round_index = 0
    history = []

    while True:
        try:
            question = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not question:
            continue
        if question in ("/exit", "/quit", "/q"):
            break

        chunks, messages, rewritten_question = _retrieve_context(
            store, llm, question, system_prompt,
            config.get("retrieval_k", 5),
            query_enhancer,
            messages_history=history,
            reranker=reranker,
            rerank_top_n=config.get("rerank_top_n", 5),
            max_context_chars=config.get("max_context_chars", 6000),
            bm25_index=bm25_index,
            retrieval_candidate_k=config.get("retrieval_candidate_k"),
            parent_store=parent_store,
        )
        if not chunks:
            continue

        answer = ""
        for token in llm.generate_stream(messages):
            print(token, end="", flush=True)
            answer += token
        print()

        print("\n-- Source Citations --")
        seen = set()
        for chunk in chunks:
            citation = _format_source_citation(chunk)
            if citation not in seen:
                print(f"  {citation}")
                seen.add(citation)
        print()

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": answer})

        # Keep only the most recent turns to avoid overlong chat context.
        max_history_turns = config.get("max_history_turns", 10)
        if len(history) > max_history_turns * 2:
            history = history[-(max_history_turns * 2):]

        if out_dir is None:
            out_dir = _init_output_dir(question, config.get("max_output_dirs", 50))
        round_index += 1
        _export_round(
            out_dir,
            round_index,
            question,
            chunks,
            answer,
            rewritten_question,
            _get_enhance_label(query_enhancer),
        )


def cmd_build_incremental(config: dict) -> None:
    """Incrementally index new, modified, and deleted documents."""
    EmbedEngine, _, VectorDb = _import_lib()
    t0 = time.perf_counter()

    docs_dir = _resolve_path(config, "docs_dir")
    persist_dir = _resolve_path(config, "chroma_persist_dir")
    model_name = config["embedding_model_name"]

    if not os.path.isdir(docs_dir):
        print(f">> Error: documents directory not found: {docs_dir}")
        sys.exit(1)

    image_captioner = _init_image_captioner(config)

    print(">> Scanning documents for changes... ", end="", flush=True)
    t1 = time.perf_counter()
    supported_paths = _walk_supported_files(docs_dir)
    current_sources: set[str] = set()
    current_fingerprints: dict[str, str] = {}
    for filepath in supported_paths:
        relpath = os.path.relpath(filepath, docs_dir)
        current_sources.add(relpath)
        current_fingerprints[relpath] = _compute_sha256(filepath)
    print(
        f"\r\033[K>> Scanned {len(current_sources)} files"
        f"  [{time.perf_counter() - t1:.1f}s]"
    )

    file_index = _load_file_index(persist_dir)
    indexed_sources = set(file_index.keys())

    new_sources = current_sources - indexed_sources
    deleted_sources = indexed_sources - current_sources
    modified_sources: set[str] = set()
    for source in current_sources & indexed_sources:
        if file_index[source].get("sha256") != current_fingerprints[source]:
            modified_sources.add(source)
    unchanged_sources = current_sources - new_sources - modified_sources

    changed_sources = new_sources | modified_sources
    removed_sources = deleted_sources | modified_sources  # modified = delete old, add new

    if file_index:
        print(
            f">> {len(new_sources)} new, {len(modified_sources)} modified, "
            f"{len(deleted_sources)} deleted, {len(unchanged_sources)} unchanged"
        )

    if not changed_sources and not deleted_sources:
        print(">> No changes detected.")
        logger.info("Incremental build: no changes detected")
        return

    print(">> Loading and chunking documents... ", end="", flush=True)
    t2 = time.perf_counter()
    parent_child_enabled = config.get("parent_child_enabled", False)
    if parent_child_enabled:
        child_chunk_size = config.get("child_chunk_size", 200)
        parent_chunk_size = config.get("chunk_size", 800)
        all_chunks = load_documents(
            docs_dir,
            chunk_size=child_chunk_size,
            chunk_overlap=config.get("child_chunk_overlap", 30),
            image_captioner=image_captioner,
            docs_lang=config.get("docs_lang", "zh"),
            only_sources=changed_sources,
            parent_chunk_size=parent_chunk_size,
        )
    else:
        all_chunks = load_documents(
            docs_dir,
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"],
            image_captioner=image_captioner,
            docs_lang=config.get("docs_lang", "zh"),
            only_sources=changed_sources,
        )

    if parent_child_enabled:
        changed_chunks = [c for c in all_chunks if c["metadata"].get("chunk_role") == "child"]
        changed_parent_chunks = [c for c in all_chunks if c["metadata"].get("chunk_role") == "parent"]
    else:
        changed_chunks = all_chunks
        changed_parent_chunks = []
    print(
        f"\r\033[K>> Loaded {len(changed_chunks)} chunks from {len(changed_sources)} changed files"
        f"  [{time.perf_counter() - t2:.1f}s]"
    )

    print(">> Loading embedding model... ", end="", flush=True)
    t3 = time.perf_counter()
    embed_engine = EmbedEngine(model_name=model_name)
    print(f"\r\033[K>> Loading embedding model... done  [{time.perf_counter() - t3:.1f}s]")

    store = VectorDb(persist_dir=persist_dir, embed_engine=embed_engine)

    # Fallback when file_index.json is absent: query indexed sources.
    if not file_index:
        store_indexed = store.get_indexed_sources()
        if store_indexed:
            new_sources = current_sources - store_indexed
            deleted_sources = store_indexed - current_sources
            modified_sources = set()  # Can't detect modifications without old SHA
            unchanged_sources = current_sources - new_sources

            changed_sources = new_sources | modified_sources
            removed_sources = deleted_sources | modified_sources

            # Re-filter changed_chunks to exclude unchanged sources
            changed_chunks = [
                c for c in all_chunks
                if c["metadata"]["source"] in changed_sources
                and c["metadata"].get("chunk_role", "child") == "child"
            ]
            changed_parent_chunks = [
                c for c in all_chunks
                if c["metadata"]["source"] in changed_sources
                and c["metadata"].get("chunk_role") == "parent"
            ]

            # Seed file_index for current files so future runs detect modifications
            file_index = {}
            for source in current_sources:
                source_chunk_count = sum(
                    1 for c in all_chunks if c["metadata"]["source"] == source
                )
                file_index[source] = {
                    "sha256": current_fingerprints[source],
                    "chunk_count": source_chunk_count,
                }

            if not changed_sources and not deleted_sources:
                _save_file_index(persist_dir, file_index)
                print(f">> file_index.json created ({len(file_index)} sources); no changes detected.")
                logger.info("Incremental build: file_index created; no changes detected")
                return

            print(
                f">> Fallback: {len(store_indexed)} sources already indexed in store; "
                f"{len(new_sources)} new, {len(deleted_sources)} deleted, "
                f"{len(unchanged_sources)} unchanged"
            )

    # Update the BM25 keyword index.
    bm25_index = None
    bm25_path = os.path.join(persist_dir, "bm25.pkl")
    if config.get("bm25_enabled", False) and os.path.isfile(bm25_path):
        bm25_index = _load_bm25_index(config)
    elif config.get("bm25_enabled", False) and removed_sources:
        # Load the existing BM25 index so removed sources can be deleted.
        bm25_index = _load_bm25_index(config)
    # Create a BM25 index when adding chunks to a missing keyword index.
    if config.get("bm25_enabled", False) and bm25_index is None and changed_chunks:
        try:
            from lib.bm25_index import BM25Index
            bm25_index = BM25Index()
            # Update the BM25 keyword index.
            if unchanged_sources:
                # Load unchanged chunks separately (all_chunks only has changed sources).
                unchanged_chunks = load_documents(
                    docs_dir,
                    chunk_size=config["chunk_size"],
                    chunk_overlap=config["chunk_overlap"],
                    image_captioner=image_captioner,
                    docs_lang=config.get("docs_lang", "zh"),
                    only_sources=unchanged_sources,
                )
                if unchanged_chunks:
                    bm25_index.build(unchanged_chunks)
        except Exception:
            bm25_index = None

    # Initialize parent store for incremental updates if needed.
    parent_store = None
    if parent_child_enabled:
        from lib.vector_db import ParentStore
        parent_store = ParentStore(persist_dir=persist_dir)

    if removed_sources:
        print(f">> Removing old entries for {len(removed_sources)} sources...")
        for source in sorted(removed_sources):
            deleted_count = store.delete_by_source(source)
            if bm25_index is not None and bm25_index.is_loaded():
                bm25_index.delete_by_source(source)
            if parent_store is not None:
                parent_store.delete_by_source(source)
            print(f"   removed {source} ({deleted_count} chunks)")

    if changed_chunks:
        print(
            f">> Adding {len(changed_chunks)} chunks from {len(changed_sources)} sources... ",
            end="", flush=True,
        )
        t4 = time.perf_counter()
        store.add_chunks(changed_chunks)
        if bm25_index is not None:
            bm25_index.add_chunks(changed_chunks)
        if parent_store is not None and changed_parent_chunks:
            parent_store.add_chunks(changed_parent_chunks)
        print(
            f"\r\033[K>> Added {len(changed_chunks)} chunks"
            f"  [{time.perf_counter() - t4:.1f}s]"
        )

    for source in deleted_sources:
        file_index.pop(source, None)
    for source in changed_sources:
        source_chunk_count = sum(
            1 for c in all_chunks if c["metadata"]["source"] == source
        )
        file_index[source] = {
            "sha256": current_fingerprints[source],
            "chunk_count": source_chunk_count,
        }
    _save_file_index(persist_dir, file_index)

    # Update the BM25 keyword index.
    if bm25_index is not None:
        os.makedirs(persist_dir, exist_ok=True)
        bm25_index.save(bm25_path)
        logger.info("BM25 index saved (%d docs)", len(bm25_index))

    # Rebuild the optional CLIP image index.
    _rebuild_clip_image_index(config, docs_dir, persist_dir)

    print(f"\r\033[K>> Incremental build complete  [{time.perf_counter() - t0:.1f}s total]")
    logger.info(
        "Incremental build: +%d -%d ~%d sources, %d chunks added",
        len(new_sources),
        len(deleted_sources),
        len(modified_sources),
        len(changed_chunks),
    )


def cmd_list_sources(config: dict) -> None:
    import chromadb
    from chromadb.config import Settings

    persist_dir = _resolve_path(config, "chroma_persist_dir")
    try:
        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_collection(name="documents")
    except Exception:
        print(">> No indexed sources found (collection does not exist).")
        return
    result = collection.get(include=["metadatas"])
    stats: dict[str, int] = {}
    for meta in result["metadatas"]:
        if not meta:
            continue
        source = meta.get("source", "unknown")
        stats[source] = stats.get(source, 0) + 1
    total_chunks = sum(stats.values())
    print(f">> Indexed {len(stats)} files, {total_chunks} chunks:")
    for source, count in sorted(stats.items()):
        print(f"   {source} ({count} chunks)")


def cmd_gaps(config: dict) -> None:
    from collections import Counter

    path = os.path.join(_PROJECT_DIR, "logs", "knowledge_gaps.jsonl")
    if not os.path.exists(path):
        print(">> No knowledge gap records found.")
        return

    active_kb = config.get("_active_kb_name", "default")

    questions = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            record_kb = item.get("kb", "default")
            if record_kb != active_kb:
                continue
            question = item.get("original")
            if question:
                questions.append(question)

    counter = Counter(questions)
    print(f">> {len(questions)} gap records, {len(counter)} unique questions:\n")
    for question, count in counter.most_common(20):
        print(f"  ({count}x) {question}")


def _parse_cli_overrides(config: dict) -> None:
    """Parse global query-time CLI overrides from *sys.argv* before command dispatch.

    Mutates *sys.argv* in place, removing recognised flags, and updates
    *config* with the parsed values.  On invalid or missing numeric
    arguments the function prints an error and calls ``sys.exit(1)``.

    Supported flags (usable before or after the command/question):

    * ``--retrieval-k N`` / ``--retrieval_k N``
        Set ``config['retrieval_k'] = N`` (must be a positive integer).
    * ``--max-context-chars N`` / ``--max_context_chars N``
        Set ``config['max_context_chars'] = N`` (must be a positive integer).
    * ``--strict-context`` / ``--strict_context``
        Set ``config['strict_context'] = True``.
    * ``--no-strict-context`` / ``--no_strict_context``
        Set ``config['strict_context'] = False``.
    """
    args = sys.argv[1:]
    remaining: list[str] = []
    i = 0
    while i < len(args):
        arg = args[i]

        if arg in ("--retrieval-k", "--retrieval_k"):
            if i + 1 >= len(args):
                print(">> Error: --retrieval-k/--retrieval_k requires a positive integer value.")
                sys.exit(1)
            try:
                val = int(args[i + 1])
                if val <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                print(
                    f">> Error: --retrieval-k/--retrieval_k requires a positive integer,"
                    f" got '{args[i + 1]}'."
                )
                sys.exit(1)
            config["retrieval_k"] = val
            i += 2
            continue

        if arg in ("--max-context-chars", "--max_context_chars"):
            if i + 1 >= len(args):
                print(">> Error: --max-context-chars/--max_context_chars requires a positive integer value.")
                sys.exit(1)
            try:
                val = int(args[i + 1])
                if val <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                print(
                    f">> Error: --max-context-chars/--max_context_chars requires a positive integer,"
                    f" got '{args[i + 1]}'."
                )
                sys.exit(1)
            config["max_context_chars"] = val
            i += 2
            continue

        if arg in ("--strict-context", "--strict_context"):
            config["strict_context"] = True
            i += 1
            continue

        if arg in ("--no-strict-context", "--no_strict_context"):
            config["strict_context"] = False
            i += 1
            continue

        remaining.append(arg)
        i += 1

    sys.argv = [sys.argv[0]] + remaining


def main() -> None:
    try:
        config = load_config()
    except FileNotFoundError:
        print(">> Fatal: config.json not found.")
        print("   Copy config_example.json to config.json and adjust settings.")
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f">> Fatal: config.json is invalid JSON: {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f">> Fatal: failed to load config: {exc}")
        sys.exit(1)

    # Parse global query-time CLI overrides before command dispatch.
    _parse_cli_overrides(config)

    # ── Parse --kb NAME overlay ─────────────────────────────────────────
    kb_name = None
    for i, arg in enumerate(sys.argv[1:], start=1):
        if arg == "--kb":
            if i + 1 >= len(sys.argv) or sys.argv[i + 1].startswith("-"):
                print(">> Error: --kb requires a knowledge-base name.")
                sys.exit(1)
            kb_name = sys.argv[i + 1]
            # Remove both --kb and its value from argv.
            del sys.argv[i : i + 2]  # noqa: E203
            break

    if kb_name is not None:
        try:
            validate_kb_name(kb_name)
        except ValueError as exc:
            print(f">> Error: --kb {exc}")
            sys.exit(1)
        config = apply_kb_overlay(config, kb_name)

    config["_active_kb_name"] = kb_name if kb_name is not None else "default"

    # ── Parse remaining args ────────────────────────────────────────────
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--doctor":
            print_doctor_report(config)
            sys.exit(0)
        elif cmd == "--build":
            cmd_build(config)
        elif cmd in ("--build-incremental", "--build-clean"):
            cmd_build_incremental(config)
        elif cmd == "--list-sources":
            cmd_list_sources(config)
        elif cmd == "--gaps":
            cmd_gaps(config)
        elif cmd == "--retrieve":
            cmd_retrieve(config, " ".join(sys.argv[2:]))
        else:
            cmd_ask(config, " ".join(sys.argv[1:]))
    else:
        cmd_chat(config)


if __name__ == "__main__":
    main()
