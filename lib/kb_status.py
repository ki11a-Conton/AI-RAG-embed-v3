"""
Lightweight knowledge-base status helpers.

These functions inspect paths and index metadata without loading embedding
models, LLM clients, rerankers, or BM25 indexes. They are shared by
``rag_runner.py --doctor`` and the Streamlit sidebar.
"""
import json
import os

from lib.config import resolve_path
from lib.doc_loader import SUPPORTED_EXTENSIONS


def _redact_key(value: str) -> str:
    """Return a short redacted representation of an API key."""
    if not value:
        return "(not set)"
    if _is_placeholder_key(value):
        return "(placeholder)"
    if len(value) <= 8:
        return "***"
    return value[:4] + "****" + value[-4:]


def _is_placeholder_key(value: str) -> bool:
    lowered = value.strip().lower()
    return (
        lowered in {"your-llm-api-key", "your-enhancer-api-key", "your-api-key"}
        or lowered.startswith("your-")
        or "your-" in lowered
        or lowered.startswith("placeholder")
    )


def _count_supported_files(docs_dir: str) -> int:
    count = 0
    for root, _, files in os.walk(docs_dir):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                count += 1
    return count


def _read_file_index(persist_dir: str) -> tuple[bool, int | None, int | None]:
    path = os.path.join(persist_dir, "file_index.json")
    if not os.path.isfile(path):
        return False, None, None
    try:
        with open(path, "r", encoding="utf-8") as f:
            file_index = json.load(f)
    except (OSError, json.JSONDecodeError):
        return True, None, None
    source_count = len(file_index)
    chunk_count = sum(item.get("chunk_count", 0) for item in file_index.values())
    return True, source_count, chunk_count


def _read_chroma_count(persist_dir: str) -> tuple[bool, int | None]:
    if not os.path.isdir(persist_dir):
        return False, None
    try:
        import chromadb
        from chromadb.config import Settings

        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        collection = client.get_collection(name="documents")
        return True, collection.count()
    except Exception:
        return False, None


def get_kb_status(config: dict) -> dict:
    """Return knowledge-base status without loading heavyweight models."""
    docs_dir = resolve_path(config, "docs_dir")
    persist_dir = resolve_path(config, "chroma_persist_dir")

    docs_dir_exists = os.path.isdir(docs_dir)
    docs_file_count = _count_supported_files(docs_dir) if docs_dir_exists else 0

    file_index_exists, source_count, chunk_count = _read_file_index(persist_dir)
    chroma_available, chroma_count = _read_chroma_count(persist_dir)
    if chunk_count is None:
        chunk_count = chroma_count

    bm25_file_exists = os.path.isfile(os.path.join(persist_dir, "bm25.pkl"))
    llm_config = config.get("llm", {}) or {}
    llm_key = llm_config.get("api_key", "")

    return {
        "docs_dir": docs_dir,
        "docs_dir_exists": docs_dir_exists,
        "docs_file_count": docs_file_count,
        "chroma_persist_dir": persist_dir,
        "chroma_persist_dir_exists": os.path.isdir(persist_dir),
        "chroma_collection_available": chroma_available,
        "chroma_source_count": source_count,
        "chroma_chunk_count": chunk_count,
        "file_index_exists": file_index_exists,
        "bm25_file_exists": bm25_file_exists,
        "bm25_enabled_in_config": bool(config.get("bm25_enabled", False)),
        "llm_configured": bool(llm_key) and not _is_placeholder_key(llm_key),
        "llm_api_key_redacted": _redact_key(llm_key),
        "embedding_model": config.get("embedding_model_name", "N/A"),
    }


def print_doctor_report(config: dict) -> None:
    """Print a concise human-readable status report."""
    status = get_kb_status(config)

    source_count = status["chroma_source_count"]
    chunk_count = status["chroma_chunk_count"]
    bm25_status = (
        "available"
        if status["bm25_file_exists"]
        else "not built (run --build with bm25_enabled=true)"
    )

    lines = [
        "=" * 56,
        "  AI-RAG-embed - Doctor Report",
        "=" * 56,
        "",
        "--- Configuration ---",
        f"  Embedding model   : {status['embedding_model']}",
        f"  BM25 enabled      : {status['bm25_enabled_in_config']}",
        f"  LLM API key       : {status['llm_api_key_redacted']}",
        f"  LLM configured    : {status['llm_configured']}",
        "",
        "--- Documents ---",
        f"  docs_dir          : {status['docs_dir']}",
        f"  Directory exists  : {status['docs_dir_exists']}",
        f"  Supported files   : {status['docs_file_count']}",
        "",
        "--- Chroma / Vector Index ---",
        f"  persist_dir       : {status['chroma_persist_dir']}",
        f"  Directory exists  : {status['chroma_persist_dir_exists']}",
        f"  Collection avail  : {status['chroma_collection_available']}",
        f"  Indexed sources   : {source_count if source_count is not None else '(not available)'}",
        f"  Indexed chunks    : {chunk_count if chunk_count is not None else '(not available)'}",
        f"  file_index.json   : {'present' if status['file_index_exists'] else '(not found)'}",
        "",
        "--- BM25 Keyword Index ---",
        f"  bm25.pkl exists   : {status['bm25_file_exists']}",
        f"  Status            : {bm25_status}",
        "",
        "--- Summary ---",
    ]

    if status["docs_dir_exists"]:
        lines.append("  [OK]   Documents directory found.")
    else:
        lines.append("  [WARN] Documents directory does not exist.")

    if status["chroma_collection_available"]:
        lines.append("  [OK]   Chroma collection is available.")
    elif status["chroma_persist_dir_exists"]:
        lines.append("  [WARN] Chroma collection not found - run --build.")
    else:
        lines.append("  [WARN] Chroma persist directory does not exist - run --build.")

    if status["bm25_enabled_in_config"] and status["bm25_file_exists"]:
        lines.append("  [OK]   BM25 index is ready.")
    elif status["bm25_enabled_in_config"]:
        lines.append("  [WARN] BM25 is enabled but index not found - run --build.")

    if not status["llm_configured"]:
        lines.append("  [INFO] LLM API key is not set - retrieval-only will work, chat/ask will not.")

    lines.append("")
    lines.append("=" * 56)
    print("\n".join(lines))
