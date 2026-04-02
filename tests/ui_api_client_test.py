"""Tests for the Streamlit API client helpers."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler
from http.server import ThreadingHTTPServer
from threading import Thread

from contentcreajudge.ui.services.api_client import request_json


class _PlainTextHandler(BaseHTTPRequestHandler):
    """Serve a plain text response to exercise non-JSON backend handling."""

    def do_GET(self) -> None:  # noqa: N802
        """Return a plain text payload."""
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"service warming up")

    def log_message(self, format: str, *args: object) -> None:
        """Silence request logs during tests."""


def test_request_json_returns_error_for_non_json_response() -> None:
    """The UI client should not crash when the backend returns plain text."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), _PlainTextHandler)
    server_thread = Thread(target=server.serve_forever)
    server_thread.start()

    try:
        host, port = server.server_address
        result = request_json(f"http://{host}:{port}/health")
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()

    assert result.ok is False
    assert result.status_code == 200
    assert result.payload == {}
    assert result.error == "Backend returned a non-JSON response."
