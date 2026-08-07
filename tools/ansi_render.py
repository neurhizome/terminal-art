#!/usr/bin/env python3
"""Render ANSI text — a still or a whole animation — to PNG / MP4 / GIF.

The blog's native format is coloured terminal text, which is perfect in a
terminal and invisible everywhere else. Anything that wants to *show* a piece
— a gallery that takes rasters, a phone, a README, a video — needs it turned
into pixels. This is that turn.

Two jobs, one parser:

    ansi_render.py plate.ans -o plate.png            # still
    ansi_render.py --frames dir/ -o burn.mp4 --fps 12  # animation

Supports the SGR subset this repo actually emits: reset, 256-colour
foreground/background (38;5;N / 48;5;N), the 8+8 basic colours, and bold.
Unknown codes are skipped rather than crashing, because a renderer that dies
on an unfamiliar escape is useless against real captures.

Requires Pillow. MP4/GIF output shells out to ffmpeg.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    print("needs Pillow:  pip install pillow", file=sys.stderr)
    raise SystemExit(1)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf",
]
BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansMono-Bold.ttf",
]

SGR = re.compile(r"\033\[([0-9;]*)m")
DEFAULT_FG = (200, 200, 200)
DEFAULT_BG = (12, 12, 16)


def xterm256(n: int) -> tuple[int, int, int]:
    """The standard xterm 256-colour cube."""
    if n < 16:
        base = [
            (0, 0, 0), (170, 0, 0), (0, 170, 0), (170, 85, 0),
            (0, 0, 170), (170, 0, 170), (0, 170, 170), (170, 170, 170),
            (85, 85, 85), (255, 85, 85), (85, 255, 85), (255, 255, 85),
            (85, 85, 255), (255, 85, 255), (85, 255, 255), (255, 255, 255),
        ]
        return base[n]
    if n < 232:
        n -= 16
        levels = [0, 95, 135, 175, 215, 255]
        return (levels[n // 36], levels[(n // 6) % 6], levels[n % 6])
    v = 8 + (n - 232) * 10
    return (v, v, v)


class Cell:
    __slots__ = ("ch", "fg", "bg", "bold")

    def __init__(self, ch: str, fg, bg, bold: bool):
        self.ch, self.fg, self.bg, self.bold = ch, fg, bg, bold


def parse(text: str) -> list[list[Cell]]:
    """ANSI string -> grid of cells. Tabs expand; other control chars drop."""
    fg, bg, bold = DEFAULT_FG, DEFAULT_BG, False
    rows: list[list[Cell]] = []
    for raw_line in text.replace("\t", "    ").split("\n"):
        row: list[Cell] = []
        pos = 0
        for m in SGR.finditer(raw_line):
            for ch in raw_line[pos:m.start()]:
                if ch.isprintable():
                    row.append(Cell(ch, fg, bg, bold))
            codes = [c for c in m.group(1).split(";") if c != ""] or ["0"]
            i = 0
            while i < len(codes):
                c = int(codes[i])
                if c == 0:
                    fg, bg, bold = DEFAULT_FG, DEFAULT_BG, False
                elif c == 1:
                    bold = True
                elif c == 22:
                    bold = False
                elif c == 39:
                    fg = DEFAULT_FG
                elif c == 49:
                    bg = DEFAULT_BG
                elif 30 <= c <= 37:
                    fg = xterm256(c - 30)
                elif 90 <= c <= 97:
                    fg = xterm256(c - 90 + 8)
                elif 40 <= c <= 47:
                    bg = xterm256(c - 40)
                elif 100 <= c <= 107:
                    bg = xterm256(c - 100 + 8)
                elif c in (38, 48) and i + 2 < len(codes) and codes[i + 1] == "5":
                    colour = xterm256(int(codes[i + 2]))
                    if c == 38:
                        fg = colour
                    else:
                        bg = colour
                    i += 2
                i += 1
            pos = m.end()
        for ch in raw_line[pos:]:
            if ch.isprintable():
                row.append(Cell(ch, fg, bg, bold))
        rows.append(row)
    return rows


def _font(paths: list[str], size: int):
    for p in paths:
        if Path(p).is_file():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def render(text: str, *, size: int = 20, pad: int = 24,
           cols: int | None = None, rows_n: int | None = None) -> Image.Image:
    grid = parse(text)
    regular = _font(FONT_CANDIDATES, size)
    bold = _font(BOLD_CANDIDATES, size)

    # Cell metrics from the font itself — a wrong advance width shears the
    # whole image, and box-drawing glyphs make that instantly obvious.
    bbox = regular.getbbox("M")
    cw = int(regular.getlength("M"))
    ch = int((bbox[3] - bbox[1]) * 1.65) or size
    width_cells = cols or max([len(r) for r in grid] or [1])
    height_cells = rows_n or len(grid)

    img = Image.new("RGB", (width_cells * cw + pad * 2,
                            height_cells * ch + pad * 2), DEFAULT_BG)
    d = ImageDraw.Draw(img)
    for y, row in enumerate(grid[:height_cells]):
        for x, cell in enumerate(row[:width_cells]):
            px, py = pad + x * cw, pad + y * ch
            if cell.bg != DEFAULT_BG:
                d.rectangle([px, py, px + cw, py + ch], fill=cell.bg)
            if cell.ch != " ":
                d.text((px, py), cell.ch, font=bold if cell.bold else regular,
                       fill=cell.fg)
    return img


def animate(frame_dir: Path, out: Path, fps: int, size: int) -> int:
    frames = sorted(p for p in frame_dir.iterdir()
                    if p.suffix in {".ans", ".txt"})
    if not frames:
        print(f"no .ans/.txt frames in {frame_dir}", file=sys.stderr)
        return 1
    if not shutil.which("ffmpeg"):
        print("ffmpeg not found", file=sys.stderr)
        return 1

    # Every frame must share one canvas or the encoder rejects the sequence,
    # so measure the whole set first and pad the rest to the largest.
    grids = [parse(p.read_text(encoding="utf-8", errors="replace")) for p in frames]
    cols = max(max((len(r) for r in g), default=0) for g in grids)
    rows_n = max(len(g) for g in grids)
    print(f"{len(frames)} frames · {cols}x{rows_n} cells · {fps} fps")

    with tempfile.TemporaryDirectory() as tmp:
        for i, p in enumerate(frames):
            img = render(p.read_text(encoding="utf-8", errors="replace"),
                         size=size, cols=cols, rows_n=rows_n)
            img.save(Path(tmp) / f"f{i:05d}.png")
        vf = "pad=ceil(iw/2)*2:ceil(ih/2)*2"
        cmd = ["ffmpeg", "-y", "-framerate", str(fps),
               "-i", str(Path(tmp) / "f%05d.png")]
        if out.suffix == ".gif":
            cmd += ["-vf", f"{vf},split[a][b];[a]palettegen[p];[b][p]paletteuse"]
        else:
            cmd += ["-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "18"]
        cmd.append(str(out))
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stderr[-1500:], file=sys.stderr)
            return r.returncode
    print(f"wrote {out}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", nargs="?", help=".ans/.txt file (still mode)")
    p.add_argument("--frames", type=Path, help="directory of frames (animation)")
    p.add_argument("-o", "--out", type=Path, required=True)
    p.add_argument("--size", type=int, default=20, help="font pixel size")
    p.add_argument("--fps", type=int, default=12)
    a = p.parse_args()

    if a.frames:
        return animate(a.frames, a.out, a.fps, a.size)
    if not a.source:
        p.error("need a source file or --frames")
    img = render(Path(a.source).read_text(encoding="utf-8", errors="replace"),
                 size=a.size)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    img.save(a.out)
    print(f"wrote {a.out}  ({img.width}x{img.height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
