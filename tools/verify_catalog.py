"""Data checks for a generated catalog. Run after every rebuild.

Verifies facts about the generated files only; it makes no claim about game
behaviour. Structure and id sets must be identical across the three languages,
so a language can never silently lose entries.
"""
from pathlib import Path
import json
import re
import sys
from lupa.lua51 import LuaRuntime

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / 'plugin/MagicQuestLog/Data'
LOCALES = ('en', 'de', 'fr')
SECTIONS = {'@story', '@shadow', '@missions', '@instances', '@craft', '@festivals', '@other'}
HEX = re.compile(r'^[0-9A-F]{8}$')


def load(locale, kind, runtime):
    readable = kind.lower()
    path = DATA / ('%s_%s.lua' % (kind, locale))
    assert path.is_file(), 'missing ' + path.name
    runtime.execute(path.read_text(encoding='utf-8'))
    return runtime.globals().MagicQuestLog.Data[readable + '_' + locale]


def check(locale, kind, records):
    assert records is not None, '%s %s missing' % (locale, kind)
    ids, structure = set(), {}
    for record in records.values():
        assert HEX.match(record.id), '%s: bad id %r' % (locale, record.id)
        assert record.name and record.name.strip(), '%s %s: empty name' % (locale, record.id)
        assert record.id not in ids, 'duplicate id ' + record.id
        ids.add(record.id)
        assert len(record.p) > 0, '%s %s: empty path' % (locale, record.id)
        for part in record.p.values():
            assert part.k and part.n, '%s %s: incomplete path part' % (locale, record.id)
            if part.n.startswith('@'):
                assert part.n in SECTIONS or part.n.startswith('@volume:'), \
                    '%s %s: unknown section %s' % (locale, record.id, part.n)
        structure[record.id] = '|'.join(part.k for part in record.p.values())
        indexes = set()
        for step in record.s.values():
            assert step.i != '', '%s %s: step without index' % (locale, record.id)
            indexes.add(step.i)
            for goal in step.g.values():
                assert goal.t and goal.t.strip(), '%s %s: empty goal' % (locale, record.id)
                if goal.c is not None:
                    assert 0 < goal.c <= 100000, '%s %s: implausible count' % (locale, record.id)
        for target in record.t.values():
            assert isinstance(target.map, int) and target.map > 0, '%s %s: bad map' % (locale, record.id)
            assert -180 <= target.lat <= 180 and -360 <= target.lon <= 360, \
                '%s %s: bad position' % (locale, record.id)
            assert target.step in indexes, '%s %s: target for unshown step' % (locale, record.id)
    return ids, structure


def main():
    manifest = json.loads((DATA / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['schema'] >= 1
    assert set(manifest['locales']) == set(LOCALES)
    ids, structures, counts = {}, {}, {}
    for locale in LOCALES:
        runtime = LuaRuntime()
        for kind in ('Quests', 'Deeds'):
            records = load(locale, kind, runtime)
            counts.setdefault(kind, {})[locale] = len(records)
            ids[(kind, locale)], structures[(kind, locale)] = check(locale, kind, records)
        del runtime
    for kind in ('Quests', 'Deeds'):
        reference = ids[(kind, 'en')]
        reference_structure = structures[(kind, 'en')]
        for locale in LOCALES[1:]:
            assert ids[(kind, locale)] == reference, '%s %s: id set differs from English' % (kind, locale)
            assert structures[(kind, locale)] == reference_structure, \
                '%s %s: path structure differs from English' % (kind, locale)
    for kind, key in (('Quests', 'quests'), ('Deeds', 'deeds')):
        for locale in LOCALES:
            assert counts[kind][locale] == manifest['locales'][locale]['counts'][key], \
                '%s %s: count differs from manifest' % (kind, locale)
    print('PASS: structure, ids and counts for ' + ', '.join(LOCALES))
    print('PASS: identical path structure and id sets across all languages')
    print(json.dumps(counts, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
