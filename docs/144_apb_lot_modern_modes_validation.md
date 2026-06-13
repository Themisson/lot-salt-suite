# Validacao dos modos modernos APB/LOT

## Resumo executivo

Foram criadas fixtures controladas para validar a combinacao:

```text
output_format = json
leakoff_coupling_mode = volume_balance
salt_displacement_mode = pre_iterative
```

Classificacao esperada:

```text
APB_LOT_MODERN_MODES_VALID
```

## Fixtures

| Fixture | Finalidade |
|---|---|
| `modern_json_volume_balance_pre_iterative.yaml` | modo moderno completo |
| `legacy_dat_nodal_force_inside_newton.yaml` | modo legado comparavel |
| `invalid_leakoff_mode.yaml` | rejeicao de leakoff invalido |
| `invalid_salt_displacement_mode.yaml` | rejeicao de deslocamento invalido |

As fixtures sao contratos diagnosticos, nao validacao fisica APB.

## Regressao estendida APB/LOT

A fase `APB_LOT_RUN_EXTENDED_REGRESSION_SUITE` adicionou fixtures dedicadas em:

```text
tests/fixtures/comparison/phase_apb_lot_extended_regression/
```

Resultado:

```text
APB_LOT_EXTENDED_REGRESSION_PASSED
contract_validation_only = true
runtime_metrics_available = false
```

O comportamento PKN permanece inalterado.
