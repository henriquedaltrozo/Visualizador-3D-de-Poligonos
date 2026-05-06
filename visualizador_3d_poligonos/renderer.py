from __future__ import annotations

import argparse
import math
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path

from .mesh_builder import Mesh, build_mesh, face_normal
from .obj_parser import Material, ObjParser, Vector3


def _dot(a: Vector3, b: Vector3) -> float:
    return a.x * b.x + a.y * b.y + a.z * b.z


def _length(v: Vector3) -> float:
    return math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)


def _normalize(v: Vector3) -> Vector3:
    length = _length(v)
    if length == 0.0:
        return Vector3(0.0, 0.0, 1.0)
    return Vector3(v.x / length, v.y / length, v.z / length)


def _rotate_x(v: Vector3, angle: float) -> Vector3:
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return Vector3(v.x, v.y * cos_a - v.z * sin_a, v.y * sin_a + v.z * cos_a)


def _rotate_y(v: Vector3, angle: float) -> Vector3:
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return Vector3(v.x * cos_a + v.z * sin_a, v.y, -v.x * sin_a + v.z * cos_a)


@dataclass(slots=True, frozen=True)
class ProjectedVertex:
    x: float
    y: float
    depth: float


class Renderer:
    """Renderizador de malhas 3D com projeção, backface culling e iluminação."""

    ISO_X = math.radians(35.26438968)
    ISO_Y = math.radians(45.0)
    LIGHT_DIRECTION = _normalize(Vector3(-0.5, -0.2, 1.0))

    def __init__(self, mesh: Mesh, materials: dict[str, Material], width: int = 900, height: int = 900) -> None:
        self.mesh = mesh
        self.materials = materials
        self.width = width
        self.height = height
        self.projection_mode = "isometric"
        self.show_solid = True
        self.show_wireframe = False
        self.background = "#111111"
        self.camera_distance = 2.5
        self._window: tk.Tk | None = None
        self._canvas: tk.Canvas | None = None

    def _transform(self, vertex: Vector3) -> Vector3:
        transformed = _rotate_x(vertex, self.ISO_X)
        transformed = _rotate_y(transformed, self.ISO_Y)
        return transformed

    def _project(self, vertex: Vector3) -> ProjectedVertex:
        view = self._transform(vertex)
        if self.projection_mode == "perspective":
            z = view.z + self.camera_distance
            if z <= 0.01:
                z = 0.01
            scale = self.camera_distance / z
            x = view.x * scale
            y = view.y * scale
            depth = z
        else:
            x = view.x
            y = view.y
            depth = view.z + self.camera_distance
        screen_scale = min(self.width, self.height) * 0.35
        screen_x = self.width * 0.5 + x * screen_scale
        screen_y = self.height * 0.5 - y * screen_scale
        return ProjectedVertex(x=screen_x, y=screen_y, depth=depth)

    def _face_visible(self, triangle: tuple[Vector3, Vector3, Vector3]) -> bool:
        v0 = self._transform(triangle[0])
        v1 = self._transform(triangle[1])
        v2 = self._transform(triangle[2])
        normal = face_normal(v0, v1, v2)
        return normal.z > 0.0

    def _material_color(self, material_name: str | None) -> tuple[int, int, int]:
        material = self.materials.get(material_name) if material_name is not None else None
        if material is None or material.diffuse is None:
            return (192, 192, 192)
        return (
            int(max(0, min(255, material.diffuse.x * 255.0))),
            int(max(0, min(255, material.diffuse.y * 255.0))),
            int(max(0, min(255, material.diffuse.z * 255.0))),
        )

    def _shade_color(self, base_color: tuple[int, int, int], triangle: tuple[Vector3, Vector3, Vector3]) -> str:
        v0 = self._transform(triangle[0])
        v1 = self._transform(triangle[1])
        v2 = self._transform(triangle[2])
        normal = face_normal(v0, v1, v2)
        intensity = max(0.05, _dot(normal, self.LIGHT_DIRECTION))
        intensity = min(intensity, 1.0)
        r = int(base_color[0] * intensity)
        g = int(base_color[1] * intensity)
        b = int(base_color[2] * intensity)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _triangle_depth(self, triangle: tuple[Vector3, Vector3, Vector3]) -> float:
        depths = [self._transform(v).z for v in triangle]
        return sum(depths) / len(depths)

    def _render_triangles(self) -> None:
        canvas = self._canvas
        if canvas is None:
            return
        canvas.delete("all")
        canvas.create_rectangle(0, 0, self.width, self.height, fill=self.background, outline="")

        triangles = list(self.mesh.triangles)
        triangles.sort(key=lambda tri: self._triangle_depth(tri.positions), reverse=True)

        for triangle in triangles:
            if not self._face_visible(triangle.positions):
                continue
            points = [self._project(vertex) for vertex in triangle.positions]
            coords = [coord for point in points for coord in (point.x, point.y)]
            fill_color = "" if not self.show_solid else self._shade_color(self._material_color(triangle.material_name), triangle.positions)
            outline_color = "#ffffff" if self.show_wireframe else ""
            width = 1 if self.show_wireframe else 0
            canvas.create_polygon(*coords, fill=fill_color, outline=outline_color, width=width, joinstyle="round")

        self._draw_text()

    def _draw_text(self) -> None:
        canvas = self._canvas
        if canvas is None:
            return
        status = f"Projeção: {self.projection_mode.title()} | Sólido: {'ON' if self.show_solid else 'OFF'} | Wireframe: {'ON' if self.show_wireframe else 'OFF'}"
        canvas.create_text(12, 12, anchor="nw", fill="#ffffff", text=status, font=("Arial", 12, "bold"))
        canvas.create_text(12, 30, anchor="nw", fill="#dddddd", text="P: Persp/Isométrica  W: Wireframe  S: Sólido", font=("Arial", 10))

    def _on_key(self, event: tk.Event) -> None:
        key = event.keysym.lower()
        if key == "p":
            self.projection_mode = "perspective" if self.projection_mode == "isometric" else "isometric"
        elif key == "w":
            self.show_wireframe = not self.show_wireframe
        elif key == "s":
            self.show_solid = not self.show_solid
        elif key == "escape":
            self._window.destroy()
            return
        self._render_triangles()

    def run(self) -> None:
        self._window = tk.Tk()
        self._window.title("Visualizador 3D de Polígonos")
        self._window.geometry(f"{self.width}x{self.height}")
        self._canvas = tk.Canvas(self._window, width=self.width, height=self.height, bg=self.background)
        self._canvas.pack(fill="both", expand=True)
        self._window.bind("<Key>", self._on_key)
        self._render_triangles()
        self._window.mainloop()


def load_model(path: str | Path) -> tuple[Mesh, dict[str, Material]]:
    obj_path = Path(path)
    parser = ObjParser()
    model = parser.parse_file(obj_path)
    mesh = build_mesh(model)
    return mesh, model.materials


def main() -> None:
    parser = argparse.ArgumentParser(description="Renderizador 3D com iluminação e modos de exibição.")
    parser.add_argument("obj_path", help="Caminho para o arquivo OBJ")
    args = parser.parse_args()
    mesh, materials = load_model(args.obj_path)
    renderer = Renderer(mesh, materials)
    renderer.run()


if __name__ == "__main__":
    main()
