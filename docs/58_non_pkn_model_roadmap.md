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

## Fase 11.9C — evidência BUZ29 PennyShaped

A Fase 11.9C audita evidências adicionais para a rota BUZ29-PENNY:

```text
classification = BUZ29_PENNY_EVIDENCE_PARTIAL
can_update_readiness = true
can_start_11_10a = false
recommended_next_phase = PHASE11_9D_UPDATE_BUZ29_PENNY_READINESS
```

Foram encontrados indícios documentais e fonte legada para o caso
`BUZ29-VISCO-first-well`, mas os campos críticos ainda não estão consumíveis
para o `PennyShapedDiagnosticAdapter`. A 11.10A continua bloqueada até a
atualização formal de readiness da 11.9D.

## Fase 11.9D — atualização de readiness BUZ29 PennyShaped

A Fase 11.9D mantém o gate da rota diagnóstica fechado:

```text
updated_readiness = BUZ29_PENNY_CANDIDATE_PARTIAL
gate = BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A
can_start_11_10A = false
```

A próxima etapa segura é completar evidência de pressão e abertura antes de
qualquer YAML candidato BUZ29-PENNY.

## Fase 11.9E — evidência BUZ29 de pressão e abertura

A Fase 11.9E completou a auditoria focal dos dois campos mínimos que bloqueavam
o gate anterior:

```text
pressure_history_status = PRESSURE_HISTORY_FOUND_CONSUMABLE
opening_time_status = OPENING_TIME_FOUND_CONSUMABLE
classification = BUZ29_PRESSURE_AND_OPENING_EVIDENCE_COMPLETE
can_reopen_11_10A_gate = true
recommended_next_phase = PHASE11_9F_REEVALUATE_BUZ29_PENNY_READINESS_AFTER_PRESSURE_OPENING
```

A evidência vem do output legado existente
`legance/LOT_Tese/results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat`, que contém `Time`,
blocos `dP`, `dV_leakoff` e `Momento da quebra: 10.4`. A fase não cria YAML
BUZ29-PENNY, não executa BUZ29 e não valida fisicamente a rota; ela apenas
habilita uma reavaliação formal de readiness na próxima fase.

## Fase 11.9F — readiness após pressão e abertura

A Fase 11.9F consumiu a evidência da 11.9E e reavaliou formalmente o gate
BUZ29-PENNY:

```text
updated_readiness = BUZ29_PENNY_CANDIDATE_PARTIAL_BUT_DIAGNOSTIC_SAFE
can_start_11_10A = true
gate = BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A
recommended_next_phase = PHASE11_10A_START_BUZ29_PENNY_DIAGNOSTIC_ROUTE
```

Essa abertura é limitada: a próxima fase pode preparar uma rota diagnóstica,
mas não validar BUZ29 fisicamente, não declarar equivalência com o legado e não
criar interpretação forte de volume. O caveat novo é:

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
```

O `fracture_volume_proxy_m3` do núcleo/adapter PennyShaped deve ser interpretado
no contexto axissimétrico de 1 rad e não como volume circular completo em 2π sem
auditoria matemática específica.

## Fase 11.10A — rota diagnóstica BUZ29-PENNY

A Fase 11.10A iniciou a rota diagnóstica controlada para BUZ29-PENNY:

```text
classification = BUZ29_PENNY_DIAGNOSTIC_ROUTE_PARTIAL_STARTED
case = cases/validation/non_pkn/buz29_penny_candidate.yaml
index = cases/validation/non_pkn/studies_index.yaml
physically_validated = false
legacy_equivalent = false
active_simulation_case = false
```

Esse candidato é somente um contrato diagnóstico. Ele preserva o gate da 11.9F,
referencia a evidência consumível de pressão/abertura da 11.9E e registra os
caveats:

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
NOT_ACTIVE_SIMULATION_CASE
```

A 11.10A não altera `lot-pkn`, não cria rota runtime oficial, não executa BUZ29
como simulação física e não remove as lacunas de `sigmaTheta`, `pw`, `margin`
ou `opened`.

## Fase 11.10B — inspeção adapter-ready BUZ29-PENNY

A Fase 11.10B inspecionou o candidato criado na 11.10A contra a API real do
`PennyShapedDiagnosticAdapter`:

```text
classification = BUZ29_PENNY_ADAPTER_INPUTS_PARTIAL
adapter_ready = false
partial_adapter_ready = true
recommended_next_phase = PHASE11_10C_AUDIT_PENNY_SHAPED_MODEL_MATH_AXISYMMETRIC_1RAD
```

A inspeção confirmou que pressão e abertura são evidências consumíveis, mas
`young_modulus_Pa`, `poisson_ratio`, `viscosity_Pa_min`, `flow_rate_m3_min` e
`sigma_theta_compression_positive_Pa` ainda não estão presentes como entradas
diretas do adapter. `elapsed_since_opening_min` e `wellbore_pressure_Pa`
existem apenas como mapeamentos parciais que exigem revisão semântica.

