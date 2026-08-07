# Pattern Discovery Log

Document cool emergent behaviors, unexpected patterns, and beautiful moments.

## Format

```markdown
## YYYY-MM-DD: Pattern Name

**Config:**
- Preset/Experiment: name
- Key params: value
- Seed: number (if reproducible)

**Pattern:**
Description of what emerged

**Why Cool:**
What made it interesting/beautiful/surprising

**Screenshot/Recording:**
Link or description
```

---

## 2026-02-18: Repository Created

**Initial Setup:**
- Modular toolkit with genetics, automata, fields, events
- 5 composable experiments
- Sketchbook system for rapid prototyping

**Next Steps:**
- Start discovering patterns!
- Document cool finds
- Build gallery of favorites

---

*Add your discoveries below...*

---

## 2026-04-06: Wolf Gap Requires Space

**Config:**
- Experiment: wolf_interval.py (headless numeric probe, no spatial dynamics)
- Key params: N=150 walkers, tune_rate=0.0008, seed=42
- 1200 ticks, sampling every 100

**Pattern:**
Without spatial proximity constraints, the Pythagorean comma produces
uniform drift — the entire hue distribution slides ~133¢ per 100 ticks
around the color wheel, completing nearly a full revolution in 1100 ticks.
No wolf gap emerges. The minimum-bin fraction stays at 88% throughout,
never approaching the 35% threshold for gap detection.

**Why Cool:**
The wolf gap is not a consequence of the tuning rule alone. The comma
accumulates evenly when every walker can see every other walker — pressure
is isotropic, so the distribution moves as a whole without developing holes.

The gap requires *uneven encounter density*: walkers physically clustered
in space create local tuning pressure that builds up in some hue regions
and not others. The comma is the fuel. Space is what ignites it.

This suggests the spatial radius parameter (SPATIAL_RADIUS) is not a
performance optimization — it is the mechanism that makes the gap possible.
Small radius → stronger spatial clustering → faster gap emergence.
Large radius → near-uniform pressure → slower or no gap.

**Follow-up question:**
At what spatial radius does the gap fail to emerge? Is there a phase
transition? What does the gap look like mid-formation?
