
import bpy
import os
import importlib

from .core import material, template, utilities, validation
from .ui import addon_preferences
from . import constants, operators, properties

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

modules = [material, template, utilities, validation, constants, operators, properties, addon_preferences]


def register():
    """
    Registers the addon classes when the addon is enabled.
    """
    for module in modules:
        importlib.reload(module)
    properties.register()
    operators.register()
    addon_preferences.register()


def unregister():
    operators.unregister()
    addon_preferences.unregister()
    properties.unregister()
