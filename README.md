# Magic Quest Log

Eigenständiges LOTRO-Plugin für Aufgaben und Taten. Der Katalog ist deutsch,
englisch und französisch vorhanden; die Anzeige folgt der Spielsprache, mit
englischem Rückfall.

Enthalten sind Plugin, Werkzeuge und Symbole. **Nicht** im Repository liegt der
erzeugte Katalog (rund 102 MB) – er kommt als Release-Archiv. Deine eigene
Fortschrittsdatei bleibt ebenfalls lokal.

## Was das Plugin kann

- Baum links: **Epische Geschichte** nach Band/Buch, sonst **Obergebiet → Gebiet
  → Untergebiet → Gruppe**, und eigene Zweige für Missionen, Instanzen, Handwerk,
  Feste sowie nicht geografisch zugeordnete Einträge. Alle Knoten starten zugeklappt.
- **Suche** nach Name oder Namensteil, Groß-/Kleinschreibung und Akzente egal.
- Rechts **Beschreibung** und in Schritte gegliederte Ziele. Belegte Zielanzahlen
  stehen als „benötigt: 10“; aktuelle Zähler werden nicht erfunden.
- **Fortschritt** aus einer eigenen Statusdatei (`Data/Progress.lua`): Baum und
  Kopfzeile zeigen dann „erledigt/gesamt“ (z. B. `(163/276)`), Details einen
  grünen Haken. Fehlt die Datei oder gehört sie einem anderen Charakter, bleibt
  es bei der reinen Gesamtzahl – nie bei einer erfundenen Null.
- **In MoorMap zeigen** über einen Quickslot mit Alias-Shortcut, sofern eine
  Position geprüft ist.
- Fenster im Stil der Spieloberfläche: Titelleiste, Schließen-Kreuz, verschiebbar.
- **Start-Icon** rechts am Bildschirmrand: Klick öffnet oder verbirgt das Fenster,
  Ziehen verschiebt es. Fenster- und Icon-Position sowie Sichtbarkeit werden
  gespeichert.
- Test-/Entwicklerinhalte sind ausgeblendet; Tests schützen das.

Nicht enthalten: Gegenstände, Handwerk, Ausrüstung, eigene Karte und Charakterexport.

## Bedienung

- `/mql` öffnet oder verbirgt das Fenster; `/mql show` und `/mql hide` steuern es
  ausdrücklich.
- **MoorMap** öffnet sich über den kleinen Quickslot links neben „In MoorMap
  zeigen“ im Detailbereich. Ein Plugin kann keinen Slash-Befehl ausführen;
  MoorMap lässt sich nur über einen Quickslot-Shortcut steuern. Das ist der
  dokumentierte Weg (wie bei Compendium), deshalb ist es ein Quickslot und kein
  normaler Knopf.
- Neuen Katalog nach einem Spielupdate einlesen: Plugin neu laden
  (`/plugins unload MagicQuestLog`, `/plugins load MagicQuestLog`) oder Spiel neu starten.

## Symbole

Alle Symbole kommen von [Lucide](https://lucide.dev) (ISC-Lizenz, siehe
`icon-sources/NOTICE`). Der Client zeichnet kein SVG, deshalb liegen sie als
32-Bit-Targa-Texturen in `Resources/`. Die SVGs liegen unverändert in
`icon-sources/`; `tools/build_icons.py` färbt und skaliert sie nur.

| Symbol | Verwendung |
|---|---|
| `start.tga` (`mop-sparkles`) | Start-Icon am Bildschirmrand |
| `quests.tga` (`scroll-text`), `deeds.tga` (`trophy`) | Reiter Aufgaben / Taten |
| `search.tga`, `clear.tga` (`x`) | Suche und Leeren |
| `closed.tga`, `open.tga` (`chevron-*`) | zugeklappte / offene Knoten |
| `todo.tga` (`circle`), `done.tga` (`circle-check`) | offen / erledigt in der Liste |
| `todobig.tga`, `donebig.tga` | dieselben Marken in der Detailansicht |
| `mappin.tga` (`map-pin`) | Hinweis neben dem MoorMap-Quickslot |

