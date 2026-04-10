"""
Template: Side-by-Side Method Comparison

Renders two FBX characters (ours vs baseline) side by side with different colors,
same camera angle, ground plane, and clean lighting.

Supports two-pass rendering:
  --preview   Fast Eevee preview at low resolution (for layout check)
  (default)   Final Cycles render at full resolution (publication quality)

Usage:
    # Fast preview
    blender --background -noaudio --python template_comparison.py -- \\
        --ours /path/to/ours.fbx --baseline /path/to/baseline.fbx \\
        --frame 60 --output /path/to/comparison.png --preview

    # Final render
    blender --background -noaudio --python template_comparison.py -- \\
        --ours /path/to/ours.fbx --baseline /path/to/baseline.fbx \\
        --frame 60 --output /path/to/comparison.png
"""

import sys
import argparse
import bpy

from blender_utils.scene import (
    setup, set_eevee_renderer, set_cycles_renderer,
    set_output_properties, render_with_progress
)
from blender_utils.camera import set_camera
from blender_utils.lighting import setup_bright_studio_lighting
from blender_utils.material import set_simple_color
from blender_utils.geometry import build_solid_plane
from blender_utils.fbx import load_fbx_at_frame
from blender_utils.colors import blue_ours, red_baseline


def parse_args():
    parser = argparse.ArgumentParser(description="Render method comparison")
    parser.add_argument("--ours", required=True, help="FBX for our method")
    parser.add_argument("--baseline", required=True, help="FBX for baseline")
    parser.add_argument("--frame", type=int, default=60, help="Animation frame")
    parser.add_argument("--output", type=str, default="comparison.png",
                        help="Output file path")
    parser.add_argument("--samples", type=int, default=256, help="Render samples")
    parser.add_argument("--spacing", type=float, default=2.0,
                        help="Distance between the two characters")
    parser.add_argument("--preview", action="store_true",
                        help="Fast Eevee preview at low resolution")
    if '--' in sys.argv:
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    else:
        args = parser.parse_args([])
    return args


def main():
    args = parse_args()
    half = args.spacing / 2

    # 1. Setup
    setup(rgb=(1, 1, 1, 1))

    # 2. Load our method — blue
    arm_ours, mesh_ours = load_fbx_at_frame(
        args.ours, frame=args.frame, x_offset=-half
    )
    for m in mesh_ours:
        set_simple_color(m, blue_ours)

    # 3. Load baseline — red
    arm_base, mesh_base = load_fbx_at_frame(
        args.baseline, frame=args.frame, x_offset=half
    )
    for m in mesh_base:
        set_simple_color(m, red_baseline)

    # 4. Ground plane
    build_solid_plane(color=(0.92, 0.92, 0.92, 1.0),
                      roughness=0.3, metallic=0.0, specular=0.3)

    # 5. Lighting
    setup_bright_studio_lighting(center=(0, 0, 1))

    # 6. Camera
    camera = set_camera(height=1.5, radius=5, focal=50, center=(0, 0, 0.9))

    # 7. Render — two-pass: preview (Eevee) or final (Cycles)
    scene = bpy.context.scene
    if args.preview:
        # Fast preview: Eevee, low resolution
        set_eevee_renderer(scene, camera)
        base, ext = args.output.rsplit('.', 1) if '.' in args.output else (args.output, 'png')
        preview_path = f"{base}_preview.png"
        set_output_properties(scene, output_file_path=preview_path,
                              res_x=960, res_y=540, format='PNG')
        print(f"Preview mode: Eevee @ 960x540 -> {preview_path}")
    else:
        # Final render: Cycles, full resolution
        set_cycles_renderer(scene, camera, num_samples=args.samples)
        set_output_properties(scene, output_file_path=args.output,
                              res_x=1920, res_y=1080, format='PNG')
        print(f"Final mode: Cycles @ 1920x1080, {args.samples} samples -> {args.output}")
    render_with_progress()


if __name__ == "__main__":
    main()
