"""HTTP interface for the in-memory URL shortener."""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlsplit

from src.shortener import URLShortener


def _page(title: str, content: str) -> str:
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{escape(title)}</title></head><body>"
        f"<h1>{escape(title)}</h1>{content}"
        '<p><a href="/">Shorten another URL</a> | <a href="/table">View table</a></p>'
        "</body></html>"
    )


class ShortenerHandler(BaseHTTPRequestHandler):
    shortener = URLShortener()

    def _send_html(self, status: int, content: str) -> None:
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/":
            form = (
                '<form method="post" action="/shorten">'
                '<label for="url">URL</label> '
                '<input id="url" name="url" type="url" required size="60"> '
                '<button type="submit">Shorten</button></form>'
            )
            self._send_html(200, _page("URL shortener", form))
            return

        if parsed.path == "/table":
            self._send_html(200, _page("Hash table", self._render_table()))
            return

        code = parsed.path.removeprefix("/")
        if not code or "/" in code:
            self._send_html(404, _page("Not found", "<p>Unknown path.</p>"))
            return
        try:
            url = self.shortener.expand(code)
        except KeyError:
            self._send_html(404, _page("Not found", "<p>Unknown short code.</p>"))
            return

        self.send_response(302)
        self.send_header("Location", url)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/shorten":
            self._send_html(404, _page("Not found", "<p>Unknown path.</p>"))
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        fields = parse_qsl(body, keep_blank_values=True)
        url = next((value for key, value in fields if key == "url"), "")
        try:
            code = self.shortener.shorten(url)
        except ValueError as error:
            self._send_html(400, _page("Invalid URL", f"<p>{escape(str(error))}</p>"))
            return

        result = (
            f'<p>Short code: <a href="/{escape(code)}">{escape(code)}</a></p>'
            f'<p>Original URL: <a href="{escape(url, quote=True)}">'
            f"{escape(url)}</a></p>"
        )
        self._send_html(200, _page("Short URL created", result))

    def _render_table(self) -> str:
        snapshot = self.shortener.table_snapshot()
        rows = []
        for bucket_index, bucket in enumerate(snapshot):
            if not bucket:
                rows.append(
                    f"<tr><td>{bucket_index}</td><td><em>empty</em></td><td></td><td></td></tr>"
                )
                continue
            for key, value in bucket:
                inspection = self.shortener.inspect_url(key)
                chain = " → ".join(escape(item_key) for item_key, _ in inspection.nodes)
                calculations = " ; ".join(
                    f"{previous} × 31 + ord({escape(repr(character))}) = {raw}; "
                    f"{raw} mod {len(snapshot)} = {reduced}"
                    for character, previous, raw, reduced in inspection.hash_steps
                )
                rows.append(
                    f"<tr><td>{bucket_index}</td><td>{escape(key)} → "
                    f"{escape(str(value))}</td><td>{chain}</td>"
                    f"<td>{calculations or 'empty key → bucket 0'}</td></tr>"
                )
        return (
            "<p>Horner hash: start at 0, then apply "
            "<code>(value × 31 + ord(character)) mod capacity</code>.</p>"
            "<table border=\"1\"><thead><tr><th>Bucket</th><th>Entry</th>"
            "<th>Chain (head first)</th><th>Hash calculation</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener web server")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    ShortenerHandler.shortener = URLShortener()
    server = HTTPServer(("0.0.0.0", args.port), ShortenerHandler)
    print(f"Serving URL shortener on port {args.port}")
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
