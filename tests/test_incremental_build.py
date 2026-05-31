"""
tests/test_incremental_build.py
Focused unit tests for the incremental build fallback in rag_runner.py:
- file_index.json absent -> fall back to store.get_indexed_sources()
- No duplication of unchanged sources
- Modified file detection on second run with file_index.json present
"""
import json
import os
import sys
import tempfile
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)


# ── helpers ────────────────────────────────────────────

def _make_chunk(source: str, text: str, page: int = 1,
                chunk_index: int = 0, file_type: str = "md") -> dict:
    return {
        "metadata": {
            "source": source,
            "file_type": file_type,
            "chunk_index": chunk_index,
            "page": page,
        },
        "text": text,
    }


def _write_md(path: str, content: str) -> str:
    """Write a .md file and return its path."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def _make_mock_config(docs_dir: str, persist_dir: str, **overrides) -> dict:
    cfg = {
        "docs_dir": docs_dir,
        "chroma_persist_dir": persist_dir,
        "embedding_model_name": "mock-model",
        "chunk_size": 200,
        "chunk_overlap": 20,
        "bm25_enabled": False,
        "image_caption_enabled": False,
        "clip_image_enabled": False,
        "query_enhance_enabled": False,
        "rerank_enabled": False,
    }
    cfg.update(overrides)
    return cfg


def _enter_mock_patches(mock_store, mock_embed_engine, all_chunks, walk_return):
    """Create a context manager stack with all patches needed for cmd_build_incremental."""
    MockEmbedEngineClass = MagicMock(return_value=mock_embed_engine)
    MockVectorDbClass = MagicMock(return_value=mock_store)

    def fake_import_lib():
        return MockEmbedEngineClass, MagicMock(), MockVectorDbClass

    stack = ExitStack()
    stack.enter_context(patch("rag_runner._import_lib", fake_import_lib))
    stack.enter_context(patch("rag_runner.load_documents", return_value=all_chunks))
    stack.enter_context(patch("rag_runner._init_image_captioner", return_value=None))
    stack.enter_context(patch("rag_runner._rebuild_clip_image_index"))
    stack.enter_context(patch("rag_runner._walk_supported_files", return_value=walk_return))
    return stack


# ── Tests ──────────────────────────────────────────────

class TestIncrementalBuildFallback:
    """Test the fallback when file_index.json is absent but store has indexed sources."""

    # ── Test 1: file_index absent, store has existing source ──

    def test_initial_without_file_index_skips_unchanged_sources(self, tmp_path):
        """Without file_index.json but with already-indexed source in store,
        unchanged source must NOT be re-added, and file_index.json is written."""

        docs_dir = tmp_path / "docs"
        persist_dir = tmp_path / "chroma"
        docs_dir.mkdir()
        persist_dir.mkdir()

        existing_path = str(docs_dir / "existing.md")
        new_path = str(docs_dir / "new.md")
        _write_md(existing_path, "# Existing Document\nAlready indexed content.")
        _write_md(new_path, "# New Document\nNot yet indexed.")

        doc1_chunk = _make_chunk("existing.md", "Already indexed content.")
        doc2_chunk = _make_chunk("new.md", "Not yet indexed.")
        all_chunks = [doc1_chunk, doc2_chunk]

        mock_config = _make_mock_config(str(docs_dir), str(persist_dir))

        mock_store = MagicMock()
        mock_store.get_indexed_sources.return_value = {"existing.md"}
        mock_store.count.return_value = 5
        mock_store.delete_by_source.return_value = 0

        mock_embed_engine = MagicMock()
        walk_return = [existing_path, new_path]

        with _enter_mock_patches(mock_store, mock_embed_engine, all_chunks, walk_return):
            from rag_runner import cmd_build_incremental
            cmd_build_incremental(mock_config)

        # 1. Unchanged source must NOT be re-added
        for call in mock_store.add_chunks.call_args_list:
            added = call[0][0]
            added_sources = {c["metadata"]["source"] for c in added}
            assert "existing.md" not in added_sources, (
                "Unchanged source 'existing.md' must NOT be re-added to vector store"
            )

        # 2. New source SHOULD be added
        added_any_new = False
        for call in mock_store.add_chunks.call_args_list:
            added = call[0][0]
            added_sources = {c["metadata"]["source"] for c in added}
            if "new.md" in added_sources:
                added_any_new = True
                break
        assert added_any_new, "New source 'new.md' should be added"

        # 3. Unchanged source must NOT be deleted
        for call in mock_store.delete_by_source.call_args_list:
            assert call[0][0] != "existing.md", (
                "Unchanged source 'existing.md' must NOT be deleted"
            )

        # 4. file_index.json must be created
        fi_path = persist_dir / "file_index.json"
        assert fi_path.exists(), "file_index.json must be created"

        with open(fi_path, "r", encoding="utf-8") as f:
            fi = json.load(f)
        assert "existing.md" in fi, "existing.md must be in file_index.json"
        assert "new.md" in fi, "new.md must be in file_index.json"
        assert "sha256" in fi["existing.md"], "file_index entry must have sha256"
        assert "chunk_count" in fi["existing.md"], "file_index entry must have chunk_count"
        assert fi["existing.md"]["chunk_count"] >= 1

    # ── Test 2: Second incremental after modifying a file ──

    def test_modified_file_deletes_old_and_adds_new(self, tmp_path):
        """When file_index.json exists and a file's SHA changes,
        old chunks must be deleted and new chunks added."""

        docs_dir = tmp_path / "docs"
        persist_dir = tmp_path / "chroma"
        docs_dir.mkdir()
        persist_dir.mkdir()

        doc_path = docs_dir / "mod.md"
        _write_md(str(doc_path), "# Modified Content\nNew content after edit.")

        from rag_runner import _compute_sha256
        new_sha = _compute_sha256(str(doc_path))

        # Write file_index.json with an OLD, non-matching SHA
        old_file_index = {
            "mod.md": {
                "sha256": "0" * 64,
                "chunk_count": 1,
            }
        }
        fi_path = persist_dir / "file_index.json"
        with open(fi_path, "w", encoding="utf-8") as f:
            json.dump(old_file_index, f)

        mock_config = _make_mock_config(str(docs_dir), str(persist_dir))
        mock_store = MagicMock()
        mock_store.get_indexed_sources.return_value = {"mod.md"}
        mock_store.count.return_value = 5
        mock_store.delete_by_source.return_value = 1
        mock_embed_engine = MagicMock()

        all_chunks = [_make_chunk("mod.md", "New content after edit.")]
        walk_return = [str(doc_path)]

        with _enter_mock_patches(mock_store, mock_embed_engine, all_chunks, walk_return):
            from rag_runner import cmd_build_incremental
            cmd_build_incremental(mock_config)

        # 1. Old source must be deleted
        mock_store.delete_by_source.assert_any_call("mod.md")

        # 2. New chunks must be added
        added = False
        for call in mock_store.add_chunks.call_args_list:
            sources = {c["metadata"]["source"] for c in call[0][0]}
            if "mod.md" in sources:
                added = True
                break
        assert added, "Modified source 'mod.md' must be re-added"

        # 3. file_index.json must be updated with new SHA
        with open(fi_path, "r", encoding="utf-8") as f:
            fi = json.load(f)
        assert fi["mod.md"]["sha256"] == new_sha, (
            f"file_index.json SHA should be updated to {new_sha}"
        )
        assert fi["mod.md"]["chunk_count"] == 1


# ── Edge case: no file_index + empty store -> all new ──

def test_no_file_index_empty_store_treats_all_as_new(tmp_path):
    """When both file_index.json and store are empty, all sources are
    treated as new (first-ever build scenario)."""

    docs_dir = tmp_path / "docs"
    persist_dir = tmp_path / "chroma"
    docs_dir.mkdir()
    persist_dir.mkdir()

    doc_path = docs_dir / "first.md"
    _write_md(str(doc_path), "# First doc\nContent.")

    mock_config = _make_mock_config(str(docs_dir), str(persist_dir))
    all_chunks = [_make_chunk("first.md", "Content.")]

    mock_store = MagicMock()
    mock_store.get_indexed_sources.return_value = set()
    mock_store.count.return_value = 0

    mock_embed_engine = MagicMock()
    walk_return = [str(doc_path)]

    with _enter_mock_patches(mock_store, mock_embed_engine, all_chunks, walk_return):
        from rag_runner import cmd_build_incremental
        cmd_build_incremental(mock_config)

    # All sources are "new" -> must be added
    added = False
    for call in mock_store.add_chunks.call_args_list:
        sources = {c["metadata"]["source"] for c in call[0][0]}
        if "first.md" in sources:
            added = True
            break
    assert added, "First-ever build: source must be added to store"

    # file_index.json must be written
    fi_path = persist_dir / "file_index.json"
    assert fi_path.exists(), "file_index.json should be created for first build"


# ── Edge case: file_index absent, all unchanged ──

def test_no_file_index_all_unchanged_creates_file_index_only(tmp_path):
    """When file_index.json is absent and all current files are already
    in the store, only file_index.json is created; no add/delete calls."""

    docs_dir = tmp_path / "docs"
    persist_dir = tmp_path / "chroma"
    docs_dir.mkdir()
    persist_dir.mkdir()

    doc_path = docs_dir / "only.md"
    _write_md(str(doc_path), "# Only doc\nAlready in store.")

    mock_config = _make_mock_config(str(docs_dir), str(persist_dir))
    all_chunks = [_make_chunk("only.md", "Already in store.")]

    mock_store = MagicMock()
    mock_store.get_indexed_sources.return_value = {"only.md"}
    mock_store.count.return_value = 3

    mock_embed_engine = MagicMock()
    walk_return = [str(doc_path)]

    with _enter_mock_patches(mock_store, mock_embed_engine, all_chunks, walk_return):
        from rag_runner import cmd_build_incremental
        cmd_build_incremental(mock_config)

    # No adds and no deletes
    mock_store.add_chunks.assert_not_called()
    mock_store.delete_by_source.assert_not_called()

    # file_index.json must be created
    fi_path = persist_dir / "file_index.json"
    assert fi_path.exists(), "file_index.json must be created even when no changes"
    with open(fi_path, "r", encoding="utf-8") as f:
        fi = json.load(f)
    assert "only.md" in fi


# only_sources parameter forwarding tests


def test_incremental_build_passes_only_sources_with_file_index(tmp_path):
    """When file_index.json exists, cmd_build_incremental must pass
    only_sources=changed_sources to load_documents."""
    from rag_runner import cmd_build_incremental

    docs_dir = tmp_path / "docs"
    persist_dir = tmp_path / "chroma"
    docs_dir.mkdir()
    persist_dir.mkdir()

    unchanged_path = docs_dir / "unchanged.md"
    changed_path = docs_dir / "changed.md"
    _write_md(str(unchanged_path), "# Unchanged\nOld content.")
    _write_md(str(changed_path), "# Changed\nNew content.")

    from rag_runner import _compute_sha256
    new_sha = _compute_sha256(str(changed_path))
    old_sha = _compute_sha256(str(unchanged_path))

    # Write an existing file_index with the OLD SHA for unchanged
    fi_path = persist_dir / "file_index.json"
    with open(fi_path, "w", encoding="utf-8") as f:
        json.dump({
            "unchanged.md": {"sha256": old_sha, "chunk_count": 1},
            "changed.md": {"sha256": "0" * 64, "chunk_count": 1},
        }, f)

    mock_config = _make_mock_config(str(docs_dir), str(persist_dir))
    mock_store = MagicMock()
    mock_store.count.return_value = 2
    mock_store.delete_by_source.return_value = 1
    mock_embed_engine = MagicMock()

    # Use a MagicMock to capture call kwargs.
    mock_load = MagicMock(return_value=[MagicMock(metadata={"source": "changed.md"})])

    stack = ExitStack()
    stack.enter_context(patch("rag_runner._import_lib",
                               lambda: (MagicMock(return_value=mock_embed_engine),
                                        MagicMock(),
                                        MagicMock(return_value=mock_store))))
    stack.enter_context(patch("rag_runner.load_documents", mock_load))
    stack.enter_context(patch("rag_runner._init_image_captioner", return_value=None))
    stack.enter_context(patch("rag_runner._rebuild_clip_image_index"))
    stack.enter_context(patch("rag_runner._walk_supported_files",
                               return_value=[str(unchanged_path), str(changed_path)]))

    with stack:
        cmd_build_incremental(mock_config)

    # Verify only_sources was passed with exactly the changed source.
    assert mock_load.call_count >= 1
    call_kwargs = mock_load.call_args.kwargs if hasattr(mock_load.call_args, 'kwargs') else mock_load.call_args[1]
    assert "only_sources" in call_kwargs, "load_documents must receive only_sources"
    only_sources = call_kwargs["only_sources"]
    assert "changed.md" in only_sources, "changed.md must be in only_sources"
    assert "unchanged.md" not in only_sources, "unchanged.md must NOT be in only_sources"


def test_incremental_build_passes_only_sources_all_files_when_file_index_absent(tmp_path):
    """When file_index.json is absent, changed_sources = all files,
    so only_sources should contain all files (equivalent to no filtering)."""
    from rag_runner import cmd_build_incremental

    docs_dir = tmp_path / "docs"
    persist_dir = tmp_path / "chroma"
    docs_dir.mkdir()
    persist_dir.mkdir()

    doc1_path = docs_dir / "doc1.md"
    doc2_path = docs_dir / "doc2.md"
    _write_md(str(doc1_path), "# Doc1\nContent one.")
    _write_md(str(doc2_path), "# Doc2\nContent two.")

    mock_config = _make_mock_config(str(docs_dir), str(persist_dir))
    mock_store = MagicMock()
    mock_store.get_indexed_sources.return_value = {"doc2.md"}
    mock_store.count.return_value = 1
    mock_embed_engine = MagicMock()

    mock_load = MagicMock(return_value=[
        MagicMock(metadata={"source": "doc1.md"}),
        MagicMock(metadata={"source": "doc2.md"}),
    ])

    stack = ExitStack()
    stack.enter_context(patch("rag_runner._import_lib",
                               lambda: (MagicMock(return_value=mock_embed_engine),
                                        MagicMock(),
                                        MagicMock(return_value=mock_store))))
    stack.enter_context(patch("rag_runner.load_documents", mock_load))
    stack.enter_context(patch("rag_runner._init_image_captioner", return_value=None))
    stack.enter_context(patch("rag_runner._rebuild_clip_image_index"))
    stack.enter_context(patch("rag_runner._walk_supported_files",
                               return_value=[str(doc1_path), str(doc2_path)]))

    with stack:
        cmd_build_incremental(mock_config)

    # Both files are "new" since file_index is absent -> all files load.
    call_kwargs = mock_load.call_args.kwargs if hasattr(mock_load.call_args, 'kwargs') else mock_load.call_args[1]
    assert "only_sources" in call_kwargs
    only_sources = call_kwargs["only_sources"]
    assert "doc1.md" in only_sources
    assert "doc2.md" in only_sources
