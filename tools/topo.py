"""Generate Packet-Tracer-style topology SVGs for the CCNA labs."""
import math, os, sys
from xml.sax.saxutils import escape

BLUE, DARK, SIDE = '#2b7bc4', '#13548f', '#0d3f6e'
GRAY, EDGE, SCREEN = '#dfe3e8', '#59606a', '#3d8fdc'
HALO = 'paint-order:stroke;stroke:#fff;stroke-width:3.5px;stroke-linejoin:round'

RADIUS = {'router': 34, 'switch': 40, 'mls': 40, 'pc': 30, 'laptop': 32, 'server': 30}


def arrow(x1, y1, x2, y2, w=2.2):
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#fff" '
            f'stroke-width="{w}" marker-end="url(#ah)"/>')


def icon_router(x, y):
    rx, ry, h = 32, 11, 20
    t = y - h / 2
    s = (f'<path d="M{x-rx},{t} L{x-rx},{t+h} A{rx},{ry} 0 0 0 {x+rx},{t+h} L{x+rx},{t} Z" fill="{DARK}"/>'
         f'<ellipse cx="{x}" cy="{t}" rx="{rx}" ry="{ry}" fill="{BLUE}" stroke="{DARK}" stroke-width="1"/>')
    # Cisco-style router symbol: two arrows in, two arrows out
    s += arrow(x + 4, t - 1.5, x + 20, t - 6.5) + arrow(x - 4, t + 1.5, x - 20, t + 6.5)
    s += arrow(x - 24, t - 7, x - 8, t - 2.5) + arrow(x + 24, t + 7, x + 8, t + 2.5)
    return s


def _box(x, y, h_front=20):
    front = f'<rect x="{x-34}" y="{y-6}" width="64" height="{h_front}" fill="{DARK}"/>'
    top = f'<polygon points="{x-34},{y-6} {x-22},{y-20} {x+42},{y-20} {x+30},{y-6}" fill="{BLUE}" stroke="{DARK}" stroke-width="1"/>'
    side = f'<polygon points="{x+30},{y-6} {x+42},{y-20} {x+42},{y-20+h_front} {x+30},{y-6+h_front}" fill="{SIDE}"/>'
    return front + top + side


def icon_switch(x, y):
    s = _box(x, y)
    s += arrow(x - 18, y - 16, x + 24, y - 16, 2) + arrow(x + 20, y - 10, x - 22, y - 10, 2)
    return s


def icon_mls(x, y):
    s = _box(x, y, 26)
    c = y - 13
    s += arrow(x + 6, c - 1, x + 22, c - 4, 2) + arrow(x - 2, c + 1, x - 18, c + 4, 2)
    s += arrow(x - 20, c - 4, x - 4, c - 1, 2) + arrow(x + 24, c + 4, x + 8, c + 1, 2)
    s += f'<text x="{x-2}" y="{y+12}" font-size="10" font-weight="700" fill="#fff" text-anchor="middle">L3</text>'
    return s


def icon_pc(x, y):
    return (f'<rect x="{x-24}" y="{y-24}" width="40" height="30" rx="2" fill="{GRAY}" stroke="{EDGE}"/>'
            f'<rect x="{x-20}" y="{y-21}" width="32" height="22" fill="{SCREEN}"/>'
            f'<rect x="{x-7}" y="{y+6}" width="6" height="6" fill="{EDGE}"/>'
            f'<rect x="{x-15}" y="{y+12}" width="22" height="3" rx="1" fill="{EDGE}"/>'
            f'<rect x="{x+20}" y="{y-22}" width="12" height="37" rx="1.5" fill="{GRAY}" stroke="{EDGE}"/>'
            f'<line x1="{x+23}" y1="{y-16}" x2="{x+29}" y2="{y-16}" stroke="{EDGE}"/>'
            f'<circle cx="{x+26}" cy="{y+9}" r="1.6" fill="#3cb043"/>')


