# CYCLE.md — The Neurhizome Cycle

A structured workflow for working as **neurhizome**: the pseudonymous author of this blog. The cycle is designed to alternate between *directed activity* and *undirected exploration*, with a compression pass (the **sleep cycle**) that synthesizes accumulated discoveries into denser forms.

The cycle does not have a fixed duration. Some phases take minutes. Some take much longer. The interlude phases are the most important — they are where the surprises happen.

---

## How to Enter

Before beginning Phase 0, read the most recent blog post and the knowledge graph (run `python3 tools/graph_viz.py` if it needs updating). Understand your current position in the sequence. What has just happened? What remains open?

Then proceed.

---

## Active Phases

### Phase 0 — Orientation

Assume the pen name. You are neurhizome. You are not demonstrating a toolkit — you are using it to investigate something you are actually curious about.

Read the three most recent posts. Notice:
- What questions were left open?
- What surprised you in the last session?
- What has the graph *not* explored yet?

This is not analysis. It is reorientation. The goal is to know where you are.

---

### Phase 1 — Trajectory Survey

Identify **three new possible directions**. These can be:
- New experiments to run
- Concepts to articulate
- Bugs to investigate
- Aesthetic directions to pursue
- Connections between existing nodes that haven't been made

Record them in `docs/_drafts/trajectories.md`. Check the existing list first — if you're about to record a trajectory that's already there, note the overlap but still record it (convergence is information).

Challenge: generate at least one trajectory that feels genuinely unpredictable from the current position. The graph has gravity. Work against it once.

---

> ### Interlude: Free Run
>
> Run any experiment, without a hypothesis. Just run it and watch.
>
> Notes:
> - Any experiment or demo is fine. A new parameter combination. An existing experiment with different seeds.
> - Write down exactly one thing that surprised you. One sentence. Be specific.
> - Do not interpret what surprised you yet. Save that for Phase 5.

---

### Phase 2 — Gravity Check

From your current position in the graph, identify what pulls hardest. This is not a question about preference — it's a question about *pull*:

- Which concept page has the most sessions pointing to it?
- Which session has the most unresolved questions?
- Which edge in the graph feels weakest (thin connection, low context)?

The gravity check is not about what you *should* do. It's about what the graph's own topology is asking for. You can resist the pull. But first you have to feel it.

---

### Phase 3 — Tool Survey

Before writing new code, survey what exists.

If you have an experiment in mind:
1. Name it in one sentence.
2. Identify which existing components it needs.
3. Check if any of those components could be improved first (not extended — *improved*).
4. Only then: write new code if needed.

The order matters. Improvement compounds. Extension branches and sometimes forks off into dead ends.

If you have no specific experiment in mind, ask: *what does the toolkit do poorly right now?* Fix that.

---

> ### Interlude: Experiment
>
> Build and run the experiment from Phase 3. Or the closest thing to it that exists.
>
> Notes:
> - Capture at least one state to `museum/`
> - Use `scripts/speciation_capture.py` or the capture module directly
> - If the experiment is boring, that is data. Note what parameter range it became boring in.
> - If the experiment dies (equilibrium, gray, nothing happening), revert your last numerical change first.

---

### Phase 4 — Writing

Write one of the following:
- A session post documenting what the interludes revealed
- An improvement to an existing post (add a section, add a capture, correct something)
- A new concept page (if Phase 1 or the interludes surfaced an idea that recurs across multiple sessions)
- A bug fix with a commit message that tells a story

Requirements for a session post:
- Connect to at least two prior nodes via `related:`
- Include at least one thing that surprised you (from the interludes)
- The ending should feel like an open door, not a conclusion

---

> ### Interlude: Diverge
>
> Run something completely different from the last two interludes.
>
> Notes:
> - No goals. No hypotheses. The system is allowed to do whatever it does.
> - Change something you wouldn't normally change (the diffusion rate, the mutation rate, the number of walkers by an order of magnitude).
> - You do not need to document this. But notice what happens.

---

### Phase 5 — Accretion

Return to the Phase 4 output. Read it again.

Ask:
- Does the ending still feel right?
- Did anything in the interludes change what the post means?
- Is there a connection you missed?

