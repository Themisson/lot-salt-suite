# Diagnostic pre-runner runtime gate (Fase 11.10Y)

## Resumo executivo

A Fase 11.10Y implementa apenas o gate diagnostico pre-runner opt-in. Ela nao
habilita dispatch fisico, nao altera o comportamento do PKN e nao executa
BUZ29-PENNY.

O ponto de integracao e propositalmente antes do runner fisico:

```text
parse_yaml
-> evaluate_fracture_gate_diagnostic_pre_runner
-> write diagnostic_fracture_gate.json, se habilitado
-> run_pkn_case
-> write_pkn_result
```

Quando o diagnostico estiver habilitado e ainda faltar estado inicial
sigma_theta, o resultado esperado e bloqueio diagnostico, nao execucao de
fratura.

## Configuracao opt-in

O diagnostico fica desligado por default. A rota so e avaliada quando o caso
declara explicitamente:

```yaml
lot:
  fracture:
    fracture_gate_diagnostics:
      enabled: true
      mode: pre_runner
      dispatch_runtime_enabled: false
```

Tambem e aceito `mode: diagnostic_only`. O campo
`dispatch_runtime_enabled: true` e rejeitado nesta fase.

## Contrato de saida

Quando habilitado, o diagnostico escreve um arquivo isolado no diretorio de
saida:

```text
diagnostic_fracture_gate.json
```

Esse arquivo nao substitui `result.json`, nao altera `timeseries.csv` e nao e
usado pelo `PknModel`. Campos principais:

```text
fracture_gate_diagnostics_enabled
mode
dispatch_runtime_enabled
selected_fracture_model
gate_status
dispatch_status
fracture_initiated
blocking_reasons
physically_validated
legacy_equivalent
buz29_execution_allowed
pkn_model_called_by_diagnostic
penny_adapter_called_by_diagnostic
```

## Estado esperado com sigma_theta ausente

A rota pre-runner ainda nao possui estado inicial sigma_theta fisicamente
definido. Portanto, com o diagnostico habilitado, o status esperado e:

```text
FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE
```

Esse bloqueio e intencional. Ele confirma que o wiring esta acessivel sem
promover execucao fisica incompleta.

## O que nao muda

- `PknModel` nao e chamado pelo diagnostico.
- `PknRunner` nao recebe nova logica.
- `PennyShapedDiagnosticAdapter` nao e chamado.
- `volumetric_balance` e `pkn_direct` permanecem inalterados.
- BUZ29-PENNY continua bloqueado.
- O comportamento padrao de `lot-sim run --mode lot-pkn` permanece inalterado
  quando `fracture_gate_diagnostics.enabled` nao e declarado.

## Status registrado

```text
PHASE11_10Y_DIAGNOSTIC_PRE_RUNNER_RUNTIME_GATE_IMPLEMENTED
DIAGNOSTIC_PRE_RUNNER_OPT_IN_IMPLEMENTED
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
PKN_BEHAVIOR_NOT_CHANGED
BUZ29_EXECUTION_BLOCKED
```

## Proxima fase recomendada

```text
PHASE11_10Z_ADD_DIAGNOSTIC_PRE_RUNNER_CASE_FIXTURES
```

A proxima fase deve criar fixtures/casos diagnosticos pequenos para exercitar
o JSON pre-runner sem liberar dispatch fisico.

## Atualizacao 11.10Z — fixtures do diagnostico pre-runner

A Fase 11.10Z adiciona fixtures versionadas em:

```text
tests/fixtures/comparison/phase11_10z/
```

Essas fixtures cobrem default disabled, PKN diagnostico, `PENNY_SHAPED`
diagnostico, `dispatch_runtime_enabled=true` invalido, mode invalido e bloqueio
por sigma_theta inicial ausente. Elas sao contrato diagnostico, nao casos de
producao e nao executam BUZ29-PENNY.

## Atualizacao 11.11A — comportamento controlado validado

A 11.11A confirma, a partir das fixtures da 11.10Z, que o diagnostico pre-runner
e opt-in, que o default disabled permanece valido, que erros esperados sao
rejeitados e que sigma_theta inicial ausente bloqueia o gate em vez de executar
fratura.

## Atualizacao 11.11B — regressao PKN disabled/enabled

A 11.11B confirma que habilitar `fracture_gate_diagnostics` em copia temporaria
dos casos LOT-PKN protegidos nao altera `result.json` nem `timeseries.csv`. O
diagnostico continua isolado em `diagnostic_fracture_gate.json`, sem liberar
dispatch fisico.

## Atualizacao 11.11C — readiness conservadora

A 11.11C registra `RUNTIME_WIRING_READY_FOR_LIMITED_GATE_SPEC`. A decisao
autoriza apenas a especificacao de uma integracao limitada futura; o dispatch
fisico permanece desabilitado e BUZ29-PENNY segue bloqueado.
