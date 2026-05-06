"""TRANSFORMAÇÕES 3D — Matrizes 4x4 e operações de transformação."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from .obj_parser import Vector3


@dataclass(slots=True, frozen=True)
class Matrix4x4:
    """Matriz 4x4 para transformações 3D homogêneas."""

    m: tuple[tuple[float, float, float, float], tuple[float, float, float, float],
             tuple[float, float, float, float], tuple[float, float, float, float]]

    def __post_init__(self) -> None:
        """Valida a forma da matriz."""
        if len(self.m) != 4 or any(len(row) != 4 for row in self.m):
            raise ValueError("Matrix4x4 deve ser 4x4")

    @staticmethod
    def identity() -> Matrix4x4:
        """Retorna a matriz identidade 4x4."""
        return Matrix4x4((
            (1.0, 0.0, 0.0, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ))

    @staticmethod
    def translation(x: float, y: float, z: float) -> Matrix4x4:
        """Cria uma matriz de translação."""
        return Matrix4x4((
            (1.0, 0.0, 0.0, x),
            (0.0, 1.0, 0.0, y),
            (0.0, 0.0, 1.0, z),
            (0.0, 0.0, 0.0, 1.0),
        ))

    @staticmethod
    def scale(sx: float, sy: float, sz: float) -> Matrix4x4:
        """Cria uma matriz de escala uniforme ou não-uniforme."""
        return Matrix4x4((
            (sx, 0.0, 0.0, 0.0),
            (0.0, sy, 0.0, 0.0),
            (0.0, 0.0, sz, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ))

    @staticmethod
    def rotation_x(angle: float) -> Matrix4x4:
        """Cria uma matriz de rotação em torno do eixo X (ângulo em radianos)."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Matrix4x4((
            (1.0, 0.0, 0.0, 0.0),
            (0.0, cos_a, -sin_a, 0.0),
            (0.0, sin_a, cos_a, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ))

    @staticmethod
    def rotation_y(angle: float) -> Matrix4x4:
        """Cria uma matriz de rotação em torno do eixo Y (ângulo em radianos)."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Matrix4x4((
            (cos_a, 0.0, sin_a, 0.0),
            (0.0, 1.0, 0.0, 0.0),
            (-sin_a, 0.0, cos_a, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ))

    @staticmethod
    def rotation_z(angle: float) -> Matrix4x4:
        """Cria uma matriz de rotação em torno do eixo Z (ângulo em radianos)."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Matrix4x4((
            (cos_a, -sin_a, 0.0, 0.0),
            (sin_a, cos_a, 0.0, 0.0),
            (0.0, 0.0, 1.0, 0.0),
            (0.0, 0.0, 0.0, 1.0),
        ))

    def multiply(self, other: Matrix4x4) -> Matrix4x4:
        """Multiplica esta matriz por outra (self * other)."""
        result = [[0.0] * 4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    result[i][j] += self.m[i][k] * other.m[k][j]
        return Matrix4x4(tuple(tuple(row) for row in result))

    def transform_vector3(self, v: Vector3) -> Vector3:
        """Transforma um Vector3 usando a matriz (ignora translação, apenas rotação/escala)."""
        x = self.m[0][0] * v.x + self.m[0][1] * v.y + self.m[0][2] * v.z
        y = self.m[1][0] * v.x + self.m[1][1] * v.y + self.m[1][2] * v.z
        z = self.m[2][0] * v.x + self.m[2][1] * v.y + self.m[2][2] * v.z
        return Vector3(x, y, z)

    def transform_point(self, v: Vector3) -> Vector3:
        """Transforma um ponto 3D incluindo translação."""
        x = self.m[0][0] * v.x + self.m[0][1] * v.y + self.m[0][2] * v.z + self.m[0][3]
        y = self.m[1][0] * v.x + self.m[1][1] * v.y + self.m[1][2] * v.z + self.m[1][3]
        z = self.m[2][0] * v.x + self.m[2][1] * v.y + self.m[2][2] * v.z + self.m[2][3]
        return Vector3(x, y, z)


@dataclass(slots=True)
class TransformationState:
    """Estado das transformações do objeto: posição, rotação e escala."""

    # Translação (em coordenadas de tela)
    translation_x: float = 0.0
    translation_y: float = 0.0
    translation_z: float = 0.0

    # Rotação (em radianos)
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0

    # Escala
    scale_factor: float = 1.0

    def get_model_matrix(self) -> Matrix4x4:
        """Retorna a matriz de modelo combinada (T × R × S)."""
        # Escala
        scale_matrix = Matrix4x4.scale(self.scale_factor, self.scale_factor, self.scale_factor)

        # Rotações em ZYX (ordem comum)
        rot_z = Matrix4x4.rotation_z(self.rotation_z)
        rot_y = Matrix4x4.rotation_y(self.rotation_y)
        rot_x = Matrix4x4.rotation_x(self.rotation_x)

        # Combinar rotações: Rz × Ry × Rx
        rotation_matrix = rot_z.multiply(rot_y).multiply(rot_x)

        # Escala × Rotação
        sr_matrix = rotation_matrix.multiply(scale_matrix)

        # Translação
        translation_matrix = Matrix4x4.translation(self.translation_x, self.translation_y, self.translation_z)

        # Translação × (Rotação × Escala)
        return translation_matrix.multiply(sr_matrix)

    def reset(self) -> None:
        """Reseta todas as transformações para o estado inicial."""
        self.translation_x = 0.0
        self.translation_y = 0.0
        self.translation_z = 0.0
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0
        self.scale_factor = 1.0

    def apply_scale(self, delta: float) -> None:
        """Ajusta o fator de escala (delta positivo aumenta)."""
        self.scale_factor = max(0.1, self.scale_factor + delta)

    def apply_rotation(self, axis: str, delta: float) -> None:
        """Aplica rotação incremental em torno de um eixo ('x', 'y' ou 'z')."""
        if axis.lower() == 'x':
            self.rotation_x += delta
        elif axis.lower() == 'y':
            self.rotation_y += delta
        elif axis.lower() == 'z':
            self.rotation_z += delta

    def apply_translation(self, dx: float, dy: float, dz: float = 0.0) -> None:
        """Aplica translação incremental."""
        self.translation_x += dx
        self.translation_y += dy
        self.translation_z += dz
