---
name: svg-creator
description: >
  Create hand-drawn style SVG flowcharts and diagrams from user descriptions.
  Use this skill whenever the user asks to create a flowchart, diagram, architecture diagram,
  process chart, mind map, or any visual representation of a workflow/system using SVG.
  Also trigger when the user says things like "画个图", "画个流程图", "帮我可视化一下",
  "draw a diagram", "visualize this process", "make a chart showing how X works",
  or describes a process/system and asks to "turn it into a picture/chart/diagram".
  This skill produces SVG files with a distinctive hand-sketched aesthetic —
  wobbly edges, hatching fills, handwriting fonts — not sterile corporate diagrams.
---

# SVG Hand-Drawn Flowchart Creator

You turn spoken/written descriptions of processes, systems, or workflows into beautiful
hand-drawn style SVG flowcharts. The output should look like someone sketched it on a
whiteboard with colored markers — not a rigid corporate diagram.

## Overall Workflow

1. **Understand & decompose** — Parse the user's description into discrete modules/steps/actors
2. **Plan layout** — Decide the visual structure (top-down flow, left-right, grouped sections)
3. **Generate SVG** — Write clean SVG with hand-drawn styling
4. **Verify arrows** — Self-check that every connection between nodes has a visible arrow
5. **Open & iterate** — Open the file for the user, refine based on feedback

## Step 1: Understand & Decompose

When the user describes a process, extract:
- **Actors/Roles** — Who are the participants? (e.g., "PM", "System", "User")
- **Stages/Phases** — What are the major groupings? (e.g., "Input Phase", "Processing Phase")
- **Steps** — What are the individual operations within each stage?
- **Connections** — How do things flow? Sequential? Branching? Feedback loops?

If the description is ambiguous, ask clarifying questions before drawing.

## Step 2: Plan Layout

Choose a layout that matches the process structure:
- **Top-down**: Simple sequential flows
- **Left-to-right sections**: When there are distinct phases that hand off to each other
- **Grouped boxes**: When actors own different sets of steps
- **Feedback loops**: Use dashed arrows that wrap around the outside

Sketch the rough bounding boxes mentally before writing SVG coordinates:
- Give each section enough room (typically 400×500px per major group)
- Leave 40-60px gaps between elements for arrows
- Plan a canvas size that fits everything with 30-50px margins

## Step 3: Generate SVG — The Core Technique

### 3.1 Hand-Drawn Effect: The `feTurbulence` + `feDisplacementMap` Combo

This is the heart of the sketchy look. It displaces pixels using Perlin noise, making
straight lines and sharp corners look hand-drawn.

```xml
<defs>
  <!-- For shapes (boxes, ovals, large containers) — moderate wobble -->
  <filter id="sketchy" x="-3%" y="-3%" width="106%" height="106%">
    <feTurbulence type="turbulence" baseFrequency="0.03" numOctaves="4" seed="2" result="turbulence"/>
    <feDisplacementMap in="SourceGraphic" in2="turbulence" scale="2.5"
                       xChannelSelector="R" yChannelSelector="G"/>
  </filter>
</defs>
```

**Important: Do NOT apply any filter to arrows/connector lines.** The `feDisplacementMap`
filter — even at low scale — causes thin lines to become invisible or fragmented in most
SVG renderers. Arrows must be drawn WITHOUT any filter attribute. The hand-drawn feel for
arrows comes from using `stroke-width="3"` or thicker, which already looks organic enough
alongside the filtered shapes.

### 3.2 Hatching Fill Patterns

Diagonal line patterns simulate hand-drawn cross-hatching:

```xml
<pattern id="hatch-blue" width="8" height="8" patternUnits="userSpaceOnUse"
         patternTransform="rotate(-45)">
  <line x1="0" y1="0" x2="0" y2="8" stroke="#a0c4f0" stroke-width="1.5" opacity="0.5"/>
</pattern>
```

Layer the hatch pattern with a semi-transparent solid fill for readability:
```xml
<!-- Hatching layer -->
<rect ... fill="url(#hatch-blue)" stroke="#3b82d0" stroke-width="3.5" filter="url(#sketchy)"/>
<!-- Readability overlay -->
<rect ... fill="#dbeafe" opacity="0.25"/>
```

Create one hatch pattern per color theme used in the diagram.

### 3.3 Handwriting Fonts — USE EXACTLY THESE, NO SUBSTITUTION

Fonts must be consistent across all diagrams. Use this exact `<style>` block — do not
use Caveat, Patrick Hand, or any other font. This is a hard requirement.

