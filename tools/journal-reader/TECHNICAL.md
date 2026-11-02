# Journal reader – technical notes

For developers. Players only need [`START-HERE.txt`](START-HERE.txt).

## What it reads

| Read | Not read |
|---|---|
| the character summary, only to name the file | inventory, wallet, mail, chat, account data |
| `m_completedQuestRecords` (keys only) | the record values and their counters |
| `m_currentQuestRecords` (keys only) | any part of the client's configuration |

Read-only: no write call into the client, no general memory dump, no account or
session data. The journal does not say whether an id is a quest or a deed; the
catalog decides that, which is why nothing is classified here.

Verified against a running client on 2 November 2026: 3,660 completed and 582
active records, written and then checked with `verify_progress.py`.

## Requirements

| | |
|---|---|
| LOTRO Companion | `app/lib/delta-lotro-memory-*.jar` and a Windows Java under `runtime/bin` |
| LOTRO client | the folder containing `client_gamelogic.dat` |
| Rights | on Windows the client may have to run as administrator for the read |

The tool does not use Companion's interface and Companion does not have to run.
The `delta-*` libraries are not part of this repository and carry no licence file
of their own, so they are never redistributed.

## Rebuilding the prebuilt class

`classes/JournalExport.class` is prebuilt for Java 8 on purpose: Companion ships
a **JRE only**, without `javac`, so compiling on the user's machine is not an
option. Rebuild it after changing the source:

```sh
javac --release 8 -cp '<companion>/app/lib/*' -d classes JournalExport.java
```

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
- The plugin only ever reads `Progress.lua`; its live data goes to the client's
  per-character plugin data.

## Alternative route

`../build_progress_from_companion.py` reads the two XML files that LOTRO
Companion writes per imported character (`questsStatus.xml`, `deedsStatus.xml`).
Same result, no memory access, no foreign code — but it needs Companion's own
character import first. Not used by the plugin and not mentioned in the player
instructions.

`verify_progress.py` checks a written file without any game data.
