import json
from fastapi.testclient import TestClient

import api
import rag_runner


class FakeStore:
    def __init__(self, distance=0.9):
        self.distance = distance

    def query(self, question, k):
        return [
            {
                "text": "weak match",
                "source": "fake.md",
                "page": None,
                "chunk_index": 0,
                "distance": self.distance,
            }
        ]


# -- _log_knowledge_gap --


def test_log_knowledge_gap_writes_jsonl(monkeypatch, tmp_path):
    path = tmp_path / "knowledge_gaps.jsonl"
    monkeypatch.setattr(api, "_KNOWLEDGE_GAPS_PATH", str(path))

    api._log_knowledge_gap("原始问题", "translated question")

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["original"] == "原始问题"
    assert entry["searched"] == "translated question"
    assert "ts" in entry
    assert entry["kb"] == "default"


def test_log_knowledge_gap_includes_explicit_kb(monkeypatch, tmp_path):
    path = tmp_path / "knowledge_gaps.jsonl"
    monkeypatch.setattr(api, "_KNOWLEDGE_GAPS_PATH", str(path))

    api._log_knowledge_gap("question", "searched", kb_name="project_a")

    entry = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert entry["kb"] == "project_a"


# -- /search endpoint --


def test_search_low_confidence_logs_gap(monkeypatch, tmp_path):
    path = tmp_path / "knowledge_gaps.jsonl"
    monkeypatch.setattr(api, "_KNOWLEDGE_GAPS_PATH", str(path))
    monkeypatch.setattr(
        api,
        "_get_search_system",
        lambda kb_name="default": (FakeStore(0.9), None, None, None, None, None),
    )
    monkeypatch.setitem(api.config, "confidence_high_threshold", 0.2)
    monkeypatch.setitem(api.config, "confidence_low_threshold", 0.4)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "missing topic"})

    assert response.status_code == 200
    assert response.json()["confidence"] == "low"
    entry = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert entry["original"] == "missing topic"
    assert entry["searched"] == "missing topic"
    assert entry["kb"] == "default"


def test_search_low_confidence_with_kb_name_logs_that_kb(monkeypatch, tmp_path):
    path = tmp_path / "knowledge_gaps.jsonl"
    monkeypatch.setattr(api, "_KNOWLEDGE_GAPS_PATH", str(path))
    monkeypatch.setattr(
        api,
        "_get_search_system",
        lambda kb_name="default": (FakeStore(0.9), None, None, None, None, None),
    )
    monkeypatch.setitem(api.config, "confidence_high_threshold", 0.2)
    monkeypatch.setitem(api.config, "confidence_low_threshold", 0.4)

    client = TestClient(api.app)
    response = client.post(
        "/search", json={"question": "missing topic", "kb_name": "project_a"}
    )

    assert response.status_code == 200
    assert response.json()["confidence"] == "low"
    entry = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert entry["kb"] == "project_a"


def test_search_high_confidence_does_not_log_gap(monkeypatch, tmp_path):
    path = tmp_path / "knowledge_gaps.jsonl"
    monkeypatch.setattr(api, "_KNOWLEDGE_GAPS_PATH", str(path))
    monkeypatch.setattr(
        api,
        "_get_search_system",
        lambda kb_name="default": (FakeStore(0.1), None, None, None, None, None),
    )
    monkeypatch.setitem(api.config, "confidence_high_threshold", 0.2)
    monkeypatch.setitem(api.config, "confidence_low_threshold", 0.4)

    client = TestClient(api.app)
    response = client.post("/search", json={"question": "known topic"})

    assert response.status_code == 200
    assert response.json()["confidence"] == "high"
    assert not path.exists()


# -- cmd_gaps filtering --


def _write_gaps_jsonl(tmp_path, records):
    """Helper: write a list of gap dicts to logs/knowledge_gaps.jsonl under tmp_path."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    path = logs_dir / "knowledge_gaps.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return str(path)


def test_cmd_gaps_filters_default_including_legacy(monkeypatch, tmp_path, capsys):
    """Default --gaps shows records with kb='default'
    AND legacy records with no 'kb' field.
    """
    _write_gaps_jsonl(tmp_path, [
        {"ts": "t1", "original": "legacy question", "searched": "legacy question"},
        {
            "ts": "t2",
            "original": "default question",
            "searched": "default question",
            "kb": "default",
        },
        {
            "ts": "t3",
            "original": "project_a question",
            "searched": "project_a question",
            "kb": "project_a",
        },
    ])
    monkeypatch.setattr(rag_runner, "_PROJECT_DIR", str(tmp_path))

    config = {"_active_kb_name": "default"}
    rag_runner.cmd_gaps(config)

    out = capsys.readouterr().out
    assert "legacy question" in out
    assert "default question" in out
    assert "project_a question" not in out
    assert "2 gap records" in out


def test_cmd_gaps_filters_project_a_only(monkeypatch, tmp_path, capsys):
    """--kb project_a --gaps shows only project_a records."""
    _write_gaps_jsonl(tmp_path, [
        {"ts": "t1", "original": "legacy question", "searched": "legacy question"},
        {
            "ts": "t2",
            "original": "default question",
            "searched": "default question",
            "kb": "default",
        },
        {
            "ts": "t3",
            "original": "project_a question",
            "searched": "project_a question",
            "kb": "project_a",
        },
    ])
    monkeypatch.setattr(rag_runner, "_PROJECT_DIR", str(tmp_path))

    config = {"_active_kb_name": "project_a"}
    rag_runner.cmd_gaps(config)

    out = capsys.readouterr().out
    assert "project_a question" in out
    assert "legacy question" not in out
    assert "default question" not in out
    assert "1 gap records" in out
