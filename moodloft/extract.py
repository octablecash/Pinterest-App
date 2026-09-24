"""Ermittelt Bilder, Titel und Beschreibung einer Webseite.

- extract(url):    nur das Hauptbild (og:image & Co.) – für die Kommandozeile
- candidates(url): alle brauchbaren Bilder der Seite – zur Auswahl in der Oberfläche
"""

import re
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (Moodloft; personal Pinterest tool)"}
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif")
# Offensichtliche Nicht-Motive (Logos, Icons, Tracking-Pixel …) ausfiltern
SKIP_PATTERN = re.compile(r"logo|icon|sprite|favicon|avatar|placeholder|spinner|loader|pixel|badge|flag|payment", re.I)
MAX_CANDIDATES = 40


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = {}
        self.og_images = []
        self.imgs = []
        self.title = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            content = a.get("content", "").strip()
            if key in ("og:image", "og:image:secure_url", "twitter:image", "twitter:image:src") and content:
                self.og_images.append(content)
            if key and content and key not in self.meta:
                self.meta[key] = content
        elif tag == "link" and a.get("rel", "").lower() == "image_src" and a.get("href"):
            self.og_images.append(a["href"])
        elif tag in ("img", "source"):
            src = _best_src(a)
            if src:
                self.imgs.append((src, a.get("alt", "").strip(), a.get("width", ""), a.get("height", "")))
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and not self.title and data.strip():
            self.title = data.strip()


def _best_src(a):
    """Größte Variante aus srcset bevorzugen, sonst src/data-src."""
    for key in ("srcset", "data-srcset"):
        if a.get(key):
            best, best_w = None, -1
            for part in a[key].split(","):
                bits = part.strip().split()
                if not bits:
                    continue
                w = 0
                if len(bits) > 1 and bits[1][:-1].replace(".", "", 1).isdigit():
                    w = float(bits[1][:-1])
                if w > best_w:
                    best, best_w = bits[0], w
            if best:
                return best
    for key in ("data-src", "data-lazy-src", "data-original", "src"):
        v = a.get(key, "")
        if v and not v.startswith("data:"):
            return v
    return None


def _too_small(width, height):
    try:
        return (width and int(width) < 150) or (height and int(height) < 150)
    except ValueError:
        return False


def _fetch(url):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    is_image = resp.headers.get("Content-Type", "").startswith("image/") or \
        url.lower().split("?")[0].endswith(IMAGE_EXTENSIONS)
    return resp, is_image


def _page_info(resp):
    parser = _PageParser()
    parser.feed(resp.text)
    m = parser.meta
    return parser, {
        "link": resp.url,
        "title": m.get("og:title") or m.get("twitter:title") or parser.title,
        "description": m.get("og:description") or m.get("description") or m.get("twitter:description"),
    }


def extract(url):
    """Gibt dict mit image_url, link, title, description zurück (nur Hauptbild)."""
    resp, is_image = _fetch(url)
    if is_image:
        return {"image_url": url, "link": None, "title": None, "description": None}
    parser, info = _page_info(resp)
    image = (parser.og_images[0] if parser.og_images else None) or \
        next((src for src, _, w, h in parser.imgs if not SKIP_PATTERN.search(src) and not _too_small(w, h)), None)
    if not image:
        raise ValueError(f"Kein Bild gefunden auf {url}")
    info["image_url"] = urljoin(resp.url, image)
    info["link"] = url
    return info


def candidates(url):
    """Alle brauchbaren Bilder einer Seite (Hauptbild zuerst) plus Titel/Beschreibung."""
    resp, is_image = _fetch(url)
    if is_image:
        return {"url": url, "link": None, "title": None, "description": None, "images": [url]}
    parser, info = _page_info(resp)
    seen, images = set(), []
    for src in parser.og_images + [s for s, _, w, h in parser.imgs if not _too_small(w, h)]:
        full = urljoin(resp.url, src)
        if not full.startswith("http") or full.lower().split("?")[0].endswith(".svg"):
            continue
        if SKIP_PATTERN.search(full) or full in seen:
            continue
        seen.add(full)
        images.append(full)
        if len(images) >= MAX_CANDIDATES:
            break
    info.update({"url": url, "link": url, "images": images})
    return info
