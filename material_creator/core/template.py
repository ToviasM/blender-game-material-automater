import json
from dataclasses import dataclass, asdict
import typing as t


@dataclass
class TextureSlot():
    slot_name: str
    description: str
    properties: t.Dict[str, t.Dict[str, str]]
    connections: t.List[t.List[str]]
    
    @classmethod
    def from_dict(cls: t.Type["TextureSlot"], obj: t.Dict):
        return cls(
            slot_name=obj["slot_name"],
            description=obj["description"],
            properties=obj["properties"],
            connections=obj["connections"]
        )

    def dict(self):
        return {k: str(v) for k, v in asdict(self.items())}


@dataclass
class MaterialType():
    suffix: str
    required_texture_slots: t.List[TextureSlot]
    optional_texture_slots: t.List[TextureSlot]

    @classmethod
    def from_dict(cls: t.Type["MaterialType"], obj: t.Dict):
        return cls(
            suffix=obj["suffix"],
            required_texture_slots=[TextureSlot.from_dict(item) for item in obj["required_texture_slots"]],
            optional_texture_slots=[TextureSlot.from_dict(item) for item in obj["optional_texture_slots"]]
        )

    def dict(self):
        return {k: str(v) for k, v in asdict(self.items())}
 

@dataclass
class MaterialConfig():
    material_types: t.Dict[str, MaterialType]

    @classmethod
    def from_dict(cls: t.Type["MaterialConfig"], obj: t.Dict):
        
        return cls(
            material_types={key: MaterialType.from_dict(item) for key, item in obj["material_types"].items()}
        )

    def dict(self):
        return {k: str(v) for k, v in asdict(self.items())}


@dataclass
class ShaderConfig():
    node_attributes: t.Dict[str, str]

    @classmethod
    def from_dict(cls: t.Type["ShaderConfig"], obj: t.Dict):
        return cls(
            node_attributes=obj["node_attributes"]
        )

    def dict(self):
        return {k: str(v) for k, v in asdict(self.items())}


@dataclass
class Template():
    material_config: MaterialConfig
    shader_config: ShaderConfig

    @classmethod
    def from_json(cls: t.Type["Template"], path: str):
        with open(path, 'r') as f:
            obj = json.load(f)

        return cls(
            material_config=MaterialConfig.from_dict(obj["material_config"]),
            shader_config=ShaderConfig.from_dict(obj["shader_config"]),
        )
 
    @classmethod
    def from_dict(cls: t.Type["Template"], obj: t.Dict):
        return cls(
            material_config=MaterialConfig.from_dict(obj["material_config"]),
            shader_config=ShaderConfig.from_dict(obj["shader_config"]),
        )

    def dict(self):
        return {k: str(v) for k, v in asdict(self.items())}
