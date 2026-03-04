"""
Scene setup, rendering engine configuration, and output properties.

Source: thirdparty/BlenderFig/myblender/setup.py (clean_objects, setup,
build_rgb_background, set_eevee_renderer, set_cycles_renderer,
set_output_properties, render_with_progress).
"""

import bpy
import numpy as np
import time


def clean_objects(name='Cube'):
    """Remove a default object by name (e.g. 'Cube', 'Light').

    Args:
        name: Name of the object to remove. No-op if it doesn't exist.
    """
    if name not in bpy.data.objects:
        return
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[name].select_set(True)
    bpy.ops.object.delete(use_global=False)


def setup(rgb=(1, 1, 1, 1)):
    """Initialize a clean scene: remove default Cube/Light and set background.

    Args:
        rgb: Background color as RGBA tuple (default: white opaque).
             Use (1,1,1,0) for transparent background.
    """
    np.random.seed(666)
    scene = bpy.context.scene
    build_rgb_background(scene.world, rgb=rgb, strength=1.)
    clean_objects('Cube')
    clean_objects('Light')


def build_rgb_background(world, rgb=(0.9, 0.9, 0.9, 1.0), strength=1.0):
    """Set a solid-color world background.

    Args:
        world: bpy.types.World object
        rgb: RGBA color tuple
        strength: Background emission strength
    """
    world.use_nodes = True
    node_tree = world.node_tree

    rgb_node = node_tree.nodes.new(type="ShaderNodeRGB")
    rgb_node.outputs["Color"].default_value = rgb

    node_tree.nodes["Background"].inputs["Strength"].default_value = strength
    node_tree.links.new(rgb_node.outputs["Color"],
                        node_tree.nodes["Background"].inputs["Color"])


def set_eevee_renderer(scene, camera_object):
    """Configure Eevee renderer for fast preview rendering.

    Args:
        scene: bpy.types.Scene
        camera_object: Camera object to render from
    """
    scene.camera = camera_object

    try:
        scene.render.engine = 'BLENDER_EEVEE'
    except TypeError:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'

    scene.eevee.taa_render_samples = 16
    try:
        scene.eevee.use_ssr = False
    except AttributeError:
        if hasattr(scene.eevee, 'ssr_enable'):
            scene.eevee.ssr_enable = False
    try:
        scene.eevee.use_ssr_refraction = False
    except AttributeError:
        if hasattr(scene.eevee, 'ssr_refraction_enable'):
            scene.eevee.ssr_refraction_enable = False
    scene.eevee.use_gtao = True
    scene.eevee.gtao_distance = 0.2
    try:
        scene.eevee.use_bloom = False
    except AttributeError:
        if hasattr(scene.eevee, 'bloom_enable'):
            scene.eevee.bloom_enable = False


def set_cycles_renderer(scene, camera_object, num_samples=128,
                        use_denoising=True, use_motion_blur=False,
                        use_transparent_bg=True, prefer_gpu=True,
                        use_adaptive_sampling=False):
    """Configure Cycles renderer with GPU auto-detection.

    Args:
        scene: bpy.types.Scene
        camera_object: Camera object to render from
        num_samples: Number of path-tracing samples (64=draft, 128=default, 512=final)
        use_denoising: Enable denoiser
        use_motion_blur: Enable motion blur
        use_transparent_bg: Transparent film background (for PNG alpha)
        prefer_gpu: Auto-detect and use GPU (Metal/CUDA/OptiX/HIP)
        use_adaptive_sampling: Enable adaptive sampling
    """
    scene.camera = camera_object
    scene.render.engine = 'CYCLES'
    scene.render.use_motion_blur = use_motion_blur
    scene.render.film_transparent = use_transparent_bg
    scene.view_layers[0].cycles.use_denoising = use_denoising
    scene.cycles.use_adaptive_sampling = use_adaptive_sampling
    scene.cycles.samples = num_samples

    if prefer_gpu:
        bpy.context.scene.cycles.device = "GPU"

        import sys
        if sys.platform == "darwin":
            compute_device_types = ["METAL", "NONE"]
        else:
            compute_device_types = ["CUDA", "OPTIX", "HIP", "NONE"]

        cycles_prefs = bpy.context.preferences.addons["cycles"].preferences
        device_set = False

        for device_type in compute_device_types:
            try:
                cycles_prefs.compute_device_type = device_type
                cycles_prefs.get_devices()
                gpu_devices = [d for d in cycles_prefs.devices if d.type != 'CPU']
                if gpu_devices or device_type == "NONE":
                    print(f"Using compute device type: {device_type}")
                    device_set = True
                    break
            except Exception as e:
                print(f"Could not use {device_type}: {e}")
                continue

        if not device_set:
            print("No GPU device found, using CPU instead.")
            bpy.context.scene.cycles.device = "CPU"

    bpy.context.preferences.addons["cycles"].preferences.get_devices()
    for d in bpy.context.preferences.addons["cycles"].preferences.devices:
        d["use"] = 1

    print("----")
    print("Devices for path tracing:")
    for d in bpy.context.preferences.addons["cycles"].preferences.devices:
        print(f"- {d['name']} (type: {d['type']}, use: {d['use']})")
    print("----")


