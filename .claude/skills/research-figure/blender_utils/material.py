"""
PBR materials, colors, checkerboard, gradient clay, ghost, and fog.

Source: thirdparty/BlenderFig/myblender/material.py
      + thirdparty/BlenderFig/examples/fig_v2m/render_smpl_seq_teaser.py
        (set_gradient_blue_material, set_transparent_ghost_material, setup_mist_fog)
"""

import bpy
from .colors import get_rgb


# ---------------------------------------------------------------------------
# Core material helpers
# ---------------------------------------------------------------------------

def add_material(name="Material", use_nodes=False, make_node_tree_empty=False):
    """Create a new Blender material.

    Args:
        name: Material name
        use_nodes: Enable the node-based shader editor
        make_node_tree_empty: Remove all default nodes

    Returns:
        bpy.types.Material
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = use_nodes
    if use_nodes and make_node_tree_empty:
        clean_nodes(mat.node_tree.nodes)
    return mat


def clean_nodes(nodes):
    """Remove all nodes from a node tree.

    Args:
        nodes: bpy.types.Nodes collection
    """
    for node in list(nodes):
        nodes.remove(node)


def set_principled_node(principled_node, base_color=(1., 1., 1., 1.),
                        subsurface=0.0, subsurface_color=(1., 1., 1., 1.),
                        subsurface_radius=(1.0, 0.2, 0.1),
                        metallic=0.0, specular=0.5, specular_tint=0.0,
                        roughness=0.5, anisotropic=0.0,
                        anisotropic_rotation=0.0, sheen=0.0,
                        sheen_tint=0.5, clearcoat=0.0,
                        clearcoat_roughness=0.03, ior=1.45,
                        transmission=0.0, transmission_roughness=0.0,
                        alpha=1.0):
    """Set all PBR parameters on a Principled BSDF node.

    Silently skips any input that doesn't exist in the current Blender version.
    """
    _mapping = {
        'Base Color': base_color,
        'Subsurface': subsurface,
        'Subsurface Color': subsurface_color,
        'Subsurface Radius': subsurface_radius,
        'Metallic': metallic,
        'Specular': specular,
        'Specular Tint': specular_tint,
        'Roughness': roughness,
        'Anisotropic': anisotropic,
        'Anisotropic Rotation': anisotropic_rotation,
        'Sheen': sheen,
        'Sheen Tint': sheen_tint,
        'Clearcoat': clearcoat,
        'Clearcoat Roughness': clearcoat_roughness,
        'IOR': ior,
        'Transmission': transmission,
        'Transmission Roughness': transmission_roughness,
        'Alpha': alpha,
    }
    for key, value in _mapping.items():
        try:
            principled_node.inputs[key].default_value = value
        except KeyError:
            pass


def build_pbr_nodes(node_tree, base_color, **kwargs):
    """Set up PBR on an existing Principled BSDF in *node_tree*.

    Args:
        node_tree: Material node tree (must already contain Principled BSDF)
        base_color: RGBA tuple
        **kwargs: Forwarded to set_principled_node
    """
    principled = node_tree.nodes["Principled BSDF"]
    set_principled_node(principled, base_color=base_color, **kwargs)


def set_simple_color(obj, color):
    """Quick solid RGB color on an object using Principled BSDF.

    Args:
        obj: Blender mesh object
        color: RGB tuple (r, g, b) with values 0-1
    """
    mat = bpy.data.materials.new(name="SimpleColor")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs['Base Color'].default_value = (color[0], color[1], color[2], 1.0)
    bsdf.inputs['Roughness'].default_value = 0.5
    bsdf.inputs['Metallic'].default_value = 0.0

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
    obj.active_material = mat


class colorObj:
    """Legacy helper wrapping RGBA + HSV + brightness/contrast for setMat_plastic."""

    def __init__(self, RGBA, H=0.5, S=1.0, V=1.0, B=0.0, C=0.0):
        self.H = H
        self.S = S
        self.V = V
        self.RGBA = RGBA
        self.B = B
        self.C = C


def setMat_plastic(mesh, meshColor, AOStrength=0.0, alpha=1.,
                   roughness=0.1, metallic=0.2, specular=0.6, **kwargs):
    """Apply a plastic material with ambient occlusion.

    Args:
        mesh: Blender mesh object
        meshColor: colorObj instance with RGBA, H, S, V, B, C
        AOStrength: Ambient occlusion gamma strength
        alpha: Material alpha
        roughness: Surface roughness
        metallic: Metallic factor
        specular: Specular factor
    """
    mat = bpy.data.materials.new('MeshMaterial')
    mesh.data.materials.append(mat)
    mesh.active_material = mat
    mat.use_nodes = True
    tree = mat.node_tree

    tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = roughness
    tree.nodes["Principled BSDF"].inputs['Metallic'].default_value = metallic
    try:
        tree.nodes["Principled BSDF"].inputs['Sheen Tint'].default_value = 0
    except KeyError:
        pass
    try:
        tree.nodes["Principled BSDF"].inputs['Specular'].default_value = specular
    except KeyError:
        pass
    tree.nodes["Principled BSDF"].inputs['IOR'].default_value = 1.45
    try:
        tree.nodes["Principled BSDF"].inputs['Transmission'].default_value = 0
    except KeyError:
        pass
    try:
        tree.nodes["Principled BSDF"].inputs['Clearcoat Roughness'].default_value = 0
    except KeyError:
        pass
    tree.nodes["Principled BSDF"].inputs['Alpha'].default_value = alpha

    # AO
    tree.nodes.new('ShaderNodeAmbientOcclusion')
    tree.nodes.new('ShaderNodeGamma')
    MIXRGB = tree.nodes.new('ShaderNodeMixRGB')
    MIXRGB.blend_type = 'MULTIPLY'
    tree.nodes["Gamma"].inputs["Gamma"].default_value = AOStrength
    tree.nodes["Ambient Occlusion"].inputs["Distance"].default_value = 10.0
    tree.nodes["Gamma"].location.x -= 600

    # HSV
    HSVNode = tree.nodes.new('ShaderNodeHueSaturation')
    HSVNode.inputs['Color'].default_value = meshColor.RGBA
    HSVNode.inputs['Saturation'].default_value = meshColor.S
    HSVNode.inputs['Value'].default_value = meshColor.V
    HSVNode.inputs['Hue'].default_value = meshColor.H
    HSVNode.location.x -= 200

    # Brightness/Contrast
    BCNode = tree.nodes.new('ShaderNodeBrightContrast')
    BCNode.inputs['Bright'].default_value = meshColor.B
    BCNode.inputs['Contrast'].default_value = meshColor.C
    BCNode.location.x -= 400

    # Links
    tree.links.new(HSVNode.outputs['Color'], BCNode.inputs['Color'])
    tree.links.new(BCNode.outputs['Color'], tree.nodes['Ambient Occlusion'].inputs['Color'])
    tree.links.new(tree.nodes["Ambient Occlusion"].outputs['Color'], MIXRGB.inputs['Color1'])
    tree.links.new(tree.nodes["Ambient Occlusion"].outputs['AO'], tree.nodes['Gamma'].inputs['Color'])
    tree.links.new(tree.nodes["Gamma"].outputs['Color'], MIXRGB.inputs['Color2'])
    tree.links.new(MIXRGB.outputs['Color'], tree.nodes['Principled BSDF'].inputs['Base Color'])


def set_material_i(mat_or_obj, pid, metallic=0.5, specular=0.5, roughness=0.9,
                   use_plastic=True, **kwargs):
    """Apply color *pid* to a material or mesh object.

    Args:
        mat_or_obj: bpy.types.Material or bpy.types.Object
        pid: Color identifier (int index, hex string, color name, or RGB list)
        use_plastic: If True use setMat_plastic; else plain PBR
    """
    color = get_rgb(pid)
    if not use_plastic:
        if isinstance(mat_or_obj, bpy.types.Object):
            if mat_or_obj.active_material is None:
                new_mat = bpy.data.materials.new('MeshMaterial')
                new_mat.use_nodes = True
                mat_or_obj.data.materials.append(new_mat)
                mat_or_obj.active_material = new_mat
            material = mat_or_obj.active_material
        else:
            material = mat_or_obj
        build_pbr_nodes(material.node_tree, base_color=color,
                        metallic=metallic, specular=specular,
                        roughness=roughness, **kwargs)
    else:
        setMat_plastic(mat_or_obj, colorObj(color, B=0.3))


# ---------------------------------------------------------------------------
# Gradient / Ghost / Fog  (from render_smpl_seq_teaser.py)
# ---------------------------------------------------------------------------

def set_gradient_blue_material(mesh_obj, progress, matname="GradientBlue"):
    """Clay-like gradient blue material with AO, SSS, and fresnel.

    Maps *progress* in [0, 1] from light blue to dark blue.

    Args:
        mesh_obj: Mesh object to apply material to
        progress: 0.0 = lightest, 1.0 = darkest
        matname: Material name

    Returns:
        The created material
    """
    light_blue = (0.55, 0.72, 0.88, 1.0)
    dark_blue = (0.12, 0.28, 0.52, 1.0)

    r = light_blue[0] + (dark_blue[0] - light_blue[0]) * progress
    g = light_blue[1] + (dark_blue[1] - light_blue[1]) * progress
    b = light_blue[2] + (dark_blue[2] - light_blue[2]) * progress
    base_color = (r, g, b, 1.0)
    ao_shadow_color = (r * 0.4, g * 0.4, b * 0.5, 1.0)

    mat = bpy.data.materials.new(name=matname)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (800, 0)

    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (500, 0)

    ao_node = nodes.new(type='ShaderNodeAmbientOcclusion')
    ao_node.location = (-200, 100)
    ao_node.samples = 16
    ao_node.inputs['Distance'].default_value = 0.15

    base_color_node = nodes.new(type='ShaderNodeRGB')
    base_color_node.location = (-400, 200)
    base_color_node.outputs[0].default_value = base_color

    shadow_color_node = nodes.new(type='ShaderNodeRGB')
    shadow_color_node.location = (-400, 0)
    shadow_color_node.outputs[0].default_value = ao_shadow_color

    # Version-compatible mix node
    try:
        mix_color = nodes.new(type='ShaderNodeMix')
        mix_color.data_type = 'RGBA'
        mix_color.blend_type = 'MIX'
        use_new_mix = True
    except Exception:
        mix_color = nodes.new(type='ShaderNodeMixRGB')
        mix_color.blend_type = 'MIX'
        use_new_mix = False
    mix_color.location = (100, 100)

    color_ramp = nodes.new(type='ShaderNodeValToRGB')
    color_ramp.location = (-50, -100)
    color_ramp.color_ramp.elements[0].position = 0.0
    color_ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    color_ramp.color_ramp.elements[1].position = 0.7
    color_ramp.color_ramp.elements[1].color = (1, 1, 1, 1)

    fresnel = nodes.new(type='ShaderNodeFresnel')
    fresnel.location = (100, -200)
    fresnel.inputs['IOR'].default_value = 1.45

    links.new(ao_node.outputs['AO'], color_ramp.inputs['Fac'])
    if use_new_mix:
        links.new(color_ramp.outputs['Color'], mix_color.inputs['Factor'])
        links.new(shadow_color_node.outputs['Color'], mix_color.inputs[6])
        links.new(base_color_node.outputs['Color'], mix_color.inputs[7])
        links.new(mix_color.outputs[2], principled.inputs['Base Color'])
    else:
        links.new(color_ramp.outputs['Color'], mix_color.inputs['Fac'])
        links.new(shadow_color_node.outputs['Color'], mix_color.inputs[1])
        links.new(base_color_node.outputs['Color'], mix_color.inputs[2])
        links.new(mix_color.outputs['Color'], principled.inputs['Base Color'])

    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    principled.inputs['Roughness'].default_value = 0.35
    principled.inputs['Metallic'].default_value = 0.0
    try:
        principled.inputs['Specular IOR Level'].default_value = 0.5
    except KeyError:
        try:
            principled.inputs['Specular'].default_value = 0.5
        except KeyError:
            pass
    try:
        principled.inputs['Subsurface Weight'].default_value = 0.06
        principled.inputs['Subsurface Scale'].default_value = 0.08
        principled.inputs['Subsurface Radius'].default_value = (0.4, 0.4, 0.4)
    except KeyError:
        try:
            principled.inputs['Subsurface'].default_value = 0.04
            principled.inputs['Subsurface Color'].default_value = base_color
            principled.inputs['Subsurface Radius'].default_value = (0.3, 0.3, 0.3)
        except KeyError:
            pass
    try:
        principled.inputs['Sheen Weight'].default_value = 0.1
    except KeyError:
        try:
            principled.inputs['Sheen'].default_value = 0.1
        except KeyError:
            pass
    try:
        principled.inputs['Coat Weight'].default_value = 0.05
        principled.inputs['Coat Roughness'].default_value = 0.3
    except KeyError:
        pass

    mesh_obj.data.materials.clear()
    mesh_obj.data.materials.append(mat)
    return mat


def set_transparent_ghost_material(mesh_obj, progress, matname="GhostMaterial",
                                   alpha=0.3):
    """Semi-transparent ghost material for virtual/predicted characters.

    Args:
        mesh_obj: Mesh object
        progress: 0-1 for gradient color
        matname: Material name
        alpha: Transparency (0=invisible, 1=opaque)

    Returns:
        The created material
    """
    light_color = (0.5, 0.6, 0.9, 1.0)
    dark_color = (0.3, 0.5, 0.75, 1.0)

    r = light_color[0] + (dark_color[0] - light_color[0]) * progress
    g = light_color[1] + (dark_color[1] - light_color[1]) * progress
    b = light_color[2] + (dark_color[2] - light_color[2]) * progress
    base_color = (r, g, b, 1.0)

    mat = bpy.data.materials.new(name=matname)
    mat.use_nodes = True
    mat.blend_method = 'BLEND'
    mat.shadow_method = 'HASHED'
    mat.use_backface_culling = False

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (600, 0)

    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (300, 0)
    principled.inputs['Base Color'].default_value = base_color
    principled.inputs['Alpha'].default_value = alpha
    principled.inputs['Roughness'].default_value = 0.4
    principled.inputs['Metallic'].default_value = 0.0

    try:
        principled.inputs['Emission Color'].default_value = (r * 0.3, g * 0.3, b * 0.4, 1.0)
        principled.inputs['Emission Strength'].default_value = 0.2
    except KeyError:
        try:
            principled.inputs['Emission'].default_value = (r * 0.3, g * 0.3, b * 0.4, 1.0)
        except KeyError:
            pass

    try:
        principled.inputs['Subsurface Weight'].default_value = 0.1
    except KeyError:
        try:
            principled.inputs['Subsurface'].default_value = 0.1
        except KeyError:
            pass

    links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    mesh_obj.data.materials.clear()
    mesh_obj.data.materials.append(mat)
    return mat


def setup_mist_fog(scene, start=5.0, depth=20.0,
                   fog_color=(0.7, 0.8, 0.9), falloff='QUADRATIC'):
    """Compositor-based mist/fog effect.

    Note: Conflicts with Film Transparent — fog replaces transparent background.

    Args:
        scene: bpy.types.Scene
        start: Distance where fog starts
        depth: Fog depth range
        fog_color: RGB tuple for the fog color
        falloff: 'LINEAR', 'QUADRATIC', or 'INVERSE_QUADRATIC'
    """
    scene.view_layers[0].use_pass_mist = True
    scene.world.mist_settings.use_mist = True
    scene.world.mist_settings.start = start
    scene.world.mist_settings.depth = depth
    scene.world.mist_settings.falloff = falloff

    scene.use_nodes = True
    tree = scene.node_tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()

    render_layers = nodes.new(type='CompositorNodeRLayers')
    render_layers.location = (-300, 0)

    fog_color_node = nodes.new(type='CompositorNodeRGB')
    fog_color_node.location = (-100, 200)
    fog_color_node.outputs[0].default_value = (*fog_color, 1.0)

    mix = nodes.new(type='CompositorNodeMixRGB')
    mix.blend_type = 'MIX'
    mix.location = (100, 0)

    composite = nodes.new(type='CompositorNodeComposite')
    composite.location = (400, 0)

    links.new(render_layers.outputs['Mist'], mix.inputs['Fac'])
    links.new(render_layers.outputs['Image'], mix.inputs[1])
    links.new(fog_color_node.outputs['RGBA'], mix.inputs[2])
    links.new(mix.outputs['Image'], composite.inputs['Image'])

    print(f"Fog: start={start}, depth={depth}, falloff={falloff}")
