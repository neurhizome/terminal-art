
# Unicode Glyph Scanner (Terminal/Nerd Font)

This kit helps you build a JSON map of **what your terminal can actually render** with your current font setup (e.g., Nerd Font on iPhone/iSH/Termux/etc.).

## Files

- `unicode_glyph_scanner.py` — scans a Unicode range and writes `glyphs_visible.json` mapping `"U+XXXX" -> "glyph"`.
- `glyphs_viewer.py` — quick pager to browse the JSON in your terminal.

## Quick Start

```bash
# (optional) install wcwidth for better width detection
pip3 install wcwidth

# scan a focused, useful slice first (fast):
python3 unicode_glyph_scanner.py --start 0x2500 --end 0x259F --outfile glyphs_visible.json

# include Nerd Font private-use icons:
python3 unicode_glyph_scanner.py --start 0xE000 --end 0xF8FF --include-private-use --outfile glyphs_nerdfont.json

# full sweep (slow — consider doing it in chunks):
python3 unicode_glyph_scanner.py --start 0x0000 --end 0x10FFFF --include-private-use --outfile glyphs_all.json
```

### Options

- `--include-private-use` : include PUA (Nerd Font icons live here).
- `--include-combining`   : include combining marks (rendered as `◌` + mark).
- `--include-space`       : include spaces/separators (normally skipped).
- `--no-name-check`       : faster; skips `unicodedata.name()` existence check.
- `--progress N`          : progress message every N codepoints.

### View the results

```bash
python3 glyphs_viewer.py glyphs_visible.json --page-size 160
```

### Handy Ranges

- Box Drawing:       `0x2500..0x257F`
- Block Elements:    `0x2580..0x259F`
- Braille Patterns:  `0x2800..0x28FF`
- Geometric Shapes:  `0x25A0..0x25FF`
- Arrows:            `0x2190..0x21FF`
- Misc Symbols:      `0x2600..0x26FF`
- Dingbats:          `0x2700..0x27BF`
- Nerd PUA:          `0xE000..0xF8FF` (use `--include-private-use`)

Notes:
- Heuristic only: some tofu may slip through depending on terminal fallback.
- Combining marks are shown with dotted-circle so you can see them; omit via flag if undesired.
- For massive scans, run in blocks and merge JSON later.
