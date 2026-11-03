#!/bin/bash
# Build the catalog into a scratch directory and compare it with the numbers from
# before MoorMap was taken out. Writes nothing into the plugin.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
EXP="$ROOT/../Companion-Test/source-exporter"
OUT="${1:-${TMPDIR:-/tmp}/mql-katalog-neu}"
LORE="/Users/adrian/Applications/LOTRO-Companion-Test/LotRO Companion/app/data/lore"
rm -rf "$OUT"; mkdir -p "$OUT"
python3 "$HERE/build_catalog_from_export.py" --export "$EXP/full-dat-en-de-fr-2026-11-03" \
	--enums "$EXP/enums/enum-names.json" --output "$OUT" --lore "$LORE" \
	--moormap "/Users/adrian/Documents/The Lord of the Rings Online/Plugins/GaranStuff/MoorMap/Defaults.lua" \
	--landblocks "$LORE/landblocks.xml" --npcs "$EXP/npcs-2026-11-03" \
	--did-positions "$EXP/did-positions-2026-11-03/positions.jsonl" > "$OUT/build.log" 2>&1
"$ROOT/.venv/bin/python" "$HERE/vergleich_moormap.py" "$OUT"
