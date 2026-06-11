# Phase 11.8B PennyShaped integration gate

## Resumo executivo

A Fase 11.8B decide como o núcleo `PennyShapedModel` criado na 11.8A deve
evoluir sem contaminar o fluxo `lot-pkn`.

```text
status = PENNY_ADAPTER_OPT_IN_SELECTED
current_core_status = PENNY_SHAPED_MINIMAL_CORE_IMPLEMENTED
selected_integration_path = diagnostic_adapter
recommended_next_phase = PHASE11_8C_PENNY_ADAPTER_SPEC
```

A decisão da 11.8B não valida BUZ29, não declara equivalência com o legado e
não transforma o núcleo penny-shaped em rota oficial do lot-sim. Ela apenas
seleciona o caminho de integração diagnóstica.

## Estado atual do PennyShapedModel

O núcleo atual está em:

- `include/lot/PennyShapedModel.hpp`
- `src/lot/PennyShapedModel.cpp`
- `tests/cpp/test_penny_shaped_model.cpp`

Ele calcula:

- `plane_strain_modulus_Pa`;
- `opening_m`;
- `radius_m`;
- `pressure_factor`;
- `fracture_volume_proxy_m3`.

## Opções de integração

| Opção | Status | Justificativa |
|---|---|---|
| `PENNY_CORE_REMAINS_DIAGNOSTIC_LIBRARY` | `AVAILABLE` | Mantém o núcleo isolado, mas não exercita um contrato de integração. |
| `PENNY_ADAPTER_OPT_IN_SELECTED` | `SELECTED` | Permite adapter diagnóstico isolado sem alterar `lot-pkn`, parser, schema oficial ou casos protegidos. |
| `PENNY_LOT_SIM_MODE_SELECTED` | `BLOCKED` | Exigiria decisões de CLI/parser/schema antes de readiness BUZ29. |
| `PENNY_YAML_ROUTE_SELECTED` | `DEFERRED` | A especificação 11.7C ainda é fixture-only, não schema runtime. |

## Opção selecionada

```text
diagnostic_adapter
```

O adapter diagnóstico deve ser opt-in, receber SI puro, chamar
`PennyShapedModel` e retornar resultado estruturado. Ele não deve depender de
`PknModel`, `PknRunner`, parser oficial ou CLI.

## Opções bloqueadas

- rota oficial `lot-sim`;
- schema runtime oficial;
- adaptação de BUZ29 como caso validado;
- equivalência com LOT_Tese.

## Riscos

- Promover o adapter cedo demais para CLI pode criar uma rota runtime sem
  contrato físico completo.
- BUZ29 ainda depende de histórico de pressão, `sigmaTheta`, APB/sal e
  convenções volumétricas legadas.
- A fixture YAML atual é especificação, não contrato de produção.

## Próxima fase recomendada

```text
PHASE11_8C_PENNY_ADAPTER_SPEC
```

## Resultado da Fase 11.8C

A fase seguinte especificou o contrato do adapter diagnóstico:

```text
status = PENNY_ADAPTER_SPEC_VALID
fixture = tests/fixtures/comparison/phase11_8c_penny_adapter_input.yaml
tool = tools/validate_phase11_8c_penny_adapter_spec.py
```

O contrato continua opt-in e diagnóstico. Ele não valida BUZ29, não altera o
schema oficial e não promove `penny_shaped` a modo runtime do `lot-sim`.
