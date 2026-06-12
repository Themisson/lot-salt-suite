# Fase 11.11N — fonte diagnostica explicita de sigma_theta

## Resumo executivo

A 11.11N implementa uma fonte diagnóstica explícita de sigma_theta. Ela não
implementa a fonte física definitiva, não habilita dispatch físico e não valida
BUZ29-PENNY.

Status:

```text
SIGMATHETA_DIAGNOSTIC_SOURCE_IMPLEMENTED
LIMITED_GATE_CAN_BE_FED_DIAGNOSTICALLY
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_NOT_CHANGED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

## Contexto pós-11.11M

A Fase 11.11M manteve o `limited_gate` diagnostico porque faltava fonte runtime
real de sigma-theta inicial/current. A 11.11N nao tenta resolver essa fonte
fisica definitiva. Ela adiciona um contrato opt-in para alimentar o gate com
valores explicitamente diagnosticos.

## Campos YAML

O bloco fica em `lot.fracture.sigma_theta_diagnostic_input`:

```yaml
sigma_theta_diagnostic_input:
  enabled: true
  source: EXPLICIT_DIAGNOSTIC_INPUT
  sigma_theta_initial_compression_positive_Pa: 5000000.0
  sigma_theta_current_compression_positive_Pa: -2000000.0
  sign_convention: COMPRESSION_POSITIVE
  reference_frame: WELLBORE_WALL_TOTAL_STRESS
  state_time: POST_DRILLING_BEFORE_LOT
  physically_validated: false
  legacy_equivalent: false
```

`SYNTHETIC_FIXTURE` tambem e aceito para fixtures controladas. `UNKNOWN`,
convencao de sinal diferente, referencial diferente, `state_time` diferente,
`physically_validated=true` e `legacy_equivalent=true` sao rejeitados.

physically_validated e legacy_equivalent devem permanecer false para entradas
EXPLICIT_DIAGNOSTIC_INPUT e SYNTHETIC_FIXTURE.

## Parser e schema

O parser converte o bloco para `CaseData` sem alterar casos antigos:

```text
campo ausente -> disabled
enabled=false -> disabled
enabled=true -> campos obrigatorios e flags fisicas false
```

O schema foi atualizado de forma opcional e retrocompativel.

## Integração com diagnostic pre-runner

Quando `fracture_gate_diagnostics.enabled=true` e o novo bloco diagnostico esta
habilitado, o pre-runner preenche:

```text
SigmaThetaInitialStateGuard
PressureSigmaThetaFractureCriterionGuard
FractureGateRuntimeWiring
```

O resultado pode chegar a:

```text
FRACTURE_GATE_READY_NOT_REACHED
FRACTURE_GATE_REACHED
FRACTURE_DISPATCH_PKN_ELIGIBLE
FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE
```

Esses status continuam diagnosticos. Eles nao chamam `PknModel`, `PknRunner` ou
`PennyShapedDiagnosticAdapter`.

## Fixtures

Fixtures da fase:

```text
tests/fixtures/comparison/phase11_11n/
```

Elas cobrem default disabled, PKN not reached, PKN reached, PENNY diagnostico
reached e casos invalidos para campos ausentes, flags fisicas e strings
invalidas.

## Limites físicos

Esta fase nao declara validacao fisica, equivalencia com legado ou readiness de
BUZ29-PENNY. A fonte e diagnostica e serve para exercitar o contrato do gate
limitado.

## O que permanece bloqueado

```text
RUNTIME_PHYSICAL_DISPATCH
BUZ29_PENNY_EXECUTION
PENNY_SHAPED_RUNTIME
REAL_SIGMATHETA_PHYSICAL_SOURCE
LEGACY_EQUIVALENCE
```

## Próxima fase recomendada

```text
PHASE11_11O_VALIDATE_SIGMATHETA_DIAGNOSTIC_SOURCE_ON_CONTROLLED_CASES
```

## Resultado da validacao 11.11O

A 11.11O adicionou fixtures controladas e validou:

```text
SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALID
ready_not_reached_case_valid = true
pkn_reached_case_valid = true
penny_reached_diagnostic_case_valid = true
missing_sigmatheta_blocks = true
physically_validated_true_rejected = true
legacy_equivalent_true_rejected = true
runtime_dispatch_enabled = false
```

O estado `Reached` permanece elegibilidade diagnostica do gate. Ele nao chama
runtime fisico PKN/PENNY e nao altera outputs fisicos PKN.

## Decisao 11.11P

A 11.11P consolidou a fonte diagnostica como pronta para uso diagnostico do
gate:

```text
DIAGNOSTIC_SIGMATHETA_GATE_READY
READY_FOR_DIAGNOSTIC_USE
```

Essa decisao nao promove `sigma_theta_diagnostic_input` a fonte fisica, nao
habilita dispatch e nao declara equivalencia com legado.
