# Diagnostic pre-runner controlled validation (Fase 11.11A)

## Resumo executivo

A 11.11A valida apenas o comportamento controlado do diagnostico pre-runner.
Ela nao valida fisicamente BUZ29, nao habilita dispatch fisico e nao declara
equivalencia com legado.

## Contexto pos-11.10Z

A 11.10Y implementou o diagnostico pre-runner opt-in. A 11.10Z adicionou
fixtures pequenas para cobrir os cenarios minimos. A 11.11A consome essas
fixtures e confirma que o contrato diagnostico esta coerente.

## Casos controlados analisados

```text
diagnostic_disabled_default.yaml
diagnostic_enabled_pkn_pre_runner.yaml
diagnostic_enabled_penny_pre_runner.yaml
diagnostic_dispatch_true_invalid.yaml
diagnostic_invalid_mode.yaml
diagnostic_missing_sigmatheta_blocks.yaml
```

## Comportamento opt-in

O diagnostico e considerado habilitado apenas quando a fixture declara
`fracture_gate_diagnostics.enabled: true`. Nesse caso, a expectativa e saida
diagnostica isolada, sem alteracao fisica do PKN.

## Comportamento default disabled

Quando o bloco `fracture_gate_diagnostics` esta ausente, o diagnostico permanece
desabilitado e nenhum arquivo diagnostico e esperado.

## Erros esperados

Dois cenarios sao intencionalmente invalidos:

- `dispatch_runtime_enabled: true`;
- `mode: runtime`.

Esses casos validam que a fase continua bloqueando dispatch fisico.

## Bloqueio por sigma_theta ausente

Com diagnostico habilitado e sem estado inicial sigma_theta, o status esperado e:

```text
FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE
FRACTURE_DISPATCH_NOT_ALLOWED
```

## Saida diagnostica isolada

A presenca esperada de diagnostico nos cenarios opt-in nao altera `result.json`
nem `timeseries.csv`. A comparacao fisica detalhada fica reservada para a
11.11B.

## Proxima fase recomendada

```text
PHASE11_11B_COMPARE_PKN_RESULTS_WITH_DIAGNOSTIC_DISABLED_ENABLED
```
