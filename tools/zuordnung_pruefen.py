"""How often does a quest's map (or one of its parents) carry the name of the area the
game files the quest under? An independent check of map attribution: old (MoorMap)
against new (game maps). Only quests whose area has a map of that name count.

Usage: zuordnung_pruefen.py <old Data dir> <new Data dir>
"""
import re
import sys
from collections import Counter
from pathlib import Path

from lupa.lua51 import LuaRuntime

sys.path.insert(0, str(Path(__file__).resolve().parent))
import game_maps  # noqa: E402

MOORMAP = Path('/Users/adrian/Documents/The Lord of the Rings Online/Plugins/GaranStuff/MoorMap/Defaults.lua')


def norm(name):
    name = (name or '').lower().replace('\xa0', ' ')
    name = re.sub(r'^(east|west) rohan: ', '', name)
    name = re.sub(r'^the ', '', name)
    return re.sub(r'[^a-z0-9]', '', name)


def load(directory):
    lua = LuaRuntime()
    lua.execute((Path(directory) / 'Quests_en.lua').read_text(encoding='utf-8'))
    return lua.globals().MagicQuestLog.Data.quests_en


def main(old_dir, new_dir):
    game = game_maps.GameMaps()
    image_of_moormap = {number: image for image, number in game_maps.moormap_index(MOORMAP).items()}
    game_of_image = {entry['image']: ident for ident, entry in game.maps.items()}
    map_names = {norm(entry['name']) for entry in game.maps.values()}

    def chain_names(ident):
        return {norm(game.maps[i]['name']) for i in game.chain(ident)} if ident in game.maps else set()

    def zone_of(record):
        for part in (record['p'] or {}).values():
            key = part['k']
            if key.startswith('zone:') or key.startswith('area:'):
                if norm(key.split(':', 1)[1]) in map_names:
                    return norm(key.split(':', 1)[1])
        return None

    result = {}
    for label, directory, new in (('old (MoorMap)', old_dir, False), ('new (game maps)', new_dir, True)):
        records = load(directory)
        counts = Counter()
        for index in range(1, len(records) + 1):
            record = records[index]
            zone = zone_of(record)
            targets = record['t']
            if zone is None or targets is None or len(targets) == 0:
                continue
            for field, place in (('target', targets[1]), ('giver', record['gt'])):
                if place is None:
                    continue
                if new:
                    ident = place['gm']
                else:
                    ident = game_of_image.get(image_of_moormap.get(place['map']))
                counts[field] += 1
                if zone in chain_names(ident):
                    counts[field + '_agrees'] += 1
        result[label] = counts
        print(label, {k: v for k, v in counts.items()},
              'targets %.1f %%' % (100 * counts['target_agrees'] / max(1, counts['target'])),
              'givers %.1f %%' % (100 * counts['giver_agrees'] / max(1, counts['giver'])))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
