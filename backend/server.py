"""HTTP backend: serve the frontend and read students from the CSV database."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from backend.database import students
from backend.models import CompetencyModel

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
HOST = "127.0.0.1"
PORT = 8000


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/api/students":
            body = json.dumps(students()).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        elif path == "/api/competencies":
            averages = [row.to_dict() for row in CompetencyModel().averages()]
            body = json.dumps(averages).encode("utf-8")
            content_type = "application/json; charset=utf-8"
        elif path in ("/", "/index.html"):
            body = (FRONTEND / "index.html").read_bytes()
            content_type = "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} {fmt % args}")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Serving http://{HOST}:{PORT}")
    server.serve_forever()
