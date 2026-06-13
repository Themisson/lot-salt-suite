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
