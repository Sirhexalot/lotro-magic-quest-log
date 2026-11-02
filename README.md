# Magic Quest Log

A standalone LOTRO plugin for quests and deeds. The catalog covers German,
English and French; the plugin follows the client language and falls back to
English.

The repository contains the plugin, the tools and the icons. The generated
catalog (~102 MB) is **not** in the repository — it ships as a release archive.
A character's own progress file also stays local.

## What the plugin does

- Tree on the left: **Epic story** by volume/book, everything else as
  **region → zone → area → group**, plus separate branches for missions,
  instances, crafting, festivals and entries without a geographic assignment.
  Every node starts collapsed. Long names wrap and the row grows with them
  instead of running into the row below.
- **Search** by name or part of a name, ignoring case and accents.
- On the right, the **description** and the objectives split into steps. Known
  objective counts read "required: 10"; live counters are never invented.
- The counters show what a character can still do, not what merely exists: a
  **session play** is never written to the journal, and of two quests that rule
  each other out only one can be taken. Both are marked in the tree ("session
  play", "not possible") and stay out of the numbers. The details say why.
- **Progress** from two sources: an optional status file (`Data/Progress.lua`)
  for everything done before, and the quest chat channel for what you finish
  while playing. The tree and the headline then show "finished / total" (e.g.
  `(163/276)`) and the details a green check. With no file at all the totals are
  labelled as partial ("finished (known)"), because a live session cannot know
  older history — never an invented full count.
- **Show in MoorMap** through a quickslot with an alias shortcut, whenever a
  position has been verified.
- Window in the client's own style: title bar, close button, draggable.
- **Start icon** at the right screen edge: a click opens or hides the window, a
  drag moves it. Window and icon position as well as visibility are remembered.
- Test and developer content is hidden, and the tests keep it that way.

Not included: items, crafting, equipment, an own map and character export.

## Screenshots

Tree by region, zone and area — with the epic story in its own branch. All nodes
start collapsed:

![The tree: regions, epic story and the special branches](docs/screenshots/tree-overview.png)

Description and objectives split into steps, with the verified MoorMap position
underneath:

![Quest details with numbered steps and the MoorMap button](docs/screenshots/quest-details.jpg)

Progress while playing — every branch counts what you have finished:

![Quests with finished and open entries](docs/screenshots/quest-progress.jpg)

Deeds use the same tree and the same counters:

![Deeds by region and zone with finished entries](docs/screenshots/deed-progress.jpg)

## Using it

- `/mql` opens or hides the window; `/mql show` and `/mql hide` are explicit.
- **MoorMap** opens through the small quickslot next to "Show in MoorMap" in the
  detail pane. A plugin cannot run a slash command itself; MoorMap can only be
  driven by a quickslot shortcut. That is the documented way (as Compendium does
  it), which is why it is a quickslot and not a plain button.
- To pick up a new catalog after a game update, **restart the game**. Unloading
  and loading the plugin again in the same session can fail — the client is
  32-bit and does not manage to import the large catalog a second time; it then
  answers "Laden von 'MagicQuestLog' nicht möglich" and writes nothing to
  `Script.log`. A restart always loads the files from disk. In a **German
  client** every plugin command is called `Zusatzmodule` instead of `/plugins`
  (use `/zusatzmodule manager` for the manager).

## Watching your progress

The client announces completions in the quest channel as a header line plus the
name (`Completed:`, `Abgeschlossen:`, `Terminé :`). The plugin listens there, so a
quest you finish shows up immediately — no export, no restart.

What that means in practice:

- Ids seen live are stored **per character** in the client's own plugin data, not
  in `Data/Progress.lua`. A live session never overwrites an export and an export
  never overwrites a live session; both are merged for display.
- Deeds use the same header, so one handler covers quests and deeds.
- The message carries a **name, not an id**. 639 quest names and 237 deed names in
  the German catalog belong to more than one entry (race and class variants,
  repeatable lines). A shared name is **never** assigned to a guess: nothing is
  marked and the chat names what could not be assigned. Those stay in a list, so a
  later version or a manual decision can resolve them.
- Because a live session starts at zero, the headline says "finished (known)"
  until a `Progress.lua` supplies the older history.

## Licence

The plugin and its tools are MIT licensed; see `LICENSE`. The icons are a
separate case: they come from Lucide under the ISC licence (see
`icon-sources/NOTICE`). The quest and deed texts in the release archive are game
content and are not covered by either licence.

## Icons

All icons come from [Lucide](https://lucide.dev) (ISC licence, see
`icon-sources/NOTICE`). The client paints no SVG, so they ship as 32-bit Targa
textures in `Resources/`. The SVGs sit unchanged in `icon-sources/`;
`tools/build_icons.py` only recolours and sizes them.

| Icon | Used for |
|---|---|
| `start.tga` (`mop-sparkles`) | start icon at the screen edge |
| `quests.tga` (`scroll-text`), `deeds.tga` (`trophy`) | quests / deeds tab |
| `search.tga`, `clear.tga` (`x`) | search field and clearing it |
| `closed.tga`, `open.tga` (`chevron-*`) | collapsed / expanded nodes |
| `todo.tga` (`circle`), `done.tga` (`circle-check`) | open / finished in the list |
| `todobig.tga`, `donebig.tga` | the same marks in the detail pane |
| `mappin.tga` (`map-pin`) | the hint covering the MoorMap quickslot |

**Every icon is rendered at exactly the pixel size it is drawn at.** The client
samples plugin textures poorly, so a downscaled 32 px icon looks jagged. The size
is therefore stated twice: in `build_icons.py` and in `ICON_SIZE` in
`Window.lua`. Change a size in both.

## Installing

The catalog ships as a release archive because it is about 102 MB and thus not in
the repository. The archive is ready to install:

```sh
# unpack into the game's Plugins folder, then /mql in game
unzip MagicQuestLog-<version>.zip -d '<Plugins folder>'
```

In game: `/plugins load MagicQuestLog`, then `/mql` — or simply start the game,
which loads it by itself. To fetch a **new** catalog later, restart the game; a
reload in the same session can fail because of the catalog size.

## Building and checking

The examples assume `LORE_DIR` is a directory with extracted game data
(`quests.xml`, `deeds.xml`, `geoAreas.xml`, `labels/<language>/…`) and
`PLUGIN_DIR` is the game's `Plugins` folder.

```sh
# the shipped path: build from our own DAT export, check it, install it
MagicQuestLog/tools/rebuild-from-export.command "<EXPORT_DIR>" "<PLUGIN_DIR>"

# the old XML path, kept for comparison and for a Companion lore directory
MagicQuestLog/tools/rebuild.command "<LORE_DIR>" "<PLUGIN_DIR>"

# build a status file from a character export (read-only)
python3 MagicQuestLog/tools/build_progress.py <export.json>

# re-render the icons from the Lucide SVGs (read-only)
python3 MagicQuestLog/tools/build_icons.py

# build the release archive with the catalog (writes only to dist/)
python3 MagicQuestLog/tools/make_release.py
```

Both checks need a Python environment with `lupa` (Lua 5.1); either rebuild
script creates it under `.venv/` on first use:

```sh
.venv/bin/python MagicQuestLog/tools/verify_catalog.py   # data: ids, structure, counts
.venv/bin/python MagicQuestLog/tools/test_plugin.py      # plugin logic on real data
```

`tools/overrides.json` holds manual corrections: `hidden_ids` and different
paths. They are applied on every rebuild and never overwritten. Files carrying
the generator header `-- Generated by Magic Quest Log; do not edit.` are
replaced; anything else is refused.

### Where the catalog comes from

The shipped catalog is built from **our own DAT export**, not from Companion
XML. `tools/build_catalog_from_export.py` reads `quests.json`, `deeds.json`,
`areas.json`, `locations.json` and `manifest.json` from
`Companion-Test/source-exporter`, the category enums
(`enums/enum-names.json`, also read from the client) and MoorMap's map table. No
Companion application and no Companion XML are involved; the import is plain
Python and runs without Companion installed. The one optional Companion file is
`app/data/lore/landblocks.xml`, used only as a territory fallback.

```sh
MagicQuestLog/tools/rebuild-from-export.command \
  <export-dir> <Plugins-dir> <landblocks.xml>
```

Arguments can also come from `MQL_EXPORT`, `MQL_PLUGINS` and `MQL_LANDBLOCKS`.
Without the first argument the newest `full-dat-*` folder below
`Companion-Test/source-exporter` is used; without the third, `landblocks.xml` is
looked up in the usual Companion install locations. The script builds, runs
`verify_catalog.py` and `test_plugin.py`, prints the counts from `manifest.json`
and installs into `PLUGIN_DIR`. `tools/rebuild.command` still drives the old XML
path and is marked as such.

Result: 15,209 quests and 5,534 deeds per language, identical ids and identical
tree structure in all three languages (verified). 483 test/developer entries are
hidden. 11,583 quests get a zone (formerly 9,963) and 8,403 have a verified map
position (formerly 10,051).

Some territories used to stand twice in the tree, once as a zone and once as an
area inside a neighbouring zone: `zone:Agarnaith` next to
`area:Mordor:Agarnaith` and the same for Lhingris, Ambarûl, Khûd Zagin, Imhûlar,
Urash Dâr, Lossarnach, Osgiliath, Pinnath Gelin, Anfalas and Ringló Vale. An area
that carries the name of a known zone of the same region is now that zone
(530 quests on 13 category paths). The decision is made on the English keys, so
the tree stays identical in every language, and `verify_catalog.py` refuses a name
that appears both as zone and as area.

Two facts from the game data decide what is still possible. Both are worked out
in the catalogue, so all three languages and every view agree:

- 78 quests are **session plays** (`Quest_IsSessionQuest`): the game plays someone
  else for a while and never records them. None of the 87 session plays in the
  export appears in a played character's journal.
- 521 quests rule out another quest and are ruled out by it: each demands the
  other one "not started and not finished", so whoever took one cannot take the
  other. Which pairs those are is derived from the requirement blobs; the operator
  mapping (2 = not equal, 3 = equal, 0x30000000 = completed) was checked against
  1,886 prerequisites of finished quests, 96 % of whose targets are finished too.
  Missing prerequisite names, class or trait gates are *not* evaluated: the plugin
  cannot know what a character has.

**Known limits, accepted on purpose:**

- The DAT export carries no per-quest map reference. Companion XML has
  `<map mapId=… region=…>`; the DAT has only the category and the target
  coordinates. Where the category is not a zone (e.g. "Introduction" in The
  Shire), the territory is derived from the landblocks of all target positions —
  and only when they all agree. That fallback gives 4,804 quests and 680 deeds a
  zone. A majority decision was considered and rejected as a guess.
- Net effect against the XML: 1,620 quests gain a zone, 556 lose one, 5 switch.
  Two of the switches are Osgiliath → Eastern Gondor, one Ithilien → Anórien, one
  The Shire → Festival Grounds, one Moria → Eregion. These are documented, not
  repaired.
- The upper area comes from an explicit `REGIONS` list in the script, not from
  `geoAreas.parentId` or `Area_Region`: that tree is wrong for the world maps
  (Western Gondor, Mordor and King's Gondor hang under Rhovanion, Osgiliath under
  Eriador). Zones must keep their real accents (`Lothlórien`, `Old Anórien`,
  `Ringló Vale`, `Umbar Baharbêl`, `Haradwaith`, `Rhûn`); ASCII spellings make
  whole zones disappear silently.
- The export writes text markers bare (`PLAYER`, `CLASS`, without the `${…}`
  wrapper) in 14 and 2–18 places per language. The plugin fills them, and
  `test_plugin.py` checks that with a fixture built in the test itself.
- 1,454 quests still sit in the collection node "Ohne Gebiet" (9.6 %).
- Eleven exclusion pairs have both sides finished in the export although the data
  calls them exclusive. A finished entry always counts, so the rule never hides
  something that was done - but it is a reminder that the requirement blobs also
  describe entry points, not only either/or choices.

### Getting your older progress in

The plugin counts what you finish from the moment it is installed. Quests and
deeds from before that are not in the game's chat, so the plugin cannot know
them. There is one optional tool for this, and it ships with the plugin:
`MagicQuestLog/Optional-Progress-Tool/`. Use it once.

**What you need**

- The plugin, already installed.
- **LOTRO Companion** from <https://sourceforge.net/projects/lotrocompanion/>.
  Install it and leave it installed; you never start it and never import
  anything in it. The tool only borrows two files from its program folder.
- The game, running, with your character **in the world** (not at the launcher).

**Windows**

1. Log in your character and enter the world.
2. Open `Plugins\MagicQuestLog\Optional-Progress-Tool\` in Explorer.
3. Double-click `read-journal.bat`; allow the administrator prompt.
4. Wait until it says `Done`.
5. Close the game completely and start it again.
6. Type `/mql` — your old progress is counted.

**macOS**

LOTRO runs through Wine there, and `read-journal.command` knows that setup.

1. Log in your character and enter the world.
2. Open the same folder in Finder.
3. Double-click `read-journal.command`. If macOS blocks it, right-click it,
   choose **Open** and confirm once.
4. Wait until it says `Done`.
5. Close the game completely and start it again.
6. Type `/mql` — your old progress is counted.

**Why a restart?** The plugin reads the file when it loads. Unloading and loading
it again inside a running game usually fails because the catalog is large; a
restart always works.

The tool reads the journal of the character that is logged in — there is nothing
to choose. For a second character, log that one in and run it again; each
character keeps its own file. With two game windows open, close one first.

It reads only the quest journal: no inventory, money, mail, chat or account data,
and it never writes into the game. Delete `Data/Progress.lua` to undo it.

The same instructions ship in the folder (`README.md` and `START-HERE.txt`).
Developers find the internals, exit codes and the alternative route through
Companion's XML files in `tools/journal-reader/TECHNICAL.md`.

A character's own status file does **not** belong in the repository:
`Data/Progress.lua` is listed in `.gitignore`, `make_release.py` leaves it out of
the archive, and `Data/Progress.example.lua` shows the format with sample data.

## Where the catalog data comes from

The shipped catalog is built from **our own DAT export**. `Companion-Test/source-exporter`
reads the client's data files directly and writes JSON; see its README for the
exporter and its licence questions. The importer needs no Companion application.

| Source | Provides |
|---|---|
| `Companion-Test/source-exporter/full-dat-*/` | `quests.json`, `deeds.json`, `areas.json`, `locations.json`, `manifest.json` |
| `Companion-Test/source-exporter/enums/enum-names.json` | the category enums (also read from the client) |
| `GaranStuff/MoorMap/Defaults.lua` | map bounds for the verified positions |
| `LOTRO Companion` → `app/data/lore/landblocks.xml` | optional territory fallback |

The **old XML path** still exists in `build_catalog.py` and `rebuild.command`.
It reads extracted game data from two LOTRO Companion repositories, because the
map data is not in the first one:

| Source | Provides | Belongs at |
|---|---|---|
| `LotroCompanion/lotro-data` | `quests.xml`, `deeds.xml`, `geoAreas.xml`, `enums/`, `labels/<language>/` | `<LORE_DIR>` |
| `LotroCompanion/lotro-maps-db` | `maps/maps.xml` | `<LORE_DIR>/maps` |

```sh
git clone https://github.com/LotroCompanion/lotro-data.git     "<LORE_DIR>"
git clone https://github.com/LotroCompanion/lotro-maps-db.git  "<LORE_DIR>/maps"
```

That is the same layout a LOTRO Companion installation has, where both sit under
`app/data/lore/`. Files actually read: `quests.xml`, `deeds.xml`, `geoAreas.xml`,
`maps/maps/maps.xml`, `enums/QuestCategory.xml`, `enums/DeedCategory.xml`, and per
language the labels for quests, deeds, geoAreas, npc and both enums.

### Rights, kept apart on purpose

- **The plugin and its tools** are this repository's own work, MIT licensed (see
  `LICENSE`). No third-party code is bundled or linked: reading the game's
  database and reading Companion's status files are both done without foreign
  libraries. An earlier experiment that read the client's memory was dropped for
  this reason — it needed a third-party memory library whose licence is not
  settled.
- **The data files** come from LOTRO Companion, which is Apache-2.0 licensed. No
  Companion code is copied or linked; the extracted files are read locally and the
  catalog is generated from them. The extraction work is credited to that project.
- **The quest and deed texts** are game content. They belong to their rights
  holders (Standing Stone Games and the Tolkien rights holders), not to LOTRO
  Companion and not to this project. No licence here covers them.

The generated catalog is therefore *data about the game*, not licensed source
code. It never leaves a machine on its own: it is written into `plugin/…/Data/`
locally, and it is the release archive at the top of this page that hands it to
somebody else. Publishing plugins that carry game text is long-standing practice
in this community, but tolerance is not permission — the only body that can grant
that is the rights holder. `rebuild-from-export.command` exists precisely so
anyone can build the catalog from their own installation instead of taking a
copy.

## Limitations

- The catalog needs **an exported game-data set**: the JSON export of our own
  reader, or else extracted XML for the old path. Neither is part of this
  repository; without a fresh export nothing can be refreshed after a game
  update.
- The catalog is still **one large file per language and kind** (~32 MB for
  German). That costs time when loading. Splitting it into smaller files is the
  next step.
- **MoorMap needs one click** on the quickslot. A slash command cannot be run
  from inside a plugin.
- **Progress** is only as complete as its sources. A `Progress.lua` is a journal
  export from one point in time; live tracking only knows what happened since the
  plugin was loaded with that character. Neither replaces the other, and nothing
  here can know what was done before either of them existed.
- **The same name can appear more than once** — hundreds of quests sit twice in
  the same group (for example "Das letzte Wort" or "Einleitung überspringen").
  These are not duplicates from our build: every entry has its own id. They are
  separate quests that share a name, for instance with a different bestower (`7003783D` → Arcil,
  `7003A67E` → Éothain), or one version per race and class. The game only shows
  the applicable one; without prerequisite data the catalog cannot tell them
  apart and therefore keeps both visible. A bestower field in the catalog would
  be the clean distinction and is not implemented yet.
- **Texts and group names are resolved.** Placeholders such as `${PLAYER}`,
  `${CLASS}` or `${PLAYERNAME:A[m]|B[f]}` are replaced; the first with the
  character, the `A / B` form with both alternatives. Counters (`${CURRENT}`)
  stay as "counter in game" because the plugin does not know them. 16 group names
  in the German catalog carry such placeholders and would otherwise show raw.
- **Zone names are translated** as far as the language files provide them
  ("Bree-land" → "Breeland", "The Shire" → "Das Auenland"). The keys
  (`zone:Bree-land`) stay English on purpose, because the tree structure has to
  be identical in every language. Where a translation is missing, the English
  name is shown — never a guess.
- **Stored window positions are text**, not numbers. The client writes numbers
  with the decimal comma of the client language (`239,000000`), which is not
  valid Lua: it made the whole settings file unreadable.
- World regions follow an explicit comparison with the original maps.
  `geoAreas.parentId` is unusable for that: it hangs Gondor and Mordor off
  Rhovanion.
- Map positions are only offered when they have been verified against the
  **exact texture id** of the map and the MoorMap bounds, and the region code
  matches. Ambiguous or missing positions show no button at all: 8,403 of the
  15,209 quests have a verified position.
- Positions come from the original coordinates of objectives and bestowers.
  They are not always the start of the quest.
- The catalog totals are entries, not "reachable" quests. Class, race,
  alternatives and repeatability are part of them.
- Gender-dependent wording is shown as "mein Freund / meine Freundin"; the public
  player interface exposes no gender.

## Publishing

Ready-to-paste values for a LOTROInterface download — category, description,
changelog and the `.plugincompendium` file for the LOTRO Plugin Compendium — are
in [`packaging/lotrointerface.md`](packaging/lotrointerface.md).

## State and checks

Generated: 15,209 quests (483 test entries hidden) and 5,534 deeds per language,
8,403 verified quest positions in the German catalog (8,402 in English). A
progress file with 3,657 entries finished
(3,177 quests + 480 deeds), 579 running, 3 listed twice (repeatable) and 3
unknown ids. Data check: identical id sets and an identical tree structure in all
three languages, child totals add up. Plugin test: 21 checks green, among them a
collapsed start, name search including "ker izel" → "Kêr Izel", details without
raw placeholders, an honest display without a position, the English fallback when
a language catalog is missing, the header below the title bar, a labelled search
field, "n/total" counters, the cached tree when expanding, an ignored status file
of another character, resolved placeholders, LOTRO markup removed from texts, the
detail scroll reset when switching records, and that every icon texture named in
the Lua really exists.

**Fixed after the second play test** (not re-checked in game since): no rebuild
and re-sort of the whole catalog when expanding (the tree is cached), one control
per row instead of more than 40 for the status mark, the header below the title
bar, the search field labelled "Suchen", MoorMap through a quickslot alias
instead of printing a command that did nothing, and progress counters per node.

**Done after the third play test (2 Nov), not checked in game since:** icons from
Lucide (start icon `mop-sparkles`, tabs, search field, clearing, node chevrons,
status circles, map pin), description and step text one size larger (Verdana14
instead of Verdana12, title Verdana16), and documented that quest names can
repeat as separate entries.

**Done after the fourth play test (2 Nov), not checked in game since:** LOTRO
markup such as `<rgb=#FF0000>…</rgb>`, `<b>` and `<u>` is stripped from texts
instead of showing as tags, and switching records scrolls the detail pane back to
the top. Tree and
row text one size larger as well (Verdana14, like the description; row heights
20 and 18 px). The MoorMap slot no longer shows the alias: the map pin lies on
top of it as a click-through cover (`mapCover`/`mapIcon` with
`SetMouseVisible(false)`) so the click still reaches the quickslot underneath.

**Two more errors from the fifth play test, both fixed:**

1. **`Window.lua: SetValue: Invalid operation while the scroll bar is bound.`**
   The scroll reset set the value on a bar that a label drives. The client refuses
   that. The pane is now unbound, filled and rebound — the same way Compendium does
   it — which resets the offset without touching the bar.
2. **`MagicQuestLogSettings.plugindata: '}' expected near ','`** again. Stray
   numeric keys (`[1,000000] = 0,000000`) had got into the settings table at some
   point and were copied back on every save. Loading and saving now take only the
   six known keys, so junk cannot persist, and the file on disk was repaired.

**Four real bugs fixed during this round:**

1. **Placeholders were not replaced but became "[value]".** In `Resolve` the
   result of `gsub` was discarded, so the fallback branch overwrote every
   placeholder. `${PLAYER}` now reads the character name, `${CLASS}` the class,
   and `${PLAYERNAME:A[m]|B[f]}` becomes "A / B". A test asserts the character
   name appears in the text and the fallback marker does not.
2. **Group names with placeholders stayed raw** (`${PLAYERNAME:…}` in the tree).
   Captions now go through the same resolution as the texts.
3. **Zone names stayed English.** The generator looked a zone name up in a table
   keyed by id, so it never found anything. Now "Breeland", "Das Auenland",
   "Pays de Bree"; the keys stay English so the structure is identical in every
   language.
4. **The settings file was unreadable** (`'}' expected near ','`): the client
   writes numbers with a decimal comma. Positions are now stored as text. The
   damaged file was repaired by hand.

**Icons:** re-rendered at their exact display size. They used to be 32 px and
were shrunk to 11–18 px in game; the client samples plugin textures poorly, which
made them look jagged.

Row clicks go through the list selection, the same path the client uses
elsewhere; it is reset after every selection so the same row stays clickable.

**Fixed after the first play test:** missing window frame (now
`Turbine.UI.Lotro.Window`), missing start icon (now a Lucide texture) and rows
that did not react (now through the list selection). One requirement remains: the
client has to learn about the plugin folder — restart the game, then `/mql`.
