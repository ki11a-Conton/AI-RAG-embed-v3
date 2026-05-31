"""
lib/bm25_index.py
BM25 keyword search index for sparse retrieval.
Builds from document chunks, persists as pickle, queries with BM25 scoring.
"""
import pickle
import re
from pathlib import Path
from typing import Any

import jieba
from rank_bm25 import BM25Okapi

_CJK_RE = re.compile(r"[一-鿿]")


def _tokenize(text: str) -> list[str]:
    """Tokenize text: uses jieba for CJK text, English regex/lower otherwise."""
    if not text:
        return []
    if _CJK_RE.search(text):
        tokens = [t.strip() for t in jieba.cut(text)]
        return [t for t in tokens if t]
    return re.findall(r"[a-z0-9]+", text.lower())


class BM25Index:
    """BM25 sparse retrieval index over document chunks."""

    def __init__(self) -> None:
        self._bm25: BM25Okapi | None = None
        self._chunks: list[dict[str, Any]] = []
        self._corpus: list[list[str]] = []

    def _chunk_text(self, chunk: dict[str, Any]) -> str:
        return chunk.get("text", "")

    def _chunk_meta(self, chunk: dict[str, Any]) -> dict[str, Any]:
        return chunk.get("metadata", {})

    # ── build ──────────────────────────────────────────────

    def build(self, chunks: list[dict[str, Any]]) -> None:
        """Build BM25 index from document chunks."""
        self._chunks = list(chunks)
        self._corpus = [_tokenize(self._chunk_text(c)) for c in self._chunks]
        if not self._corpus:
            self._bm25 = None
            return
        self._bm25 = BM25Okapi(self._corpus)

    def delete_by_source(self, source: str) -> int:
        """Delete all chunks whose metadata.source exactly matches source."""
        original_len = len(self._chunks)
        self._chunks = [
            chunk
            for chunk in self._chunks
            if self._chunk_meta(chunk).get("source") != source
        ]
        deleted = original_len - len(self._chunks)
        if deleted <= 0:
            return 0

        self._corpus = [_tokenize(self._chunk_text(c)) for c in self._chunks]
        self._bm25 = BM25Okapi(self._corpus) if self._corpus else None
        return deleted

    def add_chunks(self, chunks: list[dict[str, Any]]) -> None:
        """Incrementally add new chunks to the existing index.

        Does NOT check for duplicates – caller must ensure that old chunks
        for the same source are removed via :meth:`delete_by_source` before
        calling this method with updated versions.
        """
        if not chunks:
            return
        self._chunks.extend(chunks)
        self._corpus.extend([_tokenize(self._chunk_text(c)) for c in chunks])
        self._bm25 = BM25Okapi(self._corpus)

    # ── query ──────────────────────────────────────────────

    def query(self, question: str, k: int = 6) -> list[dict[str, Any]]:
        """Return top-k chunks with bm25_score."""
        if self._bm25 is None or not self._corpus:
            return []

        k = max(0, int(k))
        if k <= 0:
            return []

        tokens = _tokenize(question)
        scores = self._bm25.get_scores(tokens)

        # collect top-k indices by score (descending)
        indexed = [(i, scores[i]) for i in range(len(scores))]
        indexed.sort(key=lambda x: x[1], reverse=True)
        top = indexed[:k]

        results: list[dict[str, Any]] = []
        for idx, score in top:
            chunk = self._chunks[idx]
            meta = self._chunk_meta(chunk)
            results.append({
                "source": meta.get("source", "unknown"),
                "file_type": meta.get("file_type", ""),
                "chunk_index": meta.get("chunk_index"),
                "page": meta.get("page"),
                "text": self._chunk_text(chunk),
                "bm25_score": float(score),
            })
        return results

    # ── save / load ────────────────────────────────────────

    def save(self, path: str | Path) -> None:
        """Save index state to a pickle file."""
        data = {
            "chunks": self._chunks,
            "corpus": self._corpus,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load(self, path: str | Path) -> None:
        """Load index state from a pickle file."""
        with open(path, "rb") as f:
            data = pickle.load(f)
        self._chunks = data["chunks"]
        self._corpus = data["corpus"]
        self._bm25 = BM25Okapi(self._corpus) if self._corpus else None

    # ── helpers ────────────────────────────────────────────

    def __len__(self) -> int:
        return len(self._chunks)

    def is_loaded(self) -> bool:
        return self._bm25 is not None
