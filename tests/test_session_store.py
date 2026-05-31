import os
import sys
import threading

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

from lib import session_store
from lib.session_store import SessionStore


def test_get_empty_session_returns_empty_list():
    store = SessionStore()

    assert store.get_history("missing") == []


def test_append_and_get_history():
    store = SessionStore()

    store.append_turn("s1", "question", "answer")

    assert store.get_history("s1") == [
        {"role": "user", "content": "question"},
        {"role": "assistant", "content": "answer"},
    ]


def test_get_history_returns_copy():
    store = SessionStore()
    store.append_turn("s1", "question", "answer")

    history = store.get_history("s1")
    history[0]["content"] = "mutated"

    assert store.get_history("s1")[0]["content"] == "question"


def test_session_ttl_expires(monkeypatch):
    now = 1000.0
    monkeypatch.setattr(session_store.time, "time", lambda: now)
    store = SessionStore(ttl_seconds=10)
    store.append_turn("s1", "question", "answer")

    now = 1011.0

    assert store.get_history("s1") == []
    assert store.session_count() == 0


def test_max_sessions_evicts_oldest():
    store = SessionStore(max_sessions=2)
    store.append_turn("old", "q1", "a1")
    store.append_turn("middle", "q2", "a2")
    store.append_turn("new", "q3", "a3")

    assert store.get_history("old") == []
    assert store.get_history("middle")
    assert store.get_history("new")


def test_clear_session():
    store = SessionStore()
    store.append_turn("s1", "question", "answer")

    assert store.clear_session("s1") is True
    assert store.clear_session("s1") is False
    assert store.get_history("s1") == []


def test_concurrent_access_thread_safe():
    store = SessionStore(max_sessions=10)

    def worker(start):
        for i in range(20):
            store.append_turn("shared", f"q{start + i}", f"a{start + i}")
            store.get_history("shared")

    threads = [threading.Thread(target=worker, args=(i * 20,)) for i in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(store.get_history("shared")) == 200
