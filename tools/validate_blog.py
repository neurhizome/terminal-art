#!/usr/bin/env python3
"""
validate_blog.py — Pre-publish integrity checker for the asciicology blog.

Catches common failure modes before they reach the deployed site:

    1. Duplicate session numbers across all posts (and optionally remote branches)
    2. Missing capture files  — every `file:` in `captures:` must exist on disk
    3. Broken related links   — every `url:` in `related:` must resolve to a
                                known post or concept (no dead links)
    4. Date / session ordering — session numbers should increase with date

Usage:
    python3 tools/validate_blog.py               # warn mode (draft branches)
    python3 tools/validate_blog.py --strict      # error on any issue (pre-merge)
    python3 tools/validate_blog.py --branches    # also scan remote branches for
                                                 # session number collisions
    python3 tools/validate_blog.py --fix         # suggest fixes inline

Exit codes:
    0  — no errors (warnings may be present)
    1  — one or more errors found
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:
    sys.exit(
        "ERROR: PyYAML is required.  Install with:  pip install pyyaml\n"
        "  (or:  pip install -r requirements-dev.txt)"
    )

# ── paths ─────────────────────────────────────────────────────────────────────

ROOT      = Path(__file__).parent.parent
POSTS_DIR = ROOT / "docs" / "_posts"
CONCEPTS_DIR = ROOT / "docs" / "concepts"
CAPTURES_DIR = ROOT / "docs" / "assets" / "captures"

# ── ANSI helpers ──────────────────────────────────────────────────────────────

RESET = "\033[0m"
BOLD  = "\033[1m"
RED   = "\033[31m"
YEL   = "\033[33m"
GRN   = "\033[32m"
CYN   = "\033[36m"
DIM   = "\033[2m"


def _c(color, text):
    return f"{color}{text}{RESET}"


# ── data model ────────────────────────────────────────────────────────────────

@dataclass
class Post:
    path:    Path
    slug:    str       # filename without date and .md
    date:    str       # YYYY-MM-DD from filename
    title:   str
    session: Optional[int]          # None for unnumbered posts
    captures: list[str]             # list of filenames from captures: blocks
    related_urls: list[str]         # list of url: strings from related: blocks
    raw_fm:  dict = field(default_factory=dict)


@dataclass
class Issue:
    severity: str   # "error" | "warning"
    post:     Path
    message:  str


# ── frontmatter parser ────────────────────────────────────────────────────────

_FM_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def parse_frontmatter(path: Path) -> Optional[dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    m = _FM_RE.match(text)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        print(_c(YEL, f"  YAML parse error in {path.name}: {e}"))
        return None


def _session_from_title(title: str) -> Optional[int]:
    """Extract session number from 'Session 006: ...' style titles."""
    m = re.search(r"\bSession\s+(\d+)\b", title, re.IGNORECASE)
    return int(m.group(1)) if m else None


def load_posts(directory: Path) -> list[Post]:
    posts = []
    for p in sorted(directory.glob("*.md")):
        name = p.stem   # e.g. 2026-02-23-session-006-the-seam-as-comma
        parts = name.split("-", 3)
        if len(parts) < 4:
            date_str = "-".join(parts[:3]) if len(parts) >= 3 else "0000-00-00"
            slug = parts[-1] if len(parts) > 3 else name
        else:
            date_str = f"{parts[0]}-{parts[1]}-{parts[2]}"
            slug = parts[3]

        fm = parse_frontmatter(p)
        if fm is None:
            continue

        title = fm.get("title", "")
        session = _session_from_title(title)

        captures = []
        for cap in fm.get("captures", []) or []:
            if isinstance(cap, dict) and "file" in cap:
                captures.append(cap["file"])

        related_urls = []
        for rel in fm.get("related", []) or []:
            if isinstance(rel, dict) and "url" in rel:
                related_urls.append(rel["url"])

        posts.append(Post(
            path=p, slug=slug, date=date_str, title=title,
            session=session, captures=captures,
            related_urls=related_urls, raw_fm=fm,
        ))
    return posts


# ── URL resolver ──────────────────────────────────────────────────────────────

def build_url_map(posts: list[Post], concepts_dir: Path) -> set[str]:
    """
    Return all Jekyll URLs that exist in the repo.

    Post  2026-02-19-session-001-the-sharpening.md
          → /2026/02/19/session-001-the-sharpening.html

    Concept  docs/concepts/stigmergy.md  with  permalink: /concepts/stigmergy/
             → /concepts/stigmergy/
    """
    known: set[str] = set()

    # Posts: derive Jekyll URL from filename
    for post in posts:
        parts = post.date.split("-")
        if len(parts) == 3:
            url = f"/{parts[0]}/{parts[1]}/{parts[2]}/{post.slug}.html"
            known.add(url)

    # Concepts: read permalink from frontmatter
    for p in concepts_dir.glob("*.md"):
        fm = parse_frontmatter(p)
        if fm and "permalink" in fm:
            known.add(fm["permalink"])

    # Common static pages referenced in posts
    known.update({"/graph/", "/palette/", "/concepts/"})

    return known


# ── remote branch scanner ─────────────────────────────────────────────────────

def scan_remote_branches(current_posts: list[Post]) -> list[Issue]:
    """
    Look at all remote branches for session numbers that would collide with
    the current working tree's sessions.
    """
    issues = []
    current_sessions = {p.session: p for p in current_posts if p.session}

    try:
        result = subprocess.run(
            ["git", "branch", "-r"],
            capture_output=True, text=True, cwd=ROOT
        )
        branches = [b.strip() for b in result.stdout.splitlines()]
        branches = [b for b in branches if b and "->" not in b]
    except Exception:
        return []

    _FM_RE_B = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

    for branch in branches:
        try:
            ls = subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", branch, "--", "docs/_posts/"],
                capture_output=True, text=True, cwd=ROOT
            )
            for fname in ls.stdout.splitlines():
                fpath = fname.strip()
                if not fpath.endswith(".md"):
                    continue
                raw = subprocess.run(
                    ["git", "show", f"{branch}:{fpath}"],
                    capture_output=True, text=True, cwd=ROOT
                )
                m = _FM_RE_B.match(raw.stdout)
                if not m:
                    continue
                try:
                    fm = yaml.safe_load(m.group(1))
                except Exception:
                    continue
                if not fm:
                    continue
                title = fm.get("title", "")
                sess = _session_from_title(title)
                if sess and sess in current_sessions:
                    local_post = current_sessions[sess]
                    remote_title = title
                    if local_post.title != remote_title:
                        issues.append(Issue(
                            severity="error",
                            post=local_post.path,
                            message=(
                                f"Session {sess:03d} also claimed by "
                                f"{branch}:{fpath} "
                                f'("{remote_title}")'
                            ),
                        ))
        except Exception:
            continue

    return issues


# ── validators ────────────────────────────────────────────────────────────────

def check_duplicate_sessions(posts: list[Post]) -> list[Issue]:
    seen: dict[int, Post] = {}
    issues = []
    for post in posts:
        if post.session is None:
            continue
        if post.session in seen:
            issues.append(Issue(
                severity="error",
                post=post.path,
                message=(
                    f"Session {post.session:03d} is already used by "
                    f"{seen[post.session].path.name}"
                ),
            ))
        else:
            seen[post.session] = post
    return issues


def check_captures(posts: list[Post], strict: bool) -> list[Issue]:
    issues = []
    for post in posts:
        for cap_file in post.captures:
            target = CAPTURES_DIR / cap_file
            if not target.exists():
                issues.append(Issue(
                    severity="error" if strict else "warning",
                    post=post.path,
                    message=f"Missing capture: docs/assets/captures/{cap_file}",
                ))
    return issues


def check_related_links(posts: list[Post], url_map: set[str]) -> list[Issue]:
    issues = []
    for post in posts:
        for url in post.related_urls:
            # Skip absolute external URLs
            if url.startswith("http://") or url.startswith("https://"):
                continue
            if url not in url_map:
                issues.append(Issue(
                    severity="error",
                    post=post.path,
                    message=f"Broken related link: {url}",
                ))
    return issues


def check_session_ordering(posts: list[Post]) -> list[Issue]:
    """
    Session numbers should increase monotonically with post date.
    Warn (don't error) if they don't — unnumbered posts between sessions are fine.
    """
    issues = []
    numbered = [(p.date, p.session, p) for p in posts if p.session is not None]
    numbered.sort(key=lambda x: (x[0], x[1]))

    for i in range(1, len(numbered)):
        prev_date, prev_sess, prev_post = numbered[i - 1]
        curr_date, curr_sess, curr_post = numbered[i]
        if curr_date < prev_date and curr_sess > prev_sess:
            issues.append(Issue(
                severity="warning",
                post=curr_post.path,
                message=(
                    f"Session {curr_sess:03d} ({curr_date}) is later than "
                    f"Session {prev_sess:03d} ({prev_date}) but has an earlier date"
                ),
            ))
    return issues


# ── reporter ──────────────────────────────────────────────────────────────────

def report(issues: list[Issue], posts: list[Post]) -> int:
    """Print formatted report.  Returns exit code (0=ok, 1=errors)."""

    errors   = [i for i in issues if i.severity == "error"]
    warnings = [i for i in issues if i.severity == "warning"]

    # ── session table ──────────────────────────────────────────────────────
    print()
    print(_c(BOLD, "Sessions found:"))
    numbered = sorted(
        [p for p in posts if p.session is not None],
        key=lambda p: p.session
    )
    unnamed  = [p for p in posts if p.session is None]

    for p in numbered:
        cap_count = len(p.captures)
        cap_ok = all((CAPTURES_DIR / c).exists() for c in p.captures)
        cap_icon = _c(GRN, "✓") if cap_ok else _c(RED, "✗")
        print(
            f"  Session {p.session:03d}  {p.date}  "
            f"{cap_icon} {cap_count} cap{'s' if cap_count != 1 else ''}  "
            f"{_c(DIM, p.path.name)}"
        )
    if unnamed:
        print(_c(DIM, f"  + {len(unnamed)} unnumbered post(s)"))

    # ── issues ────────────────────────────────────────────────────────────
    if issues:
        print()
        for issue in sorted(issues, key=lambda i: (i.severity, str(i.post))):
            icon  = _c(RED, "ERROR  ") if issue.severity == "error" else _c(YEL, "WARNING")
            fname = issue.post.name
            print(f"  {icon}  {_c(DIM, fname)}")
            print(f"           {issue.message}")

    # ── summary ───────────────────────────────────────────────────────────
    print()
    if not issues:
        print(_c(GRN, "  All checks passed.") + f"  ({len(posts)} posts, {len(numbered)} sessions)")
        return 0

    parts = []
    if errors:
        parts.append(_c(RED, f"{len(errors)} error{'s' if len(errors) != 1 else ''}"))
    if warnings:
        parts.append(_c(YEL, f"{len(warnings)} warning{'s' if len(warnings) != 1 else ''}"))
    print("  " + ", ".join(parts))

    return 1 if errors else 0


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Validate blog post integrity before publishing."
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (required before merging to main).",
    )
    parser.add_argument(
        "--branches",
        action="store_true",
        help="Also scan remote git branches for session number collisions.",
    )
    args = parser.parse_args()

    print(_c(BOLD + CYN, "\n  asciicology blog validator"))
    print(_c(DIM, f"  posts: {POSTS_DIR}"))
    print(_c(DIM, f"  captures: {CAPTURES_DIR}"))

    posts    = load_posts(POSTS_DIR)
    url_map  = build_url_map(posts, CONCEPTS_DIR)

    issues: list[Issue] = []
    issues += check_duplicate_sessions(posts)
    issues += check_captures(posts, strict=args.strict)
    issues += check_related_links(posts, url_map)
    issues += check_session_ordering(posts)

    if args.branches:
        print(_c(DIM, "  scanning remote branches for session collisions..."))
        issues += scan_remote_branches(posts)

    if args.strict:
        # Promote all warnings to errors
        for issue in issues:
            if issue.severity == "warning":
                issue.severity = "error"

    exit_code = report(issues, posts)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