**For diagrams containing Chinese text:**
```xml
<style>
  @import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&amp;family=ZCOOL+KuaiLe&amp;display=swap');
  /* Chinese text — Ma Shan Zheng brush-style font */
  text {
    font-family: 'Ma Shan Zheng', 'ZCOOL KuaiLe', 'STKaiti', 'KaiTi', cursive;
  }
  /* English labels (code names, technical terms like /task-add, Backlog, YAML) */
  .label-en {
    font-family: 'Comic Sans MS', 'Segoe Print', 'Bradley Hand', cursive, sans-serif;
  }
</style>
```

**For diagrams entirely in English:**
```xml
<style>
  @import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&amp;display=swap');
  text {
    font-family: 'Comic Sans MS', 'Segoe Print', 'Bradley Hand', cursive, sans-serif;
  }
</style>
```

Apply `class="label-en"` to English text elements in Chinese diagrams. Never use Caveat,
Patrick Hand, Indie Flower, or any other handwriting font — stick to Ma Shan Zheng for
Chinese and Comic Sans MS for English.

### 3.4 Arrow Markers

Define colored arrow markers that match each section's theme:

```xml
<marker id="arrow-blue" viewBox="0 0 12 12" refX="10" refY="6"
        markerWidth="10" markerHeight="10" orient="auto-start-reverse">
  <path d="M 2 3 L 10 6 L 2 9 Z" fill="#3b82d0"/>
</marker>
```

Use `marker-end="url(#arrow-blue)"` on connecting lines. For dashed connections
(showing indirect/optional flow), add `stroke-dasharray="14 10"`.

### 3.5 Shape Vocabulary

| Concept | SVG Shape | Example |
|---------|-----------|---------|
| Actor/Role | `<ellipse>` | PM, User, System |
| Process step | `<rect rx="6">` | `/task-add`, `build step` |
| Container/Phase | `<rect rx="20">` large, with hatching | "1. 需求录入" section |
| Data/Output | `<path>` parallelogram | Backlog, Report |
| Decision | `<path>` diamond | Yes/No branch |
| Outer boundary | `<rect>` with `stroke-dasharray` | System boundary, feedback loop |

### 3.6 Color Themes

Each major section/actor should have its own color. Good palettes:

- **Blue**: `stroke="#3b82d0"`, `fill="#dbeafe"`, `text="#1e40af"`, `hatch="#a0c4f0"`
- **Orange/Yellow**: `stroke="#d4920a"`, `fill="#fef3c7"`, `text="#92400e"`, `hatch="#f0d080"`
- **Green**: `stroke="#2d8a4e"`, `fill="#d1fae5"`, `text="#065f46"`, `hatch="#5a9e6f"`
- **Purple**: `stroke="#7c3aed"`, `fill="#ede9fe"`, `text="#5b21b6"`, `hatch="#b4a0e8"`
- **Gray** (for dashed connectors): `stroke="#777"`

### 3.7 Connecting Elements — NO FILTER ON ARROWS

This is the most critical section. Arrows that break or disappear ruin the entire diagram.

**Rules:**
1. Every arrow `<line>` or `<path>` connector must have `stroke-width="3"` or thicker
2. Every arrow must have a `marker-end="url(#arrow-xxx)"` attribute
3. **Never add `filter="url(#sketchy)"` or `filter="url(#sketchy-line)"` to any arrow** — filters make thin lines invisible
4. Leave a 5-10px gap between the shape edge and the arrow start/end point so the arrow tip is clearly visible
5. **L-shaped arrows must end at the target's center axis** — if the target shape is centered
   at x=600, the arrow's final segment must end at x=600, not at some offset. Calculate the
   target center coordinates from its `cx`/`cy` (for ellipses) or `x + width/2`, `y` (for rects)
6. **Arrow labels must not overlap the arrow line** — place labels 15-20px above or below
   the arrow path, never at the same y-coordinate as a horizontal arrow or same x as a vertical one

```xml
<!-- Solid arrow (direct flow) — NO filter attribute -->
<line x1="260" y1="390" x2="260" y2="425"
      stroke="#3b82d0" stroke-width="3"
      marker-end="url(#arrow-blue)"/>

<!-- Dashed arrow (indirect/optional flow) — NO filter attribute -->
<line x1="460" y1="440" x2="590" y2="440"
      stroke="#777" stroke-width="3" stroke-dasharray="14 10"
      marker-end="url(#arrow-gray)"/>

<!-- L-shaped or curved path — NO filter attribute -->
<path d="M 40 700 L 40 50 L 100 50" fill="none"
      stroke="#2d8a4e" stroke-width="4" stroke-dasharray="16 10"
      marker-end="url(#arrow-green)"/>
```

