"""In-memory LRU + TTL cache for search results."""
import copy
import hashlib
import time
from collections import OrderedDict


class SearchCache:
    def __init__(
        self,
        max_size: int = 200,
        ttl_seconds: int = 3600,
        config_fingerprint: str = "",
    ):
        self._cache: OrderedDict[str, tuple[float, list]] = OrderedDict()
        self._max_size = max(1, int(max_size))
        self._ttl = max(0, int(ttl_seconds))
        self._config_fingerprint = config_fingerprint or ""

    def _key(self, question: str) -> str:
        normalized = question.strip().lower()
        raw = f"{self._config_fingerprint}|{normalized}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def get(self, question: str) -> list | None:
        key = self._key(question)
        if key not in self._cache:
            return None
        ts, value = self._cache[key]
        if self._ttl and time.time() - ts > self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return copy.deepcopy(value)

    def set(self, question: str, chunks: list) -> None:
        key = self._key(question)
        self._cache[key] = (time.time(), chunks)
        self._cache.move_to_end(key)
        while len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        self._cache.clear()

    @property
    def max_size(self) -> int:
        return self._max_size

    @property
    def ttl_seconds(self) -> int:
        return self._ttl

    def __len__(self) -> int:
        return len(self._cache)
