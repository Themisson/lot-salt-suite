# Fase 11.10H — gate do runner diagnóstico não-PKN

## Resumo executivo

A Fase 11.10H registra o gate para uma futura especificação de runner
diagnóstico não-PKN para PennyShaped.

Status:

```text
PHASE11_10H_NON_PKN_DIAGNOSTIC_RUNNER_GATE_RECORDED
NON_PKN_DIAGNOSTIC_RUNNER_SPEC_PARTIAL
RUNNER_IMPLEMENTATION_NOT_ALLOWED_IN_11_10H
BUZ29_RUNTIME_EXECUTION_NOT_ALLOWED
LOT_PKN_IMPACT_NOT_ALLOWED
```

A 11.10H não implementa runner. Ela apenas decide se é seguro especificar, em
fase futura, um runner diagnóstico não-PKN isolado para conectar
PennyShapedDiagnosticAdapter e PennyShapedDiagnosticWriter.

## Contexto pós-11.10G

A Fase 11.10G implementou:

```text
include/lot/PennyShapedDiagnosticWriter.hpp
src/lot/PennyShapedDiagnosticWriter.cpp
tests/cpp/test_penny_shaped_diagnostic_writer.cpp
```

O writer está disponível, opt-in e isolado, mas ainda não existe runner
diagnóstico não-PKN nem execução BUZ29-PENNY.

## Adapter disponível

O `PennyShapedDiagnosticAdapter` existe desde a 11.8D:

```text
include/lot/PennyShapedDiagnosticAdapter.hpp
src/lot/PennyShapedDiagnosticAdapter.cpp
```

Entradas exigidas:

| Campo | Unidade | Estado BUZ29 atual |
|---|---:|---|
| `young_modulus_Pa` | Pa | Ausente no candidato |
| `poisson_ratio` | adimensional | Ausente no candidato |
| `viscosity_Pa_min` | Pa.min | Ausente no candidato |
| `flow_rate_m3_min` | m3/min | Ausente no candidato |
| `elapsed_since_opening_min` | min | Requer revisão semântica |
| `wellbore_pressure_Pa` | Pa | Requer seleção/amostragem |
| `sigma_theta_compression_positive_Pa` | Pa | Ausente no output legado direto |
| `volume_multiplier` | adimensional | Default conhecido, mas não valida BUZ29 |

Saídas do adapter:

```text
plane_strain_modulus_Pa
opening_m
radius_m
pressure_factor
fracture_volume_proxy_m3
```

## Writer disponível

O `PennyShapedDiagnosticWriter` existe desde a 11.10G:

```text
include/lot/PennyShapedDiagnosticWriter.hpp
src/lot/PennyShapedDiagnosticWriter.cpp
```

Ele consome uma entrada diagnóstica estruturada e emite JSON/CSV em memória,
preservando campos de origem em 1 rad e equivalentes 2π com `source`
explícito.

## Lacunas adapter → writer

O adapter produz `fracture_volume_proxy_m3`; o writer espera o contrato de
saída mais explícito:

```text
fracture_volume_proxy_1rad_m3
fracture_volume_equivalent_2pi_m3
fracture_volume_equivalent_2pi_source
solid_volume_1rad_m3
solid_volume_equivalent_2pi_m3
solid_volume_equivalent_2pi_source
```

Um runner futuro pode mapear `fracture_volume_proxy_m3` para
`fracture_volume_proxy_1rad_m3` somente como saída diagnóstica, preservando o
caveat `PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED`.

A lacuna principal é `solid_volume_1rad_m3`: ela não vem do adapter. Um runner
futuro deve preencher esse campo somente se houver origem documentada; caso
contrário, deve usar valor explícito e caveatado como não aplicável ou bloqueado
por contrato futuro.

## Estado BUZ29 candidato

O candidato existe em:

```text
cases/validation/non_pkn/buz29_penny_candidate.yaml
```

Estado:

