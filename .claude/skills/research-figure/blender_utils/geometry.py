"""
Geometric primitives, arrows, bounding boxes, ground planes, backdrop, trajectory.

All functions use Blender primitives (primitive_plane_add, primitive_cube_add, etc.)
instead of OBJ asset files.

Source: thirdparty/BlenderFig/myblender/geometry.py
      + thirdparty/BlenderFig/examples/fig_v2m/render_smpl_seq_teaser.py
        (create_studio_backdrop, add_reflection_to_ground, add_root_trajectory)
"""

import math
import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

from .material import (
    add_material, set_material_i, set_principled_node,
    set_simple_color, clean_nodes,
)


# ---------------------------------------------------------------------------
# Orientation helpers
# ---------------------------------------------------------------------------

def orient_along_direction(obj, direction):
    """Orient an object (whose default axis is +Z) to point in *direction*.

    Args:
        obj: Blender object
        direction: (dx, dy, dz) target direction
    """
    direction = np.array(direction, dtype=float)
    direction /= np.linalg.norm(direction)
    z_axis = Vector((0, 0, 1))
    rot_quat = z_axis.rotation_difference(Vector(direction))
    obj.rotation_euler = rot_quat.to_euler()


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

def create_plane_blender(location=(0, 0, 0), rotation=(0, 0, 0), size=2.0,
                         name=None, shadow=True):
    """Create a Blender primitive plane.

    Args:
        location: (x, y, z)
        rotation: Euler rotation
        size: Plane diameter
        name: Object name
        shadow: Whether the plane casts shadows

    Returns:
        The plane object
    """
    bpy.ops.mesh.primitive_plane_add(size=size, location=location, rotation=rotation)
    obj = bpy.context.object
    if name is not None:
        obj.name = name
    if not shadow:
        if hasattr(obj, 'visible_shadow'):
            obj.visible_shadow = False
        else:
            try:
                obj.cycles_visibility.shadow = False
            except Exception:
                pass
    return obj


def build_plane(translation=(-1., -1., 0.), plane_size=8., alpha=1,
                use_transparent=False, white=(1., 1., 1., 1.),
                black=(0., 0., 0., 0.), roughness=0.5, metallic=0.0,
                specular=0.5):
    """Build a checkerboard ground plane.

    Args:
        translation: Plane center position
        plane_size: Size of the plane
        alpha: Transparency
        use_transparent: Use transparent shader instead of Principled BSDF
        white: Color for white squares (RGBA)
        black: Color for black squares (RGBA)
        roughness: Surface roughness
        metallic: Metallic factor
        specular: Specular intensity

    Returns:
        The plane object
    """
    plane = create_plane_blender(size=plane_size, name="Floor")
    plane.location = translation
    floor_mat = add_material("Material_Plane", use_nodes=True, make_node_tree_empty=True)

    nt = floor_mat.node_tree
    output_node = nt.nodes.new(type='ShaderNodeOutputMaterial')
    checker = nt.nodes.new(type='ShaderNodeTexChecker')
    checker.inputs['Scale'].default_value = plane_size

    if use_transparent:
        shader = nt.nodes.new(type='ShaderNodeBsdfTransparent')
        nt.links.new(checker.outputs['Color'], shader.inputs['Color'])
    else:
        shader = nt.nodes.new(type='ShaderNodeBsdfPrincipled')
        set_principled_node(shader, alpha=alpha, roughness=roughness,
                            metallic=metallic, specular=specular)
        nt.links.new(checker.outputs['Color'], shader.inputs['Base Color'])

    nt.links.new(shader.outputs[0], output_node.inputs['Surface'])
    nt.nodes["Checker Texture"].inputs[1].default_value = white
    nt.nodes["Checker Texture"].inputs[2].default_value = black

    plane.data.materials.append(floor_mat)
    return plane


