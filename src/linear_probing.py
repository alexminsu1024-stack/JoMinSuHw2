"""A fixed-array hash table using linear probing for string keys."""

from src.hash_table import HashInspection, HashTable


class LinearProbingHashTable:
    def __init__(self, capacity: int = 8, max_load_factor: float | None = 0.75):
        if not isinstance(capacity, int) or isinstance(capacity, bool) or capacity < 1:
            raise ValueError("capacity must be a positive integer")
        if max_load_factor is not None and (
            not isinstance(max_load_factor, (int, float))
            or isinstance(max_load_factor, bool)
            or max_load_factor <= 0
        ):
            raise ValueError("max_load_factor must be positive or None")
        self._slots: list[tuple[str, object] | None] = [None] * capacity
        self._size = 0
        self._max_load_factor = max_load_factor

    @property
    def capacity(self) -> int:
        return len(self._slots)

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: str) -> bool:
        return self.contains(key)

    @staticmethod
    def _validate_key(key: str) -> None:
        if not isinstance(key, str):
            raise TypeError("keys must be strings")

    def _find_slot(self, key: str) -> tuple[int | None, int, tuple[int, ...]]:
        self._validate_key(key)
        home = HashTable._index(key, self.capacity)
        probe_indices = []
        for offset in range(self.capacity):
            index = (home + offset) % self.capacity
            probe_indices.append(index)
            slot = self._slots[index]
            if slot is None or slot[0] == key:
                return index, len(probe_indices), tuple(probe_indices)
        return None, self.capacity, tuple(probe_indices)

    def contains(self, key: str) -> bool:
        index, _, _ = self._find_slot(key)
        return index is not None and self._slots[index] is not None

    def get(self, key: str, default=None):
        value, _ = self.get_with_probes(key, default)
        return value

    def get_with_probes(self, key: str, default=None) -> tuple[object, int]:
        index, probes, _ = self._find_slot(key)
        if index is None or self._slots[index] is None:
            return default, probes
        return self._slots[index][1], probes

    def set(self, key: str, value: object) -> None:
        self._validate_key(key)
        index, _, _ = self._find_slot(key)
        if index is not None and self._slots[index] is not None:
            self._slots[index] = (key, value)
            return

        if (
            self._max_load_factor is not None
            and (self._size + 1) / self.capacity > self._max_load_factor
        ):
            self._resize(self.capacity * 2)

        index, _, _ = self._find_slot(key)
        if index is None:
            raise OverflowError("hash table is full")
        self._slots[index] = (key, value)
        self._size += 1

    def _resize(self, new_capacity: int) -> None:
        old_slots = self._slots
        self._slots = [None] * new_capacity
        self._size = 0
        for slot in old_slots:
            if slot is not None:
                self._insert_without_resize(slot[0], slot[1])

    def _insert_without_resize(self, key: str, value: object) -> None:
        index, _, _ = self._find_slot(key)
        if index is None:
            raise OverflowError("hash table is full")
        self._slots[index] = (key, value)
        self._size += 1

    def items(self) -> list[tuple[str, object]]:
        return [slot for slot in self._slots if slot is not None]

    def table_snapshot(self) -> tuple[tuple[tuple[str, object], ...], ...]:
        return tuple(() if slot is None else (slot,) for slot in self._slots)

    def inspect(self, key: str) -> HashInspection:
        self._validate_key(key)
        value = 0
        steps = []
        for character in key:
            previous = value
            raw_value = previous * 31 + ord(character)
            value = raw_value % self.capacity
            steps.append((character, previous, raw_value, value))

        probe_indices = []
        nodes = []
        position = -1
        for offset in range(self.capacity):
            index = (value + offset) % self.capacity
            probe_indices.append(index)
            slot = self._slots[index]
            if slot is None:
                break
            nodes.append(slot)
            if slot[0] == key:
                position = index
                break

        return HashInspection(
            value,
            tuple(steps),
            tuple(nodes),
            position,
            len(probe_indices),
            tuple(probe_indices),
        )
