# 139 — BUZ29 Penny adapter input completion

**Status:** Partial inputs recorded |
**Phase:** `PHASE_COMPLETE_BUZ29_PENNY_ADAPTER_INPUTS`

## Executive Summary

This phase audits the real BUZ29/PENNY candidate against the actual
`PennyShapedDiagnosticAdapter` API. It does not execute BUZ29/PENNY and does
not fill missing physical values from synthetic fixtures.

```text
input_status = BUZ29_PENNY_ADAPTER_INPUTS_STILL_PARTIAL
all_required_inputs_complete = false
resolved_input_created = false
diagnostic_only = true
physically_validated = false
legacy_equivalent = false
runtime_dispatch_enabled = false
```

A fase completa ou bloqueia explicitamente os inputs do
PennyShapedDiagnosticAdapter para BUZ29/PENNY. Ela não inventa valores físicos,
não habilita dispatch físico, não valida BUZ29 fisicamente e não declara
equivalência com legado.

## Required Adapter Fields

The real adapter consumes:

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

## Field Matrix

| Field | Status | Use for BUZ29 diagnostic? | Source |
|---|---|---:|---|
| `young_modulus_Pa` | `MISSING` | false | candidate/docs 75 |
| `poisson_ratio` | `MISSING` | false | candidate/docs 75 |
| `viscosity_Pa_min` | `MISSING` | false | candidate/docs 75 |
| `flow_rate_m3_min` | `MISSING` | false | candidate/docs 75 |
| `elapsed_since_opening_min` | `AMBIGUOUS_SEMANTICS` | false | opening marker exists, diagnostic current time is not selected |
| `wellbore_pressure_Pa` | `AMBIGUOUS_SEMANTICS` | false | pressure history exists, single adapter sample is not selected |
| `sigma_theta_compression_positive_Pa` | `MISSING` | false | BUZ29 legacy output does not export sigmaTheta |
| `volume_multiplier` | `AVAILABLE_FROM_DIAGNOSTIC_SOURCE` | true | diagnostic 1 rad/2pi contract, empirical multiplier `10.0` |

## Blocking Fields

```text
young_modulus_Pa
poisson_ratio
viscosity_Pa_min
flow_rate_m3_min
sigma_theta_compression_positive_Pa
```

## Ambiguous Fields

```text
elapsed_since_opening_min
wellbore_pressure_Pa
```

`opening_time_min = 10.4` is a legacy event marker. It is not the adapter
duration `elapsed_since_opening_min` until a diagnostic current time is chosen.

The pressure history is consumable evidence, but it is not yet a single
`wellbore_pressure_Pa` input with selected time and explicit pressure semantics.

## Resolved Input

No complete resolved input fixture was created in this phase. Creating one
would require inventing at least one physical value or making an unsupported
semantic selection.

## Forbidden Substitutions

```text
do not copy values from penny_shaped_synthetic_minimal.yaml into BUZ29
do not use volume_multiplier = 2pi automatically
do not use pressure history as a single adapter pressure without selected diagnostic time
do not derive sigma_theta without compression-positive source
```

## Next Step

```text
PHASE_RESOLVE_BUZ29_PENNY_BLOCKING_ADAPTER_FIELDS
```
