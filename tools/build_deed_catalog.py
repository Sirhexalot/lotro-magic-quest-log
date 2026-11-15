#!/usr/bin/env python3
"""Shared deed catalog generator for the plugin and the website.

Reads our own DAT export and writes the Deeds_*.lua files (plus the manifest)
into the given output directory. The quests are processed as well because a
deed's "where its quests happen" hints come from them, but only the deed files
are written. The plugin and the website both call this one entry point, so the
deed mapping, the duplicate replacements and the filters cannot drift apart.

    python3 tools/build_deed_catalog.py --output ~/.cache/llb-php/deed-catalog
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
from build_catalog_from_export import build  # noqa: E402

HAUS = Path.home()
EXPORT = (HAUS / 'Documents/07_Hobbys/Lotro/Companion-Test/source-exporter'
          / 'full-dat-en-de-fr-2026-11-03')
LORE = HAUS / 'Applications/LOTRO-Companion-Test/LotRO Companion/app/data/lore'
MOORMAP = HAUS / 'Documents/The Lord of the Rings Online/Plugins/GaranStuff/MoorMap/Defaults.lua'


def neueste_rewards(export: Path) -> Path | None:
    kandidaten = sorted(export.parent.glob('rewards-*/rewards.json'))
    return kandidaten[-1] if kandidaten else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--export', type=Path, default=EXPORT)
    parser.add_argument('--enums', type=Path, default=None)
    parser.add_argument('--lore', type=Path, default=LORE)
    parser.add_argument('--moormap', type=Path, default=MOORMAP)
    parser.add_argument('--landblocks', type=Path, default=None)
    parser.add_argument('--npcs', type=Path, default=None)
    parser.add_argument('--did-positions', type=Path, default=None)
    parser.add_argument('--placed-entities', type=Path, default=None)
    parser.add_argument('--rewards', type=Path, default=None)
    parser.add_argument('--overrides', type=Path, default=HIER / 'overrides.json')
    args = parser.parse_args()

    export = args.export
    if not export.is_dir():
        raise SystemExit('export missing: %s' % export)
    enums = args.enums or export.parent / 'enums/enum-names.json'
    landblocks = args.landblocks or (args.lore / 'landblocks.xml')
    npcs = args.npcs or export.parent / 'npcs-2026-11-03'
    did = args.did_positions or export.parent / 'did-positions-2026-11-03/positions.jsonl'
    placed = args.placed_entities or export.parent / 'placed-2026-11-03/raw.jsonl'
    rewards = args.rewards or neueste_rewards(export)

    overrides = json.loads(args.overrides.read_text(encoding='utf-8')) if args.overrides.is_file() else {}
    args.output.mkdir(parents=True, exist_ok=True)
    report = build(
        export, enums, args.output,
        args.moormap if args.moormap and args.moormap.is_file() else None,
        overrides,
        landblocks if landblocks.is_file() else None,
        npcs if npcs.is_dir() else None,
        did if did.is_file() else None,
        args.lore if args.lore.is_dir() else None,
        placed if placed.is_file() else None,
        rewards if rewards and rewards.is_file() else None,
        only='deeds',
    )
    written = sorted(p.name for p in args.output.glob('Deeds_*.lua'))
    print('deeds: %s' % ', '.join(written))
    for locale, data in report['locales'].items():
        print('  %s: %d deeds' % (locale, data['counts']['deeds']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