def build_solid_plane(translation=(0., 0., 0.), plane_size=100.,
                      color=(0.02, 0.02, 0.02, 1.0),
                      roughness=0.1, metallic=0.5, specular=0.5):
    """Build a solid-color reflective ground plane.

    Args:
        translation: Plane center position
        plane_size: Size
        color: RGBA color
        roughness: Surface roughness
        metallic: Metallic factor
        specular: Specular intensity

    Returns:
        The plane object
    """
    plane = create_plane_blender(size=plane_size, name="Floor")
    plane.location = translation
    floor_mat = add_material("Material_Plane", use_nodes=True, make_node_tree_empty=False)
    principled = floor_mat.node_tree.nodes["Principled BSDF"]
    principled.inputs['Base Color'].default_value = color
    principled.inputs['Roughness'].default_value = roughness
    principled.inputs['Metallic'].default_value = metallic
    try:
        principled.inputs['Specular'].default_value = specular
    except KeyError:
        pass
    plane.data.materials.append(floor_mat)
    return plane


# ---------------------------------------------------------------------------
# Arrows and axes
# ---------------------------------------------------------------------------

def create_simple_arrow(start, end, color=(1, 0, 0),
                        cylinder_radius=0.02, cone_radius=0.04,
                        cone_height=0.1):
    """Create an arrow from start to end using Blender primitives.

    Args:
        start: Start point (x, y, z)
        end: End point (x, y, z)
        color: RGB color
        cylinder_radius: Arrow shaft radius
        cone_radius: Arrow head base radius
        cone_height: Arrow head height

    Returns:
        Tuple (cylinder, cone) objects, or (None, None) if degenerate
    """
    start, end = np.array(start), np.array(end)
    length = np.linalg.norm(end - start)
    if length < 1e-6:
        return None, None
    direction = (end - start) / length

    shaft_length = max(length - cone_height, 0.01)
    shaft_end = start + direction * shaft_length
    shaft_center = (start + shaft_end) / 2

    bpy.ops.mesh.primitive_cylinder_add(radius=cylinder_radius,
                                        depth=shaft_length,
                                        location=shaft_center)
    cylinder = bpy.context.object
    orient_along_direction(cylinder, direction)
    set_simple_color(cylinder, color)
    cylinder.visible_shadow = False

    bpy.ops.mesh.primitive_cone_add(radius1=cone_radius, radius2=0,
                                    depth=cone_height,
                                    location=shaft_end + direction * cone_height / 2)
    cone = bpy.context.object
    orient_along_direction(cone, direction)
    set_simple_color(cone, color)
    cone.visible_shadow = False

    return cylinder, cone


def create_coordinate_axes(origin=(0, 0, 0), length=1.0,
                           cylinder_radius=0.02, cone_radius=0.04,
                           cone_height=0.1):
    """Create RGB coordinate axes (X=Red, Y=Green, Z=Blue).

    Returns:
        Dict with 'x', 'y', 'z' keys, each (cylinder, cone) tuple
    """
    origin = np.array(origin)
    return {
        'x': create_simple_arrow(origin, origin + [length, 0, 0], (1, 0, 0),
                                 cylinder_radius, cone_radius, cone_height),
        'y': create_simple_arrow(origin, origin + [0, length, 0], (0, 1, 0),
                                 cylinder_radius, cone_radius, cone_height),
        'z': create_simple_arrow(origin, origin + [0, 0, length], (0, 0, 1),
                                 cylinder_radius, cone_radius, cone_height),
    }


# ---------------------------------------------------------------------------
# Bounding box, camera visualization, volume cube
# ---------------------------------------------------------------------------

def create_bbox3d(scale=(1., 1., 1.), location=(0., 0., 0.),
                  rotation=None, pid=0):
    """Create a wireframe 3D bounding box.

    Args:
        scale: Half-extents (sx, sy, sz)
        location: Center position
        rotation: Quaternion rotation (optional)
        pid: Color identifier
    """
    bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD')
    bpy.ops.object.modifier_add(type='WIREFRAME')
    obj = bpy.context.object
    obj.modifiers["Wireframe"].thickness = 0.04
    add_material_to_blender_primitive(obj, pid)
    if rotation is not None:
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = rotation
    else:
        obj.rotation_euler = (0, 0, 0)
    obj.scale = scale
    obj.location = location
    if hasattr(obj, 'visible_shadow'):
        obj.visible_shadow = False
    try:
        obj.cycles_visibility.shadow = False
    except Exception:
        pass


