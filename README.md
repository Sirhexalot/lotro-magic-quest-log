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
  Every node starts collapsed.
- **Search** by name or part of a name, ignoring case and accents.
- On the right, the **description** and the objectives split into steps. Known
  objective counts read "required: 10"; live counters are never invented.
- **Progress** from an optional status file (`Data/Progress.lua`): the tree and
  the headline then show "finished / total" (e.g. `(163/276)`) and the details a
  green check. If the file is missing, or belongs to another character, only
  plain totals are shown — never an invented zero.
- **Show in MoorMap** through a quickslot with an alias shortcut, whenever a
  position has been verified.
- Window in the client's own style: title bar, close button, draggable.
- **Start icon** at the right screen edge: a click opens or hides the window, a
  drag moves it. Window and icon position as well as visibility are remembered.
- Test and developer content is hidden, and the tests keep it that way.

Not included: items, crafting, equipment, an own map and character export.

## Using it

- `/mql` opens or hides the window; `/mql show` and `/mql hide` are explicit.
- **MoorMap** opens through the small quickslot next to "Show in MoorMap" in the
  detail pane. A plugin cannot run a slash command itself; MoorMap can only be
  driven by a quickslot shortcut. That is the documented way (as Compendium does
  it), which is why it is a quickslot and not a plain button.
- To pick up a new catalog after a game update, reload the plugin
  (`/plugins unload MagicQuestLog`, `/plugins load MagicQuestLog`) or restart the
  game.

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

In game: `/plugins unload MagicQuestLog`, `/plugins load MagicQuestLog`, `/mql`.

## Building and checking

The examples assume `LORE_DIR` is a directory with extracted game data
(`quests.xml`, `deeds.xml`, `geoAreas.xml`, `labels/<language>/…`) and
`PLUGIN_DIR` is the game's `Plugins` folder.

```sh
# build the catalog, check it, install it (reads game data, never writes it)
MagicQuestLog/tools/rebuild.command "<LORE_DIR>" "<PLUGIN_DIR>"

# build a status file from a character export (read-only)
python3 MagicQuestLog/tools/build_progress.py <export.json>

# re-render the icons from the Lucide SVGs (read-only)
python3 MagicQuestLog/tools/build_icons.py

# build the release archive with the catalog (writes only to dist/)
python3 MagicQuestLog/tools/make_release.py
```

Both checks need a Python environment with `lupa` (Lua 5.1); `rebuild.command`
creates it under `.venv/` on first use:

```sh
.venv/bin/python MagicQuestLog/tools/verify_catalog.py   # data: ids, structure, counts
.venv/bin/python MagicQuestLog/tools/test_plugin.py      # plugin logic on real data
```

`tools/overrides.json` holds manual corrections: `hidden_ids` and different
paths. They are applied on every rebuild and never overwritten. Files carrying
the generator header `-- Generated by Magic Quest Log; do not edit.` are
replaced; anything else is refused.

A character's own status file does **not** belong in the repository:
`Data/Progress.lua` is listed in `.gitignore`, `make_release.py` leaves it out of
the archive, and `Data/Progress.example.lua` shows the format with sample data.

## Limitations

- The catalog reads **extracted game data in XML form**, not the binary LOTRO
  archives. Extracting that XML is not part of this project; without it nothing
  can be refreshed after a game update.
- The catalog is still **one large file per language and kind** (~32 MB for
  German). That costs time when loading. Splitting it into smaller files is the
  next step.
- **MoorMap needs one click** on the quickslot. A slash command cannot be run
  from inside a plugin.
- **Progress** only shows what the status file proves. It comes from a journal
  export taken at one point in time; it does not update itself and is no
  substitute for a new export.
- **The same name can appear more than once** — 381 of the 15,117 quests sit
  twice in the same group (for example "Das letzte Wort" or "Einleitung
  überspringen"). These are not duplicates from our build: 15,117 entries were
  checked and all 15,117 have different ids. They are separate quests that share
  a name, for instance with a different bestower (`7003783D` → Arcil,
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
  matches. Ambiguous or missing positions show no button at all: 10,051 of the
  15,117 quests have a verified position.
- Positions come from the original coordinates of objectives and bestowers.
  They are not always the start of the quest.
- The catalog totals are entries, not "reachable" quests. Class, race,
  alternatives and repeatability are part of them.
- Gender-dependent wording is shown as "mein Freund / meine Freundin"; the public
  player interface exposes no gender.

## State and checks

Generated: 15,117 quests (372 test entries hidden) and 5,534 deeds per language,
71,189 verified quest positions. A progress file with 3,657 entries finished
(3,177 quests + 480 deeds), 579 running, 3 listed twice (repeatable) and 3
unknown ids. Data check: identical id sets and an identical tree structure in all
three languages, child totals add up. Plugin test: 17 checks green, among them a
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
client has to learn about the plugin folder — reload the plugin or restart the
game, then `/mql`.
