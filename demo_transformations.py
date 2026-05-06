#!/usr/bin/env python
"""Script de demonstração das transformações 3D em tempo real."""

from __future__ import annotations

import math
from pathlib import Path

from visualizador_3d_poligonos.renderer import load_model, Renderer


def main() -> None:
    """Carrega um cubo e abre o visualizador com transformações 3D ativas."""
    
    # Procurar pelo arquivo de exemplo
    examples_dir = Path(__file__).parent / "examples"
    cube_path = examples_dir / "cube.obj"
    
    if not cube_path.exists():
        # Se não estiver em examples, procurar em outros locais
        workspace = Path(__file__).parent
        cube_path = workspace / "cube.obj"
    
    if not cube_path.exists():
        print(f"❌ Arquivo cube.obj não encontrado em {examples_dir}")
        print("\nCrie um arquivo .obj para visualizar, ou use:")
        print("  python -m visualizador_3d_poligonos.renderer seu_arquivo.obj")
        return
    
    # Carregar modelo
    print(f"📁 Carregando: {cube_path}")
    mesh, materials = load_model(cube_path)
    
    # Criar renderer
    renderer = Renderer(mesh, materials, width=1000, height=900)
    
    # Aplicar algumas transformações iniciais para demonstração
    renderer.transform_state.apply_rotation("x", math.radians(20))
    renderer.transform_state.apply_rotation("y", math.radians(30))
    
    print("✅ Visualizador iniciado com suporte a transformações 3D!")
    print("\n📋 Controles:")
    print("  • S + ↑/↓: Escalar")
    print("  • R + X/Y/Z: Rotacionar")
    print("  • T + ↑/↓/←/→: Transladar")
    print("  • Mouse: Arrastar para rotacionar continuamente")
    print("  • Esc: Resetar transformações")
    print("  • P: Alternar projeção")
    print("  • W: Wireframe")
    print()
    
    renderer.run()


if __name__ == "__main__":
    main()
