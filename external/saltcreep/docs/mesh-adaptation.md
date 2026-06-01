# Refinamento adaptativo h

Este documento descreve a Etapa 12: refinamento adaptativo de malha por estimador
Zienkiewicz-Zhu (ZZ). O objetivo é concentrar GDLs nas regiões onde a tensão recuperada indica
erro alto, ou onde o dano já passou de um limiar operacional, preservando a física existente do
solver.

## Visão geral

O fluxo implementado é um pre-refinamento elástico:

1. O caso é montado com a malha inicial do YAML.
2. O solver calcula o estado elástico inicial, incluindo `u`, `sigma_gp` e estados internos nulos.
3. O `ErrorEstimator` recupera tensões suavizadas nos nós (`sigma*`) e calcula o erro elementar em
   norma de energia.
4. Elementos com `eta_rel > mesh.error_threshold` ou `damage_D > mesh.damage_refinement_threshold`
   são marcados.
5. O `MeshRefiner` subdivide elementos Q4 ou T3 marcados, transfere deslocamentos e campos internos
   para a nova malha e repete até `mesh.max_refinement_levels`.
6. A simulação final roda na malha refinada.

Essa escolha mantém os integradores e leis constitutivas intactos. A transferência de estado existe
e é testada; a aplicação atual usa a etapa adaptativa como preparação de malha antes da marcha no
tempo.

## Estimador Zienkiewicz-Zhu

Para cada ponto de Gauss o solver já possui a tensão descontínua `sigma_h`. O estimador:

- acumula nos nós uma média ponderada por função de forma e peso de integração;
- reconstrói a tensão suavizada `sigma*` no ponto de Gauss interpolando as tensões nodais;
- integra o erro em norma de energia:

```text
eta_e^2 = integral_e (sigma_h - sigma*)^T D_elastic^{-1} (sigma_h - sigma*) dOmega
```

O erro relativo por elemento é:

```text
eta_rel_e = eta_e / sqrt(integral_e sigma_h^T D_elastic^{-1} sigma_h dOmega)
```

A marcação usa `eta_rel_e > mesh.error_threshold`. Se `mesh.damage_refinement_threshold >= 0`, o
elemento também é marcado quando qualquer ponto de Gauss do elemento tiver `damage_D` acima do
limiar.

## Refinadores

### Q4 -> 4 Q4

Cada quadrilátero bilinear marcado é subdividido em quatro filhos usando pontos médios das arestas e
um centro. Os pontos médios são compartilhados por chave de aresta, preservando conformidade entre
elementos vizinhos. Para evitar nós pendurados, a implementação fecha a vizinhança: se um Q4 marcado
compartilha aresta com outro Q4, o vizinho também é refinado.

### T3 -> 3 T3

Cada triângulo linear marcado é subdividido em três triângulos conectando o centróide aos vértices.
Esse refinador preserva área e conectividade simples. Ele é adequado para testes e para malhas T3
sem exigência de bisseção por arestas; refinamento T3 totalmente local com fechamento por aresta
pode ser acrescentado depois se a malha não estruturada exigir.

## Transferência de campos

O `MeshRefiner` transfere:

- deslocamento nodal `u`;
- tensões em pontos de Gauss;
- deformação viscosa `eps_v_gp`;
- deformação térmica `eps_th_gp`;
- `InternalState`, incluindo `eps_v_eff`, `eps_v_primary`, `eps_v_secondary`, `damage_D` e `f_hard`.

Campos em pontos de Gauss antigos são recuperados nos nós por média ponderada e interpolados para os
novos pontos. O dano é limitado em `[0, 0.99]` e variáveis acumuladas são mantidas não negativas.

## YAML

```yaml
mesh:
  n_elements_radial: 20
  n_elements_axial: 2
  ratio: 1000
  adaptive: true
  error_threshold: 0.10
  max_refinement_levels: 3
  damage_refinement_threshold: 0.30
```

`damage_refinement_threshold` é opcional. Use valor negativo ou omita o campo para refinar apenas por
erro de tensão.

## Limitações atuais

- A simulação adaptativa é um pre-refinamento baseado no estado elástico inicial.
- A subdivisão conformante é implementada para `axisym_2d_Q4` e `axisym_2d_T3`.
- O estimador funciona com qualquer elemento 2D, incluindo AQ9; se um elemento sem refinador for
  marcado, o solver para com mensagem clara.
- `axisym_1d_L3` não usa `mesh.adaptive`.

## Verificação

Os testes cobrem:

- campo de tensão constante sem marcação espúria;
- salto de tensão próximo a interface;
- marcação por dano;
- conservação de área em Q4 e T3;
- transferência exata de campo linear de deslocamento em Q4;
- limites físicos das variáveis internas transferidas;
- parsing dos campos YAML adaptativos.
