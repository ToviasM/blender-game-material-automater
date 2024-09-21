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

operator_classes = [
    CreateMaterial,
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