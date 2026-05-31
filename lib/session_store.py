"""Thread-safe in-memory session history store."""
from __future__ import annotations

import copy
import threading
import time
from collections import OrderedDict


class SessionStore:
    """Store per-session chat history with TTL and LRU eviction."""

    def __init__(self, ttl_seconds: int = 3600, max_sessions: int = 500):
        self._ttl = ttl_seconds
        self._max = max_sessions
        self._store: OrderedDict[str, dict] = OrderedDict()
        self._lock = threading.Lock()

    def get_history(self, session_id: str) -> list[dict]:
        """Return a copy of session history, or an empty list if missing/expired."""
        with self._lock:
            self._evict_expired()
            entry = self._store.get(session_id)
            if entry is None:
                return []
            entry["last_active"] = time.time()
            self._store.move_to_end(session_id)
            return copy.deepcopy(entry["history"])

    def append_turn(self, session_id: str, question: str, answer: str) -> None:
        """Append one user/assistant turn to a session."""
        with self._lock:
            self._evict_expired()
            if session_id not in self._store:
                if len(self._store) >= self._max:
                    self._store.popitem(last=False)
                self._store[session_id] = {
                    "history": [],
                    "last_active": time.time(),
                }
            entry = self._store[session_id]
            entry["history"].append({"role": "user", "content": question})
            entry["history"].append({"role": "assistant", "content": answer})
            entry["last_active"] = time.time()
            self._store.move_to_end(session_id)

    def clear_session(self, session_id: str) -> bool:
        """Clear a session and return whether it existed."""
        with self._lock:
            return self._store.pop(session_id, None) is not None

    def session_count(self) -> int:
        """Return the number of active sessions after TTL cleanup."""
        with self._lock:
            self._evict_expired()
            return len(self._store)

    def _evict_expired(self) -> None:
        now = time.time()
        expired = [
            session_id
            for session_id, entry in self._store.items()
            if now - entry["last_active"] > self._ttl
        ]
        for session_id in expired:
            del self._store[session_id]
