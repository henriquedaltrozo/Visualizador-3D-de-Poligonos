from __future__ import annotations

import argparse
import math
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path

from .mesh_builder import Mesh, build_mesh, face_normal
from .obj_parser import Material, ObjParser, Vector3
from .transformation import TransformationState


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
        self.background = "#e0e0e0"
        self.camera_distance = 2.5
        self._window: tk.Tk | None = None
        self._canvas: tk.Canvas | None = None

        # Transformações 3D
        self.transform_state = TransformationState()

        # Estado de modo de transformação ativa (None, 'scale', 'rotate', 'translate')
        self.active_transform_mode: str | None = None

        # Para rotação contínua com mouse
        self.mouse_last_x = 0
        self.mouse_last_y = 0
        self.dragging = False

    def _transform(self, vertex: Vector3) -> Vector3:
        # Aplicar transformações 3D (model matrix)
        model_matrix = self.transform_state.get_model_matrix()
        transformed = model_matrix.transform_point(vertex)
        
        # Aplicar projeção isométrica
        transformed = _rotate_x(transformed, self.ISO_X)
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
        canvas.create_text(12, 12, anchor="nw", fill="#000000", text=status, font=("Arial", 12, "bold"))
        
        help_lines = [
            "P: Persp/Isométrica  W: Wireframe  S: Sólido",
            "S: Escala (+/- setas)  R: Rotação (X/Y/Z+setas)  T: Translação (setas)",
            "Mouse: Arrastar para rotacionar  Esc: Reset",
        ]
        y_offset = 30
        for line in help_lines:
            canvas.create_text(12, y_offset, anchor="nw", fill="#000000", text=line, font=("Arial", 9))
            y_offset += 18

        # Mostrar modo ativo
        if self.active_transform_mode:
            mode_text = f"Modo: {self.active_transform_mode.upper()}"
            canvas.create_text(self.width - 12, 12, anchor="ne", fill="#000000", text=mode_text, font=("Arial", 10, "bold"))

    def _on_key(self, event: tk.Event) -> None:
        key = event.keysym.lower()
        
        # Modos de transformação
        if key == "s" and self.active_transform_mode != "scale":
            self.active_transform_mode = "scale"
            return
        elif key == "r" and self.active_transform_mode != "rotate":
            self.active_transform_mode = "rotate"
            return
        elif key == "t" and self.active_transform_mode != "translate":
            self.active_transform_mode = "translate"
            return
        
        # Sair do modo de transformação
        if key == "escape":
            self.transform_state.reset()
            self.active_transform_mode = None
            self._render_triangles()
            return
        
        # Transformações baseadas no modo ativo
        if self.active_transform_mode == "scale":
            if key == "up":
                self.transform_state.apply_scale(0.05)
                self._render_triangles()
            elif key == "down":
                self.transform_state.apply_scale(-0.05)
                self._render_triangles()
            elif key in ("p", "w"):
                # Permitir alternar projeção e wireframe enquanto em modo scale
                self._handle_projection_wireframe(key)
                return
            else:
                self.active_transform_mode = None
            return
        
        if self.active_transform_mode == "rotate":
            if key == "x":
                self.transform_state.apply_rotation("x", math.radians(5))
                self._render_triangles()
            elif key == "y":
                self.transform_state.apply_rotation("y", math.radians(5))
                self._render_triangles()
            elif key == "z":
                self.transform_state.apply_rotation("z", math.radians(5))
                self._render_triangles()
            elif key in ("p", "w"):
                self._handle_projection_wireframe(key)
                return
            else:
                self.active_transform_mode = None
            return
        
        if self.active_transform_mode == "translate":
            if key == "up":
                self.transform_state.apply_translation(0.0, 0.05, 0.0)
                self._render_triangles()
            elif key == "down":
                self.transform_state.apply_translation(0.0, -0.05, 0.0)
                self._render_triangles()
            elif key == "left":
                self.transform_state.apply_translation(-0.05, 0.0, 0.0)
                self._render_triangles()
            elif key == "right":
                self.transform_state.apply_translation(0.05, 0.0, 0.0)
                self._render_triangles()
            elif key in ("p", "w"):
                self._handle_projection_wireframe(key)
                return
            else:
                self.active_transform_mode = None
            return
        
        # Controles globais (sem modo ativo)
        if key == "p":
            self.projection_mode = "perspective" if self.projection_mode == "isometric" else "isometric"
            self._render_triangles()
        elif key == "w":
            self.show_wireframe = not self.show_wireframe
            self._render_triangles()
        elif key == "shift+w":
            self.show_solid = not self.show_solid
            self._render_triangles()

    def _handle_projection_wireframe(self, key: str) -> None:
        """Trata atalhos de projeção e wireframe enquanto em modo de transformação."""
        if key == "p":
            self.projection_mode = "perspective" if self.projection_mode == "isometric" else "isometric"
            self._render_triangles()
        elif key == "w":
            self.show_wireframe = not self.show_wireframe
            self._render_triangles()

    def _on_mouse_press(self, event: tk.Event) -> None:
        """Inicia rotação contínua ao pressionar botão do mouse."""
        self.dragging = True
        self.mouse_last_x = event.x
        self.mouse_last_y = event.y

    def _on_mouse_release(self, event: tk.Event) -> None:
        """Para rotação contínua ao liberar botão do mouse."""
        self.dragging = False

    def _on_mouse_motion(self, event: tk.Event) -> None:
        """Rotação contínua ao arrastar mouse."""
        if not self.dragging:
            return
        
        dx = event.x - self.mouse_last_x
        dy = event.y - self.mouse_last_y
        
        # Rotação proporcional ao movimento do mouse
        self.transform_state.apply_rotation("y", math.radians(dx * 0.5))
        self.transform_state.apply_rotation("x", math.radians(dy * 0.5))
        
        self.mouse_last_x = event.x
        self.mouse_last_y = event.y
        
        self._render_triangles()

    def run(self) -> None:
        self._window = tk.Tk()
        self._window.title("Visualizador 3D de Polígonos")
        self._window.geometry(f"{self.width}x{self.height}")
        self._canvas = tk.Canvas(self._window, width=self.width, height=self.height, bg=self.background)
        self._canvas.pack(fill="both", expand=True)
        
        # Registrar eventos de teclado
        self._window.bind("<Key>", self._on_key)
        
        # Registrar eventos de mouse para rotação contínua
        self._canvas.bind("<Button-1>", self._on_mouse_press)
        self._canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        self._canvas.bind("<Motion>", self._on_mouse_motion)
        
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
