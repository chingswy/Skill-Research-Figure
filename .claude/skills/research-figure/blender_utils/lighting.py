"""
Light creation and studio lighting setups.

Source: thirdparty/BlenderFig/myblender/setup.py (add_sunlight, add_area_light, add_spot_light)
      + thirdparty/BlenderFig/examples/fig_v2m/render_smpl_seq_teaser.py
        (setup_studio_three_point_lighting, setup_bright_studio_lighting)
"""

import math
import bpy
import numpy as np
from mathutils import Vector


# ---------------------------------------------------------------------------
# Individual light creation
# ---------------------------------------------------------------------------

def add_sunlight(name='Light', location=(10., 0., 5.),
                 rotation=(0., -np.pi / 4, 3.14), lookat=None,
                 strength=4., cast_shadow=True):
    """Add a directional sun light.

    Args:
        name: Object name
        location: Light position
        rotation: Euler rotation (ignored if lookat is set)
        lookat: Target point — overrides rotation
        strength: Emission strength
        cast_shadow: Whether to cast shadows

    Returns:
        The created sun light object
    """
    bpy.ops.object.light_add(type='SUN', location=location)
    sun = bpy.context.object
    if name is not None:
        sun.name = name

    if lookat is not None:
        direction = Vector(np.array(lookat) - np.array(location))
        sun.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    else:
        sun.rotation_euler = rotation

    sun.data.use_nodes = True
    sun.data.node_tree.nodes["Emission"].inputs["Strength"].default_value = strength
    sun.data.use_shadow = cast_shadow
    if hasattr(sun.data, 'cycles'):
        sun.data.cycles.cast_shadow = cast_shadow
    return sun


def add_area_light(name='Light', location=(10., 0., 5.),
                   rotation=(0., -np.pi / 4, 3.14), lookat=None,
                   strength=4., size=1.0, size_y=None, shape='SQUARE'):
    """Add a soft area light.

    Args:
        name: Object name
        location: Light position
        rotation: Euler rotation (ignored if lookat is set)
        lookat: Target point — overrides rotation
        strength: Emission strength
        size: Light size (width)
        size_y: Height for RECTANGLE/ELLIPSE shapes
        shape: 'SQUARE', 'RECTANGLE', 'DISK', or 'ELLIPSE'

    Returns:
        The created area light object
    """
    bpy.ops.object.light_add(type='AREA', location=location)
    area = bpy.context.object
    area.name = name
    area.data.use_nodes = True
    area.data.node_tree.nodes["Emission"].inputs["Strength"].default_value = strength
    area.data.shape = shape
    area.data.size = size
    if size_y is not None and shape in ('RECTANGLE', 'ELLIPSE'):
        area.data.size_y = size_y

    if lookat is not None:
        direction = Vector(np.array(lookat) - np.array(location))
        area.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    else:
        area.rotation_euler = rotation
    return area


def add_spot_light(name='SpotLight', location=(10., 0., 5.),
                   rotation=(0., -np.pi / 4, 3.14), lookat=None,
                   strength=100., spot_size=np.pi / 4, spot_blend=0.15,
                   shadow_soft_size=0.25, cast_shadow=True):
    """Add a cone spot light.

    Args:
        name: Object name
        location: Light position
        rotation: Euler rotation (ignored if lookat is set)
        lookat: Target point — overrides rotation
        strength: Emission strength (spots need higher values, ~100+)
        spot_size: Cone angle in radians
        spot_blend: Edge softness 0-1
        shadow_soft_size: Soft shadow radius
        cast_shadow: Whether to cast shadows

    Returns:
        The created spot light object
    """
    bpy.ops.object.light_add(type='SPOT', location=location)
    spot = bpy.context.object
    if name is not None:
        spot.name = name

    if lookat is not None:
        direction = Vector(np.array(lookat) - np.array(location))
        spot.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    else:
        spot.rotation_euler = rotation

    spot.data.spot_size = spot_size
    spot.data.spot_blend = spot_blend
    spot.data.shadow_soft_size = shadow_soft_size
    spot.data.use_shadow = cast_shadow
    if hasattr(spot.data, 'cycles'):
        spot.data.cycles.cast_shadow = cast_shadow

    spot.data.use_nodes = True
    spot.data.node_tree.nodes["Emission"].inputs["Strength"].default_value = strength
    return spot


# ---------------------------------------------------------------------------
# Studio lighting presets
# ---------------------------------------------------------------------------

def _add_track_to_constraint(light_obj, target_obj):
    """Add a TRACK_TO constraint so a light always aims at a target."""
    constraint = light_obj.constraints.new(type='TRACK_TO')
    constraint.target = target_obj
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'


