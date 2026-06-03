# 24 — Design do SaltCreepSaltcreepAdapter

**Status:** Adapter conectado ao bridge temporal — Fases 7.2-7.9 | **Ultima atualizacao:** 2026-06-03

## Objetivo

`SaltCreepSaltcreepAdapter` e o primeiro adapter C++ concreto que implementa
`SaltCreepInterface` em preparacao para o backend `external/saltcreep/`.

Nesta fase ele e deliberadamente isolado:

- nao e conectado ao LOT/PKN;
- nao e conectado ao APB;
- nao e chamado por `lot-sim run`;
- linka apenas a rota elastica minima do `external/saltcreep`;
- executa um caso elastico/geostatico controlado em memoria.
- persiste objetos do backend minimo entre queries da mesma instancia.

## Status do backend

O adapter existe, compila, valida queries e executa uma rota real minima do
backend `external/saltcreep`.

```text
SaltCreepSaltcreepAdapter::is_available() = true
```

Esse valor significa que a configuracao e suportada pelo backend minimo
elastico/geostatico: `AxisymL3`, `ElasticIsotropic`, `Assembler`,
`ConstantWallPressureField` e `ElasticSolver`.

Desde a Fase 7.5, o adapter tambem aceita uma configuracao explicita
`SaltCreepAdapterConfig`, inicializa um `SaltCreepAdapterState` local e expoe
`config()` / `state()` para testes e futura integracao. Desde a Fase 7.6,
`evaluate_wall_response()` grava a resposta no estado interno.

## Entrada

O adapter recebe `SaltCreepQuery` em SI:

| Campo | Unidade | Regra |
|-------|---------|-------|
| `time_s` | s | finito e `>= 0` |
| `wall_pressure_Pa` | Pa | finito e `>= 0`, compressao positiva |
| `temperature_K` | K | finito e `> 0` |
| `radial_position_m` | m | finito e `>= 0` |

Valores invalidos lancam `std::invalid_argument`.

## Saida nesta fase

Para query valida, o adapter retorna a resposta calculada pelo backend minimo:

```text
radial_displacement_m = u_wall assinado
radial_closure_m = max(0, -u_wall)
radial_strain = u_wall / inner_radius_m
effective_closure_pressure_Pa = 0
valid = true
```

`effective_closure_pressure_Pa` permanece zero porque a Fase 7.6 nao estima
pressao efetiva a partir do campo elastico. O estado interno registra cada
resposta por `SaltCreepAdapterState::record_response()`.

## Convencao de sinais

A Fase 7.2 preserva `docs/23_lot_salt_sign_convention.md`:

- pressao de parede compressiva e positiva;
- deslocamento radial positivo aponta para fora;
- deslocamento radial negativo aponta para dentro;
- fechamento radial e magnitude positiva:

```text
radial_closure_m = max(0, -radial_displacement_m)
```

O adapter expõe `radial_closure_from_displacement()` para manter essa regra
testada antes do backend real.

## Auditoria de suporte no saltcreep

`docs/audits/saltcreep_radial_displacement_sign_audit.md` confirma que os
caminhos auditados do `external/saltcreep` armazenam o deslocamento radial da
parede como `u_r` assinado, com fechamento para dentro representado por
`u_r < 0`, e calculam fechamento positivo como `-u_r`.

## Caso controlado do backend

A Fase 7.3 adiciona `tests/cpp/test_saltcreep_backend_controlled_case.cpp` e
`docs/audits/saltcreep_backend_controlled_case.md`. O teste compila um target
Catch2 separado, `saltcreep_backend_controlled_tests`, com um subconjunto minimo
das fontes do `external/saltcreep`, sem alterar o backend vendorizado e sem
linkar `lot-sim` ou `lot_sim_tests` ao solver de sal.

O caso usa Lame elastico axisimetrico para provar a rota C++ direta:

- pressao interna positiva aplicada como `WallPressureField` produz
  `u_r > 0`, isto e, deslocamento para fora e fechamento nulo;
- pressao externa/confinante positiva produz `u_r < 0`, isto e, fechamento
  para dentro com `radial_closure_m = max(0, -u_r)`;
- ambos os casos batem a solucao analitica com erro relativo menor que `1e-6`.

Esse resultado mostra que existe uma API C++ direta para um caso elastico
controlado. Ele nao muda o status do adapter: o backend real ainda nao esta
conectado a `SaltCreepSaltcreepAdapter`.

## Caso controlado com tempo, geostatica e termico neutro

A Fase 7.4 adiciona `tests/cpp/test_saltcreep_backend_time_geostatic_case.cpp`
e `docs/audits/saltcreep_backend_time_geostatic_case.md`. O target Catch2
separado `saltcreep_backend_time_geostatic_tests` instancia `TimeIntegrator`
com:

- material elastico `ElasticIsotropic`;
- `ProfileField::make_constant()` com `alpha_thermal = 0`;
- `ConstantWallPressureField`;
- vetor geostatico explicito por ponto de Gauss;
- um ou poucos passos `advance(dt_s)`.

O teste confirma que campos neutros preservam a resposta elastica estatica e
que uma geostatica compressiva simplificada, com parede externa fixa, produz
fechamento assinado (`u_r < 0`) e fechamento positivo (`max(0, -u_r)`).

Classificacao da API: `TIME_THERMAL_GEOSTATIC_CONTROLLED_TEST_READY`.

Esse resultado prova uma superficie C++ controlada mais rica, mas ainda nao
transforma `SaltCreepSaltcreepAdapter` em backend real.

## Configuracao e state machine

A Fase 7.5 adiciona `SaltCreepAdapterConfig` e `SaltCreepAdapterState`.
Detalhes completos estao em
`docs/25_saltcreep_adapter_config_state.md`.

Resumo:

