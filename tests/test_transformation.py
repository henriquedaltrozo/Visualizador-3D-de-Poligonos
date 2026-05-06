from __future__ import annotations

import math
import unittest

from visualizador_3d_poligonos.obj_parser import Vector3
from visualizador_3d_poligonos.transformation import Matrix4x4, TransformationState


class Matrix4x4Tests(unittest.TestCase):
    def test_identity_matrix_returns_same_point(self) -> None:
        """Matriz identidade não deve alterar um ponto."""
        identity = Matrix4x4.identity()
        v = Vector3(1.0, 2.0, 3.0)
        result = identity.transform_point(v)
        self.assertAlmostEqual(result.x, 1.0)
        self.assertAlmostEqual(result.y, 2.0)
        self.assertAlmostEqual(result.z, 3.0)

    def test_translation_matrix_moves_point(self) -> None:
        """Matriz de translação deve mover um ponto."""
        trans = Matrix4x4.translation(1.0, 2.0, 3.0)
        v = Vector3(0.0, 0.0, 0.0)
        result = trans.transform_point(v)
        self.assertAlmostEqual(result.x, 1.0)
        self.assertAlmostEqual(result.y, 2.0)
        self.assertAlmostEqual(result.z, 3.0)

    def test_scale_matrix_scales_vector(self) -> None:
        """Matriz de escala deve redimensionar um vetor."""
        scale = Matrix4x4.scale(2.0, 2.0, 2.0)
        v = Vector3(1.0, 1.0, 1.0)
        result = scale.transform_point(v)
        self.assertAlmostEqual(result.x, 2.0)
        self.assertAlmostEqual(result.y, 2.0)
        self.assertAlmostEqual(result.z, 2.0)

    def test_rotation_x_90_degrees(self) -> None:
        """Rotação de 90° em X transforma (0, 1, 0) em (0, 0, 1)."""
        rot = Matrix4x4.rotation_x(math.pi / 2)
        v = Vector3(0.0, 1.0, 0.0)
        result = rot.transform_vector3(v)
        self.assertAlmostEqual(result.x, 0.0, places=5)
        self.assertAlmostEqual(result.y, 0.0, places=5)
        self.assertAlmostEqual(result.z, 1.0, places=5)

    def test_rotation_y_90_degrees(self) -> None:
        """Rotação de 90° em Y transforma (1, 0, 0) em (0, 0, -1)."""
        rot = Matrix4x4.rotation_y(math.pi / 2)
        v = Vector3(1.0, 0.0, 0.0)
        result = rot.transform_vector3(v)
        self.assertAlmostEqual(result.x, 0.0, places=5)
        self.assertAlmostEqual(result.y, 0.0, places=5)
        self.assertAlmostEqual(result.z, -1.0, places=5)

    def test_rotation_z_90_degrees(self) -> None:
        """Rotação de 90° em Z transforma (1, 0, 0) em (0, 1, 0)."""
        rot = Matrix4x4.rotation_z(math.pi / 2)
        v = Vector3(1.0, 0.0, 0.0)
        result = rot.transform_vector3(v)
        self.assertAlmostEqual(result.x, 0.0, places=5)
        self.assertAlmostEqual(result.y, 1.0, places=5)
        self.assertAlmostEqual(result.z, 0.0, places=5)

    def test_matrix_multiplication(self) -> None:
        """Multiplicação de matrizes."""
        trans = Matrix4x4.translation(1.0, 0.0, 0.0)
        scale = Matrix4x4.scale(2.0, 2.0, 2.0)
        combined = trans.multiply(scale)
        
        v = Vector3(1.0, 1.0, 1.0)
        result = combined.transform_point(v)
        # Esperado: primeiro escalar (2, 2, 2), depois transladar (3, 2, 2)
        self.assertAlmostEqual(result.x, 3.0)
        self.assertAlmostEqual(result.y, 2.0)
        self.assertAlmostEqual(result.z, 2.0)


class TransformationStateTests(unittest.TestCase):
    def test_initial_state_is_identity(self) -> None:
        """Estado inicial deve ser identidade."""
        state = TransformationState()
        matrix = state.get_model_matrix()
        v = Vector3(1.0, 2.0, 3.0)
        result = matrix.transform_point(v)
        self.assertAlmostEqual(result.x, 1.0)
        self.assertAlmostEqual(result.y, 2.0)
        self.assertAlmostEqual(result.z, 3.0)

    def test_apply_scale_increases_factor(self) -> None:
        """Aplicar escala deve aumentar o fator."""
        state = TransformationState()
        state.apply_scale(0.5)
        self.assertAlmostEqual(state.scale_factor, 1.5)

    def test_apply_scale_has_minimum(self) -> None:
        """Fator de escala não deve ficar abaixo de 0.1."""
        state = TransformationState()
        state.apply_scale(-10.0)
        self.assertGreaterEqual(state.scale_factor, 0.1)

    def test_apply_rotation_incremental(self) -> None:
        """Aplicar rotação deve ser incremental."""
        state = TransformationState()
        state.apply_rotation("x", math.radians(45))
        state.apply_rotation("x", math.radians(45))
        self.assertAlmostEqual(state.rotation_x, math.radians(90), places=5)

    def test_apply_translation_incremental(self) -> None:
        """Aplicar translação deve ser incremental."""
        state = TransformationState()
        state.apply_translation(1.0, 2.0, 3.0)
        state.apply_translation(1.0, 2.0, 3.0)
        self.assertAlmostEqual(state.translation_x, 2.0)
        self.assertAlmostEqual(state.translation_y, 4.0)
        self.assertAlmostEqual(state.translation_z, 6.0)

    def test_reset_clears_all_transformations(self) -> None:
        """Reset deve limpar todas as transformações."""
        state = TransformationState()
        state.apply_scale(2.0)
        state.apply_rotation("x", math.radians(45))
        state.apply_translation(5.0, 5.0, 5.0)
        
        state.reset()
        
        self.assertAlmostEqual(state.scale_factor, 1.0)
        self.assertAlmostEqual(state.rotation_x, 0.0)
        self.assertAlmostEqual(state.rotation_y, 0.0)
        self.assertAlmostEqual(state.rotation_z, 0.0)
        self.assertAlmostEqual(state.translation_x, 0.0)
        self.assertAlmostEqual(state.translation_y, 0.0)
        self.assertAlmostEqual(state.translation_z, 0.0)

    def test_model_matrix_combines_transformations(self) -> None:
        """Matriz de modelo deve combinar todas as transformações."""
        state = TransformationState()
        state.apply_scale(1.0)  # 1.0 + 1.0 = scale_factor de 2.0
        state.apply_translation(1.0, 0.0, 0.0)
        
        matrix = state.get_model_matrix()
        v = Vector3(1.0, 0.0, 0.0)
        result = matrix.transform_point(v)
        
        # Primeiro escalar por 2: (2, 0, 0)
        # Depois transladar: (3, 0, 0)
        self.assertAlmostEqual(result.x, 3.0)
        self.assertAlmostEqual(result.y, 0.0)
        self.assertAlmostEqual(result.z, 0.0)


if __name__ == "__main__":
    unittest.main()
