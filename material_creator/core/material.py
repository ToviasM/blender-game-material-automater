import os
from .template import Template, TextureSlot
import bpy
import logging
from typing import List, Optional, Any, Dict
from .utilities import apply_shader_properties, find_node
from ..constants import ToolInfo

LOGGER = logging.getLogger(__name__)

DEFAULT_TYPE = "default"

#TODO - Introduce larger management system of settings
def get_template():
    addon = bpy.context.preferences.addons.get(ToolInfo.NAME.value)
    template_path = addon.preferences.template_path
    if template_path.startswith(".."):
        template_path = os.path.join(os.path.dirname(__file__), template_path)
    
    return Template.from_json(template_path)

def get_shader_node(properties) -> Optional[bpy.types.Node]:
    """
    Retrieves the shader node connected to the 'Surface' input of the material output node.
    
    Returns:
        Optional[bpy.types.Node]: The shader node if connected, None otherwise.
    """
    material_output = properties.node_tree.nodes[0]
    input_socket = material_output.inputs['Surface']
    
    if input_socket.is_linked:
        return input_socket.links[0].from_node
    else:
        LOGGER.error("Could not find Shader Node")
        return None

def create_texture_node(properties, slot: Any) -> None:
    """ 
    Creates a texture node for the specified slot and connects it to the shader node.
    
    Args:
        slot (Any): The texture slot for which a texture node will be created.
    """
    for connection in slot.connections:
        input_node = get_shader_node(properties)
        if not input_node:
            LOGGER.error("Failed to create texture node: Shader node not found.")
            return

        # Iterate over the connections in reverse order
        for attributes in connection[::-1]:
            connected_node = None
            output_attr = attributes[0]
            input_attr = attributes[1]

            # Replace shader placeholder in input attribute
            input_attr = input_attr.replace("{SHADER}", input_node.bl_idname)

            # Get the shader input socket
            shader_input_socket = input_node.inputs[input_attr.split(".")[1]]
            
            # Check if the input is already linked to a node
            if shader_input_socket.is_linked:
                connected_node = find_node(shader_input_socket.links[0].from_node, output_attr.split(".")[0])

            # Create a new node if no connected node was found
            if not connected_node:
                connected_node = properties.node_tree.nodes.new(type=output_attr.split(".")[0])

            # Create a link between the output and input
            properties.node_tree.links.new(
                connected_node.outputs[output_attr.split(".")[1]], 
                input_node.inputs[input_attr.split(".")[1]]
            )

            # Apply shader properties for the input node if defined
            input_properties = slot.properties.get(input_attr.split(".")[0])
            if input_properties:
                apply_shader_properties(input_node, input_properties)

            # Apply shader properties for the connected node if defined
            output_properties = slot.properties.get(output_attr.split(".")[0])
            if output_properties:
                apply_shader_properties(connected_node, output_properties)
            
            # Update input node to connected node for the next iteration
            input_node = connected_node


def get_texture_slots(properties, optional: bool = False) -> List[Optional['TextureSlot']]:
    """
    Retrieves the required and optional texture slots for the current material type.
    
    Args:
        optional (bool): If True, includes optional texture slots along with required ones.
    
    Returns:
        List[Optional[TextureSlot]]: A list of texture slots, including optional ones if specified.
    """
    material_type = get_template().material_config.material_types[get_material_type(properties)]
    required_slots = material_type.required_texture_slots
    optional_slots = material_type.optional_texture_slots if optional else []

    # Combine required and optional slots if optional flag is True
    if optional_slots:
        required_slots.extend(optional_slots)
        
    return required_slots

def create_new_material(properties, material_name: str, type_name: str) -> None:
    """
    Creates A New Material 
    """

    material_type = get_template().material_config.material_types[type_name]
    material = bpy.data.materials.new(name=material_name + material_type.suffix)
    properties.source_material = material

