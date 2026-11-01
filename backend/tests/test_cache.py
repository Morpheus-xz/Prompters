import pytest
from conftest import Clock

from app.services.cache import TTLCache


def test_expiry(clock: Clock) -> None:
    """Verify expiry."""
    cache: TTLCache[str, str] = TTLCache(10, 2, clock.monotonic)
    cache.set("a", "one")
    assert cache.get("a") == "one"
    clock.seconds = 10
    assert cache.get("a") is None
    assert cache.get("missing") is None


def test_lru_and_delete(clock: Clock) -> None:
    """Verify lru and delete."""
    cache: TTLCache[str, int] = TTLCache(10, 2, clock.monotonic)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1
    cache.set("c", 3)
    assert cache.get("b") is None
    cache.set("a", 4)
    assert cache.get("a") == 4
    cache.delete("a")
    cache.delete("absent")
    assert cache.get("a") is None


@pytest.mark.parametrize(("ttl", "capacity"), [(0, 2), (1, 0), (-1, 2)])
def test_invalid_policy(ttl: int, capacity: int) -> None:
    """Verify invalid policy."""
    with pytest.raises(ValueError):
        TTLCache[str, str](ttl, capacity)
