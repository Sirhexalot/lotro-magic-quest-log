# Magic Quest Log

Aktiver lokaler Projektordner: `/Users/adrian/Developer/MagicQuestLog`.
Der bisherige Ordner unter `/Users/adrian/Documents/07_Hobbys/Lotro/MagicQuestLog` bleibt vorerst als Sicherung bestehen und wird nicht parallel weiterbearbeitet.

## Umfang und Schutz persönlicher Daten

- Plugin ausschließlich für Aufgaben und Taten. Keine eigenständigen Gegenstands-, Titel-, Tugend- oder Rezeptbereiche ergänzen.
- Website `lotro-log-book` und andere Projekte sind getrennt und bei Plugin-Arbeiten nicht zu verändern.
- Vorhandene lokale Änderungen bewahren. Persönliche Fortschrittsdaten, insbesondere `Data/Progress.lua` und PluginData, weder überschreiben noch veröffentlichen.
- Ausgeschlossene Katalogeinträge nicht mit verlorenem Charakterfortschritt verwechseln. Bereits erledigte Einträge haben bei der Zählbarkeit Vorrang.

## Client-Verhalten

`Turbine.PluginData.Load(scope, key, callback)` liefert Daten nur beim Plugin-Start direkt. Zur Laufzeit kommt zunächst `nil`, danach der Callback. Alten Zustand behalten, bis der Callback neue Daten liefert. `nil` nicht als fehlende Datei behandeln. Regression: `tools/test_plugin.py`; Bericht: `docs/import-fix-0.5.1-2026-11-07.md`.

- Deutscher Client: `/zusatzmodule` statt `/plugins`.
- Verlässliche Prüfung aktualisierter Plugin-Dateien erfordert einen Client-Neustart; Entladen und Neuladen in derselben Sitzung ist nicht verlässlich.
- Bei Fernsteuerung des Spiels nur Einfügen (`paste`), niemals `type` verwenden.
- Kopierte Python-Umgebungen können absolute alte Pfade enthalten. Vor Nutzung prüfen, nötigenfalls lokal neu erstellen.

## Quellen und Bau

README und `packaging/publish-notes.md` vor Build oder Veröffentlichung lesen. Externe Exportdaten und Companion-Lore liegen weiterhin außerhalb dieses Repositories; relative Pfade zum früheren Elternordner müssen beim Bauen explizit ersetzt werden. Ein Spieltest darf nicht aus einem Stub-Test abgeleitet werden.
