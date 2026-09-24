"""OAuth 2.0 (Authorization Code Grant) für die Pinterest API v5.

Der erste Login läuft lokal: Browser öffnet Pinterest, nach der Freigabe leitet
Pinterest auf die Redirect URI (http://localhost:...) um, wo dieses Skript den
Code entgegennimmt und gegen Access- und Refresh-Token tauscht.
"""

import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from . import config

TOKEN_URL = f"{config.API_BASE}/oauth/token"


class AuthError(RuntimeError):
    pass


def _credentials():
    return config.get("PINTEREST_APP_ID"), config.get("PINTEREST_APP_SECRET")


def _token_request(data):
    resp = requests.post(TOKEN_URL, data=data, auth=_credentials(), timeout=30)
    if resp.status_code != 200:
        raise AuthError(f"Token-Anfrage fehlgeschlagen ({resp.status_code}): {resp.text}")
    return resp.json()


def _store(tokens):
    updates = {"PINTEREST_ACCESS_TOKEN": tokens["access_token"]}
    if tokens.get("refresh_token"):
        updates["PINTEREST_REFRESH_TOKEN"] = tokens["refresh_token"]
    config.save_env(updates)


def login():
    redirect_uri = config.get("PINTEREST_REDIRECT_URI")
    parsed = urlparse(redirect_uri)
    if parsed.hostname not in ("localhost", "127.0.0.1"):
        raise AuthError("PINTEREST_REDIRECT_URI muss auf localhost zeigen, z. B. http://localhost:8080/callback")

    state = secrets.token_urlsafe(24)
    result = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlparse(self.path)
            if url.path != parsed.path:
                self.send_response(404)
                self.end_headers()
                return
            query = parse_qs(url.query)
            result.update({k: v[0] for k, v in query.items()})
            ok = "code" in result and result.get("state") == state
            self.send_response(200 if ok else 400)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = "Login erfolgreich – du kannst dieses Fenster schließen." if ok else "Login fehlgeschlagen."
            self.wfile.write(f"<h2>Moodloft</h2><p>{msg}</p>".encode("utf-8"))
            threading.Thread(target=self.server.shutdown, daemon=True).start()

        def log_message(self, *args):
            pass

    server = HTTPServer((parsed.hostname, parsed.port or 80), Handler)
    params = {
        "client_id": config.get("PINTEREST_APP_ID"),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": ",".join(config.SCOPES),
        "state": state,
    }
    auth_link = f"{config.AUTH_URL}?{urlencode(params)}"
    print("Öffne den Pinterest-Login im Browser …")
    print(f"Falls sich nichts öffnet, kopiere diesen Link in den Browser:\n{auth_link}\n")
    webbrowser.open(auth_link)
    server.serve_forever()
    server.server_close()

    if result.get("state") != state:
        raise AuthError("Ungültiger state-Parameter – Login abgebrochen.")
    if "code" not in result:
        raise AuthError(f"Kein Code erhalten: {result.get('error_description') or result.get('error') or result}")

    tokens = _token_request({
        "grant_type": "authorization_code",
        "code": result["code"],
        "redirect_uri": redirect_uri,
    })
    _store(tokens)
    return tokens


def refresh():
    tokens = _token_request({
        "grant_type": "refresh_token",
        "refresh_token": config.get("PINTEREST_REFRESH_TOKEN"),
        "scope": ",".join(config.SCOPES),
    })
    _store(tokens)
    return tokens["access_token"]
