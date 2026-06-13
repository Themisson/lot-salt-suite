# APB/LOT extended regression suite

## Resumo executivo

A fase `APB_LOT_RUN_EXTENDED_REGRESSION_SUITE` valida os contratos modernos
APB/LOT adicionados na fase anterior. A validacao e contratual: nao executa
um solver APB completo, nao altera PKN e nao toca na rota BUZ29/PENNY.

## Escopo validado

- `input.yaml`, `input.json` e `input.dat` derivam `input_out.json`;
- caminho de output explicito tem prioridade;
- `output_format = json` e `legacy_dat` permanecem aceitos;
- `leakoff_coupling_mode = volume_balance` e `legacy_nodal_force` permanecem
  aceitos;
- `salt_displacement_mode = pre_iterative` e `legacy_inside_newton` permanecem
  aceitos;
- modos invalidos sao rejeitados pela suite de contrato;
- o JSON minimo contem `metadata`, `configuration`, `time_series`, `layers`,
  `annulars`, `summary` e `caveats`.

## Resultado

```text
APB_LOT_EXTENDED_REGRESSION_PASSED
MODERN_APB_LOT_MODES_VALID
LEGACY_APB_LOT_MODES_PRESERVED
JSON_OUTPUT_CONTRACT_VALID
PKN_BEHAVIOR_NOT_CHANGED
BUZ29_PENNY_NOT_EXECUTED
```

## Limites

`runtime_metrics_available = false` e `contract_validation_only = true`.
Portanto, a fase nao declara validacao fisica APB. A proxima etapa deve usar
um caso APB real quando o runner correspondente existir.

## Proxima fase recomendada

```text
APB_LOT_VALIDATE_MODERN_MODES_WITH_REAL_APB_CASE
```

## Resultado da fase de caso real

A fase recomendada foi executada e encontrou o bloqueio esperado de runtime:

```text
APB_LOT_REAL_CASE_EXECUTION_BLOCKED_BY_MISSING_RUNNER
REAL_CASE_RUNNER_INTEGRATION_REQUIRED
```

O contrato permanece valido, mas `runtime_metrics_available = false` continua
verdadeiro. Nenhum `*_out.json` efetivo foi fabricado.
