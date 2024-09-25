import os
from .template import Template, TextureSlot
import bpy
import logging
from typing import List, Optional, Any, Dict
from .utilities import apply_shader_properties, find_node, load_image, get_material_index, find_all_nodes
from ..constants import ToolInfo, MaterialConstants

LOGGER = logging.getLogger(__name__)


def get_template():
    addon = bpy.context.preferences.addons.get(ToolInfo.NAME.value)
    template_path = addon.preferences.template_path
    if template_path.startswith(".."):
        template_path = os.path.join(os.path.dirname(__file__), template_path)
    
    return Template.from_json(template_path)

def get_material_type(properties) -> str:
    """
    Determines the material type based on the material name suffix.
    
    Returns:
        str: The material type name. If no match is found, returns the default type.
    """
    
    for name, mat_type in get_template().material_config.material_types.items():
        if name == MaterialConstants.DEFAULT_TYPE:
            continue
        if properties.source_material.name.endswith(mat_type.suffix):
            return name
    return MaterialConstants.DEFAULT_TYPE

def get_material_types(cls, context) -> List[str]:

    types = []
    for name, mat_type in get_template().material_config.material_types.items():
        types.append(name)
    return [(item, item, "Material Type - " + item) for item in types]   

def get_new_material_name(properties, source_type, new_type) -> str:
    """
    Retrieves the material type suffix for the current material.
    
    Returns:
        str: The material type suffix.
    """
    if source_type == MaterialConstants.DEFAULT_TYPE:
        return properties.source_material.name + get_template().material_config.material_types[new_type].suffix

    return properties.source_material.name.replace(get_template().material_config.material_types[source_type].suffix, get_template().material_config.material_types[new_type].suffix)

def get_shader_node(properties) -> Optional[bpy.types.Node]:
    """
    Retrieves the shader node connected to the 'Surface' input of the material output node.
    
    Returns:
        Optional[bpy.types.Node]: The shader node if connected, None otherwise.
    """
    if properties.node_tree:
        material_output = properties.node_tree.nodes["Material Output"]
        input_socket = material_output.inputs['Surface']
        
        if input_socket.is_linked:
            return input_socket.links[0].from_node
        else:
            LOGGER.error("Could not find Shader Node")
            return None
    else:
        return None

#TODO - Introduce larger system for management of nodes
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

def change_material_type(properties, new_type):
    """Change the material type of the current material.
    Args:
        properties (MaterialProperties): The material properties.
        new_type (str): The new material type to change to.
    """
    properties.material_type = new_type
    rename_material(properties, get_new_material_name(properties, get_material_type(properties), new_type))

    create_material_nodes(properties)

def change_material(properties, material) -> str:
    """
    Determines the material type based on the material name suffix.
    
    Returns:
        str: The material type name. If no match is found, returns the default type.
    """

    properties.source_material = material

    material_type = None
    for name, mat_type in get_template().material_config.material_types.items():
        if properties.source_material.name.endswith(mat_type.suffix):
            material_type = name
            
    properties.material_type = material_type or MaterialConstants.DEFAULT_TYPE
    properties.node_tree = properties.source_material.node_tree
    

def create_new_material(properties, material_name: str, type_name: str) -> None:
    """
    Creates A New Material 
    """

    material_type = get_template().material_config.material_types[type_name]
    material = bpy.data.materials.new(name=material_name + material_type.suffix)
    material.use_nodes = True
    
    properties.scene_material_index = get_material_index(material)
    properties.node_tree = properties.source_material.node_tree


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
    

def create_texture_slot(properties, slot_type: str) -> None:
    """
    Creates a texture slot of the specified type by creating a texture node in the corresponding slot.
    
    Args:
        slot_type (str): The type of texture slot to create.
    """
    for slot in get_texture_slots(properties, optional=True):
        if slot.slot_name == slot_type:
            create_texture_node(properties, slot)

def get_texture_nodes(properties, slot_name: str) -> Optional[bpy.types.Node]:
    """
    Retrieves the texture node for the given slot name.
    
    Args:
        slot_name (str): The name of the texture slot to retrieve the texture node from.
    
    Returns:
        Optional[bpy.types.Node]: The texture node if found, None otherwise.
    """
    texture_nodes = []
    
    for slot in get_texture_slots(properties, optional=True):
        if slot.slot_name == slot_name:
            for connection in slot.connections:
                for attributes in connection:
                    # Extract the input attribute from the connection
                    input_attribute = attributes[1].split(".")[1]
                    
                    if "{SHADER}" not in attributes[1]:
                        continue
                    
                    shader_node = get_shader_node(properties)
                    if not shader_node:
                        LOGGER.error("Failed to create texture node: Shader node not found.")
                        return ValueError("Shader node does not exist")
                    
                    start_node = shader_node.inputs[input_attribute]

                    # Check if the input is linked to a texture node
                    if start_node.is_linked:
                        nodes = find_all_nodes(start_node.links[0].from_node, "ShaderNodeTexImage")
                        texture_nodes.extend(nodes)
    return texture_nodes

def set_texture_map(properties, slot_name: str, path: str) -> None:
    """
    Sets the texture map for the given slot name by loading an image from the specified path.
    
    Args:
        slot_name (str): The name of the texture slot to apply the texture map to.
        path (str): The file path of the image to load.
    """
    texture_nodes = get_texture_nodes(properties, slot_name)
    if len(texture_nodes) == 0:
        LOGGER.info(f"No texture node found for slot '{slot_name}', creating a new one.")
        create_texture_slot(properties, slot_name)
        texture_nodes = get_texture_nodes(properties, slot_name)
        
    for texture_node in texture_nodes:

        # Load the image from the specified path
        image = load_image(path)

        # Apply the image to the texture node
        apply_shader_properties(texture_node, {"image": image})

        # Apply additional shader properties if available
        for slot in get_texture_slots(properties, optional=True):
            if slot.slot_name == slot_name:
                props = slot.properties.get(texture_node.bl_idname)
                if props:
                    apply_shader_properties(texture_node, props)
        
        create_texture_preview(properties, slot_name, texture_node)

def create_texture_preview(properties, slot_name: str, texture_node=None) -> None:
    """
    Sets the texture map for the given slot name by loading an image from the specified path.
    
    Args:
        slot_name (str): The name of the texture slot to apply the texture map to
    """
    if not texture_node:
        texture_nodes = get_texture_nodes(properties, slot_name)
        if texture_node is None:
            LOGGER.info(f"No texture node found for slot '{slot_name}', creating a new one.")
            create_texture_slot(properties, slot_name)
            texture_nodes = get_texture_nodes(properties, slot_name)
            if len(texture_nodes) > 0:
                texture_node = texture_nodes[0]
    
    # Load the image from the specified path
    texture = bpy.data.textures.get(slot_name)
    if not texture:
        texture = bpy.data.textures.new(slot_name, type="IMAGE")
    texture.image = texture_node.image
    texture.image.update()
    texture.image.reload()