# CYCLE.md — Development Workflow for asciicology

This document describes the branch conventions, session numbering rules, and
validation workflow that keep the blog coherent across multiple contributors
and AI-assisted sessions.

---

## The Recurring Failure Modes

These are the things that break repeatedly without a convention:

1. **Missing captures** — A blog post references `.ans` files in
   `docs/assets/captures/` that don't exist yet (or were never generated).
   The site builds fine; the page just shows a broken embed.

2. **Duplicate session numbers** — Two branches each write a "Session 006"
   post without knowing about each other.  They may both be correct, but
   only one can land in `main`.

3. **Broken related links** — A `related:` URL points to a post or concept
   that doesn't exist (wrong slug, typo, concept not written yet).

4. **Session numbering drift** — Sessions are numbered out of date order
   because a branch sat unmerged for a while.

All four are caught automatically by `tools/validate_blog.py` before any
push reaches `main`.

---

## Branch Conventions

### The three branch types

| Type | Pattern | Purpose |
|------|---------|---------|
| Published | `main` | The live blog.  All captures must exist.  Validate passes `--strict`. |
| Feature branch | `claude/<topic>-<session-id>` | One branch per AI session or experiment cluster.  Captures may be pending (warnings OK). |
| Manual branch | `exp/<slug>` | Human-initiated experiments outside AI sessions. |

**AI session branches** follow the naming pattern enforced by the agent
scaffold: `claude/<description>-<session-id>`.  The session-id suffix
(e.g. `YJuTg`) is the Claude session identifier, making branches unique
even when two sessions work on similar topics.

### One branch = one coherent chunk

A feature branch should contain:
- The new experiment script(s) in `experiments/`
- Any new/modified source files in `src/`
- The blog post(s) in `docs/_posts/`
- The actual `.ans` captures in `docs/assets/captures/`

A branch that contains a blog post but no corresponding captures is
**not ready to merge to main**.  The pre-push hook allows this for feature
branches (warning) but blocks it for main (error).

---

## Session Numbering

Session numbers are assigned at time of writing the blog post.  They must
be globally unique across **all** merged and in-flight branches.

### Claiming a number

```bash
# 1. See what numbers are already in main
git fetch origin main
git show origin/main:docs/_posts/ 2>/dev/null | grep -o "session-[0-9]\{3\}" | sort -u

# 2. Check in-flight branches too
python3 tools/validate_blog.py --branches

# 3. Take the next unused number
```

The `--branches` flag in the validator reads every remote branch's post
files via `git show origin/<branch>:docs/_posts/<file>` and reports any
session number that would collide with the current working tree.

### If a collision is discovered at merge time

The branch with the later creation date yields.  Renumber your session
and update:
- The post title and YAML frontmatter
- Any `related:` links in other posts that reference the old number

---

## Validation

### Running the validator

```bash
# Install dev deps once
pip install -r requirements-dev.txt

# On a feature branch (warnings allowed, errors block)
python3 tools/validate_blog.py

# Before merging to main (all warnings become errors)
python3 tools/validate_blog.py --strict --branches
```

### What it checks

| Check | Feature branch | Main |
|-------|---------------|------|
| Duplicate session numbers (local) | error | error |
| Duplicate session numbers (across branches) | — | error (`--branches`) |
| Missing capture files | **warning** | **error** (`--strict`) |
| Broken `related:` links | error | error |
| Session/date ordering anomalies | warning | warning |

### Installing the pre-push hook

The hook runs the validator automatically before every push:

```bash
cp scripts/hooks/pre-push .git/hooks/pre-push
chmod +x .git/hooks/pre-push
```

Once installed:
- Pushing to **any branch**: errors block, warnings pass
- Pushing to **main**: strict mode (`--strict --branches`); any issue blocks

The post-commit hook (knowledge graph rebuild) is separate:

```bash
cp scripts/hooks/post-commit .git/hooks/post-commit
chmod +x .git/hooks/post-commit
```

---

## The Publish Workflow

```
 ┌─────────────────────────────────────────────────────────────┐
 │  DEVELOP                                                     │
 │  Branch from main → write code → run experiment locally     │
 └────────────────────────┬────────────────────────────────────┘
                          │
 ┌────────────────────────▼────────────────────────────────────┐
 │  CAPTURE                                                     │
 │  python experiments/my_experiment.py --seed N               │
 │  Copy .ans files → docs/assets/captures/                    │
 └────────────────────────┬────────────────────────────────────┘
                          │
 ┌────────────────────────▼────────────────────────────────────┐
 │  WRITE                                                       │
 │  Create docs/_posts/YYYY-MM-DD-session-NNN-slug.md          │
 │  Add captures: and related: in YAML frontmatter             │
 └────────────────────────┬────────────────────────────────────┘
                          │
 ┌────────────────────────▼────────────────────────────────────┐
 │  VALIDATE (local)                                            │
 │  python3 tools/validate_blog.py                             │
 │  ✓ no errors → continue                                     │
 │  ✗ errors → fix before pushing                              │
 └────────────────────────┬────────────────────────────────────┘
                          │
 ┌────────────────────────▼────────────────────────────────────┐
 │  PUSH                                                        │
 │  git push origin claude/my-feature-XYZ                      │
 │  pre-push hook runs validator automatically                  │
 └────────────────────────┬────────────────────────────────────┘
                          │
 ┌────────────────────────▼────────────────────────────────────┐
 │  REVIEW                                                      │
 │  Open PR → read the post, verify captures display correctly  │
 │  Confirm session number doesn't collide with open PRs        │
 └────────────────────────┬────────────────────────────────────┘
                          │
 ┌────────────────────────▼────────────────────────────────────┐
 │  MERGE TO MAIN                                               │
 │  GitHub Actions: validate (--strict --branches) → build     │
 │                  → deploy                                    │
 │  post-commit hook: knowledge graph rebuilds automatically    │
 └─────────────────────────────────────────────────────────────┘
```

---

## Can an AI agent look across branches?

Yes.  The validator's `--branches` flag does exactly this: it runs
`git ls-tree` and `git show` against every remote branch to read post
files without checking them out.

A Claude session starting fresh can also do:

```bash
# What sessions exist in main right now?
git fetch origin main
git show origin/main:docs/_posts/ 2>/dev/null

# What session numbers are claimed across ALL remote branches?
python3 tools/validate_blog.py --branches
```

This is how a new session discovers the next safe session number to claim
before writing its first post.

---

## What "ready to merge" means

A branch is ready for main when:

```
python3 tools/validate_blog.py --strict --branches
```

exits with code 0.  That guarantees:
- No duplicate session numbers anywhere in the system
- Every capture referenced in every post actually exists on disk
- Every `related:` link resolves to a real post or concept
- The knowledge graph will rebuild cleanly on merge

Everything else is fair game — posts can be raw, code can be experimental,
ideas can be half-formed.  The only hard requirement is: if you say a
capture exists, it must exist.
