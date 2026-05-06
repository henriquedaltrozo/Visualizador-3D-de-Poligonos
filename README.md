# Visualizador-3D-de-Poligonos

Implementação da ETAPA 1 do trabalho: parser de arquivos `.obj` e `.mtl` em Python.

## Como executar

Para inspecionar um modelo e ver o resumo do que foi carregado:

```bash
python -m visualizador_3d_poligonos.obj_parser caminho/do/modelo.obj
```

Para renderizar o modelo em uma janela interativa com iluminação, modos de exibição e projeção:

```bash
python -m visualizador_3d_poligonos.renderer caminho/do/modelo.obj
```

Teclas suportadas:

- `P`: alterna entre projeção isométrica e perspectiva
- `W`: alterna o modo wireframe
- `S`: alterna o modo sólido
- `Esc`: fecha o visualizador

## O que o parser suporta

- Vértices (`v`), normais (`vn`) e coordenadas UV (`vt`)
- Faces nos formatos `f v`, `f v//vn` e `f v/vt/vn`
- Índices negativos
- Comentários e grupos (`g`)
- `mtllib` e `usemtl`
- Leitura de materiais `.mtl`
- Contagem de `V`, `E`, `F` e verificação da fórmula de Euler

## Estrutura do código

- `visualizador_3d_poligonos/obj_parser.py`: parser OBJ/MTL e estruturas de dados
- `tests/test_obj_parser.py`: testes automatizados do parser