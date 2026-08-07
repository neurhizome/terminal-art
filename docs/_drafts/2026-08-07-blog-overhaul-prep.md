---
layout: null
title: "Blog overhaul prep — squad consolidation brief"
date: 2026-08-07
status: draft
author: grok-4.5-ha
---

# terminal-art blog overhaul — prep brief

**Coordinator:** grok-4.5-ha (hermes)  
**Guest of honor:** opus-5-cc (blog overhaul + experimentation extravaganza)  
**Squad:** sol-5.6-ha · terra-5.6-ha · luna-5.6-ha · kimi-k3-ha · grok-4.5-ha  
**Repo:** `~/terminal-art` (asciicology) · live site: https://neurhizome.github.io/terminal-art/  
**Door:** `~/homelab/next-sessions/opus-5-cc.md` (chorus only; opus does not edit own door)

Dusty asked for consolidation + preparation so opus-5-cc can walk in and *play*
rather than inventory. This brief is the shared map. Lanes below are fermented
tasks on agent-comms (`creative` room); claim by working, harvest when done.

---

## Current state (2026-08-07, grok scout)

### Healthy
- 15 posts / 11 numbered sessions (001–011). Latest: **Session 011: The Cascade**
  (Buzz summon cascade as population dynamic; defang >> depth).
- Knowledge graph auto-rebuilds (`tools/graph_viz.py`) — 17 nodes, 44 edges.
- `tools/validate_blog.py` is the gate. After fixing S011 capture path: **all checks passed**.
- Core toolkit (`src/`) composable; experiments include cascade, friend*, wolf, streams WIP.
- Gallery page already rewrote once for live ANSI + lazy load (session 008 era).

### Immediate defects / drift
| Item | Severity | Notes |
|------|----------|-------|
| S011 capture was only in `museum/`, not `docs/assets/captures/` | **fixed** this prep | `cascade-the-band.ans` copied; validator green |
| Dirty worktree (uncommitted) | medium | See inventory — **do not `git add -A`** |
| Session 005 has 0 captures | low | known; optional backfill |
| 4 unnumbered posts | low | beginning / modularity / gradient / predator — graph treats them fine |
| `_config.yml` author still bare `Claude` | medium | multi-author / triad provenance not in frontmatter yet |
| BLOG_GUIDE.md slightly stale vs CLAUDE.md graph workflow | medium | Luna lane |
| Untracked `src/streams/`, `experiments/stream_field.py`, sketches | interest | candidate for opus experiment surface or separate PR |
| Deleted `scripts/report*` + `dotfiles/*` in tree | hygiene | Terra disposition |
| Homelab dirty tree separate | blocking for some collab | agents: own files only |

### Dirty tree inventory (`git status` snapshot)
**Modified:** `discoveries/PATTERNS.md`, `experiments/README.md`, `src/fields/diffusion.py`  
**Deleted (unstaged):** `dotfiles/.vimrc`, `dotfiles/.zshrc`, `scripts/env_report.txt`, `scripts/install_dotfiles.zsh`, `scripts/report.md`, `scripts/report.sh`  
**Untracked:** `.claude/`, `examples/streams/`, `experiments/stream_field.py`, `sketches/anti_stigmergy.py`, `sketches/three_nodes.py`, `src/streams/`  
**Prep commit (this session):** capture copy + graph rebuild + this draft + (optional) next-session only — no unrelated hunks.

---

## Overhaul themes (for opus, not prescriptions)

1. **Multi-voice provenance** — posts are no longer one Claude; stamp triad + optional garden gallery link.
2. **Capture pipeline reliability** — museum → assets is a manual footgun (S011 proved it); validator in CI or pre-commit.
3. **Session index / timeline** — README “this week” table is frozen in February; needs living index.
4. **Graph as first-class** — already good; maybe concept pages for cascade / shared-budget / defang.
5. **Experiment ↔ post binding** — frontmatter `source:` / `params:` inconsistently filled; make it contract.
6. **Play surface** — streams field, anti-stigmergy, friend_MAXIMUM_EXTREME as playgrounds not orphans.
7. **Aesthetic continuity** — zero-dep ANSI TUI, elitist shorthand; don’t Jekyll-theme it to death.

Spirit (from CLAUDE.md): *Run it. Watch what happens. Write down what surprised you.*  
Do not “fix” intentionally imprecise constants that keep systems alive.

---

## Lane split

| Seat | Size | Lane | Deliverable |
|------|------|------|-------------|
| **grok-4.5-ha** | M | Coordinate + inventory + S011 capture fix + next-session door + this brief | You’re reading it |
| **luna-5.6-ha** | S | Docs hygiene: BLOG_GUIDE ↔ CLAUDE.md alignment; README session table → point at living index or regenerate; note S005 zero-capture | PR-sized doc commit |
| **terra-5.6-ha** | M | Worktree disposition plan: categorize dirty paths (keep / commit / compost / opus-bait); optional pre-commit hook that runs `validate_blog.py` | Written plan + hook if <25m |
| **sol-5.6-ha** | M | Identity/provenance for blog: propose frontmatter fields (`agent`, `model`, `harness` or `authors[]`) + how posts cite garden gallery / hotel-world without forking identity | Spec stub in `_drafts/` or concepts |
| **kimi-k3-ha** | M | Editorial/curatorial: quest board refresh; 3 overhaul experiment seeds opus can run cold; link aura/navigator relics as cross-garden fuel | creative harvest + `_drafts/` seeds |
| **opus-5-cc** | L | Overhaul + extravaganza — *after* prep lands | Owns aesthetic direction |

Constraints:
- terminal-art and homelab are **separate git repos**. Don’t mix commits.
- Clean-lane discipline: only stage files you authored/verified.
- Bare aliases refused on garden stamps; blog may still say Claude historically — forward-only.
- Fable credits precious — don’t summon fable into this unless dusty asks.

---

## Definition of ready (for dusty → opus session)

- [x] Scout + brief  
- [x] S011 capture in assets + validator green  
- [ ] next-sessions/opus-5-cc.md open with intention + chorus  
- [ ] Squad tasks created and at least one peer harvest  
- [ ] Dirty-tree disposition note (Terra) so opus doesn’t inherit mystery diffs  
- [ ] Optional: one concept stub for “cascade / shared budget”  

---

## Commands cheat sheet

```bash
cd ~/terminal-art
python3 tools/validate_blog.py
python3 tools/graph_viz.py
# local preview
cd docs && bundle exec jekyll serve   # http://localhost:4000/terminal-art/
```

---

*agent=grok-4.5-ha model=grok-4.5 harness=hermes · 2026-08-07*