def add_material_to_blender_primitive(obj, pid):
    """Add a PBR material colored by *pid* to a Blender primitive.

    Args:
        obj: Blender object
        pid: Color identifier
    """
    matname = "Material_{}".format(obj.name)
    mat = add_material(matname, use_nodes=True, make_node_tree_empty=False)
    obj.data.materials.append(mat)
    set_material_i(bpy.data.materials[matname], pid, use_plastic=False)


def create_camera_blender(R, T, scale=0.1, pid=0):
    """Create a camera frustum visualization mesh.

    Args:
        R: 3x3 rotation matrix
        T: 3x1 translation vector
        scale: Frustum size
        pid: Color identifier

    Returns:
        The camera visualization object
    """
    bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD')
    obj = bpy.context.object
    obj.scale = (scale, scale, scale)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    for i in [0, 2, 4, 6]:
        bm.verts[i].select_set(True)
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.mesh.merge(type='CENTER')
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.modifier_add(type='WIREFRAME')
    obj.modifiers["Wireframe"].thickness = 0.1
    add_material_to_blender_primitive(obj, pid)
    center = -R.T @ T
    obj.location = center.T[0]
    obj.rotation_euler = Matrix(R.T).to_euler()
    if hasattr(obj, 'visible_shadow'):
        obj.visible_shadow = False
    return obj


def create_camera_blender_animated(camera_RT, scale=0.1, pid=0,
                                   start_frame=0, convert_axis=True):
    """Create an animated camera visualization from world-to-camera matrices.

    Args:
        camera_RT: (N, 3, 4) or (N, 4, 4) array of [R|T] matrices
        scale: Frustum size
        pid: Color identifier
        start_frame: Starting Blender frame
        convert_axis: Convert Y-up to Z-up if True

    Returns:
        The animated camera object
    """
    if convert_axis:
        axis_convert = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], dtype=np.float64)
    else:
        axis_convert = np.eye(3)

    bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD')
    obj = bpy.context.object
    obj.scale = (scale, scale, scale)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    for i in [0, 2, 4, 6]:
        bm.verts[i].select_set(True)
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.mesh.merge(type='CENTER')
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.modifier_add(type='WIREFRAME')
    obj.modifiers["Wireframe"].thickness = 0.1
    add_material_to_blender_primitive(obj, pid)
    if hasattr(obj, 'visible_shadow'):
        obj.visible_shadow = False

    num_frames = camera_RT.shape[0]
    for fi in range(num_frames):
        R = camera_RT[fi, :3, :3]
        T = camera_RT[fi, :3, 3:4]
        center = axis_convert @ (-R.T @ T)
        R_conv = axis_convert @ R @ axis_convert.T
        obj.location = (center[0, 0], center[1, 0], center[2, 0])
        obj.rotation_euler = Matrix(R_conv.T).to_euler()
        frame = start_frame + fi
        obj.keyframe_insert(data_path="location", frame=frame)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame)

    return obj


def create_volume_cube(location=(0., 0., 5.), size=20., density=0.05,
                       anisotropy=0.3, name="VolumeCube"):
    """Create a volumetric lighting cube (god rays / Tyndall effect).

    Args:
        location: Center position
        size: Cube size
        density: Volume density (0.01-0.1)
        anisotropy: Scattering direction (-1 to 1, positive = forward)
        name: Object name

    Returns:
        The volume cube object
    """
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    cube = bpy.context.object
    cube.name = name

    vol_mat = bpy.data.materials.new(name=f"{name}_Material")
    vol_mat.use_nodes = True
    nodes = vol_mat.node_tree.nodes
    links = vol_mat.node_tree.links
    nodes.clear()

    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    volume = nodes.new(type='ShaderNodeVolumePrincipled')
    volume.inputs['Color'].default_value = (1, 1, 1, 1)
    volume.inputs['Density'].default_value = density
    volume.inputs['Anisotropy'].default_value = anisotropy
    links.new(volume.outputs['Volume'], output.inputs['Volume'])

    cube.data.materials.append(vol_mat)
    if hasattr(cube, 'visible_shadow'):
        cube.visible_shadow = False
        cube.visible_diffuse = False
        cube.visible_glossy = False
    else:
        try:
            cube.cycles_visibility.shadow = False
            cube.cycles_visibility.diffuse = False
            cube.cycles_visibility.glossy = False
        except Exception:
            pass
    return cube


