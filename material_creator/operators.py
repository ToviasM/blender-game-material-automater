import bpy
from .core import material, utilities
from bpy_extras.io_utils import ExportHelper


class CreateMaterial(bpy.types.Operator):
    bl_idname = "material_creator.create_material"
    bl_label = "Create Material"

    material_name: bpy.props.StringProperty(
        name="Material Name",
        default='',
        maxlen=35
    )

    type_name: bpy.props.EnumProperty(
        name="Type",
        default=None,
        items=material.get_material_types,
        description="Select the material type",
    )

    def execute(self, context):
        properties = bpy.context.scene.material_creator
        if properties:
            material.create_new_material(properties, self.material_name, self.type_name)

        if properties.source_material is None:
            self.report({'ERROR'}, "Was unable to create material!")
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AssignMaterialTexture(bpy.types.Operator, ExportHelper):
    bl_idname = "material_creator.assign_texture"
    bl_label = "Assign Material Texture"

    slot_name: bpy.props.StringProperty(
        default='',
        maxlen=35
    )
    filename_ext = ".png"

    filter_glob = bpy.props.StringProperty(default='*.png', options={'HIDDEN'}, maxlen=255)

    def execute(self, context):
        properties = bpy.context.scene.material_creator
        if properties and properties.source_material:
            material.set_texture_map(properties, self.slot_name, self.filepath)
        else:
            self.report({'ERROR'}, "No material found to assign texture to!")
            return {'CANCELLED'}
        return {'FINISHED'}


class CreateTexturePreview(bpy.types.Operator):
    bl_idname = "material_creator.create_texture_preview"
    bl_label = "Assign Material Texture"

    slot_name: bpy.props.StringProperty(
        default='',
        maxlen=35
    )

    def execute(self, context):
        properties = bpy.context.scene.material_creator
        if properties and properties.source_material:
            material.create_texture_preview(properties, self.slot_name)
        else:
            self.report({'ERROR'}, "No material found to assign texture to!")
            return {'CANCELLED'}

        return {'FINISHED'}


class ChangeMaterialType(bpy.types.Operator):
    bl_idname = "material_creator.change_type"
    bl_label = "Change Material Type"

    type_name: bpy.props.EnumProperty(
        name="Material Type",
        default=None,
        items=material.get_material_types,
        description="Select the material type",
    )

    def execute(self, context):

        properties = bpy.context.scene.material_creator
        config = material.get_template()
        if properties and properties.source_material and self.type_name in config.material_config.material_types:
            material.change_material_type(properties, self.type_name)
            properties.scene_material_index = utilities.get_material_index(properties.source_material)
        else:
            self.report({'ERROR'}, "Did not find material to change type of!")
            return {'CANCELLED'}
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class CreateTextureSlot(bpy.types.Operator):
    bl_idname = "material_creator.create_texture_slot"
    bl_label = "Create Texture Slot"

    slot_name: bpy.props.StringProperty(
        default='',
        maxlen=35
    )

    def execute(self, context):
        properties = bpy.context.scene.material_creator
        if properties and properties.source_material:
            material.create_texture_slot(properties, self.slot_name)
        else:
            self.report({'ERROR'}, "No material found to create texture slot for!")
            return {'CANCELLED'}

        return {'FINISHED'}


class DeleteMaterial(bpy.types.Operator):
    bl_idname = "material_creator.delete_material"
    bl_label = "Create Texture Slot"

    def execute(self, context):
        properties = bpy.context.scene.material_creator
        if properties and properties.source_material:
            bpy.data.materials.remove(properties.source_material)
            properties.scene_material_index = properties.scene_material_index - 1
        else:
            self.report({'ERROR'}, "No material found to create delete!")
            return {'CANCELLED'}

        return {'FINISHED'}


class RenameMaterial(bpy.types.Operator):
    bl_idname = "material_creator.rename_material"
    bl_label = "Create Texture Slot"

    material_name: bpy.props.StringProperty(
        name="Material Name (Without Type)",
        default='',
        description="The new name for the material",
    )

    def execute(self, context):
        properties = bpy.context.scene.material_creator
        if properties and properties.source_material:
            material_type = material.get_template().material_config.material_types[material.get_material_type(properties)]
            material.rename_material(properties, self.material_name + material_type.suffix)
        else:
            self.report({'ERROR'}, "No material found to rename!")
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class AssignToSelection(bpy.types.Operator):
    bl_idname = "material_creator.assign_to_selection"
    bl_label = "Assign Material to Selection"

    def execute(self, context):
        properties = bpy.context.scene.material_creator
        if properties and properties.source_material:
            material.assign_to_selection(properties)
        else:
            self.report({'ERROR'}, "No material found to assign to selection!")
            return {'CANCELLED'}

        return {'FINISHED'}

class DeleteUnusedMaterials(bpy.types.Operator):
    bl_idname = "material_creator.delete_unused_materials"
    bl_label = "Delete Unused Materials"

    def execute(self, context):
        material.delete_unused_materials()
        return {'FINISHED'}



operator_classes = [
    CreateMaterial,
    AssignMaterialTexture,
    ChangeMaterialType,
    CreateTextureSlot,
    CreateTexturePreview,
    DeleteMaterial,
    RenameMaterial,
    AssignToSelection,
    DeleteUnusedMaterials
]


def register():
    """
    Registers the operators.
    """
    for operator_class in operator_classes:
        if not utilities.get_operator_class_by_bl_idname(operator_class.bl_idname):
            bpy.utils.register_class(operator_class)


def unregister():
    """
    Unregisters the operators.
    """
    # unregister the classes
    for operator_class in operator_classes:
        if utilities.get_operator_class_by_bl_idname(operator_class.bl_idname):
            bpy.utils.unregister_class(operator_class)