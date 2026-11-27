"""HTTP interface for the in-memory URL shortener."""

import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlsplit

from src.linear_probing import LinearProbingHashTable
from src.shortener import URLShortener


def _page(title: str, content: str, table_name: str = "chaining") -> str:
    table_path = "/table" if table_name == "chaining" else "/table?table=linear"
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{escape(title)}</title></head><body>"
        f"<h1>{escape(title)}</h1>{content}"
        f'<p><a href="/">Shorten another URL</a> | <a href="{table_path}">View table</a></p>'
        "</body></html>"
    )


class ShortenerHandler(BaseHTTPRequestHandler):
    shorteners = (
        ("chaining", URLShortener()),
        ("linear", URLShortener(LinearProbingHashTable)),
    )

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
                '<label for="table">Table</label> '
                '<select id="table" name="table">'
                '<option value="chaining">Separate chaining</option>'
                '<option value="linear">Linear probing</option>'
                '</select> <button type="submit">Shorten</button></form>'
            )
            self._send_html(200, _page("URL shortener", form))
            return

        if parsed.path == "/table":
            selected = self._select_shortener(parse_qsl(parsed.query, keep_blank_values=True))
            if selected is None:
                self._send_html(400, _page("Invalid table", "<p>Choose chaining or linear.</p>"))
                return
            table_name, shortener = selected
            self._send_html(
                200,
                _page(
                    f"Hash table ({table_name})",
                    self._render_table(table_name, shortener),
                    table_name,
                ),
            )
            return

        selected = self._select_shortener(parse_qsl(parsed.query, keep_blank_values=True))
        if selected is None:
            self._send_html(400, _page("Invalid table", "<p>Choose chaining or linear.</p>"))
            return
        _, shortener = selected
        code = parsed.path.removeprefix("/")
        if not code or "/" in code:
            self._send_html(404, _page("Not found", "<p>Unknown path.</p>"))
            return
        try:
            url = shortener.expand(code)
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
        selected = self._select_shortener(fields)
        if selected is None:
            self._send_html(400, _page("Invalid table", "<p>Choose chaining or linear.</p>"))
            return
        table_name, shortener = selected
        try:
            code = shortener.shorten(url)
        except ValueError as error:
            self._send_html(400, _page("Invalid URL", f"<p>{escape(str(error))}</p>"))
            return

        table_query = "" if table_name == "chaining" else "?table=linear"
        result = (
            f'<p>Short code: <a href="/{escape(code)}{table_query}">'
            f"{escape(code)}</a> ({escape(table_name)})</p>"
            f'<p>Original URL: <a href="{escape(url, quote=True)}">'
            f"{escape(url)}</a></p>"
        )
        self._send_html(200, _page("Short URL created", result, table_name))

    def _select_shortener(self, fields: list[tuple[str, str]]) -> tuple[str, URLShortener] | None:
        table_name = next((value for key, value in fields if key == "table"), "chaining")
        for name, shortener in self.shorteners:
            if name == table_name:
                return name, shortener
        return None

    def _render_table(self, table_name: str, shortener: URLShortener) -> str:
        snapshot = shortener.table_snapshot()
        rows = []
        for bucket_index, bucket in enumerate(snapshot):
            if not bucket:
                rows.append(
                    f"<tr><td>{bucket_index}</td><td><em>empty</em></td><td></td><td></td></tr>"
                )
                continue
            for key, value in bucket:
                inspection = shortener.inspect_url(key)
                probe_path = " → ".join(str(index) for index in inspection.probe_indices)
                visited = " → ".join(escape(item_key) for item_key, _ in inspection.nodes)
                calculations = " ; ".join(
                    f"{previous} × 31 + ord({escape(repr(character))}) = {raw}; "
                    f"{raw} mod {len(snapshot)} = {reduced}"
                    for character, previous, raw, reduced in inspection.hash_steps
                )
                rows.append(
                    f"<tr><td>{bucket_index}</td><td>{escape(key)} → "
                    f"{escape(str(value))}</td><td>{probe_path or 'none'}"
                    f"<br>{visited}</td>"
                    f"<td>{calculations or 'empty key → bucket 0'}</td></tr>"
                )
        return (
            f"<p>Implementation: {escape(table_name)}.</p>"
            "<p>Horner hash: start at 0, then apply "
            "<code>(value × 31 + ord(character)) mod capacity</code>.</p>"
            "<table border=\"1\"><thead><tr><th>Bucket</th><th>Entry</th>"
            "<th>Probe path and visited keys</th><th>Hash calculation</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener web server")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    ShortenerHandler.shorteners = (
        ("chaining", URLShortener()),
        ("linear", URLShortener(LinearProbingHashTable)),
    )
    server = HTTPServer(("0.0.0.0", args.port), ShortenerHandler)
    print(f"Serving URL shortener on port {args.port}")
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
