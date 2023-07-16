from typing import List
from datetime import datetime
from typing import TypeVar, Generic


T = TypeVar('T')


class FIFOBuffer(Generic[T]):
    """Hold a buffer of objects in memory,
    expelling the first entries when exceeding a maximum size"""

    def __init__(self, max_size: int = 16384):
        self._entries: List[T] = []
        self._max_size = max_size

    def __getitem__(self, k) -> T:
        return self._entries.__getitem__(k)

    def __len__(self) -> int:
        return len(self._entries)

    def remove_first(self, n: int = 1):
        self._entries = self._entries[n:]

    def append(self, entry: T):
        self._entries.append(entry)
        if len(self._entries) > self._max_size:
            # remove a large chunk if we hit the max size for efficiency
            self.remove_first(self._max_size // 16)


class TimestampedBuffer(FIFOBuffer):

    def __init__(self, max_size: int = 16384):
        super().__init__(max_size)
        self.timestamps: List[datetime] = []

    def remove_first(self, n: int = 1):
        super().remove_first(n)
        self.timestamps = self.timestamps[n:]

    def append(self, entry: object, dt: datetime = None):
        if dt is None:
            dt = datetime.utcnow()
        self.timestamps.append(dt)
        super().append(entry)
