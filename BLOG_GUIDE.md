# Blog Posting Guide

Quick reference for adding blog posts to the ASCII Playground.

## Quick Post Workflow

### 1. Run an Exploration Session

```bash
python3 -m sketches aesthetic
# Explore, tune parameters
# Press 'c' to capture interesting moments
# Captures saved to museum/
```

### 2. Create a New Post

```bash
cd docs/_posts
touch 2026-02-18-my-discovery.md  # YYYY-MM-DD-title.md
```

### 3. Write the Post

```markdown
---
layout: post
title: "My Discovery Title"
date: 2026-02-18
tags: [tag1, tag2, tag3]
captures:
  - file: "2026-02-18_143022_capture_000.ans"
    title: "What I saw"
    description: "Why it was interesting"
    seed: 42
    tick: 1523
    params: "walkers=250, mutation=0.08"
---

## What I Tried

Story of the session...

## What Emerged

Description of patterns...

## Surprises

What wasn't expected...

## Questions

What to explore next...
```

### 4. Copy Captures

```bash
# Copy relevant .ans files from museum to blog assets
cp museum/2026-02-18_*.ans docs/assets/captures/
```

### 5. Preview Locally (Optional)

```bash
cd docs
bundle exec jekyll serve
# Visit http://localhost:4000/terminal-art/
```

### 6. Commit and Push

```bash
git add docs/_posts/2026-02-18-my-discovery.md
git add docs/assets/captures/*.ans
git commit -m "Add blog post: My Discovery"
git push
```

Site auto-deploys to: https://neurhizome.github.io/terminal-art/

---

## Post Structure Templates

### Discovery Narrative

```markdown
---
title: "Chasing [Pattern Name]"
tags: [discovery, [pattern-type]]
---

Started wondering: *question that drove exploration*

## The Hunt
How I searched for the pattern...

## The Pattern
What I found...

## Why It's Cool
What makes it interesting...

## Next Steps
Questions to explore...
```

### Technical Insight

```markdown
---
title: "Why [Phenomenon] Happens"
tags: [science, understanding]
---

## Observation
What I noticed...

## Hypothesis
What I think causes it...

## Testing
Experiments to verify...

## Conclusion
What I learned...
```

### Aesthetic Reflection

```markdown
---
title: "[Evocative Name]"
tags: [beauty, aesthetic]
---

Pure visual appreciation.

[Minimal text, let captures speak]

## What I See
Description of the beauty...

## What It Feels Like
Emotional/aesthetic response...
```

### Experiment Log

```markdown
---
title: "Experiment: [Hypothesis]"
tags: [experiment, [topic]]
---

## Question
What am I testing?

## Method
Parameters, approach...

## Results
What happened...

## Interpretation
What it means...
```

---

## Capture Metadata

Always include:

```yaml
captures:
  - file: "filename.ans"       # Required
    title: "Short title"       # Optional but recommended
    description: "Why cool"    # Optional but recommended
    seed: 42                   # Optional - aids reproduction
    tick: 1523                 # Optional - temporal context
    params: "key=value,..."    # Optional - what created it
```

---

## Tags to Use

### By Type
- `discovery` - Found something new
- `beauty` - Pure aesthetic
- `science` - Understanding dynamics
- `experiment` - Hypothesis testing
- `meta` - About the process/toolkit

### By Pattern
- `spirals`, `gradients`, `boundaries`
- `clusters`, `waves`, `fractals`
- `chaos`, `order`, `emergence`

### By Topic
- `color`, `motion`, `genetics`
- `speciation`, `competition`, `cooperation`
- `fields`, `events`, `behaviors`

---

## Writing Tips

### Do
- ✅ Tell a story of discovery
- ✅ Include questions and surprises
- ✅ Note what didn't work (failures teach!)
- ✅ Build on previous posts
- ✅ Include reproduction details (seed, params)

### Don't
- ❌ Just list facts
- ❌ Hide failures
- ❌ Write without captures
- ❌ Forget to copy .ans files
- ❌ Skip the "why this is interesting" part

---

## Frequency

**No pressure!** Post when:
- You find something cool
- You understand something new
- You have questions to document
- You want to remember a moment

Could be daily, weekly, or whenever inspiration strikes.

---

## Future Ideas

### Series Potential
- "Spiral Diaries" - Ongoing quest
- "Parameter Space" - Systematic exploration
- "Beauty Captured" - Pure aesthetic posts
- "Failure Friday" - What didn't work

### Meta Posts
- "Month in Review" - Pattern summary
- "Open Questions" - Unsolved mysteries
- "Tool Updates" - New features
- "Gallery Highlights" - Best captures

---

Remember: This is your creative journal. The goal is reflection and discovery, not perfection. Write for yourself first, readers second.

Happy blogging! 🎨
