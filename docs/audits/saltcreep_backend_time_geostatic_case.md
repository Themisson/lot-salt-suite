# Auditoria — caso controlado com tempo, geostatica e campo termico neutro

**Data:** 2026-06-03  
**Fase:** 7.4  
**Status:** `TIME_THERMAL_GEOSTATIC_CONTROLLED_TEST_READY`

## Objetivo

Auditar e exercitar, de forma isolada, os componentes minimos do backend
`external/saltcreep` que um futuro `SaltCreepSaltcreepAdapter` real precisara
orquestrar: tempo, campo termico, tensao geostatica simplificada e pressao de
parede constante.

Esta fase nao altera `external/saltcreep/`, nao altera
`SaltCreepSaltcreepAdapter`, nao liga o backend real ao `lot-sim` e nao acopla
LOT/PKN/APB ao sal.

## Tempo

O backend representa tempo no parser standalone por `TimeParams`, com:

- `total_s`;
- `dt_s`;
- `dt_min_s`;
- `dt_max_s`;
- agenda opcional `std::vector<TimeSegment>` com pares `(until_s, dt_s)`.

No nivel C++ direto, `TimeIntegrator` oferece:

- `advance(double dt_s)`;
- `run(double dt_s, double t_end_s, ...)`;
- `run_schedule(const std::vector<TimeSegment>&, double t_end_s, ...)`.

O teste controlado usa `advance()` para evitar gerar arquivos versionados e para
provar apenas a execucao de passos temporais em memoria.

## Campo termico

O backend define a interface `ThermalField`, com:

```text
temperature_at(x, t)
alpha_thermal()
T_reference()
```

`ProfileField::make_constant()` fornece um campo uniforme. A Fase 7.4 usa
`alpha_thermal = 0` e `T_reference_K = T_K`, tornando o campo termico neutro:
o integrador consulta temperatura em cada passo, mas nao gera deformacao termica.

Campos de conducao 1D/2D existem no backend, mas nao foram usados nesta fase
porque o objetivo era testar a superficie minima necessaria ao adapter, sem
acoplamento termico real.

## Geostatica

`TimeIntegrator` recebe um vetor `std::vector<Stress>` por ponto de Gauss,
documentado como:

```text
sigma_geo_gp = {sigma_rr, sigma_tt, sigma_zz, sigma_rz}
```

O backend monta a forca interna geostatica por:

```text
Assembler::assemble_geostatic_force(mesh, element, sigma_geo_gp)
```

e usa a perturbacao inicial:

```text
f_net = f_external - f_geo
```

O teste controlado usa dois cenarios:

1. geostatica neutra (`sigma_geo = 0`) para provar que o integrador temporal
   preserva a resposta elastica estatica quando nao ha fluencia nem termo
   termico;
2. geostatica compressiva uniforme simplificada (`sigma_v < 0`, `sigma_h =
   k0 sigma_v`) com parede externa fixa para confirmar fechamento radial
   assinado (`u_r < 0`) e fechamento positivo.

## Pressao de parede

O backend expoe `WallPressureField` e `ConstantWallPressureField`.

O teste usa `ConstantWallPressureField` tanto na carga inicial quanto no
ponteiro opcional entregue ao `TimeIntegrator`. Como a pressao e constante no
tempo, `advance()` nao adiciona incremento de pressao, e o estado final do caso
elastico neutro deve permanecer igual ao estado inicial.

## Componentes usados no teste C++ isolado

- `build_mesh_L3`
- `AxisymL3`
- `ElasticIsotropic`
- `ProfileField`
- `ConstantWallPressureField`
- `Assembler::assemble_K`
- `Assembler::assemble_boundary_pressure`
- `Assembler::assemble_geostatic_force` via `TimeIntegrator`
- `ElasticSolver`
- `TimeIntegrator::advance`
- `TimeIntegrator::wall_displacement_m`
- `TimeIntegrator::wall_closure_pct`

## Componentes ainda nao prontos para adapter real

A API direta e suficiente para um caso controlado, mas ainda nao e uma interface
de producao para `SaltCreepQuery`. Permanecem pendentes:

- configuracao explicita de geometria/malha/material no adapter;
- mapeamento fisico de pressao LOT/APB para pressoes internas, externas e
  geostaticas do backend;
- politica de estado temporal persistente entre queries;
- selecao entre integrador explicito e implicito;
- definicao de campo termico real, inclusive unidades e referencia;
- saidas diagnosticas que o contrato moderno deve ou nao expor;
- validacao com fluencia real e, separadamente, dano.

## Classificacao

`TIME_THERMAL_GEOSTATIC_CONTROLLED_TEST_READY`

Ha API C++ direta suficiente para teste controlado com tempo, campo termico
neutro, geostatica simplificada e pressao de parede constante. Essa conclusao
nao declara validacao fisica ampla e nao torna o adapter real disponivel.

## Escopo preservado

- `external/saltcreep/` permaneceu somente leitura.
- `SaltCreepSaltcreepAdapter::is_available()` permanece `false`.
- LOT/PKN, APB, `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter` e
  `CaseParser` nao foram alterados.
- Nenhum script Python novo foi criado.
