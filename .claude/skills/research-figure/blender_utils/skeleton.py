"""
Skeleton visualization: keypoints as spheres, limbs as cylinders.

Rewritten to use Blender primitives instead of OBJ assets.

Source: thirdparty/BlenderFig/myblender/skeleton.py
"""

import json
import numpy as np
import bpy
from mathutils import Vector

from .material import set_simple_color
from .geometry import orient_along_direction


# ---------------------------------------------------------------------------
# Skeleton topology definitions
# ---------------------------------------------------------------------------

SKELETON_CONFIG = {
    'body25': [
        [1, 0], [2, 1], [3, 2], [4, 3], [5, 1], [6, 5], [7, 6], [8, 1],
        [9, 8], [10, 9], [11, 10], [12, 8], [13, 12], [14, 13], [15, 0],
        [16, 0], [17, 15], [18, 16], [19, 14], [20, 19], [21, 14], [22, 11],
        [23, 22], [24, 11],
    ],
    'body15': [
        [1, 0], [2, 1], [3, 2], [4, 3], [5, 1], [6, 5], [7, 6], [8, 1],
        [9, 8], [10, 9], [11, 10], [12, 8], [13, 12], [14, 13],
    ],
    'panoptic15': [
        [0, 1], [0, 2], [0, 3], [3, 4], [4, 5], [0, 9], [9, 10], [10, 11],
        [2, 6], [2, 12], [6, 7], [7, 8], [12, 13], [13, 14],
    ],
}


# ---------------------------------------------------------------------------
# Primitive creation helpers (replacing OBJ-based functions)
# ---------------------------------------------------------------------------

def _create_sphere(radius, center, color):
    """Create a UV sphere at *center* with *color*."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=center,
                                         segments=16, ring_count=8)
    obj = bpy.context.object
    bpy.ops.object.shade_smooth()
    set_simple_color(obj, color)
    return obj


def _create_limb_cylinder(radius, start, end, color):
    """Create a cylinder connecting *start* and *end* with *color*."""
    start, end = np.array(start), np.array(end)
    length = np.linalg.norm(end - start)
    if length < 1e-6:
        return None
    direction = (end - start) / length
    center = (start + end) / 2

    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=length,
                                        location=center)
    obj = bpy.context.object
    orient_along_direction(obj, direction)
    bpy.ops.object.shade_smooth()
    set_simple_color(obj, color)
    return obj


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_skeleton(skelname):
    """Load skeleton topology from a JSON file.

    Args:
        skelname: Path to JSON file

    Returns:
        Parsed JSON dict
    """
    with open(skelname, 'r') as f:
        return json.load(f)


def add_skeleton(keypoints3d, pid=0, skeltype='body25', mode='line',
                 color=None, frame=None, shadow=True):
    """Render a 3D skeleton as spheres (joints) + cylinders (limbs).

    Args:
        keypoints3d: (N, 3) or (N, 4) array; if 4 columns, last is confidence
        pid: Color index (used if *color* is None)
        skeltype: Skeleton topology name from SKELETON_CONFIG
        mode: 'line' (thin cylinders) or 'ellipsoid' (not supported in primitive mode)
        color: Explicit RGB tuple, or None to derive from pid
        frame: If set, insert a keyframe at this frame
        shadow: Whether limbs cast shadows

    Returns:
        (points, limbs) — lists of Blender objects (or None for low-confidence)
    """
    from .colors import get_rgb

    if color is None:
        c = get_rgb(pid)[:3]
    else:
        c = color[:3]

    kintree = SKELETON_CONFIG[skeltype]
    keypoints3d = np.array(keypoints3d)

    points = []
    for k3d in keypoints3d:
        if len(k3d) == 4 and k3d[3] < 0.01:
            points.append(None)
            continue
        obj = _create_sphere(0.025, k3d[:3], c)
        points.append(obj)

    limbs = []
    for (i, j) in kintree:
        if keypoints3d.shape[1] == 4 and (keypoints3d[i, 3] < 0.01
                                           or keypoints3d[j, 3] < 0.01):
            limbs.append(None)
            continue
        obj = _create_limb_cylinder(0.02, keypoints3d[i, :3], keypoints3d[j, :3], c)
        if obj and not shadow:
            if hasattr(obj, 'visible_shadow'):
                obj.visible_shadow = False
        limbs.append(obj)

    return points, limbs


def update_skeleton(keypoints3d, skeltype, points, limbs, frame,
                    conf_thres=0.0, dist_thres=1.):
    """Update skeleton pose and insert keyframes for animation.

    Args:
        keypoints3d: (N, 4) array with confidence in last column
        skeltype: Skeleton topology name
        points: List of joint sphere objects (from add_skeleton)
        limbs: List of limb cylinder objects (from add_skeleton)
        frame: Blender frame number
        conf_thres: Minimum confidence to update a joint
        dist_thres: Maximum allowed jump distance
    """
    kintree = SKELETON_CONFIG[skeltype]
    keypoints3d = np.array(keypoints3d)
    valid = keypoints3d[:, 3].copy() > conf_thres

    for i in range(keypoints3d.shape[0]):
        if not valid[i] or points[i] is None:
            continue
        target = keypoints3d[i, :3]
        current = np.array(points[i].location)
        if np.linalg.norm(target - current) > dist_thres:
            valid[i] = False
            continue
        points[i].location = target
        points[i].keyframe_insert('location', frame=frame)

    for il, (i, j) in enumerate(kintree):
        if not (valid[i] and valid[j]) or limbs[il] is None:
            continue
        obj = limbs[il]
        start, end = keypoints3d[i, :3], keypoints3d[j, :3]
        length = np.linalg.norm(end - start)
        obj.location = (start + end) / 2
        r = obj.scale[0]
        obj.scale = (r, r, length / 2)
        obj.keyframe_insert('scale', frame=frame)
        orient_along_direction(obj, end - start)
        obj.keyframe_insert('location', frame=frame)
        obj.keyframe_insert('rotation_euler', frame=frame)
