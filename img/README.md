# Photographs

Placeholders for now. Replace any file with your own and the page picks
it up — no code changes needed, as long as the filenames stay the same.

| File | Where it appears |
|------|------------------|
| `hero-1200.jpg`, `hero-2000.jpg` | Behind the invitation at the top of the page |
| `gallery-1-700.jpg`, `gallery-1-1400.jpg` | Story gallery, the wide one across the top |
| `gallery-2-*.jpg` … `gallery-4-*.jpg` | Story gallery, the three below it |

Two sizes of each: phones load the small one, desktops the large one,
and the gallery only loads a large file when someone taps a photo.

## Swapping one out

Drop the new photo in this folder and run, from the repo root:

```
python3 tools/photos.py path/to/new-photo.jpg hero
python3 tools/photos.py path/to/another.jpg gallery-2
```

That writes both sizes at the right dimensions and compression. It needs
Pillow (`pip install pillow`).

## Captions and alt text

Both live in `index.html`, in the `<div class="gallery">` block:

- `data-cap` is the caption under the photo in the lightbox.
- `alt` is what a screen reader says, and what shows if the image fails
  to load. Describe what is in the frame.

The wide photo at the top of the gallery is the one that gets the full
width, so put a landscape shot there. The other three are cropped to
3:4 portrait.

## The hero

`hero-*.jpg` sits behind the invitation with an oxblood wash over it, so
it wants a photo that still reads when it is dimmed: open sky, a horizon,
faces near the middle. The invitation card covers the centre on a phone —
`object-position: 50% 40%` in the stylesheet controls which part of the
photo stays visible, and can be nudged if a face ends up behind the card.
