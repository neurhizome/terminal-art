# Pre-Cycle README Assessment — 2026-02-22

Written before running the Neurhizome Cycle. These notes establish the baseline
against which any post-cycle README changes will be compared.

---

## What the README Currently Is

A modular toolkit reference document. It was clearly written at the moment the
`src/` architecture was assembled, when everything was "(NEW!)". It reads as an
API announcement aimed at developers wanting to build terminal animations.

Bullet format. Feature-list structure. Six modules with emoji markers. A gag
header. Code snippets for API composition. CLI flags. Then a disconnected color
schemes appendix at the bottom that was written before the modular system
existed.

---

## What the Project Has Actually Become This Week

**Feb 18:** Beginning post. The blog opens. A playground for emergence.

**Feb 19:** Session 001 (boundary sharpening) + Session 002 (event horizon /
trace persistence). The modular system is first used as a vehicle for genuine
investigation, not demonstration.

**Feb 20:** Session 003 (no man's land — the seam strike), gradient flow post,
predator-prey post (Lotka-Volterra in discrete space), discovering-modularity
post. Four posts in one day. The knowledge graph rebuilds on commit.

**Feb 21:** Session 004 (dissolution — eight species collapse to one; the math
was against divergence before tick 0). Session 005 (two threads): Wolf Interval
(Pythagorean comma accumulates in hue space, circle of fifths draws itself via
stigmergy) and Mathematical Forms (Mandelbrot, Recamán, Lissajous/cipher space).

**Feb 22 (today):** Human returns processed. Quest board built. Songs from Suno
embedded in posts. Images generated. A quest for a word.

**New code this week, absent from README:**
- `experiments/wolf_interval.py` — Pythagorean comma experiment
- `experiments/cipher_space.py` — negative space / Lissajous erasure
- `demos/mandelbrot_ascii.py` — Mandelbrot in density gradients
- `demos/recaman_arcs.py` — Recamán sequence as arc visualization
- `src/genetics/genome.py` → `Genome.tune_toward()` method
- `src/automata/behaviors.py` → `FifthSeek`, `RecamanWalk`, `LissajousOrbit` behaviors
- `src/events/event.py` → `EqualTemperament` event
- `tools/graph_viz.py` — self-documenting knowledge graph
- `docs/quests.md` — human collaboration board
- `docs/concepts/stigmergy.md` + `docs/concepts/diffusion-memory.md`

**What the README says about these:** Nothing.

---

## Specific Problems

1. **(NEW!) markers are stale.** The modular architecture is now simply the
   architecture. These badges were meaningful for ~24 hours.

2. **"Philosophy (Now with 32% More Claude!)"** is a gag header that has aged
   very badly. The project's actual philosophy — emergence over programming,
   the gap between almost-right and right, running things to find out — deserves
   an honest statement.

3. **No mention of the blog.** The docs/ directory, the session posts, the
   knowledge graph, the quest board — the repository's most distinctive and
   interesting output is completely absent from the README.

4. **Project Structure tree is incomplete.** Missing: docs/, museum/, scripts/,
   wolf_interval.py, cipher_space.py from experiments/.

5. **CLI path error.** "Run `python3 ascii_waves.py -h`" should be
   `python3 demos/ascii_waves.py -h`.

6. **Color schemes appendix** (bottom of README) is a disconnected remnant from
   the pre-modular era. These CLI options are for `ascii_waves.py` only. They're
   documented as if they apply to the whole project.

7. **The tone is developer-facing, not discovery-facing.** "Composable toolkit
   for creating animated terminal graphics" is true but misses what the project
   actually does: run systems that produce surprises, then document the surprises.

8. **The opening description doesn't mention the project's primary artifact.**
   The blog and knowledge graph are not implementation details — they're the
   reason the toolkit exists.

---

## What Should Be Preserved

- Quick Start / venv / pip install (useful)
- iSH/iOS setup section (genuinely useful, specific)
- Modular Toolkit API section (good reference, just needs additions)
- Glyph system documentation (substantial, correct)
- License line

---

## Baseline Verdict

The README describes the scaffolding, not the building. A new visitor reading it
would not know: that this is a living research blog; that walkers have been
navigating Pythagorean harmonic geometry; that the knowledge graph rebuilds
itself on commit; that humans are invited to return quests with songs, images,
and words. The README is a week old and already significantly behind.