```text
adapter_ready = false
partial_adapter_ready = true
physically_validated = false
legacy_equivalent = false
active_simulation_case = false
```

O candidato contém evidência consumível de pressão e abertura, mas não contém
todos os campos necessários para execução adapter-ready.

## Riscos

- Selecionar uma amostra de pressão errada para `wellbore_pressure_Pa`.
- Tratar `opening_time_min` como `elapsed_since_opening_min` sem regra temporal.
- Usar `sigmaTheta` inexistente como se fosse disponível.
- Promover o volume proxy de 1 rad a volume físico total sem caveat.
- Confundir writer opt-in com runner runtime oficial.
- Alterar `lot-pkn` ao tentar encaixar a rota não-PKN.

## Decisão/gate

Decisão da 11.10H:

```text
decision = NON_PKN_DIAGNOSTIC_RUNNER_SPEC_PARTIAL
runner_implementation_allowed_now = false
buz29_runtime_execution_allowed = false
lot_pkn_impact_allowed = false
recommended_next_phase = PHASE11_10I_SPECIFY_NON_PKN_DIAGNOSTIC_RUNNER
```

A decisão é parcial porque adapter e writer existem e estão isolados, mas a
execução real BUZ29 segue bloqueada por inputs parciais e semânticas ainda
diferidas.

## Restrições obrigatórias para runner futuro

Qualquer runner futuro deve ser opt-in, isolado, fora de lot-pkn, sem alterar
PknModel, PknRunner, parser ou schemas, salvo autorização explícita de fase
posterior.

O runner futuro deve:

- chamar `PennyShapedDiagnosticAdapter` apenas com entradas explicitamente
  fornecidas;
- converter a saída do adapter para o contrato do writer sem perder a origem
  1 rad;
- preservar `physically_validated=false`;
- preservar `legacy_equivalent=false`;
- preservar `active_simulation_case=false` até novo gate explícito;
- bloquear BUZ29 se campos adapter-ready estiverem ausentes;
- não criar rota oficial `lot-sim`.

## O que ainda não pode ser feito

A execução runtime BUZ29-PENNY permanece proibida nesta fase. A rota continua
diagnóstica, sem validação física e sem equivalência com legado.

Também permanecem proibidos:

- implementação de runner na 11.10H;
- alteração de C++;
- alteração de parser/schema/CLI;
- alteração de `PknModel` ou `PknRunner`;
- execução BUZ29-PENNY;
- uso do candidato BUZ29 como validação física;
- declaração de equivalência com LOT_Tese.

## Próxima fase recomendada

```text
PHASE11_10I_SPECIFY_NON_PKN_DIAGNOSTIC_RUNNER
```

A 11.10I deve especificar o contrato do runner futuro, ainda sem implementá-lo,
ou bloquear a especificação se decidir que as lacunas de entrada/semântica
precisam ser resolvidas antes.

## Reconciliação da Fase 11.10I

A Fase 11.10I substitui a direção de "runner não-PKN" como rota paralela por
uma decisão arquitetural mais estreita:

```text
UNIFIED_LOT_FRACTURE_RUNTIME_SELECTED
PKN_DEFAULT_FRACTURE_MODEL
PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY
UNSUPPORTED_FRACTURE_MODELS_BLOCKED
```

O futuro contrato deve introduzir `lot.fracture.fracture_model` como seletor
de modelo. Quando ausente, o default deve continuar PKN. `PENNY_SHAPED`
continua opt-in explícito, diagnóstico, não fisicamente validado e não
equivalente ao legado. A 11.10I não implementa runner, parser, schema ou
execução BUZ29-PENNY.
## Atualização 11.10J — runner paralelo não é o caminho principal

A Fase 11.10J consolida a evolução recomendada como um selector guard dentro de
uma rota LOT/fracture unificada. O antigo conceito de runner não-PKN paralelo
permanece subordinado ao guard `lot.fracture.fracture_model`, com PKN default,
`PENNY_SHAPED` opt-in e modelos não suportados bloqueados.
