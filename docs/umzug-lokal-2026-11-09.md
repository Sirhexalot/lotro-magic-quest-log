# Lokaler Projektumzug – 9. November 2026

- Quelle bleibt unverändert: `/Users/adrian/Documents/07_Hobbys/Lotro/MagicQuestLog`.
- Aktiver Projektordner: `/Users/adrian/Developer/MagicQuestLog`.
- OpenChamber-Projekt `MagicQuestLog` wurde mit diesem lokalen Pfad registriert. Der bisherige übergeordnete Projekteindruck `as-lotro` bleibt für Spielunterlagen erhalten; alle anderen Projekteinstellungen wurden unverändert übernommen.
- Diese Session `ses_e44def771ffexZmNU5Lrlnh5lL` wurde ausdrücklich mit `session_move` auf den lokalen Ordner umgestellt. Andere Sessions wurden nicht verschoben.

## Vollständigkeit und Grenzen

Der abschließende Vergleich erfasste 802 Quelldateien anhand relativer Pfade und Dateigrößen. Vor den unten dokumentierten lokalen Anpassungen gab es keine fehlenden Dateien und keine Größenabweichungen. Zusätzlich lag lokal die neue `AGENTS.md`, die wesentliche bisher geerbte Plugin-Anweisungen erhält.

Dies ist **kein vollständiger Inhalts- oder Prüfsummenvergleich**. Es wurden nicht erneut sämtliche Originaldateien inhaltlich gelesen.

Bewusst nicht vollständig übernommen beziehungsweise nicht in die Vollständigkeitsprüfung einbezogen:

- `.venv/`: kopierte Teilbestände sind nicht als funktionsfähige Umgebung bestätigt; lokal neu erstellen, bevor darauf vertraut wird.
- `tools/__pycache__/`: wiederherstellbarer Python-Cache.
- `plugin/MagicQuestLog/.mql-build-tbii6t94/`: alter generierter Build-Zwischenstand.
- `Sicherungen/`: ältere Sicherungen; vollständiger Bestand bleibt im iCloud-Original, lokale Teilbestände wurden nicht geprüft.

Reguläre generierte Kataloge unter `plugin/MagicQuestLog/Data/` und vorhandene Release-Dateien unter `dist/` sind **nicht ausgeschlossen**. Persönliche Fortschrittsdateien wurden nicht geändert oder veröffentlicht.

## Git-Prüfung ausschließlich lokal

`git fsck --full` fand zunächst vier ungültige, mitkopierte iCloud-Konfliktdateien:

- `.git/refs/heads/main 2`
- `.git/refs/heads/main 3`
- `.git/refs/remotes/origin/main 2`
- `.git/refs/remotes/origin/main 3`

Diese wurden nur in der lokalen Kopie unter `.git/icloud-conflict-backup/refs/…` gesichert, nicht gelöscht. Die regulären Referenzen `main` und `origin/main` bleiben unverändert auf `72041036bd1ef1b29b500358495adeb7dc933c83`.

Danach lief `git fsck --full` ohne Fehler. `git --no-optional-locks status --short --branch` funktioniert, zeigt `main...origin/main` und die erhaltenen lokalen Änderungen und unversionierten Dateien. Es wurde kein Commit, Reset oder Checkout ausgeführt.

## Noch zu beachten

- Andere bestehende Plugin-Sessions bei Bedarf einzeln auf den neuen Pfad umstellen; ein neuer Projekteindruck migriert sie nicht automatisch.
- Build-Werkzeuge mit Annahmen über `../Companion-Test` benötigen explizite Pfade zu den weiterhin am alten Ort liegenden Quellexporten. Der Datenexport und andere Projekte wurden nicht umgezogen.
- Python-Umgebung lokal neu erstellen; kein vollständiger Build- oder Spieltest war Teil der Umzugsprüfung.
