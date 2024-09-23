import bpy
from .core import material, utilities

class CreateMaterial(bpy.types.Operator):
    bl_idname = "material_creator.create_material"
    bl_label = "Create Material"

    material_name : bpy.props.StringProperty(
        default='',
        maxlen=35
    )

    type_name : bpy.props.StringProperty(
        default='',
        maxlen=35
    )

    def execute(self, context):
        properties = bpy.context.scene.material_creator
        if properties:
            material.create_new_material(properties, self.material_name, self.type_name)
        
        if properties.source_material is None:
            self.report({'ERROR'}, "Was unable to create material!")
            return {'CANCELLED'}
        return {'FINISHED'}


class AssignMaterialTexture(bpy.types.Operator):
    bl_idname = "material_creator.assign_texture"
    bl_label = "Assign Material Texture"

    slot_name : bpy.props.StringProperty(
        default='',
        maxlen=35
    )

    texture_path : bpy.props.StringProperty(
        default='',
        maxlen=35
    )


    def execute(self, context):
        properties = bpy.context.scene.material_creator
        if properties and properties.source_material:
            material.set_texture_map(properties, self.slot_name, self.texture_path)
        else:
            self.report({'ERROR'}, "No material found to assign texture to!")
            return {'CANCELLED'}

        return {'FINISHED'}


class ChangeMaterialType(bpy.types.Operator):
    bl_idname = "material_creator.change_type"
    bl_label = "Change Material Type"

    type_name : bpy.props.StringProperty(
        default='',
        maxlen=35
    )

    def execute(self, context):

        properties = bpy.context.scene.material_creator
        config = material.get_template()
        if properties and properties.source_material and self.type_name in config.material_config.material_types:
            material.change_material_type(properties, self.type_name)
        else:
            self.report({'ERROR'}, "Did not find material to change type of!")
            return {'CANCELLED'}
        return {'FINISHED'}


class CreateTextureSlot(bpy.types.Operator):
    bl_idname = "material_creator.create_texture_slot"
    bl_label = "Create Texture Slot"

    slot_name : bpy.props.StringProperty(
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



operator_classes = [
    CreateMaterial,
    AssignMaterialTexture,
    ChangeMaterialType,
    CreateTextureSlot,
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