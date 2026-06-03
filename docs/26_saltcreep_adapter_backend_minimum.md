# 26 — Backend minimo do SaltCreepSaltcreepAdapter

**Status:** Substituido pelo bridge temporal no adapter — Fases 7.6-7.9 | **Ultima atualizacao:** 2026-06-03

## Objetivo

A Fase 7.6 conecta `SaltCreepSaltcreepAdapter::evaluate_wall_response()` a uma
rota C++ real e minima do backend `external/saltcreep`, ainda sem acoplar
LOT/PKN/APB ao sal.

Esta fase nao declara validacao fisica ampla. O objetivo e provar que o adapter
moderno consegue montar e executar um caso elastico controlado do backend a
partir de `SaltCreepAdapterConfig` e registrar a resposta em
`SaltCreepAdapterState`.

## Componentes conectados

O adapter usa diretamente:

- `build_mesh_L3`;
- `AxisymL3`;
- `ElasticIsotropic`;
- `Assembler::assemble_K`;
- `Assembler::assemble_boundary_pressure`;
- `Assembler::assemble_geostatic_force`, quando `config.geostatic.enabled`;
- `ConstantWallPressureField`;
- `ElasticSolver`;
- leitura de `u[0]` como deslocamento radial assinado da parede.

O backend e compilado no target principal apenas com os fontes minimos:

- `external/saltcreep/src/constitutive/elastic_isotropic.cpp`;
- `external/saltcreep/src/elements/axisym_1d_L3.cpp`;
- `external/saltcreep/src/solver/Assembler.cpp`;
- `external/saltcreep/src/solver/ElasticSolver.cpp`;
- `external/saltcreep/src/solver/WallPressureField.cpp`.

Nenhum arquivo em `external/saltcreep/` foi alterado.

## Situacao apos a Fase 7.9

A rota elastica minima direta permanece documentada como prova da Fase 7.6 e
continua sendo usada por testes controlados separados. No adapter principal,
ela foi substituida pelo `SaltCreepTimeBridge` na Fase 7.9.

Com isso, `SaltCreepSaltcreepAdapter` nao monta mais diretamente malha,
material, matriz de rigidez ou solver elastico. Ele delega a rota temporal ao
bridge persistente, que por sua vez executa `TimeIntegrator::advance()` em
target CMake isolado.

Ver `docs/29_saltcreep_adapter_time_bridge_connection.md`.

## Persistencia adicionada na Fase 7.7

Na Fase 7.6, a rota minima era reconstruida em cada
`evaluate_wall_response()`. Na Fase 7.7, esses objetos passaram para um cache
privado e preguiçoso do adapter:

- elemento;
- material;
- malha;
- matriz de rigidez;
- vetor geostatico;
- graus de liberdade fixos.

Cada query continua montando o vetor de pressao de parede especifico do tempo e
da pressao solicitados. O solver elastico ainda resolve uma copia da matriz
persistida, preservando o contrato de chamada sem introduzir estado numerico de
fluencia.

Detalhes em `docs/27_saltcreep_adapter_temporal_state.md`.

## Limite deliberado

`TimeIntegrator` continua provado nos targets Catch2 separados das Fases 7.4,
mas nao foi linkado ao target principal nesta fase. O motivo e pratico e
documentado: `TimeIntegrator.hpp` inclui `io/CaseParser.hpp`, nome que tambem
existe no `lot-salt-suite`. Trazer esse caminho para o target principal nesta
fase criaria risco de conflito de include entre o parser moderno e o parser
vendorizado do saltcreep.

Assim, o backend minimo do adapter usa a rota elastica controlada. O caminho
com `TimeIntegrator`, campo termico e geostatica temporal permanece isolado em
`saltcreep_backend_time_geostatic_tests` ate haver uma fase dedicada para
resolver a fronteira de includes e estado temporal real.

