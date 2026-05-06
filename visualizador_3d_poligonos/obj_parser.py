from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Sequence


@dataclass(slots=True, frozen=True)
class Vector3:
    x: float
    y: float
    z: float


@dataclass(slots=True, frozen=True)
class TextureCoordinate:
    u: float
    v: float
    w: float = 0.0


@dataclass(slots=True, frozen=True)
class FaceVertex:
    position_index: int
    texcoord_index: int | None = None
    normal_index: int | None = None


@dataclass(slots=True, frozen=True)
class Face:
    vertices: tuple[FaceVertex, ...]
    material_name: str | None = None
    group_name: str | None = None


@dataclass(slots=True)
class Material:
    name: str
    ambient: Vector3 | None = None
    diffuse: Vector3 | None = None
    specular: Vector3 | None = None
    emissive: Vector3 | None = None
    specular_exponent: float | None = None
    dissolve: float | None = None
    optical_density: float | None = None
    illumination_model: int | None = None
    diffuse_map: str | None = None
    ambient_map: str | None = None
    specular_map: str | None = None
    transparency_map: str | None = None
    extras: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ObjSummary:
    vertices: int
    edges: int
    faces: int
    euler_characteristic: int
    euler_matches: bool


@dataclass(slots=True)
class ObjModel:
    vertices: list[Vector3] = field(default_factory=list)
    texcoords: list[TextureCoordinate] = field(default_factory=list)
    normals: list[Vector3] = field(default_factory=list)
    faces: list[Face] = field(default_factory=list)
    materials: dict[str, Material] = field(default_factory=dict)
    mtllibs: list[str] = field(default_factory=list)
    group_names: list[str] = field(default_factory=list)
    source_path: Path | None = None

    def summary(self) -> ObjSummary:
        edges = self.edge_count()
        vertex_count = len(self.vertices)
        face_count = len(self.faces)
        euler_value = vertex_count - edges + face_count
        return ObjSummary(
            vertices=vertex_count,
            edges=edges,
            faces=face_count,
            euler_characteristic=euler_value,
            euler_matches=euler_value == 2,
        )

    def edge_count(self) -> int:
        edges: set[tuple[int, int]] = set()
        for face in self.faces:
            indices = [vertex.position_index for vertex in face.vertices]
            if len(indices) < 2:
                continue
            for start, end in zip(indices, indices[1:] + indices[:1], strict=False):
                edge = (start, end) if start < end else (end, start)
                edges.add(edge)
        return len(edges)


