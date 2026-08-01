"""One lace engine. A style supplies the artwork for a single 120x30 band;
the engine turns that into both a mitred 9-slice frame and a flat hem, so
the two can never drift apart or be hung the wrong way round."""
import math, urllib.parse

S, B = 120, 30
enc = lambda s: "data:image/svg+xml," + urllib.parse.quote(s, safe="~()*!.'-_")

def petals(cx, cy, ring, rx, ry, n):
    out = ['<circle cx="%.2f" cy="%.2f" r="1.25"/>' % (cx, cy)]
    for i in range(n):
        a = 360 / n * i
        px, py = cx + ring * math.cos(math.radians(a)), cy + ring * math.sin(math.radians(a))
        out.append('<ellipse cx="%.2f" cy="%.2f" rx="%s" ry="%s" transform="rotate(%.1f %.2f %.2f)"/>'
                   % (px, py, rx, ry, a + 90, px, py))
    return "".join(out)

def scallop_edge(count, depth, lift=0.32):
    step = S / count
    d = ["M0,%s" % depth]
    for i in range(count):
        x0 = i * step
        d.append("Q%.2f,%.2f %.2f,%s" % (x0 + step / 2, -depth * lift, x0 + step, depth))
    return " ".join(d)

# ---------------------------------------------------------------- styles
def style_eyelet(lace):
    """Punched eyelet net with rosettes — the current design."""
    P, R, D = 4.0, 1.1, 8          # 120 / 4 = 30 exactly, so the net tiles seamlessly
    net = ('<pattern id="n" width="%s" height="%.3f" patternUnits="userSpaceOnUse">'
           '<circle cx="%.2f" cy="%.3f" r="%s"/><circle cx="0" cy="%.3f" r="%s"/>'
           '<circle cx="%s" cy="%.3f" r="%s"/></pattern>'
           % (P, P*.87*2, P/2, P*.87/2, R, P*.87*1.5, R, P, P*.87*1.5, R))
    fill = '<path d="%s L%s,%s L0,%s Z"/>' % (scallop_edge(8, D), S, B, B)
    holes = ('<rect x="1.6" y="3.2" width="%.1f" height="%.1f" fill="url(#n)"/>%s'
             % (S-3.2, B-6.4, "".join(petals(i*(S/4)+(S/8), 16, 4.4, 1.45, 2.4, 6) for i in range(4))))
    return dict(defs=net, fill=fill, holes=holes, masked=True)

def style_chantilly(lace):
    """Fine tulle: a diamond ground, shallow scallops, picot loops and an
    outlined vine. Delicate — reads as antique lace up close."""
    D = 6
    # Diamonds drawn outright rather than a rotated square: patternTransform
    # breaks seamless tiling because the rotated grid no longer lines up
    # with the tile edge.
    dia = ('<pattern id="n" width="6" height="6" patternUnits="userSpaceOnUse">'
           '<path d="M3,0.5 L5.5,3 L3,5.5 L0.5,3 Z"/>'
           '<path d="M0,-2.5 L2.5,0 L0,2.5 L-2.5,0 Z"/>'
           '<path d="M6,-2.5 L8.5,0 L6,2.5 L3.5,0 Z"/>'
           '<path d="M0,3.5 L2.5,6 L0,8.5 L-2.5,6 Z"/>'
           '<path d="M6,3.5 L8.5,6 L6,8.5 L3.5,6 Z"/></pattern>')
    fill = '<path d="%s L%s,%s L0,%s Z"/>' % (scallop_edge(10, D, .28), S, B, B)
    picot = "".join('<circle cx="%.1f" cy="%.1f" r="1.5"/>' % (i*12+6, 1.4) for i in range(10))
    vine = "".join(petals(i*(S/3)+(S/6), 17.5, 5.2, 1.1, 2.6, 8) for i in range(3))
    holes = ('<rect x="2" y="2.6" width="%.1f" height="%.1f" fill="url(#n)"/>%s'
             % (S-4, B-5.6, vine))
    return dict(defs=dia, fill=fill + picot, holes=holes, masked=True)

