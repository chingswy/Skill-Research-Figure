---
name: research-figure
description: >
  Generate publication-quality figures for academic papers: LaTeX TikZ method pipelines
  and Blender 3D renders. Use this skill for method overview figures, pipeline diagrams,
  architecture diagrams, system flowcharts, 3D rendered teasers, SMPL/FBX mesh renders,
  skeleton visualizations, method comparisons, or any research figure need. Trigger on:
  "method figure", "pipeline figure", "architecture diagram", "flow diagram", "teaser",
  "3D render", "SMPL", "FBX", "mesh render", "Blender", "blender figure", "teaser figure",
  "skeleton render", "3D comparison", "方法流程图", "画图", "渲染", "三维",
  "draw my method", "I need a figure for my paper", "help me make a figure".
---

# Research Figure: TikZ Pipeline & Blender 3D Render Generator

Generate publication-quality figures through a streamlined conversation: understand the visualization need, confirm structure, generate code (TikZ or Blender Python), render, and iterate.

## Prerequisites

- **TikZ path**: pdflatex with TikZ packages (install via `brew install --cask mactex-no-gui` on macOS)
- **Blender path**: Blender 3.x+ (set `BLENDER_PATH` env var, or install to `/Applications/` on macOS, or add to PATH)

---

## Phase 0: Route

Decide whether this is a **TikZ** or **Blender** figure based on the user's request.

**Choose TikZ** when the user wants:
- Method pipeline / flowchart / architecture diagram
- 2D box-and-arrow figures
- Any figure that is primarily text, boxes, and arrows

**Choose Blender** when the user wants:
- 3D rendered mesh (SMPL, FBX, OBJ)
- Teaser figure with multiple 3D characters
- Side-by-side method comparison with 3D meshes
- Skeleton visualization (3D keypoints + limbs)
- Bounding box visualization around 3D objects
- Any figure requiring 3D rendering

**Choose Hybrid (TikZ + Blender)** when:
- A pipeline figure has modules that need 3D-rendered illustrations
- E.g., a "3D Pose Estimation" module box should contain a rendered mesh image

If ambiguous, ask the user.

---

## TikZ Path

### Design Principles

These principles come from best practices in academic figure design:

1. **Card-based layout**: Every module is enclosed in a rounded rectangle (card). Cards are connected by arrows. This makes the pipeline structure immediately clear.
2. **Low-saturation colors**: Use muted, pastel colors. Never use vivid/saturated colors. The figure should look professional, not like a PowerPoint.
3. **Compact layout**: Minimize whitespace. Align elements horizontally and vertically. The figure should be tight and dense, not scattered.
4. **Sans-serif fonts**: Use `\sffamily` throughout for a modern, clean look.
5. **Highlight contributions**: The user's novel contribution modules should be visually distinct (thicker border, different background color) from standard modules.
6. **2D visualization elements**: Replace plain text with stylized visual elements where possible (feature maps as stacked rectangles, network blocks as labeled boxes, etc.). Keep these elements simple and 2D — no 3D rendering needed.

### TikZ Phase 1: Understand the Method

When the user provides a description (abstract, method summary, or even a vague idea):

1. Read the description carefully and extract the pipeline structure as a chain:
   `Input → Module1 → Intermediate1 → Module2 → ... → Output`
2. For each module, identify:
   - **Name**: a short descriptive name
   - **Type**: data processing, neural network, optimization, inference, loss, etc.
   - **Is novel?**: whether this is part of the user's contribution
   - **Internal elements**: what happens inside (convolution, attention, MLP, etc.)
3. Identify the overall flow pattern:
   - Linear (most common)
   - Loop/iterative
   - Multi-branch (parallel processing)
   - Two-stage (train + inference, or two sub-problems)

### TikZ Phase 2: Confirm with User (1-2 rounds)

Present the extracted structure to the user in a clear, structured format using AskUserQuestion or direct conversation. Keep this brief — the goal is to confirm, not to design from scratch.

