# Non-PKN model roadmap (Fase 11.6B)

## Resumo executivo

A Fase 11.6B consolida a decisão técnica após a auditoria
`BUZ29-VISCO-first-well` da Fase 11.6A.

Status:

```text
NON_PKN_MODEL_ROADMAP_RECORDED
NEXT_PHASE = PHASE11_6C_PENNY_SHAPED_FORMULATION_AUDIT
```

O caso BUZ29-VISCO-first-well não deve ser convertido para PKN por inferência:
o modelo ativo no legado é `penny-shaped`, a linha PKN está comentada e os
artefatos `.dat` com PKN no nome são output-only. A rota correta é separar
modelos não-PKN da infraestrutura LOT/PKN modern-refined já estabilizada.

## Entradas do gate

| Campo | Valor |
|---|---|
| Fonte auditada | `legance/LOT_Tese/BUZ29-VISCO-first-well.cpp` |
| Status da fonte | `BUZ29_VISCO_FIRST_WELL_SOURCE_FOUND` |
| Modelo ativo | `PENNY_SHAPED` |
| Evidência PKN | `COMMENT_ONLY` |
| Readiness YAML moderno | `BUZ29_VISCO_FIRST_WELL_MODERN_YAML_NOT_READY` |
| Próxima fase recomendada | `PHASE11_6C_PENNY_SHAPED_FORMULATION_AUDIT` |

## Roadmap de rotas não-PKN

| Prioridade | Rota | Driver | Objetivo | Pré-condição | Status |
|---:|---|---|---|---|---|
| 1 | `penny_shaped` | `BUZ29_VISCO_FIRST_WELL` | Auditar e formular modelo LOT penny-shaped moderno antes de qualquer YAML BUZ29. | Documentar formulação legada e contrato de saída esperado. | `PLANNED` |
| 2 | `kgd_circular_elliptical` | variantes BUZ29/Zamora | Auditar KGD circular/elliptical e decidir se entram no escopo moderno. | Separar mecânica KGD de fluido Zamora. | `PLANNED_OPTIONAL` |
| 3 | `zamora_compositional_fluid` | variantes Zamora | Manter Zamora fora do runtime até gate próprio de fluido. | Definir variáveis de estado, unidades e parser. | `BLOCKED_BY_FORMULATION_GATE` |
| 4 | `legacy_output_provenance` | `.dat` BUZ29 PKN | Auditar proveniência dos outputs PKN antes de usá-los como referência. | Encontrar fonte ou script exato que gerou os `.dat`. | `PLANNED` |
| 5 | `modern_refined_buz67d_continuation` | BUZ-67D | Continuar infraestrutura paramétrica BUZ-67D enquanto não-PKN fica fora do runtime. | Nenhum solver novo. | `AVAILABLE_NOW` |

## Gates bloqueadores

```text
NON_PKN_FORMULATION_NOT_IMPLEMENTED
BUZ29_PKN_OUTPUT_PROVENANCE_NOT_ESTABLISHED
ZAMORA_FLUID_MODEL_OUT_OF_SCOPE
```

Esses gates impedem:

- criar YAML moderno BUZ29 a partir de output-only;
- tratar `penny-shaped` como PKN por conveniência;
- misturar Zamora/compositional fluid com migração de modelo de fratura.

## Próxima fase recomendada

A próxima fase técnica recomendada é:

```text
11.6C — penny-shaped formulation audit
```

Essa fase deve auditar a formulação legada penny-shaped, listar entradas e
saídas necessárias, decidir se há escopo para um solver moderno e somente então
planejar implementação C++.

## Fase 11.7A — decisão da trilha

A Fase 11.7A formaliza essa recomendação como decisão de trilha:

```text
status = NEXT_MODEL_TRACK_SELECTED
selected_track = PENNY_SHAPED
recommended_next_phase = PHASE11_7B_LEGACY_MATH_AUDIT_SELECTED_MODEL
```

Essa decisão não altera solver, parser ou casos. Ela apenas impede que BUZ29
seja forçado para `lot-pkn` enquanto a formulação `penny-shaped` não for
auditada.

## Fase 11.7B — auditoria matemática penny-shaped

A Fase 11.7B audita o bloco `idTypeFracture == 3` em
`APB1da::calculateLOTFracturedSaltRock(...)` e registra:

```text
status = SELECTED_MODEL_MATH_AUDITED
selected_track = PENNY_SHAPED
implementation_readiness = MINIMAL_IMPLEMENTATION_READY_DIAGNOSTIC_ONLY
```