A Fase 7.7 formaliza essa decisao em
`docs/audits/saltcreep_timeintegrator_include_boundary.md` com classificacao
`TIMEINTEGRATOR_BLOCKED_BY_INCLUDE_BOUNDARY`.

## Configuracao minima

O backend minimo suporta:

- geometria axisimetrica 1D L3;
- deformacao plana;
- `mesh.axial_elements == 1`;
- material `ElasticIsotropic`;
- pressao de parede constante na fronteira interna;
- vetor geostatico explicito uniforme, se habilitado;
- parede externa fixa somente no caso geostatico.

Campos de `SaltCreepAdapterConfig` ainda nao consumidos pelo backend minimo,
como `height_m`, `temperature_K`, `reference_temperature_K`,
`alpha_thermal_1_K`, `dt_s`, `total_time_s` e `max_steps`, permanecem
validados e documentados para a futura conexao temporal.

## `is_available()`

Na Fase 7.6:

```text
SaltCreepSaltcreepAdapter::is_available() = true
```

para configuracoes suportadas pelo backend minimo:

- `geometry.axisymmetric == true`;
- `geometry.plane_strain == true`;
- `mesh.axial_elements == 1`;
- configuracao validada no construtor.

Configuracoes validas, mas fora dessa superficie minima, retornam
`is_available() = false`; chamar `evaluate_wall_response()` nesse estado lanca
`std::logic_error`.

## `mutable state_`

`evaluate_wall_response()` permanece `const` por contrato de interface. Para
registrar o historico interno, `state_` passou a ser `mutable`.

Isso e tratado como constancia logica: a chamada nao altera configuracao,
modelo fisico ou escolha de backend; apenas grava a ultima resposta e incrementa
o contador de passos em `SaltCreepAdapterState`.

## Convencao de sinais

O adapter retorna:

```text
radial_displacement_m = u_wall assinado do backend
radial_closure_m      = max(0, -radial_displacement_m)
radial_strain         = radial_displacement_m / inner_radius_m
effective_closure_pressure_Pa = 0
```

`radial_strain` usa a aproximacao `u_r / r_i`, que e tecnicamente a deformacao
circunferencial (hoop strain `epsilon_theta = u/r`) avaliada no raio interno.
A deformacao radial exata seria `epsilon_r = du/dr`. Para o backend minimo
elastico sem fluencia, o sinal e correto (positivo em expansao, negativo em
fechamento) e o erro de nomenclatura nao afeta o contrato de dados. Uma fase
futura com fluencia real deve revisar e corrigir essa convencao se necessario.

`effective_closure_pressure_Pa` permanece zero porque esta fase nao estima uma
pressao efetiva de fechamento a partir do campo elastico. Esse campo continuara
reservado para uma fase com mapeamento fisico mais completo.

O teste de Lame confirma que pressao interna positiva aplicada por
`ConstantWallPressureField` expande a parede (`u_r > 0`) e fechamento nulo. O
teste geostatico confirma que uma compressao geostatica simplificada, com
parede externa fixa, produz fechamento (`u_r < 0`) e `radial_closure_m > 0`.

## Ausencia de acoplamento LOT/PKN/APB

Esta fase nao altera `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter`,
`CaseParser`, APB ou `coupling/`.

`lot-sim run --mode lot-pkn` continua executando o caminho LOT/PKN moderno sem
instanciar `SaltCreepSaltcreepAdapter`.

## Proximos passos

1. Resolver a fronteira de includes para trazer `TimeIntegrator` ao adapter sem
   conflito entre parsers `io/CaseParser.hpp`.
2. Persistir objetos do backend entre chamadas, em vez de reconstruir o caso
   elastico a cada query. **Concluido na Fase 7.7 para a rota minima.**
3. Definir mapeamento fisico de pressao LOT/APB para pressao interna, externa e
   geostatica.
4. Introduzir campo termico real e integrador temporal apenas depois de testes
   isolados de regressao.