def icon_laptop(x, y):
    return (f'<rect x="{x-21}" y="{y-24}" width="42" height="28" rx="2" fill="#3a3f46"/>'
            f'<rect x="{x-18}" y="{y-21}" width="36" height="22" fill="{SCREEN}"/>'
            f'<polygon points="{x-24},{y+4} {x+24},{y+4} {x+30},{y+13} {x-30},{y+13}" fill="{GRAY}" stroke="{EDGE}"/>')


def icon_server(x, y):
    s = f'<rect x="{x-15}" y="{y-28}" width="30" height="52" rx="2" fill="{GRAY}" stroke="{EDGE}"/>'
    for dy in (-21, -14, -7):
        s += f'<rect x="{x-10}" y="{y+dy}" width="20" height="4" fill="{SCREEN}"/>'
    s += f'<circle cx="{x+8}" cy="{y+16}" r="2" fill="#3cb043"/>'
    return s


ICONS = {'router': icon_router, 'switch': icon_switch, 'mls': icon_mls,
         'pc': icon_pc, 'laptop': icon_laptop, 'server': icon_server}


def text(x, y, t, size=12, weight='400', color='#222', anchor='middle', halo=True, italic=False):
    st = HALO if halo else ''
    it = ' font-style="italic"' if italic else ''
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{color}" '
            f'text-anchor="{anchor}"{it} style="{st}">{escape(t)}</text>')


