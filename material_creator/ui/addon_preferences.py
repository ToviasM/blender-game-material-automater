# Copyright Epic Games, Inc. All Rights Reserved.

import bpy
from ..properties import MaterialCreatorAddonProperties
from ..constants import ToolInfo


class MaterialCreatorPreferences(MaterialCreatorAddonProperties, bpy.types.AddonPreferences):
    """
    This class creates the settings interface in the send to unreal addon.
    """
    bl_idname = ToolInfo.NAME.value

    def draw(self, context):
        """
        This defines the draw method, which is in all Blender UI types that create interfaces.

        :param context: The context of this interface.
        """
        row = self.layout.row()
        row.prop(self, 'template_path')

def register():
    """
    Registers the addon preferences when the addon is enabled.
    """
    bpy.utils.register_class(MaterialCreatorPreferences)


def unregister():
    """
    Unregisters the addon preferences when the addon is disabled.
    """
    bpy.utils.unregister_class(MaterialCreatorPreferences)