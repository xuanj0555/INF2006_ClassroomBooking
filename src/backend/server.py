"""Local development server. Demo account selection is NOT production authentication.

Booking rules live in bookingService.py; routing lives in API.py.
This file only does HTTP plumbing, static files and the demo session cookie.
Run:  python src/backend/server.py   ->  http://127.0.0.1:8765
"""
import json
import os
import secrets
import sys
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from API import dispatch
from adminService import RoomlyService

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "src" / "frontend"
DB = Path(os.environ.get("BOOKING_DB", str(ROOT / "roomly.sqlite3")))
STATIC = {"/", "/index.html", "/app.js", "/style.css", "/favicon.svg"}
MAX_BODY = 10_000

service = RoomlyService(DB, history_csv=ROOT / "data" / "reservations_cleaned_newversion.csv")
SESSIONS = {}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)

    # ---- helpers ----
    def send_json(self, status, data, cookie=None):
        raw = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(raw)

    def session_token(self):
        jar = SimpleCookie()
        jar.load(self.headers.get("Cookie", ""))
        return jar["session"].value if "session" in jar else None

    def current_user_id(self):
        token = self.session_token()
        return SESSIONS.get(token) if token else None

    def read_body(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            if n < 0 or n > MAX_BODY:
                raise ValueError
            body = json.loads(self.rfile.read(n) or "{}")
            if not isinstance(body, dict):
                raise ValueError
            return body
        except (ValueError, TypeError):
            return None

    def origin_ok(self):
        origin = self.headers.get("Origin")
        return not origin or origin == f"http://{self.headers.get('Host')}"

    def run_api(self, method, body=None):
        p = urlparse(self.path)
        status, data = dispatch(service, method, p.path, dict(parse_qsl(p.query)), body, self.current_user_id())
        self.send_json(status, data)

    def do_GET(self):
        p = urlparse(self.path)
        if not p.path.startswith("/api/"):
            return super().do_GET() if p.path in STATIC else self.send_error(404)
        if p.path == "/api/session":
            uid = self.current_user_id()
            user = service.get_user(uid) if uid else None
            return self.send_json(200, {
                "user": {"user_id": user["user_id"], "name": user["name"], "role": user["role"],
                         "is_admin": bool(user["is_admin"])} if user else None,
                "today": service.now().date().isoformat(),
            })
        if p.path == "/api/demo-accounts":
            return self.send_json(200, {"accounts": service.demo_accounts()})
        self.run_api("GET")

    def do_POST(self):
        if not self.origin_ok():
            return self.send_json(403, {"code": "bad_origin", "message": "Request origin rejected."})
        body = self.read_body()
        if body is None:
            return self.send_json(400, {"code": "invalid_input", "message": "Invalid request."})
        path = urlparse(self.path).path
        if path == "/api/demo-login":
            user = service.get_user(body.get("user_id"))
            if not user or not user["is_active"]:
                return self.send_json(400, {"code": "unknown_account", "message": "Unknown demo account."})
            token = secrets.token_urlsafe(32)
            SESSIONS[token] = user["user_id"]
            return self.send_json(200, {"ok": True}, f"session={token}; HttpOnly; SameSite=Strict; Path=/")
        if path == "/api/logout":
            SESSIONS.pop(self.session_token(), None)
            return self.send_json(200, {"ok": True}, "session=; Max-Age=0; HttpOnly; SameSite=Strict; Path=/")
        self.run_api("POST", body)

    def do_DELETE(self):
        if not self.origin_ok():
            return self.send_json(403, {"code": "bad_origin", "message": "Request origin rejected."})
        self.run_api("DELETE")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8765"))
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Open http://127.0.0.1:{port} - local demo only", flush=True)
    httpd.serve_forever()