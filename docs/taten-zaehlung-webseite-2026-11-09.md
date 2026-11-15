# Taten richtig zählen: Monsterplay aus den Zählern nehmen

Stand 9. November 2026. Übergabe vom Plugin **Magic Quest Log** an das Website-Projekt **LOTRO Log Book**. Ziel: derselbe Zählfehler, der im Plugin behoben wurde, verschwindet auch aus der Website.

## Kurzfassung

In drei Gebieten waren die Taten-Zähler um je 100 zu hoch: **Angmar 175 statt 75**, **Eregion 128 statt 28**, **Forochel 130 statt 30**. Ursache sind Monsterplay-Taten (PvMP), die im Katalog wie normale Taten behandelt und mitgezählt wurden. Sie bleiben sichtbar, dürfen aber nicht als erreichbar zählen.

Die Website liest den Plugin-Katalog (`Deeds_*.lua`). Seit Plugin **0.5.2** trägt jeder solche Eintrag das Feld `mp = 1`. Die Website muss dieses Feld nur noch durchreichen und in ihrer Zählregel berücksichtigen.

## Der Fehler im Detail

- Pro Gebiet liegen **100** gestaffelte Slayer-Taten in Angmar, Eregion und Forochel, zum Beispiel:
  - `7001A0AE` – „Angmar Warden-slayer -- Tier 2“
  - `7001A0B3` – „Angmar Hunter-slayer -- Tier 1“
  - `7001A2B1` – „Eregion Defiler-slayer -- Tier 3“
- **70** davon tragen im Export ausdrücklich `Quest_IsMonsterPlayQuest = 1`.
- **30** tragen keine Markierung. Sie sind nur über Gebiet + Titel erkennbar: Titel enthält „slayer“ und endet auf `-- Tier 1` bis `-- Tier 5`.
- Diese Taten werden als Monster im PvMP gespielt und erscheinen nie im Journal eines normalen Charakters. Ein mitgeführter Fortschritt kann sie also höchstens aus alten Daten enthalten.

## Warum kein Namensfilter

Ein Filter auf „slayer -- Tier“ wäre falsch:

- Weitere **110** gleich benannte Einträge liegen unter `Common` (UITab 49). Sie sind nicht alle Monsterplay.
- Im gesamten Export gibt es **410** solcher gestaffelten Slayer-Namen, davon **280** mit Monsterplay-Markierung und **130** ohne. Fehlende Markierung allein ist kein Ausschlusskriterium.
- Gültige PvMP-Inhalte außerhalb der drei Altgebiete dürfen nicht verschwinden.

Deshalb gilt die Regel **nur** für Taten in Angmar, Eregion und Forochel, deren englischer Titel „slayer“ enthält und auf `-- Tier 1` … `-- Tier 5` endet – zusätzlich zu allen Einträgen mit `mp`-Markierung.

## Was im Katalog steht (Plugin 0.5.2)

- Neues Feld `mp = 1` an Taten und Aufgaben. Insgesamt markiert: **481 Taten**, **241 Aufgaben**.
- Die Einträge bleiben vollständig im Katalog und im Baum sichtbar. Sie werden nur nicht gezählt.
- Bereits erledigte Einträge zählen weiter (Vorrang vor jeder Ausschlussregel). So geht kein Fortschritt verloren.
- Die Detailansicht nennt den Grund (`monsternote`), die Zeile ist gedimmt und trägt den kurzen Vermerk `monsterplay`.
- Referenz im Plugin:
  - Erzeugung: `tools/build_catalog_from_export.py`, Abschnitt „Monster play“ (rund um Zeile 694).
  - Zählregel: `plugin/MagicQuestLog/Model.lua`, `attainable()` (rund um Zeile 231).
  - Anzeige: `plugin/MagicQuestLog/Window.lua`, Zeilenvermerk und Statusmarke (rund um Zeile 760).
  - Texte: `plugin/MagicQuestLog/Strings.lua`, `monsternote` und `monsterplay` in DE/EN/FR.

## Änderungen im Website-Projekt

Die Website baut ihre Taten-Daten aus dem Plugin-Katalog:

```
python build_daten.py --art taten --katalog <Pfad>/Deeds_<sprache>.lua ...
```

Wichtig: Nach dem Plugin-Update **neu bauen**, sonst fehlt das Feld `mp`. Die alten `daten-taten-*.js` kennen es nicht.

### 1. `build_daten.py`: `mp` durchreichen

Bei den Feldern neben `x` und `e` (rund um Zeile 592):

