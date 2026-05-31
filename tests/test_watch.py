import os
import sys
from types import SimpleNamespace

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

import watch


class FakeTimer:
    instances = []

    def __init__(self, interval, function):
        self.interval = interval
        self.function = function
        self.daemon = False
        self.started = False
        self.cancelled = False
        FakeTimer.instances.append(self)

    def start(self):
        self.started = True

    def cancel(self):
        self.cancelled = True


def _event(path: str, is_directory: bool = False):
    return SimpleNamespace(src_path=path, is_directory=is_directory)


def test_debounce_handler_ignores_unsupported_extensions(monkeypatch):
    monkeypatch.setattr(watch.threading, "Timer", FakeTimer)
    FakeTimer.instances.clear()
    handler = watch._DebounceHandler(config={}, debounce_seconds=1.0)

    handler.on_any_event(_event("documents/archive.zip"))

    assert FakeTimer.instances == []
    assert handler._pending_paths == set()


def test_debounce_handler_resets_timer_on_multiple_events(monkeypatch):
    monkeypatch.setattr(watch.threading, "Timer", FakeTimer)
    FakeTimer.instances.clear()
    handler = watch._DebounceHandler(config={}, debounce_seconds=10.0)

    handler.on_any_event(_event("documents/a.md"))
    handler.on_any_event(_event("documents/b.txt"))

    assert len(FakeTimer.instances) == 2
    assert FakeTimer.instances[0].cancelled is True
    assert FakeTimer.instances[1].started is True
    assert FakeTimer.instances[1].interval == 10.0


def test_debounce_handler_collects_pending_paths(monkeypatch):
    calls = []
    monkeypatch.setattr(watch.threading, "Timer", FakeTimer)
    FakeTimer.instances.clear()

    import rag_runner

    monkeypatch.setattr(
        rag_runner,
        "cmd_build_incremental",
        lambda config: calls.append(config),
    )
    config = {"docs_dir": "documents"}
    handler = watch._DebounceHandler(config=config, debounce_seconds=1.0)

    handler.on_any_event(_event("documents/a.md"))
    handler.on_any_event(_event("documents/nested/b.pdf"))
    assert handler._pending_paths == {"documents/a.md", "documents/nested/b.pdf"}

    FakeTimer.instances[-1].function()

    assert calls == [config]
    assert handler._pending_paths == set()
    assert handler._timer is None


# -- kb_name support --------------------------------------------------------


def test_debounce_handler_carries_kb_name_and_still_calls_incremental(monkeypatch):
    """_DebounceHandler with kb_name stores it and still calls
    cmd_build_incremental with the original config."""
    calls = []
    monkeypatch.setattr(watch.threading, "Timer", FakeTimer)
    FakeTimer.instances.clear()

    import rag_runner

    monkeypatch.setattr(
        rag_runner,
        "cmd_build_incremental",
        lambda config: calls.append(config),
    )
    config = {"docs_dir": "knowledge_bases/project_a/documents"}
    handler = watch._DebounceHandler(
        config=config, debounce_seconds=1.0, kb_name="project_a"
    )
    assert handler.kb_name == "project_a"

    handler.on_any_event(_event("knowledge_bases/project_a/documents/x.md"))
    FakeTimer.instances[-1].function()

    assert calls == [config]


def test_debounce_handler_default_kb_name_is_none(monkeypatch):
    """Without explicit kb_name, the attribute defaults to None."""
    monkeypatch.setattr(watch.threading, "Timer", FakeTimer)
    FakeTimer.instances.clear()
    handler = watch._DebounceHandler(config={}, debounce_seconds=1.0)
    assert handler.kb_name is None


class _FakeObserver:
    """Minimal stand-in for watchdog Observer used in main() tests.

    Uses a class-level ``scheduled`` dict so the test can read results
    even though ``main()`` constructs a fresh instance.
    """

    scheduled: dict = {}

    def __init__(self):
        self._alive = False

    def schedule(self, handler, path, recursive):
        _FakeObserver.scheduled = {"handler": handler, "path": path}

    def start(self):
        self._alive = True

    @property
    def is_alive(self):
        return lambda: self._alive

    def stop(self):
        self._alive = False

    def join(self):
        pass


def _patch_main_deps(monkeypatch):
    """Common monkeypatches for testing watch.main()."""
    _FakeObserver.scheduled = {}
    monkeypatch.setattr(watch, "Observer", _FakeObserver)
    monkeypatch.setattr(
        watch.sys, "exit",
        lambda code=0: (_ for _ in ()).throw(SystemExit(code)),
    )
    # Break out of the infinite while-loop immediately
    monkeypatch.setattr(
        watch.time, "sleep",
        lambda s: (_ for _ in ()).throw(KeyboardInterrupt),
    )


def test_main_applies_kb_overlay(monkeypatch, tmp_path):
    """main() with --kb applies apply_kb_overlay and schedules the
    overlaid docs_dir on the observer -- all inside tmp_path."""
    kb_docs = tmp_path / "kb_project_a" / "documents"
    kb_docs.mkdir(parents=True)

    base_config = {"docs_dir": str(tmp_path / "documents")}
    overlaid = {"docs_dir": str(kb_docs)}

    monkeypatch.setattr(watch, "load_config", lambda: base_config)
    monkeypatch.setattr(
        watch, "apply_kb_overlay",
        lambda cfg, name: overlaid if name == "project_a" else (_ for _ in ()).throw(ValueError("bad")),
    )

    _patch_main_deps(monkeypatch)

    try:
        monkeypatch.setattr(sys, "argv", ["watch.py", "--kb", "project_a"])
        watch.main()
    except (KeyboardInterrupt, SystemExit):
        pass

    assert _FakeObserver.scheduled["path"] == os.path.abspath(str(kb_docs))
    assert _FakeObserver.scheduled["handler"].kb_name == "project_a"


def test_main_without_kb_uses_default_docs_dir(monkeypatch, tmp_path):
    """main() without --kb uses the config's default docs_dir."""
    docs = tmp_path / "documents"
    docs.mkdir()

    base_config = {"docs_dir": str(docs)}
    monkeypatch.setattr(watch, "load_config", lambda: base_config)

    _patch_main_deps(monkeypatch)

    try:
        monkeypatch.setattr(sys, "argv", ["watch.py"])
        watch.main()
    except (KeyboardInterrupt, SystemExit):
        pass

    assert _FakeObserver.scheduled["path"] == str(docs)
    assert _FakeObserver.scheduled["handler"].kb_name is None


def test_main_invalid_kb_exits_cleanly(monkeypatch, tmp_path):
    """main() with an invalid --kb name prints an error and exits 1."""
    base_config = {"docs_dir": str(tmp_path / "documents")}
    monkeypatch.setattr(watch, "load_config", lambda: base_config)
    monkeypatch.setattr(
        watch, "apply_kb_overlay",
        lambda cfg, name: (_ for _ in ()).throw(
            ValueError("Invalid knowledge-base name '../bad'.")
        ),
    )
    monkeypatch.setattr(
        watch.sys, "exit",
        lambda code=0: (_ for _ in ()).throw(SystemExit(code)),
    )

    captured = {}
    original_print = print

    def _capture_print(msg, **kw):
        captured["msg"] = msg
        original_print(msg, **kw)

    monkeypatch.setattr("builtins.print", _capture_print)
    monkeypatch.setattr(sys, "argv", ["watch.py", "--kb", "../bad"])

    try:
        watch.main()
    except SystemExit as exc:
        assert exc.code == 1

    assert "Error" in captured.get("msg", "")
