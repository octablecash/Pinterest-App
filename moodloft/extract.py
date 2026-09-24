"""Ermittelt zu einer Webseiten-URL das Hauptbild (og:image & Co.) plus Titel/Beschreibung."""

from html.parser import HTMLParser
from urllib.parse import urljoin

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (Moodloft; personal Pinterest tool)"}
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")


class _MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.first_img = None
        self.title = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key and a.get("content") and key not in self.meta:
                self.meta[key] = a["content"].strip()
        elif tag == "link" and a.get("rel", "").lower() == "image_src" and a.get("href"):
            self.meta.setdefault("image_src", a["href"])
        elif tag == "img" and self.first_img is None:
            src = a.get("src") or a.get("data-src")
            if src and not src.startswith("data:"):
                self.first_img = src
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and not self.title and data.strip():
            self.title = data.strip()


def extract(url):
    """Gibt dict mit image_url, link, title, description zurück."""
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    if resp.headers.get("Content-Type", "").startswith("image/") or url.lower().split("?")[0].endswith(IMAGE_EXTENSIONS):
        return {"image_url": url, "link": None, "title": None, "description": None}

    parser = _MetaParser()
    parser.feed(resp.text)
    m = parser.meta
    image = (m.get("og:image:secure_url") or m.get("og:image") or m.get("twitter:image")
             or m.get("twitter:image:src") or m.get("image_src") or parser.first_img)
    if not image:
        raise ValueError(f"Kein Bild gefunden auf {url}")

    return {
        "image_url": urljoin(resp.url, image),
        "link": url,
        "title": m.get("og:title") or m.get("twitter:title") or parser.title,
        "description": m.get("og:description") or m.get("description") or m.get("twitter:description"),
    }
