import bpy

from ..core import material
from ..constants import ToolInfo


class MATERIAL_UL_items(bpy.types.UIList):
    bl_idname = "MATERIAL_UL_items"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        material = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=material.name, icon='MATERIAL')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='MATERIAL')


class MATERIAL_PT_panel(bpy.types.Panel):
    bl_label = "Material Panel"
    bl_idname = "MATERIAL_PT_panel"
    bl_space_type = ToolInfo.AREA.value
    bl_region_type = ToolInfo.REGION.value
    bl_category = ToolInfo.CATEGORY.value

    def __init__(self, **kwargs):
        super(MATERIAL_PT_panel).__init__(**kwargs)
        self.texture_slots = {}

    def draw(self, context):
        layout = self.layout
        properties = bpy.context.scene.material_creator
        row = layout.row()
        row.template_list("MATERIAL_UL_items", "", bpy.data, "materials", properties, "scene_material_index")

        if properties.source_material:
            # Draw the material properties
            box = layout.box()
            box.label(text="Material Properties - " + properties.material_type, icon='MATERIAL')
            self.draw_material_properties(box, properties)

            # Draw the texture slots
            self.draw_texture_slots(layout, properties)

        # Draw the operations
        layout.separator()
        layout.label(text="Operations", icon='MODIFIER')
        self.draw_operations()

    def draw_material_properties(self, box, properties):
        """ Draw the properties of the selected material """
        rename_operator = box.operator("material_creator.rename_material", text="Rename Material")
        box.operator("material_creator.change_type", text="Change Type")
        box.operator("material_creator.delete_material", text="Delete", icon='ERROR')

        material_type = material.get_template().material_config.material_types[material.get_material_type(properties)]
        rename_operator.material_name = properties.source_material.name.replace(material_type.suffix, '')

    def draw_texture_slots(self, layout, properties):
        """ Draw the texture slots for the selected material """
        for texture_slot in material.get_texture_slots(properties, optional=True):
            texture_nodes = material.get_texture_nodes(properties, texture_slot.slot_name)
            if isinstance(texture_nodes, ValueError):
                continue

            texture_node = None
            if len(texture_nodes) > 0:
                texture_node = texture_nodes[0]

            layout.separator()
            layout.label(text="Texture Slots", icon='TEXTURE')

            texture_slot_box = layout.box()
            if not texture_node:
                label_row = texture_slot_box.row()
                label_row.label(text="Slot : " + texture_slot.slot_name + " " + texture_slot.description)
                row = texture_slot_box.row()
                op = row.operator("material_creator.assign_texture", text="Browse Image")
                op.slot_name = texture_slot.slot_name
            else:
                row = texture_slot_box.row()
                row.label(text="Slot : " + texture_slot.slot_name + " " + texture_slot.description)
                if texture_node.image:

                    texture = bpy.data.textures.get(texture_slot.slot_name)
                    if not texture:
                        self.create_texture_preview_deferred(texture_slot.slot_name)
                    elif texture_node.image != texture.image:
                        self.create_texture_preview_deferred(texture_slot.slot_name)

                    texture_slot_box.template_ID_preview(texture, "image", hide_buttons=True)
                op = texture_slot_box.operator("material_creator.assign_texture", text="Browse Image")
                op.slot_name = texture_slot.slot_name

    def draw_operations(self):
        """ Draw the operations for the selected material """
        layout = self.layout
        box_buttons = layout.box()
        box_buttons.operator("material_creator.create_material", text="Create Material")
        box_buttons.operator("material_creator.assign_to_selection", text="Assign To Selection")
        box_buttons.operator("material_creator.delete_unused_materials", text="Delete Unused Materials")

    def create_texture_preview_deferred(self, slot_name):
        """ Create a texture preview for the given slot name """
        def _create_texture_preview():
            bpy.ops.material_creator.create_texture_preview(slot_name=slot_name)
            return None  # Returning None stops the timer

        bpy.app.timers.register(_create_texture_preview)


def register():
    bpy.utils.register_class(MATERIAL_UL_items)
    bpy.utils.register_class(MATERIAL_PT_panel)


def unregister():
    bpy.utils.unregister_class(MATERIAL_UL_items)
    bpy.utils.unregister_class(MATERIAL_PT_panel)
