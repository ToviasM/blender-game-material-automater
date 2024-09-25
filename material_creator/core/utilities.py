import bpy
from typing import Dict, Any, Optional


# TODO: Extract Indices so we can access import shader variables such as "input[0]"
def apply_shader_properties(node: bpy.types.Node, shader_property_block: Dict[str, Any]) -> None:
    """
    Applies shader properties from the given property block to the specified node.
    
    Args:
        node (bpy.types.Node): The shader node to which properties will be applied.
        shader_property_block (Dict[str, Any]): A dictionary containing shader properties and their values.
    """
    for props, value in shader_property_block.items():
        current_property = node
        
        # Traverse through the property chain, excluding the last one
        for prop in props.split(".")[:-1]:
            if not current_property:
                return None
            current_property = getattr(current_property, prop)
        
        # Set the final property value
        setattr(current_property, props.split(".")[-1], value)


def find_node(current_node: bpy.types.Node, node_type: str) -> Optional[bpy.types.Node]:
    """
    Recursively finds a node of the specified type, starting from the given node.
    
    Args:
        current_node (bpy.types.Node): The node to start searching from.
        node_type (str): The type of node to search for.
    
    Returns:
        Optional[bpy.types.Node]: The found node if it matches the type, otherwise None.
    """
    # Check if the current node is of the desired type
    if current_node.bl_idname == node_type:
        return current_node

    # Traverse through linked nodes via inputs
    for socket in current_node.inputs:
        if socket.is_linked:
            for node_link in socket.links:
                next_node = node_link.from_node
                if next_node.bl_idname == node_type:
                    return next_node
                # Recursive search if the node isn't a direct match
                result_node = find_node(next_node, node_type)
                if result_node:
                    return result_node
    
    return None

def find_all_nodes(current_node: bpy.types.Node, node_type: str) -> Optional[bpy.types.Node]:
    """
    Recursively finds a node of the specified type, starting from the given node.
    
    Args:
        current_node (bpy.types.Node): The node to start searching from.
        node_type (str): The type of node to search for.
    
    Returns:
        Optional[bpy.types.Node]: The found node if it matches the type, otherwise None.
    """

    nodes = []
    # Check if the current node is of the desired type
    if current_node.bl_idname == node_type:
        return current_node

    # Traverse through linked nodes via inputs
    for socket in current_node.inputs:
        if socket.is_linked:
            for node_link in socket.links:
                next_node = node_link.from_node
                if next_node.bl_idname == node_type:
                    nodes.append(next_node)
                    continue
                else:
                    # Recursive search if the node isn't a direct match
                    result_nodes = find_nodes(next_node, node_type)
                    if result_nodes:
                        nodes.append(result_nodes)
    
    return nodes

def get_operator_class_by_bl_idname(bl_idname):
    """
    Gets a operator class from its bl_idname.

    :return class: The operator class.
    """
    context, name = bl_idname.split('.')
    return getattr(bpy.types, f'{context.upper()}_OT_{name}', None)

def load_image(path):
    for image in bpy.data.images:
        if image.filepath == path:
            return image
    
    image = bpy.data.images.load(path)
    return image

def get_material_index(material):
    material_index = -1
    for index, mat in enumerate(bpy.data.materials):
        if mat == material:
            material_index = index
            break
    return material_index