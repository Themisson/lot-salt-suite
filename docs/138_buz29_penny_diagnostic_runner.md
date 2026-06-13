# 138 — BUZ29 Penny Diagnostic Runner

**Status:** Implemented with partial real-input gate |
**Phase:** `PHASE_FIX_BUZ29_PENNY_DIAGNOSTIC_RUNNER`

## Executive Summary

This phase adds an isolated C++ diagnostic runner for BUZ29/PENNY. The runner
connects the existing `PennyShapedDiagnosticAdapter` and
`PennyShapedDiagnosticWriter` only when all adapter-ready inputs are explicitly
available. It blocks partial BUZ29 candidate inputs instead of filling missing
values.

```text
runner_status = BUZ29_PENNY_DIAGNOSTIC_RUNNER_IMPLEMENTED_INPUTS_PARTIAL
synthetic_complete_case_runs = true
partial_inputs_blocked = true
invalid_flags_rejected = true
unsupported_model_rejected = true
buz29_candidate_inputs_complete = false
runtime_dispatch_enabled = false
penny_shaped_runtime_enabled = false
pkn_behavior_changed = false
```

## Mandatory Constraint

O Buz29PennyDiagnosticRunner é diagnóstico e isolado. Ele não habilita dispatch
físico, não transforma PENNY_SHAPED em runtime físico, não valida BUZ29
fisicamente e não declara equivalência com legado.

Quando os inputs do candidato BUZ29/PENNY permanecem parciais, o runner deve
bloquear a execução real e registrar os campos faltantes, em vez de preencher
valores arbitrários.

## Implemented Contract

| Condition | Result |
|---|---|
| `diagnostic_only=false` | rejected |
| `physically_validated=true` | rejected |
| `legacy_equivalent=true` | rejected |
| `runtime_dispatch_enabled=true` | rejected |
| `fracture_model != PENNY_SHAPED` | rejected |
| `adapter_inputs_complete=false` | blocked as partial |
| complete synthetic diagnostic input | adapter + writer executed |

## Fixtures

The versioned fixture set lives in:

```text
tests/fixtures/comparison/phase_buz29_penny_diagnostic_runner/
```

It covers:

```text
runner_valid_complete_inputs.json
runner_partial_inputs_blocked.json
runner_invalid_physically_validated_true.json
runner_invalid_legacy_equivalent_true.json
runner_invalid_runtime_dispatch_true.json
runner_invalid_model_pkn.json
```

## Safety Guarantees

The runner does not include or call `PknModel`, `PknRunner`,
`volumetric_balance`, runtime dispatch, `legacy/`, `legance/` or
`external/saltcreep/`. The only model path exercised by a complete fixture is
the existing diagnostic-only `PennyShapedDiagnosticAdapter`.

## Next Step

```text
PHASE_COMPLETE_BUZ29_PENNY_ADAPTER_INPUTS
```

## Adapter Input Completion Follow-up

The follow-up input audit keeps the real BUZ29/PENNY candidate blocked:

```text
BUZ29_PENNY_ADAPTER_INPUTS_STILL_PARTIAL
blocking_fields_count = 5
ambiguous_fields_count = 2
resolved_input_created = false
```

The runner can execute complete diagnostic inputs, but it must not execute the
real BUZ29/PENNY candidate until the missing and ambiguous adapter fields are
resolved from explicit sources.