Mesmo com esse status parcial, a próxima fase não deve executar BUZ29; ela deve
auditar matematicamente o `PennyShapedModel` na formulação axissimétrica de 1
rad.

## Fase 11.10C — auditoria matemática PennyShaped 1 rad

A Fase 11.10C auditou o `PennyShapedModel` já implementado, sem alterar C++ e
sem executar BUZ29-PENNY. A conclusão formal foi:

```text
primary_classification = PENNY_MATH_HYDRAULIC_DIAGNOSTIC_SCALING
secondary_classification = PENNY_MATH_AXISYMMETRIC_1RAD_PROXY
tertiary_classification = PENNY_MATH_LEGACY_INSPIRED_EMPIRICAL
math_audit_passed = true
requires_code_correction = false
requires_output_contract = true
recommended_next_phase = PHASE11_10D_DEFINE_AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT
```

As fórmulas de abertura e raio são dimensionalmente consistentes para uso
diagnóstico, mas `fracture_volume_proxy_m3` permanece proxy de volume na
interpretação axissimétrica de 1 rad. O multiplicador `10.0` continua
legado-inspirado e empírico; ele não deve ser promovido a conversão formal
`2π` sem contrato de saída específico.

## Fase 11.10D — contrato de saída 1 rad ↔ 2π

A Fase 11.10D especificou o contrato de saída sem implementar runtime:

```text
contract_status = AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_SPECIFIED
axisymmetric_angle_rad = 1.0
volume_conversion_factor_1rad_to_2pi = 6.283185307179586
volume_multiplier_semantics = VOLUME_MULTIPLIER_EMPIRICAL
implementation_allowed = false
recommended_next_phase = PHASE11_10E_DEFINE_PENNY_DIAGNOSTIC_OUTPUT_FIXTURES
```

A rota passa a exigir campos separados para `fracture_volume_proxy_1rad_m3`,
`fracture_volume_equivalent_2pi_m3` e `fracture_volume_equivalent_2pi_source`.
O `volume_multiplier` permanece empírico e não substitui o fator geométrico
`2π`.

## Fase 11.10E — fixtures de saída diagnóstica PennyShaped

A Fase 11.10E materializa o contrato da 11.10D como fixtures versionados, sem
writer/runtime:

```text
PHASE11_10E_PENNY_DIAGNOSTIC_OUTPUT_FIXTURES_DEFINED
PENNY_DIAGNOSTIC_OUTPUT_FIXTURES_VALID
FIXTURE_ONLY_NO_RUNTIME_WRITER
IMPLEMENTATION_NOT_ALLOWED_IN_11_10E
```

Foram definidos fixtures JSON, CSV e metadata em
`tests/fixtures/comparison/phase11_10e/`, além do validador
`tools/validate_phase11_10e_penny_output_fixtures.py`. O contrato separa
`fracture_volume_proxy_1rad_m3` do equivalente `2π` e mantém
`volume_multiplier` como `VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI`.

## Fase 11.10F-aux — restrição standalone do SESTSAL legado

A Fase 11.10F-aux registra uma restrição da trilha sal/APB que não deve travar
a evolução PennyShaped, mas precisa ficar documentada:

```text
cause = LEGACY_SESTSAL_REQUIRES_APB1DA_COUPLING
gate = DO_NOT_USE_SESTSAL_STANDALONE_AS_VALIDATION_REFERENCE
secondary_cause = ELASTIC_DISPLACEMENT_REFERENCE_MISMATCH
secondary_gate = ALIGN_TOTAL_VS_PERTURBATION_DISPLACEMENT_BEFORE_COMPARISON
```

Chamadas standalone de `sestsal` que atinjam estado hidrostático puro podem
produzir `NaN` ao normalizar por `norm_sigd`. O uso legado esperado continua
acoplado a `APB1da`; comparações de deslocamento total legado contra
perturbação moderna ficam bloqueadas sem alinhamento explícito.

## Fase 11.10F — especificação do writer diagnóstico PennyShaped

A Fase 11.10F especifica o writer diagnóstico PennyShaped futuro sem
implementar C++ ou runtime:

```text
PENNY_DIAGNOSTIC_WRITER_SPECIFIED
IMPLEMENTATION_NOT_ALLOWED_IN_11_10F
RUNTIME_EXECUTION_NOT_ALLOWED_IN_11_10F
```

O writer futuro deve consumir uma entrada diagnóstica estruturada, emitir JSON e
CSV compatíveis com as fixtures 11.10E, preservar grandezas internas em 1 rad e
reportar equivalentes 2π apenas com `source`/caveat. A rota permanece
diagnóstica, não ativa e não equivalente ao legado.

## Caveats

- Este roadmap não implementa solver novo.
- Este roadmap não altera parser, C++, schemas ou casos protegidos.
- Este roadmap não valida BUZ29 numericamente.
- BUZ-67D modern-refined continua a rota executável principal enquanto BUZ29
  permanece em planejamento não-PKN.
