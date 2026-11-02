# Publishing on LOTROInterface

Values to fill into the download form at
<https://www.lotrointerface.com/downloads/> — category **LotRO Stand-Alone
Plugins → Other**, the same place LOTRO Compendium sits.

## Why it works at all

- The upload check that trips most plugins is the folder structure: the archive
  must contain **one top-level folder** holding the `.plugin` file. This one
  does (`MagicQuestLog/MagicQuestLog.plugin`), which is also what the LOTRO
  Plugin Compendium (LPC) needs.
- The `.plugin` file states the name **Magic Quest Log**. It must match the
  download title exactly, character for character, or the client and LPC show
  two entries.
- Precedent for shipping game text: LOTRO Compendium (id 526) carries the whole
  quest and deed database in its download. See "Where the catalog data comes
  from" in the README for the rights position.

## Fields

| Field | Value |
|---|---|
| Category | LotRO Stand-Alone Plugins → Other |
| Name | Magic Quest Log |
| Version | 0.1.0 |
| File | `dist/MagicQuestLog-<version>.zip` from `tools/make_release.py` |
| Author | Adrian |
| Homepage | https://github.com/Sirhexalot/lotro-magic-quest-log |

Tagline for the description header:

> Quest and deed atlas for Middle-earth: browse 15,117 quests and 5,534 deeds by
> area and epic story, read objectives and rewards, see what you have finished,
> and jump straight to the spot on MoorMap.

### About

Magic Quest Log is a standalone quest and deed atlas that runs inside the game.
It does not need a browser tab, an overlay or a second monitor.

- **Tree** by region, zone, area and group, with the epic story sorted by volume
  and book, plus separate branches for missions, instances, crafting, festivals
  and everything without a geographic home. All nodes start collapsed.
- **Search** by any part of a name, ignoring case and accents, so "ker izel"
  finds "Kêr Izel".
- **Details** with the description and the objectives split into steps. Counts
  that the game states are shown as "required: 10"; live counters are never made
  up.
- **Progress**: drop in a status file and every node shows finished of total,
  e.g. `(163/276)`, with a green check on what is done. Without that file the
  plugin shows plain totals and claims nothing about your character.
- **Show in MoorMap** jumps to a verified position. Positions are only offered
  when they were checked against the map's own texture id and MoorMap's bounds;
  doubtful ones show no button instead of a wrong pin.
- **Languages**: German, English and French catalogs with identical ids and an
  identical tree; the plugin follows the client language and falls back to
  English. Icons from Lucide.

Not included: items, crafting, equipment, an own map and character export.

### Changes

0.1.0 — first release.

- Quests and deeds in three languages: 15,117 quests (372 test entries hidden)
  and 5,534 deeds per language, with descriptions, step objectives and 71,189
  verified map positions.
- Tree by area and epic story, accent-insensitive name search, detail pane with
  steps and counts, start icon, remembered window placement.
- Optional progress file for finished, running, repeatable and unknown ids.
- MoorMap integration through a quickslot, because a plugin cannot run a slash
  command itself.

### Installation

1. Unzip the archive into the game's `Plugins` folder, so that
   `Plugins/MagicQuestLog/MagicQuestLog.plugin` exists.
2. Start the game, or type `/plugins load MagicQuestLog` in game.
3. `/mql` opens or hides the window; `/mql show` and `/mql hide` are explicit.

To use your own progress, write your finished ids into
`MagicQuestLog/Data/Progress.lua`; `Progress.example.lua` in the same folder
shows the format. A file that belongs to another character is ignored on
purpose.

MoorMap (by Garan) is optional but needed for the map button. The plugin reads
its own files only; nothing is written back into the game.

## After the first upload

The download needs staff approval before it is public. Once the page exists, two
things can be added:

1. **`.plugincompendium` file** so LOTRO Plugin Compendium (LPC) can install and
   update the plugin. It needs the numeric id from the download URL, which only
   exists afterwards — so it goes into the next upload:

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

   Values are case sensitive, the name must match the download title, and the
   version must be raised with every upload. Inclusion in the LPC list is
   requested in the comments on the LPC download page (id 663).

2. **Screenshots** for the Pictures section. Two are enough: the tree with the
   detail pane, and a quest whose objectives show counts.

## Before uploading

- Play-test the current build. The plugin must open, search, show details and
  reach MoorMap; a release that fails on start is worse than none.
- Raise the version in `plugin/MagicQuestLog/MagicQuestLog.plugin` and in this
  file, and rebuild the archive so the two cannot drift apart.
- Note that LPC currently reports 403 errors for many users because of
  Cloudflare protection on lotrointerface.com; that is outside this project.
