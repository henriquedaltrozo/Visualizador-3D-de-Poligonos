# Visualizador 3D de Polígonos

Visualizador 3D interativo em Python com transformações 3D via matrizes 4x4, iluminação, e múltiplos modos de exibição.

## Como Executar

### Visualizar um arquivo OBJ

```bash
python -m visualizador_3d_poligonos.renderer examples/cube.obj
python -m visualizador_3d_poligonos.renderer examples/pyramid.obj
python -m visualizador_3d_poligonos.renderer examples/cylinder.obj
python -m visualizador_3d_poligonos.renderer examples/cone.obj
```

## Controles

| Tecla | Função |
|-------|--------|
| **Mouse** | Arrastar para girar |
| `R + X/Y/Z` | Rotacionar 5° em um eixo |
| `S + ↑/↓` | Aumentar/diminuir tamanho |
| `T + ↑↓←→` | Transladar |
| `W` | Wireframe |
| `P` | Alternar projeção |
| `V` | Validar Euler |
| `Esc` | Resetar transformações |

## Estrutura

```
visualizador_3d_poligonos/
├── obj_parser.py          # Parser OBJ/MTL
├── mesh_builder.py        # Construção de malhas
├── renderer.py            # Renderizador
└── transformation.py      # Matrizes 4x4

examples/
├── cube.obj / cube.mtl
├── pyramid.obj / pyramid.mtl
├── cylinder.obj / cylinder.mtl
└── cone.obj / cone.mtl

tests/
├── test_obj_parser.py
├── test_mesh_builder.py
├── test_renderer.py
└── test_transformation.py
```

## Testes

```bash
python -m unittest discover tests -v
```

Status: ✅ **39/39 testes passando**

## Requisitos

- Python 3.10+
- Tkinter (incluído com Python)
