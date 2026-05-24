---
description: Choosing diagram tools and a programmable default for figures.
alwaysApply: false
---

# Choosing the right tool

Pick the lightest tool that can express the required constraints. Auto-layout works fine for loose box-and-arrow sketches; it fights you when a specific geometry matters.

| Need | Tool |
|---|---|
| "Render a quick block diagram, layout doesn't matter" | Mermaid in a Markdown code fence; renders in VS Code, GitHub, Obsidian without install. |
| "Same as above, want a portable SVG file" | Same Mermaid source, render via `mmdc -i in.md -o out.svg -e svg`. |
| "Need slightly more layout control without going manual" | D2 (`brew`-less install: `curl -sSL https://d2lang.com/install.sh \| sh -s -- --prefix=$HOME/.local`); render with `d2 --layout elk in.d2 out.svg`. |
| "Need exact (x, y) positions, perpendicular arrows, fine alignment" | Programmable: drawsvg (Python). Skip auto-layout. |
| "Going into a LaTeX paper" | TikZ. Match the paper's typography directly. |

Anti-pattern: chasing layout pixels by adding `near` hints, ordering tricks, and invisible spacer nodes in Mermaid or D2. Two iterations of that is a signal to switch to a programmable tool.

# Default programmable tool: drawsvg

Install (once, user-local, no sudo):

```bash
pip install --user drawsvg
```

Render pattern:

```python
import drawsvg as dw

d = dw.Drawing(width, height, origin=(0, 0))

# arrow marker (define once, reuse)
arrow = dw.Marker(-1, -3, 8, 3, scale=2, orient="auto", id="arrow")
arrow.append(dw.Path(fill="#222").M(-1, -3).L(7, 0).L(-1, 3).Z())
d.append(arrow)

# nodes are dw.Rectangle + dw.Text; edges are dw.Line(...) with marker_end=arrow
# dashed: stroke_dasharray="4 4"

d.save_svg("out.svg")
```

Conventions:
- Keep layout constants (`MAIN_Y`, `BOX_H`, gap, etc.) at the top of the script so geometry is one place.
- Compute positions from semantic anchors (`ST_X_CENTER = xs[st_idx] + widths[st_idx] / 2`) rather than hard-coding pixel numbers — survives label edits.
- Co-locate the `.py` next to the `.svg` so the source is obvious; commit both.

Reference: [/Users/hangrui/Desktop/note/image/continuous_token_head.py](../../image/continuous_token_head.py) is the canonical worked example.
