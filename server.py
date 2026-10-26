"""Local server with no third-party dependencies; same engine as FastAPI."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from backend.api import dispatch
from backend.engine import ReleaseService

service = None


class Handler(BaseHTTPRequestHandler):
    def respond(self, code, payload):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def handle_request(self):
        if self.headers.get("Origin") not in {None, "http://localhost:3000", "http://127.0.0.1:3000"}:
            return self.respond(403, {"detail": "Origin not allowed"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 0 or size > 1_000_000:
                return self.respond(413, {"detail": "Request too large"})
            body = json.loads(self.rfile.read(size)) if size else {}
            if not isinstance(body, dict):
                raise ValueError("Expected a JSON object")
            return self.respond(200, dispatch(service, self.command, self.path, body))
        except KeyError as exc:
            return self.respond(404, {"detail": str(exc)})
        except ValueError as exc:
            return self.respond(400, {"detail": str(exc)})
        except Exception:
            return self.respond(500, {"detail": "Evidence service failed. No passing evidence was generated."})

    do_GET = handle_request
    do_POST = handle_request


if __name__ == "__main__":
    service = ReleaseService(recover=True)
    port = int(os.getenv("RELEASEPROOF_PORT", "8000"))
    print(f"ReleaseProof evidence API on http://127.0.0.1:{port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()

