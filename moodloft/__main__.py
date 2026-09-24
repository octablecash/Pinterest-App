"""Moodloft – Kommandozeile.

  python -m moodloft ui                     Oberfläche im Browser öffnen (empfohlen)
  python -m moodloft login                  Einmaliger Pinterest-Login (OAuth)
  python -m moodloft boards                 Eigene Boards mit ID anzeigen
  python -m moodloft pin URL                Einen Pin sofort erstellen (Webseite oder Bild-URL)
  python -m moodloft add URL [...]          Hauptbilder von Webseiten in die Warteschlange legen
  python -m moodloft from-file urls.txt     Wie add, URLs aus einer Datei
  python -m moodloft queue                  Warteschlange und Tageslimit anzeigen
  python -m moodloft run [--watch]          Fällige Pins aus der Warteschlange erstellen
"""

import argparse
import sys
import time
from datetime import datetime

from . import api, auth, config, extract, pinqueue


def _board_id(args):
    board = args.board or config.get("PINTEREST_BOARD_ID", required=False)
    if not board:
        raise config.ConfigError(
            "Kein Board angegeben. Nutze --board ID oder setze PINTEREST_BOARD_ID in der .env "
            "(IDs zeigt 'python -m moodloft boards')."
        )
    return board


def _entries(urls, args):
    out = []
    for url in urls:
        try:
            info = extract.extract(url)
        except Exception as e:
            print(f"✗ {url}\n  {e}", file=sys.stderr)
            continue
        out.append({
            "image_url": info["image_url"],
            "link": info["link"],
            "title": args.title or info["title"],
            "description": args.description or info["description"],
        })
    return out


def _print_stats():
    s = pinqueue.stats()
    nxt = "morgen" if not s["remaining_today"] else s["next_possible_at"][11:16] + " Uhr"
    print(f"Heute gepinnt: {s['posted_today']}/{s['daily_limit']} · in Warteschlange: {s['queued']}"
          + (f" · nächster Pin ab {nxt}" if s["queued"] else "")
          + (f" · Fehler: {s['failed']}" if s["failed"] else ""))


def cmd_ui(args):
    from . import server
    server.serve(port=args.port, open_browser=not args.no_browser)


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


def cmd_pin(args):
    entries = _entries([args.url], args)
    if not entries:
        return 1
    added = pinqueue.add(entries, _board_id(args))
    if not added:
        print("– Dieses Bild ist bereits gepinnt oder vorgemerkt.")
        return 0
    try:
        item = pinqueue.post_item(added[0]["id"], ignore_gap=True)
    except pinqueue.LimitReached as e:
        print(f"⏸ {e} Das Bild bleibt in der Warteschlange.")
        return 1
    print(f"✓ Pin erstellt: https://www.pinterest.com/pin/{item.get('pin_id')}/")
    _print_stats()
    return 0


def cmd_add(args):
    added = pinqueue.add(_entries(args.urls, args), _board_id(args))
    print(f"✓ {len(added)} Bild(er) in die Warteschlange gelegt.")
    _print_stats()
    return 0


def cmd_from_file(args):
    with open(args.file, encoding="utf-8") as f:
        args.urls = [l.strip() for l in f if l.strip() and not l.lstrip().startswith("#")]
    return cmd_add(args)


def cmd_queue(args):
    _print_stats()
    for i in pinqueue.items()[-args.limit:]:
        extra = i.get("posted_at", "")[11:16] if i["status"] == "posted" else (i.get("error") or "")
        print(f"  [{i['status']:6}] {(i.get('title') or '(ohne Titel)')[:50]:50}  {extra}")


def cmd_run(args):
    while True:
        item_id = pinqueue.next_due()
        if item_id:
            try:
                item = pinqueue.post_item(item_id)
                print(f"✓ {datetime.now():%H:%M} Pin erstellt: https://www.pinterest.com/pin/{item.get('pin_id')}/")
            except api.ApiError as e:
                print(f"✗ {e}", file=sys.stderr)
            continue
        s = pinqueue.stats()
        if not args.watch or not s["queued"]:
            _print_stats()
            return 0
        wait = max(30, (datetime.fromisoformat(s["next_possible_at"]) - datetime.now()).total_seconds())
        print(f"… warte bis {datetime.fromisoformat(s['next_possible_at']):%d.%m. %H:%M} ({s['queued']} in Warteschlange)")
        time.sleep(min(wait, 3600))


def main():
    p = argparse.ArgumentParser(prog="moodloft", description="Eigene Pins über die Pinterest API v5 erstellen.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("ui", help="Oberfläche im Browser öffnen")
    sp.add_argument("--port", type=int, default=8765)
    sp.add_argument("--no-browser", action="store_true")
    sp.set_defaults(func=cmd_ui)

    sub.add_parser("login", help="Einmaliger Pinterest-Login").set_defaults(func=cmd_login)
    sub.add_parser("boards", help="Eigene Boards anzeigen").set_defaults(func=cmd_boards)

    def pin_opts(sp):
        sp.add_argument("--board", help="Board-ID (sonst PINTEREST_BOARD_ID)")
        sp.add_argument("--title", help="Titel überschreiben")
        sp.add_argument("--description", help="Beschreibung überschreiben")

    sp = sub.add_parser("pin", help="Einen Pin sofort erstellen")
    sp.add_argument("url")
    pin_opts(sp)
    sp.set_defaults(func=cmd_pin)

    sp = sub.add_parser("add", help="Webseiten in die Warteschlange legen")
    sp.add_argument("urls", nargs="+")
    pin_opts(sp)
    sp.set_defaults(func=cmd_add)

    sp = sub.add_parser("from-file", help="URLs aus Textdatei in die Warteschlange legen")
    sp.add_argument("file")
    pin_opts(sp)
    sp.set_defaults(func=cmd_from_file)

    sp = sub.add_parser("queue", help="Warteschlange anzeigen")
    sp.add_argument("--limit", type=int, default=20)
    sp.set_defaults(func=cmd_queue)

    sp = sub.add_parser("run", help="Fällige Pins erstellen")
    sp.add_argument("--watch", action="store_true", help="Weiterlaufen, bis die Warteschlange leer ist")
    sp.set_defaults(func=cmd_run)

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
