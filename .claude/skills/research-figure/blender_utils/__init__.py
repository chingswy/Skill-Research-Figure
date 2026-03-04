"""
blender_utils — Reusable Blender utility library for research figure rendering.

Extracted from thirdparty/BlenderFig/myblender/ and extended with studio lighting,
gradient materials, and teaser-specific helpers.

Dependencies: bpy, numpy, mathutils (all bundled with Blender Python).
"""

__version__ = "0.1.0"

from . import scene
from . import camera
from . import lighting
from . import material
from . import geometry
from . import fbx
from . import skeleton
from . import colors