**Jedes Symbol wird in genau der Pixelgröße gerendert, in der es erscheint.** Der
Client tastet Plugin-Texturen schlecht ab; ein herunterskaliertes 32-px-Symbol
sieht kantig aus. Die Größe steht deshalb doppelt: in `build_icons.py` und in
`ICON_SIZE` in `Window.lua`. Wer eine Größe ändert, ändert beide.

## Installieren

Den Katalog gibt es als Release-Archiv, weil er rund 102 MB groß ist und deshalb
nicht im Repository liegt. Das Archiv ist installationsfertig:

```sh
# Archiv in den Plugins-Ordner entpacken; danach im Spiel /mql
unzip MagicQuestLog-<version>.zip -d '<Plugins-Ordner>'
```

Im Spiel: `/plugins unload MagicQuestLog`, `/plugins load MagicQuestLog`, `/mql`.

## Bauen und Prüfen

Alle Beispiele gehen davon aus, dass `LORE_DIR` ein Verzeichnis mit den
extrahierten Spieldaten ist (`quests.xml`, `deeds.xml`, `geoAreas.xml`,
`labels/<sprache>/…`) und `PLUGIN_DIR` der `Plugins`-Ordner des Spiels.

```sh
# Katalog erzeugen, prüfen und installieren (nur lesend gegenüber den Spieldaten)
MagicQuestLog/tools/rebuild.command "<LORE_DIR>" "<PLUGIN_DIR>"

# Statusdatei aus einem Charakterexport erzeugen (nur lesend)
python3 MagicQuestLog/tools/build_progress.py <export.json>

# Symbole aus den Lucide-SVGs neu erzeugen (nur lesend)
python3 MagicQuestLog/tools/build_icons.py

# Release-Archiv mit Katalog bauen (schreibt nur nach dist/)
python3 MagicQuestLog/tools/make_release.py
```

Die beiden Prüfläufe brauchen eine Python-Umgebung mit `lupa` (Lua 5.1);
`rebuild.command` legt sie beim ersten Aufruf unter `.venv/` selbst an:

```sh
.venv/bin/python MagicQuestLog/tools/verify_catalog.py   # Daten: IDs, Struktur, Zähler
.venv/bin/python MagicQuestLog/tools/test_plugin.py      # Plugin-Logik mit echten Daten
```

`tools/overrides.json` enthält Handkorrekturen: `hidden_ids` und abweichende
Pfade. Sie werden beim Neuerzeugen angewandt und nicht überschrieben. Dateien mit
dem Generatorkopf `-- Generated by Magic Quest Log; do not edit.` werden ersetzt;
alles andere wird ausdrücklich verweigert.

Eine eigene Statusdatei gehört **nicht** ins Repository: `Data/Progress.lua` ist
in `.gitignore` eingetragen, `make_release.py` lässt sie aus dem Archiv weg und
`Data/Progress.example.lua` zeigt das Format mit Beispieldaten.

## Grenzen

- Der Katalog liest **extrahierte Spieldaten im XML-Format**, nicht die binären
  LOTRO-Archive. Die XML-Extraktion ist nicht Teil dieses Projekts; ohne sie lässt
  sich nach einem Spielupdate nichts erneuern.
- Der Katalog liegt weiterhin in **je einer großen Datei pro Sprache und Art**
  (rund 32 MB deutsch). Das kostet beim Laden Zeit. Aufteilen in kleinere Dateien
  ist der nächste Schritt.
- **MoorMap braucht einen Klick** auf den Quickslot. Innerhalb des Plugins lässt
  sich kein Slash-Befehl ausführen.
- **Fortschritt** zeigt nur, was die Statusdatei belegt. Sie stammt aus einem
  gelesenen Journalexport zu einem Zeitpunkt; sie wird nicht automatisch
  aktualisiert und ersetzt keinen neuen Export.
