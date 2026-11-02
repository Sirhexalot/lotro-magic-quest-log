# Publishing on LOTROInterface

Two parts: **the text to paste into the download form**, and the admin notes for
you as the author.

---

# Part 1 – the download page

## Fields

| Field | Value |
|---|---|
| Category | LotRO Stand-Alone Plugins → Other |
| Name | **Magic Quest Log** (must match the `.plugin` file exactly) |
| Version | 0.1.0 |
| File | `dist/MagicQuestLog-<version>.zip` |
| Author | Adrian |
| Homepage | https://github.com/Sirhexalot/lotro-magic-quest-log |

## Description – short version

> Quest and deed atlas for Middle-earth: browse 15,117 quests and 5,534 deeds by
> area and epic story, read the objectives, see what you have finished, and jump
> straight to the spot on MoorMap — all inside the game.

## Description – full version

### About

Magic Quest Log is a quest and deed atlas that runs inside the game. No browser
tab, no overlay, no second monitor.

- **Tree** by region, zone, area and group, with the epic story sorted by volume
  and book, plus branches for missions, instances, crafting, festivals and
  everything without a geographic home. All nodes start collapsed.
- **Search** by any part of a name, ignoring case and accents — "ker izel" finds
  "Kêr Izel".
- **Details** with the description and the objectives split into steps. Counts the
  game states are shown as "required: 10"; live counters are never invented.
- **Progress**: anything you finish while playing is picked up automatically and
  every node shows finished of total, e.g. `(163/276)`, with a green check.
- **Show in MoorMap** jumps to a verified position. A button only appears when the
  position was checked against the map's own texture and MoorMap's bounds.
- **German, English and French** catalogs with identical ids and an identical
  tree; the plugin follows the client language and falls back to English.

Not included: items, crafting, equipment, an own map and character export.

### Installation

**1.** Unzip the download into the game's `Plugins` folder.

You should end up with

```
Documents\The Lord of the Rings Online\Plugins\MagicQuestLog\MagicQuestLog.plugin
```

**2.** Start the game.

**3.** Type `/plugins load MagicQuestLog`, or restart the game.

**4.** Type `/mql` to open the window.

That is all. Enemy positions and the map button need [MoorMap](https://www.lotrointerface.com/downloads/info532-MoorMap.html)
by Garan; everything else works without it.

### Optional: your older progress

Everything you finish from now on is counted by itself. Quests you completed
**before** installing are not — the game never tells a plugin about the past.

If you want those too, there is one optional step, and it is included in the
download:

**1.** Install **LOTRO Companion** (free) from
<https://sourceforge.net/projects/lotrocompanion/>. Do **not** start it and do not
import anything in it — the tool only borrows two files from its program folder.

**2.** Start LOTRO and log in the character whose old quests you want. The
character has to be in the world, not just at the launcher.

**3.** Double-click

| Your system | File |
|---|---|
| Windows | `MagicQuestLog\Optional-Progress-Tool\read-journal.bat` |
| macOS | `MagicQuestLog\Optional-Progress-Tool\read-journal.command` |

Windows may ask for administrator rights; allow it. A console window prints a few
lines and closes when you press a key.

**4.** In game:

```
/plugins unload MagicQuestLog
/plugins load MagicQuestLog
```

The tree now counts what you have really completed.

There is no character to choose: the tool reads the character that is logged in.
For a second character, log that one in and repeat steps 3 and 4 — each character
keeps its own file.

The tool reads **only** the quest journal of the logged-in character: finished and
running quests and deeds. No inventory, no money, no mail, no chat, no account
data, and nothing is written into the game. If it cannot read, it says why and
writes nothing.

### Changes

0.1.0 — first release.

- 15,117 quests (372 test entries hidden) and 5,534 deeds per language, with
  descriptions, step objectives and 71,189 verified map positions.
- Tree by area and epic story, accent-insensitive search, detail pane with steps
  and counts, start icon, remembered window placement.
- Progress from the quest channel while playing.
- Optional import of older progress with the included tool.
- MoorMap integration through a quickslot, because a plugin cannot run a slash
  command itself.

---

# Part 2 – author notes

## Upload mechanics

- The archive must contain **one top-level folder** holding the `.plugin` file.
  It does: `MagicQuestLog/MagicQuestLog.plugin`. The optional tool lives inside
  that folder (`MagicQuestLog/Optional-Progress-Tool/`); the client ignores
  folders without a `.plugin` file, so it cannot disturb loading.
- The name in `.plugin` and in the download title must match character for
  character, otherwise the client and the Plugin Compendium show two entries.
- New uploads are invisible until staff approve them. While waiting, LPC
  downloads a broken zip; that is a known LPC bug, not ours.
- Precedent for shipping game text: LOTRO Compendium (id 526) carries the whole
  quest and deed database. Rights position: “Where the catalog data comes from”
  in the README.

## After the first upload

1. **`.plugincompendium`** so LPC can install and update. Needs the numeric id
   from the download URL, so it can only be added with the next upload:

   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <PluginConfig xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema">
     <Id>FILL_IN</Id>
     <Name>Magic Quest Log</Name>
     <Version>0.1.0</Version>
     <Author>Adrian</Author>
     <InfoUrl>https://www.lotrointerface.com/downloads/infoFILL_IN</InfoUrl>
     <DownloadUrl>https://www.lotrointerface.com/downloads/downloadFILL_IN</DownloadUrl>
     <Descriptors>
       <descriptor>MagicQuestLog\MagicQuestLog.plugin</descriptor>
     </Descriptors>
     <Dependencies />
   </PluginConfig>
   ```

   Case sensitive, name must match, raise the version with every upload. Ask for
   inclusion in the LPC list in the comments on the LPC download page (id 663).

2. **Screenshots**: two are enough — the tree with the detail pane, and a quest
   whose objectives show counts.

## Before uploading

- Play-test the current build: open, search, details, MoorMap.
- Raise the version in `plugin/MagicQuestLog/MagicQuestLog.plugin` **and** here,
  then rebuild the archive so they cannot drift apart.
- LPC currently reports 403 errors for many users because of Cloudflare on
  lotrointerface.com; that is outside this project.
