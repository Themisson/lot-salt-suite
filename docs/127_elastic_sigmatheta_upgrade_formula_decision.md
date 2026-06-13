# Decisão da formulação do upgrade elástico sigma_theta

## Resumo executivo

A formulação selecionada para o próximo provider elástico é:

```text
AXISYMMETRIC_ELASTIC_WELLBORE_SOURCE
```

Status:

```text
ELASTIC_SIGMATHETA_UPGRADE_FORMULA_SELECTED
selected_formula = AXISYMMETRIC_ELASTIC_WELLBORE_SOURCE
implementation_allowed_next = true
physically_validated = false
legacy_equivalent = false
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_change_allowed = false
```

## Base da decisão

A Fase A diagnosticou:

```text
has_kirsch_required_fields = false
has_axisymmetric_required_fields = true
has_simplified_required_fields = true
```

Como o contrato atual não expõe `sigma_H`, `sigma_h` e `azimuth_angle_rad`, a
formulação Kirsch completa permanece bloqueada. Como a fonte atual já possui
tensão far-field, pressão de poço e resistência à tração, a rota axisimétrica é
a evolução mínima segura.

## Fórmulas rejeitadas

| Fórmula | Decisão | Motivo |
|---|---|---|
| `KIRSCH_ELASTIC_WELLBORE_SOURCE` | bloqueada | faltam tensões horizontais orientadas e azimute |
| `KEEP_SIMPLIFIED_ELASTIC_SOURCE` | não selecionada | há dados suficientes para uma fonte axisimétrica diagnóstica |

## Fórmula selecionada

```text
AXISYMMETRIC_ELASTIC_WELLBORE_SOURCE
```

A formulação deve permanecer opt-in e diagnóstica. Ela não deve alterar o
comportamento físico do PKN nem habilitar dispatch físico.

## Gate

```text
implementation_allowed_next = true
```

A próxima fase deve planejar a implementação mínima no
`PostDrillingSigmaThetaProvider`, preservando a fonte antiga
`ELASTIC_INITIAL_WELLBORE_STATE`.
