# Moodloft

Persönliches Tool, das Inspiration zu Design, Interior, Möbeln und Fashion als eigene Pins
auf die eigenen Pinterest-Boards speichert – über die offizielle Pinterest API v5.

Website: https://octablecash.github.io/Pinterest-App/website.html

## Einrichtung (einmalig, am Computer)

1. **Python 3.9+** installieren (https://www.python.org/downloads/ – unter Windows beim
   Installieren „Add Python to PATH“ anhaken). Prüfen im Terminal: `python --version`
2. Repo herunterladen: auf GitHub **Code → Download ZIP**, entpacken, im Terminal in den Ordner
   wechseln (oder `git clone https://github.com/octablecash/Pinterest-App.git`).
3. Abhängigkeiten installieren:
   ```
   pip install -r requirements.txt
   ```
4. `.env.example` kopieren und in **`.env`** umbenennen, dann eintragen:
   - `PINTEREST_APP_ID` – App-ID aus dem Developer-Portal
   - `PINTEREST_APP_SECRET` – geheimer Schlüssel (Augen-Symbol im Portal)
   - `PINTEREST_REDIRECT_URI` – muss **exakt** der im Portal eingetragenen Weiterleitungs-URI
     entsprechen (Standard: `http://localhost:8080/callback`)

   Die `.env` bleibt nur auf deinem Rechner und wird nie hochgeladen.

5. Einloggen:
   ```
   python -m moodloft login
   ```
   Der Browser öffnet Pinterest → „Zulassen“ klicken → fertig. Access- und Refresh-Token werden
   automatisch in die `.env` geschrieben und später selbstständig erneuert.

## Benutzung

```
python -m moodloft boards                         # eigene Boards mit ID anzeigen
python -m moodloft pin https://beispiel.de/sessel --board BOARD_ID
python -m moodloft from-file urls.txt --board BOARD_ID
```

- Tipp: `PINTEREST_BOARD_ID=...` in die `.env` eintragen, dann kann `--board` entfallen.
- `pin` akzeptiert **Webseiten-Links** (das Hauptbild der Seite wird genommen, die Seite wird als
  Quelle verlinkt) und **direkte Bild-Links**.
- `urls.txt`: eine URL pro Zeile, Zeilen mit `#` werden ignoriert.
- Bereits gepinnte URLs werden übersprungen (`--force` pinnt trotzdem).
- Optional: `--title`, `--description`, `--delay` (Pause zwischen Pins, Standard 3 s).

## Fehler

| Meldung | Bedeutung |
|---|---|
| `HTTP 401` | Token abgelaufen → `python -m moodloft login` erneut ausführen |
| `HTTP 403` | App darf das (noch) nicht – z. B. nur Trial Access, Scope fehlt oder fremdes Board |
| `HTTP 429` | Zu viele Anfragen → kurz warten |
| `Kein Bild gefunden` | Seite hat kein erkennbares Hauptbild → direkten Bild-Link verwenden |
