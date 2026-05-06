"""Parser OBJ/MTL para a ETAPA 1 do visualizador 3D."""

from .obj_parser import (
    Face,
    FaceVertex,
    Material,
    ObjModel,
    ObjParser,
    ObjSummary,
    TextureCoordinate,
    Vector3,
)

__all__ = [
    "Face",
    "FaceVertex",
    "Material",
    "ObjModel",
    "ObjParser",
    "ObjSummary",
    "TextureCoordinate",
    "Vector3",
]