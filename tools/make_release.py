"""Build the release archive: the plugin with its generated catalog.

The catalog is ~102 MB and therefore not in the repository, so a release archive
is how it reaches other players. The archive is install-ready: unpack it into the
game's Plugins folder.

A character's own progress file is never included; a documented example is.
The version comes from MagicQuestLog.plugin, so it cannot drift from the plugin.

Run:  python3 MagicQuestLog/tools/make_release.py
"""
from pathlib import Path
import hashlib
import json
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugin/MagicQuestLog'
DATA = PLUGIN / 'Data'
DIST = ROOT / 'dist'
CATALOGS = ('Quests_en.lua', 'Quests_de.lua', 'Quests_fr.lua',
            'Deeds_en.lua', 'Deeds_de.lua', 'Deeds_fr.lua')
PRIVATE = ('Progress.lua',)
TOOLS = ROOT / 'tools/journal-reader'
TOOL_FOLDER = Path('MagicQuestLog/Optional-Progress-Tool')


def version():
    text = (PLUGIN / 'MagicQuestLog.plugin').read_text(encoding='utf-8')
    match = re.search(r'<Version>([^<]+)</Version>', text)
    assert match, 'no version in MagicQuestLog.plugin'
    return match.group(1).strip()


def main():
    if not (TOOLS / 'JournalExport.java').is_file():
        raise SystemExit('missing the optional progress tool: ' + str(TOOLS))
    missing = [name for name in CATALOGS if not (DATA / name).is_file()]
    if missing:
        print('Missing catalog files: ' + ', '.join(missing))
        print('Build them first:  tools/rebuild.command <LORE_DIR>')
        return 1
    stamp = version()
    DIST.mkdir(exist_ok=True)
    target = DIST / ('MagicQuestLog-%s.zip' % stamp)
    if target.exists():
        raise SystemExit('refusing to overwrite ' + str(target))
    count, skipped = 0, []
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(PLUGIN.rglob('*')):
            if not path.is_file():
                continue
            relative = path.relative_to(PLUGIN)
            # A character's own progress stays private; the example ships instead.
            if relative.name in PRIVATE:
                skipped.append(str(relative))
                continue
            if relative.name.endswith(('.pyc',)):
                continue
            archive.write(path, arcname=str(Path('MagicQuestLog') / relative))
            count += 1
        archive.write(ROOT / 'README.md', arcname='MagicQuestLog/README.md')
        archive.write(ROOT / 'LICENSE', arcname='MagicQuestLog/LICENSE.txt')
        archive.write(ROOT / 'icon-sources/NOTICE', arcname='MagicQuestLog/icons-NOTICE.txt')
        # The optional progress tool ships inside the plugin folder, so a player finds
        # it without visiting the repository. It needs a local LOTRO Companion
        # installation; the download page and START-HERE.txt say so.
        for path in sorted(TOOLS.rglob('*')):
            if not path.is_file() or path.name.endswith('.pyc'):
                continue
            relative = path.relative_to(TOOLS)
            archive.write(path, arcname=str(TOOL_FOLDER / relative))
            count += 1
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    print('%s  %d files  %.1f MiB'
          % (target, count + 2, target.stat().st_size / 1024 / 1024))
    if skipped:
        print('left out on purpose: ' + ', '.join(skipped))
    print('sha256 ' + digest)
    (DIST / 'release.json').write_text(
        json.dumps({'version': stamp, 'archive': target.name, 'files': count + 2,
                    'bytes': target.stat().st_size, 'sha256': digest,
                    'left_out': skipped}, indent=2) + '\n',
        encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
