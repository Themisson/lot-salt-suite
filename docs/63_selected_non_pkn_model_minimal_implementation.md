# Phase 11.8A selected non-PKN minimal implementation

## Resumo executivo

A Fase 11.8A implementa um nucleo C++ minimo e isolado para a trilha
`PENNY_SHAPED`, conforme a auditoria matematica da 11.7B e a especificacao
YAML/IO da 11.7C.

```text
status = SELECTED_NON_PKN_MINIMAL_MODEL_IMPLEMENTED
selected_track = PENNY_SHAPED
runtime_integration = false
parser_schema_changed = false
physical_validation = false
```

## Arquivos C++ criados

- `include/lot/PennyShapedModel.hpp`
- `src/lot/PennyShapedModel.cpp`
- `tests/cpp/test_penny_shaped_model.cpp`

## API implementada

```cpp
struct PennyShapedInput {
  double young_modulus_Pa;
  double poisson_ratio;
  double viscosity_Pa_min;
  double flow_rate_m3_min;
  double elapsed_since_opening_min;
  double wellbore_pressure_Pa;
  double sigma_theta_compression_positive_Pa;
  double volume_multiplier;
};

PennyShapedResult evaluate_penny_shaped_model(const PennyShapedInput& input);
```

## Formula auditada

O nucleo implementa:

```text
E' = E / (1 - nu^2)
w0 = 3.65 * ((mu^2 * Qinj^3) / E'^2)^(1/9) * time^(1/9)
R = 0.572 * ((E' * Qinj^3) / mu)^(1/9) * time^(4/9)
pressureFactor = pw / sigmaTheta
fracture_volume_proxy = volume_multiplier * (w0/2)^2 * R * pi * pressureFactor
```

## Escopo deliberadamente excluido

Esta fase nao:

- altera parser;
- altera schemas;
- cria YAML BUZ29 runtime;
- conecta ao CLI;
- altera `PknModel`;
- altera `PknRunner`;
- substitui `lot-pkn`;
- valida BUZ29;
- declara equivalencia com LOT_Tese.

## Interpretacao

O nucleo e uma base tecnica testavel para formulas penny-shaped isoladas. Ele
nao e ainda um modelo LOT/APB completo, porque BUZ29 depende de historico de
pressao, criterio sigmaTheta, estado APB/sal e convencoes volumetricas legadas.

## Proxima fase recomendada

```text
PHASE11_8B_NON_PKN_MODEL_ADAPTER_OR_CASE_GATE
```

Antes de qualquer integracao runtime, a proxima fase deve decidir se o nucleo
sera usado por um adapter diagnostico, por um caso YAML oficial futuro ou apenas
mantido como biblioteca de formula isolada.

## Resultado da Fase 11.8B

A decisão de integração selecionou:

```text
PENNY_ADAPTER_OPT_IN_SELECTED
selected_integration_path = diagnostic_adapter
```

Isso mantém o núcleo fora do `lot-pkn` e direciona a próxima fase para uma
especificação de adapter diagnóstico.

## Resultado da Fase 11.8C

A especificação do adapter diagnóstico foi registrada em
`docs/65_penny_diagnostic_adapter_spec.md`, com fixture versionada em
`tests/fixtures/comparison/phase11_8c_penny_adapter_input.yaml`.

```text
status = PENNY_ADAPTER_SPEC_VALID
runtime_integration = false
parser_schema_changed = false
buz29_validation = false
```

Ela prepara a Fase 11.8D para criar um adapter C++ opt-in em torno do núcleo
isolado, ainda sem conexão com `PknModel`, `PknRunner`, CLI ou parser.