def bound_from_keypoint(keypoint, padding=0.1, min_z=0):
    """Compute bounding box from skeleton keypoints.

    Args:
        keypoint: (..., 3+1) array with last channel as confidence
        padding: Bounding box padding
        min_z: Minimum Z value

    Returns:
        (center, scale, bounds) tuple
    """
    v = keypoint[..., -1]
    k3d_flat = keypoint[v > 0.01]
    lower = k3d_flat[:, :3].min(axis=0)
    lower[2] = max(min_z, lower[2])
    upper = k3d_flat[:, :3].max(axis=0)
    center = (lower + upper) / 2
    scale = upper - lower
    return center, scale, np.stack([lower, upper])


# ---------------------------------------------------------------------------
# Studio backdrop and ground reflection  (from render_smpl_seq_teaser.py)
# ---------------------------------------------------------------------------

def create_studio_backdrop(center=(0, 0, 0), width=20, depth=15, height=10,
                           bevel_radius=3.0, color=(0.95, 0.95, 0.95, 1.0)):
    """Create an L-shaped seamless studio backdrop (cyclorama).

    Args:
        center: Center position
        width: Backdrop width (X)
        depth: Depth (Y)
        height: Back wall height
        bevel_radius: Curved floor-to-wall transition radius
        color: Background color RGBA

    Returns:
        The backdrop object
    """
    mesh = bpy.data.meshes.new("StudioBackdrop")
    obj = bpy.data.objects.new("StudioBackdrop", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    half_width = width / 2

    v_fl = bm.verts.new((center[0] - half_width, center[1] + depth, 0))
    v_fr = bm.verts.new((center[0] + half_width, center[1] + depth, 0))
    v_bl = bm.verts.new((center[0] - half_width, center[1] - depth + bevel_radius, 0))
    v_br = bm.verts.new((center[0] + half_width, center[1] - depth + bevel_radius, 0))
    bm.faces.new([v_fl, v_fr, v_br, v_bl])

    num_segments = 16
    curve_left = [v_bl]
    curve_right = [v_br]
    for i in range(1, num_segments + 1):
        angle = (math.pi / 2) * (i / num_segments)
        y = center[1] - depth + bevel_radius - bevel_radius * math.sin(angle)
        z = bevel_radius - bevel_radius * math.cos(angle)
        curve_left.append(bm.verts.new((center[0] - half_width, y, z)))
        curve_right.append(bm.verts.new((center[0] + half_width, y, z)))

    for i in range(len(curve_left) - 1):
        bm.faces.new([curve_left[i], curve_right[i],
                       curve_right[i + 1], curve_left[i + 1]])

    v_tl = bm.verts.new((center[0] - half_width, center[1] - depth, height))
    v_tr = bm.verts.new((center[0] + half_width, center[1] - depth, height))
    bm.faces.new([curve_left[-1], curve_right[-1], v_tr, v_tl])

    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True

    mat = bpy.data.materials.new(name="StudioBackdropMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (100, 0)
    principled.inputs['Base Color'].default_value = color
    principled.inputs['Roughness'].default_value = 0.5
    principled.inputs['Metallic'].default_value = 0.0
    links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    obj.data.materials.append(mat)

    return obj


def add_reflection_to_ground(ground, roughness=0.15, metallic=0.1,
                             specular=0.8,
                             white_color=(1.0, 1.0, 1.0, 1.0),
                             gray_color=(0.85, 0.85, 0.85, 1.0)):
    """Add reflective properties to an existing checkerboard ground.

    Args:
        ground: Ground plane object
        roughness: Surface roughness (lower = more mirror)
        metallic: Metallic factor
        specular: Specular intensity
        white_color: Checker white square color
        gray_color: Checker dark square color
    """
    if len(ground.data.materials) == 0:
        return
    mat = ground.data.materials[0]
    if not mat.use_nodes:
        return
    nodes = mat.node_tree.nodes

    for node in nodes:
        if node.type == 'TEX_CHECKER':
            node.inputs['Color1'].default_value = white_color
            node.inputs['Color2'].default_value = gray_color
            break

    for node in nodes:
        if node.type == 'BSDF_PRINCIPLED':
            node.inputs['Roughness'].default_value = roughness
            node.inputs['Metallic'].default_value = metallic
            try:
                node.inputs['Specular IOR Level'].default_value = specular
            except KeyError:
                try:
                    node.inputs['Specular'].default_value = specular
                except KeyError:
                    pass
            break

    ground.visible_shadow = True


# ---------------------------------------------------------------------------
# Root trajectory
# ---------------------------------------------------------------------------

def add_root_trajectory(positions, start_color=(0.2, 0.6, 1.0, 1.0),
                        end_color=(1.0, 0.3, 0.5, 1.0),
                        line_thickness=0.02, emission_strength=3.0,
                        alpha=1.0, curve_name="RootTrajectory",
                        extend_start=0.6, extend_end=0.6,
                        add_arrow=True, arrow_scale=1.0):
    """Add a gradient trajectory curve with optional arrowhead.

    Args:
        positions: List of mathutils.Vector or (x,y,z) tuples for curve points
        start_color: RGBA at the curve start
        end_color: RGBA at the curve end
        line_thickness: Bevel depth
        emission_strength: Glow intensity
        alpha: Transparency
        curve_name: Object name
        extend_start: Meters to extend before first point
        extend_end: Meters to extend after last point
        add_arrow: Whether to add a cone arrowhead
        arrow_scale: Scale factor for arrowhead size

    Returns:
        The curve object
    """
    positions = [Vector(p) for p in positions]

    bpy.context.view_layer.update()

    if extend_start > 0 and len(positions) >= 2:
        d = (positions[0] - positions[1]).normalized()
        positions.insert(0, positions[0] + d * extend_start)
    if extend_end > 0 and len(positions) >= 2:
        d = (positions[-1] - positions[-2]).normalized()
        positions.append(positions[-1] + d * extend_end)

    # Auto-swap colors if trajectory goes right-to-left
    if len(positions) >= 2 and positions[-1].x < positions[0].x:
        start_color, end_color = end_color, start_color

    arrow_color = start_color

    curve_data = bpy.data.curves.new(curve_name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 12
    curve_data.bevel_depth = line_thickness
    curve_data.bevel_resolution = 4
    curve_data.fill_mode = 'FULL'

    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(len(positions) - 1)
    for i, pos in enumerate(positions):
        bp = spline.bezier_points[i]
        bp.co = pos
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    curve_obj = bpy.data.objects.new(curve_name, curve_data)
    bpy.context.collection.objects.link(curve_obj)

    # Gradient material
    mat = bpy.data.materials.new(name=f"{curve_name}_Material")
    mat.use_nodes = True
    if alpha < 1.0:
        mat.blend_method = 'BLEND'
        mat.shadow_method = 'HASHED'

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new(type='ShaderNodeOutputMaterial')
    out.location = (600, 0)
    mix_sh = nodes.new(type='ShaderNodeMixShader')
    mix_sh.location = (400, 0)
    mix_sh.inputs['Fac'].default_value = 0.7

    principled = nodes.new(type='ShaderNodeBsdfPrincipled')
    principled.location = (200, -150)
    principled.inputs['Roughness'].default_value = 0.3
    principled.inputs['Metallic'].default_value = 0.2
    principled.inputs['Alpha'].default_value = alpha

    emission = nodes.new(type='ShaderNodeEmission')
    emission.location = (200, 100)
    emission.inputs['Strength'].default_value = emission_strength

    ramp = nodes.new(type='ShaderNodeValToRGB')
    ramp.location = (-100, 0)
    ramp.color_ramp.elements[0].color = start_color
    ramp.color_ramp.elements[1].color = end_color
    mid = ramp.color_ramp.elements.new(0.5)
    mid.color = ((start_color[0] + end_color[0]) * 0.5 + 0.2,
                 (start_color[1] + end_color[1]) * 0.3,
                 (start_color[2] + end_color[2]) * 0.6, 1.0)

    tc = nodes.new(type='ShaderNodeTexCoord')
    tc.location = (-500, 0)
    sep = nodes.new(type='ShaderNodeSeparateXYZ')
    sep.location = (-300, 0)

    links.new(tc.outputs['Generated'], sep.inputs['Vector'])
    links.new(sep.outputs['X'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], emission.inputs['Color'])
    links.new(ramp.outputs['Color'], principled.inputs['Base Color'])
    links.new(principled.outputs['BSDF'], mix_sh.inputs[1])
    links.new(emission.outputs['Emission'], mix_sh.inputs[2])
    links.new(mix_sh.outputs['Shader'], out.inputs['Surface'])

    curve_obj.data.materials.append(mat)

    # Arrowhead
    if add_arrow and len(positions) >= 2:
        arrow_dir = (positions[-1] - positions[-2]).normalized()
        arrow_pos = positions[-1]
        ah = line_thickness * 8 * arrow_scale
        ar = line_thickness * 2 * arrow_scale

        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=ar, radius2=0,
                                        depth=ah, location=arrow_pos)
        arrow_obj = bpy.context.active_object
        arrow_obj.name = f"{curve_name}_Arrow"

        z_axis = Vector((0, 0, 1))
        rot_axis = z_axis.cross(arrow_dir)
        if rot_axis.length > 1e-4:
            rot_axis.normalize()
            angle = math.acos(max(-1, min(1, z_axis.dot(arrow_dir))))
            arrow_obj.matrix_world = (Matrix.Translation(arrow_pos)
                                      @ Matrix.Rotation(angle, 4, rot_axis))
            arrow_obj.location = arrow_pos + arrow_dir * (ah * 0.5)
        else:
            if arrow_dir.z < 0:
                arrow_obj.rotation_euler = (math.pi, 0, 0)
            arrow_obj.location = arrow_pos + arrow_dir * (ah * 0.5)

        # Arrow material
        amat = bpy.data.materials.new(name=f"{curve_name}_Arrow_Material")
        amat.use_nodes = True
        if alpha < 1.0:
            amat.blend_method = 'BLEND'
            amat.shadow_method = 'HASHED'
        an = amat.node_tree.nodes
        al = amat.node_tree.links
        an.clear()
        a_out = an.new(type='ShaderNodeOutputMaterial')
        a_out.location = (600, 0)
        a_mix = an.new(type='ShaderNodeMixShader')
        a_mix.location = (400, 0)
        a_mix.inputs['Fac'].default_value = 0.7
        a_pr = an.new(type='ShaderNodeBsdfPrincipled')
        a_pr.location = (200, -150)
        a_pr.inputs['Roughness'].default_value = 0.3
        a_pr.inputs['Metallic'].default_value = 0.2
        a_pr.inputs['Alpha'].default_value = alpha
        a_pr.inputs['Base Color'].default_value = arrow_color
        a_em = an.new(type='ShaderNodeEmission')
        a_em.location = (200, 100)
        a_em.inputs['Strength'].default_value = emission_strength
        a_em.inputs['Color'].default_value = arrow_color
        al.new(a_pr.outputs['BSDF'], a_mix.inputs[1])
        al.new(a_em.outputs['Emission'], a_mix.inputs[2])
        al.new(a_mix.outputs['Shader'], a_out.inputs['Surface'])
        arrow_obj.data.materials.append(amat)

    return curve_obj
