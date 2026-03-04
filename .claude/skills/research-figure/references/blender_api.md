# blender_utils API Reference

API reference for the `blender_utils` package. Import inside Blender Python scripts:

```python
from blender_utils.scene import setup, set_cycles_renderer, set_output_properties, render_with_progress
from blender_utils.camera import set_camera, look_at
from blender_utils.lighting import add_sunlight, setup_studio_three_point_lighting
from blender_utils.material import set_gradient_blue_material, set_simple_color, setup_mist_fog
from blender_utils.geometry import build_plane, create_studio_backdrop, add_root_trajectory
from blender_utils.fbx import load_fbx, load_fbx_at_frame
from blender_utils.skeleton import add_skeleton, SKELETON_CONFIG
from blender_utils.colors import get_rgb, blue_ours, red_baseline
```

---

## scene.py — Scene Setup & Rendering

### `clean_objects(name='Cube')`
Remove a default object by name. No-op if it doesn't exist.

### `setup(rgb=(1,1,1,1))`
Initialize a clean scene: remove default Cube and Light, set background color.
- `rgb=(1,1,1,0)` for transparent background

### `build_rgb_background(world, rgb=(0.9,0.9,0.9,1.0), strength=1.0)`
Set a solid-color world background via shader nodes.

### `set_eevee_renderer(scene, camera_object)`
Configure Eevee for fast preview rendering.

### `set_cycles_renderer(scene, camera_object, num_samples=128, use_denoising=True, use_motion_blur=False, use_transparent_bg=True, prefer_gpu=True, use_adaptive_sampling=False)`
Configure Cycles with GPU auto-detection (Metal on macOS, CUDA/OptiX on Linux/Win).
- `num_samples`: 64=draft, 128=default, 512=final
- `use_transparent_bg`: Enables `Film > Transparent` for PNG alpha

### `set_output_properties(scene, output_file_path="", res_x=1920, res_y=1080, tile_x=1920, tile_y=1080, resolution_percentage=100, format='PNG')`
Configure render output. Supported formats: `'PNG'`, `'JPEG'`, `'FFMPEG'`.

### `render_with_progress(write_still=True)`
Render the current scene with terminal progress feedback.

---

## camera.py — Camera

### `look_at(obj_camera, point)`
Orient any object to face a point. Uses `-Z` as forward, `Y` as up.

### `set_camera(height=5., radius=9, focal=40, center=(0,0,0), location=None, rotation=None, frame=None, camera=None)`
Position and configure the scene camera.
- If `location` is None: places camera at `(radius*sin(0), -radius, height)`
- If `rotation` is None: camera looks at `center`
- `focal`: Lens focal length in mm (30=wide, 50=normal, 85=portrait)
- `frame`: Insert keyframe at this frame (for animation)

### `get_calibration_matrix_K(camera=None, mode='simple')`
Get the 3x3 intrinsic matrix K. Modes: `'simple'` or `'complete'`.

### `set_intrinsic(K, camera, image_width, image_height, clip_start=None, clip_end=None)`
Set camera intrinsics from a 3x3 K matrix.

### `set_extrinsic(R_world2cv, T_world2cv, camera)`
Set camera pose from rotation (3x3) and translation (3x1) in world-to-camera convention.

---

## lighting.py — Lights & Studio Setups

### `add_sunlight(name, location, rotation, lookat, strength=4., cast_shadow=True)`
Directional sun light. If `lookat` is set, `rotation` is ignored.

### `add_area_light(name, location, rotation, lookat, strength=4., size=1.0, size_y=None, shape='SQUARE')`
Soft area light. Shape: `'SQUARE'`, `'RECTANGLE'`, `'DISK'`, `'ELLIPSE'`.

### `add_spot_light(name, location, rotation, lookat, strength=100., spot_size=pi/4, spot_blend=0.15, shadow_soft_size=0.25, cast_shadow=True)`
Cone spot light.

### `setup_studio_three_point_lighting(center=(0,0,0), key_strength=800.0)`
Professional balanced lighting: symmetric left/right area key lights + sun fill + rim + top + ambient world.
All lights track toward `center`. Returns `(left_key, right_key, front_fill, rim_light, top_light)`.

### `setup_bright_studio_lighting(center=(0,0,0), key_strength=8.0, sun_angle=0.02)`
Sun-based key light from left-back 45 deg + fill + rim + bright ambient.
Returns `(sun, fill_light, rim_light)`.

---

## material.py — Materials

### `add_material(name, use_nodes=False, make_node_tree_empty=False)`
Create a new Blender material.

### `clean_nodes(nodes)`
Remove all nodes from a node tree.

### `set_principled_node(principled_node, base_color, subsurface, metallic, roughness, ...)`
Set all PBR parameters on a Principled BSDF node. Silently skips inputs not in current Blender version.

### `build_pbr_nodes(node_tree, base_color, **kwargs)`
Configure PBR on an existing Principled BSDF.

### `set_simple_color(obj, color)`
Quick solid RGB color on a mesh object. `color` is `(r, g, b)`.

### `setMat_plastic(mesh, meshColor, AOStrength=0.0, alpha=1., roughness=0.1, metallic=0.2, specular=0.6)`
Plastic material with ambient occlusion. `meshColor` is a `colorObj` instance.

### `set_material_i(mat_or_obj, pid, metallic=0.5, specular=0.5, roughness=0.9, use_plastic=True)`
Apply color `pid` to a material or mesh object. `pid` can be int, hex string, color name, or RGB list.

### `set_gradient_blue_material(mesh_obj, progress, matname="GradientBlue")`
Clay-like gradient blue material with AO, SSS, and fresnel.
- `progress`: 0.0 (light blue) → 1.0 (dark blue)
- Returns the created material

