import http.client
import unittest
from http.server import HTTPServer
from threading import Thread
from urllib.parse import urlencode

from src.hash_table import HashTable
from src.server import ShortenerHandler
from src.shortener import URLShortener


class ShortenerServerTests(unittest.TestCase):
    def setUp(self):
        self.original_shorteners = ShortenerHandler.shorteners
        self.shortener = URLShortener()
        ShortenerHandler.shorteners = (("chaining", self.shortener),)
        self.server = HTTPServer(("127.0.0.1", 0), ShortenerHandler)
        self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()
        ShortenerHandler.shorteners = self.original_shorteners

    def _request(self, method, path, body=None):
        connection = http.client.HTTPConnection(
            "127.0.0.1",
            self.server.server_port,
            timeout=2,
        )
        connection.request(method, path, body=body)
        response = connection.getresponse()
        result = (
            response.status,
            response.getheader("Location"),
            response.read().decode("utf-8"),
        )
        connection.close()
        return result

    def test_home_form_creates_short_link_and_redirects(self):
        status, _, page = self._request("GET", "/")

        self.assertEqual(status, 200)
        self.assertIn('<form method="post" action="/shorten">', page)
        self.assertIn('name="url"', page)

        url = "https://example.com/a?b=1"
        body = urlencode((("url", url),)).encode("utf-8")
        status, _, result_page = self._request("POST", "/shorten", body)

        self.assertEqual(status, 200)
        self.assertIn('href="/0"', result_page)
        self.assertIn("Short URL created", result_page)

        status, location, _ = self._request("GET", "/0")
        self.assertEqual(status, 302)
        self.assertEqual(location, url)

    def test_invalid_urls_and_unknown_codes_return_error_statuses(self):
        body = urlencode((("url", "not-a-url"),)).encode("utf-8")
        status, _, _ = self._request("POST", "/shorten", body)
        self.assertEqual(status, 400)

        status, _, _ = self._request("GET", "/not-registered")
        self.assertEqual(status, 404)

    def test_table_shows_chained_nodes_links_and_expandable_horner_steps(self):
        urls = []
        for index in range(100):
            candidate = f"https://example.com/item-{index}"
            if not urls or HashTable._index(candidate, 8) == HashTable._index(urls[0], 8):
                urls.append(candidate)
            if len(urls) == 2:
                break

        self.assertEqual(len(urls), 2)
        for url in urls:
            body = urlencode((("url", url),)).encode("utf-8")
            status, _, _ = self._request("POST", "/shorten", body)
            self.assertEqual(status, 200)

        status, _, table_page = self._request("GET", "/table")

        self.assertEqual(status, 200)
        self.assertIn(urls[0], table_page)
        self.assertIn(urls[1], table_page)
        self.assertIn("URL key", table_page)
        self.assertIn("Short code", table_page)
        self.assertIn("Short link", table_page)
        self.assertIn('href="/0"', table_page)
        self.assertIn('href="/1"', table_page)
        self.assertIn("→", table_page)
        self.assertIn("<details>", table_page)
        self.assertEqual(table_page.count("<details>"), 2)
        self.assertIn("Horner hash calculation", table_page)
        self.assertIn("ord(", table_page)


if __name__ == "__main__":
    unittest.main()
