"""
FBX loading, armature handling, animation manipulation.

Source: thirdparty/BlenderFig/myblender/fbxtools.py
      + thirdparty/BlenderFig/myblender/geometry.py (load_fbx, load_smpl_npz, downsample_animation)
"""

import math
import bpy
import numpy as np


# ---------------------------------------------------------------------------
# Object discovery
# ---------------------------------------------------------------------------

def find_armature_and_mesh(obj_names):
    """Find armature and mesh objects from a list of imported object names.

    Args:
        obj_names: List of Blender object name strings

    Returns:
        (armature, mesh_object, mesh_object_list) — first mesh and list of all meshes
    """
    armature = None
    mesh_object = None
    mesh_object_list = []
    for name in obj_names:
        obj = bpy.data.objects[name]
        if obj.type == 'ARMATURE' or (obj.animation_data and obj.animation_data.action):
            armature = obj
        if obj.type == 'MESH' and mesh_object is None:
            mesh_object = obj
        if obj.type == 'MESH':
            mesh_object_list.append(obj)
    return armature, mesh_object, mesh_object_list


# ---------------------------------------------------------------------------
# Animation manipulation
# ---------------------------------------------------------------------------

def shift_action_frames(action, offset):
    """Shift all keyframes in an action by *offset* frames.

    Args:
        action: bpy.types.Action
        offset: Positive = forward, negative = backward
    """
    for fcurve in action.fcurves:
        for kf in fcurve.keyframe_points:
            kf.co.x += offset
            kf.handle_left.x += offset
            kf.handle_right.x += offset


def zero_xy_translation_at_frame(action, target_frame):
    """Zero X and Y translation at *target_frame* by subtracting their values.

    Operates on the armature-level ``location`` channels.

    Args:
        action: bpy.types.Action
        target_frame: The frame at which XY should become 0
    """
    for fcurve in action.fcurves:
        if fcurve.data_path == 'location' and fcurve.array_index in [0, 1]:
            val = fcurve.evaluate(target_frame)
            for kf in fcurve.keyframe_points:
                kf.co.y -= val
                kf.handle_left.y -= val
                kf.handle_right.y -= val


def zero_pelvis_xy_translation_at_frame(action, target_frame):
    """Zero Pelvis/Hips bone XY translation at *target_frame*.

    Args:
        action: bpy.types.Action
        target_frame: Frame at which XY should become 0
    """
    pelvis_names = ['Pelvis', 'pelvis', 'Hips', 'hips', 'Root', 'root',
                    'mixamorig:Hips']
    for fcurve in action.fcurves:
        for pname in pelvis_names:
            dp = f'pose.bones["{pname}"].location'
            if fcurve.data_path == dp and fcurve.array_index in [0, 1]:
                val = fcurve.evaluate(target_frame)
                for kf in fcurve.keyframe_points:
                    kf.co.y -= val
                    kf.handle_left.y -= val
                    kf.handle_right.y -= val
                break


def rotate_animation_trajectory(action, angle_degrees):
    """Rotate XY translation keyframes around the Z axis.

    Args:
        action: bpy.types.Action
        angle_degrees: Rotation angle in degrees (positive = CCW)
    """
    if angle_degrees == 0:
        return
    angle = math.radians(angle_degrees)
    cos_a, sin_a = math.cos(angle), math.sin(angle)

    pelvis_names = ['Pelvis', 'pelvis', 'Hips', 'hips', 'Root', 'root',
                    'mixamorig:Hips']
    data_paths = ['location']
    for pn in pelvis_names:
        data_paths.append(f'pose.bones["{pn}"].location')

    for dp in data_paths:
        fc_x = fc_y = None
        for fc in action.fcurves:
            if fc.data_path == dp:
                if fc.array_index == 0:
                    fc_x = fc
                elif fc.array_index == 1:
                    fc_y = fc
        if fc_x is None or fc_y is None:
            continue
        x_data = [(kf.co.y, kf.handle_left.y, kf.handle_right.y)
                   for kf in fc_x.keyframe_points]
        y_data = [(kf.co.y, kf.handle_left.y, kf.handle_right.y)
                   for kf in fc_y.keyframe_points]
        for i, (kfx, kfy) in enumerate(zip(fc_x.keyframe_points,
                                            fc_y.keyframe_points)):
            xv, xhl, xhr = x_data[i]
            yv, yhl, yhr = y_data[i]
            kfx.co.y = xv * cos_a - yv * sin_a
            kfy.co.y = xv * sin_a + yv * cos_a
            kfx.handle_left.y = xhl * cos_a - yhl * sin_a
            kfy.handle_left.y = xhl * sin_a + yhl * cos_a
            kfx.handle_right.y = xhr * cos_a - yhr * sin_a
            kfy.handle_right.y = xhr * sin_a + yhr * cos_a