def render(spec, path):
    W, H = spec['size']
    dev = {d['id']: d for d in spec['devices']}
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'font-family="Segoe UI, Helvetica, Arial, sans-serif">',
           '<defs><marker id="ah" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="4" markerHeight="4" '
           'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#fff"/></marker></defs>',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
           f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" fill="none" stroke="#d0d7de"/>']
    if spec.get('title'):
        out.append(text(16, 26, spec['title'], 15, '700', '#13548f', 'start', False))

    # zones (dashed areas such as "Part B")
    for z in spec.get('zones', []):
        x, y, w, h, lab = z
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#f6f8fa" stroke="#afb8c1" stroke-dasharray="6 4"/>')
        out.append(text(x + 10, y + 18, lab, 12, '600', '#57606a', 'start', False))

    labels = []
    for L in spec['links']:
        a, b = dev[L['a']], dev[L['b']]
        ax, ay, bx, by = a['x'], a['y'], b['x'], b['y']
        dx, dy = bx - ax, by - ay
        dist = math.hypot(dx, dy)
        ux, uy = dx / dist, dy / dist
        nx, ny = -uy, ux
        off = L.get('offset', 0)
        ax, ay, bx, by = ax + nx * off, ay + ny * off, bx + nx * off, by + ny * off
        cable = L.get('cable', 'straight')
        color = '#4aa3df' if cable == 'console' else '#1f2328'
        dash = ' stroke-dasharray="9 5"' if cable == 'cross' else ''
        if cable == 'console':
            mx, my = (ax + bx) / 2, (ay + by) / 2 + L.get('bend', 70)
            out.append(f'<path d="M{ax},{ay} Q{mx},{my} {bx},{by}" fill="none" stroke="{color}" stroke-width="2.2"/>')
        else:
            out.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{color}" stroke-width="2.2"{dash}/>')
        if cable == 'console':
            for t, port in ((0.16, L.get('pa', '')), (0.84, L.get('pb', ''))):
                qx = (1-t)**2*ax + 2*(1-t)*t*mx + t*t*bx
                qy = (1-t)**2*ay + 2*(1-t)*t*my + t*t*by
                labels.append(text(qx + (14 if t < .5 else -14), qy + 4, port, 10.5, '600', '#1b6fa8', 'start' if t < .5 else 'end'))
            continue
        side = L.get('side', 1)
        for end, (px, py, port, sx, sy, kind) in enumerate((
                (ax, ay, L.get('pa', ''), ux, uy, a['type']),
                (bx, by, L.get('pb', ''), -ux, -uy, b['type']))):
            r = RADIUS[kind]
            light = L.get('lights', ('g', 'g'))[end]
            lc = {'g': '#2ea043', 'a': '#f0a020', 'r': '#d1242f'}[light]
            lx, ly = px + sx * (r + 6), py + sy * (r + 6)
            out.append(f'<circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" fill="{lc}" stroke="#fff" stroke-width="1"/>')
            if port:
                d = r + L.get('pd', 24)
                tx = px + sx * d + nx * 11 * side
                ty = py + sy * d + ny * 11 * side + 4
                labels.append(text(tx, ty, port, 10.5, '500', '#0a3069'))
        if L.get('label'):
            mx, my = (ax + bx) / 2, (ay + by) / 2
            lo = L.get('label_off', -14)
            labels.append(text(mx + nx * lo, my + ny * lo + 4, L['label'], 11, '600', '#8a4600', italic=True))

    for e in spec.get('ellipses', []):
        x, y, rx, ry, rot, lab, lx, ly = e
        out.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" transform="rotate({rot} {x} {y})" '
                   f'fill="none" stroke="#8250df" stroke-width="1.6"/>')
        labels.append(text(lx, ly, lab, 11.5, '700', '#8250df'))

    for d in spec['devices']:
        out.append(ICONS[d['type']](d['x'], d['y']))
        if d.get('rogue'):
            out.append(f'<rect x="{d["x"]-38}" y="{d["y"]-36}" width="76" height="70" rx="8" fill="none" stroke="#d1242f" stroke-width="1.6" stroke-dasharray="5 3"/>')
        pos = d.get('label', 'below')
        r = RADIUS[d['type']]
        lines = [(d['model'], 10.5, '400', '#57606a'), (d['name'], 13, '700', '#1f2328')]
        lines += [(l, 10.5, '400', '#0969da') for l in d.get('info', [])]
        if pos == 'below':
            tx, ty, anc = d['x'], d['y'] + r + (6 if d['type'] in ('switch', 'mls', 'router') else 10), 'middle'
        elif pos == 'above':
            tx, anc = d['x'], 'middle'
            ty = d['y'] - r - 8 - 14 * (len(lines) - 1)
        elif pos == 'right':
            tx, ty, anc = d['x'] + r + 10, d['y'] - 14 * (len(lines) - 1) / 2 + 2, 'start'
        else:
            tx, ty, anc = d['x'] - r - 10, d['y'] - 14 * (len(lines) - 1) / 2 + 2, 'end'
        for i, (t, sz, wt, col) in enumerate(lines):
            out.append(text(tx, ty + i * 14, t, sz, wt, col, anc))

    out.extend(labels)
    for n in spec.get('notes', []):
        x, y, t = n[:3]
        out.append(text(x, y, t, 12, '600', '#8a4600', n[3] if len(n) > 3 else 'middle', italic=True))

    # legend
    lx, ly = 16, H - 18
    items = [('straight', 'Copper Straight-Through'), ('cross', 'Copper Cross-Over')]
    if any(l.get('cable') == 'console' for l in spec['links']):
        items.append(('console', 'Console'))
    for kind, lab in items:
        col = '#4aa3df' if kind == 'console' else '#1f2328'
        dash = ' stroke-dasharray="9 5"' if kind == 'cross' else ''
        out.append(f'<line x1="{lx}" y1="{ly-4}" x2="{lx+34}" y2="{ly-4}" stroke="{col}" stroke-width="2.2"{dash}/>')
        out.append(text(lx + 40, ly, lab, 11, '400', '#57606a', 'start', False))
        lx += 52 + len(lab) * 6.2
    out.append(f'<circle cx="{lx+4}" cy="{ly-4}" r="4" fill="#2ea043"/>')
    out.append(text(lx + 13, ly, 'Link up', 11, '400', '#57606a', 'start', False))
    out.append('</svg>')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write('\n'.join(out))
