#!/bin/bash
# Magic Quest Log: rebuild the catalog from our own DAT export ("Weg B").
# Reads game data only; it never writes to the game files. Double-clickable in Finder.
#
# The XML way (LOTRO Companion lore directory) lives in rebuild.command. This one
# needs no Companion application: only the export folder, the enum dump and
# MoorMap's bounds. landblocks.xml is optional and only used for the territory
# fallback when a quest has no map reference of its own.
#
# Usage:  rebuild-from-export.command [EXPORT_DIR] [PLUGIN_DIR] [LANDBLOCKS_XML]
#
# EXPORT_DIR     output of Companion-Test/source-exporter (quests.json, deeds.json,
#                areas.json, locations.json, manifest.json). Default: the newest
#                full-dat-* folder below ../../Companion-Test/source-exporter.
# PLUGIN_DIR     the game's Plugins folder, where the plugin is installed afterwards.
# LANDBLOCKS_XML Companion's app/data/lore/landblocks.xml. Default: looked up in the
#                usual Companion install locations.
# Either may be given as an argument or as an environment variable:
#   MQL_EXPORT=/path/to/export  MQL_PLUGINS=/path/to/Plugins  \
#   MQL_LANDBLOCKS=/path/to/landblocks.xml  ./rebuild-from-export.command
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
WORKSPACE="$(cd "$ROOT/.." && pwd)"
EXPORT="${1:-${MQL_EXPORT:-}}"
PLUGIN_DIR="${2:-${MQL_PLUGINS:-}}"
LANDBLOCKS="${3:-${MQL_LANDBLOCKS:-}}"
ENUMS="$WORKSPACE/Companion-Test/source-exporter/enums/enum-names.json"
VENV="$ROOT/.venv"

if [ -z "$EXPORT" ]; then
	EXPORT="$(ls -d "$WORKSPACE"/Companion-Test/source-exporter/full-dat-* 2>/dev/null | sort | tail -1 || true)"
fi
if [ -z "$EXPORT" ]; then
	echo "ERROR: no export folder given and none found under Companion-Test/source-exporter." >&2
	echo "Usage: $0 <EXPORT_DIR> [PLUGIN_DIR] [LANDBLOCKS_XML]" >&2
	exit 1
fi
if [ ! -f "$EXPORT/quests.json" ] || [ ! -f "$EXPORT/deeds.json" ] || [ ! -f "$EXPORT/locations.json" ]; then
	echo "ERROR: $EXPORT is not a complete export (quests.json / deeds.json / locations.json)." >&2
	echo "Without complete data nothing is replaced." >&2
	exit 1
fi
if [ ! -f "$ENUMS" ]; then
	echo "ERROR: category enums missing: $ENUMS" >&2
	exit 1
fi
MOORMAP=""
if [ -n "$PLUGIN_DIR" ] && [ -f "$PLUGIN_DIR/GaranStuff/MoorMap/Defaults.lua" ]; then
	MOORMAP="$PLUGIN_DIR/GaranStuff/MoorMap/Defaults.lua"
else
	echo "NOTE: MoorMap not found. Without its bounds no map positions are produced." >&2
fi
if [ -z "$LANDBLOCKS" ]; then
	for candidate in \
		"$HOME/Applications/LOTRO-Companion-Test/LotRO Companion/app/data/lore/landblocks.xml" \
		"$HOME/Applications/LOTRO Companion.app/Contents/Resources/app/data/lore/landblocks.xml" \
		"/Applications/LOTRO Companion.app/Contents/Resources/app/data/lore/landblocks.xml" \
		"$HOME/Applications/"*/"LotRO Companion"/app/data/lore/landblocks.xml
	do
		if [ -f "$candidate" ]; then LANDBLOCKS="$candidate"; break; fi
	done
fi
if [ -z "$LANDBLOCKS" ]; then
	echo "NOTE: landblocks.xml not found. Quests without their own map reference keep no area." >&2
fi

if [ ! -x "$VENV/bin/python" ]; then
	echo "Setting up a Python environment with lupa once ($VENV)..."
	python3 -m venv "$VENV"
	"$VENV/bin/python" -m pip install --quiet --upgrade pip lupa
fi

ARGS=(--export "$EXPORT" --enums "$ENUMS" --output "$ROOT/plugin/MagicQuestLog/Data")
[ -n "$MOORMAP" ] && ARGS+=(--moormap "$MOORMAP")
[ -n "$LANDBLOCKS" ] && ARGS+=(--landblocks "$LANDBLOCKS")

echo "source:     $EXPORT"
echo "enums:      $ENUMS"
echo "moormap:    ${MOORMAP:-none}"
echo "landblocks: ${LANDBLOCKS:-none}"

echo "1/4 build the catalog"
python3 "$HERE/build_catalog_from_export.py" "${ARGS[@]}"

echo "2/4 check the data"
"$VENV/bin/python" "$HERE/verify_catalog.py"

echo "3/4 check the plugin"
"$VENV/bin/python" "$HERE/test_plugin.py"

echo "counts (from manifest.json):"
python3 - "$ROOT/plugin/MagicQuestLog/Data/manifest.json" <<'PY'
import json, sys
m = json.load(open(sys.argv[1], encoding='utf-8'))
for locale, data in m['locales'].items():
    c = data['counts']
    print('  %s: %d Aufgaben, %d Taten, %d mit Position, %d Gebiet aus Position, %d ausgeblendet'
          % (locale, c['quests'], c['deeds'], c['quests_with_targets'],
             c['quests_zone_from_position'], c['quests_hidden']))
PY

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
