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

That is the folder which already holds your other plugins — you will see
`Compendium`, `GaranStuff` or similar in it. If you installed plugins with LOTRO
Plugin Compendium before, use the path it shows in its settings.

Check the result: `MagicQuestLog.plugin` must sit **directly** in
`Plugins\MagicQuestLog\`, next to `Main.lua` and the `Data` folder.

**2.** Start the game.

**3.** Type `/plugins load MagicQuestLog`, or restart the game.

**4.** Type `/mql` to open the window.

That is all. Enemy positions and the map button need [MoorMap](https://www.lotrointerface.com/downloads/info532-MoorMap.html)
by Garan; everything else works without it.

### Older quests

The plugin counts what you finish from the moment it is installed. Quests
completed before that are not in the game's journal messages, so they cannot be
counted — no plugin can change that.

There is an optional extra for it on the project page
(<https://github.com/Sirhexalot/lotro-magic-quest-log>). It is not part of this
download and is not needed to use the plugin.

### Changes

0.1.0 — first release.

- 15,117 quests (372 test entries hidden) and 5,534 deeds per language, with
  descriptions, step objectives and 71,189 verified map positions.
- Tree by area and epic story, accent-insensitive search, detail pane with steps
  and counts, start icon, remembered window placement.
- Progress from the quest channel while playing, so what you just finished shows
  up without any export or restart.
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

## The old-progress question

The plugin needs nothing but its own files. Older progress can only be read with
software that knows the client's memory, and that is not ours:

| Option | Cost |
|---|---|
| ship the memory library (`delta-lotro-memory`) | needs the author's permission; his `delta-*` repositories carry no licence file |
| require a local LOTRO Companion | works today, but a store page that says so loses most players |
| no import at all | plugin is complete in itself; only quests from install time on are counted |

Current state: the tool exists in the repository under `tools/journal-reader/`
and is **not** part of the download, so the download has no dependency at all.
If the permission is granted, the tool can go back into the archive and the page
gets one step instead of a pointer.

## Before uploading

- Play-test the current build: open, search, details, MoorMap.
- Raise the version in `plugin/MagicQuestLog/MagicQuestLog.plugin` **and** here,
  then rebuild the archive so they cannot drift apart.
- LPC currently reports 403 errors for many users because of Cloudflare on
  lotrointerface.com; that is outside this project.
