"""Mock OpenAI-compatible server for end-to-end testing.

Run:  python tests/mock_openai_server.py
Listens on http://0.0.0.0:9001

Endpoints:
  GET  /health          → health check
  POST /chat/completions → returns a canned chat completion response
  POST /v1/chat/completions → same (some clients use /v1 prefix)
"""
import json
import time
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler


class MockOpenAIHandler(BaseHTTPRequestHandler):
    """Minimal OpenAI-compatible HTTP handler."""

    def _json_response(self, status: int, data: dict) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/health", "/"):
            self._json_response(200, {"status": "ok", "service": "mock-openai"})
        elif self.path == "/v1/models":
            self._json_response(200, {
                "object": "list",
                "data": [
                    {"id": "gpt-3.5-turbo", "object": "model", "created": 1686935002, "owned_by": "openai"},
                    {"id": "gpt-4", "object": "model", "created": 1687882411, "owned_by": "openai"},
                ]
            })
        else:
            self._json_response(404, {"error": "not found"})

    def do_POST(self) -> None:
        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            request_data = json.loads(body)
        except json.JSONDecodeError:
            request_data = {}

        model = request_data.get("model", "unknown")
        messages = request_data.get("messages", [])

        # Handle /chat/completions (both with and without /v1 prefix)
        if self.path in ("/chat/completions", "/v1/chat/completions"):
            self._json_response(200, {
                "id": f"chatcmpl-mock-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"Mock response to: {messages[-1].get('content', '?')[:100] if messages else 'empty'}",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 15,
                    "completion_tokens": 8,
                    "total_tokens": 23,
                },
            })
        elif self.path in ("/auth/register", "/auth/login", "/keys", "/keys/"):
            # These shouldn't reach the mock — they go to the app
            self._json_response(404, {"error": "this is a mock OpenAI server, not the app"})
        else:
            self._json_response(404, {"error": f"unknown endpoint: {self.path}"})

    def log_message(self, format, *args):
        """Log to stdout with a prefix."""
        print(f"[mock-openai] {self.address_string()} - {format % args}", flush=True)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9001
    server = HTTPServer(("0.0.0.0", port), MockOpenAIHandler)
    print(f"🚀 Mock OpenAI server listening on http://0.0.0.0:{port}")
    print(f"   Endpoints: /health, /chat/completions, /v1/chat/completions, /v1/models")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
