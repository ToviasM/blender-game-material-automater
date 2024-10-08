
import bpy
import os
import importlib

from .core import material, template, utilities
from .ui import addon_preferences, material_panel
from .unittests import operator_tests
from . import constants, operators, properties

bl_info = {
    "name": "Material Creator",
    "author": "Tovias Milliken",
    "version": (2, 4, 3),
    "blender": (4, 0, 0),
    "location": "3D View > N Panel > Material Creator",
    "description": "A tool to improve the material creation workflow for games with a focused material pipeline.",
    "warning": "",
    "wiki_url": "",
    "category": "Pipeline",
}

modules = [constants, material, template, utilities, operators, properties, addon_preferences, material_panel, operator_tests]


def register():
    """
    Registers the addon classes when the addon is enabled.
    """
    for module in modules:
        importlib.reload(module)
    properties.register()
    operators.register()
    addon_preferences.register()
    material_panel.register()


def unregister():
    operators.unregister()
    addon_preferences.unregister()
    properties.unregister()
    material_panel.unregister()