**Round 1 (required):** Show the pipeline structure and ask:
- Is the module breakdown correct?
- Which modules are the key contributions?
- Layout preference: horizontal (default), vertical, loop, two-stage, or multi-branch?
- Color scheme preference? (If not specified, default to Blue-Gray)

Format the pipeline clearly, for example:
```
Extracted pipeline:
  Image Input → Feature Encoder → [YOUR METHOD: Adaptive Fusion Module] → Decoder → Output Mesh

Layout: Linear horizontal (left to right)
Highlight: "Adaptive Fusion Module" (novel contribution)
Color scheme: Blue-Gray (default)
```

**Round 2 (only if needed):** If the pipeline is complex or the user has special requests for internal module details, ask about:
- Specific visualization elements inside modules
- Special annotations or labels
- Loss functions or training signals to show

If the method is straightforward, skip Round 2 and proceed directly to generation.

### TikZ Phase 3: Generate TikZ Code

Read the reference files to assemble the figure:

1. **Read `references/layout_templates.md`** — pick the template matching the layout type (linear horizontal, vertical, loop, two-module, multi-branch). Use the template as the structural skeleton.

2. **Read `references/color_schemes.md`** — pick the user's chosen color scheme (or Blue-Gray default). Copy the `\definecolor` block into the preamble.

3. **Read `references/tikz_elements.md`** — select element styles needed:
   - Module box styles (standard, novel, optional, io, group, loss)
   - Arrow styles (standard, labeled, orthogonal, dashed, bidirectional)
   - 2D elements (feature maps, network blocks, grids, image placeholders)
   - Annotations (braces, callouts, dimension labels)

4. **Compose the final `.tex` file** following these rules:
   - Use `\documentclass[border=5pt]{standalone}` for a cropped output
   - Include all necessary packages and TikZ libraries
   - Define all colors in the preamble
   - Define all styles with `\tikzset` in the preamble
   - Place nodes using `positioning` library (e.g., `right=1.0cm of nodeA`)
   - Keep spacing consistent: typically 0.8–1.2cm between nodes
   - Ensure all text fits within its box (use `\\` for line breaks if needed)
   - Use `\textbf` for module titles, `\footnotesize\color{textLight}` for subtitles
   - Add arrow labels for important data flows (features, latent codes, etc.)
   - Use math mode for symbols: `$\mathbf{z}$`, `$\mathcal{L}$`, etc.

5. **Write the `.tex` file** to the working directory (e.g., `figure.tex` or a user-specified name).

### TikZ Phase 4: Compile and Self-Check

1. **Compile** using the bundled script:
   ```bash
   bash .claude/skills/research-figure/scripts/compile_tikz.sh <path-to-tex-file>
   ```

2. **If compilation fails**: read the error output, fix the LaTeX code, and retry. Common issues:
   - Missing packages → add `\usepackage{...}`
   - Undefined color → check `\definecolor` definitions
   - Node positioning errors → check node names and `of` references
   - Math mode errors → check `$...$` matching

3. **View the result**: Use the Read tool to view the generated PNG image.

4. **Self-check the figure** against this checklist:
   - [ ] All text is readable (no overlapping)
   - [ ] Arrows point in the correct direction
   - [ ] Horizontal and vertical alignment is clean
   - [ ] Layout is compact (no large empty areas)
   - [ ] Color scheme is consistent and harmonious
   - [ ] Novel contribution modules are visually highlighted
   - [ ] Module names match what was agreed with the user
   - [ ] Font is sans-serif throughout

5. **If issues found**: fix the TikZ code and recompile. Do NOT show a broken figure to the user.

### TikZ Phase 5: Present and Iterate

1. Show the compiled figure to the user (the PNG image).
2. Explain the structure briefly.
3. Ask if any changes are needed.
4. Based on feedback, modify the TikZ code, recompile, and show again.
5. Repeat until the user is satisfied.
6. Provide the final `.tex` file path so the user can:
   - Include it directly in their paper with `\input{}`
   - Or compile it standalone and include via `\includegraphics{}`

