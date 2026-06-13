# APB/LOT real runner numerical semantics

## Resumo executivo

A fase `APB_LOT_VALIDATE_REAL_RUNNER_NUMERICAL_SEMANTICS` validou a semantica
numerica minima da rota controlada:

```text
lot-sim run --mode apb-lot
```

O resultado da validacao foi:

```text
APB_LOT_REAL_RUNNER_NUMERICAL_SEMANTICS_VALID
FINITE_VALUES_VALID
TIME_SERIES_NON_EMPTY
SUMMARY_CONSISTENT
VOLUME_BALANCE_SEMANTICS_VALID
PRE_ITERATIVE_SEMANTICS_VALID
LEGACY_MODES_PRESERVED
PKN_BEHAVIOR_NOT_CHANGED
BUZ29_PENNY_NOT_EXECUTED
```

A fase confirma que o runner APB/LOT controlado gera JSON parseavel, com serie
temporal finita, tempo monotono, resumo consistente e exercicio efetivo dos
modos `volume_balance` e `pre_iterative`.

## Casos executados

| Caso | Modo | Saida esperada | Resultado |
|---|---|---|---|
| `tests/fixtures/comparison/phase_apb_lot_real_runner/apb_lot_modern_controlled.yaml` | `apb-lot` | `apb_lot_modern_controlled_out.json` | executado |
| `tests/fixtures/comparison/phase_apb_lot_real_runner/apb_lot_legacy_controlled.yaml` | `apb-lot` | sem JSON moderno | aceito |

O caso moderno usa `output_format = json`, `leakoff_coupling_mode =
volume_balance` e `salt_displacement_mode = pre_iterative`. O caso legado
permanece aceito para comparacao sem forcar a nova saida JSON.

## Campos numericos reais

O JSON moderno usa os seguintes campos numericos por passo:

```text
time_s
pressure_Pa
delta_pressure_Pa
dV_m3
dV_leakoff_m3
salt_displacement_m
```

O prompt de validacao citava nomes genericos como `dV_total` e
`leakoff_volume`. No contrato implementado, esses conceitos correspondem aos
campos reais `dV_m3` e `dV_leakoff_m3`.

## Invariantes validados

| Invariante | Status |
|---|---|
| JSON parseavel | valido |
| Secoes minimas `metadata`, `configuration`, `time_series`, `summary`, `caveats` | valido |
| `time_series.size >= 2` | valido |
| Valores numericos finitos | valido |
| `time_s` monotono | valido |
| `summary.max_pressure_Pa` consistente com a serie | valido |
| `summary.max_delta_pressure_Pa` consistente com a serie | valido |
| `summary.total_leakoff_volume_m3` consistente com `dV_leakoff_m3` | valido |
| Caso legado aceito sem JSON moderno | valido |

## Semantica `volume_balance`

O modo `volume_balance` foi exercitado no runner controlado. A validacao
confirma que:

```text
dV_m3 >= dV_leakoff_m3
dV_leakoff_m3 > 0
summary.total_leakoff_volume_m3 = max(dV_leakoff_m3)
```

Essa verificacao prova coerencia do contrato numerico controlado. Ela nao
valida um balanço APB fisico completo nem equivalencia com o LOT_Tese.

## Semantica `pre_iterative`

O modo `pre_iterative` foi exercitado no runner controlado. A validacao confirma
que `salt_displacement_m` e finito, nao nulo e acompanhado do caveat:

```text
CONTROLLED_PRE_ITERATIVE_SALT_DISPLACEMENT
```

Essa saida representa deslocamento diagnostico controlado, nao acoplamento
iterativo sal/APB.

## Limites

Esta fase registra explicitamente:

```text
controlled_runner = true
physical_validation_claimed = false
pkn_behavior_changed = false
buz29_penny_executed = false
```

Portanto, a rota APB/LOT controlada esta numericamente coerente para contrato e
regressao, mas ainda nao e validacao fisica APB/LOT, nao e equivalencia com
legado e nao habilita BUZ29/PENNY.

## Ferramenta

A ferramenta da fase e:

```text
tools/validate_apb_lot_real_runner_numerical_semantics.py
```

Ela executa os fixtures modernos e legados, le o JSON moderno e gera resumo em
JSON/Markdown sob `results/`, que nao deve ser versionado.

## Proxima fase recomendada

```text
APB_LOT_COMPARE_REAL_RUNNER_MODERN_VS_LEGACY_SEMANTICS
```

A proxima etapa deve comparar semanticas modernas e legadas de forma controlada,
sem declarar equivalencia fisica ate que haja criterios documentados para cada
campo comparado.
