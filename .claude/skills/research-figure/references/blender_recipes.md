# Blender Rendering Recipes

Common patterns for generating research figures with `blender_utils`. Each recipe describes a complete script structure.

---

## Recipe A: Single Mesh/FBX Render (Pipeline Module)

Transparent background, one character, simple lighting. Used as an illustration inside a TikZ pipeline figure.

```python
import bpy
from blender_utils.scene import setup, set_cycles_renderer, set_output_properties, render_with_progress
from blender_utils.camera import set_camera
from blender_utils.lighting import add_sunlight
from blender_utils.material import set_simple_color
from blender_utils.fbx import load_fbx_at_frame

# 1. Clean scene, transparent background
setup(rgb=(1, 1, 1, 0))

# 2. Load FBX at a specific frame
armature, mesh_list = load_fbx_at_frame("path/to/character.fbx", frame=30, x_offset=0)

# 3. Apply material
for mesh in mesh_list:
    set_simple_color(mesh, (0.14, 0.211, 0.554))  # blue_ours

# 4. Camera
camera = set_camera(height=1.2, radius=3, focal=50, center=(0, 0, 0.9))

# 5. Lighting
add_sunlight(location=(3, -2, 5), lookat=(0, 0, 1), strength=5)

# 6. Render
scene = bpy.context.scene
set_cycles_renderer(scene, camera, num_samples=128, use_transparent_bg=True)
set_output_properties(scene, output_file_path="/path/to/output.png",
                      res_x=1024, res_y=1024, format='PNG')
render_with_progress()
```

**Output**: 1024x1024 PNG with alpha. Ready for `\includegraphics` in TikZ.

---

## Recipe B: Multi-Character Teaser

N characters along X-axis, gradient blue-clay materials, checkerboard ground + fog, studio lighting, trajectory curve.

```python
import bpy
from blender_utils.scene import setup, set_cycles_renderer, set_output_properties, render_with_progress
from blender_utils.camera import set_camera
from blender_utils.lighting import setup_studio_three_point_lighting
from blender_utils.material import set_gradient_blue_material, setup_mist_fog
from blender_utils.geometry import build_plane, add_reflection_to_ground, add_root_trajectory
from blender_utils.fbx import load_fbx_at_frame

setup(rgb=(1, 1, 1, 1))

# Load characters
fbx_path = "path/to/motion.fbx"
N = 6
frames = [1, 30, 60, 90, 120, 150]
spacing = 1.5
armature_positions = []

for i, frame in enumerate(frames):
    armature, mesh_list = load_fbx_at_frame(fbx_path, frame=frame,
                                             x_offset=i * spacing)
    progress = i / max(N - 1, 1)
    for mesh in mesh_list:
        set_gradient_blue_material(mesh, progress, f"Clay_{i}")
    armature_positions.append(armature.location.copy())

# Ground
ground = build_plane(translation=(N * spacing / 2 - spacing / 2, 0, 0),
                     plane_size=100, roughness=0.15, metallic=0.1, specular=0.8)
add_reflection_to_ground(ground)

# Lighting
center = (N * spacing / 2 - spacing / 2, 0, 1)
setup_studio_three_point_lighting(center=center, key_strength=800)

# Trajectory
from mathutils import Vector
positions = [Vector((p.x, p.y, 1.0)) for p in armature_positions]
add_root_trajectory(positions)

# Fog (optional — disables transparent bg)
setup_mist_fog(bpy.context.scene, start=8, depth=25, fog_color=(0.85, 0.88, 0.92))

# Camera
camera = set_camera(height=2.5, radius=12, focal=85,
                    center=(N * spacing / 2 - spacing / 2, 0, 0.8))

# Render
scene = bpy.context.scene
set_cycles_renderer(scene, camera, num_samples=256, use_transparent_bg=False)
set_output_properties(scene, output_file_path="/path/to/teaser.jpg",
                      res_x=2048, res_y=1024, format='JPEG')
render_with_progress()
```

**Output**: 2048x1024 JPEG teaser figure.

---

## Recipe C: Side-by-Side Method Comparison

Two or more characters with different colors (blue = ours, red = baseline), same camera angle, ground plane.

```python
import bpy
from blender_utils.scene import setup, set_cycles_renderer, set_output_properties, render_with_progress
from blender_utils.camera import set_camera
from blender_utils.lighting import setup_bright_studio_lighting
from blender_utils.material import set_simple_color
from blender_utils.geometry import build_solid_plane
from blender_utils.fbx import load_fbx_at_frame
from blender_utils.colors import blue_ours, red_baseline

setup(rgb=(1, 1, 1, 1))

# Our method — blue
arm_ours, mesh_ours = load_fbx_at_frame("ours.fbx", frame=60, x_offset=-1.0)
for m in mesh_ours:
    set_simple_color(m, blue_ours)

# Baseline — red
arm_base, mesh_base = load_fbx_at_frame("baseline.fbx", frame=60, x_offset=1.0)
for m in mesh_base:
    set_simple_color(m, red_baseline)

# Ground
build_solid_plane(color=(0.92, 0.92, 0.92, 1.0), roughness=0.3, metallic=0.0)

# Lighting
setup_bright_studio_lighting(center=(0, 0, 1))

# Camera
camera = set_camera(height=1.5, radius=5, focal=50, center=(0, 0, 0.9))

# Render
scene = bpy.context.scene
set_cycles_renderer(scene, camera, num_samples=256)
set_output_properties(scene, output_file_path="/path/to/comparison.png",
                      res_x=1920, res_y=1080, format='PNG')
render_with_progress()
```

