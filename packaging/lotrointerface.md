# Text for the LOTROInterface download

Everything here is meant to be pasted into the download form — nothing else.
Author-only notes live in [publish-notes.md](publish-notes.md).

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

> Quest and deed atlas for Middle-earth: browse 15,209 quests and 5,534 deeds by
> area and epic story, read the objectives, see what you have finished, and jump
> straight to the spot on MoorMap — all inside the game.

## Description – full version

### What is this?

Magic Quest Log is a quest and deed companion that runs inside the game. It shows
you every quest and deed in Middle-earth, sorted by where it happens, with the
full text and its steps — and it remembers what you have already done.

No browser tab, no second monitor, no outside program: one window in the game.

### What it does

- **Everything in one tree.** Quests and deeds sorted by region, zone and area.
  The epic story has its own branch, sorted by volume and book. Missions,
  instances, crafting and festivals have their own branches too.
- **Search** for any part of a name. Small spelling differences don't matter:
  "ker izel" finds "Kêr Izel".
- **Read the details.** Description and objectives, split into steps, with the
  number the game asks for ("required: 10"). The plugin never invents a number
  it does not know.
- **See your progress.** Anything you finish while playing is counted right
  away. Every branch shows "done / total", for example `(163/276)`, and finished
  entries get a green check.
- **Show it on the map.** One click opens MoorMap at the right spot — but only
  where the position has really been checked. No guessed pins.
- **German, English and French.** The plugin follows your game language. All
  three catalogs have the same entries and the same tree.

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

### Optional: bring in your older quests and deeds

The plugin counts what you finish **from the moment it is installed**. Quests and
deeds you completed before that are not in the game's chat messages, so the plugin
cannot know them by itself.

There is a small extra tool for exactly that. It reads the quest journal of the
character you are playing right now and writes it into the plugin. Use it once —
then everything you have ever done shows up as finished. If you don't care about
the old entries, skip this whole section; the plugin works fine without it.

**What you need**

- The plugin, already installed (see above).
- **LOTRO Companion**, free, from
  <https://sourceforge.net/projects/lotrocompanion/>. Install it and leave it
  installed. You do **not** have to start it, and you do not have to import
  anything in it — the tool only borrows two files from its program folder.
- The game, running, with your character **in the world**. Being at the launcher
  or the character selection is not enough.

**Where the tool is**

It comes with the plugin, inside its folder:

```
Plugins\MagicQuestLog\Optional-Progress-Tool\
```

[Screenshot: the folder `Optional-Progress-Tool` open in Explorer, showing
`START-HERE.txt`, `read-journal.bat` and `read-journal.command`. Caption:
"Both launchers live in this folder — use the one for your system."]

**Step by step (Windows)**

1. Log in your character and enter the world.
2. Open the folder above in Explorer.
3. Double-click **`read-journal.bat`**.
4. A black window opens and prints a few lines. Windows may ask for administrator
   rights — allow it, reading the game's memory needs that.
5. Wait until it says `Done`.
6. Close the game completely and start it again. The plugin reads the file while
   it loads; reloading the plugin inside a running game often fails because the
   catalog is large. A restart always works.
7. Type `/mql`. The headline now shows your real numbers instead of
   "finished (known)".

**Step by step (macOS)**

The Mac version is a special case: LOTRO runs through Wine there, and this
launcher already knows how to reach into it. It is made for exactly this setup.

1. Log in your character and enter the world.
2. Open the plugin folder in Finder and go to `Optional-Progress-Tool`.
3. Double-click **`read-journal.command`**.

   macOS may block the file the first time because it comes from a download. Then
   right-click it, choose **Open**, and confirm once. After that a double-click is
   enough.
4. A terminal window opens and prints a few lines. Wait until it says `Done`.
5. Close the game and start it again, as in step 6 above.
6. Type `/mql` — your old progress is now counted.

[Screenshot: the terminal window after a successful run, showing `Done`. Caption:
"When it says Done, only a game restart is missing."]

**One character at a time**

The tool always reads the character that is logged in, because that is the only
one the game keeps in memory. There is nothing to choose. For a second character,
log that one in and run the tool again — each character keeps its own progress
file, and the plugin shows the one that belongs to the character you play.

If two game windows are open, close one first; the tool refuses to guess.

**What it reads**

Only the quest journal of your character: the list of finished and running quests
and deeds. Nothing else — no inventory, no money, no mail, no chat, no account
data. It never writes into the game; it only creates one file inside the plugin
folder. Delete `MagicQuestLog\Data\Progress.lua` if you ever want to go back to
plain totals.

**If it does not work**

The tool stops and tells you why. It never writes half a file.

| Message | What to do |
|---|---|
| LOTRO Companion was not found | Install it, or point `COMPANION_DIR` (Windows) or `MQL_COMPANION` (Mac) at its folder |
| the LOTRO client folder was not found | Start the game once so the path exists |
| no LOTRO processes found / enter the world first | The game is closed, or your character is not logged in yet |
| the active character is X, not Y | A different character is logged in — log in the right one |

After a big game update the read can fail until LOTRO Companion ships an update.
That only affects this tool. The plugin itself keeps working; it just will not add
older progress until then.

### Screenshots

Upload these in order; the files sit in `docs/screenshots/`.

1. `tree-overview.png` — "Everything in one window: regions, the epic story and
   the special branches, all collapsed at first."
2. `quest-details.jpg` — "Description and objectives split into steps, with the
   verified map position underneath."
3. `quest-progress.jpg` — "Every branch counts what you have finished; finished
   quests get a green check."
4. `deed-progress.jpg` — "Deeds use the same tree and the same counters."

Still to take: the `Optional-Progress-Tool` folder in Explorer and the terminal
after a successful run, both for the optional section above.

### Good to know

- The window and the small icon at the screen edge remember their place. Clicking
  the icon opens or hides the window.
- If the plugin does not appear after installing, refresh the list:
  `/plugins refresh` (German: `/zusatzmodule aktualisieren`), then load it.
- The catalogs are large (about 100 MB in total, three languages). The first load
  after a game start takes a moment.

### Changes

0.1.0 — first release.

- 15,209 quests (483 test entries hidden) and 5,534 deeds per language, with
  descriptions, step objectives and over 8,400 verified map positions.
- Tree by area and epic story, accent-insensitive search, detail pane with steps
  and counts, start icon, remembered window placement.
- Progress from the quest channel while playing, so what you just finished shows
  up without any export or restart.
- Optional journal reader for progress from before the installation, shipped in
  `Optional-Progress-Tool`.
- MoorMap integration through a quickslot, because a plugin cannot run a slash
  command itself.
