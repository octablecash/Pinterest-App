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

### Oberfläche (empfohlen)

```
python -m moodloft ui
```

Öffnet Moodloft im Browser (läuft nur auf deinem Rechner, `http://127.0.0.1:8765`):

1. Oben rechts das **Board** wählen.
2. **Links einfügen** (eine Webseite pro Zeile) → **Bilder suchen**.
3. Die gewünschten Bilder **antippen**, Titel/Beschreibung bei Bedarf anpassen.
4. **In Warteschlange** – oder **Jetzt pinnen** (erstes Bild sofort, Rest in die Warteschlange).

Solange die Oberfläche offen ist, arbeitet sie die Warteschlange automatisch ab.

### Warteschlange & Tageslimit

Du kannst beliebig viele Bilder vormerken – gepinnt wird **verteilt**: standardmäßig
höchstens **15 Pins pro Tag** mit mindestens **20 Minuten Abstand**. So wirkt das Konto wie ein
aktiver Kurator statt wie ein Bot. Anpassbar in der `.env` über `MOODLOFT_DAILY_LIMIT` und
`MOODLOFT_MIN_GAP_MINUTES`. Bereits gepinnte oder vorgemerkte Bilder werden nicht doppelt
aufgenommen.

### Kommandozeile

```
python -m moodloft boards                  # eigene Boards mit ID anzeigen
python -m moodloft pin <URL>               # einen Pin sofort erstellen
python -m moodloft add <URL> [<URL> ...]   # Hauptbild(er) in die Warteschlange legen
python -m moodloft from-file urls.txt      # dito, eine URL pro Zeile (# = Kommentar)
python -m moodloft queue                   # Warteschlange + Tageslimit anzeigen
python -m moodloft run --watch             # Warteschlange abarbeiten, bis sie leer ist
```

- `--board BOARD_ID` wählt das Board; alternativ `PINTEREST_BOARD_ID` in der `.env`.
- URLs können **Webseiten** (Hauptbild wird genommen, Seite als Quelle verlinkt) oder
  **direkte Bild-Links** sein. Optional: `--title`, `--description`.

## Fehler

| Meldung | Bedeutung |
|---|---|
| `HTTP 401` | Token abgelaufen → `python -m moodloft login` erneut ausführen |
| `HTTP 403` | App darf das (noch) nicht – z. B. nur Trial Access, Scope fehlt oder fremdes Board |
| `HTTP 429` | Zu viele Anfragen → kurz warten |
| `Kein Bild gefunden` | Seite hat kein erkennbares Hauptbild → direkten Bild-Link verwenden |
| `Tageslimit erreicht` | Kein Fehler – die Warteschlange macht morgen weiter |