- **Gleiche Namen kommen mehrfach vor** – 381 von 15.117 Aufgaben liegen in
  derselben Gruppe doppelt (zum Beispiel „Das letzte Wort“ oder „Einleitung
  überspringen“). Das sind keine Dubletten unseres Baus: geprüft wurden 15.117
  Einträge mit 15.117 verschiedenen IDs. Es sind eigenständige Aufgaben desselben
  Namens, etwa mit unterschiedlichem Auftraggeber (`7003783D` → Arcil,
  `7003A67E` → Éothain) oder als Fassung für verschiedene Völker und Klassen. Das
  Spiel zeigt nur die zutreffende; der Katalog kann das ohne
  Voraussetzungsdaten nicht unterscheiden und lässt deshalb beide sichtbar.
  Ein Auftraggeber-Feld im Katalog wäre die saubere Unterscheidung und ist noch
  nicht eingebaut.
- **Texte und Gruppennamen sind aufgelöst.** Platzhalter wie `${PLAYER}`,
  `${CLASS}` oder `${PLAYERNAME:A[m]|B[f]}` werden ersetzt; erstere mit dem
  Charakter, die Form „A / B“ als beide Möglichkeiten. Zähler (`${CURRENT}`)
  bleiben als „Zähler im Spiel“ stehen, weil das Plugin sie nicht kennt. 16
  Gruppennamen im deutschen Katalog enthalten solche Platzhalter und wären sonst
  roh sichtbar.
- **Gebietsnamen sind übersetzt**, solange die Sprachdateien sie enthalten
  („Bree-land“ → „Breeland“, „The Shire“ → „Das Auenland“). Die Schlüssel
  (`zone:Bree-land`) bleiben absichtlich englisch, weil die Baumstruktur in allen
  Sprachen identisch sein muss. Fehlt eine Übersetzung, steht der englische Name –
  nicht geraten.
- **Gespeicherte Fensterpositionen sind Text**, nicht Zahlen. Der Client schreibt
  Zahlen mit dem Dezimalkomma der Spielsprache (`239,000000`), und das ist kein
  gültiges Lua: die ganze Einstellungsdatei wurde dadurch unlesbar.
- Weltgebiete folgen einem ausdrücklichen Abgleich mit den Originalkarten.
  `geoAreas.parentId` ist dafür unbrauchbar: es hängt Gondor und Mordor an Rhovanion.
- Kartenpositionen werden nur angeboten, wenn sie über die **exakte Textur-ID**
  der Karte und die MoorMap-Grenzen geprüft sind und der Regionencode passt.
  Mehrdeutige oder fehlende Positionen zeigen keine Schaltfläche: 10.051 von
  15.117 Aufgaben haben eine geprüfte Position.
- Positionen stammen aus Originalkoordinaten von Zielen und Auftraggebern.
  Sie sind nicht immer der Aufgabenbeginn.
- Die Katalognenner sind Einträge, nicht „erreichbare“ Aufgaben. Klasse, Volk,
  Alternativen und Wiederholbarkeit sind darin enthalten.
- Geschlechtsabhängige Formulierungen werden als „mein Freund / meine Freundin“
  gezeigt; die öffentliche Player-Schnittstelle liefert kein Geschlecht.

## Stand und Prüfung

Erzeugt: 15.117 Aufgaben (372 Testeinträge ausgeblendet) und 5.534 Taten je
Sprache, 71.189 geprüfte Aufgabenpositionen. Statusdatei für **Feldobar**:
3.657 erledigt (3.177 Aufgaben + 480 Taten), 579 laufend, 3 doppelt geführt
(wiederholbar), 3 unbekannte IDs. Datenprüfung: identische ID-Mengen
und identische Baumstruktur in allen drei Sprachen, Kindersummen stimmig.
Plugin-Test: 15 Prüfungen grün, darunter Start zugeklappt, Namenssuche inklusive
„ker izel“ → „Kêr Izel“, Details ohne Rohplatzhalter, ehrliche Anzeige ohne
Position, englischer Rückfall bei fehlendem Sprachkatalog, Kopfzeile unter der
Titelleiste, Suche mit Beschriftung, Zähler „n/gesamt“, Zwischenspeicher beim
Aufklappen, ignorierte Statusdatei eines fremden Charakters und die Prüfung,
dass jede im Lua genannte Icon-Textur wirklich vorhanden ist.

