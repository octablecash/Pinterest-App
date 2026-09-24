"""Moodloft – Kommandozeile.

  python -m moodloft login                  Einmaliger Pinterest-Login (OAuth)
  python -m moodloft boards                 Eigene Boards mit ID anzeigen
  python -m moodloft pin URL [...]          Pin aus Webseite oder Bild-URL erstellen
  python -m moodloft from-file urls.txt     Pins für alle URLs in einer Datei erstellen
"""

import argparse
import json
import sys
import time

from . import api, auth, config, extract

POSTED_FILE = config.ROOT / ".moodloft_posted.json"


def _load_posted():
    try:
        return set(json.loads(POSTED_FILE.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return set()


def _save_posted(posted):
    POSTED_FILE.write_text(json.dumps(sorted(posted), indent=2), encoding="utf-8")


def _board_id(args):
    board = args.board or config.get("PINTEREST_BOARD_ID", required=False)
    if not board:
        raise config.ConfigError(
            "Kein Board angegeben. Nutze --board ID oder setze PINTEREST_BOARD_ID in der .env "
            "(IDs zeigt 'python -m moodloft boards')."
        )
    return board


def cmd_login(args):
    auth.login()
    print("✓ Login erfolgreich. Tokens wurden lokal in .env gespeichert.")


def cmd_boards(args):
    boards = api.list_boards()
    if not boards:
        print("Keine Boards gefunden. Lege zuerst ein Board auf Pinterest an.")
    for b in boards:
        privacy = b.get("privacy", "").lower()
        print(f"{b['id']}  {b['name']}" + (f"  ({privacy})" if privacy and privacy != "public" else ""))


def _pin_one(url, board, args, posted):
    if url in posted and not args.force:
        print(f"– übersprungen (bereits gepinnt): {url}")
        return True
    try:
        info = extract.extract(url)
        pin = api.create_pin(
            board,
            info["image_url"],
            link=info["link"],
            title=args.title or info["title"],
            description=args.description or info["description"],
        )
    except api.ApiError as e:
        print(f"✗ {url}\n  {e}", file=sys.stderr)
        return False
    except Exception as e:  # Netzwerk-/Parsing-Fehler einer einzelnen URL
        print(f"✗ {url}\n  {e}", file=sys.stderr)
        return False
    posted.add(url)
    _save_posted(posted)
    print(f"✓ Pin erstellt: https://www.pinterest.com/pin/{pin.get('id')}/  ←  {url}")
    return True


def _run(urls, args):
    board = _board_id(args)
    posted = _load_posted()
    ok = 0
    for i, url in enumerate(urls):
        if i:
            time.sleep(args.delay)
        ok += _pin_one(url, board, args, posted)
    print(f"\n{ok}/{len(urls)} erfolgreich.")
    return 0 if ok == len(urls) else 1


def cmd_pin(args):
    return _run(args.urls, args)


def cmd_from_file(args):
    with open(args.file, encoding="utf-8") as f:
        urls = [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]
    return _run(urls, args)


def main():
    p = argparse.ArgumentParser(prog="moodloft", description="Eigene Pins über die Pinterest API v5 erstellen.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("login", help="Einmaliger Pinterest-Login").set_defaults(func=cmd_login)
    sub.add_parser("boards", help="Eigene Boards anzeigen").set_defaults(func=cmd_boards)

    def pin_opts(sp):
        sp.add_argument("--board", help="Board-ID (sonst PINTEREST_BOARD_ID)")
        sp.add_argument("--title", help="Titel überschreiben")
        sp.add_argument("--description", help="Beschreibung überschreiben")
        sp.add_argument("--delay", type=float, default=3.0, help="Pause zwischen Pins in Sekunden (Standard 3)")
        sp.add_argument("--force", action="store_true", help="Auch bereits gepinnte URLs erneut pinnen")

    sp = sub.add_parser("pin", help="Pin(s) aus Webseiten- oder Bild-URLs erstellen")
    sp.add_argument("urls", nargs="+")
    pin_opts(sp)
    sp.set_defaults(func=cmd_pin)

    sp = sub.add_parser("from-file", help="Pins für alle URLs einer Textdatei erstellen")
    sp.add_argument("file")
    pin_opts(sp)
    sp.set_defaults(func=cmd_from_file)

    args = p.parse_args()
    try:
        sys.exit(args.func(args) or 0)
    except (config.ConfigError, auth.AuthError, api.ApiError) as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