def create_material_nodes(properties) -> None:
    """
    Iterates over all texture slots and creates texture nodes for each slot.
    """
    for slot in get_texture_slots(properties):
        create_texture_node(properties, slot)

def rename_material(properties, new_name: str) -> None:
    """
    Renames the current material to the new name.
    
    Args:
        new_name (str): The new name to assign to the material.
    """
    material = properties.source_material
    if material:
        material.name = new_name
    else:
        LOGGER.error(f"Material '{properties.source_material.name}' not found, unable to rename.")

def change_material_type(self, context):
    properties = self

    type_name = properties.material_type
    new_type = get_template().material_config.material_types[type_name]
    if not new_type:
        new_type = DEFAULT_TYPE

    rename_material(properties, properties.source_material.name.replace(properties.material_type, new_type.suffix))

    create_material_nodes(properties)

def change_material(self, context) -> str:
    """
    Determines the material type based on the material name suffix.
    
    Returns:
        str: The material type name. If no match is found, returns the default type.
    """

    found_type = False
    properties = self
    
    for name, mat_type in get_template().material_config.material_types.items():
        if properties.source_material.name.endswith(mat_type.suffix):
            properties.material_type = mat_type
            
    if found_type == False:
        properties.material_type = DEFAULT_TYPE
    
    properties.node_tree = properties.source_material.node_tree
    create_material_nodes(properties)
    

def create_texture_slot(properties, slot_type: str) -> None:
    """
    Creates a texture slot of the specified type by creating a texture node in the corresponding slot.
    
    Args:
        slot_type (str): The type of texture slot to create.
    """
    for slot in get_texture_slots(properties, optional=True):
        if slot.name == slot_type:
            create_texture_node(properties, slot)

def get_texture_node(properties, slot_name: str) -> Optional[bpy.types.Node]:
    """
    Retrieves the texture node for the given slot name.
    
    Args:
        slot_name (str): The name of the texture slot to retrieve the texture node from.
    
    Returns:
        Optional[bpy.types.Node]: The texture node if found, None otherwise.
    """
    texture_node = None
    
    for slot in get_texture_slots(properties, optional=True):
        if slot.slot_name == slot_name:
            for connection in slot.connections:
                for attributes in connection:
                    # Extract the input attribute from the connection
                    input_attribute = attributes[1].split(".")[1]
                    
                    if "{SHADER}" not in attributes[1]:
                        continue
                    
                    start_node = get_shader_node().inputs[input_attribute]

                    # Check if the input is linked to a texture node
                    if start_node.is_linked:
                        node = find_node(start_node.links[0].from_node, "ShaderNodeTexImage")
                        
                        if texture_node and texture_node != node:
                            LOGGER.error(
                                f"Multiple textures connected to slot '{slot_name}'! Only one is allowed."
                            )
                        texture_node = node
                    else:
                        LOGGER.warning(
                            f"Texture is not connected for slot '{slot_name}' at '{input_attribute}'."
                        )

    return texture_node

def set_texture_map(properties, slot_name: str, path: str) -> None:
    """
    Sets the texture map for the given slot name by loading an image from the specified path.
    
    Args:
        slot_name (str): The name of the texture slot to apply the texture map to.
        path (str): The file path of the image to load.
    """
    texture_node = get_texture_node(properties, slot_name)
    if texture_node is None:
        LOGGER.info(f"No texture node found for slot '{slot_name}', creating a new one.")
        create_texture_slot(properties, slot_name)
        texture_node = get_texture_node(properties, slot_name)
    
    # Load the image from the specified path
    image = bpy.data.images.load(path)
    
    # Apply the image to the texture node
    apply_shader_properties(texture_node, {"image": image})

    # Apply additional shader properties if available
    for slot in get_texture_slots(properties, optional=True):
        if slot.slot_name == slot_name:
            props = slot.properties.get(texture_node.bl_idname)
            if props:
                apply_shader_properties(texture_node, props)