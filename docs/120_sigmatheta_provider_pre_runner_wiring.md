# Fase D — wiring do provider sigma_theta ao diagnostic pre-runner

## Resumo executivo

A Fase D conecta `PostDrillingSigmaThetaProvider` ao
`FractureGateDiagnosticPreRunner`. A montagem direta dos valores de
`sigma_theta_diagnostic_input` passa por um provider centralizado antes de
alimentar `SigmaThetaInitialStateGuard` e
`PressureSigmaThetaFractureCriterionGuard`.

Status:

```text
SIGMATHETA_PROVIDER_WIRED_TO_DIAGNOSTIC_PRE_RUNNER
```

## O que mudou

- `FractureGateDiagnosticPreRunner` chama
  `evaluate_post_drilling_sigma_theta(...)` quando
  `sigma_theta_diagnostic_input.enabled=true`.
- `FractureGateDiagnosticPreRunner` tambem chama
  `evaluate_post_drilling_sigma_theta(...)` quando
  `sigma_theta_provider.enabled=true` e a fonte e
  `ELASTIC_INITIAL_WELLBORE_STATE`.
- A fonte diagnostica continua aceita.
- `sigma_theta_provider` e `sigma_theta_diagnostic_input` sao mutuamente
  exclusivos quando habilitados.
- A semantica de sinal/referencial permanece a mesma dos guards atuais.
- `runtime_dispatch_enabled` permanece falso.

## O que nao mudou

- Nao ha dispatch fisico.
- `PknModel` e `PknRunner` nao sao chamados pelo gate.
- `PennyShapedDiagnosticAdapter` nao e chamado pelo gate.
- PKN permanece o default retrocompativel.
- BUZ29-PENNY permanece bloqueado.

## Proxima fase

```text
MASTER_PHASE_E_VALIDATE_SIGMATHETA_PROVIDER_CONTROLLED_CASES
```
