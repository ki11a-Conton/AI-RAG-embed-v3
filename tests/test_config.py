"""tests/test_config.py"""
import os
import json
import shutil
import pytest


def test_config_example_is_valid_json():
    """config_example.json 应是合法 JSON 且包含必填字段"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config_example.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    required_keys = [
        "docs_dir",
        "chunk_size",
        "chunk_overlap",
        "embedding_model_name",
        "retrieval_k",
        "max_context_chars",
        "max_output_dirs",
        "chroma_persist_dir",
        "llm",
    ]
    for key in required_keys:
        assert key in config, f"config_example.json 缺少必填字段: {key}"


def test_config_example_has_bm25_enabled():
    """config_example.json 的 bm25_enabled 应为 true"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config_example.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    assert config.get("bm25_enabled") is True, (
        "config_example.json bm25_enabled should be true for personal-use default"
    )


def test_resolve_path_uses_project_root_for_relative_paths():
    from lib.config import PROJECT_DIR, resolve_path

    resolved = resolve_path({"docs_dir": "./documents"}, "docs_dir")

    assert resolved == os.path.join(PROJECT_DIR, "documents")


def test_resolve_path_keeps_absolute_paths():
    from lib.config import resolve_path

    absolute = os.path.abspath(os.path.join(os.sep, "tmp", "rag-docs"))

    assert resolve_path({"docs_dir": absolute}, "docs_dir") == absolute


def test_env_example_exists():
    """.env.example 文件应存在"""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env.example")
    assert os.path.exists(env_path), ".env.example 文件不存在"


def test_gitignore_excludes_env():
    """.gitignore 应包含 .env"""
    gi_path = os.path.join(os.path.dirname(__file__), "..", ".gitignore")
    with open(gi_path, "r") as f:
        content = f.read()
    assert ".env" in content, ".gitignore 未包含 .env"
    assert "config.json" in content, ".gitignore 未包含 config.json"


def test_load_config_fallback_to_example_when_config_json_missing(tmp_path, monkeypatch):
    """load_config() 使用 config_example.json 当 config.json 不存在时"""
    from lib.config import load_config

    # 复制 config_example.json 到临时目录（不复制 config.json）
    example_src = os.path.join(os.path.dirname(__file__), "..", "config_example.json")
    shutil.copy2(example_src, tmp_path / "config_example.json")

    # 模拟 PROJECT_DIR 指向临时目录
    monkeypatch.setattr("lib.config.PROJECT_DIR", str(tmp_path))

    config = load_config()
    assert "docs_dir" in config
    assert config["docs_dir"] == "./documents"
    assert "llm" in config
    assert "embedding_model_name" in config
    assert config.get("bm25_enabled") is True


# ── Knowledge-base name validation ────────────────────────────────────────


class TestValidateKbName:
    """Tests for lib.config.validate_kb_name"""

    def test_valid_names(self):
        from lib.config import validate_kb_name

        for name in ["electronics", "my-kb", "my_kb", "v2.1", "a_b-c.d"]:
            assert validate_kb_name(name) == name

    def test_empty_name_raises(self):
        from lib.config import validate_kb_name

        with pytest.raises(ValueError):
            validate_kb_name("")

    def test_invalid_chars_raises(self):
        from lib.config import validate_kb_name

        for name in ["hello world", "kb/name", "kb\\name", "name!", "space name"]:
            with pytest.raises(ValueError):
                validate_kb_name(name)

    def test_path_traversal_rejected(self):
        from lib.config import validate_kb_name

        with pytest.raises(ValueError):
            validate_kb_name("..")
        with pytest.raises(ValueError):
            validate_kb_name("../etc")
        with pytest.raises(ValueError):
            validate_kb_name("a/../b")

    def test_dot_prefix_rejected(self):
        from lib.config import validate_kb_name

        with pytest.raises(ValueError):
            validate_kb_name(".hidden")
        with pytest.raises(ValueError):
            validate_kb_name("..hidden")


class TestApplyKbOverlay:
    """Tests for lib.config.apply_kb_overlay"""

    def test_overlay_folders(self):
        from lib.config import PROJECT_DIR, apply_kb_overlay

        config = {
            "docs_dir": "./documents",
            "chroma_persist_dir": "./chroma_db",
            "other_key": "value",
        }
        result = apply_kb_overlay(config, "electronics")
        assert result["other_key"] == "value", "other keys should survive"
        expected_docs = os.path.join(PROJECT_DIR, "knowledge_bases", "electronics", "documents")
        expected_chroma = os.path.join(PROJECT_DIR, "knowledge_bases", "electronics", "chroma_db")
        assert result["docs_dir"] == expected_docs
        assert result["chroma_persist_dir"] == expected_chroma

    def test_overlay_preserves_original(self):
        from lib.config import apply_kb_overlay

        config = {"docs_dir": "./documents", "chroma_persist_dir": "./chroma_db"}
        result = apply_kb_overlay(config, "test-kb")
        # Original config must be unchanged
        assert config["docs_dir"] == "./documents"
        assert config["chroma_persist_dir"] == "./chroma_db"
        assert result is not config

    def test_invalid_name_raises(self):
        from lib.config import apply_kb_overlay

        with pytest.raises(ValueError):
            apply_kb_overlay({"docs_dir": ".", "chroma_persist_dir": "."}, "bad/name")