def get_mesh_lowest_z(mesh_object_list, depsgraph):
    """Calculate the lowest Z coordinate across all meshes after deformation.

    Args:
        mesh_object_list: List of mesh objects
        depsgraph: bpy.types.Depsgraph

    Returns:
        Minimum Z value in world space
    """
    min_z = float('inf')
    for mesh_obj in mesh_object_list:
        eval_obj = mesh_obj.evaluated_get(depsgraph)
        mesh_data = eval_obj.to_mesh()
        world_matrix = eval_obj.matrix_world
        for vert in mesh_data.vertices:
            wz = (world_matrix @ vert.co).z
            if wz < min_z:
                min_z = wz
        eval_obj.to_mesh_clear()
    return min_z


def downsample_animation(speedup=2.0):
    """Downsample animation keyframes for faster playback.

    Args:
        speedup: Factor (2.0 = keep every 2nd frame → 2x faster)
    """
    if speedup <= 1.0:
        return
    speedup = int(speedup)
    scene = bpy.context.scene
    orig_start = scene.frame_start
    orig_end = scene.frame_end

    animated = [o for o in bpy.data.objects
                if o.animation_data and o.animation_data.action]
    if not animated:
        return

    new_end = orig_start + (orig_end - orig_start) // speedup

    for obj in animated:
        action = obj.animation_data.action
        if not action:
            continue
        for fc in action.fcurves:
            kps = fc.keyframe_points
            if not kps:
                continue
            keep = list(range(0, len(kps), speedup))
            if len(kps) - 1 not in keep:
                keep.append(len(kps) - 1)
            keep = sorted(set(keep))
            for idx in keep:
                kp = kps[idx]
                new_frame = orig_start + (kp.co[0] - orig_start) // speedup
                kp.co[0] = new_frame
                kp.handle_left[0] = new_frame
                kp.handle_right[0] = new_frame
            for idx in reversed(range(len(kps))):
                if idx not in keep:
                    kps.remove(kps[idx])

    scene.frame_start = orig_start
    scene.frame_end = new_end
    print(f"Animation downsampled {speedup}x: {orig_start}-{orig_end} -> {orig_start}-{new_end}")


# ---------------------------------------------------------------------------
# FBX loading
# ---------------------------------------------------------------------------

def load_fbx(filename, default_rotation=(0., 0., 0.), speedup=1.0):
    """Import an FBX file with optional animation downsampling.

    Args:
        filename: Path to .fbx file
        default_rotation: Euler rotation to apply after import
        speedup: Animation speedup factor

    Returns:
        (mesh_object, key, material_name)
    """
    keys_old = set(bpy.data.objects.keys())
    mat_old = set(bpy.data.materials.keys())
    image_old = set(bpy.data.images.keys())

    bpy.ops.import_scene.fbx(filepath=filename)

    keys_new = set(bpy.data.objects.keys())
    mat_new = set(bpy.data.materials.keys())
    image_new = set(bpy.data.images.keys())

    obj_names = [o.name for o in bpy.context.selected_objects]
    if not obj_names:
        obj_names = list(keys_new - keys_old)

    armature, mesh_object, mesh_object_list = find_armature_and_mesh(obj_names)

    if armature and armature.animation_data and armature.animation_data.action:
        action = armature.animation_data.action
        frame_start = int(action.frame_range[0])
        frame_end = int(action.frame_range[1])
        bpy.context.scene.frame_start = frame_start
        bpy.context.scene.frame_end = frame_end
        if speedup > 1.0:
            downsample_animation(speedup)

    current_obj = mesh_object or armature or bpy.data.objects[list(keys_new - keys_old)[0]]
    current_obj.rotation_euler = default_rotation

    key = current_obj.name
    key_image = list(image_new - image_old)
    if key_image:
        key = (key, key_image[0])

    mat = list(mat_new - mat_old)[0] if (mat_new - mat_old) else None
    return current_obj, key, mat


