# Decisao de defaults modernos APB/LOT

## Decisao

Classificacao:

```text
APB_LOT_MODERN_MODES_READY_AS_DEFAULT_FOR_NEW_CASES
```

Para novos contratos APB/LOT, os defaults diagnosticos sao:

```text
output_format = json
output_suffix = _out.json
leakoff_coupling_mode = volume_balance
salt_displacement_mode = pre_iterative
```

Modos legados permanecem disponiveis:

```text
legacy_dat
legacy_nodal_force
legacy_inside_newton
```

## Garantia

O PKN permanece retrocompativel. A decisao nao executa BUZ29/PENNY, nao altera
`PknModel` e nao declara validacao fisica APB/LOT completa.

## Regressao estendida APB/LOT

A suite `APB_LOT_RUN_EXTENDED_REGRESSION_SUITE` confirmou a decisao anterior:

```text
APB_LOT_EXTENDED_REGRESSION_PASSED
APB_LOT_MODERN_MODES_READY_AS_DEFAULT_FOR_NEW_CASES
```

O proximo gate e validar esses modos contra um caso APB real, quando houver
runner moderno correspondente.

## Dependencia para default operacional

O gate de caso real bloqueou a promocao operacional dos modos modernos. Eles
continuam recomendados como contrato, mas nao como default fisico validado,
porque ainda nao ha runner APB/LOT moderno consumindo `volume_balance` e
`pre_iterative`.

Status:

```text
APB_LOT_REAL_CASE_EXECUTION_BLOCKED_BY_MISSING_RUNNER
```