A auditoria extrai as relações mínimas de abertura `w0`, raio `R`,
`pressureFactor = pw/sigmaTheta` e volume proxy. Ela não implementa solver novo
e não valida BUZ29.

## Fase 11.7C — especificação YAML/IO penny-shaped

A Fase 11.7C congela uma especificação versionada de YAML/IO para a trilha
`PENNY_SHAPED`:

```text
status = SELECTED_MODEL_YAML_IO_SPECIFIED
schema_status = SPEC_FIXTURE_ONLY_NOT_RUNTIME_SCHEMA
recommended_next_phase = PHASE11_8A_MINIMAL_SELECTED_NON_PKN_MODEL
```

Essa especificação usa fixture em `tests/fixtures/comparison/` e validador
externo em `tools/`. Ela não altera o schema oficial, parser, runtime, CLI ou
casos protegidos.

## Fase 11.8A — núcleo mínimo penny-shaped

A Fase 11.8A implementa um núcleo C++ isolado para a trilha `PENNY_SHAPED`,
com API em `include/lot/PennyShapedModel.hpp` e testes Catch2. O núcleo calcula
`E'`, abertura, raio, `pressureFactor` e volume proxy, mas não é conectado ao
parser, CLI, `PknModel`, `PknRunner` ou casos BUZ29.

```text
status = SELECTED_NON_PKN_MINIMAL_MODEL_IMPLEMENTED
runtime_integration = false
physical_validation = false
```

## Fase 11.8B — gate de integração

A Fase 11.8B seleciona o caminho seguro de integração:

```text
status = PENNY_ADAPTER_OPT_IN_SELECTED
selected_integration_path = diagnostic_adapter
recommended_next_phase = PHASE11_8C_PENNY_ADAPTER_SPEC
```

Rotas de CLI/schema/runtime oficial permanecem bloqueadas ou adiadas. A próxima
fase deve especificar um adapter diagnóstico opt-in antes de qualquer código de
integração adicional.

## Fase 11.8C — especificação do adapter diagnóstico

A Fase 11.8C registra o contrato mínimo do adapter diagnóstico opt-in:

```text
status = PENNY_ADAPTER_SPEC_VALID
fixture = tests/fixtures/comparison/phase11_8c_penny_adapter_input.yaml
recommended_next_phase = PHASE11_8D_PENNY_DIAGNOSTIC_ADAPTER_IMPLEMENTATION
```

A especificação usa os campos reais do `PennyShapedInput`, mantém caveat
explícito de não validação BUZ29 e não cria rota oficial de parser/schema/CLI.

## Fase 11.8D — adapter diagnóstico C++ opt-in

A Fase 11.8D implementa o adapter mínimo:

```text
status = PENNY_SHAPED_DIAGNOSTIC_ADAPTER_IMPLEMENTED
header = include/lot/PennyShapedDiagnosticAdapter.hpp
source = src/lot/PennyShapedDiagnosticAdapter.cpp
test = tests/cpp/test_penny_shaped_diagnostic_adapter.cpp
```

O adapter apenas mapeia input diagnóstico em SI para `PennyShapedInput` e chama
`evaluate_penny_shaped_model`. Ele não altera parser, schema, CLI, `PknModel`,
`PknRunner` ou casos protegidos.

## Fase 11.9A — caso sintético mínimo

A Fase 11.9A adiciona um caso sintético versionado:

```text
status = PENNY_SYNTHETIC_CASE_CREATED
case = cases/validation/non_pkn/penny_shaped_synthetic_minimal.yaml
tool = tools/verify_phase11_9a_penny_synthetic_case.py
```

O caso é verificado por Python e não é uma rota de schema/runtime oficial do
`lot-sim`. Ele serve apenas para manter o contrato diagnóstico exercitável.

## Fase 11.9B — readiness BUZ29 PennyShaped

A Fase 11.9B classifica BUZ29 como candidato parcial:

```text
readiness = BUZ29_PENNY_CANDIDATE_PARTIAL
gate = BUZ29_PENNY_READINESS_PARTIAL_DO_NOT_START_11_10A
```

Há núcleo, adapter e caso sintético, mas faltam histórico de pressão,
`sigmaTheta`, tempo desde abertura e estado APB/sal de BUZ29 em forma
consumível. Assim, a 11.10A permanece bloqueada.

## Caveats

- Este roadmap não implementa solver novo.
- Este roadmap não altera parser, C++, schemas ou casos protegidos.
- Este roadmap não valida BUZ29 numericamente.
- BUZ-67D modern-refined continua a rota executável principal enquanto BUZ29
  permanece em planejamento não-PKN.
