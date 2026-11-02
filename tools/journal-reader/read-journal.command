#!/bin/bash
# Magic Quest Log - read the quest journal and write Progress.lua (macOS)
#
# Double-clickable. Reads only the running client's quest journal (read-only) and
# writes the plugin's progress file from it.
#
# Override the detected paths with environment variables if needed:
#   MQL_LOTRO_APP=/Applications/The Lord of the Rings Online.app
#   MQL_COMPANION='/Applications/LOTRO Companion'
#   MQL_CHARACTER=Feldobar
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
LOTRO_APP="${MQL_LOTRO_APP:-/Applications/The Lord of the Rings Online.app}"
COMPANION="${MQL_COMPANION:-}"
CHARACTER="${MQL_CHARACTER:--}"
OUTPUT="${MQL_OUTPUT:-$HOME/Documents/The Lord of the Rings Online/Plugins/MagicQuestLog/Data/Progress.lua}"

echo "Magic Quest Log - reading the quest journal"
echo

fail() {
	echo "ERROR: $1" >&2
	shift
	for line in "$@"; do echo "  $line" >&2; done
	echo
	echo "Press any key to close."
	read -n 1 -s -r || true
	exit 1
}

# --- 1. Companion: memory library and a Windows Java -------------------------
if [ -z "$COMPANION" ]; then
	for candidate in "/Applications/LOTRO Companion" "/Applications/LotRO-Companion" \
	                 "$HOME/Applications/LOTRO Companion" "$HOME/Applications/LOTRO-Companion-Test/LotRO Companion"; do
		if [ -d "$candidate/app/lib" ]; then COMPANION="$candidate"; break; fi
	done
fi
[ -n "$COMPANION" ] && [ -d "$COMPANION/app/lib" ] || fail \
	"LOTRO Companion not found." \
	"Its memory library is required to read the client." \
	"Install it, or set MQL_COMPANION to its folder."
LIBS="$COMPANION/app/lib"
echo "Companion: $COMPANION"

JAVA="$COMPANION/runtime/bin/java.exe"
[ -f "$JAVA" ] || fail "no Windows Java found under $COMPANION/runtime/bin" \
	"Companion ships one there; reinstall it if the folder is missing."
echo "Java:      $JAVA"

# --- 2. The game: Wine engine, prefix and client folder ---------------------
[ -d "$LOTRO_APP" ] || fail "LOTRO not found at $LOTRO_APP" \
	"Set MQL_LOTRO_APP to the app bundle."
SUPPORT="$LOTRO_APP/Contents/SharedSupport"
WINE="$SUPPORT/wine/bin/wine64"
[ -x "$WINE" ] || fail "no Wine engine at $WINE"
PREFIX="$SUPPORT/prefix"
[ -d "$PREFIX" ] || fail "no Wine prefix at $PREFIX"

CLIENT=""
while IFS= read -r found; do CLIENT="$(dirname "$found")"; break; done < <(find "$PREFIX/drive_c" -maxdepth 6 -name client_gamelogic.dat 2>/dev/null)
[ -n "$CLIENT" ] || fail "the LOTRO client folder was not found in the prefix" \
	"Start the game once so the prefix is complete."
echo "Client:    $CLIENT"

# Wine wants a distinct wineserver per prefix and the bundled libraries first.
export WINEPREFIX="$PREFIX"
export WINEMSYNC=1 WINEESYNC=1 WINEDEBUG=-all
export DYLD_FALLBACK_LIBRARY_PATH="$SUPPORT/wine/lib"

# --- 3. Paths inside Wine are Z:\... ----------------------------------------
if [ ! -f "$HERE/classes/JournalExport.class" ]; then
	fail "classes/JournalExport.class is missing" \
	"Take the prebuilt class from the repository, or compile it with:" \
	"  javac --release 8 -cp '$LIBS/*' -d classes JournalExport.java"
fi
win_path() { printf 'Z:%s' "$1" | tr '/' '\\'; }
CLASSPATH="$(win_path "$HERE/classes");$(win_path "$LIBS")\\*"
rm -f "$HERE/classes/JournalExport.class.lck" 2>/dev/null || true

echo
"$WINE" "$JAVA" -Djava.awt.headless=true -cp "$CLASSPATH" \
	JournalExport "$(win_path "$CLIENT")" "$(win_path "$OUTPUT")" "$CHARACTER" 2>&1 \
	| grep -vE "fixme:|err:sync|FreeType|TrueType|freetype" || true

RESULT=${PIPESTATUS[0]}
echo
if [ "$RESULT" -eq 0 ]; then
	echo "Done. Reload the plugin in game:"
	echo "    /plugins unload MagicQuestLog"
	echo "    /plugins load MagicQuestLog"
	echo
	echo "Note: a running plugin session may overwrite the file when it unloads."
	echo "Running this tool again rewrites it."
else
	echo "Nothing was written (code $RESULT)."
	echo "Usual causes: the game is not running, the character is not in the world,"
	echo "or a different character is logged in."
fi
echo
echo "Press any key to close."
read -n 1 -s -r || true
