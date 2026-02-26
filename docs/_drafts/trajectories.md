# Trajectories Log

A living record of possible next directions, surfaced during Phase 1 (Trajectory Survey) of the neurhizome cycle. Check this list before adding new entries — convergence across cycles is a signal.

Format: `- [ ]` pending, `- [~]` in progress, `- [x]` completed (with link to result).

---

## 2026-02-21

- [ ] BFS constellation grouping: cluster nearby walkers into constellations using breadth-first search, draw edges between members. Do emergent constellation shapes resemble the patterns the mind imposes on static star fields, or something genuinely different? (source: Session 005: Mathematical Forms)
- [ ] Negative space + genetics: walkers trace Lissajous curves but breed — offspring inherit frequency ratio with mutation drift. Which ratio is evolutionarily stable? Which curve survives? (source: Session 005: Mathematical Forms)
- [ ] Concept page: Tuning and Temperament — the pythagorean comma as a case study in systems that can't close. Connects wolf interval session to broader question of whether emergence can produce exact closure. (source: Session 006: Wolf Interval)
- [ ] Field combinations: couple DiffusionField and TerritoryField so territory decay rate depends on diffusion concentration. Does feedback create sharper or blurrier territory? (source: Phase 2, gravity check — diffusion-memory concept is underlinking TerritoryField dynamics)
- [ ] Two genomes per walker competing internally: each walker carries two hue values in rivalry. Which wins? Under what conditions does a dominant hue emerge? Is speciation faster or slower? (source: discovering-modularity open question)
- [ ] Events that trigger other events: chain-reaction event scheduling. Could produce emergent event patterns. (source: discovering-modularity open question)

## 2026-02-21 (cycle 2)

- [ ] Knife edge experiment: systematically vary `breed_threshold` around `1/initial_species` in `color_speciation.py`. Map the phase boundary. At what exact ratio does dissolution transition to rigid partition? What lives on the knife edge itself? (source: Session 004 — explicit ending, Phase 1 predictable follow-through)
- [ ] Comma without temperament: run `wolf_interval.py` with `--et-tick` set high enough that `EqualTemperament` never fires. Does the population self-organize into a scale? Does hue drift forever with no attractor? Or does stigmergy produce its own equilibrium without the external snap? (source: Session 005 Wolf Interval, Phase 1 predictable follow-through)
- [ ] Anti-stigmergy: walkers that flee their own scent trails — negative chemotaxis. Every experiment so far has agents following or reinforcing trails. The opposite assumption hasn't been tried. Do fleeing walkers crystallize into a lattice? Scatter to maximum entropy? Form unexpected attractors? (source: Phase 1, gravity check against the project's own assumptions — unpredictable direction)

## 2026-02-26

- [x] Rhizomatic walkers: abandon arborescent (tree/center) logic. Walkers form plateaus, break into lines of flight, restart anywhere. Discordian Variable (Law of Fives) inverts colors and scatters walkers on every 5th tick or when 5 walkers converge. Does structured chaos enable richer ecology than clean stability? (source: external invitation — Session 009: The Rhizome and Eris)
- [ ] Negative-image reterritorialization: run the rhizomatic walker long enough (1000+ ticks) to observe whether the warm-zone and cold-zone (inverted) territories ever fully merge or if they maintain complementary separation indefinitely. Is the hue-inversion a permanent genetic mark or does drift erase it? (source: Session 009 open question)
- [ ] Discordian event chaining: when a Collapse fires, make some of the scattered walkers carry a "Discordian trait" that raises their probability of triggering the *next* Collapse. Does this produce Collapse cascades, or does the rhizome self-regulate? (source: Session 009 — the convergence Collapses felt qualitatively different from periodic ones)

## 2026-02-22

- [ ] Cross-session field seeding: import the resonance scent field from `wolf_interval.py` as the initial state of a `DiffusionField` in `memetic_territories.py`. Do walkers navigating a space pre-shaped by harmonic geometry inherit the circle-of-fifths topology in their territorial behavior? Does Pythagorean structure persist as spatial influence? (source: Phase 1, connecting wolf_interval to memetic_territories — the resonance field is a stigmergic record that could seed a different kind of memory)
- [ ] Memory decay as age-dependent selection pressure: couple `DiffusionField.decay_rate` to walker age — young walkers deposit strong trails, old walkers deposit faint ones. Does this create selection pressure for faster reproduction (young walkers dominate the field) or for longevity (old walkers with faint trails survive longer by not advertising position)? (source: Phase 1, unpredictable direction — extends aging into field dynamics, reverses the usual assumption that trail strength is constant)
- [ ] Anti-stigmergy refinement: add negative deposit to `DiffusionField.deposit()` — walkers that actively bleach their own trail rather than just moving away from it. The field interpretation: a walker that reduces the signal it's fleeing from. Does active bleaching produce sharper crystallization than mere avoidance? (source: Phase 3 tool survey — GradientFollow with attraction=False already exists; the missing piece is active trail removal, not just fleeing)
