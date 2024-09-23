import bpy

class MATERIAL_PT_Panel(bpy.types.Panel):
    bl_label = "Material Creator"
    bl_idname = "MATERIAL_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Material Creator'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Material List
        row = layout.row()
        row.template_list("MATERIAL_UL_items", "", scene, "materials", scene, "material_index")

        # Display texture slots for the selected material
        if scene.material_index >= 0 and scene.material_index < len(scene.materials):
            material = scene.materials[scene.material_index]
            box = layout.box()
            box.label(text="Texture Slots")
            for i, texture_slot in enumerate(material.texture_slots):
                if texture_slot:
                    box.prop(texture_slot, "name", text=f"Slot {i}")

        # Create and Delete buttons
        row = layout.row()
        row.operator("material.create", text="Create Material")
        row.operator("material.delete", text="Delete Material")

class MATERIAL_UL_items(bpy.types.UIList):
    bl_idname = "MATERIAL_UL_items"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        material = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=material.name, icon='MATERIAL')
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon='MATERIAL')

def register():
    bpy.utils.register_class(MATERIAL_PT_Panel)
    bpy.utils.register_class(MATERIAL_UL_items)

def unregister():
    bpy.utils.unregister_class(MATERIAL_PT_Panel)
    bpy.utils.unregister_class(MATERIAL_UL_items)

if __name__ == "__main__":
    register()