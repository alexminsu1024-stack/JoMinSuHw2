import unittest

from src.shortener import URLShortener
from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable


class URLShortenerTests(unittest.TestCase):
    def test_shortens_and_expands_absolute_http_urls(self):
        shortener = URLShortener()
        url = "https://example.com/a?b=1"

        code = shortener.shorten(url)

        self.assertEqual(shortener.expand(code), url)

    def test_same_url_keeps_its_code_and_different_urls_get_unique_codes(self):
        shortener = URLShortener()
        first_url = "https://example.com/first"
        second_url = "https://example.com/second"

        first_code = shortener.shorten(first_url)
        self.assertEqual(shortener.shorten(first_url), first_code)
        second_code = shortener.shorten(second_url)

        self.assertNotEqual(first_code, second_code)
        self.assertEqual(first_code, "0")
        self.assertEqual(second_code, "1")

    def test_rejects_unsupported_schemes_missing_hosts_and_non_string_input(self):
        shortener = URLShortener()
        invalid_urls = (
            "",
            "example.com",
            "ftp://example.com/path",
            "https:///missing-host",
            "https://bad host",
            None,
        )
        for url in invalid_urls:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    shortener.shorten(url)

    def test_unknown_code_raises_key_error(self):
        with self.assertRaises(KeyError):
            URLShortener().expand("unknown")

    def test_same_shortener_contract_works_with_both_table_implementations(self):
        for table_class in (HashTable, LinearProbingHashTable):
            with self.subTest(table_class=table_class.__name__):
                shortener = URLShortener(table_class=table_class)
                first = "https://example.com/first"
                second = "https://example.com/second"

                first_code = shortener.shorten(first)
                second_code = shortener.shorten(second)

                self.assertEqual(shortener.shorten(first), first_code)
                self.assertNotEqual(first_code, second_code)
                self.assertEqual(shortener.expand(first_code), first)
                self.assertEqual(shortener.expand(second_code), second)


if __name__ == "__main__":
    unittest.main()
