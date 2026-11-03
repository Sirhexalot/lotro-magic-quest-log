"""Compare a newly built catalog with the numbers recorded before MoorMap was taken
out (docs/moormap-ausbau/vorher.json). Prints counts and writes a report.

Usage: vergleich.py <new Data dir>
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

from lupa.lua51 import LuaRuntime

sys.path.insert(0, str(Path(__file__).resolve().parent))
import game_maps  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MOORMAP = Path('/Users/adrian/Documents/The Lord of the Rings Online/Plugins/GaranStuff/MoorMap/Defaults.lua')


def main(new_dir):
    game = game_maps.GameMaps()
    before = json.loads((ROOT / 'docs/moormap-ausbau/vorher.json').read_text())
    names = {}
    for match in re.finditer(r'^\s*tmpMapInfo\[(\d+)\].*--\s*(.*)$', MOORMAP.read_text(errors='replace'), re.M):
        names[int(match.group(1))] = match.group(2).strip()
    report = {}
    for language in ('de', 'en', 'fr'):
        for kind, filename in (('quests', 'Quests_%s.lua'), ('deeds', 'Deeds_%s.lua')):
            lua = LuaRuntime()
            lua.execute((Path(new_dir) / (filename % language)).read_text(encoding='utf-8'))
            records = lua.globals().MagicQuestLog.Data[kind + '_' + language]
            old = before['per'][language + kind]
            counts, lost, changed, no_button = Counter(), Counter(), Counter(), Counter()
            for index in range(1, len(records) + 1):
                record = records[index]
                targets = record['t']
                first = targets[1] if targets is not None and len(targets) > 0 else None
                was = old.get(record['id'], {})
                for field, now in (('t', first), ('g', record['gt'])):
                    previous = was.get(field)
                    if now is None:
                        if previous is not None:
                            counts[field + '_lost'] += 1
                            lost[names.get(previous, previous)] += 1
                        continue
                    counts[field + '_now'] += 1
                    if now['map'] is None:
                        counts[field + '_no_moormap_number'] += 1
                        no_button[game.maps[now['gm']]['name']] += 1
                    if previous is None:
                        counts[field + '_new'] += 1
                    elif now['map'] == previous:
                        counts[field + '_same_map'] += 1
                    else:
                        counts[field + '_other_map'] += 1
                        changed['%s -> %s' % (names.get(previous, previous), game.maps[now['gm']]['name'])] += 1
                    if previous is not None:
                        counts[field + '_before'] += 1
            for field in ('t', 'g'):
                had = sum(1 for value in old.values() if value.get(field) is not None)
                counts[field + '_had_before'] = had
            report[language + '_' + kind] = {'counts': dict(counts), 'lost': lost.most_common(),
                                             'changed': changed.most_common(), 'no_button': no_button.most_common()}
            print(language, kind, dict(counts))
            if language == 'de':
                print('  lost (old map):', lost.most_common(10))
                print('  changed:', changed.most_common(12))
                print('  no MoorMap number:', no_button.most_common(8))
    (ROOT / 'docs/moormap-ausbau/vergleich.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
