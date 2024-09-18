from .template import Template, TextureSlot
import bpy
import logging
from typing import List, Optional, Any, Dict

LOGGER = logging.getLogger(__name__)


class Material():
    DEFAULT_TYPE = "default"

    def __init__(self, material_name: str, template_config: 'Template', logger: Optional[Any] = None):
        """
        Initializes a Material instance.

        Args:
            material_name (str): The name of the material.
            template_config (Template): The configuration template for the material.
            logger (Optional[Any]): A logger instance for logging errors or warnings. Defaults to a global LOGGER.
        """
       
        # private 
        self._material_type = None
        self._material_name = material_name

        # public
        self.template = template_config
        self.logger = logger or LOGGER

    @property
    def material_name(self):
        if self._material_name in bpy.data.materials:
            return self._material_name
        else:
            self.logger.error(f"Cannot find material named {self._material_name}")

    @property
    def material_type(self):
        if not self._material_type:
            self._material_type = self.get_material_type()
        return self._material_type

    @property
    def node_tree(self):
        return bpy.data.materials.get(self.material_name).node_tree

    @material_type.setter
    def material_type(self, type_name: str):
        new_type = self.template.material_config.material_types[type_name]
        if not new_type:
            new_type = self.DEFAULT_TYPE

        self.rename_material(self.material_name.replace(self.material_type, new_type.suffix))

        self.create_texture_nodes()

    def get_material_type(self) -> str:
        """
        Determines the material type based on the material name suffix.
       
        Returns:
            str: The material type name. If no match is found, returns the default type.
        """
        for name, mat_type in self.template.material_config.material_types.items():
            if self.material_name.endswith(mat_type.suffix):
                return name

        return self.DEFAULT_TYPE

    def rename_material(self, new_name: str) -> None:
        """
        Renames the current material to the new name.
       
        Args:
            new_name (str): The new name to assign to the material.
        """
        material = bpy.data.materials.get(self.material_name)
        if material:
            material.name = new_name
        else:
            self.logger.error(f"Material '{self.material_name}' not found, unable to rename.")

    def get_texture_slots(self, optional: bool = False) -> List[Optional['TextureSlot']]:
        """
        Retrieves the required and optional texture slots for the current material type.
        
        Args:
            optional (bool): If True, includes optional texture slots along with required ones.
       
        Returns:
            List[Optional[TextureSlot]]: A list of texture slots, including optional ones if specified.
        """
        material_type = self.template.material_config.material_types[self.get_material_type()]
        required_slots = material_type.required_texture_slots
        optional_slots = material_type.optional_texture_slots if optional else []

        # Combine required and optional slots if optional flag is True
        if optional_slots:
            required_slots.extend(optional_slots)
           
        return required_slots

    def get_shader_node(self) -> Optional[bpy.types.Node]:
        """
        Retrieves the shader node connected to the 'Surface' input of the material output node.
       
        Returns:
            Optional[bpy.types.Node]: The shader node if connected, None otherwise.
        """
        material_output = self.node_tree.nodes[0]
        input_socket = material_output.inputs['Surface']
       
        if input_socket.is_linked:
            return input_socket.links[0].from_node
        else:
            self.logger.error("Could not find Shader Node")
            return None

    def create_texture_node(self, slot: Any) -> None:
        """
        Creates a texture node for the specified slot and connects it to the shader node.
       
        Args:
            slot (Any): The texture slot for which a texture node will be created.
        """
        for connection in slot.connections:
            input_node = self.get_shader_node()
            if not input_node:
                self.logger.error("Failed to create texture node: Shader node not found.")
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
                    connected_node = self.find_node(shader_input_socket.links[0].from_node, output_attr.split(".")[0])

                # Create a new node if no connected node was found
                if not connected_node:
                    connected_node = self.node_tree.nodes.new(type=output_attr.split(".")[0])

                # Create a link between the output and input
                self.node_tree.links.new(
                    connected_node.outputs[output_attr.split(".")[1]], 
                    input_node.inputs[input_attr.split(".")[1]]
                )

                # Apply shader properties for the input node if defined
                input_properties = slot.properties.get(input_attr.split(".")[0])
                if input_properties:
                    self.apply_shader_properties(input_node, input_properties)

                # Apply shader properties for the connected node if defined
                output_properties = slot.properties.get(output_attr.split(".")[0])
                if output_properties:
                    self.apply_shader_properties(connected_node, output_properties)
               
                # Update input node to connected node for the next iteration
                input_node = connected_node
   
    # TODO: Extract Indices so we can access import shader variables such as "input[0]"
    def apply_shader_properties(self, node: bpy.types.Node, shader_property_block: Dict[str, Any]) -> None:
        """
        Applies shader properties from the given property block to the specified node.
       
        Args:
            node (bpy.types.Node): The shader node to which properties will be applied.
            shader_property_block (Dict[str, Any]): A dictionary containing shader properties and their values.
        """
        for properties, value in shader_property_block.items():
            current_property = node
           
            # Traverse through the property chain, excluding the last one
            for prop in properties.split(".")[:-1]:
                if not current_property:
                    return None
                current_property = getattr(current_property, prop)
           
            # Set the final property value
            setattr(current_property, properties.split(".")[-1], value)

    def create_texture_slot(self, slot_type: str) -> None:
        """
        Creates a texture slot of the specified type by creating a texture node in the corresponding slot.
       
        Args:
            slot_type (str): The type of texture slot to create.
        """
        for slot in self.get_texture_slots(optional=True):
            if slot.name == slot_type:
                self.create_texture_node(slot)

    def create_material_nodes(self) -> None:
        """
        Iterates over all texture slots and creates texture nodes for each slot.
        """
        for slot in self.get_texture_slots():
            self.create_texture_node(slot)

    def find_node(self, current_node: bpy.types.Node, node_type: str) -> Optional[bpy.types.Node]:
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
                    result_node = self.find_node(next_node, node_type)
                    if result_node:
                        return result_node
       
        return None

    def get_texture_node(self, slot_name: str) -> Optional[bpy.types.Node]:
        """
        Retrieves the texture node for the given slot name.
       
        Args:
            slot_name (str): The name of the texture slot to retrieve the texture node from.
       
        Returns:
            Optional[bpy.types.Node]: The texture node if found, None otherwise.
        """
        texture_node = None
       
        for slot in self.get_texture_slots(optional=True):
            if slot.slot_name == slot_name:
                for connection in slot.connections:
                    for attributes in connection:
                        # Extract the input attribute from the connection
                        input_attribute = attributes[1].split(".")[1]
                       
                        if "{SHADER}" not in attributes[1]:
                            continue
                       
                        start_node = self.get_shader_node().inputs[input_attribute]

                        # Check if the input is linked to a texture node
                        if start_node.is_linked:
                            node = self.find_node(start_node.links[0].from_node, "ShaderNodeTexImage")
                           
                            if texture_node and texture_node != node:
                                self.logger.error(
                                    f"Multiple textures connected to slot '{slot_name}'! Only one is allowed."
                                )
                            texture_node = node
                        else:
                            self.logger.warning(
                                f"Texture is not connected for slot '{slot_name}' at '{input_attribute}'."
                            )

        return texture_node

    def set_texture_map(self, slot_name: str, path: str) -> None:
        """
        Sets the texture map for the given slot name by loading an image from the specified path.
       
        Args:
            slot_name (str): The name of the texture slot to apply the texture map to.
            path (str): The file path of the image to load.
        """
        texture_node = self.get_texture_node(slot_name)
        if texture_node is None:
            self.logger.error(f"No texture node found for slot '{slot_name}'")
            return
       
        # Load the image from the specified path
        image = bpy.data.images.load(path)
       
        # Apply the image to the texture node
        self.apply_shader_properties(texture_node, {"image": image})

        # Apply additional shader properties if available
        for slot in self.get_texture_slots(optional=True):
            if slot.slot_name == slot_name:
                properties = slot.properties.get(texture_node.bl_idname)
                if properties:
                    self.apply_shader_properties(texture_node, properties)