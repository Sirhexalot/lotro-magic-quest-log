# Journal reader – questions and answers

You do not need this page to use the tool. [`START-HERE.txt`](START-HERE.txt) has
the four steps. This page answers what people ask afterwards.

## Do I have to use LOTRO Companion?

No. You only have to **install** it once. The tool borrows two files from its
program folder that can read the game's memory; those files are not ours to give
away. Companion itself never starts, and you do not import anything in it.

## Why does it need the game running?

The quest journal exists only while the game is open: the client keeps it in
memory and nowhere else. So the tool has to look while your character stands in
the world. Being at the launcher or the character selection is not enough.

## Which character does it read?

The one that is logged in. There is nothing to choose, because the game only
holds that one in memory. For a second character, log it in and run the tool
again — each character keeps its own progress file.

If two game windows are open, close one first. The tool refuses to guess.

## Is my data safe?

Yes. It reads the list of finished and running quests and deeds — nothing else.
No inventory, no money, no mail, no chat, no account data. It never writes into
the game and never sends anything anywhere; it only writes one file inside the
plugin folder: `Data/Progress.lua`.

## Can I undo it?

Delete `MagicQuestLog/Data/Progress.lua`. The plugin then shows plain totals
again, as if the tool had never run.

## It said `Done`, but nothing changed

The file is read when the plugin loads, so the game has to be restarted. Unloading
and loading the plugin inside a running game usually fails because the catalog is
large; a restart always works.

## The tool stops and writes nothing

It tells you why. The usual causes:

| What it says | What to do |
|---|---|
| LOTRO Companion was not found | Install it, or point `COMPANION_DIR` (Windows) or `MQL_COMPANION` (Mac) at its folder |
| the LOTRO client folder was not found | Start the game once so the path exists |
| no LOTRO processes found / enter the world first | The game is closed, or your character is not logged in yet |
| the active character is X, not Y | A different character is logged in — log in the right one |

After a big game update the read can fail until LOTRO Companion ships an update.
That only affects this tool. The plugin keeps working; it just will not add older
progress until then.

## On a Mac

LOTRO runs through Wine there. `read-journal.command` knows that setup and finds
the game and its Wine prefix by itself; nothing has to be configured.

## Something for developers?

[`TECHNICAL.md`](TECHNICAL.md) has the internals: what exactly is read, exit
codes, rebuilding the prebuilt class and the alternative route through
Companion's XML files.
