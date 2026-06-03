# Auditoria — Fronteira de includes do TimeIntegrator

**Status:** `TIMEINTEGRATOR_BLOCKED_BY_INCLUDE_BOUNDARY`
**Fase:** 7.7
**Data:** 2026-06-03

## Objetivo

Avaliar se `solver/TimeIntegrator.hpp` do `external/saltcreep/` pode ser
trazido para o target principal do `lot-salt-suite` sem conflito de headers
homonimos.

## Evidencia observada

O `TimeIntegrator` do saltcreep inclui headers de I/O do proprio backend:

```text
external/saltcreep/include/solver/TimeIntegrator.hpp
  -> "io/CaseParser.hpp"
  -> "io/VtuWriter.hpp"
```

O repositorio principal tambem possui:

```text
include/io/CaseParser.hpp
include/io/ResultWriter.hpp
```

No target principal `lot-sim` e no target `lot_sim_tests`, a ordem atual de
includes e:

```text
include/
external/saltcreep/include/
```

Com essa ordem, um include textual como `"io/CaseParser.hpp"` pode resolver
para `include/io/CaseParser.hpp` quando um header do saltcreep e consumido pelo
target principal. Isso e exatamente a colisao que o proxy de Eigen evitou no
build standalone do `external/saltcreep`: expor somente `Eigen/`, e nao o
diretorio raiz `include/` do `lot-salt-suite`, preserva os includes relativos
do saltcreep.

## Classificacao

`TimeIntegrator` continua viavel em target controlado separado:

```text
saltcreep_backend_time_geostatic_tests
```

Nesse target, o include do saltcreep e isolado e o teste de tempo/geostatica
permanece uma prova util da API direta.

Para o adapter principal, a classificacao desta fase e:

```text
TIMEINTEGRATOR_BLOCKED_BY_INCLUDE_BOUNDARY
```

## Decisao da Fase 7.7

A Fase 7.7 nao altera `external/saltcreep/` e nao traz `TimeIntegrator` para
`SaltCreepSaltcreepAdapter`.

Em vez disso, o adapter passa a persistir a rota minima ja controlada:

- elemento `AxisymL3`;
- material `ElasticIsotropic`;
- malha L3;
- matriz de rigidez;
- vetor geostatico, quando habilitado;
- graus de liberdade fixos.

Cada query ainda monta somente o vetor de pressao de parede correspondente ao
tempo e pressao solicitados. O estado temporal do adapter segue em
`SaltCreepAdapterState`.

## Caminhos futuros seguros

Antes de ligar `TimeIntegrator` ao adapter principal, uma fase dedicada deve
escolher uma das rotas:

1. Criar um wrapper interno no saltcreep com headers que nao exponham
   `io/CaseParser.hpp`.
2. Separar tipos de parametros temporais do parser do saltcreep.
3. Compilar um target intermediario com include boundary controlada e expor ao
   `lot-salt-suite` apenas uma API de adapter limpa.
4. Renomear ou namespacear a superficie de I/O do saltcreep, com testes do
   proprio backend e registro de governanca.

Qualquer uma dessas rotas exige testes dedicados e registro em
`docs/16_saltcreep_governance.md`.