def set_output_properties(scene, output_file_path="", res_x=1920, res_y=1080,
                          tile_x=1920, tile_y=1080, resolution_percentage=100,
                          format='PNG'):
    """Configure render output: resolution, format, file path.

    Args:
        scene: bpy.types.Scene
        output_file_path: Where to save the rendered image
        res_x: Horizontal resolution in pixels
        res_y: Vertical resolution in pixels
        tile_x: Tile width (older Blender)
        tile_y: Tile height (older Blender)
        resolution_percentage: Scale percentage (100 = full res)
        format: 'PNG', 'JPEG', or 'FFMPEG'
    """
    scene.render.resolution_percentage = resolution_percentage
    scene.render.resolution_x = res_x
    scene.render.resolution_y = res_y
    if hasattr(scene.render, 'tile_x'):
        scene.render.tile_x = tile_x
        scene.render.tile_y = tile_y

    scene.render.filepath = output_file_path
    if format == 'PNG':
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGBA"
    elif format == 'JPEG':
        scene.render.image_settings.file_format = "JPEG"
        scene.render.image_settings.color_mode = "RGB"
    elif format == 'FFMPEG':
        scene.render.image_settings.file_format = "FFMPEG"
        scene.render.image_settings.color_mode = "RGB"
        scene.render.ffmpeg.format = "MPEG4"
        scene.render.ffmpeg.codec = "H264"
    else:
        raise ValueError(f"Unsupported format: {format}")


def render_with_progress(write_still=True):
    """Render the current scene with terminal progress feedback.

    Args:
        write_still: Whether to save the rendered image to file
    """
    scene = bpy.context.scene
    total_samples = scene.cycles.samples if scene.render.engine == 'CYCLES' else 0

    render_start = time.time()

    def render_init(scene):
        print("Render initialized...")

    def render_post(scene):
        elapsed = time.time() - render_start
        print(f"\nRender complete! Total time: {elapsed:.1f}s")

    bpy.app.handlers.render_init.append(render_init)
    bpy.app.handlers.render_post.append(render_post)

    try:
        print(f"\nStarting render... (samples: {total_samples})")
        print(f"Output: {scene.render.filepath}")
        print("-" * 60)

        bpy.ops.render.render(animation=False, write_still=write_still)

        elapsed = time.time() - render_start
        print(f"\n{'=' * 60}")
        print(f"Render complete!")
        print(f"  Samples: {total_samples}")
        print(f"  Time: {elapsed:.1f}s")
        print(f"  Output: {scene.render.filepath}")
        print("=" * 60)
    finally:
        if render_init in bpy.app.handlers.render_init:
            bpy.app.handlers.render_init.remove(render_init)
        if render_post in bpy.app.handlers.render_post:
            bpy.app.handlers.render_post.remove(render_post)