```python
# mp: monster play. The creep side fights these; a normal character's journal
# never contains one, so they stay visible but are not counted.
**({'mp': 1} if field(record, 'mp', 0) == 1 else {}),
```

Das gilt für Aufgaben und Taten (derselbe Codepfad).

### 2. `web/app.js`: Zählregel erweitern

`zustandVon()` (Zeile 70) bekommt einen weiteren Zustand:

```js
function zustandVon(quest) {
	if (fertig[quest.i] === true) { return 'fertig'; }
	if (quest.x === 1) { return 'sitzung'; }
	if (quest.mp === 1) { return 'monster'; }
	if (hatFortschritt && quest.e) { /* unverändert */ }
	...
}
```

`gezaehlt()` (Zeile 120) nimmt den neuen Zustand aus:

```js
return zustand !== 'sitzung' && zustand !== 'ausgeschlossen' && zustand !== 'monster';
```

Alle Stellen, die bisher `'sitzung'`/`'ausgeschlossen'` behandeln, müssen `'monster'` mitführen:

- Kartenbeschriftung (Zeilen 712–713)
- Listenzeilen (Zeilen 1590–1613): dimmen und Vermerk anzeigen
- Verfügbarkeitsfilter (Zeilen 1662, 1721–1722): Monsterplay ist nie „offen“
- Detailansicht (Zeilen 1886–1890 und 2095–2106): Hinweistext statt „offen“
- Jede weitere Stelle mit `!== 'sitzung' && !== 'ausgeschlossen'`

Muster für die Zeile (analog zur Sitzung):

```js
if (lage === 'monster') {
	vermerk.textContent = t('monsterspiel');
	zeile.classList.add('gedimmt');
}
```

### 3. `web/texte.js`: Texte in DE/EN/FR

Je Sprachblock neben `sitzung_hinweis` ergänzen:

```js
// Deutsch
monsterspiel: 'Monsterplay',
monster_hinweis: 'Monsterplay: Diese Tat wird als Monster gespielt und erscheint nie im Journal eines normalen Charakters. Deshalb zählt sie nicht mit.',

// English
monsterspiel: 'monster play',
monster_hinweis: 'Monster play: this deed is fought as a monster and never appears in a normal character\'s journal, so it is not counted.',

// Français
monsterspiel: 'jeu de monstre',
monster_hinweis: 'Jeu de monstre : cette prouesse se joue du côté des monstres et n\'apparaît jamais dans le journal d\'un personnage normal. Elle n\'est donc pas comptée.',
```

## Erwartetes Ergebnis

Nach dem Neubau der Taten-Daten und der Anpassung der Zählregel:

| Gebiet | sichtbar | davon Monsterplay | gezählt |
|---|---|---|---|
| Angmar | 175 | 100 | **75** |
| Eregion | 128 | 100 | **28** |
| Forochel | 130 | 100 | **30** |

Die sichtbaren Summen bleiben 175/128/130. Nur die Zähler sinken. Dieselben Zahlen zeigt das Plugin.

## Prüfschritte

1. Taten-Daten gegen den 0.5.2-Katalog neu bauen (`build_daten.py --art taten`).
2. In den drei Gebieten die Kopfzahlen prüfen: 75 / 28 / 30 gezählt.
3. Eine Monsterplay-Tat öffnen: sichtbar, gedimmt, mit Vermerk, ohne „offen“-Markierung.
4. Fortschritt laden und prüfen, dass eine **erledigte** Monsterplay-Tat weiter als erledigt zählt und nicht aus der Liste fällt.
5. Stichprobe `Common`: Die 110 gleich benannten Einträge dürfen nicht pauschal verschwinden.
6. Deutsch, Englisch und Französisch müssen dieselben Zahlen und Vermerke zeigen.

## Was nicht zu tun ist

- Keine Taten aus dem Katalog löschen. Nur die Zählung ändert sich.
- Keinen Namensfilter „slayer -- Tier“ über alle Gebiete legen (siehe oben).
- Keinen Fortschritt verwerfen: erledigt schlägt jede Ausschlussregel.
- Die Plugin-Seite nicht nachziehen: Sie ist mit 0.5.2 bereits korrekt.

## Hinweis zur PHP-Umstellung

Die Zeilenangaben beziehen sich auf die aktuelle JavaScript-Fassung (`build_daten.py`, `web/app.js`, `web/texte.js`). Wird die Seite auf PHP umgestellt, gilt dieselbe Regel: `mp` aus dem Katalog übernehmen, Monsterplay sichtbar lassen, aus den Zählern nehmen, erledigt vor Ausschluss, Texte in allen drei Sprachen.
