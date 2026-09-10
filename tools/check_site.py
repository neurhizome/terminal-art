#!/usr/bin/env python3
"""Check actual Jekyll output, including historical .html redirect pages.

python3 tools/check_site.py docs/_site --baseurl /terminal-art
External resources and fragment anchors are outside this local-file check.
"""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value and key in ("href", "src"):
                self.urls.append(value)


def check(root, baseurl):
    root = root.resolve()
    errors = []
    pages = sorted(root.rglob("*.html"))
    if not (root / "index.html").is_file():
        errors.append("Missing index.html: build the site first")
    for page in pages:
        parser = References()
        parser.feed(page.read_text(encoding="utf-8"))
        for raw in parser.urls:
            url = urlsplit(raw)
            if url.scheme or url.netloc or not url.path:
                continue
            path = unquote(url.path)
            if path.startswith('/'):
                if baseurl and path != baseurl and not path.startswith(baseurl + '/'):
                    errors.append(f"{page.relative_to(root)}: outside baseurl: {raw}")
                    continue
                target = root / path[len(baseurl):].lstrip('/')
            else:
                target = page.parent / path
            target = target.resolve()
            if not target.is_relative_to(root):
                errors.append(f"{page.relative_to(root)}: outside site: {raw}")
                continue
            if target.is_dir():
                target = target / 'index.html'
            if not target.is_file():
                errors.append(f"{page.relative_to(root)}: missing: {raw}")
    return pages, sorted(set(errors))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('site', type=Path)
    parser.add_argument('--baseurl', default='/terminal-art')
    args = parser.parse_args()
    pages, errors = check(args.site, args.baseurl.rstrip('/'))
    for error in errors:
        print(error)
    print(f"Checked {len(pages)} HTML pages; {len(errors)} broken local references")
    raise SystemExit(bool(errors))