### `set_transparent_ghost_material(mesh_obj, progress, matname="GhostMaterial", alpha=0.3)`
Semi-transparent ghost material for virtual/predicted characters.

### `setup_mist_fog(scene, start=5.0, depth=20.0, fog_color=(0.7, 0.8, 0.9), falloff='QUADRATIC')`
Compositor-based mist/fog. **Warning**: Conflicts with `Film > Transparent`; fog replaces transparent bg.

---

## geometry.py — Primitives & Scene Elements

### `orient_along_direction(obj, direction)`
Orient an object (default +Z axis) to point in `direction`.

### `create_plane_blender(location, rotation, size, name, shadow)`
Create a Blender primitive plane.

### `build_plane(translation, plane_size, alpha, use_transparent, white, black, roughness, metallic, specular)`
Build a checkerboard ground plane.

### `build_solid_plane(translation, plane_size, color, roughness, metallic, specular)`
Build a solid-color reflective ground plane.

### `create_simple_arrow(start, end, color, cylinder_radius, cone_radius, cone_height)`
Arrow from start to end using Blender primitives. Returns `(cylinder, cone)`.

### `create_coordinate_axes(origin, length, cylinder_radius, cone_radius, cone_height)`
RGB coordinate axes (X=Red, Y=Green, Z=Blue). Returns dict with 'x', 'y', 'z' keys.

### `create_bbox3d(scale, location, rotation, pid)`
Wireframe 3D bounding box.

### `add_material_to_blender_primitive(obj, pid)`
Add a PBR material colored by `pid` to a Blender primitive.

### `create_camera_blender(R, T, scale=0.1, pid=0)`
Camera frustum visualization mesh.

### `create_camera_blender_animated(camera_RT, scale, pid, start_frame, convert_axis)`
Animated camera visualization from `(N, 3, 4)` world-to-camera matrices.

### `create_volume_cube(location, size, density, anisotropy, name)`
Volumetric lighting cube (god rays).

### `bound_from_keypoint(keypoint, padding, min_z)`
Compute bounding box from skeleton keypoints. Returns `(center, scale, bounds)`.

### `create_studio_backdrop(center, width, depth, height, bevel_radius, color)`
L-shaped seamless studio backdrop (cyclorama).

### `add_reflection_to_ground(ground, roughness, metallic, specular, white_color, gray_color)`
Add reflective properties to an existing checkerboard ground.

### `add_root_trajectory(positions, start_color, end_color, line_thickness, emission_strength, alpha, curve_name, extend_start, extend_end, add_arrow, arrow_scale)`
Gradient trajectory curve with arrowhead. `positions` is a list of `(x, y, z)`.

---

## fbx.py — FBX / Animation

### `find_armature_and_mesh(obj_names)`
Find armature and mesh objects from imported object names. Returns `(armature, mesh_object, mesh_object_list)`.

### `shift_action_frames(action, offset)`
Shift all keyframes by `offset` frames.

### `zero_xy_translation_at_frame(action, target_frame)`
Zero armature-level XY translation at a specific frame.

### `zero_pelvis_xy_translation_at_frame(action, target_frame)`
Zero Pelvis/Hips bone XY translation at a specific frame.

### `rotate_animation_trajectory(action, angle_degrees)`
Rotate XY translation keyframes around Z axis.

### `get_mesh_lowest_z(mesh_object_list, depsgraph)`
Get lowest Z coordinate across all meshes (for ground placement).

### `downsample_animation(speedup=2.0)`
Downsample animation keyframes by factor.

### `load_fbx(filename, default_rotation, speedup)`
Import FBX file. Returns `(mesh_object, key, material_name)`.

### `load_fbx_at_frame(fbx_path, frame, x_offset, y_offset=0, z_offset=0, target_frame=1, z_rotation=0, rotate_trajectory=False)`
Load FBX, shift animation so `frame` → `target_frame`, zero root translation, apply offsets, auto-adjust Z.
Returns `(armature, mesh_object_list)`.

### `load_smpl_npz(filename, default_rotation, speedup)`
Load SMPL NPZ animation (requires smplx Blender addon). Returns `(smplx_object, key, material_name)`.

---

## skeleton.py — Skeleton Visualization

### `SKELETON_CONFIG`
Dict of skeleton topologies: `'body25'`, `'body15'`, `'panoptic15'`. Each is a list of `[child, parent]` pairs.

### `read_skeleton(skelname)`
Load skeleton topology from a JSON file.

### `add_skeleton(keypoints3d, pid=0, skeltype='body25', mode='line', color=None, frame=None, shadow=True)`
Render 3D skeleton as spheres (joints) + cylinders (limbs).
- `keypoints3d`: `(N, 3)` or `(N, 4)` — last column is confidence
- Returns `(points, limbs)` lists

### `update_skeleton(keypoints3d, skeltype, points, limbs, frame, conf_thres=0.0, dist_thres=1.)`
Update skeleton pose and insert animation keyframes.

---

## colors.py — Colors

### `get_rgb(pid)`
Resolve color identifier to `[r, g, b, 1.0]`. Accepts:
- `int` → index into `colors_rgb`
- `str` in `colors_table` → named color (e.g., `'gray'`, `'b'`, `'r'`)
- 6-char hex string → e.g., `'5E7CE2'`
- list/tuple → use directly

### Constants
- `colors_rgb` — indexed color palette
- `colors_table` — named color dictionary
- `blue_ours = (0.14, 0.211, 0.554)` — standard "ours" blue
- `red_baseline = (0.55, 0.21, 0.14)` — standard baseline red
- `green_gt = (0.14, 0.45, 0.22)` — ground truth green
- `orange_ablation = (0.7, 0.4, 0.1)` — ablation orange
- `color_jet` — 256-entry jet colormap, shape `(256, 4)` RGBA
