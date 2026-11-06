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
SECTIONS = {'@more', '@story', '@shadow', '@missions', '@instances', '@craft', '@festivals', '@other'}
HEX = re.compile(r'^[0-9A-F]{8}$')


def load(locale, kind, runtime):
    readable = kind.lower()
    path = DATA / ('%s_%s.lua' % (kind, locale))
    assert path.is_file(), 'missing ' + path.name
    runtime.execute(path.read_text(encoding='utf-8'))
    return runtime.globals().MagicQuestLog.Data[readable + '_' + locale]


def load_details(locale, runtime):
    """All detail blocks of one language: description, steps, every objective."""
    blocks = {}
    for path in sorted(DATA.glob('QuestDetails_%s_*.lua' % locale)):
        runtime.execute(path.read_text(encoding='utf-8'))
        number = path.stem.rsplit('_', 1)[1]
        blocks[int(number)] = runtime.globals().MagicQuestLog.Data['questDetails_' + locale + '_' + number]
    assert blocks, 'no detail blocks for ' + locale
    return blocks


def check(locale, kind, records, details=None):
    assert records is not None, '%s %s missing' % (locale, kind)
    details = details or {}
    ids, structure = set(), {}
    marks = {}
    zones, areas = set(), set()
    for record in records.values():
        assert HEX.match(record.id), '%s: bad id %r' % (locale, record.id)
        assert record.name and record.name.strip(), '%s %s: empty name' % (locale, record.id)
        # Developer placeholders ("DNT", "HIDING CONTENT") stay hidden in every language.
        assert not re.search(r'\bDNT\b', record.name) and 'HIDING CONTENT' not in record.name.upper(), \
            'developer placeholder visible: %s %s' % (record.id, record.name)
        assert record.id not in ids, 'duplicate id ' + record.id
        ids.add(record.id)
        assert len(record.p) > 0, '%s %s: empty path' % (locale, record.id)
        for part in record.p.values():
            assert part.k and part.n, '%s %s: incomplete path part' % (locale, record.id)
            if part.n.startswith('@'):
                assert part.n in SECTIONS or part.n.startswith('@volume:'), \
                    '%s %s: unknown section %s' % (locale, record.id, part.n)
        structure[record.id] = '|'.join(part.k for part in record.p.values())
        # x = session play, ex = quests that rule this one out. Both are facts from
        # the game data and must read the same in every language.
        assert record.x is None or record.x == 1, '%s %s: bad session flag %r' % (locale, record.id, record.x)
        partners = tuple(sorted(record.ex.values())) if record.ex is not None else ()
        # Description, steps and all objectives come from the entry's detail block.
        full = record
        if kind == 'Quests':
            assert record.blk is not None, '%s %s: no detail block' % (locale, record.id)
            block = details.get(record.blk)
            assert block is not None, '%s %s: detail block %s missing' % (locale, record.id, record.blk)
            full = block[record.id]
            assert full is not None, '%s %s: not in its detail block' % (locale, record.id)
            shown = sum(1 for _ in full.s.values()) if full.s is not None else 0
            assert (record.sc or 0) == shown, '%s %s: step count differs from its block' % (locale, record.id)
        # Goal numbering ("k") is what a character's running counter is matched by,
        # so every language must carry the same goals with the same numbers.
        # Materialised once: the Lua iterator is one-shot.
        steps = list(full.s.values()) if full.s is not None else []
        goals = tuple((step.i, tuple(goal.k for goal in step.g.values())) for step in steps
                      if len(step.g) > 0)
        # Rewards come from the game's reward table. Names are localized, so the
        # cross-language comparison uses kind, quality, level, count and binding;
        # their number and order must match in every language.
        rewards = list(full.rw.values()) if full.rw is not None else []
        rewards_mark = []
        for entry in rewards:
            kind = entry[1]
            assert kind in ('i', 'c', 't', 'v', 'tr', 'e'), \
                '%s %s: unknown reward kind %r' % (locale, record.id, kind)
            name = entry[2] or ''
            assert name.strip(), '%s %s: reward without name' % (locale, record.id)
            assert '${' not in name and 'RANK NAME SURNAME' not in name, \
                '%s %s: raw placeholder in reward %r' % (locale, record.id, name)
            assert not re.search(r'\[[A-Za-z]{1,4}\]', name), \
                '%s %s: game tag left in reward %r' % (locale, record.id, name)
            assert 'DNT' not in name and 'HIDING CONTENT' not in name.upper(), \
                '%s %s: developer reward visible %r' % (locale, record.id, name)
            if kind in ('i', 'c'):
                quality, level = int(entry[3] or 0), int(entry[4] or 0)
                count = int(entry[5] or 1) if kind == 'i' else 1
                bound = int(entry[6] or 0) if kind == 'i' else int(entry[5] or 0)
                ident = entry[7] if kind == 'i' else entry[6]
                assert isinstance(ident, str) and HEX.match(ident), \
                    '%s %s: reward item without a source id' % (locale, record.id)
                assert 0 <= quality <= 6, '%s %s: bad quality' % (locale, record.id)
                assert 0 <= level <= 1000, '%s %s: bad item level' % (locale, record.id)
                assert 1 <= count <= 10000, '%s %s: bad count' % (locale, record.id)
                rewards_mark.append((kind, quality, level, count, bound, ident))
            else:
                rewards_mark.append((kind, 0, 0, 1, 0, ''))
        marks[record.id] = (record.x or 0, partners, goals, tuple(rewards_mark))
        for part in record.p.values():
            if part.k.startswith('zone:'):
                zones.add(part.k[len('zone:'):])
            elif part.k.startswith('area:'):
                areas.add(part.k.rsplit(':', 1)[1])
        indexes = set()
        for step in steps:
            assert step.i != '', '%s %s: step without index' % (locale, record.id)
            indexes.add(step.i)
            for goal in step.g.values():
                assert goal.t and goal.t.strip(), '%s %s: empty goal' % (locale, record.id)
                if goal.c is not None:
                    assert 0 < goal.c <= 100000, '%s %s: implausible count' % (locale, record.id)
        for target in (list(full.t.values()) if full.t is not None else []):
            assert isinstance(target.map, int) and target.map > 0, '%s %s: bad map' % (locale, record.id)
            assert -180 <= target.lat <= 180 and -360 <= target.lon <= 360, \
                '%s %s: bad position' % (locale, record.id)
            assert target.step in indexes, '%s %s: target for unshown step' % (locale, record.id)
    # A name may be a zone or a sub-area, never both: "Agarnaith" appeared as a zone
    # and as the area "Mordor: Agarnaith" at the same time, which looked like a
    # duplicate territory in the tree.
    shared = sorted(areas & zones)
    assert not shared, '%s %s: name used as zone and as area: %s' % (locale, kind, ', '.join(shared))
    # A partner that is not in the catalog would be a dangling promise, and a
    # one-sided entry would silently take an entry out of the count for nobody.
    for ident, (_, partners, _goals, _rewards) in marks.items():
        for partner in partners:
            assert partner in ids, '%s %s: %s points at unknown %s' % (locale, kind, ident, partner)
            assert ident in marks[partner][1], '%s %s: %s and %s are not mutual' % (locale, kind, ident, partner)
    return ids, structure, marks


