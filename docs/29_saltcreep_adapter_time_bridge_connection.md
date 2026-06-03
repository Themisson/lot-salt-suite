# 29 — Conexao do SaltCreepSaltcreepAdapter ao SaltCreepTimeBridge

**Status:** Implementado e isolado — Fase 7.9
**Ultima atualizacao:** 2026-06-03

## Objetivo

A Fase 7.9 conecta `SaltCreepSaltcreepAdapter` ao `SaltCreepTimeBridge`
persistente criado na Fase 7.8. O adapter passa a usar
`TimeIntegrator::advance()` indiretamente pelo bridge, sem incluir headers do
`external/saltcreep` no adapter e sem acoplar LOT/PKN/APB ao sal.

## Mapeamento de configuracao

O mapeamento interno e:

| `SaltCreepAdapterConfig` | `SaltCreepTimeBridgeConfig` |
|--------------------------|-----------------------------|
| `geometry.inner_radius_m` | `inner_radius_m` |
| `geometry.outer_radius_m` | `outer_radius_m` |
| `geometry.height_m` | `height_m` |
| `mesh.radial_elements` | `radial_elements` |
| `material.elastic_modulus_Pa` | `elastic_modulus_Pa` |
| `material.poisson_ratio` | `poisson_ratio` |
| `thermal.temperature_K` | `temperature_K` |
| `thermal.reference_temperature_K` | `reference_temperature_K` |
| `thermal.alpha_thermal_1_K` | `alpha_thermal_1_K` |
| `wall_pressure.initial_wall_pressure_Pa` | `wall_pressure_Pa` |
| `geostatic.enabled` | `geostatic_enabled` |
| `geostatic.radial_stress_Pa` | `geostatic_radial_stress_Pa` |
| `geostatic.hoop_stress_Pa` | `geostatic_hoop_stress_Pa` |
| `geostatic.vertical_stress_Pa` | `geostatic_vertical_stress_Pa` |

Campos ainda sem uso direto no bridge:

- `material.density_kg_m3`;
- `time.dt_s`;
- `time.total_time_s`;
- `time.max_steps`.

Esses campos permanecem validados no adapter para preservar o contrato futuro,
mas nao alteram a prova temporal elastica desta fase.

## Superficie suportada

`is_available()` retorna `true` quando a configuracao validada satisfaz:

- `geometry.axisymmetric == true`;
- `geometry.plane_strain == true`;
- `mesh.axial_elements == 1`;
- `geostatic.use_explicit_gauss_point_vector == true`.

Configuracoes validas fora dessa superficie retornam `false` e
`evaluate_wall_response()` lanca `std::logic_error`.

## Persistencia

O adapter mantem um `BackendCache` opaco, mas esse cache agora possui um
`SaltCreepTimeBridge` persistente. O bridge e construido preguiçosamente na
primeira query valida e fica vivo entre chamadas da mesma instancia.

Se `time.initial_time_s > 0`, o bridge e avancado ate esse tempo na construcao
do cache para alinhar o estado temporal interno ao estado inicial do adapter.

## Politica de pressao temporal

O bridge da Fase 7.8 usa `ConstantWallPressureField` e ainda nao troca a
pressao dinamicamente entre passos. Por isso, a Fase 7.9 adota uma politica
deliberadamente restrita:

```text
query.wall_pressure_Pa deve ser igual a
config.wall_pressure.initial_wall_pressure_Pa
```

Se a query trouxer pressao diferente, `evaluate_wall_response()` lanca
`std::invalid_argument` antes de construir o bridge. Uma fase futura deve
introduzir campo de pressao temporal ou reconstrucao controlada antes de aceitar
historico variavel de pressao.

## Estado e resposta

`evaluate_wall_response()`:

1. valida a query SI;
2. verifica suporte da configuracao;
3. aplica a politica de pressao constante;
4. constroi ou reutiliza o bridge;
5. avanca o bridge ate `query.time_s`;
6. converte o resultado para `SaltCreepResponse`;
7. registra a resposta em `SaltCreepAdapterState`.

O retorno preserva o contrato:

```text
radial_displacement_m = deslocamento de parede do bridge
radial_closure_m = max(0, -radial_displacement_m)
radial_strain = radial_displacement_m / inner_radius_m
effective_closure_pressure_Pa = 0
valid = true
```

`radial_strain` continua sendo o proxy `u_r / r_i` documentado nas Fases 7.6 e
7.7.

## Ausencia de acoplamento LOT/PKN/APB

Esta fase nao altera `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter`,
`CaseParser`, APB ou `coupling/`.

`lot-sim run --mode lot-pkn` continua executando o caminho LOT/PKN moderno sem
instanciar `SaltCreepSaltcreepAdapter`.

## Proximos passos

1. Adicionar suporte explicito a pressao de parede variavel no bridge.
2. Revisar a semantica de `radial_strain` quando o estado temporal expuser
   campo de deformacao adequado.
3. Mapear configs de fluencia real e dano apenas com testes dedicados.
4. Depois disso, avaliar conexao opcional do adapter ao futuro `coupling/`,
   ainda sem tocar no caminho LOT/PKN existente.
