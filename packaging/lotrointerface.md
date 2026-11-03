# Text for the LOTROInterface download

Everything here is meant to be pasted into the download form — nothing else.
Author-only notes live in [publish-notes.md](publish-notes.md). The formatted text actually pasted (BBCode) is [lotrointerface.bbcode](lotrointerface.bbcode).

## Fields

| Field | Value |
|---|---|
| Category | LotRO Stand-Alone Plugins → Other |
| Name | **Magic Quest Log** (must match the `.plugin` file exactly) |
| Version | 0.2.0 |
| File | `dist/MagicQuestLog-<version>.zip` |
| Author | Adrian |
| Homepage | https://github.com/Sirhexalot/lotro-magic-quest-log |

## Description – short version

> Quest and deed atlas for Middle-earth: browse 15,209 quests and 5,534 deeds by
> area and epic story, read the details without spoilers, see what you have finished, and jump
> straight to the spot on MoorMap — all inside the game.

## Description – full version

### What is this?

Magic Quest Log is a quest and deed companion that runs inside the game. It shows
you every quest and deed in Middle-earth, sorted by where it happens, with the
full text and its steps — and it remembers what you have already done.

No browser tab, no second monitor, no outside program: one window in the game.

### What it does

- **Everything in one tree.** Two levels only: region (or epic volume), then
  area. An area lists its quests under foldable sections – the area itself,
  sub-areas, quest groups.
- **Search** for any part of a name or an area. Small spelling differences don't
  matter: "ker izel" finds "Kêr Izel".
- **No spoilers.** You see level, quest giver, requirements, quest chain and
  description. Steps and objectives only when you ask for them – for that one
  quest.
- **Filter** with four buttons: All, Open, Done, Available. "Available" checks
  your level and earlier quests.
- **See your progress.** Anything you finish is counted right away. Every branch
  shows "done / total", deed counters show "44/75", finished entries get a green
  check.
- **Show it on the map.** One click opens MoorMap where the quest giver stands,
  or at the first objective when you show them – only where the position is
  known. No guessed pins.
- **Facts from the game.** LOTRO points of deeds, daily, repeatable, fellowship,
  instance, time limit.
- **German, English and French.** The plugin follows your game language.

Not included: items, crafting recipes, equipment, an own map.

### Installing

**1.** Unzip the download into the game's `Plugins` folder.

That is the folder where your other plugins live — you will see `Compendium`,
`GaranStuff` or similar in it. If you installed plugins with LOTRO Plugin
Compendium before, use the path shown in its settings.

After unzipping, `Plugins\MagicQuestLog\MagicQuestLog.plugin` must exist, next to
`Main.lua` and the `Data` folder.

**2.** Start the game.

**3.** Load the plugin. Type:

```
/plugins load MagicQuestLog
```

German client: plugin commands are called `Zusatzmodule` there, so type
`/zusatzmodule laden MagicQuestLog`.

You can also simply restart the game; the plugin then loads by itself.

**4.** Type `/mql` to open the window.

