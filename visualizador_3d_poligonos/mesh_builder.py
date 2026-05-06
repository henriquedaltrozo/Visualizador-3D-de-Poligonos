"""ETAPA 2 — Construção da malha 3D a partir dos dados do parser OBJ."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from .obj_parser import ObjModel, TextureCoordinate, Vector3

# ── Data structures ───────────────────────────────────────────────────────────


@dataclass(slots=True, frozen=True)
class Triangle:
    """Um triângulo pronto para renderização, com posições, normais e UVs."""

    positions: tuple[Vector3, Vector3, Vector3]
    normals: tuple[Vector3, Vector3, Vector3]
    texcoords: tuple[TextureCoordinate | None, TextureCoordinate | None, TextureCoordinate | None]
    material_name: str | None = None


@dataclass(slots=True)
class Mesh:
    """Malha 3D processada e pronta para renderização."""

    triangles: list[Triangle] = field(default_factory=list)
    # Centroide calculado antes da translação (para referência/debug)
    centroid: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 0.0))
    # Fator de escala aplicado para normalizar o objeto na tela
    scale_factor: float = 1.0
    # True quando normais foram calculadas (não estavam no arquivo .obj)
    normals_computed: bool = False


# ── Funções matemáticas internas ──────────────────────────────────────────────


def _sub(a: Vector3, b: Vector3) -> Vector3:
    return Vector3(a.x - b.x, a.y - b.y, a.z - b.z)


def _cross(a: Vector3, b: Vector3) -> Vector3:
    return Vector3(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    )


def _length(v: Vector3) -> float:
    return math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)


def _normalize(v: Vector3) -> Vector3:
    mag = _length(v)
    if mag == 0.0:
        return Vector3(0.0, 0.0, 1.0)  # fallback para vetores degenerados
    return Vector3(v.x / mag, v.y / mag, v.z / mag)


def face_normal(v0: Vector3, v1: Vector3, v2: Vector3) -> Vector3:
    """Calcula a normal de uma face via produto vetorial: n = (V1-V0) × (V2-V0), normalizado."""
    return _normalize(_cross(_sub(v1, v0), _sub(v2, v0)))


# ── Triangulação por fan ──────────────────────────────────────────────────────


def _fan_indices(n: int) -> list[tuple[int, int, int]]:
    """Fan triangulation: polígono com n vértices → n-2 triângulos.

    Para (v0, v1, ..., vN-1) gera: (0,1,2), (0,2,3), ..., (0,N-2,N-1)
    """
    return [(0, i, i + 1) for i in range(1, n - 1)]


# ── Construtor principal ──────────────────────────────────────────────────────


def build_mesh(model: ObjModel) -> Mesh:
    """Constrói uma Mesh pronta para renderização a partir de um ObjModel.

    Etapas executadas:
      1. Triangulação fan de todas as faces (polígonos com 4+ vértices são
         decompostos automaticamente em triângulos).
      2. Cálculo do centroide e translação para a origem.
      3. Normalização da escala para que o objeto caiba na tela
         (distância máxima dos vértices à origem = 1).
      4. Se o arquivo não contiver normais, calcula normais por face via
         produto vetorial: n = (V1-V0) × (V2-V0), normalizado.
    """
    mesh = Mesh()

    if not model.vertices:
        return mesh

    # ── Etapa 2: centroide e translação para a origem ─────────────────────────
    n = len(model.vertices)
    cx = sum(v.x for v in model.vertices) / n
    cy = sum(v.y for v in model.vertices) / n
    cz = sum(v.z for v in model.vertices) / n
    mesh.centroid = Vector3(cx, cy, cz)

    centered = [Vector3(v.x - cx, v.y - cy, v.z - cz) for v in model.vertices]

    # ── Etapa 3: normalização da escala ───────────────────────────────────────
    max_dist = max((_length(v) for v in centered), default=1.0)
    scale = max_dist if max_dist > 0.0 else 1.0
    mesh.scale_factor = scale

    scaled = [Vector3(v.x / scale, v.y / scale, v.z / scale) for v in centered]

    # ── Etapas 1 e 4: triangulação + normais ─────────────────────────────────
    has_file_normals = len(model.normals) > 0

    for face in model.faces:
        verts = face.vertices
        if len(verts) < 3:
            continue

        for i, j, k in _fan_indices(len(verts)):
            fv0, fv1, fv2 = verts[i], verts[j], verts[k]

            p0 = scaled[fv0.position_index]
            p1 = scaled[fv1.position_index]
            p2 = scaled[fv2.position_index]

            # Normais: usa as do arquivo quando disponíveis; caso contrário calcula por face
            if has_file_normals:
                fn = face_normal(p0, p1, p2)  # fallback para vértices sem normal
                n0 = model.normals[fv0.normal_index] if fv0.normal_index is not None else fn
                n1 = model.normals[fv1.normal_index] if fv1.normal_index is not None else fn
                n2 = model.normals[fv2.normal_index] if fv2.normal_index is not None else fn
            else:
                fn = face_normal(p0, p1, p2)
                n0 = n1 = n2 = fn
                mesh.normals_computed = True

            t0 = model.texcoords[fv0.texcoord_index] if fv0.texcoord_index is not None else None
            t1 = model.texcoords[fv1.texcoord_index] if fv1.texcoord_index is not None else None
            t2 = model.texcoords[fv2.texcoord_index] if fv2.texcoord_index is not None else None

            mesh.triangles.append(
                Triangle(
                    positions=(p0, p1, p2),
                    normals=(n0, n1, n2),
                    texcoords=(t0, t1, t2),
                    material_name=face.material_name,
                )
            )

    return mesh
