# APB/LOT real runner integration

## Resumo executivo

A fase `APB_LOT_IMPLEMENT_REAL_CASE_RUNNER_INTEGRATION` conecta uma rota
controlada de runtime para:

```text
lot-sim run --mode apb-lot
```

Essa rota chama `ApbLotJsonOutputWriter`, gera `*_out.json` real para fixtures
modernas controladas e exercita os contratos:

```text
APB_LOT_REAL_CASE_RUNNER_IMPLEMENTED
LOT_SIM_APB_LOT_MODE_AVAILABLE
MODERN_JSON_OUTPUT_GENERATED
VOLUME_BALANCE_EXERCISED
PRE_ITERATIVE_EXERCISED
LEGACY_MODES_PRESERVED
PKN_BEHAVIOR_NOT_CHANGED
BUZ29_PENNY_NOT_EXECUTED
```

A implementação e deliberadamente limitada. Ela não é solver APB completo, não
é validação física APB/LOT, não executa BUZ29/PENNY e não altera `lot-pkn`.

## O que foi implementado

Foi criado `lss::lot::ApbLotRunner`, um runner C++ controlado e separado do
`PknRunner`. Ele consome `CaseData.apb_lot`, aplica os helpers de modo já
existentes e gera um documento `apb_lot_output_v1`.

O CLI agora aceita:

```text
lot-sim run --case <case.yaml> --mode apb-lot --output <dir>
```

O modo `apb-lot`:

1. lê o YAML pelo parser C++;
2. respeita `apb_lot.output_format`;
3. respeita `apb_lot.output_path` quando informado;
4. aplica `volume_balance` para o termo controlado de leakoff;
5. aplica `pre_iterative` para o plano controlado de deslocamento de sal;
6. escreve `*_out.json` via `ApbLotJsonOutputWriter`;
7. preserva `legacy_dat`, `legacy_nodal_force` e `legacy_inside_newton` como
   modos de contrato.

## Saida JSON

O arquivo gerado contem:

```text
metadata
configuration
time_series
layers
annulars
summary
caveats
```

A regra de nome segue:

```text
<input_stem>_out.json
```

quando `apb_lot.output_path` nao e informado. Quando `output_path` existe, o
caminho explicito e resolvido dentro do diretório passado por `--output`.

## Fixtures executaveis

As fixtures parseaveis ficam em:

```text
tests/fixtures/comparison/phase_apb_lot_real_runner/
```

| Fixture | Papel |
|---|---|
| `apb_lot_modern_controlled.yaml` | executa `json + volume_balance + pre_iterative` |
| `apb_lot_modern_explicit_output.yaml` | valida `apb_lot.output_path` |
| `apb_lot_legacy_controlled.yaml` | preserva modos legados sem gerar JSON moderno |
| `apb_lot_invalid_mode.yaml` | garante rejeicao de modo invalido |

## Limites

Esta fase nao valida equivalencia com o legado, nao calcula uma resposta fisica
APB completa e nao cria acoplamento sal/APB iterativo. A saida e efetiva para
contrato/runtime, mas permanece diagnóstica e controlada.

`lot-pkn` continua sendo executado pela rota anterior. `PknModel`,
`PknRunner`, BUZ29/PENNY, `legacy/`, `legance/`, `external/saltcreep/`,
baselines e `postprocess/` permanecem fora do escopo.

## Ferramenta de validacao

A ferramenta:

```text
tools/validate_apb_lot_real_runner_integration.py
```

executa os fixtures controlados pelo CLI e confirma:

```text
modern_case_executed = true
legacy_case_accepted = true
json_output_generated = true
json_has_effective_data = true
output_name_rule_valid = true
explicit_output_path_valid = true
volume_balance_exercised = true
pre_iterative_exercised = true
pkn_behavior_changed = false
buz29_penny_executed = false
```

## Proxima fase recomendada

```text
APB_LOT_VALIDATE_REAL_RUNNER_NUMERICAL_SEMANTICS
```

Essa próxima fase deve revisar a semântica numérica do runner APB/LOT
controlado antes de qualquer expansão para solver APB físico ou comparação com
legado.
