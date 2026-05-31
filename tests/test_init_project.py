import importlib


def _prepare_project(tmp_path, monkeypatch):
    init_project = importlib.import_module("init_project")
    monkeypatch.setattr(init_project, "PROJECT_DIR", str(tmp_path))
    (tmp_path / "config_example.json").write_text('{"docs_dir": "./documents"}\n', encoding="utf-8")
    (tmp_path / ".env.example").write_text("LLM_API_KEY=your-llm-api-key\n", encoding="utf-8")
    return init_project


def test_creates_config_json_from_example(tmp_path, monkeypatch):
    init_project = _prepare_project(tmp_path, monkeypatch)

    init_project.step_copy_config()

    assert (tmp_path / "config.json").read_text(encoding="utf-8") == '{"docs_dir": "./documents"}\n'


def test_skips_config_if_already_exists(tmp_path, monkeypatch):
    init_project = _prepare_project(tmp_path, monkeypatch)
    config_path = tmp_path / "config.json"
    config_path.write_text('{"existing": true}\n', encoding="utf-8")

    init_project.step_copy_config()

    assert config_path.read_text(encoding="utf-8") == '{"existing": true}\n'


def test_creates_env_from_example(tmp_path, monkeypatch):
    init_project = _prepare_project(tmp_path, monkeypatch)

    init_project.step_copy_env()

    assert (tmp_path / ".env").read_text(encoding="utf-8") == "LLM_API_KEY=your-llm-api-key\n"


def test_skips_env_if_already_exists(tmp_path, monkeypatch):
    init_project = _prepare_project(tmp_path, monkeypatch)
    env_path = tmp_path / ".env"
    env_path.write_text("LLM_API_KEY=real-ish\n", encoding="utf-8")

    init_project.step_copy_env()

    assert env_path.read_text(encoding="utf-8") == "LLM_API_KEY=real-ish\n"


def test_creates_required_directories(tmp_path, monkeypatch):
    init_project = _prepare_project(tmp_path, monkeypatch)

    init_project.step_create_dirs()

    assert (tmp_path / "documents").is_dir()
    assert (tmp_path / "logs").is_dir()
    assert (tmp_path / "knowledge_bases").is_dir()


def test_warns_if_api_key_not_set(tmp_path, monkeypatch, capsys):
    init_project = _prepare_project(tmp_path, monkeypatch)
    (tmp_path / ".env").write_text("LLM_API_KEY=your-llm-api-key\n", encoding="utf-8")

    init_project.step_check_api_key()

    captured = capsys.readouterr()
    assert "LLM_API_KEY is not configured" in captured.out
