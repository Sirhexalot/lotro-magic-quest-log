# Magic Quest Log 0.5.1 – Importfehler und Prüfung

## Stand

7. November 2026: Website-Fix live, Version 0.5.1 lokal installiert, neuer Website-Export im Spielordner. **Der erste Spieltest deckte einen weiteren Fehler auf: Ein erneuter Leseaufruf verlor den Import und die Charakterliste.** Der eigentliche Laufzeit-Ladefehler ist inzwischen korrigiert und durch einen automatischen Rückfalltest abgesichert; die überarbeitete Fassung liegt im Spielordner. Sie braucht noch einen vollständigen Client-Neustart und die erneute Sichtprüfung. Keine Veröffentlichung, keine öffentlichen Antworten versendet.

## Meldung

peskycritter auf [LOTROInterface](https://www.lotrointerface.com/downloads/info1346-MagicQuestLog.html), derselbe Bericht von LabNo8051 auf Reddit: kein importierter Fortschritt; der Character-Knopf verschwindet nach dem Anklicken. Laut Ergänzung blieb der Fortschritt auch nach dem Entpacken der ZIP unsichtbar.

## Belegte Fehler und offene Ursache

1. **Laufzeit-Laden:** `Turbine.PluginData.Load` liefert beim Plugin-Start einen direkten Rückgabewert. Während der Sitzung liefert es zunächst `nil` und reicht die Tabelle über den dritten Parameter, einen Callback, nach. Der bisherige Lader verwendete keinen Callback. Dadurch verschwanden beim Wiederöffnen der Import und beim Charakterwechsel die eingelesenen Namen. Jetzt bleibt der letzte bekannte Stand während des laufenden Lesevorgangs erhalten; der Callback übernimmt die neu gelesenen Daten. Ein noch laufender Lesevorgang wird nicht als fehlende Datei gemeldet. Unveränderte Ergebnisse lösen keinen unnötigen Neuaufbau aus. Auch das Charakterverzeichnis wird beim periodischen Auffrischen erneut gelesen.
2. Die Website ließ beim Plugin-Export nur `A–Z` und `a–z` im Charakternamen zu. Namen wie Éowyn oder Frödo verschwanden ohne Hinweis aus der ZIP und ihrem Charakterverzeichnis.
3. Das Plugin prüfte mit Lua 5.1 `%a`. Unter dem getesteten Zeichensatz lehnte es dieselben Namen ab, auch wenn die Importdatei vorhanden war.
4. Der Character-Knopf wurde bei höchstens einem erkannten Namen ausgeblendet. Jetzt bleibt er sichtbar und ist ohne Wechselmöglichkeit deaktiviert. Das verhindert das irritierende Verschwinden, ersetzt aber keine fehlenden Importdateien.
5. Ein fehlender Import blieb bisher ohne Erklärung. Jetzt nennt das Fenster den fehlenden Import; der Chat zeigt einmal pro Charakter und Sitzung den erwarteten Dateipfad.

Den Laufzeitfehler haben wir mit Feldobar im echten Spiel reproduziert: zunächst Companion-Import und 480 erledigte Taten, nach Schließen und `/mql` dann fälschlich „kein Companion-Import“. Die Datei auf der Platte blieb bytegleich. Die sichtbaren Häkchen blieben wegen der privaten alten `Progress.lua` zunächst erhalten und hätten den Fehler sonst verdeckt. [Die abweichende API-Semantik ist auch auf LOTROInterface beschrieben](https://lotrointerface.com/forums/showpost.php?p=9221&postcount=2).

Der neue asynchrone Rückfalltest scheitert gegen die erste 0.5.1-Fassung mit „pending refresh must keep progress“ und besteht gegen den korrigierten Lader. Die Namensfehler wurden ebenfalls mit zunächst fehlschlagenden Tests reproduziert. **Nicht belegt ist, dass der meldende Nutzer einen Namen mit Akzent hat; seine Rückprüfung bleibt erforderlich.** Bei fortbestehendem Fehler Dateipfad, Server und Import prüfen; keine privaten Kontonamen oder vollständigen ZIPs öffentlich anfordern.

## Veröffentlichung der Website

Nur `companion.js` und die zugehörige Cache-Version in `spielstand.html` geändert. Die übrige Live-Website blieb unberührt.

- `https://llb.sirhexalot.de/companion.js`: SHA-256 `93f3c98399d07fcdae759c140f82f08156539e948b80dea01315a9391c8e105f`.
- Importseite lädt `companion.js?v=93f3c98399`.
- Beide Dateien nach dem Upload erneut per HTTPS geladen und bytegleich geprüft.
- Live-Seite im Browser geöffnet; echte Companion-Dateien über den Ordnerdialog geladen und ZIP über die sichtbare Schaltfläche heruntergeladen.
- Vier Testnamen mit Akzenten direkt mit dem geladenen Live-Konverter geprüft. Jeweils Importdatei und Charakterverzeichnis vorhanden. Keine Testcharaktere in Adrians Spieldaten geschrieben.

## Plugin-Version und Umfang

0.5.1 basiert auf dem veröffentlichten Archiv **0.5.0**, nicht auf dem inzwischen erweiterten Entwicklungsstand. Genau sechs Archivdateien unterscheiden sich:

- `Characters.lua`: Namen und Importprüfung.
- `Main.lua`: Rückmeldung bei fehlendem Import.
- `Strings.lua`: neue Hinweise DE/EN/FR.
- `Window.lua`: Schalterzustand und Hinweis.
- `MagicQuestLog.plugin`: Version 0.5.1.
- `README.md`: Hinweise zur Fehlerkorrektur.

Katalog, Karten, Jagdort-Ausbau und Belohnungen unverändert gegenüber 0.5.0. Keine private `Data/Progress.lua` im Archiv.

Archiv: `MagicQuestLog/dist/MagicQuestLog-0.5.1.zip`, 16.003.214 Bytes. Noch nicht veröffentlicht; erste Prüfversion durch korrigierten Kandidaten ersetzt.

SHA-256: `aa3575101eef2c9f186806adf29dfe0a0aec1f6eb7c3375aa834c0d74d2f09be`.

Installiert unter `~/Documents/The Lord of the Rings Online/Plugins/MagicQuestLog`. Sicherung der ersetzten Dateien: `~/.cache/mql-before-0.5.1-20261107/`. Alle drei geprüften privaten Fortschrittsdateien blieben bei der Plugin-Installation unverändert. Anschließend wurden ausschließlich die beiden Dateien des beauftragten Website-Exports erneuert; vorherige Fassungen sind ebenfalls dort unter `PluginData` gesichert. Keine Live-Abschlussdatei geändert.

## Prüfungen

- `tools/test_character_import.py`: Website-Schreiber → Lua-5.1-Loader, vier Namen mit Akzenten, unsichere Namen, fremde Charaktere, fehlende und leere Imports.
- `tools/test_plugin.py`: kompletter bestehender Testlauf auch gegen die separat bereitgestellte 0.5.1 auf Basis des Originalarchivs; bestanden. Private Testdatei danach wieder aus der Bereitstellung entfernt.
- Ergänzter Laufzeittest: Rückgabe `nil`, späterer Callback; unveränderte und neue Imports, Namensliste, Charakterwechsel, erstmaliger Import eines weiteren Charakters. Kein falscher Fehlhinweis während des Ladens und keine rekursive Ladeschleife. Gegen den ersten Kandidaten rot, gegen den korrigierten Kandidaten grün.
- Website `tests/test_companion.js`: bestanden, einschließlich Namen mit Akzenten und ZIP.
- Website `tests/test_companion_real.py`: bestanden. Der Test lädt jetzt die seit 0.5.0 getrennten Questdetails, statt auf nicht mehr vorhandene Schritte im Kernkatalog zuzugreifen.
- ZIP-Integrität geprüft; Dateiliste mit 0.5.0 verglichen, nur die sechs genannten Dateien abweichend.
- Installierter Loader mit dem tatsächlich im Browser heruntergeladenen und ins Spiel übernommenen Export geprüft: **3.656 abgeschlossene Einträge = 3.176 Aufgaben + 480 Taten**, **580 laufende Einträge**, Stufe 123, Charakter Feldobar, Server Meriadoc. Namensliste enthält Feldobar.

Der neue Export verwendet den vorhandenen Companion-Schnappschuss vom **3. November**. Er ist kein neu aus dem laufenden Client eingelesener Journalstand. Ein Vergleich mit älteren Plugin-Zahlen muss diese unterschiedliche Datenquelle berücksichtigen.

## Noch vor der Veröffentlichung

- Client vollständig beenden, neu starten, mit Feldobar anmelden und `/mql` öffnen. Nur Fenster schließen oder Plugin entladen genügt nicht.
- Importdatum und sichtbare Zähler prüfen. Alte `Progress.lua` kann zusätzliche bekannte Abschlüsse beitragen; der Plugin-Gesamtzähler ist nicht zwingend gleich der reinen Importzahl.
- Character-Schalter sichtbar und bei genau einem bekannten Charakter deaktiviert; Fenster schließen und wieder öffnen, Fortschritt bleibt erhalten.
- Stichprobe: erledigte Aufgabe, laufende Tat mit Zähler, Suche, Details; keine Fehlermeldung.
- Danach 0.5.1 auf LOTROInterface hochladen und Freigabestatus nennen, nicht vorzeitig einen freigegebenen Download behaupten.
- Beschreibung aus `packaging/lotrointerface-0.5.1.bbcode` ersetzen und im echten Browser kontrollieren. Der Text ist bewusst ASCII-only, um die bisherige UTF-8/Windows-1252-Verwechslung auf der alten Seite zu vermeiden.
- Antworten aus `packaging/antworten-0.5.1-2026-11-07.md` an den tatsächlichen Veröffentlichungsstand anpassen und versenden.
