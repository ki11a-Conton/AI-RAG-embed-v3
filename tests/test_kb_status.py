"""tests/test_kb_status.py"""
import json
import os
import pytest

from lib.kb_status import _redact_key, get_kb_status, print_doctor_report


class TestRedactKey:
    def test_empty(self):
        assert _redact_key("") == "(not set)"

    def test_short_key(self):
        assert _redact_key("abc") == "***"

    def test_placeholder_key(self):
        assert _redact_key("your-llm-api-key") == "(placeholder)"

    def test_long_key(self):
        result = _redact_key("key-12345678abcdefgh")
        assert result == "key-****efgh"
        assert "*" in result
        assert len(result) == len("key-****efgh")


class TestGetKbStatus:
    """get_kb_status should work without loading embedding models or LLM."""

    def test_minimal_config(self, tmp_path):
        """With a bare-minimum config, all fields should be present."""
        from lib.config import PROJECT_DIR

        config = {
            "docs_dir": str(tmp_path / "docs"),
            "chroma_persist_dir": str(tmp_path / "chroma"),
            "embedding_model_name": "test-model",
            "bm25_enabled": True,
            "llm": {"api_key": ""},
        }
        status = get_kb_status(config)

        # Basic structure
        assert "docs_dir" in status
        assert "chroma_persist_dir" in status
        assert "docs_dir_exists" in status
        assert "chroma_persist_dir_exists" in status
        assert "docs_file_count" in status
        assert "chroma_collection_available" in status
        assert "file_index_exists" in status
        assert "bm25_file_exists" in status
        assert "bm25_enabled_in_config" in status
        assert "llm_configured" in status
        assert "llm_api_key_redacted" in status
        assert "embedding_model" in status

        # Non-existent dirs => false flags
        assert status["docs_dir_exists"] is False
        assert status["chroma_persist_dir_exists"] is False
        assert status["docs_file_count"] == 0
        assert status["chroma_collection_available"] is False
        assert status["file_index_exists"] is False
        assert status["bm25_file_exists"] is False

        # BM25 is enabled in config but file doesn't exist
        assert status["bm25_enabled_in_config"] is True

        # No LLM key
        assert status["llm_configured"] is False
        assert status["llm_api_key_redacted"] == "(not set)"

    def test_with_docs_dir(self, tmp_path):
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "readme.md").write_text("hello", encoding="utf-8")
        (docs / "data.csv").write_text("a,b", encoding="utf-8")
        (docs / "image.png").write_text("fake", encoding="utf-8")  # supported
        (docs / "notes.txt").write_text("notes", encoding="utf-8")

        config = {
            "docs_dir": str(docs),
            "chroma_persist_dir": str(tmp_path / "chroma"),
            "embedding_model_name": "test",
            "bm25_enabled": False,
            "llm": {"api_key": ""},
        }
        status = get_kb_status(config)
        assert status["docs_dir_exists"] is True
        assert status["docs_file_count"] == 4  # md, csv, png, txt

    def test_with_file_index(self, tmp_path):
        persist = tmp_path / "chroma"
        persist.mkdir()
        fi = {
            "doc1.md": {"sha256": "aaa", "chunk_count": 3},
            "doc2.md": {"sha256": "bbb", "chunk_count": 5},
        }
        (persist / "file_index.json").write_text(
            json.dumps(fi), encoding="utf-8"
        )

        config = {
            "docs_dir": str(tmp_path / "docs"),
            "chroma_persist_dir": str(persist),
            "embedding_model_name": "test",
            "bm25_enabled": True,
            "llm": {"api_key": ""},
        }
        status = get_kb_status(config)
        assert status["file_index_exists"] is True
        assert status["chroma_source_count"] == 2
        assert status["chroma_chunk_count"] == 8

    def test_with_bm25_file(self, tmp_path):
        persist = tmp_path / "chroma"
        persist.mkdir()
        (persist / "bm25.pkl").write_text("dummy", encoding="utf-8")

        config = {
            "docs_dir": str(tmp_path / "docs"),
            "chroma_persist_dir": str(persist),
            "embedding_model_name": "test",
            "bm25_enabled": True,
            "llm": {"api_key": ""},
        }
        status = get_kb_status(config)
        assert status["bm25_file_exists"] is True

    def test_llm_key_redacted(self):
        config = {
            "docs_dir": "./docs",
            "chroma_persist_dir": "./chroma",
            "embedding_model_name": "test",
            "bm25_enabled": False,
            "llm": {"api_key": "dummy-abcdef1234567890"},
        }
        status = get_kb_status(config)
        assert status["llm_configured"] is True
        redacted = status["llm_api_key_redacted"]
        assert "****" in redacted
        assert "abcdef" not in redacted  # full key not visible

    def test_missing_llm_key_field(self):
        """If llm key field is missing, should not crash."""
        config = {
            "docs_dir": "./docs",
            "chroma_persist_dir": "./chroma",
            "embedding_model_name": "test",
            "bm25_enabled": False,
            "llm": {"model": "gpt-4"},
        }
        status = get_kb_status(config)
        assert status["llm_configured"] is False

    def test_placeholder_llm_key_is_not_configured(self):
        config = {
            "docs_dir": "./docs",
            "chroma_persist_dir": "./chroma",
            "embedding_model_name": "test",
            "bm25_enabled": False,
            "llm": {"api_key": "your-llm-api-key"},
        }
        status = get_kb_status(config)
        assert status["llm_configured"] is False
        assert status["llm_api_key_redacted"] == "(placeholder)"

    def test_llm_section_none(self):
        """If llm is None (edge case), should not crash."""
        config = {
            "docs_dir": "./docs",
            "chroma_persist_dir": "./chroma",
            "embedding_model_name": "test",
            "bm25_enabled": False,
            "llm": None,
        }
        status = get_kb_status(config)
        assert status["llm_configured"] is False

    def test_empty_docs_dir_returns_zero_files(self, tmp_path):
        docs = tmp_path / "empty_docs"
        docs.mkdir()
        config = {
            "docs_dir": str(docs),
            "chroma_persist_dir": str(tmp_path / "chroma"),
            "embedding_model_name": "test",
            "bm25_enabled": False,
            "llm": {"api_key": ""},
        }
        status = get_kb_status(config)
        assert status["docs_dir_exists"] is True
        assert status["docs_file_count"] == 0


class TestPrintDoctorReport:
    """print_doctor_report should print to stdout and not raise."""

    def test_basic_report(self, tmp_path, capsys):
        config = {
            "docs_dir": str(tmp_path / "docs"),
            "chroma_persist_dir": str(tmp_path / "chroma"),
            "embedding_model_name": "test-model",
            "bm25_enabled": True,
            "llm": {"api_key": "dummy-test1234key5678"},
        }
        print_doctor_report(config)
        captured = capsys.readouterr()
        out = captured.out
        assert "Doctor Report" in out
        assert "test-model" in out
        assert "dumm" in out  # first 4 chars of redacted
        assert "BM25" in out
        assert "Documents" in out
        assert "Chroma" in out

    def test_report_no_key(self, tmp_path, capsys):
        config = {
            "docs_dir": str(tmp_path / "docs"),
            "chroma_persist_dir": str(tmp_path / "chroma"),
            "embedding_model_name": "test",
            "bm25_enabled": False,
            "llm": {"api_key": ""},
        }
        print_doctor_report(config)
        captured = capsys.readouterr()
        out = captured.out
        assert "(not set)" in out
        assert "not set" in out