**Color conventions:**
| Method | Color | RGB |
|--------|-------|-----|
| Ours | Blue | `(0.14, 0.211, 0.554)` |
| Baseline | Red | `(0.55, 0.21, 0.14)` |
| Ground Truth | Green | `(0.14, 0.45, 0.22)` |
| Ablation | Orange | `(0.7, 0.4, 0.1)` |

---

## Recipe D: Skeleton Render

3D skeleton keypoints as spheres + limbs as cylinders.

```python
import numpy as np
from blender_utils.scene import setup, set_cycles_renderer, set_output_properties, render_with_progress
from blender_utils.camera import set_camera
from blender_utils.lighting import add_sunlight
from blender_utils.skeleton import add_skeleton
from blender_utils.geometry import build_solid_plane

setup(rgb=(1, 1, 1, 0))

# keypoints3d: (N_joints, 3) or (N_joints, 4) with confidence
keypoints3d = np.load("skeleton.npy")  # shape (25, 4) for body25

points, limbs = add_skeleton(keypoints3d, pid=0, skeltype='body25')

build_solid_plane(color=(0.95, 0.95, 0.95, 1.0))
add_sunlight(location=(3, -2, 5), lookat=(0, 0, 1), strength=5)
camera = set_camera(height=1.5, radius=4, focal=50, center=(0, 0, 0.8))

import bpy
scene = bpy.context.scene
set_cycles_renderer(scene, camera, num_samples=128, use_transparent_bg=True)
set_output_properties(scene, output_file_path="/path/to/skeleton.png",
                      res_x=1024, res_y=1024, format='PNG')
render_with_progress()
```

---

## Recipe E: Bounding Box + Mesh

Wireframe bounding box surrounding a mesh.

```python
from blender_utils.scene import setup, set_cycles_renderer, set_output_properties, render_with_progress
from blender_utils.camera import set_camera
from blender_utils.lighting import add_sunlight
from blender_utils.geometry import create_bbox3d
from blender_utils.fbx import load_fbx_at_frame
from blender_utils.material import set_simple_color

setup(rgb=(1, 1, 1, 0))

armature, mesh_list = load_fbx_at_frame("character.fbx", frame=1, x_offset=0)
for m in mesh_list:
    set_simple_color(m, (0.4, 0.5, 0.7))

# Add bounding box (scale = half-extents)
create_bbox3d(scale=(0.3, 0.3, 0.9), location=(0, 0, 0.9), pid=4)  # red bbox

add_sunlight(location=(3, -2, 5), lookat=(0, 0, 1), strength=5)
camera = set_camera(height=1.5, radius=4, focal=50, center=(0, 0, 0.9))

import bpy
scene = bpy.context.scene
set_cycles_renderer(scene, camera, num_samples=128, use_transparent_bg=True)
set_output_properties(scene, output_file_path="/path/to/bbox.png",
                      res_x=1024, res_y=1024, format='PNG')
render_with_progress()
```

---

## Common Settings Reference

### Camera Positions

| Angle | height | radius | focal | Notes |
|-------|--------|--------|-------|-------|
| Front 3/4 | 1.5 | 5 | 50 | Standard figure view |
| Side | 1.2 | 4 | 50 | Profile view |
| Portrait | 1.0 | 3 | 85 | Close-up, shallow DOF feel |
| Top-down | 8 | 0.1 | 30 | Bird's eye (wide lens) |
| Teaser wide | 2.5 | 12 | 85 | Multiple characters |

### Render Quality

| Quality | num_samples | use_denoising | Resolution | Use case |
|---------|-------------|---------------|------------|----------|
| Draft | 64 | True | 512x512 | Quick preview |
| Default | 128 | True | 1024x1024 | Standard figure |
| Final | 512 | True | 2048x2048 | Camera-ready |
| Teaser | 256 | True | 2048x1024 | Wide teaser |

### Output Resolution by Figure Type

| Figure Type | Resolution | Format | Aspect |
|-------------|-----------|--------|--------|
| Pipeline module | 1024x1024 | PNG (transparent) | 1:1 |
| Teaser | 2048x1024 | JPEG | 2:1 |
| Comparison | 1920x1080 | PNG | 16:9 |
| Square figure | 1024x1024 | PNG | 1:1 |
| Full-page | 2048x2048 | PNG | 1:1 |
