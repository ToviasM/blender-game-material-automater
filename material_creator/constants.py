from enum import Enum


class ToolInfo(Enum):
    NAME = 'material_creator'
    LABEL = 'Game Engine Material Creator'
    AREA = 'VIEW_3D'
    REGION = 'UI'
    CATEGORY = 'Material Creator'


class MaterialConstants():
    DEFAULT_TYPE = 'default'
    DEFAULT_TEMPLATE_PATH = '../templates/default.json'
