import json
import unicodedata
import sys

def is_printable(char: str) -> bool:
    """Heuristic check for printable glyphs."""""
    if char.isspace():
        return False  # skip whitespace
    if char in {'�', '\uFFFD'}:
        return False  # replacement characters
    try:
        name = unicodedata.name(char)
    except ValueError:
        return False  # unnamed = likely non-rendering
    return True

def try_render(char: str) -> bool:
    """Check if the terminal actually renders something."""""
    import subprocess
    try:
        result = subprocess.run(
            ['echo', char],
            capture_output=True,
            text=True

        )
        output = result.stdout.strip()
        return output not in ('', char.encode('utf-8',
                                              'replace').decode())
    except Exception:
        return False

    def scan_unicode(max_codepoint=0x2FFFF,
                     outfile="glyphs_visible.json"):
        visible = {}
        for codepoint in range(max_codepoint):
            try:
                char = chr(codepoint)
                if not is_printable(char):
                    continue
                print(f"\rTesting U+{codepoint:04X}: {char}",
                      end='',
                      flush=True)
                sys.stdout.flush()
                # crude
                # visibility
                # test:
                # is
                # it
                # visible
                # and
                # not
                # tofu?
                if char != '\uFFFD' and char != '?' and try_render(char):
                    visible[f"U+{codepoint:04X}"] = char
            except Exception:
                continue

            print(f"\nFound {len(visible)} visible characters.")
            with open(outfile, "w", encoding="utf-8") as f:
                json.dump(visible, f, ensure_ascii=False,
                          indent=2)
                print(f"Saved to {outfile}")

        if __name__ == "__main__":
            scan_unicode()
