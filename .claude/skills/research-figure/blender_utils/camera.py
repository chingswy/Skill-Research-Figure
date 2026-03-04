"""
Camera positioning, intrinsics, and extrinsics.

Source: thirdparty/BlenderFig/myblender/geometry.py (set_camera, look_at)
      + thirdparty/BlenderFig/myblender/camera.py (intrinsics/extrinsics)
"""

import bpy
import numpy as np
from mathutils import Matrix, Vector, Euler


def look_at(obj_camera, point):
    """Orient any object (typically a camera) to look at a point.

    Args:
        obj_camera: Blender object to orient
        point: Target point as Vector, tuple, or numpy array
    """
    loc_camera = obj_camera.location
    direction = Vector(point) - Vector(loc_camera)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    obj_camera.rotation_euler = rot_quat.to_euler()


def set_camera(height=5., radius=9, focal=40, center=(0., 0., 0.),
               location=None, rotation=None, frame=None, camera=None):
    """Position and configure the scene camera.

    Args:
        height: Camera height (used when location is None)
        radius: Camera distance from center (used when location is None)
        focal: Focal length in mm
        center: Look-at target point (used when rotation is None)
        location: Explicit camera position (overrides height/radius)
        rotation: Explicit Euler rotation in radians (overrides center look-at)
        frame: If set, insert a keyframe at this frame
        camera: Camera object (defaults to bpy.data.objects['Camera'])

    Returns:
        The camera object
    """
    if camera is None:
        camera = bpy.data.objects['Camera']

    if location is None:
        theta = 0.
        camera.location = (radius * np.sin(theta), -radius * np.cos(theta), height)
    else:
        camera.location = location

    if rotation is None:
        look_at(camera, Vector(center))
    else:
        camera.rotation_euler = Euler(rotation, 'XYZ')

    camera.data.lens = focal

    if frame is not None:
        camera.keyframe_insert(data_path="location", frame=frame)
        camera.keyframe_insert(data_path="rotation_euler", frame=frame)

    return camera


def get_calibration_matrix_K(camera=None, mode='simple'):
    """Get the 3x3 intrinsic calibration matrix K from a Blender camera.

    Args:
        camera: Camera object (defaults to scene camera)
        mode: 'simple' or 'complete'

    Returns:
        3x3 numpy array K
    """
    scene = bpy.context.scene
    scale = scene.render.resolution_percentage / 100
    width = scene.render.resolution_x * scale
    height = scene.render.resolution_y * scale

    if camera is None:
        camdata = scene.camera.data
    else:
        camdata = camera.data

    if mode == 'simple':
        aspect_ratio = width / height
        K = np.zeros((3, 3), dtype=np.float32)
        K[0][0] = width / 2 / np.tan(camdata.angle / 2)
        K[1][1] = height / 2. / np.tan(camdata.angle / 2) * aspect_ratio
        K[0][2] = width / 2.
        K[1][2] = height / 2.
        K[2][2] = 1.
        K.transpose()
    elif mode == 'complete':
        focal = camdata.lens
        sensor_width = camdata.sensor_width
        sensor_height = camdata.sensor_height
        pixel_aspect_ratio = scene.render.pixel_aspect_x / scene.render.pixel_aspect_y

        if camdata.sensor_fit == 'VERTICAL':
            s_u = width / sensor_width / pixel_aspect_ratio
            s_v = height / sensor_height
        else:
            s_u = width / sensor_width
            s_v = height * pixel_aspect_ratio / sensor_height

        alpha_u = focal * s_u
        alpha_v = focal * s_v
        u_0 = width / 2
        v_0 = height / 2

        K = np.array([
            [alpha_u, 0, u_0],
            [0, alpha_v, v_0],
            [0, 0, 1]
        ], dtype=np.float32)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return K


def set_intrinsic(K, camera, image_width, image_height,
                  clip_start=None, clip_end=None):
    """Set camera intrinsics from a 3x3 K matrix.

    Args:
        K: 3x3 intrinsic matrix [[fx, 0, cx], [0, fy, cy], [0, 0, 1]]
        camera: Camera object
        image_width: Image width in pixels
        image_height: Image height in pixels
        clip_start: Near clipping distance
        clip_end: Far clipping distance
    """
    K = Matrix(K)
    cam = camera.data

    if abs(K[0][1]) > 1e-7:
        raise ValueError(f"Skew is not supported by Blender: {K[0][1]}")

    fx, fy = K[0][0], K[1][1]
    cx, cy = K[0][2], K[1][2]

    pixel_aspect_x = pixel_aspect_y = 1
    if fx > fy:
        pixel_aspect_y = fx / fy
    elif fx < fy:
        pixel_aspect_x = fy / fx

    pixel_aspect_ratio = pixel_aspect_y / pixel_aspect_x

    # Compute view_fac_in_px
    if cam.sensor_fit == 'AUTO':
        if pixel_aspect_x * image_width >= pixel_aspect_y * image_height:
            view_fac_in_px = image_width
        else:
            view_fac_in_px = pixel_aspect_ratio * image_height
    elif cam.sensor_fit == 'HORIZONTAL':
        view_fac_in_px = image_width
    else:
        view_fac_in_px = pixel_aspect_ratio * image_height

    sensor_size_in_mm = (cam.sensor_height if cam.sensor_fit == 'VERTICAL'
                         else cam.sensor_width)
    f_in_mm = fx * sensor_size_in_mm / view_fac_in_px

    shift_x = (cx - (image_width - 1) / 2) / -view_fac_in_px
    shift_y = (cy - (image_height - 1) / 2) / view_fac_in_px * pixel_aspect_ratio

    cam.lens = f_in_mm
    cam.shift_x = shift_x
    cam.shift_y = shift_y
    bpy.context.scene.render.resolution_x = image_width
    bpy.context.scene.render.resolution_y = image_height
    bpy.context.scene.render.pixel_aspect_x = pixel_aspect_x
    bpy.context.scene.render.pixel_aspect_y = pixel_aspect_y

    if clip_start is not None:
        cam.clip_start = clip_start
    if clip_end is not None:
        cam.clip_end = clip_end


def set_extrinsic(R_world2cv, T_world2cv, camera):
    """Set camera extrinsics from rotation and translation (world-to-camera).

    Args:
        R_world2cv: 3x3 rotation matrix (world to camera)
        T_world2cv: 3x1 translation vector (world to camera)
        camera: Camera object
    """
    R_bcam2cv = Matrix(((1, 0, 0), (0, -1, 0), (0, 0, -1)))
    R_cv2world = R_world2cv.T
    rotation = Matrix(R_cv2world.tolist()) @ R_bcam2cv
    location = -R_cv2world @ T_world2cv
    camera.location = location
    camera.matrix_world = Matrix.Translation(location) @ rotation.to_4x4()