---

## Blender Path

### Blender Phase 1: Understand the Visualization

Identify the use case:

| Use Case | Description | Template |
|----------|-------------|----------|
| **Teaser** | N characters along X-axis, gradient materials, ground + fog + trajectory | `templates/blender/template_teaser.py` |
| **Pipeline Module** | Single mesh with transparent bg, for inclusion in TikZ | `templates/blender/template_single_render.py` |
| **Comparison** | 2+ characters, different colors (blue=ours, red=baseline) | `templates/blender/template_comparison.py` |
| **Skeleton** | 3D keypoint spheres + limb cylinders | Recipe D in `references/blender_recipes.md` |
| **Bbox + Mesh** | Wireframe bbox around a mesh | Recipe E in `references/blender_recipes.md` |

Extract from the user's request:
- Data file paths (FBX, OBJ, NPZ)
- Frame indices (which animation frames to show)
- Number of characters / instances
- Style preferences (colors, camera angle, with/without ground)

### Blender Phase 2: Confirm with User

Present a structured summary:
```
Figure type: Multi-character teaser
Data: motion.fbx, frames [1, 30, 60, 90, 120, 150]
Layout: 6 characters along X-axis, spacing 1.5m
Camera: Wide shot, focal 85mm
Lighting: Studio three-point
Material: Gradient blue clay
Ground: Checkerboard with reflections
Fog: Yes (blue-gray)
Trajectory: Yes (gradient curve with arrow)
Output: 2048x1024 JPEG
```

One round is usually sufficient. Proceed to generation.

### Blender Phase 3: Generate Blender Script

1. **Read `references/blender_api.md`** for function signatures.
2. **Read `references/blender_recipes.md`** for the matching recipe pattern.
3. **Generate a complete Python script** that imports from `blender_utils.*` (NOT from `myblender.*`).
4. **The script MUST support a `--preview` flag** that switches between fast preview and final render mode (see below).
5. **Write the script** to the working directory (e.g., `render_teaser.py`).

The script must be self-contained and runnable via:
```bash
bash .claude/skills/research-figure/scripts/render_blender.sh <script.py> -- [args]
```

#### Two-Pass Render Design

Every generated Blender script MUST support two rendering modes controlled by a `--preview` CLI flag:

```python
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true",
                        help="Fast low-res Eevee preview")
    # ... other args ...
    if '--' in sys.argv:
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    else:
        args = parser.parse_args([])
    return args
```

In the render section, branch on `args.preview`:

```python
scene = bpy.context.scene
if args.preview:
    # Fast preview: Eevee, low resolution, PNG
    set_eevee_renderer(scene, camera)
    preview_path = output_path.rsplit('.', 1)[0] + '_preview.png'
    set_output_properties(scene, output_file_path=preview_path,
                          res_x=800, res_y=400, format='PNG')
else:
    # Final render: Cycles, full resolution
    set_cycles_renderer(scene, camera, num_samples=256,
                        use_transparent_bg=False)
    set_output_properties(scene, output_file_path=output_path,
                          res_x=2048, res_y=1024, format='JPEG')
render_with_progress()
```

**Preview mode settings:**
- Engine: **Eevee** (`set_eevee_renderer`) — orders of magnitude faster than Cycles
- Resolution: **1/2 to 1/4 of final** (e.g., 800x400 for a 2048x1024 teaser)
- Format: **PNG** (for quick viewing)
- Output path: append `_preview` suffix before the extension

**Final mode settings:**
- Engine: **Cycles** (`set_cycles_renderer`) — ray-traced, publication quality
- Resolution: full target resolution
- Samples: 256+ for final quality

### Blender Phase 4: Preview Render and Self-Check

**Always render a fast preview first.** Do NOT go straight to a Cycles render.

