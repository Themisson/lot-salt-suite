# Fase 11.11G — validação controlada do limited_gate

## Resumo executivo

A Fase 11.11G valida os casos controlados do modo `limited_gate` criado na
trilha 11.11E/11.11F. O objetivo e confirmar que o gate limitado continua
opt-in, diagnostico e isolado dos outputs fisicos PKN.

A 11.11G valida o limited_gate apenas em modo controlado e diagnóstico. Ela não
habilita dispatch físico, não executa BUZ29-PENNY e não transforma
PENNY_SHAPED em runtime físico.

A validação confirma que os outputs físicos PKN permanecem inalterados e que a
saída diagnóstica permanece isolada.

## Contexto pós-11.11F

A 11.11F criou fixtures pequenas em:

```text
tests/fixtures/comparison/phase11_11f/
```

Status herdado:

```text
LIMITED_GATE_FIXTURES_VALID
PKN_OUTPUTS_UNCHANGED_WITH_LIMITED_GATE
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_change_allowed = false
penny_shaped_runtime_enabled = false
```

## Fixtures validadas

| Fixture | Resultado esperado |
|---|---|
| `limited_gate_disabled_default.yaml` | default disabled sem diagnostico |
| `limited_gate_enabled_pkn.yaml` | opt-in PKN com diagnostico isolado |
| `limited_gate_enabled_penny.yaml` | `PENNY_SHAPED` diagnostic-only |
| `limited_gate_dispatch_true_invalid.yaml` | `dispatch_runtime_enabled=true` rejeitado |
| `limited_gate_missing_sigmatheta_blocks.yaml` | bloqueio por sigma_theta inicial ausente |
| `limited_gate_invalid_model_blocked.yaml` | modelo nao suportado bloqueado |

## Casos controlados

A ferramenta:

```text
tools/validate_phase11_11g_limited_gate_controlled_cases.py
```

valida os fixtures e emite:

```text
LIMITED_GATE_CONTROLLED_CASES_VALID
```

## Comportamento opt-in

`limited_gate` so e considerado quando:

```yaml
lot:
  fracture:
    fracture_gate_diagnostics:
      enabled: true
      mode: limited_gate
      dispatch_runtime_enabled: false
```

## Comportamento default disabled

Quando `fracture_gate_diagnostics` esta ausente, o contrato permanece:

```text
diagnostics_enabled = false
diagnostic_output_expected = false
runtime_dispatch_enabled = false
```

## Bloqueios esperados

```text
DISPATCH_RUNTIME_ENABLED_TRUE_REJECTED
FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE
UNSUPPORTED_FRACTURE_MODEL_BLOCKED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

## Comparação de outputs físicos PKN

A comparação explicita disabled/enabled com `--diagnostic-mode limited_gate`
continua exigindo:

```text
result.json idêntico
timeseries.csv idêntico
diagnostic_fracture_gate.json isolado
```

## Isolamento da saída diagnóstica

O arquivo `diagnostic_fracture_gate.json` pertence ao canal diagnostico. Ele
nao substitui `result.json`, nao altera `timeseries.csv` e nao autoriza dispatch
fisico.

## O que permanece bloqueado

- Dispatch fisico runtime.
- BUZ29-PENNY.
- Validacao fisica BUZ29.
- `PENNY_SHAPED` como runtime fisico.
- Equivalencia com legado.
- Qualquer alteracao no comportamento fisico PKN.

## Próxima fase recomendada

```text
PHASE11_11H_DECIDE_LIMITED_GATE_READINESS_FOR_RUNTIME_USE
```

## Atualização 11.11H — readiness runtime diagnóstico

A Fase 11.11H consolida a validação controlada e registra:

```text
LIMITED_GATE_READY_FOR_DIAGNOSTIC_RUNTIME_USE
LIMITED_GATE_NOT_READY_FOR_PHYSICAL_DISPATCH
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_NOT_CHANGED
```

O `limited_gate` fica aceito como uso runtime diagnóstico seguro, sem liberar
dispatch físico.
