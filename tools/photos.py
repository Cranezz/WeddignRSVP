#!/usr/bin/env python3
"""Resize a photograph into the two sizes the site loads.

    python3 tools/photos.py ~/Pictures/us.jpg hero
    python3 tools/photos.py ~/Pictures/dog.jpg gallery-2

Writes img/<name>-<width>.jpg for each width the slot needs. Needs
Pillow: pip install pillow
"""
import pathlib
import sys

from PIL import Image, ImageOps

# Width pairs per slot: the large one is what the lightbox (or a desktop
# hero) loads, the small one is what a phone gets.
SLOTS = {
    "hero": (2000, 1200),
    "gallery-1": (1400, 700),
    "gallery-2": (1400, 700),
    "gallery-3": (1400, 700),
    "gallery-4": (1400, 700),
}

# The hero is background — it can afford more compression than a photo
# someone has deliberately tapped to look at.
QUALITY = {"hero": 74}

OUT = pathlib.Path(__file__).resolve().parent.parent / "img"


def main(argv):
    if len(argv) != 3 or argv[2] not in SLOTS:
        sys.exit("usage: photos.py <source.jpg> <%s>" % "|".join(SLOTS))

    src, slot = pathlib.Path(argv[1]), argv[2]
    # exif_transpose, or a photo shot in portrait on a phone lands sideways.
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")

    for width in SLOTS[slot]:
        height = round(im.height * width / im.width)
        out = OUT / f"{slot}-{width}.jpg"
        im.resize((width, height), Image.LANCZOS).save(
            out, "JPEG", quality=QUALITY.get(slot, 78),
            optimize=True, progressive=True)
        print(f"{out.name:22} {width}x{height}  {out.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main(sys.argv)
