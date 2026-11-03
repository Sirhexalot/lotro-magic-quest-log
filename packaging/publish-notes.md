# Publishing notes (author only)

Not for the download page. The text that goes there is in
[lotrointerface.md](lotrointerface.md).

## Upload mechanics

- The archive must contain **one top-level folder** holding the `.plugin` file.
  It does: `MagicQuestLog/MagicQuestLog.plugin`.
- The archive contains only the plugin. Older progress comes from LOTRO Companion
  through the map site (0.2.0); the journal reader shipped in 0.1.x is gone.
- The name in `.plugin` and in the download title must match character for
  character, otherwise the client and the Plugin Compendium show two entries.
- New uploads are invisible until staff approve them. While waiting, LPC
  downloads a broken zip; that is a known LPC bug, not ours.
- Precedent for shipping game text: LOTRO Compendium (id 526) carries the whole
  quest and deed database. Rights position: “Where the catalog data comes from”
  in the README.

## Submission state

Submitted on 2 November 2026 through `downloads/upload.php?op=fileupload&catid=29`
(LotRO Stand-Alone Plugins → Other), version 0.1.0, with all four screenshots.
The site answered: "Your interface or update has been submitted to our database
and is now awaiting approval from one of our file administrators." Nothing is
public until that approval.

Next once approved: take the numeric id from the download URL and add the
`.plugincompendium` file with the next upload.

## Updating an existing entry

File id **1346**: `downloads/editfile.php?id=1346` (only while logged in). The form
has `ftitle`, `version`, `fileaction` (`keep`/`replace`), `replacementfile`,
the description as `message`, `deletearchives` (left unchecked, as the form had it),
`allowpa`, `securitytoken`, `op=editfile`, `id`, `type`, `sbutton=Update`.
An update keeps the entry and goes back into the approval queue: the version and
the changes are visible at once, the download keeps serving the old archive until
a file admin approves it.

- 2 November 2026, evening: 0.1.2 uploaded (long names wrap, duplicate area gone,
  counters show only what is still possible). Page shows "awaiting approval";
  the download link still serves 0.1.0.
- 3 November 2026: 0.2.0 uploaded (progress from LOTRO Companion through the map
  site, character switch, journal reader removed, Deed Tracker recommended for
  deeds). Description replaced in full. Again "awaiting approval".

## After the first upload

1. **`.plugincompendium`** so LPC can install and update. Needs the numeric id
   from the download URL, so it can only be added with the next upload:

   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <PluginConfig xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema">
     <Id>FILL_IN</Id>
     <Name>Magic Quest Log</Name>
     <Version>0.2.0</Version>
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

Decided for 0.2.0 (on advice from Damien, LOTRO Companion's author): the plugin
uses **LOTRO Companion's own character files**, as Deed Tracker does. Companion
keeps its memory access current after every client update; its output format is
stable. The conversion runs in the browser on the map site (no upload), which
writes one plugin data file per character into `PluginData`. The journal reader
from 0.1.x is gone.

Why not rebuild it ourselves: LOTRO's Lua API has no quest access at all — the
only gameplay objects it exposes are `LocalPlayer`, `Class`, `Race` and
`Alignment`, so a plugin cannot see the journal. The past therefore only exists
in the client's memory, and reading it means re-deriving the object model: the
reference table, the class layouts from the database and the internal hash maps.
That is exactly what the third-party library already does, it breaks with game
patches, and asking its author is one email.

## Before uploading

- Play-test the current build: open, search, details, MoorMap.
- Raise the version in `plugin/MagicQuestLog/MagicQuestLog.plugin` **and** here,
  then rebuild the archive so they cannot drift apart.
- LPC currently reports 403 errors for many users because of Cloudflare on
  lotrointerface.com; that is outside this project.
