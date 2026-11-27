"""A small separate-chaining hash table for string keys."""


from typing import NamedTuple


class HashInspection(NamedTuple):
    bucket_index: int
    hash_steps: tuple[tuple[str, int, int, int], ...]
    nodes: tuple[tuple[str, object], ...]
    position: int
    probes: int


class HashTable:
    def __init__(self, capacity: int = 8, max_load_factor: float | None = 0.75):
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            raise ValueError("capacity must be a positive integer")
        if max_load_factor is not None and (
            not isinstance(max_load_factor, (int, float))
            or isinstance(max_load_factor, bool)
            or max_load_factor <= 0
        ):
            raise ValueError("max_load_factor must be positive or None")
        self._buckets = [[] for _ in range(capacity)]
        self._size = 0
        self._max_load_factor = max_load_factor

    @property
    def capacity(self) -> int:
        return len(self._buckets)

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: str) -> bool:
        return self.contains(key)

    def _validate_key(self, key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("keys must be strings")

    @staticmethod
    def _index(key: str, capacity: int) -> int:
        value = 0
        for character in key:
            value = (value * 31 + ord(character)) % capacity
        return value

    def _find(self, key: str) -> tuple[list, int, int]:
        self._validate_key(key)
        bucket = self._buckets[self._index(key, self.capacity)]
        for position, node in enumerate(bucket):
            if node[0] == key:
                return bucket, position, position + 1
        return bucket, -1, len(bucket)

    def contains(self, key: str) -> bool:
        _, position, _ = self._find(key)
        return position >= 0

    def get(self, key: str, default=None):
        value, _ = self.get_with_probes(key, default)
        return value

    def get_with_probes(self, key: str, default=None) -> tuple[object, int]:
        bucket, position, probes = self._find(key)
        if position < 0:
            return default, probes
        return bucket[position][1], probes

    def items(self) -> list[tuple[str, object]]:
        return [
            (node[0], node[1])
            for bucket in self._buckets
            for node in bucket
        ]

    def table_snapshot(self) -> tuple[tuple[tuple[str, object], ...], ...]:
        return tuple(
            tuple((node[0], node[1]) for node in bucket)
            for bucket in self._buckets
        )

    def inspect(self, key: str) -> HashInspection:
        self._validate_key(key)
        value = 0
        steps = []
        for character in key:
            previous = value
            raw_value = previous * 31 + ord(character)
            value = raw_value % self.capacity
            steps.append((character, previous, raw_value, value))

        bucket = self._buckets[value]
        nodes = tuple((node[0], node[1]) for node in bucket)
        position = next(
            (index for index, node in enumerate(bucket) if node[0] == key),
            -1,
        )
        probes = position + 1 if position >= 0 else len(bucket)
        return HashInspection(value, tuple(steps), nodes, position, probes)

    def set(self, key: str, value: object) -> None:
        self._validate_key(key)
        bucket, position, _ = self._find(key)
        if position >= 0:
            bucket[position][1] = value
            return

        if (
            self._max_load_factor is not None
            and (self._size + 1) / self.capacity > self._max_load_factor
        ):
            self._resize(self.capacity * 2)

        bucket = self._buckets[self._index(key, self.capacity)]
        bucket.insert(0, [key, value])
        self._size += 1

    def _resize(self, new_capacity: int) -> None:
        old_buckets = self._buckets
        self._buckets = [[] for _ in range(new_capacity)]
        for bucket in old_buckets:
            for key, value in bucket:
                self._buckets[self._index(key, new_capacity)].append([key, value])
