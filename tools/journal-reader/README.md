# Loading your older quests and deeds

Magic Quest Log counts what you finish from the moment it is installed. Everything
you did **before** that is not in the game's chat, so the plugin cannot know it by
itself.

This little tool reads the quest journal of the character you are playing and
writes it into the plugin. Run it once and your old progress is there. If you do
not care about the old entries, ignore this folder — the plugin works without it.

## What you need

- The plugin, already installed.
- **LOTRO Companion**, free, from
  <https://sourceforge.net/projects/lotrocompanion/>. Install it and leave it
  installed. You do **not** have to start it and you do not have to import
  anything — this tool only borrows two files from its program folder.
- The game, running, with your character **in the world**. Being at the launcher
  or the character selection is not enough.

## Windows: step by step

1. Log in your character and enter the world.
2. Open this folder in Explorer.
3. Double-click **`read-journal.bat`**.
4. A black window opens and prints a few lines. Windows may ask for administrator
   rights — allow it, reading the game's memory needs that.
5. Wait until it says `Done`.
6. Close the game completely and start it again.
7. Type `/mql`. The headline now shows your real numbers instead of
   "finished (known)".

## macOS: step by step

LOTRO runs through Wine on the Mac. `read-journal.command` knows that setup and
finds the game and its Wine prefix by itself.

1. Log in your character and enter the world.
2. Open this folder in Finder.
3. Double-click **`read-journal.command`**.

   macOS may block the file the first time because it came from a download. Then
   right-click it, choose **Open**, and confirm once. After that a double-click is
   enough.
4. A terminal window opens and prints a few lines. Wait until it says `Done`.
5. Close the game completely and start it again.
6. Type `/mql` — your old progress is counted.

**Why a restart?** The plugin reads the file when it loads. Unloading and loading
it again inside a running game usually fails because the catalog is large; a
restart always works.

## A second character

Log that character in and run the tool again. Each character keeps its own
progress file, and the plugin shows the one that belongs to the character you
play. There is nothing to choose, because the game only holds the logged-in
character in memory.

If two game windows are open, close one first. The tool refuses to guess.

## Is my data safe?

Yes. It reads the list of finished and running quests and deeds — nothing else.
No inventory, no money, no mail, no chat, no account data. It never writes into
the game and never sends anything anywhere; it only creates one file inside the
plugin folder: `Data/Progress.lua`.

## Undo

Delete `MagicQuestLog/Data/Progress.lua`. The plugin then shows plain totals
again, as if the tool had never run.

## If it does not work

It stops, tells you why and writes nothing. The usual causes:

| What it says | What to do |
|---|---|
| LOTRO Companion was not found | Install it, or point `COMPANION_DIR` (Windows) or `MQL_COMPANION` (Mac) at its folder |
| the LOTRO client folder was not found | Start the game once so the path exists |
| no LOTRO processes found / enter the world first | The game is closed, or your character is not logged in yet |
| the active character is X, not Y | A different character is logged in — log in the right one |

After a big game update the read can fail until LOTRO Companion ships an update.
That only affects this tool. The plugin keeps working; it just will not add older
progress until then.

## For developers

[`TECHNICAL.md`](TECHNICAL.md) has the internals: what exactly is read, exit
codes, rebuilding the prebuilt class and the alternative route through
Companion's XML files.