- configuracao em SI para geometria, malha, material, termico, geostatica,
  tempo e pressao inicial de parede;
- validacao de finitude, dimensoes positivas, material valido, temperatura em K
  positiva, tempo coerente e pressao nao negativa;
- tensoes geostaticas permanecem assinadas para futura montagem do vetor do
  backend;
- estado registra inicializacao, tempo atual, ultima pressao, ultimo
  deslocamento, ultimo fechamento e numero de passos.

Essa estrutura prepara a ligacao futura com `TimeIntegrator`, mas nao a executa.

## Backend minimo conectado

A Fase 7.6 conecta o adapter a uma rota elastica minima do backend:

- `build_mesh_L3`;
- `AxisymL3`;
- `ElasticIsotropic`;
- `Assembler::assemble_K`;
- `Assembler::assemble_boundary_pressure`;
- `Assembler::assemble_geostatic_force`, quando a geostatica esta habilitada;
- `ConstantWallPressureField`;
- `ElasticSolver`.

Detalhes completos estao em
`docs/26_saltcreep_adapter_backend_minimum.md`.

`TimeIntegrator` permanece validado em target separado, mas nao e linkado ao
target principal nesta fase por risco de conflito de include com
`io/CaseParser.hpp`.

## Estado temporal persistido

A Fase 7.7 adiciona um cache privado ao `SaltCreepSaltcreepAdapter` para evitar
reconstruir malha, elemento, material, matriz de rigidez, vetor geostatico e
graus fixos a cada query. A primeira chamada valida de
`evaluate_wall_response()` cria esse cache; chamadas seguintes reutilizam a
mesma superficie minima e montam apenas o vetor de pressao de parede da query.

Classificacao:

```text
TEMPORAL_STATE_READY_WITHOUT_TIMEINTEGRATOR
```

A auditoria completa da fronteira de includes esta em
`docs/audits/saltcreep_timeintegrator_include_boundary.md`, e o contrato de
estado persistido esta em `docs/27_saltcreep_adapter_temporal_state.md`.

## Bridge temporal isolado

A Fase 7.8 cria `SaltCreepTimeBridge`, documentado em
`docs/28_saltcreep_time_bridge.md`. Ele compila e executa
`TimeIntegrator::advance()` em target CMake isolado, com include boundary
controlada para que `"io/CaseParser.hpp"` resolva para o header do
`external/saltcreep`.

O bridge nao e chamado por `SaltCreepSaltcreepAdapter` nesta fase. Ele apenas
remove o bloqueio tecnico de includes e prova uma API publica limpa para uma
futura substituicao do cache elastico por integrador temporal.

## Adapter conectado ao bridge

A Fase 7.9 conecta `SaltCreepSaltcreepAdapter` ao `SaltCreepTimeBridge`.
`BackendCache` permanece opaco e preguiçoso, mas agora guarda um bridge
persistente em vez de montar diretamente `AxisymL3`, `Assembler` e
`ElasticSolver` dentro do adapter.

O adapter nao inclui headers do `external/saltcreep`; a rota temporal fica
atraves do bridge isolado. A politica de pressao desta fase e constante:
`query.wall_pressure_Pa` deve coincidir com
`config.wall_pressure.initial_wall_pressure_Pa`.

Detalhes completos em
`docs/29_saltcreep_adapter_time_bridge_connection.md`.

## Por que o backend temporal real ainda nao foi ligado

Ainda nao ha uma API temporal de producao do tipo "avaliar resposta de parede"
que aceite apenas `SaltCreepQuery`. O uso completo do `saltcreep` exige
selecionar e construir:

- malha;
- elemento;
- material constitutivo;
- campo termico;
- tensao geostatica;
- campo de pressao de parede;
- condicoes de contorno;
- integrador explicito ou implicito.

Conectar parcialmente o integrador temporal nesta fase criaria risco de
reinterpretar a fisica e de misturar headers homonimos. A decisao tecnica da
Fase 7.6 e ativar somente a rota elastica/geostatica minima.

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Mapeamento de pressao de parede incompleto | Fase 7.4 testou `WallPressureField` + `TimeIntegrator`; adapter real ainda precisa mapear condicoes fisicas LOT/APB. |
| Tensao geostatica e sinal interno do backend | Preservar FA03 no contrato moderno e testar conversao no adapter real. |
| Tempo e passo do backend | Fase 7.6 registra tempo no estado, mas ainda nao usa `TimeIntegrator` no adapter. |
| Temperatura | Contrato usa K; backend real deve receber campo termico coerente. |
| Acoplamento LOT/sal prematuro | `lot-sim run` e `PknModel` permanecem intocados nesta fase. |
| Sinal da pressao aplicada | Fase 7.3 provou que pressao interna positiva expande a parede; o adapter real deve mapear pressoes internas, externas e geostaticas deliberadamente. |

## Proximos passos

1. Projetar configuracao explicita do adapter real: geometria, malha, material,
   integrador e campo termico. **Concluido na Fase 7.5 como contrato C++ ainda
   neutro.**
2. Conectar `SaltCreepAdapterConfig` aos objetos reais do backend em teste
   isolado antes de ativar `is_available()`. **Concluido parcialmente na Fase
   7.6 para backend elastico/geostatico minimo.**
3. Persistir objetos do backend minimo entre chamadas. **Concluido na Fase 7.7
   sem `TimeIntegrator`.**
4. Resolver a rota temporal com `TimeIntegrator` sem conflito de includes.
   **Concluido como bridge isolado na Fase 7.8.**
5. Conectar o bridge ao adapter principal, ainda sem modificar `PknModel`.
   **Concluido na Fase 7.9 com pressao constante.**
6. Somente depois conectar o adapter a `coupling/`, ainda sem modificar
   `PknModel`.