def style_tape(lace):
    """Battenberg: a solid tape looping in scallops, joined to a straight
    heading tape by fine bars, with real open space between. Graphic, so
    it survives being shrunk to a 30px hem across a wide screen."""
    loops, step = 6, S / 6
    tape = ('<path d="M0,20 %s" fill="none" stroke="%s" stroke-width="4.6" stroke-linecap="round"/>'
            % (" ".join("C%.1f,%.1f %.1f,%.1f %.1f,20"
                        % (i*step+step*.18, 32.5, i*step+step*.82, 32.5, (i+1)*step)
                        for i in range(loops)), lace))
    heading = '<rect x="0" y="2.2" width="%s" height="4.2" fill="%s"/>' % (S, lace)
    bars = "".join('<rect x="%.1f" y="6" width="1.3" height="14.5" fill="%s"/>'
                   % (i*step/2 + step/4, lace) for i in range(loops*2))
    rings = "".join('<circle cx="%.1f" cy="24.5" r="2.5" fill="none" stroke="%s" stroke-width="1.5"/>'
                    % (i*step + step/2, lace) for i in range(loops))
    dots = "".join('<circle cx="%.1f" cy="10.5" r="1.5" fill="%s"/>' % (i*step + step/2, lace)
                   for i in range(loops))
    return dict(defs="", art=heading + bars + tape + rings + dots, masked=False)

STYLES = {"eyelet": style_eyelet, "chantilly": style_chantilly, "tape": style_tape}

def build(style, lace="#F1E7D3"):
    s = STYLES[style](lace)
    mitre = '<clipPath id="mit"><path d="M0,0 L%s,0 L%s,%s L%s,%s Z"/></clipPath>' % (S, S-B, B, B, B)
    rot = lambda body: "".join('<g transform="rotate(%d %s %s)"><g clip-path="url(#mit)">%s</g></g>'
                               % (a, S/2, S/2, body) for a in (0, 90, 180, 270))
    if s["masked"]:
        frame = ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s">'
                 '<defs>%s%s<g id="f">%s</g><g id="h">%s</g>'
                 '<mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="%s" height="%s">'
                 '<rect width="%s" height="%s" fill="#fff"/><g fill="#000">%s</g></mask></defs>'
                 '<g fill="%s" mask="url(#m)">%s</g></svg>'
                 % (S, S, S, S, s["defs"], mitre, s["fill"], s["holes"], S, S, S, S,
                    rot('<use href="#h"/>'), lace, rot('<use href="#f"/>')))
        strip = ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s">'
                 '<defs>%s<mask id="m" maskUnits="userSpaceOnUse" x="0" y="0" width="%s" height="%s">'
                 '<rect width="%s" height="%s" fill="#fff"/><g fill="#000">%s</g></mask></defs>'
                 '<g fill="%s" mask="url(#m)">%s</g></svg>'
                 % (S, B, S, B, s["defs"], S, B, S, B, s["holes"], lace, s["fill"]))
    else:
        frame = ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s">'
                 '<defs>%s<g id="a">%s</g></defs>%s</svg>'
                 % (S, S, S, S, mitre, s["art"], rot('<use href="#a"/>')))
        strip = ('<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s">'
                 '%s</svg>' % (S, B, S, B, s["art"]))
    return enc(frame), enc(strip)


# ---------------------------------------------------------------- CLI
if __name__ == "__main__":
    import sys
    style = sys.argv[1] if len(sys.argv) > 1 else "eyelet"
    colour = sys.argv[2] if len(sys.argv) > 2 else "#F1E7D3"
    frame, hem = build(style, colour)
    print("--lace-frame: url(\"%s\");\n" % frame)
    print("--lace-hem:   url(\"%s\");" % hem)