That is all. Only the map button needs
[MoorMap](https://www.lotrointerface.com/downloads/info532-MoorMap.html) by Garan;
everything else works without it.

### Your older quests and deeds — and several characters

The plugin counts what you finish **from the moment it is installed**. Quests and
deeds you completed before that are not in the game's chat messages, so the plugin
cannot know them by itself. **LOTRO Companion** knows them, and the free web page
of this plugin hands them over. If you don't care about the old entries, skip
this; the plugin works fine without it.

1. **LOTRO Companion** (free, <https://sourceforge.net/projects/lotrocompanion/>):
   log in your character and enter the world, then in Companion click
   **Import from LOTRO…** under *Misc*, then *Refresh* and *Start*.
2. Open **<https://llb.sirhexalot.de/spielstand.html>** and choose Companion's
   `characters` folder. It is read **only in your browser** — nothing is uploaded.
3. Click **Write into the LOTRO folder** (Chrome, Edge) or **Download as zip** and
   unpack the zip into the game's `PluginData` folder.
4. Open the Magic Quest Log window. Done — no restart needed.

The page explains every step for Windows and for Mac (where Companion runs in the
same Wine setup as the game), including where the folders are.

**Several characters:** load as many as you like. In the plugin, the button at the
top right switches between all characters of the server you play on. On the web
page, the menu does the same for the map.

**Collecting deeds above all?** Have a look at
[Deed Tracker](https://www.lotrointerface.com/downloads/info1139-DeedTracker.html)
by b414213562 — a mature plugin just for deeds. Magic Quest Log is mainly about
quests; both work side by side.

### Screenshots

Uploaded (four is the site's maximum), files in `docs/screenshots/`:

1. `tree-overview.png` — "Everything in one window: regions, the epic story and
   the special branches, all collapsed at first."
2. `quest-details.jpg` — "Description and objectives split into steps, with the
   verified map position underneath."
3. `progress-characters.jpg` — "Progress page: load LOTRO Companion's folder in
   your browser, nothing is uploaded"
4. `map-character-switch.jpg` — "The web map with your progress and a character
   switch"

Not uploaded any more, but kept: `quest-progress.jpg`, `deed-progress.jpg`,
`progress-page.jpg`. Still to take: the character switch inside the plugin window.

### Good to know

- The window and the small icon at the screen edge remember their place. Clicking
  the icon opens or hides the window.
- If the plugin does not appear after installing, refresh the list:
  `/plugins refresh` (German: `/zusatzmodule aktualisieren`), then load it.
- The catalogs are large (about 100 MB in total, three languages). The first load
  after a game start takes a moment.

### Changes

0.3.0 - what the LOTRO Log Book shows, now in the plugin.

- No spoilers: objectives per quest on request; MoorMap points at the quest giver.
- Quest giver, requirements, quest chain, LOTRO points, daily/repeatable,
  "available" filter.
- Tree with two levels and foldable sections; four filter buttons.
- More positions: 12,010 quests with an objective, 6,621 with the giver's place.

0.2.0 - progress from LOTRO Companion, several characters.

- Your older progress now comes from LOTRO Companion through the plugin's web page:
  choose Companion's folder there, write the result into the game's PluginData
  folder. It is read in your browser only. The separate tool from 0.1.x is gone; it
  needed an update after every game update.
- A character switch in the window: every character of your server that has
  progress. Each import shows its date.
- A new import is picked up whenever you open the window.
- Live progress is kept per character. Progress from 0.1.x is taken over.

0.1.2 - the counters show what is still possible.

- A session play is never written to the journal, so it is now marked and left out of
  the counters instead of standing there as permanently open.
- Of two quests that rule each other out only one can be taken. Once one is finished
  the other is marked "not possible" and no longer counted - for example the alternate
  ninth chapter of volume IV. A chapter group that showed 6 of 8 now reads 6/6.

0.1.1 — long names and a duplicate area fixed.

- A long quest or deed name now wraps onto a second line and the row grows with
  it. Before, the second line was drawn underneath the next row and could not be
  read ("Rückeroberung des Agarnaith: Mokál Rukh").
- Territories no longer appear twice in the tree: "Agarnaith", "Lhingris",
  "Ambarûl", "Khûd Zagin", "Imhûlar", "Urash Dâr", "Lossarnach", "Osgiliath",
  "Pinnath Gelin", "Anfalas" and "Ringló Vale" were listed once as a zone and once
  as an area inside a neighbouring zone. 530 quests moved to the plain zone.

0.1.0 — first release.

- 15,209 quests (483 test entries hidden) and 5,534 deeds per language, with
  descriptions, step objectives and over 8,400 verified map positions.
- Tree by area and epic story, accent-insensitive search, detail pane with steps
  and counts, start icon, remembered window placement.
- Progress from the quest channel while playing, so what you just finished shows
  up without any export or restart.
- MoorMap integration through a quickslot, because a plugin cannot run a slash
  command itself.
