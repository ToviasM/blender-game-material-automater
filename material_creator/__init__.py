
import bpy
import os
import importlib

from .core import material, template

bl_info = {
    "name": "Material Creator",
    "author": "Tovias Milliken",
    "version": (2, 4, 3),
    "blender": (4, 0, 0),
    "location": "Header > Pipeline > Material Creator",
    "description": "A tool to improve the material creation workflow for games",
    "warning": "",
    "wiki_url": "",
    "category": "Pipeline",
}

modules = [material, template]


def register():
    """
    Registers the addon classes when the addon is enabled.
    """
    for module in modules:
        importlib.reload(module)


def unregister():
    pass