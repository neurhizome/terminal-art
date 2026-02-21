#!/usr/bin/env python3
"""
tools/graph_viz.py  –  Render the knowledge graph as a cyberpunk ANSI capture.

Parses frontmatter from docs/_posts/ and docs/concepts/, builds the link
graph, renders as box-drawing / 24-bit colour art, and writes to
docs/assets/captures/knowledge-graph.ans.

Layout is fully dynamic: new posts and concepts are automatically positioned
as they are added. No hardcoded node positions or edge lists.

Run manually:
    python3 tools/graph_viz.py

Called automatically by .git/hooks/post-commit when docs/_posts/ or
docs/concepts/ files change.
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "docs" / "_posts"
CONC_DIR  = ROOT / "docs" / "concepts"
OUT       = ROOT / "docs" / "assets" / "captures" / "knowledge-graph.ans"

# ── canvas geometry ───────────────────────────────────────────────────────────
COLS     = 96
NODE_H   = 5      # height of each node box (including borders)
NODE_GAP = 2      # gap rows between adjacent node boxes
NODE_STRIDE = NODE_H + NODE_GAP   # rows from top of one node to top of next

# Layout columns
LX, LW = 1, 37     # left node column  (x offset, width)
RX, RW = 52, 42    # right node column (x offset, width)
SPINE_X  = LX + LW // 2   # x of the vertical chronological spine (= 19)
CONN_MID = 44              # x of midpoint routing for L-shaped connectors

START_Y  = 3       # first node's top row (below outer border + header)
FOOTER_H = 7       # rows reserved for legend + bottom outer border

# ── colour palette (RGB tuples) ───────────────────────────────────────────────
BG        = (17,  21,  28)
C_FRAME   = (56,  182, 194)   # teal    – outer chrome
C_HEAD    = (200, 212, 230)   # near-white – headline text
C_DIM     = (66,  78,  100)   # dark-grey – ambient labels
C_EDGE    = (88,  108, 140)   # edge connector lines
C_TICK    = (48,  58,  80)    # subtle tick / scanline marks

C_BEGIN   = (229, 192, 123)   # amber   – beginning node
C_SESSION = (97,  175, 239)   # blue    – session nodes
C_GRAD    = (152, 195, 121)   # green   – gradient/aesthetic nodes
C_CONCEPT = (198, 120, 221)   # purple  – concept nodes

# ── node appearance maps ──────────────────────────────────────────────────────
NODE_TYPE_COLOR = {
    'beginning': C_BEGIN,
    'session':   C_SESSION,
    'gradient':  C_GRAD,
    'concept':   C_CONCEPT,
}

NODE_TYPE_STYLE = {
    'beginning': 'heavy',
    'session':   'double',
    'gradient':  'round',
    'concept':   'single',
}

NODE_TYPE_GLYPH = {
    'beginning': '◈',
    'session':   '◆',
    'gradient':  '◉',
    'concept':   '◇',
}

# ── ANSI helpers ──────────────────────────────────────────────────────────────
def _fg(r, g, b): return f"\x1b[38;2;{r};{g};{b}m"
def _bg(r, g, b): return f"\x1b[48;2;{r};{g};{b}m"
RST = "\x1b[0m"


# ── minimal YAML frontmatter parser ──────────────────────────────────────────
_FM_RE = re.compile(r'^---\s*\n(.*?)\n---', re.DOTALL)

def _parse_yaml(text):
    """Extract flat key→value / key→list from YAML frontmatter."""
    result = {}
    lines  = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'^(\w[\w-]*):\s*(.*)', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val == '':
                # block: list of scalars or dicts
                items = []
                i += 1
                while i < len(lines) and (lines[i].startswith('  ') or lines[i] == ''):
                    sub = lines[i].strip()
                    if sub.startswith('- '):
                        item_text = sub[2:]
                        if ':' in item_text and not item_text.startswith('"'):
                            # dict item – grab continuation lines
                            d = {}
                            dm = re.match(r'(\w+):\s*(.*)', item_text)
                            if dm:
                                d[dm.group(1)] = dm.group(2).strip().strip('"\'')
                            i += 1
                            while i < len(lines) and re.match(r'^    \w', lines[i]):
                                kv = re.match(r'\s+(\w+):\s*(.*)', lines[i])
                                if kv:
                                    d[kv.group(1)] = kv.group(2).strip().strip('"\'')
                                i += 1
                            items.append(d)
                            continue
                        else:
                            items.append(item_text.strip('"\''))
                    i += 1
                result[key] = items
                continue
            else:
                if val.startswith('[') and val.endswith(']'):
                    val = [v.strip().strip('"\'') for v in val[1:-1].split(',') if v.strip()]
                else:
                    val = val.strip('"\'')
                result[key] = val
        i += 1
    return result


def _parse_file(path):
    text = path.read_text(encoding='utf-8')
    m = _FM_RE.match(text)
    return _parse_yaml(m.group(1)) if m else {}


# ── graph construction ────────────────────────────────────────────────────────
def build_graph():
    """
    Parse all post and concept markdown files, return (nodes, edges).

    nodes: dict  nid → {label, sub, type, related}
    edges: set of frozenset({nid_a, nid_b})
    """
    nodes = {}
    edges = set()

    def node_id(path, fm):
        stem = path.stem
        if 'concepts' in str(path):
            return stem
        # date-slug form: strip YYYY-MM-DD- prefix
        parts = stem.split('-', 3)
        return parts[3] if len(parts) == 4 else stem

    def classify(fm, path):
        tags = fm.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        if 'concepts' in str(path):
            return 'concept'
        if 'session' in tags:
            return 'session'
        if 'aesthetic' in tags or 'gradient-flow' in tags:
            return 'gradient'
        return 'beginning'

    def short_title(title):
        t = title.replace('Concept: ', '').replace('Session ', 'S').strip()
        return t[:30] + '…' if len(t) > 33 else t

    # ─ load posts ─
    for md in sorted(POSTS_DIR.glob('*.md')):
        fm  = _parse_file(md)
        nid = node_id(md, fm)
        t   = classify(fm, md)
        nodes[nid] = {
            'label':   short_title(fm.get('title', nid)),
            'sub':     str(fm.get('date', ''))[:10],
            'type':    t,
            'related': fm.get('related', []),
        }

    # ─ load concepts (skip index) ─
    for md in sorted(CONC_DIR.glob('*.md')):
        if md.stem == 'index':
            continue
        fm  = _parse_file(md)
        nid = md.stem
        nodes[nid] = {
            'label':   short_title(fm.get('title', nid)),
            'sub':     'concept',
            'type':    'concept',
            'related': fm.get('related', []),
        }

    # ─ build edges from related lists ─
    def url_to_id(url):
        url = url.rstrip('/')
        parts = [p for p in url.split('/') if p]
        slug = parts[-1].replace('.html', '')
        if re.match(r'^\d{4}-\d{2}-\d{2}-', slug):
            slug = slug.split('-', 3)[3]
        return slug

    for src, node in nodes.items():
        for rel in node['related']:
            if isinstance(rel, dict):
                tgt = url_to_id(rel.get('url', ''))
                if tgt in nodes:
                    edges.add(frozenset({src, tgt}))

    return nodes, edges


# ── dynamic layout ───────────────────────────────────────────────────────────
def compute_layout(nodes):
    """
    Assign canvas positions to all nodes without any hardcoding.

    Left column  — chronological narrative posts (type: beginning, session)
    Right column — reference/aesthetic content  (type: concept, gradient)

    Left sorted by date ascending; right sorted by label alphabetically.

    Returns:
        layout     – dict nid → {x, w, y, col: 'left'|'right'}
        left_nodes – list of nids in left column, sorted by date
        right_nodes– list of nids in right column, sorted by label
    """
    left_nodes  = []
    right_nodes = []

    for nid, node in nodes.items():
        if node['type'] in ('concept', 'gradient'):
            right_nodes.append(nid)
        else:
            left_nodes.append(nid)

    left_nodes.sort(key=lambda nid: nodes[nid].get('sub', ''))
    right_nodes.sort(key=lambda nid: nodes[nid].get('label', nid).lower())

    layout = {}
    for i, nid in enumerate(left_nodes):
        layout[nid] = {'x': LX, 'w': LW, 'y': START_Y + i * NODE_STRIDE, 'col': 'left'}
    for i, nid in enumerate(right_nodes):
        layout[nid] = {'x': RX, 'w': RW, 'y': START_Y + i * NODE_STRIDE, 'col': 'right'}

    return layout, left_nodes, right_nodes


def canvas_height(left_nodes, right_nodes):
    """Compute required canvas rows from node counts."""
    max_col = max(len(left_nodes), len(right_nodes), 1)
    return max(40, START_Y + max_col * NODE_STRIDE + FOOTER_H)


# ── Canvas ────────────────────────────────────────────────────────────────────
class Canvas:
    def __init__(self, cols, rows):
        self.cols, self.rows = cols, rows
        self.ch = [[' '] * cols for _ in range(rows)]
        self.fc = [[None]  * cols for _ in range(rows)]
        self.bc = [[BG]    * cols for _ in range(rows)]

    def put(self, x, y, char, fc=None, bc=None):
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self.ch[y][x] = char
            if fc is not None: self.fc[y][x] = fc
            if bc is not None: self.bc[y][x] = bc

    def txt(self, x, y, s, fc=None, bc=None):
        for i, c in enumerate(s):
            self.put(x + i, y, c, fc, bc)

    def hline(self, x, y, n, c, fc=None):
        for i in range(n):
            self.put(x + i, y, c, fc)

    def vline(self, x, y, n, c, fc=None):
        for i in range(n):
            self.put(x, y + i, c, fc)

    def box(self, x, y, w, h, color, style='single'):
        tl, hz, tr, vt, bl, br = {
            'single': ('┌', '─', '┐', '│', '└', '┘'),
            'double': ('╔', '═', '╗', '║', '╚', '╝'),
            'heavy':  ('┏', '━', '┓', '┃', '┗', '┛'),
            'round':  ('╭', '─', '╮', '│', '╰', '╯'),
        }[style]
        self.put(x,     y,     tl, color)
        self.hline(x+1, y,     w-2, hz, color)
        self.put(x+w-1, y,     tr, color)
        self.put(x,     y+h-1, bl, color)
        self.hline(x+1, y+h-1, w-2, hz, color)
        self.put(x+w-1, y+h-1, br, color)
        self.vline(x,     y+1, h-2, vt, color)
        self.vline(x+w-1, y+1, h-2, vt, color)
        for ry in range(y+1, y+h-1):
            for rx in range(x+1, x+w-1):
                self.bc[ry][rx] = BG

    def to_ansi(self):
        out = []
        for row in range(self.rows):
            line = []
            cf = cb = None
            for col in range(self.cols):
                c  = self.ch[row][col]
                nf = self.fc[row][col]
                nb = self.bc[row][col]
                if nf != cf:
                    line.append(_fg(*nf) if nf else "\x1b[39m")
                    cf = nf
                if nb != cb:
                    line.append(_bg(*nb) if nb else "\x1b[49m")
                    cb = nb
                line.append(c)
            out.append(''.join(line))
        return '\r\n'.join(out) + RST


# ── node drawing ──────────────────────────────────────────────────────────────
def draw_node(cv, nid, node, layout):
    pos = layout.get(nid)
    if pos is None:
        return
    color = NODE_TYPE_COLOR.get(node['type'], C_DIM)
    style = NODE_TYPE_STYLE.get(node['type'], 'single')
    glyph = NODE_TYPE_GLYPH.get(node['type'], '·')
    x, y, w = pos['x'], pos['y'], pos['w']
    cv.box(x, y, w, NODE_H, color, style)
    badge = f"{glyph} {node['type'].upper()}"
    cv.txt(x+2, y+1, badge[:w-4],        fc=color)
    cv.txt(x+2, y+2, node['label'][:w-4], fc=C_HEAD)
    cv.txt(x+2, y+3, node['sub'][:w-4],   fc=C_DIM)


# ── chronological spine ───────────────────────────────────────────────────────
def draw_spine(cv, layout, left_nodes):
    """
    Vertical chronological spine connecting all left-column nodes.

    The spine runs down from the first node (BEGINNING) through all sessions,
    with branch joints (├) above each node and a terminus (└) at the last.
    """
    if len(left_nodes) < 2:
        return

    x        = SPINE_X
    first_y  = layout[left_nodes[0]]['y']
    last_y   = layout[left_nodes[-1]]['y']

    # Top cap: corner at the bottom-centre of the first node → spine turns down
    cap_y = first_y + NODE_H - 1
    cv.put(x, cap_y, '┐', C_EDGE)

    # Trunk: vertical line from just below first node to last node's top row
    trunk_start = first_y + NODE_H
    cv.vline(x, trunk_start, last_y - trunk_start, '│', C_EDGE)

    # Bottom cap at the top row of the last node
    cv.put(x, last_y, '└', C_EDGE)

    # Branch joints: one per subsequent node (all except the first)
    for nid in left_nodes[1:]:
        ny = layout[nid]['y']
        cv.put(x,             ny - 1, '├', C_EDGE)
        cv.hline(x + 1,       ny - 1, LX + LW - x - 2, '─', C_EDGE)
        cv.put(LX + LW - 1,   ny - 1, '▶', C_EDGE)


# ── connectors ────────────────────────────────────────────────────────────────
def _h_connector(cv, left_y_row, right_y_row, left_x_end, right_x_start, color=C_EDGE):
    """Route a connector between the left and right columns (straight or L-shaped)."""
    mid_y_l = left_y_row  + NODE_H // 2
    mid_y_r = right_y_row + NODE_H // 2
    lx = left_x_end
    rx = right_x_start - 1

    if mid_y_l == mid_y_r:
        # straight horizontal
        cv.hline(lx, mid_y_l, rx - lx, '─', color)
        cv.put(rx, mid_y_l, '▶', color)
    else:
        # L-shape: go right to CONN_MID, then up/down to right-column row
        turn_x = CONN_MID
        cy, ty = mid_y_l, mid_y_r
        cv.hline(lx, cy, turn_x - lx, '─', color)
        if ty < cy:
            cv.vline(turn_x, ty, cy - ty, '│', color)
            cv.put(turn_x, ty, '┬', color)
            cv.put(turn_x, cy, '└', color)
        else:
            cv.vline(turn_x, cy, ty - cy + 1, '│', color)
            cv.put(turn_x, cy, '┌', color)
            cv.put(turn_x, ty, '└', color)
        cv.hline(turn_x + 1, ty, rx - turn_x - 1, '─', color)
        cv.put(rx, ty, '▶', color)


def draw_edges(cv, edges, layout):
    """
    Draw connectors for all edges derived from [[related]] frontmatter.

    Cross-column edges are drawn as horizontal/L-shaped connectors.
    Same-column right-column edges (concept→concept or concept→aesthetic)
    are drawn as subtle vertical dotted links.
    Left-column (session→session) edges are implied by the chronological
    spine and are skipped to avoid visual clutter.
    """
    for edge in edges:
        pair = list(edge)
        if len(pair) != 2:
            continue
        a, b = pair
        if a not in layout or b not in layout:
            continue

        pa, pb = layout[a], layout[b]

        if pa['col'] == pb['col']:
            # Right-column only: draw a subtle vertical dotted link
            if pa['col'] == 'right':
                py1, py2 = sorted([pa['y'], pb['y']])
                gx = RX + RW // 2
                gap_start = py1 + NODE_H
                gap_len   = py2 - gap_start
                if gap_len > 0:
                    cv.vline(gx, gap_start, gap_len, '┆', fc=C_DIM)
                    cv.put(gx, py2 - 1, '▼', fc=C_DIM)
            # Left-left edges implied by spine — skip
            continue

        # Cross-column: normalise so pa is always left, pb always right
        if pa['col'] == 'right':
            pa, pb = pb, pa

        _h_connector(
            cv,
            left_y_row    = pa['y'],
            right_y_row   = pb['y'],
            left_x_end    = pa['x'] + pa['w'],
            right_x_start = pb['x'],
            color         = C_EDGE,
        )


# ── legend ────────────────────────────────────────────────────────────────────
def draw_legend(cv, n_nodes, n_edges):
    rows     = cv.rows
    y_rule   = rows - 7
    y_types  = rows - 6
    y_meta   = rows - 5

    cv.hline(1, y_rule, COLS - 2, '─', C_TICK)
    cv.txt(2, y_types, "node types", fc=C_DIM)

    cx = 14
    for t, color, glyph in [
        ('beginning', C_BEGIN,   '◈'),
        ('session',   C_SESSION, '◆'),
        ('aesthetic', C_GRAD,    '◉'),
        ('concept',   C_CONCEPT, '◇'),
    ]:
        cv.txt(cx, y_types, f"{glyph} {t}", fc=color)
        cx += len(t) + 5

    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    cv.txt(2, y_meta,
           f"nodes: {n_nodes}   edges: {n_edges}   auto-rendered on commit",
           fc=C_DIM)
    cv.txt(COLS - len(ts) - 2, y_meta, ts, fc=C_TICK)


# ── rendering ─────────────────────────────────────────────────────────────────
def render(nodes, edges, print_ansi=False):
    layout, left_nodes, right_nodes = compute_layout(nodes)
    rows = canvas_height(left_nodes, right_nodes)
    cv   = Canvas(cols=COLS, rows=rows)

    # ── outer chrome ──────────────────────────────────────────────────────────
    cv.box(0, 0, COLS, rows, C_FRAME, 'double')

    header = "KNOWLEDGE GRAPH  //  TERMINAL-ART"
    cv.txt((COLS - len(header)) // 2, 0, header, fc=C_HEAD)
    cv.txt(2, 1,
           "commit-driven topology · nodes link through [[related]] frontmatter",
           fc=C_DIM)

    # decorative scanlines
    for y in range(3, rows - 2, 6):
        cv.hline(1, y, COLS - 2, '·', fc=C_TICK)

    # column labels
    cv.txt(LX + 1, START_Y - 1, "chronological spine", fc=C_DIM)
    cv.txt(RX + 1, START_Y - 1, "concept space",       fc=C_DIM)
    cv.vline(49, START_Y - 1, rows - START_Y - FOOTER_H, '┆', fc=C_TICK)

    # ── nodes, spine, edges ───────────────────────────────────────────────────
    for nid, node in nodes.items():
        draw_node(cv, nid, node, layout)

    draw_spine(cv, layout, left_nodes)
    draw_edges(cv, edges, layout)

    # ── legend ────────────────────────────────────────────────────────────────
    draw_legend(cv, len(nodes), len(edges))

    ansi = cv.to_ansi()
    if print_ansi:
        print(ansi)
    return ansi, rows


# ── .ans file writer ──────────────────────────────────────────────────────────
HEADER_TEMPLATE = """\
# title: Knowledge Graph — terminal-art
# cols: {cols}
# rows: {rows}
# fontsize: 13
# date: {date}
# description: Post-commit knowledge graph. Nodes = posts + concepts, edges = related frontmatter.
"""

def save(ansi, rows, path=OUT):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = HEADER_TEMPLATE.format(
        cols=COLS,
        rows=rows,
        date=datetime.now().strftime('%Y-%m-%d'),
    )
    path.write_text(header + "\n" + ansi, encoding='utf-8')
    print(f"[graph_viz] wrote {path.stat().st_size:,} bytes → {path}", file=sys.stderr)


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Render knowledge graph as ANSI capture — dynamic layout, auto-rebuilds on commit"
    )
    parser.add_argument('--print', action='store_true', help='Also dump raw ANSI to stdout')
    parser.add_argument('--out', default=str(OUT), help='Output .ans file path')
    args = parser.parse_args()

    nodes, edges = build_graph()
    ansi, rows   = render(nodes, edges, print_ansi=args.print)
    save(ansi, rows, path=args.out)

    print(f"[graph_viz] {len(nodes)} nodes, {len(edges)} edges, {rows} rows", file=sys.stderr)


if __name__ == '__main__':
    main()