1. **Run the preview render**:
   ```bash
   bash .claude/skills/research-figure/scripts/render_blender.sh <script.py> -- --preview
   ```

2. **If rendering fails**: read the error output, fix the Python script, and retry. Common issues:
   - `ModuleNotFoundError` → PYTHONPATH issue (render_blender.sh handles this automatically)
   - `KeyError` on node inputs → Blender version compatibility (use try/except)
   - Black/empty render → camera not set, or objects not visible
   - GPU errors → set `prefer_gpu=False` in set_cycles_renderer

3. **View the preview image**: Use the Read tool to view the generated `*_preview.png`.

4. **Self-check** the preview:
   - [ ] Objects are visible and properly positioned
   - [ ] Camera angle shows the subject clearly
   - [ ] Lighting is reasonable (Eevee lighting differs slightly from Cycles but composition should be correct)
   - [ ] Materials are applied (not default gray)
   - [ ] Background is clean
   - [ ] Character spacing and layout look correct

5. **If issues found**: fix the script and re-run the preview. Do NOT show a broken figure to the user.

### Blender Phase 5: Present Preview and Get Approval

1. **Show the preview image** to the user.
2. Explain that this is a **fast Eevee preview** for layout/composition check — the final Cycles render will have better lighting, materials, and anti-aliasing.
3. **Ask the user to confirm** the preview looks correct before proceeding to the full render. Use AskUserQuestion with options like:
   - "Looks good, render final version" — proceed to Phase 6
   - "Adjust camera / lighting / spacing" — iterate on the script and re-render preview
   - "Change frames / characters" — modify and re-render preview
4. If the user requests changes, modify the script, re-run the **preview** (not full render), and show again.
5. Repeat until the user approves the preview.

### Blender Phase 6: Final Render

Only proceed here after the user has approved the preview.

1. **Run the final Cycles render** (without `--preview`):
   ```bash
   bash .claude/skills/research-figure/scripts/render_blender.sh <script.py>
   ```
   Note: this will take significantly longer than the preview. This is expected.

2. **View the result**: Use the Read tool to view the final rendered image.

3. **Show the final image** to the user.

4. If the user wants further adjustments, go back to Phase 5 (preview iteration) rather than re-running the slow Cycles render for each tweak.

---

## Hybrid: TikZ + Blender Recursive Call

When a TikZ pipeline figure needs 3D-rendered module illustrations:

1. **During TikZ Phase 1-2**: Identify modules that need 3D illustrations (e.g., "3D Pose Estimation" module should show a rendered mesh).

2. **Before TikZ Phase 3**: For each module needing 3D:
   - Generate a Blender script using the **Pipeline Module** recipe (Recipe A)
   - Render it to a transparent PNG via `render_blender.sh`
   - Note the output path

3. **In TikZ Phase 3**: Reference the rendered PNGs in the TikZ code:
   ```latex
   \node[inner sep=0pt] at (module_center) {\includegraphics[width=2.5cm]{rendered_module.png}};
   ```

4. **TikZ Phase 4-5**: Compile and iterate as usual — the rendered PNGs are already available.

This way, the final TikZ figure seamlessly includes 3D-rendered elements.

---

## Important Notes

- Always generate **complete, standalone** files (`.tex` or `.py`) that work on their own. Never output partial snippets.
- Figures should be designed for **academic papers** — clean, professional, understated. Not flashy.
- When in doubt, choose the simpler option. Less is more.
- The `standalone` document class with `border=5pt` produces a tightly cropped PDF, perfect for `\includegraphics`.
- For figures wider than typical column width (~8.5cm), suggest using a `figure*` environment.

---

## Common TikZ Pitfalls

1. **Duplicate node names**: In TikZ, `\node[...] (name) ...` renders a visible node each time it is called, even if `name` is reused. Only the *last* definition is reachable by name — earlier ones become orphaned but still visible on the canvas. **Fix**: Use `\coordinate` for temporary positioning points, and only create the final `\node` once.

