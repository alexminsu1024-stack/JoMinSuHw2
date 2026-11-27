import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def test_empty_lookup_returns_default_and_zero_probes(self):
        table = HashTable()

        self.assertIsNone(table.get("missing"))
        self.assertEqual(table.get("missing", "fallback"), "fallback")
        self.assertEqual(table.get_with_probes("missing"), (None, 0))
        self.assertFalse(table.contains("missing"))

    def test_collisions_preserve_values_and_count_visited_nodes(self):
        table = HashTable()
        table.set("a", 1)
        table.set("i", 2)

        self.assertTrue(table.contains("a"))
        self.assertTrue("i" in table)
        self.assertEqual(table.get_with_probes("a"), (1, 2))
        self.assertEqual(table.get_with_probes("i"), (2, 1))
        self.assertEqual(table.get_with_probes("q"), (None, 2))

    def test_setting_existing_key_replaces_value_without_growing(self):
        table = HashTable()
        table.set("key", 1)
        original_capacity = table.capacity

        table.set("key", 2)

        self.assertEqual(len(table), 1)
        self.assertEqual(table.get("key"), 2)
        self.assertEqual(table.capacity, original_capacity)

    def test_table_grows_above_load_threshold(self):
        table = HashTable()
        for value in range(7):
            table.set(f"key-{value}", value)

        self.assertEqual(table.capacity, 16)
        self.assertEqual(len(table), 7)
        for value in range(7):
            self.assertEqual(table.get(f"key-{value}"), value)

    def test_keys_must_be_strings(self):
        table = HashTable()
        with self.assertRaises(TypeError):
            table.set(1, "value")
        with self.assertRaises(TypeError):
            table.get(1)


if __name__ == "__main__":
    unittest.main()
