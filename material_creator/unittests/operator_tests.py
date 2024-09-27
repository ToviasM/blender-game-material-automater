import unittest
import bpy
import os
from ..constants import MaterialConstants
from ..core import material

PATH = __file__

class TestOperators(unittest.TestCase):

    TEST_MATERIAL_NAME = 'TestMaterial'
    SLOT_NAME = 'B'

    def setUp(self):
        self.operators = bpy.ops.material_creator

        properties = bpy.context.scene.material_creator
        if self.TEST_MATERIAL_NAME in bpy.data.materials:
            bpy.data.materials.remove(bpy.data.materials.get(self.TEST_MATERIAL_NAME))
        if properties.source_material:
            bpy.data.materials.remove(properties.source_material)
            properties.source_material = None

        if 'TestScene' in bpy.data.scenes:
            bpy.data.scenes.remove(bpy.data.scenes.get('TestScene'))

        new_scene = bpy.data.scenes.new("TestScene")
        bpy.context.window.scene = new_scene

    def test_material_creation(self):
        """ Test the creation of a material """

        self.operators.create_material(material_name=self.TEST_MATERIAL_NAME, type_name=MaterialConstants.DEFAULT_TYPE)

        properties = bpy.context.scene.material_creator
        if self.TEST_MATERIAL_NAME not in bpy.data.materials:
            self.fail('Material not created!')

        if properties.source_material.name != self.TEST_MATERIAL_NAME:
            self.fail('Material not assigned to properties!')

        material_type = material.get_material_type(properties)
        if material_type != MaterialConstants.DEFAULT_TYPE:
            self.fail('Material type not set correctly!')

    def test_material_deletion(self):
        """ Test the deletion of a material """
        self.operators.create_material(material_name=self.TEST_MATERIAL_NAME, type_name=MaterialConstants.DEFAULT_TYPE)
        self.operators.delete_material()

        if self.TEST_MATERIAL_NAME in bpy.data.materials:
            self.fail('Material not deleted!')

        properties = bpy.context.scene.material_creator
        if properties.source_material:
            if properties.source_material.name == self.TEST_MATERIAL_NAME:
                self.fail("Material not removed from properties")

    def test_material_rename(self):
        """ Test the renaming of a material """
        self.operators.create_material(material_name=self.TEST_MATERIAL_NAME, type_name=MaterialConstants.DEFAULT_TYPE)
        new_name = 'NewName'
        self.operators.rename_material(material_name=new_name)

        if new_name not in bpy.data.materials:
            self.fail('Material not renamed!')

        properties = bpy.context.scene.material_creator
        if properties.source_material.name != new_name:
            self.fail('Material not renamed in properties!')

    def test_material_type_change(self):
        """ Test the changing of a material type """
        self.operators.create_material(material_name=self.TEST_MATERIAL_NAME, type_name=MaterialConstants.DEFAULT_TYPE)
        new_type = 'metal'
        self.operators.change_type(type_name=new_type)

        properties = bpy.context.scene.material_creator
        if material.get_material_type(properties) != new_type:
            self.fail('Material type not changed!')

    def test_create_texture_slot(self):
        """ Test the assignment of a texture to a material """
        self.operators.create_material(material_name=self.TEST_MATERIAL_NAME, type_name=MaterialConstants.DEFAULT_TYPE)
        self.operators.create_texture_slot(slot_name=self.SLOT_NAME)
        
        properties = bpy.context.scene.material_creator
        texture_nodes = material.get_texture_nodes(properties, slot_name=self.SLOT_NAME)
        if len(texture_nodes) < 1:
            self.fail('Texture nodes not created!')

    def test_texture_assignment(self):
        """ Test the assignment of a texture to a material """
        self.operators.create_material(material_name=self.TEST_MATERIAL_NAME, type_name=MaterialConstants.DEFAULT_TYPE)
        self.operators.create_texture_slot(slot_name=self.SLOT_NAME)
        self.operators.assign_texture(slot_name=self.SLOT_NAME, filepath= os.path.join(os.path.dirname(PATH), 'grid.png'))

        properties = bpy.context.scene.material_creator
        texture_nodes = material.get_texture_nodes(properties, slot_name=self.SLOT_NAME)
        if not texture_nodes[0].image:
            self.fail('Texture not assigned to material!')

    def test_assign_to_selected(self):
        """ Test the assignment of a material to a selected object """
        self.operators.create_material(material_name=self.TEST_MATERIAL_NAME, type_name=MaterialConstants.DEFAULT_TYPE)
        if bpy.context.scene.objects.get("Circle"):
            bpy.data.objects.remove(bpy.data.objects.get("Circle"))
        cube = bpy.ops.mesh.primitive_circle_add()
        obj = bpy.context.scene.objects.get("Circle")
        self.operators.assign_to_selection()

        if bpy.context.object.active_material.name != self.TEST_MATERIAL_NAME:
            self.fail('Material not assigned to object!')   

    def test_delete_unused_materials(self):
        """ Test the deletion of unused materials """
        self.operators.create_material(material_name=self.TEST_MATERIAL_NAME, type_name=MaterialConstants.DEFAULT_TYPE)
        self.operators.create_material(material_name="TEST1", type_name=MaterialConstants.DEFAULT_TYPE)
        self.operators.delete_unused_materials()

        if self.TEST_MATERIAL_NAME in bpy.data.materials:
            self.fail('Material not deleted!')

def test_operators():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOperators)
    unittest.TextTestRunner(verbosity=2).run(suite) 