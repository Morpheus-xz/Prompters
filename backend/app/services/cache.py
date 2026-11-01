"""Bounded least-recently-used storage with monotonic expiry."""

from collections import OrderedDict
from collections.abc import Callable
from time import monotonic
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class TTLCache(Generic[K, V]):
    """A process-local cache with injectable time and bounded memory."""

    def __init__(
        self, ttl: float, max_entries: int, clock: Callable[[], float] = monotonic
    ) -> None:
        """Reject invalid policies and start empty."""
        if ttl <= 0 or max_entries <= 0:
            raise ValueError("TTL and capacity must be positive.")
        self.ttl = ttl
        self.max_entries = max_entries
        self.clock = clock
        self._items: OrderedDict[K, tuple[float, V]] = OrderedDict()

    def get(self, key: K) -> V | None:
        """Read a live entry and promote it to most recently used."""
        item = self._items.get(key)
        if item is None:
            return None
        deadline, value = item
        if deadline <= self.clock():
            self.delete(key)
            return None
        self._items.move_to_end(key)
        return value

    def set(self, key: K, value: V) -> None:
        """Insert and evict the oldest entry beyond capacity."""
        self._items[key] = (self.clock() + self.ttl, value)
        self._items.move_to_end(key)
        while len(self._items) > self.max_entries:
            self._items.popitem(last=False)

    def delete(self, key: K) -> None:
        """Forget an entry if present."""
        self._items.pop(key, None)
