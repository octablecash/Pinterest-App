"""Warteschlange mit Tageslimit und Mindestabstand zwischen Pins.

Beliebig viele Bilder können vorgemerkt werden; gepinnt wird verteilt
(Standard: max. 15 Pins pro Tag, mind. 20 Minuten Abstand), damit das Konto
wie ein aktiver Kurator wirkt und nicht wie ein Bot.
Gespeichert wird lokal in .moodloft_queue.json (nicht im Repo).
"""

import json
import os
import threading
import uuid
from datetime import datetime, timedelta

from . import api, config

FILE = config.ROOT / ".moodloft_queue.json"
_lock = threading.RLock()


class LimitReached(RuntimeError):
    pass


def daily_limit():
    return int(os.getenv("MOODLOFT_DAILY_LIMIT", "15"))


def min_gap():
    return timedelta(minutes=float(os.getenv("MOODLOFT_MIN_GAP_MINUTES", "20")))


def _now():
    return datetime.now().replace(microsecond=0)


def _load():
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []


def _save(items):
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(FILE)


def items():
    with _lock:
        return _load()


def add(entries, board_id):
    """entries: dicts mit image_url, link, title, description. Gibt Anzahl neu vorgemerkter zurück."""
    with _lock:
        data = _load()
        known = {i["image_url"] for i in data if i["status"] != "failed"}
        added = []
        for e in entries:
            if not e.get("image_url") or e["image_url"] in known:
                continue
            known.add(e["image_url"])
            item = {
                "id": uuid.uuid4().hex[:10],
                "image_url": e["image_url"],
                "link": e.get("link"),
                "title": (e.get("title") or "")[:100] or None,
                "description": (e.get("description") or "")[:800] or None,
                "board_id": board_id,
                "status": "queued",
                "added_at": _now().isoformat(),
            }
            data.append(item)
            added.append(item)
        _save(data)
        return added


def remove(item_id):
    with _lock:
        data = _load()
        _save([i for i in data if not (i["id"] == item_id and i["status"] in ("queued", "failed"))])


def retry(item_id):
    with _lock:
        data = _load()
        for i in data:
            if i["id"] == item_id and i["status"] == "failed":
                i["status"], i["error"] = "queued", None
        _save(data)


def stats(data=None):
    data = _load() if data is None else data
    today = _now().date()
    posted = [datetime.fromisoformat(i["posted_at"]) for i in data if i.get("posted_at")]
    posted_today = sum(1 for p in posted if p.date() == today)
    last = max(posted) if posted else None
    remaining = max(0, daily_limit() - posted_today)
    if remaining == 0:
        next_at = datetime.combine(today + timedelta(days=1), datetime.min.time())
    else:
        next_at = max(_now(), last + min_gap()) if last else _now()
    return {
        "daily_limit": daily_limit(),
        "posted_today": posted_today,
        "remaining_today": remaining,
        "queued": sum(1 for i in data if i["status"] == "queued"),
        "failed": sum(1 for i in data if i["status"] == "failed"),
        "last_posted_at": last.isoformat() if last else None,
        "next_possible_at": next_at.isoformat(),
    }


def post_item(item_id, ignore_gap=False):
    """Pinnt ein vorgemerktes Bild. Das Tageslimit gilt immer, der Mindestabstand optional."""
    with _lock:
        data = _load()
        item = next((i for i in data if i["id"] == item_id), None)
        if not item or item["status"] != "queued":
            raise ValueError("Eintrag nicht gefunden oder bereits erledigt.")
        s = stats(data)
        if s["remaining_today"] <= 0:
            raise LimitReached(f"Tageslimit von {s['daily_limit']} Pins erreicht – morgen geht's weiter.")
        if not ignore_gap and datetime.fromisoformat(s["next_possible_at"]) > _now():
            raise LimitReached(f"Nächster Pin erst ab {s['next_possible_at'][11:16]} Uhr (Mindestabstand).")
        try:
            pin = api.create_pin(item["board_id"], item["image_url"], link=item.get("link"),
                                 title=item.get("title"), description=item.get("description"))
            item.update(status="posted", posted_at=_now().isoformat(), pin_id=pin.get("id"), error=None)
        except api.ApiError as e:
            item.update(status="failed", error=str(e))
            _save(data)
            raise
        _save(data)
        return item


def next_due():
    """ID des nächsten Eintrags, der jetzt gepinnt werden darf – oder None."""
    with _lock:
        data = _load()
        s = stats(data)
        if s["remaining_today"] <= 0 or datetime.fromisoformat(s["next_possible_at"]) > _now():
            return None
        return next((i["id"] for i in data if i["status"] == "queued"), None)
