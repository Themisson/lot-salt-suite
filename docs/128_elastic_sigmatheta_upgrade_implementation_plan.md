# Plano de implementação do upgrade elástico sigma_theta

## Resumo executivo

A implementação planejada adiciona uma fonte opt-in ao
`PostDrillingSigmaThetaProvider`:

```text
AXISYMMETRIC_ELASTIC_WELLBORE_STATE
```

Status:

```text
ELASTIC_SIGMATHETA_UPGRADE_IMPLEMENTATION_PLAN_READY
selected_formula = AXISYMMETRIC_ELASTIC_WELLBORE_SOURCE
proposed_provider_source = AXISYMMETRIC_ELASTIC_WELLBORE_STATE
implementation_allowed_next = true
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_change_allowed = false
```

## Campos mínimos

```text
far_field_stress_compression_positive_Pa
wellbore_pressure_Pa
tensile_strength_Pa
```

Esses campos já existem no contrato do provider elástico atual e permitem uma
primeira fonte axisimétrica diagnóstica sem alterar o runtime físico.

## Fórmula planejada

Convenção: compressão positiva.

```text
sigma_theta_initial_compression_positive_Pa =
  far_field_stress_compression_positive_Pa

sigma_theta_current_compression_positive_Pa =
  far_field_stress_compression_positive_Pa - wellbore_pressure_Pa
```

A diferença em relação à fonte simplificada atual é contratual: a nova fonte
declara explicitamente a rota axisimétrica de parede e abre espaço para campos
futuros como raio, propriedades elásticas e mapeamento de camada, sem modificar
o comportamento da fonte antiga.

## Mudanças planejadas

- adicionar `AXISYMMETRIC_ELASTIC_WELLBORE_STATE` ao enum do provider;
- aceitar a fonte no parser e no schema;
- preservar `ELASTIC_INITIAL_WELLBORE_STATE`;
- manter `physically_validated=false` e `legacy_equivalent=false`;
- manter `runtime_dispatch_enabled=false`;
- adicionar testes C++ de provider/parser/pre-runner;
- adicionar fixtures e auditoria Python da nova fonte.

## Gate

```text
implementation_allowed_next = true
```

O próximo commit pode implementar a fonte, desde que não altere PKN, não execute
BUZ29-PENNY e não habilite dispatch físico.
