#!/usr/bin/env python3
"""
tools/graph_viz.py  –  Render the knowledge graph as a cyberpunk ANSI capture.

Parses frontmatter from docs/_posts/ and docs/concepts/, builds the link
graph, renders as box-drawing / 24-bit colour art, and writes to
docs/assets/captures/knowledge-graph.ans.

Run manually:
    python tools/graph_viz.py

Called automatically by .git/hooks/post-commit.
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
COLS, ROWS = 96, 40

# ── colour palette (RGB tuples) ───────────────────────────────────────────────
BG        = (17,  21,  28)
C_FRAME   = (56,  182, 194)   # teal  – outer chrome
C_HEAD    = (200, 212, 230)   # near-white headline
C_DIM     = (66,  78,  100)   # dark-grey dim elements
C_EDGE    = (88,  108, 140)   # edge connector lines
C_TICK    = (48,  58,  80)    # subtle tick marks

C_BEGIN   = (229, 192, 123)   # amber   – beginning node
C_SESSION = (97,  175, 239)   # blue    – session nodes
C_GRAD    = (152, 195, 121)   # green   – gradient/aesthetic nodes
C_CONCEPT = (198, 120, 221)   # purple  – concept nodes
C_ACCENT  = (224, 108, 117)   # red     – accent / highlights

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
    nodes = {}  # id -> dict
    edges = set()  # frozensets of 2 ids

    def node_id(path, fm):
        stem = path.stem
        if 'concepts' in str(path):
            return stem
        # date-slug form: strip date prefix
        parts = stem.split('-', 3)
        return parts[3] if len(parts) == 4 else stem

    def classify(fm, path):
        tags = fm.get('tags', [])
        if isinstance(tags, str): tags = [tags]
        if 'concepts' in str(path):       return 'concept'
        if 'session'  in tags:            return 'session'
        if 'aesthetic' in tags or 'gradient-flow' in tags: return 'gradient'
        return 'beginning'

    def short_title(title):
        """Shorten long titles to fit in a 33-char label field."""
        t = title.replace('Concept: ', '').replace('Session ', 'S').strip()
        if len(t) > 33:
            t = t[:30] + '…'
        return t

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
        if md.stem == 'index': continue
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
        # if it looks like a date-slug strip the date
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


# ── Canvas ────────────────────────────────────────────────────────────────────
class Canvas:
    def __init__(self, cols=COLS, rows=ROWS):
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
        for i in range(n): self.put(x + i, y, c, fc)

    def vline(self, x, y, n, c, fc=None):
        for i in range(n): self.put(x, y + i, c, fc)

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


# ── layout constants ──────────────────────────────────────────────────────────
# Left column: sessions/beginning  (x=1, w=37, right edge at x=37)
# Right column: concepts/gradient  (x=52, w=42, right edge at x=93)
# Connection zone: x=38 to x=51
LX, LW = 1, 37     # left node column
RX, RW = 52, 42    # right node column
SPINE_X = 19       # x of the vertical chronological spine
CONN_MID = 44      # x of midpoint of horizontal connectors

# Row positions (each node box h=5 to include a blank row inside)
NODE_H = 5

NODE_ROWS = {
    'beginning':                    3,
    'session-001-the-sharpening':   10,
    'session-002-the-event-horizon':17,
    'session-003-the-seam-strike':  24,
    # right column
    'diffusion-memory':             10,
    'stigmergy':                    17,
    'gradient-flow-without-competition': 24,
}

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

RIGHT_NODES = {'diffusion-memory', 'stigmergy', 'gradient-flow-without-competition'}

# ── rendering ─────────────────────────────────────────────────────────────────
def draw_node(cv, nid, node):
    color = NODE_TYPE_COLOR.get(node['type'], C_DIM)
    style = NODE_TYPE_STYLE.get(node['type'], 'single')
    glyph = NODE_TYPE_GLYPH.get(node['type'], '·')

    y = NODE_ROWS.get(nid)
    if y is None: return  # unknown node, skip

    x = RX if nid in RIGHT_NODES else LX
    w = RW if nid in RIGHT_NODES else LW

    cv.box(x, y, w, NODE_H, color, style)

    # type badge + title line
    label = node['label']
    badge = f"{glyph} {node['type'].upper()}"
    cv.txt(x+2, y+1, badge[:w-4],   fc=color)
    cv.txt(x+2, y+2, label[:w-4],   fc=C_HEAD)
    cv.txt(x+2, y+3, node['sub'][:w-4], fc=C_DIM)


def draw_spine(cv, n_sessions):
    """Draw the vertical chronological spine connecting beginning → sessions."""
    start_y = NODE_ROWS['beginning'] + NODE_H       # just below BEGINNING
    end_y   = NODE_ROWS['session-003-the-seam-strike']  # top of SESSION 003
    x = SPINE_X

    # vertical trunk
    cv.vline(x, start_y, end_y - start_y, '│', C_EDGE)

    # branch joints at each session row
    session_ids = [
        'session-001-the-sharpening',
        'session-002-the-event-horizon',
        'session-003-the-seam-strike',
    ]
    for sid in session_ids:
        sy = NODE_ROWS[sid]
        cv.put(x, sy - 1, '├', C_EDGE)   # junction
        cv.hline(x+1, sy-1, LX + LW - x - 2, '─', C_EDGE)
        # arrowhead just before box left edge
        cv.put(LX + LW - 1, sy - 1, '▶', C_EDGE)

    # bottom cap
    cv.put(x, end_y, '└', C_EDGE)

    # top connection from BEGINNING
    beg_y = NODE_ROWS['beginning']
    cv.put(LX + LW//2, beg_y + NODE_H - 1, '┴', C_EDGE)
    cv.hline(LX + LW//2 + 1, beg_y + NODE_H - 1, x - LX - LW//2 - 1, '─', C_EDGE)
    cv.put(x, beg_y + NODE_H - 1, '┐', C_EDGE)


def draw_h_connector(cv, left_y_row, right_y_row, left_x_end, right_x_start, color=C_EDGE):
    """Draw a horizontal (or L-shaped) connector between left and right columns."""
    mid_y_l = left_y_row  + NODE_H // 2
    mid_y_r = right_y_row + NODE_H // 2

    lx = left_x_end
    rx = right_x_start - 1

    if mid_y_l == mid_y_r:
        # straight horizontal
        cv.hline(lx, mid_y_l, rx - lx, '─', color)
        cv.put(rx, mid_y_l, '▶', color)
    else:
        # L-shape: go right then up/down
        turn_x = CONN_MID
        cy = mid_y_l
        ty = mid_y_r
        # horizontal from left node to turn point
        cv.hline(lx, cy, turn_x - lx, '─', color)
        # vertical from cy to ty at turn_x
        if ty < cy:
            cv.vline(turn_x, ty, cy - ty, '│', color)
            cv.put(turn_x, ty, '┬', color)
            cv.put(turn_x, cy, '└', color)
        else:
            cv.vline(turn_x, cy, ty - cy + 1, '│', color)
            cv.put(turn_x, cy, '┌', color)
            cv.put(turn_x, ty, '└', color)
        # horizontal from turn point to right node
        cv.hline(turn_x+1, ty, rx - turn_x - 1, '─', color)
        cv.put(rx, ty, '▶', color)


def draw_legend(cv, n_nodes, n_edges):
    """Draw type legend and metadata at the bottom."""
    y = 33
    cv.txt(2, y, "node types", fc=C_DIM)
    cx = 14
    for t, color, glyph in [
        ('beginning', C_BEGIN,   '◈'),
        ('session',   C_SESSION, '◆'),
        ('aesthetic', C_GRAD,    '◉'),
        ('concept',   C_CONCEPT, '◇'),
    ]:
        cv.txt(cx, y, f"{glyph} {t}", fc=color)
        cx += len(t) + 5

    y = 34
    cv.txt(2, y, f"nodes: {n_nodes}   edges: {n_edges}   auto-rendered on commit", fc=C_DIM)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M')
    cv.txt(COLS - len(ts) - 2, y, ts, fc=C_TICK)

    # horizontal rule
    cv.hline(1, 32, COLS - 2, '─', C_TICK)


def render(nodes, edges, print_ansi=False):
    cv = Canvas()

    # ── outer chrome ──────────────────────────────────────────────────────────
    cv.box(0, 0, COLS, ROWS, C_FRAME, 'double')

    # header text
    header = "KNOWLEDGE GRAPH  //  TERMINAL-ART"
    cv.txt((COLS - len(header)) // 2, 0, header, fc=C_HEAD)
    cv.txt(2, 1, "commit-driven topology · rendered on post-commit · nodes link through [[related]] frontmatter", fc=C_DIM)

    # decorative scanlines
    for y in range(3, ROWS - 2, 6):
        cv.hline(1, y, COLS - 2, '·', fc=C_TICK)

    # ── nodes ─────────────────────────────────────────────────────────────────
    for nid, node in nodes.items():
        draw_node(cv, nid, node)

    # ── vertical chronological spine ──────────────────────────────────────────
    draw_spine(cv, n_sessions=3)

    # ── horizontal connectors (session → concept) ─────────────────────────────
    # S001 → DIFFUSION MEMORY  (same row, straight)
    draw_h_connector(cv,
        left_y_row  = NODE_ROWS['session-001-the-sharpening'],
        right_y_row = NODE_ROWS['diffusion-memory'],
        left_x_end  = LX + LW,
        right_x_start = RX,
        color = C_EDGE,
    )
    # S002 → STIGMERGY  (same row, straight)
    draw_h_connector(cv,
        left_y_row  = NODE_ROWS['session-002-the-event-horizon'],
        right_y_row = NODE_ROWS['stigmergy'],
        left_x_end  = LX + LW,
        right_x_start = RX,
        color = C_EDGE,
    )
    # S003 → DIFFUSION MEMORY  (different rows, L-shape)
    draw_h_connector(cv,
        left_y_row  = NODE_ROWS['session-003-the-seam-strike'],
        right_y_row = NODE_ROWS['diffusion-memory'],
        left_x_end  = LX + LW,
        right_x_start = RX,
        color = C_TICK,
    )
    # S002 → DIFFUSION MEMORY  (different rows, L-shape)
    draw_h_connector(cv,
        left_y_row  = NODE_ROWS['session-002-the-event-horizon'],
        right_y_row = NODE_ROWS['diffusion-memory'],
        left_x_end  = LX + LW,
        right_x_start = RX,
        color = C_TICK,
    )
    # GRADIENT FLOW → STIGMERGY  (different rows on right, vertical internal)
    gf_y  = NODE_ROWS['gradient-flow-without-competition']
    st_y  = NODE_ROWS['stigmergy']
    gx    = RX + RW // 2
    # draw a right-column vertical link
    cv.vline(gx, st_y + NODE_H, gf_y - st_y - NODE_H, '┆', fc=C_DIM)
    cv.put(gx, st_y + NODE_H - 1, '▼', fc=C_DIM)

    # ── legend and metadata ───────────────────────────────────────────────────
    draw_legend(cv, len(nodes), len(edges))

    # ── sub-header labels ─────────────────────────────────────────────────────
    cv.txt(LX + 1, 8, "chronological spine", fc=C_DIM)
    cv.txt(RX + 1, 8, "concept space", fc=C_DIM)
    # separator
    cv.vline(49, 8, 24, '┆', fc=C_TICK)

    ansi = cv.to_ansi()
    if print_ansi:
        print(ansi)
    return ansi


# ── .ans file writer ─────────────────────────────────────────────────────────
HEADER_TEMPLATE = """\
# title: Knowledge Graph — terminal-art
# cols: {cols}
# rows: {rows}
# fontsize: 13
# date: {date}
# description: Post-commit knowledge graph. Nodes = posts + concepts, edges = related frontmatter.
"""

def save(ansi, path=OUT):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    header = HEADER_TEMPLATE.format(
        cols=COLS,
        rows=ROWS,
        date=datetime.now().strftime('%Y-%m-%d'),
    )
    path.write_text(header + "\n" + ansi, encoding='utf-8')
    print(f"[graph_viz] wrote {path.stat().st_size:,} bytes → {path}", file=sys.stderr)


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Render knowledge graph as ANSI capture")
    parser.add_argument('--print', action='store_true', help='Also dump raw ANSI to stdout')
    parser.add_argument('--out', default=str(OUT), help='Output .ans file path')
    args = parser.parse_args()

    nodes, edges = build_graph()
    ansi = render(nodes, edges, print_ansi=args.print)
    save(ansi, path=args.out)

    n, e = len(nodes), len(edges)
    print(f"[graph_viz] {n} nodes, {e} edges", file=sys.stderr)


if __name__ == '__main__':
    main()
