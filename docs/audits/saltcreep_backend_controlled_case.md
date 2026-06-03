# Auditoria — caso controlado do backend saltcreep

**Data:** 2026-06-03  
**Fase:** 7.3  
**Status:** `BACKEND_DIRECT_CORE_API_READY_FOR_ELASTIC_CONTROLLED_CASE`

## Objetivo

Provar, de forma isolada e sem acoplamento LOT/PKN, que o nucleo C++ de
`external/saltcreep` pode ser instanciado diretamente em um caso sintetico
minimo e comparado contra uma solucao analitica conhecida.

Esta fase nao altera `external/saltcreep/`, nao altera o adapter
`SaltCreepSaltcreepAdapter`, nao liga o backend real ao `lot-sim` e nao muda
modelos fisicos LOT/APB/sal.

## Caminhos de execucao existentes no saltcreep

O `external/saltcreep/CMakeLists.txt` define o executavel standalone
`saltcreep`, que usa `main/main.cpp` e as fontes do backend para ler casos YAML
em `external/saltcreep/cases/` e gravar resultados em
`external/saltcreep/results/`.

O mesmo projeto tambem compila uma suite Catch2 propria com objetos do backend.
Essa suite demonstra que as classes numericas podem ser instanciadas em C++ sem
passar obrigatoriamente pelo executavel ou pelo parser YAML standalone.

## Caminho de deslocamento de parede

As auditorias da Fase 7.2 identificaram que os integradores do saltcreep expõem
o deslocamento radial da parede como `u_r` assinado:

```text
wall_displacement_m() = state_.u_total[0]
wall_closure_pct()   = -u_r / Ri * 100
```

`TimeOutput.cpp` tambem grava `wall_disp_m` como valor assinado e `u_wall_m`
como magnitude positiva de fechamento.

## API C++ usada no caso controlado

O teste `tests/cpp/test_saltcreep_backend_controlled_case.cpp` usa somente uma
rota elastica minima do backend:

- `build_mesh_L3`
- `AxisymL3`
- `ElasticIsotropic`
- `ConstantWallPressureField`
- `Assembler::assemble_K`
- `Assembler::assemble_boundary_pressure`
- `ElasticSolver`

O target CMake separado `saltcreep_backend_controlled_tests` compila apenas as
fontes necessarias do backend e usa um diretorio proxy de Eigen no build dir,
copiado de `include/Eigen/`, para manter a precedencia do Eigen oficial do
`lot-salt-suite`.

## Caso analitico

O caso e um cilindro elastico espesso axisimetrico em deformacao plana, com:

Hipoteses do teste:

- elasticidade linear;
- pequenas deformacoes;
- sem fluencia;
- sem dano;
- sem acoplamento termico;
- geometria sintetica;
- sem acoplamento LOT/PKN/APB.

```text
Ri = 0.1556 m
Re = 10 Ri
E  = 25 GPa
nu = 0.30
p  = 10 MPa
```

A solucao de Lame usada no teste e:

```text
sigma_r = A - B/r^2
sigma_t = A + B/r^2
u_r     = (1 + nu) / E * ((1 - 2 nu) A r + B/r)
```

com:

```text
A = (p_inner Ri^2 - p_outer Re^2) / (Re^2 - Ri^2)
B = (p_inner - p_outer) Ri^2 Re^2 / (Re^2 - Ri^2)
```

## Resultado tecnico

O teste controlado cobre duas cargas:

| Carga | Resultado esperado | Regra de fechamento |
|-------|--------------------|---------------------|
| `p_inner > 0`, `p_outer = 0` | `u_r > 0`, parede expande para fora | `max(0, -u_r) = 0` |
| `p_inner = 0`, `p_outer > 0` | `u_r < 0`, parede fecha para dentro | `max(0, -u_r) > 0` |

Ambos os casos sao comparados com a solucao de Lame no raio interno com erro
relativo menor que `1e-6`.

## Conclusao

Existe uma rota C++ direta e testavel para um caso elastico controlado do
backend. Portanto, o backend nao e limitado a execucao YAML-only para testes
unitarios ou de integracao controlada.

Essa conclusao nao torna o adapter real pronto. Para um adapter de producao
ainda e necessario definir explicitamente geometria, malha, material, campo
termico, tensao geostatica, historico temporal, pressao de parede e integrador.

O achado de sinais tambem e importante: no backend, uma pressao interna positiva
aplicada como `WallPressureField` produz deslocamento para fora. Fechamento
compressivo positivo do contrato LOT-sal deve ser mapeado para a combinacao
fisica correta de pressoes internas, externas e geostaticas, nao simplesmente
passado como escalar positivo esperando fechamento.

## Escopo preservado

- `external/saltcreep/` permaneceu somente leitura.
- `SaltCreepSaltcreepAdapter::is_available()` permanece `false`.
- LOT/PKN, APB, `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter` e
  `CaseParser` nao foram alterados.
- Nenhum script Python novo foi criado.
