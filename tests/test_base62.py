import unittest

from src.base62 import decode, decode_base62, encode, encode_base62


class Base62Tests(unittest.TestCase):
    def test_zero_round_trips_as_zero(self):
        self.assertEqual(encode(0), "0")
        self.assertEqual(decode("0"), 0)

    def test_round_trips_values_across_digits(self):
        for value in (1, 9, 10, 35, 36, 61, 62, 3844, 2**64):
            with self.subTest(value=value):
                self.assertEqual(decode(encode(value)), value)

    def test_digit_order_matches_specification(self):
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")
        self.assertEqual(decode("a"), 10)
        self.assertEqual(decode("A"), 36)
        self.assertEqual(decode("10"), 62)

    def test_legacy_function_names_remain_compatible(self):
        self.assertEqual(encode_base62(62), encode(62))
        self.assertEqual(decode_base62("10"), decode("10"))

    def test_encode_rejects_negative_values(self):
        with self.assertRaises(ValueError):
            encode(-1)

    def test_encode_rejects_non_integer_values(self):
        for value in (1.5, "12", True):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    encode(value)

    def test_decode_rejects_empty_or_invalid_values(self):
        for encoded in ("", "a?", "-1"):
            with self.subTest(encoded=encoded):
                with self.assertRaises(ValueError):
                    decode(encoded)

    def test_decode_rejects_non_string_values(self):
        with self.assertRaises(TypeError):
            decode(12)


if __name__ == "__main__":
    unittest.main()
