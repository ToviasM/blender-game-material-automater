import os
from .template import Template, TextureSlot
import bpy
import logging
from typing import List, Optional, Any
from .utilities import apply_shader_properties, find_node, load_image, get_material_index, find_all_nodes, join_relative_path, delete_node_recursive
from ..constants import ToolInfo, MaterialConstants

LOGGER = logging.getLogger(__name__)


def get_template():
    """ Get the template from the addon preferences """
    addon = bpy.context.preferences.addons.get(ToolInfo.NAME.value)
    template_name = addon.preferences.template_path

    template_dir = os.path.dirname(join_relative_path(MaterialConstants.DEFAULT_TEMPLATE_PATH))
    template_path = os.path.join(template_dir, template_name)
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

    return properties.source_material.name.replace(
        get_template().material_config.material_types[source_type].suffix,
        get_template().material_config.material_types[new_type].suffix
    )


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


def create_texture_node(properties, slot: Any) -> None:
    """
    Creates a texture node for the specified slot and connects it to the shader node.

    Args:
        slot (Any): The texture slot for which a texture node will be created.
    """
    new_inputs = []

    for connection in slot.connections:
        input_node = get_shader_node(properties)
        if not input_node:
            LOGGER.error("Failed to create texture node: Shader node not found.")
            return

        new_inputs.append(connection[-1][1].split(".")[1])

        # Iterate over the connections in reverse order
        for attributes in connection[::-1]:
            connected_node = None
            output_attr = attributes[0]
            input_attr = attributes[1]

            # Replace shader placeholder in input attribute
            input_attr = input_attr.replace("{SHADER}", input_node.bl_idname)

            # Get the shader input socket
            shader_input_socket = input_node.inputs.get(input_attr.split(".")[1])
            if shader_input_socket:
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
 
    return new_inputs


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
    new_inputs = []
    for slot in get_texture_slots(properties):
        new_inputs.extend(create_texture_node(properties, slot))
    
    input_node = get_shader_node(properties)
    
    # Remove the old links
    deletable_inputs = [socket for socket in input_node.inputs if socket.is_linked and socket.name not in new_inputs]
    for socket in deletable_inputs:
        delete_node_recursive(properties.node_tree, socket.links[0].from_node)


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
        image = load_image(path)
        apply_shader_properties(texture_node, {"image": image})

        for slot in get_texture_slots(properties, optional=True):
            if slot.slot_name == slot_name:
                props = slot.properties.get(texture_node.bl_idname)
                if props:
                    apply_shader_properties(texture_node, props)

        create_texture_preview(properties, slot_name, texture_node)


def create_texture_preview(properties, slot_name: str, texture_node=None) -> None:
    """
    Create a texture preview for the given slot name

    Args:
        slot_name (str): The name of the texture slot to create a preview for.
        texture_node (bpy.types.Node): The texture node to create a preview for
    """
    texture_nodes = get_texture_nodes(properties, slot_name)
    if not texture_node:
        if texture_nodes is None:
            LOGGER.info(f"No texture node found for slot '{slot_name}', creating a new one.")
            create_texture_slot(properties, slot_name)
            texture_nodes = get_texture_nodes(properties, slot_name)
    
    texture_node = texture_node or texture_nodes[0]
    texture = bpy.data.textures.get(slot_name)
    if not texture:
        texture = bpy.data.textures.new(slot_name, type="IMAGE")
    texture.image = texture_node.image
    texture.image.update()
    texture.image.reload()


def assign_to_selection(properties) -> None:
    """
    Assigns the current material to the selected objects or faces in the scene.

    Args:
        properties (MaterialProperties): The material properties.
    """

    was_in_edit_mode = bpy.context.mode == 'EDIT_MESH'
    if was_in_edit_mode:
        bpy.ops.object.mode_set(mode='OBJECT')
 
    selected_objects = bpy.context.selected_objects
    selected_faces = [f for obj in selected_objects for f in obj.data.polygons if f.select]


    for obj in selected_objects:
        selected_faces = [f for f in obj.data.polygons if f.select]
        if selected_faces:
            if obj.type == "MESH":
                if properties.source_material.name not in obj.data.materials:
                    obj.data.materials.append(properties.source_material)
                material_index = obj.data.materials.find(properties.source_material.name)
                for face in selected_faces:
                    face.material_index = material_index
        else:

            if obj.type == "MESH":
                if properties.source_material.name not in obj.data.materials:
                    obj.data.materials.append(properties.source_material)
            obj.data.materials[properties.scene_material_index] = properties.source_material

    if was_in_edit_mode:
        bpy.ops.object.mode_set(mode='EDIT')

def delete_unused_materials() -> None:
    """
    Deletes all materials that are not assigned to any objects in the scene.
    """
    materials = bpy.data.materials
    for material in materials:
        if material.users == 0:
            materials.remove(material)