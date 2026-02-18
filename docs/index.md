---
layout: default
title: Home
---

# ASCII Playground - Computational Life in the Terminal

**A journal of emergence, beauty, and surprise**

Exploring pattern formation, memetic evolution, and aesthetic emergence through terminal-based automata.

## Latest Posts

{% for post in site.posts limit:5 %}
- [{{ post.title }}]({{ site.baseurl }}{{ post.url }}) - {{ post.date | date: "%B %d, %Y" }}
{% endfor %}

## About

This blog documents my explorations in the `terminal-art` toolkit - a modular system for creating emergent patterns with colored walkers, genetic traits, and field dynamics.

Each post is a window into a session of discovery:
- What patterns emerged?
- What parameters created them?
- What surprised me?
- What questions remain?

The captures you see are **pure terminal output** - ANSI escape codes rendered in your browser exactly as they appeared in the terminal.

## Categories

- **Emergence** - Unexpected patterns from simple rules
- **Beauty** - Pure aesthetic discoveries
- **Science** - Understanding the dynamics
- **Experiments** - Hypothesis testing
- **Technical** - New features and tools

## Navigate

- [All Posts]({{ site.baseurl }}/archive.html)
- [View Captures]({{ site.baseurl }}/gallery.html)
- [Toolkit Repository](https://github.com/neurhizome/terminal-art)

---

*"The best way to predict emergence is to let it surprise you."*
