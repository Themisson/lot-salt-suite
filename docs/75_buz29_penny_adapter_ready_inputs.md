# Fase 11.10B — entradas adapter-ready BUZ29-PENNY

## Resumo executivo

A 11.10B não executa BUZ29-PENNY e não valida BUZ29. Ela apenas inspeciona se o candidato BUZ29-PENNY possui entradas suficientes e semanticamente mapeáveis para o PennyShapedDiagnosticAdapter.

Classificação:

```text
PHASE11_10B_BUZ29_PENNY_ADAPTER_READY_INPUTS_INSPECTED
BUZ29_PENNY_ADAPTER_INPUTS_PARTIAL
```

O candidato tem evidência consumível de pressão e abertura, mas ainda não possui
todos os campos exigidos pelo `PennyShapedDiagnosticAdapter` como entradas
diretas. Portanto:

```text
adapter_ready = false
partial_adapter_ready = true
physically_validated = false
legacy_equivalent = false
active_simulation_case = false
```

## Contexto pós-11.10A

A 11.10A criou:

```text
cases/validation/non_pkn/buz29_penny_candidate.yaml
cases/validation/non_pkn/studies_index.yaml
```

O candidato é inativo, diagnóstico e não-runtime. Ele preserva:

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
NOT_ACTIVE_SIMULATION_CASE
```

## API exigida pelo PennyShapedDiagnosticAdapter

A API real auditada em `include/lot/PennyShapedDiagnosticAdapter.hpp` consome:

| Campo | Unidade | Status 11.10B |
|---|---:|---|
| `young_modulus_Pa` | Pa | Ausente no candidato |
| `poisson_ratio` | adimensional | Ausente no candidato |
| `viscosity_Pa_min` | Pa.min | Ausente no candidato |
| `flow_rate_m3_min` | m3/min | Ausente no candidato |
| `elapsed_since_opening_min` | min | Marcador de abertura existe, mas ainda requer revisão semântica |
| `wellbore_pressure_Pa` | Pa | Histórico de pressão existe, mas amostra adaptada ainda requer revisão semântica |
| `sigma_theta_compression_positive_Pa` | Pa | Ausente no output legado direto |
| `volume_multiplier` | adimensional | Inferido pelo default `10.0`, mas não declarado explicitamente para BUZ29 |

Saídas do adapter:

```text
plane_strain_modulus_Pa
opening_m
radius_m
pressure_factor
fracture_volume_proxy_m3
```

## YAML candidato inspecionado

Arquivo:

```text
cases/validation/non_pkn/buz29_penny_candidate.yaml
```

Campos consumíveis como evidência:

- `pressure_history_status = PRESSURE_HISTORY_FOUND_CONSUMABLE`;
- `opening_time_status = OPENING_TIME_FOUND_CONSUMABLE`;
- `opening_time_min = 10.4`;
- blocos `dP`, `dV_leakoff`, `V_outflow`;
- `axisymmetric_angle_rad = 1.0`.

## Mapeamento campo-a-campo

| Campo | Status | Interpretação |
|---|---|---|
| `young_modulus_Pa` | `MISSING` | Não está no candidato 11.10A. |
| `poisson_ratio` | `MISSING` | Não está no candidato 11.10A. |
| `viscosity_Pa_min` | `MISSING` | Não está no candidato 11.10A. |
| `flow_rate_m3_min` | `MISSING` | Não está no candidato 11.10A. |
| `elapsed_since_opening_min` | `FOUND_NEEDS_SEMANTIC_REVIEW` | O candidato tem tempo de abertura absoluto, não duração pós-abertura. |
| `wellbore_pressure_Pa` | `FOUND_NEEDS_SEMANTIC_REVIEW` | Há histórico de pressão, mas falta selecionar a amostra de entrada. |
| `sigma_theta_compression_positive_Pa` | `MISSING` | O output legado não exporta `sigmaTheta` diretamente. |
| `volume_multiplier` | `INFERRED` | O adapter possui default `10.0`, mas o candidato ainda não o declara como escolha BUZ29. |
| `netPressure_Pa` | `NOT_APPLICABLE` | Não é entrada real da API atual. |
| `characteristicRadius_m` | `NOT_APPLICABLE` | A API calcula `radius_m`; não consome raio característico. |
| `opening_time_min` | `FOUND_CONSUMABLE` | Marcador legado consumível para preparação diagnóstica. |
| `pressure_history` | `FOUND_NEEDS_CONVERSION` | Histórico existe, mas a amostra adapter-ready é futura. |
| `leakoff_history` | `FOUND_CONSUMABLE` | Evidência disponível, não consumida diretamente pelo adapter. |
| `outflow_history` | `FOUND_CONSUMABLE` | Evidência disponível, não consumida diretamente pelo adapter. |
| `axisymmetric_angle_rad` | `FOUND_CONSUMABLE` | Interpretação 1 rad declarada. |

## Campos que exigem revisão semântica

- `elapsed_since_opening_min`;
- `wellbore_pressure_Pa`;
- `pressure_history`.

## Campos ausentes

- `young_modulus_Pa`;
- `poisson_ratio`;
- `viscosity_Pa_min`;
- `flow_rate_m3_min`;
- `sigma_theta_compression_positive_Pa`.

## Campos diferidos

- `sigmaTheta`;
- `pw`;
- `margin`;
- `opened`;
- validação física completa;
- auditoria matemática do `PennyShapedModel`;
- runner não-PKN runtime;
- conversão explícita 1rad/2π.

## Caveat axissimétrico 1 rad

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
```

