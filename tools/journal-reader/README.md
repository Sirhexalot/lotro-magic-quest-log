# Journal reader – technical reference

**Start with [`START-HERE.txt`](START-HERE.txt)** if you just want to use it; that
file has the four steps. This one is the reference.

Reads the quest journal of the **running LOTRO client** and writes the plugin's
`Progress.lua` directly. Read-only towards the game: no write call into the
client, no general memory dump, no account or session data.

Verified against a running client on 2 November 2026: 3,660 completed and 582
active records, written and then checked with `verify_progress.py`.

## Setting it up

Three things have to exist, two of them are found automatically.

1. **The plugin.** The folder `Plugins/MagicQuestLog` has to be installed — the
   tool writes into its `Data` folder.
2. **LOTRO Companion.** Only for its `app/lib` (the memory library) and its
   Windows Java under `runtime/bin`. The tool does not use its interface. It does
   **not** have to run.
3. **The game, running**, with the character in the world. The launcher alone is
   not enough; the tool reads the journal of a logged-in character.

Then, from this folder:

| System | Start |
|---|---|
| Windows | double-click `read-journal.bat` |
| macOS | double-click `read-journal.command` |

Both wrappers search for Companion and the game, so nothing has to be configured
in the normal case. If the search fails, the error message names the variable to
set: `COMPANION_DIR` and `LOTRO_DIR` in the `.bat`, `MQL_COMPANION`,
`MQL_LOTRO_APP` and `MQL_OUTPUT` for the `.command`.

Afterwards, restart the game. The plugin reads the file at load; a reload inside
a running session is not reliable with the large catalog.

The result lands in `Plugins/MagicQuestLog/Data/Progress.lua`; the headline then
reads the full count instead of "finished (known)".

### Check the result without the game

```sh
python3 verify_progress.py <Progress.lua>
```

It loads the file, checks the generator header, the id format and the table the
plugin expects. Needs `lupa` (Lua 5.1).

## What it needs on the system

| | |
|---|---|
| LOTRO Companion | `app/lib/delta-lotro-memory-*.jar` and a Windows Java |
| LOTRO client | the folder containing `client_gamelogic.dat` |
| Rights | on Windows the client may have to run as administrator for the read |

`classes/JournalExport.class` is prebuilt for Java 8 on purpose: Companion ships
a **JRE only**, without `javac`, so compiling on the user's machine is not an
option. Rebuild it after changing the source:

```sh
javac --release 8 -cp '<companion>/app/lib/*' -d classes JournalExport.java
```

## What it reads, and what it does not

| Read | Not read |
|---|---|
| the character summary, only to name the file | inventory, wallet, mail, chat, account data |
| `m_completedQuestRecords` (keys only) | the record values and their counters |
| `m_currentQuestRecords` (keys only) | any part of the client's configuration |

The journal does not say whether an id is a quest or a deed; the catalog decides
that, which is why nothing is classified here.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | written |
| 1 | usage, paths, or the target file was not written by this tool |
| 2 | game not running, character not in the world, wrong character, or no read access |
| 3 | the read returned nothing plausible – nothing written |

Only a file whose first line is the generator header is replaced, and only through
a temporary file, so a failed run cannot leave half a file behind.

## Limits

- **Version-bound.** The memory library has to match the game client. After a
  game update the read can fail; the tool then reports it instead of writing a
  half-empty file.
- **One client only.** Two running clients are refused rather than guessing.
- **Live counters are not read.** Active records are listed, but not their
  objective progress.
- **The memory library is not part of this repository.** It comes from the user's
  own LOTRO Companion installation. LOTRO Companion as a distribution is
  Apache-2.0, while the repositories of the `delta-*` libraries carry no licence
  file — ask the author (lotrocompanion@gmail.com) before passing the jars on.
- The plugin only ever reads `Progress.lua`; its live data goes to the client's
  per-character plugin data. Running the tool again simply replaces the file.

## Alternative without any memory access

If the library cannot be used,
[`../build_progress_from_companion.py`](../build_progress_from_companion.py) reads
the two XML files that LOTRO Companion writes per imported character
(`questsStatus.xml`, `deedsStatus.xml`). Same result, no memory access, no foreign
code — but it needs Companion's own character import first.
