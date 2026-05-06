# Visualizador-3D-de-Poligonos

Implementação de um visualizador 3D interativo com suporte a transformações em tempo real, iluminação e múltiplos modos de exibição.

## Como executar

### Opção 1: Script de demonstração (recomendado)
```bash
python demo_transformations.py
```

### Opção 2: Com seu próprio arquivo OBJ
```bash
python -m visualizador_3d_poligonos.renderer seu_arquivo.obj
```

### Opção 3: Inspecionar um modelo OBJ
Para ver estatísticas do modelo sem visualizar:
```bash
python -m visualizador_3d_poligonos.obj_parser caminho/do/modelo.obj
```

Para renderizar o modelo em uma janela interativa com iluminação, modos de exibição e projeção:

```bash
python -m visualizador_3d_poligonos.renderer caminho/do/modelo.obj
```

## Controles Interativos

### Projeção e Visualização
- `P`: alterna entre projeção isométrica e perspectiva
- `W`: alterna o modo wireframe
- `S`: alterna o modo sólido

### Transformações 3D (via matriz 4x4)

#### Escala
- `S`: ativa modo escala
- `↑` / `↓`: aumenta/diminui tamanho (incremental)

#### Rotação
- `R`: ativa modo rotação
- `X`: rotaciona em torno do eixo X (5° incremental)
- `Y`: rotaciona em torno do eixo Y (5° incremental)
- `Z`: rotaciona em torno do eixo Z (5° incremental)

#### Translação
- `T`: ativa modo translação
- `↑` / `↓`: move verticalmente
- `←` / `→`: move horizontalmente

#### Mouse
- **Clique e arraste**: rotação contínua em tempo real (ativa modo rotação dinâmica)

#### Reset
- `Esc`: reseta todas as transformações para o estado inicial

**Nota**: Enquanto em um modo de transformação, pressione outra tecla de modo ou `Esc` para sair.

## O que o parser suporta

- Vértices (`v`), normais (`vn`) e coordenadas UV (`vt`)
- Faces nos formatos `f v`, `f v//vn` e `f v/vt/vn`
- Índices negativos
- Comentários e grupos (`g`)
- `mtllib` e `usemtl`
- Leitura de materiais `.mtl`
- Contagem de `V`, `E`, `F` e verificação da fórmula de Euler

## Transformações 3D (Matrizes 4x4)

O renderer implementa transformações 3D completas usando matrizes 4x4 homogêneas:

- **Escala**: modifica uniformemente o tamanho do objeto
- **Rotação**: rotações independentes em X, Y e Z (com acumulação incremental)
- **Translação**: movimento no espaço 3D
- **Composição**: todas as transformações são combinadas via `Model Matrix = T × R × S`

A transformação é aplicada no seguinte pipeline:
1. Aplicação da matriz de modelo aos vértices originais
2. Projeção isométrica ou perspectiva
3. Renderização com backface culling e iluminação

Exemplo de uso (em código):
```python
from visualizador_3d_poligonos.transformation import TransformationState
from visualizador_3d_poligonos.renderer import Renderer, load_model

mesh, materials = load_model("cube.obj")
renderer = Renderer(mesh, materials)

# Aplicar transformações
renderer.transform_state.apply_scale(1.5)
renderer.transform_state.apply_rotation("y", math.radians(45))
renderer.transform_state.apply_translation(0.5, 0.0, 0.0)

# Resetar se necessário
renderer.transform_state.reset()

renderer.run()
```

## Estrutura do código

- `visualizador_3d_poligonos/obj_parser.py`: parser OBJ/MTL e estruturas de dados
- `visualizador_3d_poligonos/mesh_builder.py`: construção de malhas 3D e triangulação
- `visualizador_3d_poligonos/renderer.py`: renderizador com iluminação e projeção
- `visualizador_3d_poligonos/transformation.py`: **NOVO** — matrizes 4x4 e transformações 3D
- `tests/`: suite de testes automatizados para todos os módulos

## Requisitos

- Python 3.10+
- Tkinter (geralmente incluído com Python)
- Nenhuma dependência externa necessária

## Testes

Execute todos os testes com:
```bash
python -m unittest discover tests -v
```

Status: ✅ **39/39 testes passando**
- 8 testes de matrizes 4x4
- 6 testes de estado de transformação
- 25 testes de parser, mesh builder e renderer