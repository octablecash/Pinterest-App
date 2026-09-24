"""Schlanker Client für die benötigten Pinterest-API-v5-Endpunkte."""

import requests

from . import auth, config


class ApiError(RuntimeError):
    pass


HINTS = {
    401: "Token ungültig oder abgelaufen. Führe 'python -m moodloft login' erneut aus.",
    403: ("Zugriff verweigert. Mögliche Ursachen: Die App hat nur Trial Access und darf diese "
          "Aktion noch nicht ausführen (Standard Access beantragen), ein Scope fehlt, oder das "
          "Board gehört nicht dir."),
    429: "Rate-Limit erreicht. Warte ein paar Minuten und versuche es erneut.",
}


def _request(method, path, retry=True, **kwargs):
    token = config.get("PINTEREST_ACCESS_TOKEN")
    resp = requests.request(
        method,
        f"{config.API_BASE}{path}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
        **kwargs,
    )
    if resp.status_code == 401 and retry and config.get("PINTEREST_REFRESH_TOKEN", required=False):
        auth.refresh()
        return _request(method, path, retry=False, **kwargs)
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("message", resp.text)
        except ValueError:
            detail = resp.text
        hint = HINTS.get(resp.status_code, "")
        raise ApiError(f"HTTP {resp.status_code}: {detail}" + (f"\n→ {hint}" if hint else ""))
    return resp.json() if resp.content else {}


def list_boards():
    boards, bookmark = [], None
    while True:
        params = {"page_size": 100}
        if bookmark:
            params["bookmark"] = bookmark
        data = _request("GET", "/boards", params=params)
        boards.extend(data.get("items", []))
        bookmark = data.get("bookmark")
        if not bookmark:
            return boards


def create_pin(board_id, image_url, link=None, title=None, description=None, alt_text=None):
    body = {
        "board_id": board_id,
        "media_source": {"source_type": "image_url", "url": image_url},
    }
    if link:
        body["link"] = link
    if title:
        body["title"] = title[:100]
    if description:
        body["description"] = description[:800]
    if alt_text:
        body["alt_text"] = alt_text[:500]
    return _request("POST", "/pins", json=body)