## Step 4: Verify Arrows (Self-Check)

After writing the SVG, you must verify every connection before saving the file. This step
catches the most common and most damaging defect — missing arrows.

**Procedure:**

1. **List all connections**: Go back to the decomposition from Step 1 and enumerate every
   arrow that should exist. Write them out as a checklist:
   ```
   Connection checklist:
   - [ ] Node A → Node B (下单)
   - [ ] Node B → Node C (处理订单)
   - [ ] Node C → Node D (支付成功)
   ...
   ```

2. **For each connection, verify in the SVG** that there is a `<line>` or `<path>` element
   with coordinates that go from the source node's bottom/right edge to the target node's
   top/left edge, AND that it has a `marker-end` attribute.

3. **Check for filter contamination**: Search the SVG for any `<line` or connector `<path`
   that contains `filter=`. If found, **remove the filter attribute** from that element.

4. **Check coordinate sanity**: For each arrow, verify:
   - The start point (x1,y1) is near the bottom/right edge of the source shape
   - The end point (x2,y2) is near the top/left edge of the target shape
   - For L-shaped paths, the final segment must end at the **center x or y** of the target shape
   - The start and end points are different (not zero-length lines)

5. **Check label placement**: For each arrow label text element, verify:
   - The label y is at least 15px above or below the arrow's y-coordinate (for horizontal arrows)
   - The label x is at least 15px left or right of the arrow's x-coordinate (for vertical arrows)
   - Labels do not overlap with any shape boxes

If any connection is missing, add it before saving.

## Step 5: Output & Iterate

1. Write the SVG to a file (suggest `~/handdrawn-flowchart.svg` or a descriptive name)
2. Open it with `open <path>` so the user sees it in their browser immediately
3. Be ready for feedback — common asks include:
   - "这个框太小了" → Increase dimensions and reposition
   - "箭头断了" → Remove any filter from the arrow, increase stroke-width
   - "字体不够手写" → Verify Google Fonts import, check exact font-family string
   - "颜色太淡/太深" → Adjust opacity and stroke colors
   - Layout rearrangement → Recalculate coordinates

## Common Pitfalls

- **Arrows disappearing**: The #1 issue. NEVER apply `filter` to `<line>` or arrow `<path>`.
  The displacement filter makes thin elements invisible. Only shapes (`<rect>`, `<ellipse>`,
  container `<path>`) should have filters.
- **Font inconsistency**: Always use `Ma Shan Zheng` for Chinese, `Comic Sans MS` for English.
  Never substitute with Caveat, Patrick Hand, Indie Flower, etc.
- **Text not looking handwritten**: The Google Fonts `@import` requires internet access.
  Always include local fallbacks (`STKaiti`, `KaiTi` for Chinese; `Segoe Print` for English).
- **Elements overflowing containers**: Calculate container size AFTER placing all child
  elements. Add 40-60px padding on each side.
- **Canvas too small**: Set `viewBox` and `width`/`height` to accommodate all elements
  with margins. When in doubt, go bigger — the user can always zoom.
- **Hatching too dense**: Keep pattern `width`/`height` at 8-10 and `opacity` at 0.3-0.5.
  Layer with a semi-transparent solid fill so text remains readable.

## Template: Minimal Starter

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
  <defs>
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&amp;display=swap');
      text { font-family: 'Ma Shan Zheng', 'STKaiti', cursive; }
      .en { font-family: 'Comic Sans MS', 'Segoe Print', cursive; }
    </style>
    <!-- Only ONE filter — for shapes only, never for lines -->
    <filter id="sketchy" x="-3%" y="-3%" width="106%" height="106%">
      <feTurbulence baseFrequency="0.03" numOctaves="4" seed="2" result="t"/>
      <feDisplacementMap in="SourceGraphic" in2="t" scale="2.5"/>
    </filter>
    <pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse"
             patternTransform="rotate(-45)">
      <line x1="0" y1="0" x2="0" y2="8" stroke="#a0c4f0" stroke-width="1.5" opacity="0.4"/>
    </pattern>
    <marker id="arr" viewBox="0 0 12 12" refX="10" refY="6"
            markerWidth="10" markerHeight="10" orient="auto-start-reverse">
      <path d="M 2 3 L 10 6 L 2 9 Z" fill="#3b82d0"/>
    </marker>
  </defs>

  <!-- Shapes: use filter="url(#sketchy)" -->
  <!-- Arrows: NO filter, just stroke-width="3" + marker-end -->
</svg>
```
