# Fase 11.10A — rota diagnóstica BUZ29-PENNY

## Resumo executivo

A Fase 11.10A inicia uma rota diagnóstica controlada para o caso
`BUZ29-VISCO-first-well` na trilha `PENNY_SHAPED`.

Classificação:

```text
PHASE11_10A_BUZ29_PENNY_DIAGNOSTIC_ROUTE_PARTIAL_STARTED
BUZ29_PENNY_DIAGNOSTIC_ROUTE_PARTIAL_STARTED
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
NOT_ACTIVE_SIMULATION_CASE
```

A fase cria um YAML candidato e um índice não-PKN, ambos restritos a
preparação diagnóstica. Eles não são rota oficial do `lot-sim`, não validam
BUZ29 fisicamente e não declaram equivalência com o `LOT_Tese`.

## Pré-condição herdada

A Fase 11.9F abriu o gate:

```text
updated_readiness = BUZ29_PENNY_CANDIDATE_PARTIAL_BUT_DIAGNOSTIC_SAFE
can_start_11_10A = true
gate = BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A
recommended_next_phase = PHASE11_10A_START_BUZ29_PENNY_DIAGNOSTIC_ROUTE
axisymmetric_interpretation = PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
```

Essa autorização é limitada à preparação diagnóstica. Ela não permite execução
física BUZ29, calibração, rota runtime oficial ou equivalência legado-moderna.

## Artefatos criados

| Artefato | Função |
|---|---|
| `cases/validation/non_pkn/buz29_penny_candidate.yaml` | YAML candidato BUZ29-PENNY, inativo e diagnóstico. |
| `cases/validation/non_pkn/studies_index.yaml` | Índice local de estudos não-PKN, apenas metadado de descoberta. |
| `tools/inspect_phase11_10a_buz29_penny_candidate.py` | Inspetor do contrato diagnóstico 11.10A. |
| `tests/python/test_inspect_phase11_10a_buz29_penny_candidate.py` | Testes do inspetor e dos bloqueios semânticos. |

## Evidência consumida

O candidato referencia a evidência consumível da 11.9E:

```text
source_output = legance/LOT_Tese/results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat
pressure_history_status = PRESSURE_HISTORY_FOUND_CONSUMABLE
opening_time_status = OPENING_TIME_FOUND_CONSUMABLE
time_points = 131
time_range = 0.0 .. 13.0 min
opening_time = 10.4 min
```

Campos presentes no output legado:

- `Time`;
- blocos `dP`;
- blocos `dV_leakoff`;
- `V_outflow`;
- `Momento da quebra: 10.4`.

## Campos ausentes ou diferidos

O output legado ainda não exporta diretamente:

- `sigmaTheta`;
- `pw`;
- `margin`;
- `opened`.

Esses campos permanecem lacunas para validação física ou equivalência
estrita. Na 11.10A eles são caveats não bloqueantes apenas porque a fase não
executa simulação e não compara física.

## Caveat axissimétrico

O caveat obrigatório continua:

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
```

Portanto, o proxy de volume do `PennyShapedModel` deve ser interpretado em
base axissimétrica de 1 rad. A próxima exigência documental é:

```text
AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED
```

Uma fase futura deve separar explicitamente quantidades internas de 1 rad e
quantidades equivalentes 2π antes de qualquer interpretação forte de volume.

## O que esta fase não faz

- Não executa BUZ29 como simulação física.
- Não cria rota runtime oficial para `lot-sim`.
- Não altera `PknModel`, `PknRunner`, `volumetric_balance` ou `pkn_direct`.
- Não implementa solver `PENNY_SHAPED` acoplado ao runtime.
- Não implementa correção matemática do `PennyShapedModel`.
- Não altera `legance/`, `legacy/`, `external/saltcreep/` ou casos protegidos.
- Não versiona artefatos em `results/`.

## Próxima fase recomendada

```text
PHASE11_10B_INSPECT_BUZ29_PENNY_ADAPTER_READY_INPUTS
```

Essa próxima fase deve auditar se os inputs reais necessários ao
`PennyShapedDiagnosticAdapter` podem ser montados sem inventar parâmetros e sem
promover o candidato a rota runtime oficial.

## Resultado da 11.10B

A inspeção dos inputs adapter-ready classificou o candidato como parcial:

```text
classification = BUZ29_PENNY_ADAPTER_INPUTS_PARTIAL
adapter_ready = false
partial_adapter_ready = true
```

A API real do `PennyShapedDiagnosticAdapter` exige:

```text
young_modulus_Pa
poisson_ratio
viscosity_Pa_min
flow_rate_m3_min
elapsed_since_opening_min
wellbore_pressure_Pa
sigma_theta_compression_positive_Pa
volume_multiplier
```

O candidato 11.10A possui pressão/abertura consumíveis, mas ainda não possui
todos os campos acima como entradas diretas e semanticamente prontas. A próxima
fase recomendada é:

```text
PHASE11_10C_AUDIT_PENNY_SHAPED_MODEL_MATH_AXISYMMETRIC_1RAD
```

## Resultado da 11.10C

A auditoria matemática foi executada sem alterar C++ e sem executar
BUZ29-PENNY:

```text
primary_classification = PENNY_MATH_HYDRAULIC_DIAGNOSTIC_SCALING
secondary_classification = PENNY_MATH_AXISYMMETRIC_1RAD_PROXY
tertiary_classification = PENNY_MATH_LEGACY_INSPIRED_EMPIRICAL
math_audit_passed = true
requires_code_correction = false
requires_output_contract = true
recommended_next_phase = PHASE11_10D_DEFINE_AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT
```

Com isso, a rota BUZ29-PENNY continua diagnóstica e inativa. A divergência
principal não é uma correção matemática imediata do núcleo, mas a falta de um
contrato explícito para `fracture_volume_proxy_m3` entre base interna de 1 rad
e volume total equivalente 2π.

## Resultado da 11.10I

A 11.10I especificou que o futuro caminho PennyShaped não deve criar uma rota
oficial paralela ao LOT. A seleção deverá ser feita por:

```text
lot.fracture.fracture_model
```

com `PKN` como default quando o campo estiver ausente e `PENNY_SHAPED` apenas
como opt-in explícito, diagnóstico e não fisicamente validado. BUZ29-PENNY
continua não executado e fora de validação física.
## Atualização 11.10J — seleção guardada por `fracture_model`

A rota BUZ29-PENNY permanece diagnóstica e inativa. A Fase 11.10J especifica
que uma futura seleção por `lot.fracture.fracture_model` deve aceitar
`PENNY_SHAPED` somente por opt-in explícito, rejeitar valor vazio explícito e
bloquear modelos não suportados antes de qualquer execução.
