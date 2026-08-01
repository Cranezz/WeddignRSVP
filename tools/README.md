# Lace

`lace.py` draws the lace. One band of artwork is defined per style, and the
engine turns it into both pieces the site needs:

- a **mitred nine-slice frame** for the invitation cards
- a **flat hem** for the seams between grounds on desktop

Both come from the same source, so the frame and the hem cannot drift
apart, and a hem can't end up hung the wrong way round.

## Regenerating

    python3 tools/lace.py eyelet '#F1E7D3'

It prints two CSS custom properties. Paste them over `--lace-frame` and
`--lace-hem` in the `:root` block of `index.html`. Nothing else in the
stylesheet references the artwork directly.

## Styles

- **eyelet** — punched net with rosettes and a scalloped edge. In use.
- **chantilly** — finer diamond ground. Reads as fishnet at small sizes
  and its rotated grid will not tile seamlessly.
- **tape** — bold Battenberg tape. Graphic, but reads more folk-art than
  wedding lace.

## The rule that matters

**The pattern pitch must divide 120 exactly.** The tile is 120 units
wide. A pitch of 3.9 gives 30.77 repeats, so every tile restarts
mid-mesh and the joins show as vertical seams — obvious in a hem
stretched across a wide screen, invisible on a phone. 4.0 gives exactly
30. If you change the pitch, pick a factor of 120.