def load_fbx_at_frame(fbx_path, frame, x_offset, y_offset=0, z_offset=0,
                      target_frame=1, z_rotation=0, rotate_trajectory=False):
    """Load FBX and position it so that *frame* becomes *target_frame*.

    Zeros root XY translation at target_frame and applies offsets.
    Adjusts Z so the mesh doesn't penetrate the ground.

    Args:
        fbx_path: Path to .fbx file
        frame: Original animation frame to extract
        x_offset: X-axis positioning offset
        y_offset: Y-axis positioning offset
        z_offset: Z-axis positioning offset
        target_frame: Blender frame where *frame* should appear (default: 1)
        z_rotation: Rotation around Z in degrees
        rotate_trajectory: Also rotate the animation root motion if True

    Returns:
        (armature, mesh_object_list)
    """
    keys_old = set(bpy.data.objects.keys())
    bpy.ops.import_scene.fbx(filepath=fbx_path)
    keys_new = set(bpy.data.objects.keys())
    obj_names = list(keys_new - keys_old)

    armature, mesh_object, mesh_object_list = find_armature_and_mesh(obj_names)

    if armature and armature.animation_data and armature.animation_data.action:
        action = armature.animation_data.action
        fs = int(action.frame_range[0])
        fe = int(action.frame_range[1])
        bpy.context.scene.frame_start = fs
        bpy.context.scene.frame_end = fe
        offset = target_frame - frame
        shift_action_frames(action, offset)
        zero_xy_translation_at_frame(action, target_frame)
        zero_pelvis_xy_translation_at_frame(action, target_frame)

    if armature is None:
        raise ValueError(f"No armature in {fbx_path}. Objects: {obj_names}")

    armature.location.x += x_offset
    armature.location.y += y_offset

    if z_rotation != 0:
        if rotate_trajectory and armature.animation_data and armature.animation_data.action:
            rotate_animation_trajectory(armature.animation_data.action, z_rotation)
        armature.rotation_euler[2] += math.radians(z_rotation)

    bpy.context.scene.frame_set(target_frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    min_z = get_mesh_lowest_z(mesh_object_list, depsgraph)
    if min_z < 0:
        armature.location.z -= min_z
    armature.location.z += z_offset

    return armature, mesh_object_list


def load_smpl_npz(filename, default_rotation=(0., 0., 0.), speedup=1.0):
    """Load an SMPL NPZ animation file (requires smplx addon).

    Args:
        filename: Path to .npz file
        default_rotation: Euler rotation after import
        speedup: Animation speedup factor

    Returns:
        (smplx_object, key, material_name)
    """
    keys_old = set(bpy.data.objects.keys())
    mat_old = set(bpy.data.materials.keys())
    image_old = set(bpy.data.images.keys())

    bpy.ops.object.smplx_add_animation(filepath=filename)

    keys_new = set(bpy.data.objects.keys())
    mat_new = set(bpy.data.materials.keys())
    image_new = set(bpy.data.images.keys())

    key = list(keys_new - keys_old)[0]
    current_obj = bpy.data.objects[key]
    current_obj.rotation_euler = default_rotation

    key_image = list(image_new - image_old)
    if key_image:
        key = (key, key_image[0])
    mat = list(mat_new - mat_old)[0]

    smplx_obj = current_obj
    if "Body" in bpy.data.objects:
        smplx_obj = bpy.data.objects["Body"]
    else:
        for obj in bpy.data.objects:
            if obj.parent == smplx_obj and obj.type == 'MESH':
                smplx_obj = obj
                break

    scene = bpy.context.scene
    if speedup > 1.0 and scene.frame_end > scene.frame_start:
        has_anim = any(o.animation_data and o.animation_data.action
                       for o in bpy.data.objects)
        if has_anim:
            downsample_animation(speedup)

    return smplx_obj, key, mat
