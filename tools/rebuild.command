#!/bin/bash
# Magic Quest Log: rebuild the catalog, check it, install it.
# Reads game data only; it never writes to the game files. Double-clickable in Finder.
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
	echo "FEHLER: Keine Spieldaten angegeben." >&2
	echo "Aufruf: $0 <LORE_DIR> [PLUGIN_DIR]" >&2
	exit 1
fi
if [ ! -f "$LORE/quests.xml" ] || [ ! -f "$LORE/deeds.xml" ]; then
	echo "FEHLER: In dieser Quelle fehlen quests.xml / deeds.xml." >&2
	echo "Ohne vollstaendige Daten wird nichts ersetzt." >&2
	exit 1
fi
MOORMAP=""
if [ -n "$PLUGIN_DIR" ] && [ -f "$PLUGIN_DIR/GaranStuff/MoorMap/Defaults.lua" ]; then
	MOORMAP="$PLUGIN_DIR/GaranStuff/MoorMap/Defaults.lua"
else
	echo "HINWEIS: MoorMap nicht gefunden. Ohne seine Grenzen entstehen keine Kartenpositionen." >&2
fi

if [ ! -x "$VENV/bin/python" ]; then
	echo "Richte einmalig eine Python-Umgebung mit lupa ein ($VENV)..."
	python3 -m venv "$VENV"
	"$VENV/bin/python" -m pip install --quiet --upgrade pip lupa
fi

echo "1/4 Katalog erzeugen"
if [ -n "$MOORMAP" ]; then
	python3 "$HERE/build_catalog.py" --lore "$LORE" --moormap "$MOORMAP"
else
	python3 "$HERE/build_catalog.py" --lore "$LORE"
fi

echo "2/4 Daten pruefen"
"$VENV/bin/python" "$HERE/verify_catalog.py"

echo "3/4 Plugin pruefen"
"$VENV/bin/python" "$HERE/test_plugin.py"

if [ -z "$PLUGIN_DIR" ]; then
	echo "4/4 Uebersprungen: kein Plugin-Verzeichnis angegeben."
elif [ ! -d "$PLUGIN_DIR" ]; then
	echo "FEHLER: $PLUGIN_DIR gibt es nicht." >&2
	exit 1
else
	echo "4/4 Installieren"
	rm -rf "$PLUGIN_DIR/MagicQuestLog"
	cp -R "$ROOT/plugin/MagicQuestLog" "$PLUGIN_DIR/"
	echo
	echo "Fertig. Im Spiel: /plugins unload MagicQuestLog, /plugins load MagicQuestLog, /mql"
fi
