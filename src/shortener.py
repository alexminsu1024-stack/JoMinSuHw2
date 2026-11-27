"""URL shortener built on the project's base62 encoder and hash table."""

from urllib.parse import urlsplit

from src.base62 import encode
from src.hash_table import HashInspection, HashTable


class URLShortener:
    def __init__(self, table_class=HashTable):
        self._url_to_code = table_class()
        self._code_to_url = table_class()
        self._next_id = 0

    def shorten(self, url: str) -> str:
        if not isinstance(url, str) or any(character.isspace() for character in url):
            raise ValueError("URL must be an absolute http or https URL")

        try:
            parsed = urlsplit(url)
            valid = parsed.scheme in ("http", "https") and bool(parsed.hostname)
            parsed.port
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("URL must be an absolute http or https URL")

        if self._url_to_code.contains(url):
            return self._url_to_code.get(url)

        code = encode(self._next_id)
        self._next_id += 1
        self._url_to_code.set(url, code)
        self._code_to_url.set(code, url)
        return code

    def expand(self, code: str) -> str:
        if not self._code_to_url.contains(code):
            raise KeyError(code)
        return self._code_to_url.get(code)

    def table_snapshot(self) -> tuple[tuple[tuple[str, object], ...], ...]:
        return self._url_to_code.table_snapshot()

    def inspect_url(self, url: str) -> HashInspection:
        return self._url_to_code.inspect(url)
