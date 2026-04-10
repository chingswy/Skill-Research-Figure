"""
Template: Single Mesh/FBX Render (for pipeline module illustrations)

Renders a single FBX character at a specific frame with transparent background.
Output is a clean PNG suitable for \\includegraphics in TikZ pipeline figures.

Supports two-pass rendering:
  --preview   Fast Eevee preview at low resolution (for layout check)
  (default)   Final Cycles render at full resolution (publication quality)

Usage:
    # Fast preview
    blender --background -noaudio --python template_single_render.py -- \\
        /path/to/character.fbx --frame 30 --output /path/to/output.png --preview

    # Final render
    blender --background -noaudio --python template_single_render.py -- \\
        /path/to/character.fbx --frame 30 --output /path/to/output.png
"""

import sys
import argparse
import bpy

from blender_utils.scene import (
    setup, set_eevee_renderer, set_cycles_renderer,
    set_output_properties, render_with_progress
)
from blender_utils.camera import set_camera
from blender_utils.lighting import add_sunlight
from blender_utils.material import set_simple_color
from blender_utils.fbx import load_fbx_at_frame
from blender_utils.colors import blue_ours


def parse_args():
    parser = argparse.ArgumentParser(description="Render a single FBX character")
    parser.add_argument("fbx_path", help="Path to FBX file")
    parser.add_argument("--frame", type=int, default=1, help="Animation frame to render")
    parser.add_argument("--output", type=str, default="render_single.png", help="Output file path")
    parser.add_argument("--samples", type=int, default=128, help="Render samples")
    parser.add_argument("--res", type=int, default=1024, help="Resolution (square)")
    parser.add_argument("--preview", action="store_true",
                        help="Fast Eevee preview at low resolution")
    if '--' in sys.argv:
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    else:
        args = parser.parse_args([])
    return args


def main():
    args = parse_args()

    # 1. Clean scene with transparent background
    setup(rgb=(1, 1, 1, 0))

    # 2. Load FBX at specified frame
    armature, mesh_list = load_fbx_at_frame(
        args.fbx_path, frame=args.frame, x_offset=0
    )

    # 3. Apply solid blue material
    for mesh in mesh_list:
        set_simple_color(mesh, blue_ours)

    # 4. Set up camera — front 3/4 view
    camera = set_camera(height=1.2, radius=3.5, focal=50, center=(0, 0, 0.9))

    # 5. Simple sun light
    add_sunlight(name="KeyLight", location=(3, -2, 5),
                 lookat=(0, 0, 1), strength=5)
    add_sunlight(name="FillLight", location=(-2, -3, 3),
                 lookat=(0, 0, 0.8), strength=2)

    # 6. Render — two-pass: preview (Eevee) or final (Cycles)
    scene = bpy.context.scene
    if args.preview:
        # Fast preview: Eevee, low resolution
        set_eevee_renderer(scene, camera)
        base, ext = args.output.rsplit('.', 1) if '.' in args.output else (args.output, 'png')
        preview_path = f"{base}_preview.png"
        preview_res = max(args.res // 2, 256)
        set_output_properties(scene, output_file_path=preview_path,
                              res_x=preview_res, res_y=preview_res, format='PNG')
        print(f"Preview mode: Eevee @ {preview_res}x{preview_res} -> {preview_path}")
    else:
        # Final render: Cycles, full resolution, transparent bg
        set_cycles_renderer(scene, camera, num_samples=args.samples,
                            use_transparent_bg=True)
        set_output_properties(scene, output_file_path=args.output,
                              res_x=args.res, res_y=args.res, format='PNG')
        print(f"Final mode: Cycles @ {args.res}x{args.res}, {args.samples} samples -> {args.output}")
    render_with_progress()


if __name__ == "__main__":
    main()
