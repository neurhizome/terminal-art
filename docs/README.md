# ASCII Playground Blog

This directory contains the Jekyll blog for the ASCII Playground.

## Structure

```
docs/
├── _posts/          # Blog posts
├── _layouts/        # Page templates
├── assets/
│   ├── css/         # Styles
│   ├── js/          # JavaScript (ANSI rendering)
│   └── captures/    # Terminal captures (.ans files)
├── _config.yml      # Jekyll configuration
├── index.md         # Homepage
├── archive.html     # All posts
└── gallery.html     # Capture gallery
```

## Writing Posts

Create a new file in `_posts/` with the format: `YYYY-MM-DD-title.md`

Example post with captures:

```markdown
---
layout: post
title: "Chasing Spirals"
date: 2026-02-18
tags: [spirals, emergence]
captures:
  - file: "spiral_001.ans"
    title: "Perfect 5-arm Spiral"
    description: "Formed at tick 892"
    seed: 42
    tick: 892
    params: "walkers=250, mutation=0.08"
---

Content goes here...

Captures will be automatically rendered at the end of the post.
```

## Adding Captures

1. Copy `.ans` files from `museum/` to `docs/assets/captures/`
2. Reference them in post front matter (see above)
3. They'll be rendered with xterm.js

## Local Development

```bash
cd docs
bundle install
bundle exec jekyll serve
```

Visit http://localhost:4000/terminal-art/

## Deployment

GitHub Pages automatically builds and deploys when you push to main.

The site will be live at: https://neurhizome.github.io/terminal-art/

## Theme

Custom terminal-aesthetic theme with:
- Dark background
- ANSI color palette
- Monospace fonts (IBM Plex Mono)
- xterm.js for authentic terminal rendering
