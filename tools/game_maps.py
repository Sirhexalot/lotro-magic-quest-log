"""Maps from the game data: list, bounds, hierarchy and which map a position is on.

Sources, all from the game (LOTRO Companion's lore data, used with Damien's
permission):

- ``parchmentMaps.xml``: the game's world maps ("parchment maps") with their region
  and parent map. This is the list and the hierarchy (Eriador > Bree-land > Bree).
  Dungeon and interior maps are not in it.
- ``maps/maps/maps.xml``: image id, scale factor and geographic bounds per map.
- ``maps/links.xml``: links between maps with the pixel spot of the link on the
  parent's image. The overview maps (Eriador, Rhovanion …) have only their image
  size as bounds; the links to their places are at known pixels and those places'
  bounds are known, so a straight-line fit turns pixels into longitude and
  latitude. Overviews whose links do not fit a straight line get no bounds and
  show no dots.
- ``maps/labels/<language>/basemaps.xml``: map names per language.

MoorMap (Garan's plugin) is used for one thing only: ``moormap_index()`` translates
a game map into MoorMap's map number through the shared image id, so the plugin's
"Show in MoorMap" button can open the right map. No bounds, regions or parents are
taken from MoorMap.
"""
import html
import re
from collections import defaultdict
from pathlib import Path

DEFAULT_LORE = Path('/Users/adrian/Applications/LOTRO-Companion-Test/LotRO Companion/app/data/lore')
WIDTH, HEIGHT = 1024.0, 768.0
# Overview fit: largest mean distance (pixels) between a link and where the fitted
# bounds put its place. Above it the overview gets no bounds and shows no dots.
FIT_LIMIT = 40.0
ROOT = 268437554  # Middle-earth


