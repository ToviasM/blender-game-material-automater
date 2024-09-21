import bpy

from .core import material
from . import constants


class MaterialCreatorAddonProperties:
    template_path: bpy.props.StringProperty(
        default='../templates/default.json'
    )


class MaterialProperties(bpy.types.PropertyGroup):
    source_material: bpy.props.PointerProperty(
        type=bpy.types.Material,
        update=material.change_material,
    )

    node_tree: bpy.props.PointerProperty(
        type=bpy.types.NodeTree
    )

    material_type: bpy.props.StringProperty(
        default='',
        maxlen=35,
        update=material.change_material_type,
    )


def register():
    """
    Registers the property group class and adds it to the window manager context when the
    addon is enabled.
    """
    properties = getattr(bpy.types.Scene, constants.ToolInfo.NAME.value, None)
    if not properties:
        bpy.utils.register_class(MaterialProperties)
        bpy.types.Scene.material_creator = bpy.props.PointerProperty(type=MaterialProperties)


def unregister():
    """
    Unregisters the property group class and deletes it from the window manager context when the
    addon is disabled.
    """
    properties = getattr(bpy.types.Scene, constants.ToolInfo.NAME.value, None)
    if properties:
        bpy.utils.unregister_class(MaterialProperties)
        del bpy.types.Scene.material_creator