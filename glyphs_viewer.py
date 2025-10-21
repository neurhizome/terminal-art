#!/usr/bin/env python3
# glyphs_viewer.py
import argparse, json, math

def main():
    ap = argparse.ArgumentParser(description="View glyph JSON in pages")
    ap.add_argument("json_path")
    ap.add_argument("--page-size", type=int, default=128)
    args = ap.parse_args()

    with open(args.json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = sorted(data.items(), key=lambda kv: int(kv[0][2:], 16))

    n = len(items)
    page = 0
    pages = max(1, (n + args.page_size - 1) // args.page_size)

    while True:
        start = page * args.page_size
        end = min(n, start + args.page_size)
        print(f"\nPage {page+1}/{pages}  {start}..{end-1} of {n}   [n]ext [p]rev [g HEX]oto [q]uit")

        cols = 8
        height = (end - start + cols - 1) // cols
        for r in range(height):
            line = []
            for c in range(cols):
                i = start + r + c * height
                if i < end:
                    code, glyph = items[i]
                    cell = f"{code:>7} {glyph}"
                else:
                    cell = ""
                line.append(cell.ljust(12))
            print("  ".join(line))

        cmd = input("> ").strip()
        if cmd == "q":
            break
        elif cmd == "n":
            page = (page + 1) % pages
        elif cmd == "p":
            page = (page - 1 + pages) % pages
        elif cmd.startswith("g "):
            try:
                hx = cmd.split()[1].upper()
                if not hx.startswith("U+"):
                    hx = "U+" + hx
                target = int(hx[2:], 16)
                # find nearest index
                lo, hi = 0, n-1; best = 0
                while lo <= hi:
                    mid = (lo + hi)//2
                    midcp = int(items[mid][0][2:], 16)
                    if midcp < target:
                        best = mid; lo = mid + 1
                    elif midcp > target:
                        hi = mid - 1
                    else:
                        best = mid; break
                page = best // args.page_size
            except Exception:
                print("Usage: g U+2588  or  g 2588")
        else:
            print("Commands: n, p, g HEX, q")

if __name__ == "__main__":
    main()
