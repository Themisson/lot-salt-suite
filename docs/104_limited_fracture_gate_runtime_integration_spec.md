# Fase 11.11D — especificacao da integracao runtime limitada do fracture gate

## Resumo

A Fase 11.11D especifica a proxima integracao limitada do fracture gate no
runtime. A fase e documental/analitica: nao altera C++, nao habilita dispatch
fisico, nao executa BUZ29-PENNY e nao transforma PennyShaped em modelo runtime
fisicamente validado.

Status:

```text
LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_SPECIFIED
```

## Ponto de integracao permitido

O ponto permitido continua sendo:

```text
after parse/validate and before run_pkn_case
```

O diagnostico deve ser ativado somente por:

```text
lot.fracture.fracture_gate_diagnostics.enabled = true
```

E deve preservar:

```text
lot.fracture.fracture_gate_diagnostics.dispatch_runtime_enabled = false
```

## Escopo permitido para a proxima implementacao

A proxima fase pode implementar apenas integracao diagnostica limitada:

- executar o fracture gate como diagnostico opt-in;
- gravar `diagnostic_fracture_gate.json` quando habilitado;
- preservar `result.json` e `timeseries.csv`;
- manter default disabled;
- manter `dispatch_runtime_enabled=true` rejeitado;
- manter BUZ29-PENNY bloqueado.

## Mudancas proibidas

```text
do_not_change_PknModel
do_not_change_PknRunner
do_not_enable_physical_dispatch
do_not_execute_BUZ29_PENNY
do_not_call_PennyShaped_adapter_as_runtime_physical_model
```

## Gates obrigatorios para a proxima fase

```text
default_disabled_preserves_outputs
diagnostic_enabled_preserves_result_json
diagnostic_enabled_preserves_timeseries_csv
diagnostic_json_isolated
dispatch_runtime_enabled_true_rejected
BUZ29_execution_blocked
```

## Status conservador

```text
implementation_allowed_next = true
runtime_dispatch_allowed_next = false
runtime_physical_dispatch_allowed_next = false
buz29_execution_allowed_next = false
pkn_behavior_change_allowed = false
penny_runtime_allowed = false
penny_diagnostic_only = true
```

## Proxima fase recomendada

```text
PHASE11_11E_IMPLEMENT_LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION
```
