import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_empty_table_lookup_returns_default(self):
        table = HashTable()

        self.assertIsNone(table.get("missing"))
        self.assertEqual(table.get("missing", "fallback"), "fallback")

    def test_colliding_keys_and_missing_key_are_handled(self):
        table = HashTable()
        table.set("a", 1)
        table.set("i", 2)

        self.assertEqual(table.get("a"), 1)
        self.assertEqual(table.get("i"), 2)
        self.assertIsNone(table.get("q"))

    def test_setting_same_key_replaces_value(self):
        table = HashTable()
        table.set("key", 1)

        table.set("key", 2)

        self.assertEqual(len(table), 1)
        self.assertEqual(table.get("key"), 2)

    def test_table_grows_only_after_load_exceeds_three_quarters(self):
        table = HashTable()
        for value in range(6):
            table.set(f"key-{value}", value)

        self.assertEqual(table.capacity, 8)
        table.set("key-6", 6)

        self.assertEqual(table.capacity, 16)
        self.assertEqual(len(table), 7)
        for value in range(7):
            self.assertEqual(table.get(f"key-{value}"), value)


if __name__ == "__main__":
    unittest.main()