**Behoben nach der zweiten Spielprüfung** (noch nicht erneut im Spiel bestätigt):
kein Neuaufbau und Neusortieren des ganzen Katalogs beim Aufklappen (Baum wird
zwischengespeichert), nur noch eine Kontrolle je Zeile statt über 40 für das
Statussymbol, Kopfzeile unter der Titelleiste, Suchfeld mit der Beschriftung
„Suchen“, MoorMap über Quickslot-Alias statt wirkungslosem Ausgeben des Befehls,
Fortschrittszähler je Knoten.

**Nach der dritten Spielprüfung (02.11.) umgesetzt, im Spiel noch nicht
nachgeprüft:** Symbole von Lucide (Start-Icon `mop-sparkles`, Reiter,
Suchfeld, Leeren, Knotenpfeile, Status Kreise, Karten-Nadel), Beschreibung und
Schritttexte eine Schriftgröße größer (Verdana14 statt Verdana12, Titel
Verdana16), doppelt vorkommende Aufgabennamen als eigenständige Einträge
dokumentiert.

**Nach der vierten Spielprüfung (02.11.) umgesetzt, im Spiel noch nicht
nachgeprüft:** Baum- und Zeilenschrift eine Größe größer (Verdana14 wie der
Beschreibungstext, Zeilenhöhen 20 bzw. 18 px). Der MoorMap-Slot zeigt den Alias
nicht mehr an: das Karten-Symbol liegt als klickdurchlässige Abdeckung darüber
(`mapCover`/`mapIcon` mit `SetMouseVisible(false)`), damit der Klick weiterhin den
Quickslot darunter trifft.

**Vier Fehler aus dieser Prüfung behoben:**

1. **Platzhalter wurden nicht ersetzt, sondern zu „[Spielwert]“.** In `Resolve`
   wurde das Ergebnis von `gsub` verworfen, sodass am Ende der Notfall-Zweig
   jeden Platzhalter überschrieb. `${PLAYER}` heißt jetzt „Feldobar“, `${CLASS}`
   die Klasse, `${PLAYERNAME:A[m]|B[f]}` wird „A / B“. Ein Test prüft, dass der
   Charaktername im Text steht und die Ersatzmarke nirgends mehr auftaucht.
2. **Gruppennamen mit Platzhaltern blieben roh** (`${PLAYERNAME:…}` im Baum).
   Beschriftungen gehen jetzt durch dieselbe Auflösung wie Texte.
3. **Gebietsnamen blieben englisch.** Der Generator suchte einen Gebietsnamen in
   einer nach ID sortierten Tabelle und fand nie etwas. Jetzt „Breeland“,
   „Das Auenland“, „Pays de Bree“; die Schlüssel bleiben englisch, damit die
   Struktur in allen Sprachen gleich bleibt.
4. **Die Einstellungsdatei war unlesbar** (`'}' expected near ','`): der Client
   schreibt Zahlen mit Dezimalkomma. Positionen werden jetzt als Text gespeichert.
   Die beschädigte Datei wurde von Hand repariert.

**Symbole:** neu in exakter Anzeigegröße gerendert. Vorher lagen sie in 32 px vor
und wurden im Spiel auf 11–18 px verkleinert; der Client tastet Plugin-Texturen
schlecht ab, deshalb sahen sie kantig aus.

Zeilenklicks laufen über die Listenauswahl, denselben Weg, den der Client an
anderer Stelle nutzt; nach jeder Auswahl wird sie zurückgesetzt, damit dieselbe
Zeile erneut klickbar bleibt.

**Behoben nach der ersten Spielprüfung:** fehlender Fensterrahmen
(jetzt `Turbine.UI.Lotro.Window`), fehlendes Start-Icon (jetzt eigenes, aus Pixeln
gezeichnetes Icon) und nicht reagierende Zeilen (jetzt über die Listenauswahl).
Voraussetzung bleibt: Der Client muss den Plugin-Ordner kennen – Plugin neu laden
oder Spiel neu starten, dann `/mql`.