class GameMaps:
    def __init__(self, lore_dir=DEFAULT_LORE):
        self.lore = Path(lore_dir)
        geometry = {}
        text = (self.lore / 'maps' / 'maps' / 'maps.xml').read_text(encoding='utf-8')
        for block in re.finditer(r'<map id="(\d+)" name="([^"]*)" imageId="(\d+)">(.*?)</map>', text, re.S):
            body = block.group(4)
            factor = re.search(r'<geo factor="([^"]+)"', body)
            low = re.search(r'<min longitude="([^"]+)" latitude="([^"]+)"', body)
            high = re.search(r'<max longitude="([^"]+)" latitude="([^"]+)"', body)
            if factor and low and high:
                geometry[int(block.group(1))] = {
                    'image': int(block.group(3)), 'factor': float(factor.group(1)),
                    'west': float(low.group(1)), 'south': float(low.group(2)),
                    'east': float(high.group(1)), 'north': float(high.group(2))}
        self.maps = {}
        parchment = (self.lore / 'parchmentMaps.xml').read_text(encoding='utf-8')
        for match in re.finditer(r'<parchmentMap ([^>]*?)/?>', parchment):
            attributes = dict(re.findall(r'(\w+)="([^"]*)"', match.group(1)))
            ident = int(attributes['id'])
            if ident not in geometry:
                continue
            entry = dict(geometry[ident], id=ident, name=html.unescape(attributes.get('name', '')),
                         region=int(attributes.get('region', 0)),
                         parent=int(attributes['parentMapId']) if attributes.get('parentMapId') else None)
            # Overviews: factor 1 and bounds that are only the image in pixels.
            entry['overview'] = entry['factor'] == 1.0
            entry['bounds'] = not entry['overview']
            self.maps[ident] = entry
        for entry in self.maps.values():
            if entry['parent'] not in self.maps:
                entry['parent'] = None
        self.links = []
        for link in re.finditer(r'<link parentId="(\d+)"[^>]*target="(\d+)"[^>]*from="([-\d.]+)/([-\d.]+)"',
                                (self.lore / 'maps' / 'links.xml').read_text(encoding='utf-8')):
            parent, target = int(link.group(1)), int(link.group(2))
            if parent in self.maps and target in self.maps and parent != target:
                self.links.append((parent, target, float(link.group(3)), float(link.group(4))))
        self._fit_overviews()
        self._names = {}

    def _fit_overviews(self):
        """Bounds for an overview from its links: x = a*lon + b, y = c*lat + d."""
        self.fit = {}
        for ident, entry in self.maps.items():
            if not entry['overview'] or ident == ROOT:
                continue
            pairs = []
            for parent, target, x, y in self.links:
                child = self.maps[target]
                if parent != ident or not child['bounds'] or child['region'] != entry['region']:
                    continue
                pairs.append(((child['west'] + child['east']) / 2, (child['south'] + child['north']) / 2, x, y))
            result = {'children': len(pairs), 'error': None}
            self.fit[ident] = result
            if len(pairs) < 6:
                continue
            a, b = _line([p[0] for p in pairs], [p[2] for p in pairs])
            c, d = _line([p[1] for p in pairs], [p[3] for p in pairs])
            if a <= 0 or c <= 0:
                continue
            result['error'] = round(sum(((a * p[0] + b - p[2]) ** 2 + (c * p[1] + d - p[3]) ** 2) ** 0.5
                                        for p in pairs) / len(pairs), 1)
            if result['error'] <= FIT_LIMIT:
                # Pixel y runs from 0 at the top to -768 at the bottom.
                entry.update(west=(0 - b) / a, east=(WIDTH - b) / a,
                             north=(0 - d) / c, south=(-HEIGHT - d) / c, bounds=True, fitted=True)

    @staticmethod
    def contains(entry, lat, lon):
        return entry['south'] <= lat <= entry['north'] and entry['west'] <= lon <= entry['east']

    @staticmethod
    def area(entry):
        return max(0.0, entry['north'] - entry['south']) * max(0.0, entry['east'] - entry['west'])

    def chain(self, ident):
        """Root first, the map itself last; Middle-earth is left out."""
        out, seen = [], set()
        while ident is not None and ident not in seen and ident in self.maps:
            seen.add(ident)
            if ident != ROOT:
                out.append(ident)
            ident = self.maps[ident]['parent']
        return list(reversed(out))

    def attribute(self, lat, lon, region):
        """The map of the position's region whose bounds hold it, chosen the way the
        game's own map hierarchy suggests: the deepest map in the hierarchy wins
        (Bree before Bree-land before Eriador); between maps of the same depth,
        neighbours whose rectangles overlap (Swanfleet and Enedwaith), the one on
        which the point lies nearer the middle. None when no map holds it."""
        hits = [entry for entry in self.maps.values()
                if entry['bounds'] and entry['region'] == region and self.contains(entry, lat, lon)]
        if not hits:
            return None

        def off_centre(entry):
            half_width = (entry['east'] - entry['west']) / 2 or 1
            half_height = (entry['north'] - entry['south']) / 2 or 1
            return max(abs(lon - (entry['west'] + entry['east']) / 2) / half_width,
                       abs(lat - (entry['south'] + entry['north']) / 2) / half_height)
        # Checked against the area the game files each quest under (03.11.2026):
        # depth, then nearness to the middle agrees 82.6 % (MoorMap 75.5 %, the
        # most detailed scale first 76.1 %).
        hits.sort(key=lambda e: (-self.depth(e['id']), off_centre(e), e['id']))
        return hits[0]['id']

    def depth(self, ident):
        return len(self.chain(ident))

    def names(self, language):
        if language not in self._names:
            labels = {}
            path = self.lore / 'maps' / 'labels' / language / 'basemaps.xml'
            if path.is_file():
                for match in re.finditer(r'<label key="(\d+)" value="([^"]*)"', path.read_text(encoding='utf-8')):
                    labels[int(match.group(1))] = clean_name(html.unescape(match.group(2)).replace('\\q', '"'))
            self._names[language] = labels
        return self._names[language]

    def name(self, ident, language):
        return self.names(language).get(ident) or clean_name(self.maps[ident]['name'])


def clean_name(name):
    """Game markup ("[fp]") out of a name."""
    return re.sub(r'\[[a-z]{1,3}\]', '', name or '').strip()


def _line(xs, ys):
    """Least squares y = a*x + b."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    var = sum((x - mx) ** 2 for x in xs)
    if var == 0:
        return 0.0, my
    a = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / var
    return a, my - a * mx


def moormap_index(path):
    """Game image id -> MoorMap map number, from MoorMap's Defaults.lua. The only
    thing taken from MoorMap: it lets the plugin's button open the right map. An
    image id two MoorMap maps share is ambiguous and left out."""
    table = defaultdict(set)
    if path is None or not Path(path).is_file():
        return {}
    text = Path(path).read_text(encoding='utf-8', errors='replace')
    for match in re.finditer(r'^\s*tmpMapInfo\[(\d+)\]\s*=\s*\{([^}\n]+)', text, re.M):
        fields = [part.strip() for part in match.group(2).split(',')]
        try:
            if len(fields) > 10 and int(fields[10]) == 1:
                table[int(fields[2], 0)].add(int(match.group(1)))
        except ValueError:
            continue
    return {image: next(iter(found)) for image, found in table.items() if len(found) == 1}