class ObjParser:
    def parse_file(self, path: str | Path) -> ObjModel:
        obj_path = Path(path)
        text = obj_path.read_text(encoding="utf-8", errors="ignore")
        return self.parse_text(text, source_path=obj_path)

    def parse_text(
        self,
        text: str,
        *,
        source_path: Path | None = None,
        mtl_loader: Callable[[Path], str] | None = None,
    ) -> ObjModel:
        model = ObjModel(source_path=source_path)
        current_group = None
        current_material = None
        pending_mtllibs: list[str] = []

        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue

            parts = line.split()
            prefix = parts[0]
            values = parts[1:]

            if prefix == "v":
                if len(values) < 3:
                    raise ValueError(f"Invalid vertex line: {raw_line!r}")
                model.vertices.append(Vector3(float(values[0]), float(values[1]), float(values[2])))
                continue

            if prefix == "vt":
                if len(values) < 2:
                    raise ValueError(f"Invalid texture coordinate line: {raw_line!r}")
                w = float(values[2]) if len(values) > 2 else 0.0
                model.texcoords.append(TextureCoordinate(float(values[0]), float(values[1]), w))
                continue

            if prefix == "vn":
                if len(values) < 3:
                    raise ValueError(f"Invalid normal line: {raw_line!r}")
                model.normals.append(Vector3(float(values[0]), float(values[1]), float(values[2])))
                continue

            if prefix == "f":
                if len(values) < 3:
                    raise ValueError(f"A face needs at least three vertices: {raw_line!r}")
                face_vertices = tuple(
                    self._parse_face_vertex(
                        token,
                        vertex_count=len(model.vertices),
                        texcoord_count=len(model.texcoords),
                        normal_count=len(model.normals),
                    )
                    for token in values
                )
                model.faces.append(
                    Face(vertices=face_vertices, material_name=current_material, group_name=current_group)
                )
                continue

            if prefix == "g":
                current_group = " ".join(values) if values else None
                if current_group and current_group not in model.group_names:
                    model.group_names.append(current_group)
                continue

            if prefix == "usemtl":
                current_material = " ".join(values) if values else None
                continue

            if prefix == "mtllib":
                libraries = [value for value in values if value]
                pending_mtllibs.extend(libraries)
                model.mtllibs.extend(libraries)
                continue

        for library in pending_mtllibs:
            material_text = self._load_material_library(library, source_path=source_path, mtl_loader=mtl_loader)
            if material_text is None:
                continue
            parsed_materials = self.parse_mtl_text(material_text)
            model.materials.update(parsed_materials)

        return model

    def parse_mtl_file(self, path: str | Path) -> dict[str, Material]:
        mtl_path = Path(path)
        return self.parse_mtl_text(mtl_path.read_text(encoding="utf-8", errors="ignore"))

    def parse_mtl_text(self, text: str) -> dict[str, Material]:
        materials: dict[str, Material] = {}
        current: Material | None = None

        for raw_line in text.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue

            parts = line.split()
            prefix = parts[0]
            values = parts[1:]

            if prefix == "newmtl":
                if not values:
                    raise ValueError(f"Invalid material declaration: {raw_line!r}")
                current = Material(name=" ".join(values))
                materials[current.name] = current
                continue

            if current is None:
                continue

            if prefix == "Ka":
                current.ambient = self._parse_vector3(values, raw_line)
                continue
            if prefix == "Kd":
                current.diffuse = self._parse_vector3(values, raw_line)
                continue
            if prefix == "Ks":
                current.specular = self._parse_vector3(values, raw_line)
                continue
            if prefix == "Ke":
                current.emissive = self._parse_vector3(values, raw_line)
                continue
            if prefix == "Ns":
                current.specular_exponent = float(values[0])
                continue
            if prefix == "d":
                current.dissolve = float(values[0])
                continue
            if prefix == "Tr":
                current.dissolve = 1.0 - float(values[0])
                continue
            if prefix == "Ni":
                current.optical_density = float(values[0])
                continue
            if prefix == "illum":
                current.illumination_model = int(values[0])
                continue
            if prefix == "map_Kd":
                current.diffuse_map = " ".join(values)
                continue
            if prefix == "map_Ka":
                current.ambient_map = " ".join(values)
                continue
            if prefix == "map_Ks":
                current.specular_map = " ".join(values)
                continue
            if prefix == "map_d":
                current.transparency_map = " ".join(values)
                continue

            current.extras[prefix] = " ".join(values)

        return materials

    def _load_material_library(
        self,
        library_name: str,
        *,
        source_path: Path | None,
        mtl_loader: Callable[[Path], str] | None,
    ) -> str | None:
        if mtl_loader is not None:
            candidate = Path(library_name)
            if source_path is not None and not candidate.is_absolute():
                candidate = source_path.parent / candidate
            return mtl_loader(candidate)

        candidate = Path(library_name)
        if source_path is not None and not candidate.is_absolute():
            candidate = source_path.parent / candidate
        if candidate.exists():
            return candidate.read_text(encoding="utf-8", errors="ignore")
        return None

    def _parse_face_vertex(
        self,
        token: str,
        *,
        vertex_count: int,
        texcoord_count: int,
        normal_count: int,
    ) -> FaceVertex:
        parts = token.split("/")
        position_index = self._resolve_index(parts[0], vertex_count)

        texcoord_index: int | None = None
        if len(parts) >= 2 and parts[1]:
            texcoord_index = self._resolve_index(parts[1], texcoord_count)

        normal_index: int | None = None
        if len(parts) >= 3 and parts[2]:
            normal_index = self._resolve_index(parts[2], normal_count)

        return FaceVertex(
            position_index=position_index,
            texcoord_index=texcoord_index,
            normal_index=normal_index,
        )

    def _resolve_index(self, token: str, size: int) -> int:
        index = int(token)
        if index == 0:
            raise ValueError("OBJ indices are 1-based or negative relative indices; 0 is invalid")
        if index > 0:
            resolved = index - 1
        else:
            resolved = size + index
        if resolved < 0 or resolved >= size:
            raise ValueError(f"OBJ index {token} is out of range for a list with {size} items")
        return resolved

    def _parse_vector3(self, values: Sequence[str], raw_line: str) -> Vector3:
        if len(values) < 3:
            raise ValueError(f"Invalid 3D vector line: {raw_line!r}")
        return Vector3(float(values[0]), float(values[1]), float(values[2]))


def _format_summary(model: ObjModel) -> str:
    summary = model.summary()
    lines = [
        f"Vertices (V): {summary.vertices}",
        f"Edges (E): {summary.edges}",
        f"Faces (F): {summary.faces}",
        f"Euler characteristic: {summary.euler_characteristic}",
        f"Euler check (V - E + F = 2): {'yes' if summary.euler_matches else 'no'}",
    ]

    if model.materials:
        lines.append(f"Materials loaded: {', '.join(sorted(model.materials))}")
    if model.mtllibs:
        lines.append(f"Material libraries: {', '.join(model.mtllibs)}")
    if model.group_names:
        lines.append(f"Groups: {', '.join(model.group_names)}")

    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Parser OBJ/MTL da ETAPA 1")
    parser.add_argument("obj_path", help="Caminho para o arquivo .obj")
    args = parser.parse_args(list(argv) if argv is not None else None)

    model = ObjParser().parse_file(args.obj_path)
    print(_format_summary(model))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())