def setup_studio_three_point_lighting(center=(0, 0, 0), key_strength=800.0):
    """Professional balanced studio lighting: left key + right key + front fill
    (sun) + rim + top + ambient world.  All lights track toward *center*.

    Good for teaser figures with even illumination and minimal shadow bias.

    Args:
        center: Scene center point (subject location)
        key_strength: Area-light intensity for the two key lights

    Returns:
        Tuple (left_key, right_key, front_fill, rim_light, top_light)
    """
    # Create tracking target
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=center)
    target = bpy.context.object
    target.name = "Light_Target"

    # Left Key — large soft area
    bpy.ops.object.light_add(type='AREA',
                             location=(center[0] - 5, center[1] + 4, center[2] + 4))
    left_key = bpy.context.object
    left_key.name = "Left_Key_Light"
    left_key.data.energy = key_strength
    left_key.data.size = 6.0
    left_key.data.color = (1.0, 0.99, 0.97)
    _add_track_to_constraint(left_key, target)

    # Right Key — same intensity for balance
    bpy.ops.object.light_add(type='AREA',
                             location=(center[0] + 5, center[1] + 4, center[2] + 4))
    right_key = bpy.context.object
    right_key.name = "Right_Key_Light"
    right_key.data.energy = key_strength
    right_key.data.size = 6.0
    right_key.data.color = (1.0, 0.99, 0.97)
    _add_track_to_constraint(right_key, target)

    # Front Fill — sun for even base illumination
    bpy.ops.object.light_add(type='SUN',
                             location=(center[0], center[1] + 6, center[2] + 2))
    front_fill = bpy.context.object
    front_fill.name = "Front_Fill_Light"
    front_fill.data.energy = 1.0
    front_fill.data.color = (1.0, 1.0, 1.0)
    _add_track_to_constraint(front_fill, target)

    # Rim / Back
    bpy.ops.object.light_add(type='AREA',
                             location=(center[0], center[1] - 4, center[2] + 3))
    rim_light = bpy.context.object
    rim_light.name = "Rim_Light"
    rim_light.data.energy = key_strength * 0.3
    rim_light.data.size = 5.0
    rim_light.data.color = (1.0, 1.0, 1.0)
    _add_track_to_constraint(rim_light, target)

    # Top
    bpy.ops.object.light_add(type='AREA',
                             location=(center[0], center[1], center[2] + 6))
    top_light = bpy.context.object
    top_light.name = "Top_Light"
    top_light.data.energy = key_strength * 0.4
    top_light.data.size = 12.0
    top_light.data.color = (1.0, 1.0, 1.0)
    _add_track_to_constraint(top_light, target)

    # World ambient
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()
    bg = nodes.new(type='ShaderNodeBackground')
    bg.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs['Strength'].default_value = 1.0
    out = nodes.new(type='ShaderNodeOutputWorld')
    out.location = (200, 0)
    links.new(bg.outputs['Background'], out.inputs['Surface'])

    # AO hints
    scene = bpy.context.scene
    if scene.render.engine == 'CYCLES':
        scene.cycles.use_fast_gi = False
        try:
            scene.cycles.ao_bounces = 2
            scene.cycles.ao_bounces_render = 2
        except Exception:
            pass
    try:
        scene.eevee.use_gtao = True
        scene.eevee.gtao_distance = 0.5
        scene.eevee.gtao_factor = 1.2
    except Exception:
        pass

    print(f"Studio balanced lighting: key={key_strength}, symmetric left/right")
    return left_key, right_key, front_fill, rim_light, top_light


def setup_bright_studio_lighting(center=(0, 0, 0), key_strength=8.0,
                                 sun_angle=0.02):
    """Sun-based key light from left-back 45 deg + fill + rim + bright ambient.
    Good for clear shadow renders and comparison figures.

    Args:
        center: Scene center point
        key_strength: Sun light energy
        sun_angle: Angular diameter (smaller = sharper shadows)

    Returns:
        Tuple (sun, fill_light, rim_light)
    """
    # Key Sun — left-back 45 deg
    bpy.ops.object.light_add(type='SUN',
                             location=(center[0], center[1], center[2] + 10))
    sun = bpy.context.object
    sun.name = "Key_Sun_Light"
    sun.data.energy = key_strength
    sun.data.angle = sun_angle
    sun.rotation_euler = (math.radians(45), 0, math.radians(-135))

    # Fill — soft area from right-front
    bpy.ops.object.light_add(type='AREA',
                             location=(center[0] + 5, center[1] + 3, center[2] + 4))
    fill = bpy.context.object
    fill.name = "Fill_Light"
    fill.data.energy = key_strength * 0.3
    fill.data.size = 5.0
    fill.rotation_euler = (math.radians(60), 0, math.radians(30))

    # Rim — edge light from behind
    bpy.ops.object.light_add(type='AREA',
                             location=(center[0], center[1] - 4, center[2] + 3))
    rim = bpy.context.object
    rim.name = "Rim_Light"
    rim.data.energy = key_strength * 0.4
    rim.data.size = 3.0
    rim.rotation_euler = (math.radians(120), 0, 0)

    # Bright world
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()
    bg = nodes.new(type='ShaderNodeBackground')
    bg.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs['Strength'].default_value = 0.8
    out = nodes.new(type='ShaderNodeOutputWorld')
    out.location = (200, 0)
    links.new(bg.outputs['Background'], out.inputs['Surface'])

    print(f"Bright studio lighting: key={key_strength}, sharp shadows left-back 45 deg")
    return sun, fill, rim
