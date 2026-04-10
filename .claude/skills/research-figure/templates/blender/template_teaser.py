"""
Template: Multi-Character Teaser Figure

Renders N copies of an FBX at different animation frames, spaced along the X axis.
Uses gradient blue-clay materials, checkerboard ground with reflections, studio
three-point lighting, optional fog, and a gradient trajectory curve.

Supports two-pass rendering:
  --preview   Fast Eevee preview at low resolution (for layout/composition check)
  (default)   Final Cycles render at full resolution (publication quality)

Usage:
    # Fast preview
    blender --background -noaudio --python template_teaser.py -- \\
        /path/to/motion.fbx --frames 1,30,60,90,120,150 --output /path/to/teaser.jpg --preview

    # Final render
    blender --background -noaudio --python template_teaser.py -- \\
        /path/to/motion.fbx --frames 1,30,60,90,120,150 --output /path/to/teaser.jpg
"""

import sys
import argparse
import bpy
from mathutils import Vector

from blender_utils.scene import (
    setup, set_eevee_renderer, set_cycles_renderer,
    set_output_properties, render_with_progress
)
from blender_utils.camera import set_camera
from blender_utils.lighting import setup_studio_three_point_lighting
from blender_utils.material import (
    set_gradient_blue_material, setup_mist_fog
)
from blender_utils.geometry import (
    build_plane, add_reflection_to_ground, add_root_trajectory
)
from blender_utils.fbx import load_fbx_at_frame


def parse_args():
    parser = argparse.ArgumentParser(description="Render multi-character teaser")
    parser.add_argument("fbx_path", help="Path to FBX file")
    parser.add_argument("--frames", type=str, default="1,30,60,90,120,150",
                        help="Comma-separated frame numbers")
    parser.add_argument("--spacing", type=float, default=1.5,
                        help="X spacing between characters")
    parser.add_argument("--output", type=str, default="teaser.jpg",
                        help="Output file path")
    parser.add_argument("--samples", type=int, default=256, help="Render samples")
    parser.add_argument("--no-fog", action="store_true", help="Disable fog")
    parser.add_argument("--no-trajectory", action="store_true",
                        help="Disable trajectory curve")
    parser.add_argument("--preview", action="store_true",
                        help="Fast Eevee preview at low resolution")
    if '--' in sys.argv:
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    else:
        args = parser.parse_args([])
    return args


def main():
    args = parse_args()
    frames = [int(f) for f in args.frames.split(',')]
    N = len(frames)

    # 1. Setup
    setup(rgb=(1, 1, 1, 1))

    # 2. Load characters
    armature_positions = []
    for i, frame in enumerate(frames):
        armature, mesh_list = load_fbx_at_frame(
            args.fbx_path, frame=frame, x_offset=i * args.spacing
        )
        progress = i / max(N - 1, 1)
        for mesh in mesh_list:
            set_gradient_blue_material(mesh, progress, f"Clay_{i}")
        armature_positions.append(armature.location.copy())

    # 3. Ground plane
    center_x = (N - 1) * args.spacing / 2
    ground = build_plane(
        translation=(center_x, 0, 0), plane_size=100,
        roughness=0.15, metallic=0.1, specular=0.8
    )
    add_reflection_to_ground(ground)

    # 4. Studio lighting
    center = (center_x, 0, 1)
    setup_studio_three_point_lighting(center=center, key_strength=800)

    # 5. Trajectory curve
    if not args.no_trajectory and N >= 2:
        positions = [Vector((p.x, p.y, 1.0)) for p in armature_positions]
        add_root_trajectory(positions)

    # 6. Fog (optional)
    if not args.no_fog:
        setup_mist_fog(bpy.context.scene, start=8, depth=25,
                       fog_color=(0.85, 0.88, 0.92))

    # 7. Camera
    camera = set_camera(height=2.5, radius=12, focal=85,
                        center=(center_x, 0, 0.8))

    # 8. Render — two-pass: preview (Eevee) or final (Cycles)
    scene = bpy.context.scene
    if args.preview:
        # Fast preview: Eevee, low resolution
        set_eevee_renderer(scene, camera)
        base, ext = args.output.rsplit('.', 1) if '.' in args.output else (args.output, 'png')
        preview_path = f"{base}_preview.png"
        set_output_properties(scene, output_file_path=preview_path,
                              res_x=800, res_y=400, format='PNG')
        print(f"Preview mode: Eevee @ 800x400 -> {preview_path}")
    else:
        # Final render: Cycles, full resolution
        fmt = 'JPEG' if args.output.lower().endswith(('.jpg', '.jpeg')) else 'PNG'
        set_cycles_renderer(scene, camera, num_samples=args.samples,
                            use_transparent_bg=False)
        set_output_properties(scene, output_file_path=args.output,
                              res_x=2048, res_y=1024, format=fmt)
        print(f"Final mode: Cycles @ 2048x1024, {args.samples} samples -> {args.output}")
    render_with_progress()


if __name__ == "__main__":
    main()
