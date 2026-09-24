# Demo-Video für den Standard-Access-Antrag

Ziel: In 1–2 Minuten zeigen, **was Moodloft wirklich tut** – Login über Pinterest-OAuth,
eigene Boards, selbst ausgewählte Bilder, Pin mit Quell-Link.

## Vorbereitung

- Am Mac: Moodloft ist eingerichtet (siehe `README.md`), mindestens ein **öffentliches Board**
  existiert (z. B. „Interior“).
- In der `.env` die Zeilen `PINTEREST_ACCESS_TOKEN=` und `PINTEREST_REFRESH_TOKEN=` **leeren**,
  damit der Login im Video zu sehen ist.
- 1–2 Links zu Produktseiten bereithalten (z. B. ein Sessel, eine Leuchte).
- Aufnahme: `Cmd + Shift + 5` → „Ganzen Bildschirm aufnehmen“ (oder nur das Browserfenster).
- Browser-Zoom so, dass alles gut lesbar ist; keine privaten Tabs/Lesezeichen sichtbar.

## Ablauf (Drehbuch)

| # | Was du zeigst | Text / Einblendung (Englisch, fürs Pinterest-Team) |
|---|---|---|
| 1 | Moodloft-Website `…/website.html` kurz scrollen | "Moodloft is my personal, non-commercial tool to save design, interior and fashion inspiration to my own Pinterest boards." |
| 2 | Terminal: `python -m moodloft ui` → Moodloft öffnet sich im Browser | "The app runs locally on my computer." |
| 3 | Button **„Mit Pinterest anmelden“** → Pinterest-Zustimmungsseite → **Zulassen** | "I sign in with the official Pinterest OAuth flow and grant boards:read, pins:read and pins:write." |
| 4 | Zurück in Moodloft: „Mit Pinterest verbunden“, oben rechts das Board wählen | "The app reads my own boards so I can choose where to save." |
| 5 | Link einfügen → **Bilder suchen** → 1 Bild antippen, Titel kurz zeigen | "I paste a page I like and hand-pick the image myself." |
| 6 | **Jetzt pinnen** → Meldung „Pin erstellt“ → in der Warteschlange auf **ansehen** | "The app creates a Pin on my own board via POST /v5/pins." |
| 7 | Pin auf Pinterest: Bild, Titel, **Quell-Link** anklicken → Original-Webseite öffnet sich | "Every Pin links back to the original source so the creator is credited." |
| 8 | Zurück zu Moodloft: Bereich „Warteschlange“ mit Tageslimit zeigen | "Saving is rate-limited to a few Pins per day. No bulk posting, no access to other users' data." |

## Tipps

- Lieber ruhig und langsam klicken; Schnitte sind okay, aber den OAuth-Schritt (3) komplett zeigen.
- Den Text kannst du als Untertitel einblenden (iMovie → Titel) oder einfach sprechen.
- Hochladen z. B. als nicht gelistetes YouTube-Video oder direkt im Formular, je nachdem was
  Pinterest verlangt.
- Das Video muss zu Website und Antrag passen: persönlich, selbst ausgewählt, mit Quell-Link.
