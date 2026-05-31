import os


def test_list_knowledge_bases_always_includes_default(tmp_path, monkeypatch):
    import lib.kb_registry as kb_registry

    monkeypatch.setattr(kb_registry, "PROJECT_DIR", str(tmp_path))

    assert kb_registry.list_knowledge_bases() == ["default"]


def test_list_knowledge_bases_includes_dirs_with_chroma(tmp_path, monkeypatch):
    import lib.kb_registry as kb_registry

    monkeypatch.setattr(kb_registry, "PROJECT_DIR", str(tmp_path))
    (tmp_path / "knowledge_bases" / "project_a" / "chroma_db").mkdir(parents=True)
    (tmp_path / "knowledge_bases" / "project_b").mkdir(parents=True)

    assert kb_registry.list_knowledge_bases() == ["default", "project_a"]


def test_list_knowledge_bases_excludes_dirs_without_chroma(tmp_path, monkeypatch):
    import lib.kb_registry as kb_registry

    monkeypatch.setattr(kb_registry, "PROJECT_DIR", str(tmp_path))
    (tmp_path / "knowledge_bases" / "project_b" / "documents").mkdir(parents=True)

    assert kb_registry.list_knowledge_bases() == ["default"]


def test_kb_config_default_returns_base_config():
    from lib.kb_registry import kb_config

    base_config = {"docs_dir": "./documents"}

    assert kb_config(base_config, "default") is base_config


def test_kb_config_nondefault_applies_overlay(monkeypatch):
    import lib.kb_registry as kb_registry

    calls = []

    def fake_apply_kb_overlay(config, kb_name):
        calls.append((config, kb_name))
        cfg = dict(config)
        cfg["docs_dir"] = os.path.join("knowledge_bases", kb_name, "documents")
        return cfg

    monkeypatch.setattr(kb_registry, "apply_kb_overlay", fake_apply_kb_overlay)
    base_config = {"docs_dir": "./documents"}

    result = kb_registry.kb_config(base_config, "project_a")

    assert calls == [(base_config, "project_a")]
    assert result["docs_dir"] == os.path.join("knowledge_bases", "project_a", "documents")
