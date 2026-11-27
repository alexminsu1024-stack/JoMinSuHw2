import unittest

from src.shortener import URLShortener


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

    def test_rejects_invalid_urls(self):
        shortener = URLShortener()
        for url in ("", "example.com", "ftp://example.com", "https:///missing-host", "https://bad host"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    shortener.shorten(url)
        with self.assertRaises(ValueError):
            shortener.shorten(None)

    def test_unknown_code_raises_key_error(self):
        with self.assertRaises(KeyError):
            URLShortener().expand("unknown")


if __name__ == "__main__":
    unittest.main()