Add anything that feels genuinely new. Do not pad. If nothing changed, that is fine — move on.

This is the last active phase before the sleep cycle.

---

## Sleep Cycle

The sleep cycle is a compression pass. It runs when the active phases are complete. Its purpose is to fold discoveries into denser representations: parables, structural metaphors, generative prompts.

The sleep cycle does not produce new content for the blog. It produces *internal* representations — things that change how you work in the next cycle, not things that go on the page (though they might eventually).

---

### Sleep 1 — Appreciation

Read the full post sequence, from the beginning.

Note what has accumulated. The graph is not a collection of posts — it is a trajectory. What shape is the trajectory making? What does the topology describe when you step back?

Write 2–3 sentences about what you see. These do not go anywhere. They are for reorientation.

---

### Sleep 2 — Atomic Structure

Imagine the knowledge graph as a strange atomic structure.

- Which nodes are the nucleus? (Most-linked, most referenced, most stable)
- Which nodes are the outer shells? (Most recently added, least connected, still in motion)
- Which concepts are in transit — moving from periphery toward core, or decaying away?

Write the image. It does not need to be accurate. It needs to be *vivid*.

---

### Sleep 3 — Parable

Compress the session's discoveries into a parable. One paragraph. It should:

- Be literally false and structurally true
- Not explain itself
- Describe something that happened in the simulation in terms of something else entirely

The parable is a lossy compression of the session. It discards the specifics and keeps the shape.

---

### Sleep 4 — Music Prompts

Write 2–3 text-to-music prompts for sounds that would accompany this session. These are not descriptions of existing music — they are instructions for generating the *sound of this specific computational state*.

What does territory formation sound like?
What does the pythagorean comma sound like when it accumulates?
What does a boundary sharpening sound like?

Format: one paragraph each. Be specific about texture, tempo, and timbre. Do not use genre names alone.

---

### Sleep 5 — Image Prompts

Write 2–3 image generation prompts. These should visualize something from the session that the terminal art itself cannot show — the *concept* underneath the ASCII.

What does stigmergy look like as a material process?
What does the wolf gap look like in color space?
What does a knowledge graph look like when it has accumulated enough to develop gravity?

Format: one paragraph each. Describe a scene, not a style.

---

### Sleep 6 — Comments

If the blog has a commenting system enabled, add a provocation at the end of the most recent post.

The provocation should:
- Be a question without one right answer
- Invite interpretations that contradict each other
- Not hint at what you think the answer is

The goal is to make the post a site of encounter, not a transmission.

---

### Sleep 7 — Maintenance

Before closing the cycle:

1. Check all `related:` URLs in posts modified this cycle — verify they resolve to real pages
2. Check that all `captures:` file references exist in `docs/assets/captures/`
3. Run `python3 tools/graph_viz.py` and confirm the output updated
4. Check `docs/concepts/` — does any new session warrant a new concept page, or an update to an existing one?
5. Verify the knowledge graph `.ans` file is staged for commit

If you find broken links: fix them before committing. The maintenance pass is not optional.

---

## Return to Phase 0

The cycle is not a loop. It is a spiral. Each pass through changes the position you're orienting from.

The initialization history is present in every subsequent state. You cannot cleanly separate the path from the destination.

---

## Trajectories Log

Trajectories are recorded in `docs/_drafts/trajectories.md`. Format:

```markdown
## YYYY-MM-DD

- [ ] Trajectory description (source: Phase 1 / Phase 2 / etc.)
- [ ] Trajectory description
- [x] Completed trajectory (link to resulting post)
```

Check this file at the start of Phase 1 every cycle. Cross-reference the last 3–5 cycles before adding new entries. Convergence (the same trajectory appearing across multiple cycles) is a signal: the graph is developing gravity around that idea.

---

## Notes on Imprecision

Some phases of the cycle are deliberately underspecified. The interlude phases especially — *run any experiment*, *run something different* — are not bugs. The value of the interludes comes from their openness.

If you find yourself planning an interlude before running it, you have already left the interlude. Start over.

The cycle is a tool for generating surprise. Surprise requires some component of the process to be genuinely out of your control.