def main():
    manifest = json.loads((DATA / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['schema'] >= 1
    assert set(manifest['locales']) == set(LOCALES)
    ids, structures, counts, marks = {}, {}, {}, {}
    for locale in LOCALES:
        runtime = LuaRuntime()
        blocks = load_details(locale, runtime)
        for kind in ('Quests', 'Deeds'):
            records = load(locale, kind, runtime)
            counts.setdefault(kind, {})[locale] = len(records)
            ids[(kind, locale)], structures[(kind, locale)], marks[(kind, locale)] = check(
                locale, kind, records, blocks if kind == 'Quests' else None)
            if kind == 'Quests':
                # Every detail entry belongs to a record of the core: no orphans,
                # which would mean a block and the core disagree.
                core_ids = {record.id for record in records.values()}
                for number, block in blocks.items():
                    for ident in block.keys():
                        assert ident in core_ids, '%s: detail %s has no entry in the core' % (locale, ident)
        del runtime
    for kind in ('Quests', 'Deeds'):
        reference = ids[(kind, 'en')]
        reference_structure = structures[(kind, 'en')]
        reference_marks = marks[(kind, 'en')]
        for locale in LOCALES[1:]:
            assert ids[(kind, locale)] == reference, '%s %s: id set differs from English' % (kind, locale)
            assert structures[(kind, locale)] == reference_structure, \
                '%s %s: path structure differs from English' % (kind, locale)
            assert marks[(kind, locale)] == reference_marks, \
                '%s %s: session, exclusion or goal numbering differs from English' % (kind, locale)
    for kind, key in (('Quests', 'quests'), ('Deeds', 'deeds')):
        for locale in LOCALES:
            assert counts[kind][locale] == manifest['locales'][locale]['counts'][key], \
                '%s %s: count differs from manifest' % (kind, locale)
    print('PASS: structure, ids and counts for ' + ', '.join(LOCALES))
    print('PASS: identical path structure and id sets across all languages')
    for kind in ('Quests', 'Deeds'):
        english = marks[(kind, 'en')]
        print('PASS: %s flags read the same in all languages (%d session plays, %d entries with an alternative)'
              % (kind.lower(), sum(1 for value in english.values() if value[0]),
                 sum(1 for value in english.values() if value[1])))
    print(json.dumps(counts, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
