"""Render the vendored Lucide icons into LOTRO plugin textures (.tga).

Lucide icons are ISC licensed (see icon-sources/NOTICE). They keep their shape and
are only recoloured and sized, because the client paints no SVG: it loads 32-bit
Targa textures by plugin-relative path.

Two rules matter for how they look in the game:

* every icon is rendered at exactly the pixel size it is drawn at. The client
  samples plugin textures poorly, so shrinking a large icon produces jagged edges.
* the alpha is taken from a black stroke on white. ImageMagick's SVG renderer
  ignores transparency and always paints an opaque background, and this way both
  renderers produce the same mask.

ImageMagick is used first; a few Lucide icons contain compact arc flags
("a3 3 0 01-3-3") that its parser rejects, and those fall back to macOS Quick
Look. The fallback is the only macOS-only part.

Run:  python3 MagicQuestLog/tools/build_icons.py
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'icon-sources'
TARGET = ROOT / 'plugin/MagicQuestLog/Resources'

# file name -> (lucide slug, pixel size, stroke colour in the game)
ICONS = {
    'start': ('mop-sparkles', 24, '#f0d18c'),
    'quests': ('scroll-text', 18, '#e8e0c8'),
    'deeds': ('trophy', 18, '#e8e0c8'),
    'search': ('search', 16, '#c8c8c8'),
    'clear': ('x', 14, '#c8c8c8'),
    'mappin': ('map-pin', 18, '#f0d18c'),
    'closed': ('chevron-right', 11, '#c8c8c8'),
    'open': ('chevron-down', 11, '#c8c8c8'),
    'todo': ('circle', 12, '#9a9a9a'),
    'done': ('circle-check', 12, '#5af05a'),
    'todobig': ('circle', 18, '#9a9a9a'),
    'donebig': ('circle-check', 18, '#5af05a'),
}

INK = 8  # alpha above this counts as drawn, for cropping


def sized_copy(name, slug, size, stroke='#000000'):
    """Black stroke on nothing, and the SVG itself declared at the target size."""
    source = SOURCES / (slug + '.svg')
    assert source.is_file(), 'missing icon source: %s' % source
    text = source.read_text(encoding='utf-8')
    assert 'currentColor' in text, 'unexpected icon: no currentColor stroke'
    text = text.replace('currentColor', stroke)
    text = re.sub(r'width="[\d.]+"', 'width="%d"' % size, text, count=1)
    text = re.sub(r'height="[\d.]+"', 'height="%d"' % size, text, count=1)
    copy = SOURCES / (name + '.plain.svg')
    copy.write_text(text, encoding='utf-8')
    return copy


def to_alpha(grey):
    """Black stroke on white -> opaque stroke on transparent background."""
    return grey.point(lambda value: 255 - value)


def with_magick(svg, size):
    """Alpha mask, or None when ImageMagick cannot parse this icon."""
    tga = svg.with_suffix('.magick.tga')
    try:
        subprocess.run(['magick', str(svg), '-resize', '%dx%d' % (size, size),
                        '-colorspace', 'Gray', 'tga:%s' % tga],
                       check=True, capture_output=True)
        with Image.open(tga) as image:
            image.load()
            grey = image.convert('L')
        assert grey.size == (size, size), 'renderer returned %s' % (grey.size,)
        return to_alpha(grey)
    except subprocess.CalledProcessError:
        return None
    finally:
        tga.unlink(missing_ok=True)


def with_quicklook(svg, size):
    """Alpha mask through macOS Quick Look.

    Quick Look renders at the size the SVG declares and pads the thumbnail to a
    square, so the drawn shape is cropped to its ink and only then fitted.
    """
    scratch = SOURCES / 'quicklook'
    scratch.mkdir(exist_ok=True)
    try:
        subprocess.run(['qlmanage', '-t', '-s', str(size * 8), '-o', str(scratch), str(svg)],
                       check=True, capture_output=True)
        rendered = scratch / (svg.name + '.png')
        assert rendered.is_file(), 'Quick Look produced nothing for ' + svg.name
        with Image.open(rendered) as raw:
            alpha = to_alpha(raw.convert('L'))
        ink = alpha.point(lambda value: 255 if value > INK else 0).getbbox()
        assert ink is not None, 'Quick Look drew nothing for ' + svg.name
        return alpha.crop(ink).resize((size, size), Image.LANCZOS)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def tga32(image):
    """Uncompressed 32-bit Targa, bottom-left origin: the format the plugins ship.

    ImageMagick and Pillow both write a top-left origin flag; the client's own
    texture files use the classic bottom-left one, so it is written by hand.
    """
    width, height = image.size
    header = bytearray(18)
    header[2] = 2                       # uncompressed true colour
    header[12:14] = width.to_bytes(2, 'little')
    header[14:16] = height.to_bytes(2, 'little')
    header[16] = 32                     # bits per pixel
    header[17] = 8                      # 8 alpha bits, bottom-left origin
    body = bytearray()
    for y in range(height - 1, -1, -1):
        for x in range(width):
            red, green, blue, alpha = image.getpixel((x, y))
            body += bytes((blue, green, red, alpha))
    return bytes(header) + bytes(body)


def render(name, slug, size, colour):
    svg = sized_copy(name, slug, size)
    try:
        # Quick Look ignores currentColor and pads to square, so it gets a copy
        # declared larger and is only used when ImageMagick cannot parse the icon.
        mask = with_magick(svg, size)
        if mask is None:
            big = sized_copy(name + '.big', slug, size * 8)
            try:
                mask = with_quicklook(big, size)
            finally:
                big.unlink(missing_ok=True)
        image = Image.new('RGBA', (size, size), colour)
        image.putalpha(mask)
        solid = image.getchannel('A').getextrema()
        assert solid[1] > 200, 'icon %s stayed empty' % name
        assert solid[0] < 60, 'icon %s has no transparency' % name
        target = TARGET / (name + '.tga')
        target.write_bytes(tga32(image))
    finally:
        svg.unlink(missing_ok=True)
    return target


def main():
    TARGET.mkdir(parents=True, exist_ok=True)
    for name, (slug, size, colour) in sorted(ICONS.items()):
        target = render(name, slug, size, colour)
        print('%-8s %-14s %2dpx  %s' % (name, slug, size, target.name))
    return 0


if __name__ == '__main__':
    sys.exit(main())
