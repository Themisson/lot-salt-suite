# APB/LOT leakoff volume balance mode

## Resumo executivo

Foram formalizados dois modos de acoplamento do leakoff:

```text
legacy_nodal_force
volume_balance
```

`volume_balance` aplica explicitamente:

```text
dV_coupled = dV + dV_leakoff
```

## Convencao de sinal

O contrato documenta que `dV_leakoff_m3` positivo ou negativo deve seguir a
convencao do chamador. Nos testes, leakoff que retira volume hidraulico e
representado por contribuicao negativa, reduzindo o volume efetivo que pressuriza
o anular.

## Compatibilidade

`legacy_nodal_force` preserva `dV` sem somar o termo de leakoff, representando o
modo legado para comparacao. O PKN padrao nao foi alterado.

## Regressao estendida APB/LOT

A fase `APB_LOT_RUN_EXTENDED_REGRESSION_SUITE` validou os modos:

```text
volume_balance
legacy_nodal_force
```

Tambem confirmou que `force_balance_unknown` e rejeitado no contrato de
regressao. Status: `MODERN_APB_LOT_MODES_VALID` e
`LEGACY_APB_LOT_MODES_PRESERVED`.

## Gate de caso real

A validacao `APB_LOT_VALIDATE_MODERN_MODES_WITH_REAL_APB_CASE` auditou a
disponibilidade de um runner APB/LOT real. Como nao ha runner moderno integrado,
`volume_balance` permanece contrato/helper e ainda nao foi exercitado por um
solver APB runtime.

Status: `APB_LOT_REAL_CASE_EXECUTION_BLOCKED_BY_MISSING_RUNNER`.
