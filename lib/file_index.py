"""File discovery and fingerprint helpers for incremental indexing."""

import hashlib
import json
import os

from lib.doc_loader import SUPPORTED_EXTENSIONS, _collect_ignore_specs, _is_ignored
from lib.logger import get_logger

logger = get_logger(__name__)


def _walk_supported_files(docs_dir: str) -> list[str]:
    ignore_specs = _collect_ignore_specs(docs_dir)
    paths: list[str] = []
    for root, _, files in os.walk(docs_dir):
        for filename in sorted(files):
            if filename == ".doc_loader_ignore":
                continue
            ext = os.path.splitext(filename)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            filepath = os.path.join(root, filename)
            if _is_ignored(filepath, ignore_specs):
                continue
            paths.append(filepath)
    return paths


def _compute_sha256(filepath: str) -> str:
    """Return the SHA-256 hex digest of *filepath* contents."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(1 << 16)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()


def _load_file_index(persist_dir: str) -> dict:
    """Load file_index.json from persist_dir, returning {} if absent/corrupt."""
    path = os.path.join(persist_dir, "file_index.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load file_index.json: %s - treating as empty", exc)
        return {}


def _save_file_index(persist_dir: str, file_index: dict) -> None:
    """Atomically write file_index.json to persist_dir."""
    os.makedirs(persist_dir, exist_ok=True)
    path = os.path.join(persist_dir, "file_index.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(file_index, f, indent=2, sort_keys=True, ensure_ascii=False)
    os.replace(tmp, path)


def _build_and_save_file_index(persist_dir: str, docs_dir: str, chunks: list[dict]) -> None:
    """Build file fingerprints and chunk counts, then write file_index.json."""
    file_index: dict[str, dict] = {}
    for filepath in _walk_supported_files(docs_dir):
        relpath = os.path.relpath(filepath, docs_dir)
        sha = _compute_sha256(filepath)
        count = sum(1 for c in chunks if c["metadata"]["source"] == relpath)
        file_index[relpath] = {"sha256": sha, "chunk_count": count}
    _save_file_index(persist_dir, file_index)
