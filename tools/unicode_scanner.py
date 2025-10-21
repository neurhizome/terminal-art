#!/usr/bin/env python3
# unicode_glyph_scanner.py (v1.0.1)
# Scan a Unicode range and write JSON: "U+XXXX" -> "glyph" that likely renders.
import argparse, json, sys, unicodedata

try:
    from wcwidth import wcwidth, wcswidth  # type: ignore
except Exception:
    def wcwidth(ch: str) -> int:
        cat = unicodedata.category(ch)
        if cat[0] in ('C','Z') or unicodedata.combining(ch):
            return 0
        return 1
    def wcswidth(s: str) -> int:
        return sum(wcwidth(c) for c in s)

DOT = '\u25CC'  # dotted circle for combining marks preview

def hexint(s: str) -> int:
    s = s.strip().lower()
    return int(s, 16) if s.startswith('0x') else int(s)

def is_surrogate(cp: int) -> bool:
    return 0xD800 <= cp <= 0xDFFF

def main():
    ap = argparse.ArgumentParser(description="Scan Unicode and write JSON: U+XXXX -> glyph")
    ap.add_argument("--start", default="0x0000", help="Start codepoint (int or 0xHEX)")
    ap.add_argument("--end",   default="0x2FFFF", help="End codepoint inclusive (int or 0xHEX)")
    ap.add_argument("--outfile", default="glyphs_visible.json", help="Output JSON filename")
    ap.add_argument("--include-space", action="store_true", help="Include spaces/separators (Z*)")
    ap.add_argument("--include-private-use", action="store_true", help="Include Private Use Area (Co) like Nerd Font icons")
    ap.add_argument("--include-combining", action="store_true", help="Include combining marks (Mn/Mc/Me) rendered as ◌ + mark")
    ap.add_argument("--no-name-check", dest="no_name_check", action="store_true",
                    help="Skip unicodedata.name() existence check (faster, includes unassigned Cn except non-PUA)")
    ap.add_argument("--progress", type=int, default=4096, help="Progress update interval (codepoints)")
    args = ap.parse_args()

    start = hexint(args.start)
    end   = hexint(args.end)

    if start < 0 or end > 0x10FFFF or end < start:
        print("Invalid range.", file=sys.stderr)
        sys.exit(2)

    out = {}
    tested = kept = 0

    for cp in range(start, end + 1):
        tested += 1
        if is_surrogate(cp):
            continue

        ch = chr(cp)
        cat = unicodedata.category(ch)  # e.g. 'Lu', 'Mn', 'Zs', 'Co', 'Cc'

        if not args.include_space and cat[0] == 'Z':
            continue
        if cat in ('Cc','Cf','Cs'):  # control/format/surrogate
            continue
        if cat == 'Co' and not args.include_private_use:
            continue
        if ch == '\uFFFD':
            continue

        # combining handling
        if cat[0] == 'M':
            if not args.include_combining:
                continue
            display = DOT + ch
        else:
            display = ch

        # width must be > 0
        if wcswidth(display) <= 0:
            continue

        # optional name check to filter unassigned Cn (except PUA when requested)
        if not args.no_name_check:
            try:
                _ = unicodedata.name(ch)
            except ValueError:
                if cat != 'Co':
                    continue

        out[f"U+{cp:04X}"] = display
        kept += 1

        if args.progress and (tested % args.progress == 0):
            pct = 100.0 * (cp - start) / max(1, (end - start))
            print(f"\rScanned U+{cp:04X}  tested={tested} kept={kept}  ({pct:5.1f}%)", end="", flush=True)

    print(f"\nDone. Tested {tested}, kept {kept}. Writing {args.outfile} ...")
    with open(args.outfile, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote {args.outfile}")

if __name__ == "__main__":
    main()
