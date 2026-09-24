# Projekt: Pinterest Automatisierung

> Eigenständiges Projekt – hat nichts mit Cartono zu tun.

## ⚠️ Sicherheit (Repo ist ÖFFENTLICH)
- Niemals App Secret, Access Token oder Refresh Token committen.
- Zugangsdaten ausschließlich aus Umgebungsvariablen lesen:
  `PINTEREST_APP_ID`, `PINTEREST_APP_SECRET`, `PINTEREST_REFRESH_TOKEN`
  (lokal optional über eine `.env`-Datei, die per `.gitignore` ausgeschlossen ist).
- Vor jedem Commit prüfen, dass keine Tokens/Secrets im Diff stehen.

## ⚠️ GitHub-Pages-Dateien nicht umbenennen/verschieben
`website.html` und `datenschutz.html` sind im Pinterest-Developer-Formular hinterlegt.
Dateinamen und Pfade müssen gleich bleiben. Inhaltliche Änderungen nur nach Rücksprache mit
dem Nutzer (im Sept. 2026 mit Freigabe überarbeitet: App-Name, Verantwortlicher, Kontakt,
vollständige DSGVO-Datenschutzerklärung).

## Ziel
Automatisiertes Erstellen von Pins über die offizielle Pinterest API v5 (kein Browser-Scraping,
kein Connector) – Bilder von Webseiten sollen automatisiert als eigene Pins auf ein eigenes
Board hochgeladen werden.

## Account
- Pinterest: privates/persönliches Konto (kein Business-Konto nötig – "Pinner accounts" können
  laut Pinterest-Doku ebenfalls Pins erstellen, Boards anlegen, Pins speichern)
- Neue Gmail-Adresse extra für dieses Projekt angelegt

## Developer-App
- App-Name: **Pinautomatisierung**
- Themen: Design, Interior, Möbel, Fashion
- Logo: `logo.svg` (Quelle) + `logo.png` (512×512, App-Icon) – Moodboard mit Sessel, Kleid, Lampe, Tasche
- Verantwortlicher / Kontakt (öffentlich auf den Pages): Max Locker, pintillmio@gmx.de
- Registriert auf developers.pinterest.com
- App-Zweck: "Automatisiertes Speichern von Design-Recherche-Bildern auf eigene Boards für
  persönliche Nutzung"
- Benötigte Scopes: `pins:write`, `pins:read`, `boards:read`
- Bei "Liest Daten von Pins und/oder Pinnwänden" wurde "Ja, meine" gewählt – Zugriff nur auf
  eigene Pins/Boards

## Website & Datenschutzerklärung (für Pinterest-Formular)
Gehostet via GitHub Pages, Repo: octablecash/Pinterest-App
- Website: https://octablecash.github.io/Pinterest-App/website.html
- Datenschutz: https://octablecash.github.io/Pinterest-App/datenschutz.html

## Status
- Erster Antrag: **Trial Access verweigert** (wahrscheinlich wegen Platzhalter-Website und
  unvollständiger Datenschutzerklärung). Seiten überarbeitet → Antrag neu stellen.
- Ohne Trial Access gibt es keinerlei API-Zugriff (auch kein OAuth-Test).
- App ID / App Secret liegen dem Nutzer vor – nur als Umgebungsvariablen, nie im Repo

## Nächste Schritte
1. OAuth 2.0 Flow (Authorization Code Grant); Redirect URI wie im Pinterest-Formular eingetragen
   (z. B. `http://localhost:8080/callback`) – der erste Login muss lokal beim Nutzer laufen
2. Access Token + Refresh Token sicher lokal speichern (`.env`, nicht committen)
3. Skript zum Erstellen eines Pins: Board-ID abfragen (`GET /v5/boards`), Pin erstellen
   (`POST /v5/pins`) mit Bild-URL + Board-ID + Beschreibung
4. Input: Liste von Webseiten-URLs, aus denen die Bild-URL extrahiert und als neuer Pin
   hochgeladen wird
5. Fehlerbehandlung für Trial-Access-Limitierung (403 bei `/v5/pins`, falls Standard Access noch
   nicht freigegeben)

## Hinweise
- Die Cloud-Umgebung braucht Netzwerkzugriff auf `api.pinterest.com`; Code soll auch lokal beim
  Nutzer lauffähig sein.
- Kommunikation mit dem Nutzer auf Deutsch.
