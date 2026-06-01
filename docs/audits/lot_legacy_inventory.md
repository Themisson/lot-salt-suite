# Inventario LOT nos legados

## Escopo

Auditoria somente leitura dos caminhos LOT nos legados, com foco em arquivos
relacionados a fratura, leakoff, injecao e resultados PKN. Nenhum arquivo em
`legance/`, `legacy/` ou `external/saltcreep/` foi alterado.

## Principais regioes

| Area | Papel observado |
|------|-----------------|
| `legance/LOT_Tese/include/apb_code/Fluids.h` | Define propriedades de fluido e `LeakoffProps`, incluindo tipo de fratura. |
| `legance/LOT_Tese/src/apb_code/Fluids.cpp` | Converte viscosidade e registra o tipo de fratura por string. |
| `legance/LOT_Tese/include/apb_code/APB1da.h` | Declara controle LOT, vazao, tempo sem injecao e funcoes de fratura. |
| `legance/LOT_Tese/src/apb_code/APB1da.cpp` | Contem injecao LOT, deteccao de pressao acima do limite e modelos de fratura/leakoff. |
| `legance/LOT_Tese/main/` | Casos executaveis hard-coded para pocos e geometrias. |
| `legance/LOT_Tese/Teste/` | Resultados, figuras e dados comparativos de LOT. |
| `legance/LOT_APB_v5/` | Caminho moderno JSON/APB/sal, mas sem ser o eixo prioritario para PKN LOT. |

## Strings de geometria

`Fluids::idTypeFracture()` mapeia:

| String | ID | Status para migracao |
|--------|----|----------------------|
| `circular` | 0 | Catalogado, nao prioritario. |
| `elliptical` | 1 | Catalogado, nao prioritario. |
| `pkn` | 2 | Prioridade da primeira migracao LOT. |
| `penny-shaped` | 3 | Catalogado, nao prioritario. |

## Casos PKN observados

| Arquivo | Observacao |
|---------|------------|
| `legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp` | Caso PKN explicito para 8-BUZ-67D, com injecao LOT em minutos. |
| `legance/LOT_Tese/9-BUZ-39DA-RJS-VISCO-2.cpp` | Caso PKN para 9-BUZ-39DA, gravando `results/9-BUZ-39DA-RJS_PKN2.dat`. |
| `legance/LOT_Tese/Teste/8-BUZ-67D-PKN*.dat` | Familia de resultados e comparacoes PKN. |
| `legance/LOT_Tese/Teste/Dados do artigo/` | Dados derivados usados em material de artigo. |

## Sinais de inconsistencias

- Alguns arquivos nomeados como circular, eliptico ou penny-shaped apresentam
  configuracoes aparentes copiadas de PKN em trechos auditados. Isso deve ser
  tratado como risco de inventario, nao como verdade fisica.
- As conversoes de vazao no legado incluem fator `M_PI / 2`; uma funcao de
  conversao para `bb/min -> m3/h` contem `M_PI / 22`, que parece erro de digito.
- A saida `Momento da quebra` existe no fluxo de escrita, mas a semantica exata
  deve ser preservada por testes antes de ser usada como benchmark.

## Conclusao

O caminho PKN em `legance/LOT_Tese` e o candidato correto para a primeira
migracao LOT. `LOT_APB_v5` continua importante para APB/JSON/sal, mas nao deve
ser usado como fonte principal da formulacao PKN.
