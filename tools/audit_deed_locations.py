#!/usr/bin/env python3
"""Read-only, reproducible deed location audit; no foreign coordinates required.

Usage: python audit_deed_locations.py EXPORT_DIR WEB_DATEN_TATEN_EN_JS
Prints a JSON report to stdout. Cell zero is not proof of a landscape location.
"""
import collections
import json
import sys
from pathlib import Path

from game_maps import GameMaps
from build_catalog_from_export import walk_events


def audit(export, web_data):
    game = GameMaps()
    text = Path(web_data).read_text(encoding='utf-8')
    records = json.JSONDecoder().raw_decode(text.split('window.MQL_QUESTS = ', 1)[1])[0]
    records = {row['i']: row for row in records}
    deeds = {row['id']: row for row in json.loads((Path(export) / 'deeds.json').read_text())}
    missing = {ident for ident, row in records.items() if not row['t']}
    counts, per_deed = collections.Counter(), collections.defaultdict(collections.Counter)
    for row in json.loads((Path(export) / 'locations.json').read_text()):
        if row['id'] not in missing:
            continue
        p = row['position']
        # attribute takes LATITUDE first. Do not reverse these axes.
        map_id = game.attribute(p['latitude'], p['longitude'], p['region'])
        kind = ('cell-zero' if p['cell'] == '00000000' else 'interior-cell') + (
            '-mapped' if map_id is not None else '-unmapped')
        counts[kind] += 1
        per_deed[row['id']][kind] += 1
    landmarks = []
    for ident in sorted(missing):
        events = []
        walk_events(deeds[ident].get('objectives') or [], events.append)
        refs = sorted({e['QuestEvent_LandmarkDID'] for e in events if e.get('QuestEvent_LandmarkDID')})
        if refs:
            landmarks.append({'id': ident, 'name': records[ident]['n'],
                              'landmarks': ['%08X' % (v & 0xffffffff) for v in refs],
                              'raw_rows': dict(per_deed.get(ident, {}))})
    return {'deeds': len(records), 'exact_positioned': sum(bool(r['t']) for r in records.values()),
            'exact_rows': sum(len(r['t']) for r in records.values()),
            'hunting_deeds': sum(bool(r.get('h')) for r in records.values()),
            'hunting_only_deeds': sum(bool(r.get('h')) and not r['t'] for r in records.values()),
            'hunting_rows': sum(len(r.get('h', [])) for r in records.values()),
            'missing_exact_with_raw': len(per_deed), 'missing_exact_raw_rows': dict(counts),
            'remaining_landmark_deeds': landmarks}


if __name__ == '__main__':
    print(json.dumps(audit(*sys.argv[1:]), ensure_ascii=False, indent=2))
