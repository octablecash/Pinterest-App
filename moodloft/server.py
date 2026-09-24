"""Lokale Browser-Oberfläche: python -m moodloft ui

Läuft nur auf diesem Rechner (127.0.0.1). Links einfügen → Bilder auswählen →
sofort pinnen oder in die Warteschlange legen, die im Hintergrund verteilt
abgearbeitet wird (Tageslimit + Mindestabstand, siehe pinqueue.py).
"""

import json
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import api, auth, config, extract, pinqueue

UI_FILE = Path(__file__).with_name("ui.html")
LOGO_FILE = config.ROOT / "logo.svg"

state = {"auto": True, "login": "idle", "login_error": None, "worker_error": None}


def _logged_in():
    return bool(config.get("PINTEREST_ACCESS_TOKEN", required=False))


def _login_thread():
    state.update(login="pending", login_error=None)
    try:
        auth.login()
        state["login"] = "ok"
    except Exception as e:
        state.update(login="error", login_error=str(e))


def _worker():
    """Arbeitet die Warteschlange im Hintergrund ab, solange die Oberfläche läuft."""
    while True:
        time.sleep(30)
        if not state["auto"] or not _logged_in():
            continue
        item_id = pinqueue.next_due()
        if not item_id:
            continue
        try:
            pinqueue.post_item(item_id)
            state["worker_error"] = None
        except Exception as e:
            state["worker_error"] = str(e)


def _extract_many(urls):
    def one(url):
        try:
            return extract.candidates(url)
        except Exception as e:
            return {"url": url, "error": str(e), "images": []}
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(one, urls))


class Handler(BaseHTTPRequestHandler):
    server_version = "Moodloft"

    def log_message(self, *args):
        pass

    # Schutz: nur Anfragen von dieser lokalen Oberfläche annehmen
    def _allowed(self):
        port = self.server.server_address[1]
        ok_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host") not in ok_hosts:
            return False
        origin = self.headers.get("Origin")
        return origin is None or origin in {f"http://{h}" for h in ok_hosts}

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def do_GET(self):
        if not self._allowed():
            return self._send(403, {"error": "forbidden"})
        if self.path == "/":
            return self._send(200, UI_FILE.read_bytes(), "text/html; charset=utf-8")
        if self.path == "/logo.svg":
            return self._send(200, LOGO_FILE.read_bytes(), "image/svg+xml")
        if self.path == "/api/status":
            return self._send(200, {
                "logged_in": _logged_in(),
                "login": state["login"],
                "login_error": state["login_error"],
                "auto": state["auto"],
                "worker_error": state["worker_error"],
                "default_board": config.get("PINTEREST_BOARD_ID", required=False),
                "stats": pinqueue.stats(),
            })
        if self.path == "/api/boards":
            try:
                return self._send(200, {"boards": api.list_boards()})
            except Exception as e:
                return self._send(502, {"error": str(e)})
        if self.path == "/api/queue":
            return self._send(200, {"items": list(reversed(pinqueue.items()))})
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._allowed():
            return self._send(403, {"error": "forbidden"})
        try:
            body = self._json()
            if self.path == "/api/login":
                if state["login"] != "pending":
                    threading.Thread(target=_login_thread, daemon=True).start()
                return self._send(200, {"ok": True})
            if self.path == "/api/extract":
                urls = [u.strip() for u in body.get("urls", []) if u.strip().startswith("http")]
                return self._send(200, {"pages": _extract_many(urls[:30])})
            if self.path == "/api/queue":
                if not body.get("board_id"):
                    return self._send(400, {"error": "Bitte zuerst ein Board wählen."})
                added = pinqueue.add(body.get("items", []), body["board_id"])
                if body.get("now") and added:
                    # Nur das erste Bild sofort, der Rest wird verteilt abgearbeitet
                    try:
                        pinqueue.post_item(added[0]["id"], ignore_gap=True)
                        results = [{"id": added[0]["id"], "ok": True}]
                    except Exception as e:
                        results = [{"id": added[0]["id"], "ok": False, "error": str(e)}]
                    return self._send(200, {"added": len(added), "results": results})
                return self._send(200, {"added": len(added)})
            if self.path == "/api/queue/remove":
                pinqueue.remove(body["id"])
                return self._send(200, {"ok": True})
            if self.path == "/api/queue/retry":
                pinqueue.retry(body["id"])
                return self._send(200, {"ok": True})
            if self.path == "/api/auto":
                state["auto"] = bool(body.get("auto"))
                return self._send(200, {"auto": state["auto"]})
            self._send(404, {"error": "not found"})
        except Exception as e:
            self._send(500, {"error": str(e)})


def serve(port=8765, open_browser=True):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=_worker, daemon=True).start()
    url = f"http://127.0.0.1:{port}/"
    print(f"Moodloft läuft auf {url}  (beenden mit Ctrl+C)")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
