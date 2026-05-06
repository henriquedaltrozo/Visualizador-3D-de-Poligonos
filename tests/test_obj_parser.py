from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from visualizador_3d_poligonos.obj_parser import ObjParser


class ObjParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = ObjParser()

    def test_parses_faces_in_all_supported_formats(self) -> None:
        obj_text = textwrap.dedent(
            """
            mtllib sample.mtl
            g base
            v 0 0 0
            v 1 0 0
            v 1 1 0
            v 0 1 0
            vt 0 0
            vt 1 0
            vt 1 1
            vt 0 1
            vn 0 0 1
            vn 0 0 1
            vn 0 0 1
            vn 0 0 1
            usemtl red
            f 1 2 3
            f 1/1/1 2/2/2 3/3/3 4/4/4
            f -4//-4 -3//-3 -2//-2
            """
        ).strip()

        model = self.parser.parse_text(obj_text)

        self.assertEqual(len(model.vertices), 4)
        self.assertEqual(len(model.texcoords), 4)
        self.assertEqual(len(model.normals), 4)
        self.assertEqual(len(model.faces), 3)
        self.assertEqual(model.faces[0].vertices[0].position_index, 0)
        self.assertEqual(model.faces[1].vertices[0].texcoord_index, 0)
        self.assertEqual(model.faces[2].vertices[0].normal_index, 0)
        self.assertEqual(model.faces[0].group_name, "base")
        self.assertEqual(model.faces[0].material_name, "red")
        self.assertEqual(model.mtllibs, ["sample.mtl"])

    def test_loads_material_library_and_counts_euler(self) -> None:
        obj_text = textwrap.dedent(
            """
            mtllib tetra.mtl
            v 0 0 0
            v 1 0 0
            v 0 1 0
            v 0 0 1
            usemtl blue
            f 1 2 3
            f 1 2 4
            f 1 3 4
            f 2 3 4
            """
        ).strip()
        mtl_text = textwrap.dedent(
            """
            newmtl blue
            Kd 0.2 0.3 0.8
            Ns 32
            """
        ).strip()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            obj_path = tmp_path / "tetra.obj"
            mtl_path = tmp_path / "tetra.mtl"
            obj_path.write_text(obj_text, encoding="utf-8")
            mtl_path.write_text(mtl_text, encoding="utf-8")

            model = self.parser.parse_file(obj_path)

        summary = model.summary()
        self.assertEqual(summary.vertices, 4)
        self.assertEqual(summary.edges, 6)
        self.assertEqual(summary.faces, 4)
        self.assertEqual(summary.euler_characteristic, 2)
        self.assertTrue(summary.euler_matches)
        self.assertIn("blue", model.materials)
        self.assertEqual(model.materials["blue"].diffuse.x, 0.2)


if __name__ == "__main__":
    unittest.main()