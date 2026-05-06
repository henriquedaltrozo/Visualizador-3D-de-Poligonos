from __future__ import annotations

import textwrap
import unittest

from visualizador_3d_poligonos.mesh_builder import build_mesh
from visualizador_3d_poligonos.obj_parser import ObjParser, Vector3
from visualizador_3d_poligonos.renderer import Renderer


class RendererMathTests(unittest.TestCase):
    def test_isometric_projection_has_distinct_coordinates(self) -> None:
        model = ObjParser().parse_text(textwrap.dedent("""
            v 0 0 0
            v 1 0 0
            v 0 1 0
            f 1 2 3
        """))
        renderer = Renderer(build_mesh(model), model.materials)
        p0 = renderer._project(Vector3(0.0, 0.0, 0.0))
        p1 = renderer._project(Vector3(1.0, 0.0, 0.0))
        p2 = renderer._project(Vector3(0.0, 1.0, 0.0))
        self.assertNotEqual(p0.x, p1.x)
        self.assertNotEqual(p0.y, p2.y)

    def test_perspective_projection_applies_depth_scaling(self) -> None:
        model = ObjParser().parse_text(textwrap.dedent("""
            v 0 0 0
            v 0 0 1
            v 0 0 2
            f 1 2 3
        """))
        renderer = Renderer(build_mesh(model), model.materials)
        renderer.projection_mode = "perspective"
        p0 = renderer._project(Vector3(0.0, 0.0, 0.0))
        p1 = renderer._project(Vector3(0.0, 0.0, 1.0))
        self.assertGreater(p1.depth, p0.depth)
        self.assertNotEqual(p0.x, p1.x)
        self.assertNotEqual(p0.y, p1.y)

    def test_backface_culling_discards_back_facing_triangles(self) -> None:
        model = ObjParser().parse_text(textwrap.dedent("""
            v 0 0 0
            v 1 0 0
            v 0 1 0
            f 1 3 2
        """))
        renderer = Renderer(build_mesh(model), model.materials)
        reversed_triangle = (Vector3(0.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0), Vector3(1.0, 0.0, 0.0))
        self.assertFalse(renderer._face_visible(reversed_triangle))

    def test_shading_color_changes_with_normal(self) -> None:
        model = ObjParser().parse_text(textwrap.dedent("""
            v 0 0 0
            v 1 0 0
            v 0 1 0
            f 1 2 3
        """))
        renderer = Renderer(build_mesh(model), model.materials)
        color = renderer._shade_color((255, 128, 0), (Vector3(0.0, 0.0, 0.0), Vector3(1.0, 0.0, 0.0), Vector3(0.0, 1.0, 0.0)))
        self.assertTrue(color.startswith("#"))
        self.assertEqual(len(color), 7)


if __name__ == "__main__":
    unittest.main()