Mesmo que as entradas sejam classificadas como adapter-ready, a execução diagnóstica deve aguardar auditoria matemática específica do PennyShapedModel na formulação axissimétrica de 1 rad.

## Requisito futuro de saída 1rad + 2π

```text
AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED
```

As saídas futuras deverão distinguir grandezas internas em 1 rad de volumes totais equivalentes em 2π quando a interpretação física do sólido completo for necessária.

## Decisão

```text
classification = BUZ29_PENNY_ADAPTER_INPUTS_PARTIAL
adapter_ready = false
partial_adapter_ready = true
recommended_next_phase = PHASE11_10C_AUDIT_PENNY_SHAPED_MODEL_MATH_AXISYMMETRIC_1RAD
```

A próxima fase recomendada é auditoria matemática, não execução BUZ29.

## Resultado da 11.10C

A auditoria matemática do `PennyShapedModel` foi concluída:

```text
primary_classification = PENNY_MATH_HYDRAULIC_DIAGNOSTIC_SCALING
secondary_classification = PENNY_MATH_AXISYMMETRIC_1RAD_PROXY
pressure_semantics = PRESSURE_SEMANTICS_CLEAR
volume_multiplier_semantics = VOLUME_MULTIPLIER_EMPIRICAL
math_audit_passed = true
requires_code_correction = false
requires_output_contract = true
```

Isso reduz o risco de correção matemática imediata no núcleo, mas não torna o
candidato BUZ29 adapter-ready. Os campos ausentes continuam ausentes, e o
próximo gate deve definir o contrato de saída 1 rad/2π antes de qualquer
execução diagnóstica BUZ29.

## Resultado da 11.10D

O contrato de saída 1 rad/2π foi especificado:

```text
contract_status = AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_SPECIFIED
volume_multiplier_semantics = VOLUME_MULTIPLIER_EMPIRICAL
implementation_allowed = false
recommended_next_phase = PHASE11_10E_DEFINE_PENNY_DIAGNOSTIC_OUTPUT_FIXTURES
```

A execução BUZ29-PENNY segue bloqueada. A próxima etapa segura é criar fixtures
de saída diagnóstica que preservem o valor de origem em 1 rad e reportem
equivalentes 2π apenas com `source`/caveat.

## Riscos remanescentes

- A pressão legada ainda precisa ser transformada em amostra `wellbore_pressure_Pa`.
- O tempo de abertura não é automaticamente `elapsed_since_opening_min`.
- `sigmaTheta` BUZ29 segue ausente no output legado direto.
- O volume proxy continua na convenção axissimétrica de 1 rad.
- O candidato permanece fora do parser/schema/runtime oficial.

## Resultado da Fase 11.10H

A 11.10H manteve a classificação operacional do candidato como parcial no gate
do runner não-PKN:

```text
decision = NON_PKN_DIAGNOSTIC_RUNNER_SPEC_PARTIAL
adapter_ready = false
partial_adapter_ready = true
runner_implementation_allowed_now = false
buz29_runtime_execution_allowed = false
```

O runner futuro pode ser especificado, mas não implementado nesta fase. A
execução BUZ29-PENNY segue proibida até que os campos ausentes e as semânticas
de pressão, tempo desde abertura e `sigmaTheta` sejam resolvidos por gate
posterior.
