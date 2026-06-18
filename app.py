#!/usr/bin/env python3
import json
import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, urlsplit


DB_PATH = Path(os.environ.get("OPENHEART_DB", os.environ.get("OPENHEART_STORE", "/data/openheart.db")))
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))
ALLOWED_DOMAINS = [
    domain.strip().lower().lstrip(".")
    for domain in os.environ.get("OPENHEART_ALLOWED_DOMAINS", "").split(",")
    if domain.strip()
]
ALLOWED_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.environ.get("OPENHEART_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
}

lock = threading.Lock()
db = None


def init_db():
    global db
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None, check_same_thread=False)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=30000")
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS reactions (
            path TEXT NOT NULL,
            emoji TEXT NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (path, emoji)
        )
        """
    )


def load_counts(path: str) -> dict[str, int]:
    rows = db.execute(
        "SELECT emoji, count FROM reactions WHERE path = ? ORDER BY emoji",
        (path,),
    ).fetchall()
    return {emoji: count for emoji, count in rows}


def increment_reaction(path: str, emoji: str) -> dict[str, int]:
    db.execute("BEGIN IMMEDIATE")
    try:
        db.execute(
            """
            INSERT INTO reactions (path, emoji, count)
            VALUES (?, ?, 1)
            ON CONFLICT(path, emoji) DO UPDATE SET count = count + 1
            """,
            (path, emoji),
        )
        db.execute("COMMIT")
    except Exception:
        db.execute("ROLLBACK")
        raise
    return load_counts(path)


def parse_reaction(body: str) -> str:
    body = body.strip()
    if body == "=":
        return ""
    return body


def request_host(self) -> str:
    host = self.headers.get("Host", "").strip().lower()
    if not host:
        return ""
    return urlparse("//" + host).hostname or ""


def host_allowed(host: str) -> bool:
    host = host.lower()
    return any(host == domain or host.endswith("." + domain) for domain in ALLOWED_DOMAINS)


def request_origin(self) -> str:
    origin = self.headers.get("Origin") or self.headers.get("Referer") or ""
    if not origin:
        return ""
    parsed = urlparse(origin)
    return parsed.hostname or ""


def reject_if_disallowed(self) -> bool:
    if not ALLOWED_DOMAINS:
        return False
    origin_host = request_origin(self)
    if not origin_host:
        return False
    if host_allowed(origin_host):
        return False
    self.send_response(403)
    self.send_header("Content-Type", "text/plain; charset=utf-8")
    self.end_headers()
    self.wfile.write(b"forbidden")
    return True


def tenant_key(self, path: str) -> str:
    host = request_host(self) or "localhost"
    return f"{host}|{path}"


def request_origin_header(self) -> str:
    return (self.headers.get("Origin") or "").strip().rstrip("/")


def cors_origin_allowed(self) -> str:
    if not ALLOWED_ORIGINS:
        return ""
    origin = request_origin_header(self)
    return origin if origin in ALLOWED_ORIGINS else ""


class Handler(BaseHTTPRequestHandler):
    def _path_key(self) -> str:
        return urlsplit(self.path).path or "/"

    def _send_json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        origin = cors_origin_allowed(self)
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Credentials", "false")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_plain(self, text, status=200):
        data = text.encode("utf-8")
        self.send_response(status)
        origin = cors_origin_allowed(self)
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Credentials", "false")
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_cors_preflight(self):
        origin = cors_origin_allowed(self)
        if not origin:
            self.send_response(403)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"forbidden")
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Credentials", "false")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        request_headers = self.headers.get("Access-Control-Request-Headers", "Content-Type, Accept")
        self.send_header("Access-Control-Allow-Headers", request_headers)
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_OPTIONS(self):
        if reject_if_disallowed(self):
            return
        self._send_cors_preflight()

    def do_GET(self):
        if reject_if_disallowed(self):
            return
        path = self._path_key()
        key = tenant_key(self, path)
        with lock:
            counts = load_counts(key)

        if path == "/":
            html = ["<!doctype html><meta charset='utf-8'><title>OpenHeart</title>"]
            html.append("<form method='POST' enctype='text/plain'><button name=''>❤️</button></form>")
            html.append("<pre>" + json.dumps(counts, ensure_ascii=False, indent=2) + "</pre>")
            data = "".join(html).encode("utf-8")
            self.send_response(200)
            origin = cors_origin_allowed(self)
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
                self.send_header("Access-Control-Allow-Credentials", "false")
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        self._send_json(counts)

    def do_POST(self):
        if reject_if_disallowed(self):
            return
        path = self._path_key()
        key = tenant_key(self, path)
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8", "ignore")
        reaction = parse_reaction(body)

        with lock:
            counts = increment_reaction(key, reaction)

        self._send_json(counts, 201)

    def log_message(self, format, *args):
        return


def self_test():
    assert parse_reaction("=") == ""
    assert parse_reaction(" ❤️ ") == "❤️"
    assert parse_reaction("👍 extra") == "👍 extra"
    assert host_allowed("sub.example.com") is False

    class Dummy:
        headers = {"Host": "example.com:8080"}

    assert tenant_key(Dummy(), "/heart") == "example.com|/heart"


if __name__ == "__main__":
    if os.environ.get("OPENHEART_SELFTEST") == "1":
        self_test()
        raise SystemExit(0)

    init_db()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.serve_forever()
