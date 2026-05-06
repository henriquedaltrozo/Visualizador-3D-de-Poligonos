from __future__ import annotations

import math
import textwrap
import unittest

from visualizador_3d_poligonos.mesh_builder import Mesh, Triangle, build_mesh, face_normal
from visualizador_3d_poligonos.obj_parser import ObjParser


def _parse(obj_text: str) -> Mesh:
    model = ObjParser().parse_text(textwrap.dedent(obj_text).strip())
    return build_mesh(model)


def _approx(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(a - b) < tol


class FaceNormalTests(unittest.TestCase):
    def test_normal_of_xy_plane_triangle(self) -> None:
        """Triângulo no plano XY deve ter normal apontando para +Z."""
        from visualizador_3d_poligonos.obj_parser import Vector3

        v0 = Vector3(0.0, 0.0, 0.0)
        v1 = Vector3(1.0, 0.0, 0.0)
        v2 = Vector3(0.0, 1.0, 0.0)
        n = face_normal(v0, v1, v2)
        self.assertTrue(_approx(n.x, 0.0))
        self.assertTrue(_approx(n.y, 0.0))
        self.assertTrue(_approx(n.z, 1.0))

    def test_normal_is_unit_length(self) -> None:
        from visualizador_3d_poligonos.obj_parser import Vector3

        v0 = Vector3(1.0, 2.0, 3.0)
        v1 = Vector3(4.0, 6.0, 3.0)
        v2 = Vector3(1.0, 5.0, 7.0)
        n = face_normal(v0, v1, v2)
        length = math.sqrt(n.x**2 + n.y**2 + n.z**2)
        self.assertAlmostEqual(length, 1.0, places=6)

    def test_degenerate_triangle_returns_fallback(self) -> None:
        """Triângulo degenerado (área zero) não deve lançar exceção."""
        from visualizador_3d_poligonos.obj_parser import Vector3

        v = Vector3(1.0, 1.0, 1.0)
        n = face_normal(v, v, v)
        length = math.sqrt(n.x**2 + n.y**2 + n.z**2)
        self.assertAlmostEqual(length, 1.0, places=6)


class FanTriangulationTests(unittest.TestCase):
    def test_triangle_face_yields_one_triangle(self) -> None:
        mesh = _parse(
            """
            v 0 0 0
            v 1 0 0
            v 0 1 0
            f 1 2 3
            """
        )
        self.assertEqual(len(mesh.triangles), 1)

    def test_quad_face_yields_two_triangles(self) -> None:
        mesh = _parse(
            """
            v 0 0 0
            v 1 0 0
            v 1 1 0
            v 0 1 0
            f 1 2 3 4
            """
        )
        self.assertEqual(len(mesh.triangles), 2)

    def test_pentagon_face_yields_three_triangles(self) -> None:
        mesh = _parse(
            """
            v 0  1 0
            v 1  0 0
            v  0.5 -1 0
            v -0.5 -1 0
            v -1  0 0
            f 1 2 3 4 5
            """
        )
        self.assertEqual(len(mesh.triangles), 3)

    def test_multiple_faces_are_accumulated(self) -> None:
        mesh = _parse(
            """
            v 0 0 0
            v 1 0 0
            v 1 1 0
            v 0 1 0
            v 0 0 1
            f 1 2 3
            f 1 3 4
            f 1 2 5
            """
        )
        self.assertEqual(len(mesh.triangles), 3)


class CentroidAndScaleTests(unittest.TestCase):
    def test_centroid_is_stored(self) -> None:
        """O centroide deve ser a média dos vértices originais."""
        mesh = _parse(
            """
            v -1 0 0
            v  1 0 0
            v  0 2 0
            f 1 2 3
            """
        )
        # Centroide: ((-1+1+0)/3, (0+0+2)/3, 0) = (0, 2/3, 0)
        self.assertTrue(_approx(mesh.centroid.x, 0.0))
        self.assertTrue(_approx(mesh.centroid.y, 2.0 / 3.0))
        self.assertTrue(_approx(mesh.centroid.z, 0.0))

    def test_vertices_are_centered_at_origin(self) -> None:
        """Após centrar, a média das posições dos vértices no triângulo deve ser ~0."""
        mesh = _parse(
            """
            v 0 0 0
            v 4 0 0
            v 0 4 0
            f 1 2 3
            """
        )
        tri = mesh.triangles[0]
        xs = [p.x for p in tri.positions]
        ys = [p.y for p in tri.positions]
        # centroide original: (4/3, 4/3, 0) → após subtrair, média = 0
        self.assertAlmostEqual(sum(xs) / 3, 0.0, places=6)
        self.assertAlmostEqual(sum(ys) / 3, 0.0, places=6)

    def test_scale_factor_is_positive(self) -> None:
        mesh = _parse(
            """
            v -10 0 0
            v  10 0 0
            v   0 10 0
            f 1 2 3
            """
        )
        self.assertGreater(mesh.scale_factor, 0.0)

    def test_all_vertices_within_unit_sphere(self) -> None:
        """Todos os vértices processados devem caber no raio 1."""
        mesh = _parse(
            """
            v 0   0   0
            v 100 0   0
            v 0   100 0
            v 0   0   100
            f 1 2 3
            f 1 2 4
            f 1 3 4
            f 2 3 4
            """
        )
        for tri in mesh.triangles:
            for p in tri.positions:
                dist = math.sqrt(p.x**2 + p.y**2 + p.z**2)
                self.assertLessEqual(dist, 1.0 + 1e-6)

    def test_empty_model_returns_empty_mesh(self) -> None:
        model = ObjParser().parse_text("")
        mesh = build_mesh(model)
        self.assertEqual(len(mesh.triangles), 0)


class NormalsTests(unittest.TestCase):
    def test_normals_computed_when_not_in_file(self) -> None:
        """Quando o .obj não tem 'vn', normais devem ser calculadas."""
        mesh = _parse(
            """
            v 0 0 0
            v 1 0 0
            v 0 1 0
            f 1 2 3
            """
        )
        self.assertTrue(mesh.normals_computed)
        tri = mesh.triangles[0]
        for n in tri.normals:
            length = math.sqrt(n.x**2 + n.y**2 + n.z**2)
            self.assertAlmostEqual(length, 1.0, places=6)

    def test_normals_from_file_are_used(self) -> None:
        """Quando o .obj tem 'vn', elas devem ser usadas (não calculadas)."""
        mesh = _parse(
            """
            v 0 0 0
            v 1 0 0
            v 0 1 0
            vn 0 0 1
            vn 0 0 1
            vn 0 0 1
            f 1//1 2//2 3//3
            """
        )
        self.assertFalse(mesh.normals_computed)
        tri = mesh.triangles[0]
        for n in tri.normals:
            self.assertAlmostEqual(n.z, 1.0, places=6)

    def test_computed_normal_direction_xy_plane(self) -> None:
        """Triângulo no plano XY (sentido anti-horário) → normal +Z."""
        mesh = _parse(
            """
            v 0 0 0
            v 1 0 0
            v 0 1 0
            f 1 2 3
            """
        )
        tri = mesh.triangles[0]
        # Todas as três normais são a mesma normal de face
        for n in tri.normals:
            self.assertGreater(n.z, 0.0)

    def test_quad_triangulated_normals_are_consistent(self) -> None:
        """Quad planar triangulado deve ter normais consistentes nos dois triângulos."""
        mesh = _parse(
            """
            v 0 0 0
            v 1 0 0
            v 1 1 0
            v 0 1 0
            f 1 2 3 4
            """
        )
        self.assertEqual(len(mesh.triangles), 2)
        n0 = mesh.triangles[0].normals[0]
        n1 = mesh.triangles[1].normals[0]
        self.assertAlmostEqual(n0.x, n1.x, places=5)
        self.assertAlmostEqual(n0.y, n1.y, places=5)
        self.assertAlmostEqual(n0.z, n1.z, places=5)


class MaterialAndTexcoordTests(unittest.TestCase):
    def test_material_name_propagated_to_triangles(self) -> None:
        mesh = _parse(
            """
            v 0 0 0
            v 1 0 0
            v 0 1 0
            usemtl red
            f 1 2 3
            """
        )
        self.assertEqual(mesh.triangles[0].material_name, "red")

    def test_texcoords_are_propagated(self) -> None:
        mesh = _parse(
            """
            v 0 0 0
            v 1 0 0
            v 0 1 0
            vt 0 0
            vt 1 0
            vt 0 1
            vn 0 0 1
            vn 0 0 1
            vn 0 0 1
            f 1/1/1 2/2/2 3/3/3
            """
        )
        tri = mesh.triangles[0]
        self.assertIsNotNone(tri.texcoords[0])
        self.assertIsNotNone(tri.texcoords[1])
        self.assertIsNotNone(tri.texcoords[2])

    def test_missing_texcoords_are_none(self) -> None:
        mesh = _parse(
            """
            v 0 0 0
            v 1 0 0
            v 0 1 0
            f 1 2 3
            """
        )
        tri = mesh.triangles[0]
        for t in tri.texcoords:
            self.assertIsNone(t)


if __name__ == "__main__":
    unittest.main()
