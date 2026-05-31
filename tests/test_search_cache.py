from lib.search_cache import SearchCache


def test_cache_hit():
    cache = SearchCache(max_size=2, ttl_seconds=60)
    chunks = [{"text": "result"}]

    cache.set("What is ETS?", chunks)

    assert cache.get(" what is ets? ") == chunks


def test_cache_miss_after_ttl(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("lib.search_cache.time.time", lambda: now[0])
    cache = SearchCache(max_size=2, ttl_seconds=10)

    cache.set("question", [{"text": "old"}])
    now[0] = 1011.0

    assert cache.get("question") is None
    assert len(cache) == 0


def test_lru_eviction():
    cache = SearchCache(max_size=2, ttl_seconds=60)

    cache.set("a", [1])
    cache.set("b", [2])
    assert cache.get("a") == [1]
    cache.set("c", [3])

    assert cache.get("a") == [1]
    assert cache.get("b") is None
    assert cache.get("c") == [3]


def test_cache_clear():
    cache = SearchCache(max_size=2, ttl_seconds=60)
    cache.set("a", [1])
    cache.set("b", [2])

    cache.clear()

    assert len(cache) == 0
    assert cache.get("a") is None


# ── config_fingerprint tests ──────────────────────────────────────


def test_fingerprint_isolation():
    """Same question with different fingerprints must NOT share cache entries."""
    cache_a = SearchCache(
        max_size=2, ttl_seconds=60, config_fingerprint="abc123"
    )
    cache_b = SearchCache(
        max_size=2, ttl_seconds=60, config_fingerprint="xyz789"
    )

    cache_a.set("question", [{"text": "from A"}])
    cache_b.set("question", [{"text": "from B"}])

    # Each cache returns its own value
    assert cache_a.get("question") == [{"text": "from A"}]
    assert cache_b.get("question") == [{"text": "from B"}]


def test_fingerprint_cache_normalizes_question():
    """With a fingerprint present, question normalization (case/whitespace)
    still works so cache hits are reliable."""
    fingerprint = "fp-42"
    cache = SearchCache(
        max_size=2, ttl_seconds=60, config_fingerprint=fingerprint
    )
    cache.set("What is ETS?", [{"text": "answer"}])

    assert cache.get(" what is ets? ") == [{"text": "answer"}]
    assert cache.get("WHAT IS ETS?") == [{"text": "answer"}]


def test_empty_fingerprint_still_works():
    """Empty (default) fingerprint must not break the cache."""
    cache = SearchCache(max_size=2, ttl_seconds=60)
    cache.set("hello", [1])
    assert cache.get("hello") == [1]
    assert cache.get("HELLO") == [1]


def test_fingerprint_stores_and_retrieves():
    """Basic round-trip: set with fingerprint → get with same fingerprint."""
    cache = SearchCache(
        max_size=10, ttl_seconds=60, config_fingerprint="fp1"
    )
    chunks = [{"text": "result"}]
    cache.set("q", chunks)
    assert cache.get("q") == chunks
    # Same cache instance, different question — still fine
    cache.set("q2", [{"text": "r2"}])
    assert cache.get("q2") == [{"text": "r2"}]


def test_get_returns_deep_copy_not_mutable_reference():
    """Mutating a get() result must not affect the cached value returned
    by a subsequent get()."""
    cache = SearchCache(max_size=5, ttl_seconds=60)
    original = [{"key": "value"}, [1, 2, 3]]
    cache.set("q", original)

    first = cache.get("q")
    second = cache.get("q")

    # Mutate the first result deeply
    first.append("new_item")
    first[0]["key"] = "mutated"
    first[1].append(4)

    # Second result must be unchanged
    assert second == [{"key": "value"}, [1, 2, 3]]
    # The original list must also be unchanged
    assert original == [{"key": "value"}, [1, 2, 3]]
