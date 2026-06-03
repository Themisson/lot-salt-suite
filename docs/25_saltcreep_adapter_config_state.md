# 25 — Configuracao e estado do SaltCreepSaltcreepAdapter

**Status:** Implementado e usado pelo backend minimo — Fases 7.5-7.7 | **Ultima atualizacao:** 2026-06-03

## Objetivo

A Fase 7.5 adiciona uma configuracao explicita e uma pequena state machine para
o futuro adapter real do `external/saltcreep/`, ainda sem executar o backend FEM
de sal.

O objetivo e estabilizar a fronteira C++ necessaria antes de qualquer ligacao
fisica: geometria, malha, material elastico, campo termico constante, tensoes
geostaticas assinadas, controle de tempo, pressao inicial de parede e estado
temporal do adapter.

## Escopo implementado

Arquivos C++ novos:

- `include/salt/SaltCreepAdapterConfig.hpp`
- `src/salt/SaltCreepAdapterConfig.cpp`
- `include/salt/SaltCreepAdapterState.hpp`
- `src/salt/SaltCreepAdapterState.cpp`

Testes Catch2 novos:

- `tests/cpp/test_salt_creep_adapter_config.cpp`
- `tests/cpp/test_salt_creep_adapter_state.cpp`

O `SaltCreepSaltcreepAdapter` agora aceita uma `SaltCreepAdapterConfig`
validada, inicializa `SaltCreepAdapterState` com tempo e pressao inicial, e
expoe `config()` e `state()` para inspecao. O metodo
`evaluate_wall_response()` usa esses dados para montar o backend elastico
minimo da Fase 7.6 e registrar a resposta no estado.

## Configuracao

`SaltCreepAdapterConfig` usa apenas SI. Os defaults sao conservadores e
sinteticos:

| Grupo | Campos principais |
|-------|-------------------|
| `geometry` | `inner_radius_m`, `outer_radius_m`, `height_m`, `axisymmetric`, `plane_strain` |
| `mesh` | `radial_elements`, `axial_elements` |
| `material` | `elastic_modulus_Pa`, `poisson_ratio`, `density_kg_m3` |
| `thermal` | `temperature_K`, `reference_temperature_K`, `alpha_thermal_1_K` |
| `geostatic` | `enabled`, `radial_stress_Pa`, `hoop_stress_Pa`, `vertical_stress_Pa`, `use_explicit_gauss_point_vector` |
| `time` | `initial_time_s`, `dt_s`, `total_time_s`, `max_steps` |
| `wall_pressure` | `initial_wall_pressure_Pa` |

Validações principais:

- todos os `double` devem ser finitos;
- dimensoes geometricas devem ser positivas e `outer_radius_m > inner_radius_m`;
- numero de elementos deve ser positivo;
- modulo elastico e densidade devem ser positivos;
- `poisson_ratio` deve estar no intervalo aberto `(-1, 0.5)`;
- temperaturas em K devem ser positivas;
- tensoes geostaticas podem ser negativas, pois sao assinadas para o backend;
- tempo inicial deve ser nao negativo, `dt_s > 0`, `total_time_s >= initial_time_s`;
- pressao inicial de parede deve ser nao negativa.

## Estado

`SaltCreepAdapterState` rastreia somente dados do adapter: inicializacao, tempo
atual, ultima pressao de parede, ultimo deslocamento radial, ultimo fechamento
radial e contador de passos.

`initialize()` valida tempo e pressao inicial, marca o estado como inicializado e
zera deslocamento, fechamento e contador. `record_response()` exige estado
inicializado, tempo nao decrescente, pressao nao negativa, resposta valida e
campos finitos. `reset()` retorna ao estado neutro nao inicializado.

## O que permanece fora de escopo

Esta fase nao instancia `TimeIntegrator` no adapter real, nao acopla
LOT/PKN/APB ao sal e nao muda nenhum modelo fisico.

`SaltCreepSaltcreepAdapter::is_available()` permanece:

```text
true para configuracoes suportadas pelo backend minimo
```

## Relacao com os testes controlados do backend

As Fases 7.3 e 7.4 provaram rotas C++ isoladas para o backend `saltcreep`:
caso elastico de Lame, `WallPressureField`, `ProfileField`, geostatica explicita
e `TimeIntegrator`. A Fase 7.5 nao conecta essas rotas ao adapter; ela apenas
cria a estrutura de configuracao e estado que sera necessaria para uma fase
posterior de ligacao real.

Na Fase 7.6, a configuracao passou a alimentar uma rota elastica/geostatica
minima (`AxisymL3`, `ElasticIsotropic`, `Assembler`, `ElasticSolver`) e
`state_` passou a ser `mutable` para permitir registro em
`evaluate_wall_response() const`. Ver
`docs/26_saltcreep_adapter_backend_minimum.md`.

Na Fase 7.7, a configuracao tambem passou a alimentar um cache privado do
backend minimo. O cache persiste malha, elemento, material, matriz de rigidez,
vetor geostatico e graus fixos entre queries, enquanto `SaltCreepAdapterState`
continua responsavel pelo tempo atual, ultima pressao, ultimo deslocamento,
ultimo fechamento e contador de passos. Ver
`docs/27_saltcreep_adapter_temporal_state.md`.
