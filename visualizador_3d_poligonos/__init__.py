"""Parser OBJ/MTL (ETAPA 1) e construtor de malha 3D (ETAPA 2) do visualizador 3D."""

from .mesh_builder import Mesh, Triangle, build_mesh, face_normal
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
    # Etapa 1 — parser
    "Face",
    "FaceVertex",
    "Material",
    "ObjModel",
    "ObjParser",
    "ObjSummary",
    "TextureCoordinate",
    "Vector3",
    # Etapa 2 — malha
    "Mesh",
    "Triangle",
    "build_mesh",
    "face_normal",
]