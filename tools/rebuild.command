#!/bin/bash
# Magic Quest Log: rebuild the catalog from a LOTRO Companion lore directory.
# Reads game data only; it never writes to the game files. Double-clickable in Finder.
#
# This is the OLD XML way. The shipped catalog is built from our own DAT export:
# use rebuild-from-export.command instead. This script stays for comparison and
# for anyone who only has a Companion lore directory.
#
# Usage:  rebuild.command [LORE_DIR] [PLUGIN_DIR]
#
# LORE_DIR    a LOTRO Companion lore directory (contains quests.xml, deeds.xml,
#             geoAreas.xml and labels/<locale>/...). Required for a rebuild.
# PLUGIN_DIR  the game's Plugins folder, where the plugin is installed afterwards.
# Either may be given as an argument or as an environment variable:
#   MQL_LORE=/path/to/lore  MQL_PLUGINS=/path/to/Plugins  ./rebuild.command
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
LORE="${1:-${MQL_LORE:-}}"
PLUGIN_DIR="${2:-${MQL_PLUGINS:-}}"
VENV="$ROOT/.venv"

if [ -z "$LORE" ]; then
	echo "ERROR: no game data given." >&2
	echo "Usage: $0 <LORE_DIR> [PLUGIN_DIR]" >&2
	exit 1
fi
if [ ! -f "$LORE/quests.xml" ] || [ ! -f "$LORE/deeds.xml" ]; then
	echo "ERROR: that source has no quests.xml / deeds.xml." >&2
	echo "Without complete data nothing is replaced." >&2
	exit 1
fi
MOORMAP=""
if [ -n "$PLUGIN_DIR" ] && [ -f "$PLUGIN_DIR/GaranStuff/MoorMap/Defaults.lua" ]; then
	MOORMAP="$PLUGIN_DIR/GaranStuff/MoorMap/Defaults.lua"
else
	echo "NOTE: MoorMap not found. Without its bounds no map positions are produced." >&2
fi

if [ ! -x "$VENV/bin/python" ]; then
	echo "Setting up a Python environment with lupa once ($VENV)..."
	python3 -m venv "$VENV"
	"$VENV/bin/python" -m pip install --quiet --upgrade pip lupa
fi

echo "1/4 build the catalog"
if [ -n "$MOORMAP" ]; then
	python3 "$HERE/build_catalog.py" --lore "$LORE" --moormap "$MOORMAP"
else
	python3 "$HERE/build_catalog.py" --lore "$LORE"
fi

echo "2/4 check the data"
"$VENV/bin/python" "$HERE/verify_catalog.py"

echo "3/4 check the plugin"
"$VENV/bin/python" "$HERE/test_plugin.py"

if [ -z "$PLUGIN_DIR" ]; then
	echo "4/4 skipped: no plugin directory given."
elif [ ! -d "$PLUGIN_DIR" ]; then
	echo "ERROR: $PLUGIN_DIR does not exist." >&2
	exit 1
else
	echo "4/4 install"
	rm -rf "$PLUGIN_DIR/MagicQuestLog"
	cp -R "$ROOT/plugin/MagicQuestLog" "$PLUGIN_DIR/"
	echo
	echo "Done. In game: /plugins unload MagicQuestLog, /plugins load MagicQuestLog, /mql"
	echo "German client: /zusatzmodule entfernen MagicQuestLog, /zusatzmodule laden MagicQuestLog"
fi