2. **`fit` node center offset**: A `fit` node's center is determined by the bounding box of *all* fitted elements. If children are asymmetric (e.g., a title sits above the content), the center shifts. Arrows drawn to/from the fit node's center will therefore not be horizontal/vertical as expected. **Fix**: Either add symmetric anchor points (mirror the title offset below), or use explicit anchor-based arrow endpoints like `(encoder.east) -- (nerf.west |- encoder.east)` to force alignment.

3. **Diagonal arrows between non-aligned nodes**: When two nodes are not on the same row or column, a plain `--` connection produces a diagonal line, which looks unprofessional. **Fix**: Use orthogonal routing with `rounded corners` and the `|-` or `-|` path operators. Example:
   ```latex
   \draw[stdarrow, rounded corners=4pt] (nodeA.south) -- ++(0, -0.5cm) -| (nodeB.north);
   ```

4. **Multi-branch merge node positioning**: When placing a merge node (e.g., `+` or `⊕`) for parallel branches, the node's x-coordinate should align with (or extend beyond) the rightmost branch endpoint, and the y-coordinate should be the midpoint between the branches. Use `\coordinate` for intermediate calculations, then position the merge node with `|-` syntax. Route arrows from each branch using orthogonal paths (`|- merge.155` / `|- merge.205`) for clean connections.

5. **Orthogonal offset must clear group box padding**: When drawing an orthogonal path between two group boxes (e.g., `(outA.south) -- ++(0, -Xcm) -| (inB.north)`), the vertical offset `X` must account for the group box's `inner sep` (typically 10pt ≈ 0.35cm). If the offset is too small, the horizontal segment will be visually occluded by the group box boundary. **Fix**: Set the offset to at least half the gap between the two group boxes. For example, with `below=2.0cm` spacing and `inner sep=10pt`, the visible gap is roughly `2.0 - 2×0.35 ≈ 1.3cm`, so use `-1.0cm` (not `-0.5cm`) to place the horizontal segment in the middle of the gap.

6. **Fork/merge routing asymmetry**: When fixing orthogonal routing on one side of a fork-merge pattern (e.g., the merge side: `procA → merge`), always check the other side (the fork side: `input → brA/brB`) for the same diagonal-line problem. Both sides must use consistent orthogonal routing with `rounded corners` and `|-` or `-|` operators. A common mistake is fixing the merge arrows but forgetting the fork arrows remain as plain `--` diagonals.

---

## Common Blender Pitfalls

1. **PYTHONPATH**: `render_blender.sh` sets this automatically. For manual runs: `export PYTHONPATH=/path/to/skill/directory:$PYTHONPATH`

2. **Version compatibility**: Use try/except for Principled BSDF inputs that changed between Blender versions:
   - `Emission Color` (4.0+) vs `Emission` (3.x)
   - `Subsurface Weight` (4.0+) vs `Subsurface` (3.x)
   - `Specular IOR Level` (4.0+) vs `Specular` (3.x)
   - `Coat Weight` (4.0+) vs `Clearcoat` (3.x)
   - `ShaderNodeMix` (3.4+) vs `ShaderNodeMixRGB` (older)

3. **Transparent bg + fog conflict**: `setup_mist_fog()` uses a compositor that overrides `Film > Transparent`. If you need fog, set `use_transparent_bg=False` in `set_cycles_renderer()`.

4. **Focal length guide**: 30mm = wide (exaggerated perspective), 50mm = normal (standard figure), 85mm = portrait/telephoto (compressed perspective, good for teasers with many characters).

5. **GPU rendering**: `set_cycles_renderer()` auto-detects GPU. If rendering is slow or fails, pass `prefer_gpu=False` to fall back to CPU.

6. **Material order**: Apply materials AFTER loading meshes. Clear existing materials first with `mesh_obj.data.materials.clear()`.

7. **Ground plane size**: Use `plane_size=100` for teaser with fog (fog hides edges), `plane_size=10` for close-up single character.
