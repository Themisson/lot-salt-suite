# Non-PKN model roadmap (Fase 11.6B)

## Resumo executivo

A Fase 11.6B consolida a decisão técnica após a auditoria
`BUZ29-VISCO-first-well` da Fase 11.6A.

## Atualizacao 11.11O — sigma-theta diagnostico controlado

A 11.11O validou `sigma_theta_diagnostic_input` em casos controlados do
`limited_gate`, incluindo `PENNY_SHAPED` apenas como elegibilidade diagnostica.
Isso nao altera a decisao de roadmap nao-PKN: `PENNY_SHAPED` continua sem
runtime fisico, BUZ29-PENNY continua bloqueado e qualquer estado `Reached`
representa somente gate diagnostico.

```text
SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALID
PENNY_SHAPED_RUNTIME_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
```

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

## Fase 11.10G — writer diagnóstico PennyShaped opt-in

A Fase 11.10G implementa o writer C++ isolado:

```text
include/lot/PennyShapedDiagnosticWriter.hpp
src/lot/PennyShapedDiagnosticWriter.cpp
tests/cpp/test_penny_shaped_diagnostic_writer.cpp
```

O status é:

```text
PENNY_DIAGNOSTIC_WRITER_IMPLEMENTED_OPT_IN
NO_BUZ29_RUNTIME_EXECUTION
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
```

O writer preserva campos internos em 1 rad, calcula equivalentes volumétricos
2π apenas com `source`, rejeita flags proibidas e permanece fora de
`lot-pkn`, parser, schema, CLI e runner não-PKN.

## Fase 11.10H — gate do runner diagnóstico não-PKN

A Fase 11.10H registra o gate para uma futura especificação de runner
diagnóstico não-PKN:

```text
NON_PKN_DIAGNOSTIC_RUNNER_SPEC_PARTIAL
RUNNER_IMPLEMENTATION_NOT_ALLOWED_IN_11_10H
BUZ29_RUNTIME_EXECUTION_NOT_ALLOWED
LOT_PKN_IMPACT_NOT_ALLOWED
```

Adapter e writer existem e estão isolados, mas o candidato BUZ29 continua
parcial: faltam campos adapter-ready e algumas semânticas de pressão/tempo e
`sigmaTheta` seguem diferidas. A próxima fase segura é especificar o runner
futuro, não implementá-lo.

## Fase 11.10I — seleção unificada por `fracture_model`

A Fase 11.10I reconcilia a recomendação anterior de um runner não-PKN com a
decisão arquitetural de evitar rotas runtime paralelas. A rota futura deve ser
LOT/fracture unificada, com seleção por input:

```text
lot.fracture.fracture_model
```

Status registrado:

```text
UNIFIED_LOT_FRACTURE_RUNTIME_SELECTED
PKN_DEFAULT_FRACTURE_MODEL
PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY
UNSUPPORTED_FRACTURE_MODELS_BLOCKED
```

O comportamento default futuro, quando `fracture_model` estiver ausente, deve
permanecer PKN. `PENNY_SHAPED` continua diagnóstico e só poderá ser ativado por
opt-in explícito. `KGD`, `RADIAL`, `ELLIPTICAL` e variantes seguem bloqueados.
Esta fase não altera parser, schema, C++, CLI, `PknModel`, `PknRunner` ou
`lot-pkn`.

## Fase 11.10J — guard do seletor `fracture_model`

A Fase 11.10J especifica o guard futuro para a seleção unificada por
`lot.fracture.fracture_model`:

```text
FRACTURE_MODEL_SELECTOR_GUARD_SPECIFIED
PKN_DEFAULT_WHEN_ABSENT
EXPLICIT_EMPTY_FRACTURE_MODEL_REJECTED
PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY
UNSUPPORTED_FRACTURE_MODELS_BLOCKED
```

Ausência do campo preserva PKN. Valor vazio explícito é erro. `PENNY_SHAPED`
continua apenas opt-in diagnóstico e depende de `fracture_initiation_gate` e da
convenção explícita de sinal de `sigma_theta`. A fase não implementa runtime,
parser, schema ou execução BUZ29-PENNY.

## Fase 11.10K — helper C++ isolado do guard

A Fase 11.10K implementa `FractureModelSelector` como helper C++ testável e
isolado. Ele define a semântica futura de seleção sem conectar essa semântica
ao parser, schema, CLI ou runtime. `PENNY_SHAPED` permanece diagnóstico,
`PKN` permanece default quando o campo estiver ausente, e BUZ29-PENNY não é
executado.

## Fase 11.10L — especificação parser/schema

A Fase 11.10L especifica a integração futura de
`lot.fracture.fracture_model` ao parser/schema. A política recomendada é
`SCHEMA_STRICT_CANONICAL_ONLY`: YAML oficial aceita `PKN` e `PENNY_SHAPED`,
ausência do campo preserva PKN, valor vazio explícito é erro e modelos não
suportados seguem bloqueados. A fase não altera parser, schema, runtime ou
casos.

## Fase 11.10M — integração parser/schema

A Fase 11.10M integra `lot.fracture.fracture_model` no parser/schema com
default retrocompatível `PKN`. `PENNY_SHAPED` explícito é aceito como seleção
diagnóstica, com `runtime_dispatch_enabled = false`, `physically_validated =
false` e `legacy_equivalent = false`. Modelos não suportados, como `KGD` e
`RADIAL`, são rejeitados.

Essa fase ainda não torna BUZ29-PENNY executável. O próximo gate é
`SIGMATHETA_INITIAL_STATE_REQUIRED_BEFORE_MODEL_DISPATCH`, porque o critério de
fratura não deve ser avaliado antes de auditar o estado geomecânico inicial
pós-perfuração.

## Fase 11.10N — estado inicial de sigma-theta

A Fase 11.10N audita o gate físico que ficou pendente após a integração
parser/schema:

```text
sigmatheta_initial_state = SIGMATHETA_INITIAL_STATE_MISSING
fracture_gate_status = FRACTURE_GATE_REQUIRES_INITIAL_STATE_WIRING
dispatch_allowed_next = false
buz29_execution_allowed_next = false
```

O resultado confirma que a seleção de `PENNY_SHAPED` no parser/schema ainda
não pode virar execução. As rotas atuais consomem `sigma_theta_static`,
`sigma_theta_time_series` ou diagnóstico sal/coupling, mas não comprovam um
`sigma_theta_initial_after_drilling` calculado e alinhado com a pressão do
gate. A próxima fase recomendada é
`PHASE11_10O_SPECIFY_SIGMATHETA_INITIAL_STATE_WIRING`.

## Fase 11.10O — especificação do wiring sigma-theta inicial

A Fase 11.10O especifica, sem implementar runtime, o contrato futuro para
conectar `sigma_theta_initial_compression_positive_Pa` ao
`fracture_initiation_gate`:

```text
PHASE11_10O_SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED
SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED
ELASTIC_INITIAL_WELLBORE_STATE_SELECTED_AS_PREFERRED_SOURCE
FRACTURE_GATE_BLOCKED_UNTIL_SIGMATHETA_INITIALIZED
PRESSURE_SIGMATHETA_COMPATIBILITY_REQUIRED
DISPATCH_REMAINS_BLOCKED
```

A fonte preferencial futura é o estado elástico/geomecânico inicial da parede
do poço após perfuração e antes do LOT, não um valor arbitrário de YAML.
`implementation_allowed_next = true` apenas para implementar o guard de wiring
na próxima fase. `PENNY_SHAPED`, BUZ29-PENNY e dispatch físico continuam
bloqueados.

## Fase 11.10P — guard sigma-theta inicial isolado

A Fase 11.10P implementa `SigmaThetaInitialStateGuard` como helper C++
isolado. O status e `SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED`, mas o guard
ainda nao e chamado pelo parser, schema, `PknModel`, `PknRunner` ou runtime.

Status preservados:

```text
PARSER_SCHEMA_NOT_CHANGED
RUNTIME_DISPATCH_NOT_CHANGED
LOT_PKN_BEHAVIOR_NOT_CHANGED
DISPATCH_REMAINS_BLOCKED
```

A proxima fase deve especificar o uso do guard pelo
`fracture_initiation_gate`, sem executar BUZ29-PENNY.

## Fase 11.10Q — dispatch especificado com sigma-theta guard

A Fase 11.10Q especifica o fluxo futuro:

```text
FractureModelSelector -> SigmaThetaInitialStateGuard -> criterio pressao x sigma_theta -> dispatch
```

O status registrado e:

```text
FRACTURE_GATE_DISPATCH_WITH_SIGMATHETA_GUARD_SPECIFIED
SIGMATHETA_GUARD_REQUIRED_BEFORE_DISPATCH
FRACTURE_MODEL_SELECTOR_REQUIRED_BEFORE_DISPATCH
PRESSURE_SIGMATHETA_CRITERION_SPEC_REQUIRED
SIGN_CONVENTION_RESOLUTION_REQUIRED
DISPATCH_REMAINS_BLOCKED
```

A fase nao integra runtime e nao executa BUZ29-PENNY. A proxima fase
recomendada e `PHASE11_10R_SPECIFY_PRESSURE_SIGMATHETA_FRACTURE_CRITERION`.

## Caveats

- Este roadmap não implementa solver novo.
- Este roadmap não altera parser, C++, schemas ou casos protegidos.
- Este roadmap não valida BUZ29 numericamente.
- BUZ-67D modern-refined continua a rota executável principal enquanto BUZ29
  permanece em planejamento não-PKN.
## Fase 11.10R — critério pressão x sigma-theta

A Fase 11.10R especifica o critério algébrico futuro do
`fracture_initiation_gate` sem implementar runtime. A decisão registrada é:

```text
PRESSURE_SIGMATHETA_FRACTURE_CRITERION_SPECIFIED
SIGMATHETA_COMPRESSION_POSITIVE_SIGN_CONVENTION_RESOLVED
PRESSURE_GREATER_THAN_SIGMATHETA_SHORTCUT_FORBIDDEN
DISPATCH_REMAINS_BLOCKED_UNTIL_CRITERION_GUARD_IMPLEMENTED
```

Para `sigma_theta` em compressão positiva, o critério preferencial futuro é:

```text
sigma_theta_current_compression_positive_Pa <= -tensile_strength_Pa
```

`pressure > sigma_theta_compression_positive_Pa` não deve ser usado como
critério físico final sem transformação de sinal, pressão crítica e referencial
explícito. `PENNY_SHAPED` continua opt-in diagnóstico e sem execução BUZ29.

## Fase 11.10S — guard do criterio pressao x sigma-theta

A Fase 11.10S implementa `PressureSigmaThetaFractureCriterionGuard` como helper
C++ isolado. O status registrado e:

```text
PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD_IMPLEMENTED
SIGMATHETA_COMPRESSION_POSITIVE_CRITERION_IMPLEMENTED
RUNTIME_DISPATCH_NOT_CHANGED
LOT_PKN_BEHAVIOR_NOT_CHANGED
```

O helper nao executa BUZ29-PENNY, nao altera `PknModel`, nao altera
parser/schema e nao libera dispatch. A proxima fase recomendada e especificar
o wiring runtime com guards, ainda sem executar fisicamente modelos nao PKN.

## Fase 11.10T — especificacao do wiring runtime do fracture gate

A Fase 11.10T especifica a sequencia futura do `fracture_initiation_gate`:

```text
FractureModelSelector
-> SigmaThetaInitialStateGuard
-> PressureSigmaThetaFractureCriterionGuard
-> fracture_initiation_gate_status
-> fracture_dispatch_status
```

O status registrado e:

```text
FRACTURE_GATE_RUNTIME_WIRING_SPECIFIED
RUNTIME_WIRING_NOT_IMPLEMENTED
DISPATCH_REMAINS_BLOCKED
```

Essa especificacao nao altera C++, runtime, parser, schema, CLI ou casos. PKN
permanece o default retrocompativel e `PENNY_SHAPED` permanece diagnostico,
nao fisicamente validado e nao equivalente ao legado. A proxima fase deve
especificar fixtures/testes de wiring antes de qualquer conexao runtime real.

## Fase 11.10U — fixtures do wiring runtime do fracture gate

A Fase 11.10U materializa fixtures sinteticas para o contrato definido na
11.10T. Os cenarios cobrem default PKN, PKN explicito, `PENNY_SHAPED`
diagnostico, bloqueios por `SigmaThetaInitialStateGuard`, bloqueios pelo
criterio pressao x sigma-theta, modelo KGD nao suportado e valor vazio
explicito.

```text
FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_VALID
RUNTIME_WIRING_NOT_IMPLEMENTED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_DIAGNOSTIC_ONLY
```

Essas fixtures sao contrato de teste; nao executam runtime nem validam BUZ29.

## Fase 11.10V — plano de implementacao do wiring

A Fase 11.10V registra o plano para uma proxima implementacao C++ isolada do
`FractureGateRuntimeWiring`, usando as fixtures da 11.10U como contrato.

```text
PHASE11_10V_RUNTIME_WIRING_IMPLEMENTATION_PLAN_SPECIFIED
RUNTIME_WIRING_IMPLEMENTATION_ALLOWED_NEXT
RUNTIME_EXECUTION_STILL_BLOCKED
BUZ29_EXECUTION_STILL_BLOCKED
PKN_BEHAVIOR_CHANGE_NOT_ALLOWED
```

A trilha nao-PKN continua segura: `PENNY_SHAPED` pode ser marcado futuramente
como `PennyDiagnosticEligible`, mas isso nao significa execucao fisica nem
validacao BUZ29-PENNY.

## Fase 11.10W — FractureGateRuntimeWiring

A Fase 11.10W implementa o helper isolado de wiring. Para a trilha nao-PKN, a
mudanca importante e que `PENNY_SHAPED` pode receber o status:

```text
FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE
```

Esse status nao executa BUZ29-PENNY, nao chama o adapter penny-shaped e nao
declara validacao fisica. A proxima decisao continua sendo um gate explicito
de integracao runtime.

## Fase 11.10X — gate de integracao runtime

A Fase 11.10X seleciona a rota futura `DIAGNOSTIC_PRE_RUNNER_OPT_IN`.

Para a trilha nao-PKN, isso preserva:

```text
PENNY_SHAPED = diagnostic_only
BUZ29_EXECUTION_BLOCKED
RUNTIME_PHYSICAL_DISPATCH_NOT_ALLOWED
```

Nenhum caso BUZ29-PENNY deve ser executado ate que uma fase posterior autorize
explicitamente um runtime fisico ou diagnostico isolado com entradas completas.

## Fase 11.10Y — gate pre-runner diagnostico

A Fase 11.10Y implementa a primeira conexao runtime do fracture gate, mas
somente como diagnostico opt-in antes do `run_pkn_case`.

Para a trilha nao-PKN:

```text
PENNY_SHAPED = diagnostic_only
BUZ29_EXECUTION_BLOCKED
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
```

`PENNY_SHAPED` pode aparecer no JSON diagnostico como modelo selecionado, mas
isso nao chama o adapter penny-shaped e nao executa BUZ29-PENNY.

## Fase 11.10Z — fixtures diagnosticas pre-runner

A Fase 11.10Z registra fixtures pequenas para o gate pre-runner. Para a trilha
nao-PKN, o cenario `diagnostic_enabled_penny_pre_runner` confirma:

```text
PENNY_SHAPED = diagnostic_only
physically_validated = false
legacy_equivalent = false
BUZ29_EXECUTION_BLOCKED
```

## Fase 11.11I — fonte real de sigma-theta inicial

A Fase 11.11I especifica que a fonte primaria futura para
`sigma_theta_initial_compression_positive_Pa` deve ser
`ELASTIC_INITIAL_WELLBORE_STATE`, representando o estado pos-perfuracao e
pre-LOT. `LEGACY_DIAGNOSTIC_TRACE` permanece fonte apenas diagnostica, nao
fonte de validacao fisica automatica.

Status registrados:

```text
PHASE11_11I_REAL_SIGMATHETA_INITIAL_SOURCE_STRATEGY_SPECIFIED
PRIMARY_SIGMATHETA_SOURCE_ELASTIC_INITIAL_WELLBORE_STATE
LOT_TIME_ZERO_NOT_DRILLING_TIME_ZERO
LEGACY_TRACE_NOT_PHYSICAL_VALIDATION_SOURCE
```

## Fase 11.11J — auditoria runtime sigma-theta/pressao

A Fase 11.11J confirma que o runtime diagnostico possui pressao de poco, mas
nao possui ainda sigma-theta inicial/current real para alimentar fisicamente o
gate:

```text
RUNTIME_SIGMATHETA_PRESSURE_AVAILABILITY_AUDITED
sigma_theta_initial_runtime_available = false
sigma_theta_current_runtime_available = false
wellbore_pressure_runtime_available = true
runtime_real_wiring_allowed_next = false
```

`PENNY_SHAPED` permanece diagnostic-only e BUZ29-PENNY continua bloqueado.

## Fase 11.11K — contrato pos-perfuracao

A Fase 11.11K especifica o contrato `PostDrillingInitialState`, mas registra:

```text
POST_DRILLING_INITIAL_STATE_INTEGRATION_SPECIFIED_BUT_SOURCE_MISSING
implementation_allowed_next = false
runtime_dispatch_allowed_next = false
buz29_execution_allowed_next = false
```

Assim, modelos nao-PKN seguem limitados a diagnostico e nao ha execucao BUZ29
ou dispatch fisico.

## Fase 11.11L — decisao de manter diagnostico bloqueado

A Fase 11.11L mantem:

```text
LIMITED_GATE_REMAINS_DIAGNOSTIC_BLOCKED_BY_REAL_SOURCE
PENNY_SHAPED_RUNTIME_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
```

O caminho 11.11M deve ser documental/planejamento, nao implementacao runtime
fisica.

O status permanece documental/diagnostico; nenhum runner nao-PKN e executado.

## Fase 11.11A — validacao controlada do pre-runner

A Fase 11.11A valida os cenarios controlados do diagnostico pre-runner. Para a
trilha nao-PKN, a conclusao permanece:

```text
PENNY_SHAPED = diagnostic_only
BUZ29_EXECUTION_BLOCKED
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
```

Nenhum adapter penny-shaped e chamado como runtime fisico.

## Fase 11.11B — regressao PKN com diagnostico opt-in

A Fase 11.11B reforca que o diagnostico pre-runner nao altera o comportamento
PKN fisico. Para a trilha nao-PKN, o resultado e conservador: `PENNY_SHAPED`
continua `diagnostic_only`, BUZ29-PENNY permanece bloqueado e nenhum adapter
penny-shaped e chamado como runtime fisico.

## Fase 11.11C — readiness sem desbloqueio nao-PKN

A decisao `RUNTIME_WIRING_READY_FOR_LIMITED_GATE_SPEC` nao altera a trilha
nao-PKN. A proxima fase pode especificar integracao limitada, mas
`PENNY_SHAPED` segue diagnostico e BUZ29-PENNY segue bloqueado.

## Fase 11.11D — especificacao sem runtime nao-PKN

A especificacao limitada nao desbloqueia PennyShaped runtime. A proxima
implementacao deve manter `PENNY_SHAPED = diagnostic_only`, nao chamar o adapter
penny-shaped como modelo fisico e nao executar BUZ29-PENNY.
A 11.11E implementa a integracao runtime limitada do fracture gate como rota
diagnostica opt-in. O modo `limited_gate` avalia o wiring antes do PKN e escreve
`diagnostic_fracture_gate.json`, mas nao habilita dispatch fisico. `PKN`
permanece o default retrocompativel, `PENNY_SHAPED` permanece diagnostic-only e
BUZ29-PENNY segue bloqueado.

Status:

```text
PHASE11_11E_LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_IMPLEMENTED
RUNTIME_DISPATCH_NOT_ENABLED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

## Fase 11.11F — fixtures limited_gate

A Fase 11.11F registra fixtures de contrato para `limited_gate`, incluindo o
cenario `limited_gate_enabled_penny`. Para a trilha nao-PKN, o contrato continua:

```text
PENNY_SHAPED = diagnostic_only
PENNY_SHAPED_RUNTIME_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
RUNTIME_DISPATCH_NOT_ENABLED
```

Essas fixtures nao executam BUZ29-PENNY e existem apenas para validar bloqueios,
metadata e regressao do gate limitado.

## Fase 11.11G — validacao controlada limited_gate

A Fase 11.11G confirma que `limited_gate` permanece opt-in e diagnostico. Para
a trilha nao-PKN:

```text
PENNY_SHAPED_RUNTIME_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
RUNTIME_DISPATCH_NOT_ENABLED
```

`PENNY_SHAPED` pode continuar aparecendo como selecao diagnostica, mas nao e
runtime fisico e nao executa BUZ29-PENNY.

## Fase 11.11H — readiness diagnostico sem runtime nao-PKN

A Fase 11.11H classifica `limited_gate` como pronto para uso runtime
diagnostico, mas explicitamente nao pronto para dispatch fisico:

```text
LIMITED_GATE_READY_FOR_DIAGNOSTIC_RUNTIME_USE
LIMITED_GATE_NOT_READY_FOR_PHYSICAL_DISPATCH
PENNY_SHAPED_RUNTIME_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
```
### Fase 11.11M — limited_gate permanece diagnostico

A Fase 11.11M registrou o plano para completar a fonte real de sigma-theta sem
habilitar runtime fisico nao PKN:

```text
LIMITED_GATE_REMAINS_DIAGNOSTIC_SIGMATHETA_SOURCE_PLAN_RECORDED
runtime_dispatch_enabled = false
buz29_execution_allowed = false
penny_shaped_runtime_enabled = false
```

O PENNY_SHAPED continua como contrato diagnostico. BUZ29-PENNY permanece
bloqueado ate existir fonte runtime real de sigma-theta e novo gate explicito.

### Fase 11.11N — fonte sigma-theta diagnostica

A 11.11N permite que PENNY_SHAPED atinja
`FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE` em fixtures diagnosticas quando
`sigma_theta_diagnostic_input` e fornecido, mas isso nao habilita runtime fisico.

```text
PENNY_SHAPED_RUNTIME_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
RUNTIME_DISPATCH_NOT_ENABLED
```

### Fase 11.11P — readiness do gate sigma-theta diagnostico

A 11.11P decide que o gate alimentado por `sigma_theta_diagnostic_input` esta
pronto apenas para uso diagnostico:

```text
DIAGNOSTIC_SIGMATHETA_GATE_READY
READY_FOR_DIAGNOSTIC_USE
NOT_READY_FOR_PHYSICAL_VALIDATION
NOT_READY_FOR_PHYSICAL_DISPATCH
```

Para a trilha nao-PKN, isso preserva:

```text
PENNY_SHAPED_RUNTIME_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
RUNTIME_DISPATCH_NOT_ENABLED
```

`FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE` continua sendo elegibilidade
diagnostica, nao execucao fisica.

### Fase 11.11Q — fonte real sigma-theta ainda especificada, nao implementada

A 11.11Q especifica o caminho futuro para uma fonte real de sigma-theta sem
liberar a trilha nao-PKN:

```text
REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH_SPECIFIED
PRIMARY_REAL_SOURCE_ELASTIC_INITIAL_WELLBORE_STATE
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
RUNTIME_DISPATCH_NOT_ALLOWED
```

BUZ29-PENNY permanece bloqueado ate que uma fonte real seja implementada,
validada e aprovada por novo gate.

### Fonte elastica inicial sigma-theta — sem desbloqueio nao-PKN

A fonte `ELASTIC_INITIAL_WELLBORE_STATE` foi implementada como alimentacao
diagnostica semi-fisica do `limited_gate`.

```text
ELASTIC_INITIAL_WELLBORE_SIGMATHETA_SOURCE_IMPLEMENTED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
RUNTIME_DISPATCH_NOT_ENABLED
```

Mesmo quando o gate atinge `FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE`, esse
estado continua sendo elegibilidade diagnostica. O adapter `PENNY_SHAPED` nao e
executado como runtime fisico.

### Validação analítica da fonte elástica — sem runtime não-PKN

A validação analítica da fonte `ELASTIC_INITIAL_WELLBORE_STATE` confirma
`FORMULA_VERIFIED`, `SIGN_CONVENTION_VERIFIED` e
`THRESHOLD_BEHAVIOR_VERIFIED`, mas não altera o bloqueio não-PKN:

```text
PENNY_SHAPED_RUNTIME_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
RUNTIME_DISPATCH_NOT_ENABLED
```

### Readiness da fonte elástica — ainda sem runtime não-PKN

A decisão posterior classifica a fonte como pronta para uso diagnóstico
semi-físico:

```text
ELASTIC_SIGMATHETA_SOURCE_READY_FOR_DIAGNOSTIC_SEMIPHYSICAL_USE
READY_FOR_KIRSCH_OR_AXISYMMETRIC_UPGRADE_SPEC
```

Isso não desbloqueia `PENNY_SHAPED` como runtime físico. BUZ29-PENNY permanece
bloqueado, `runtime_dispatch_enabled` permanece `false` e o próximo passo é
especificar uma formulação Kirsch/hoop stress ou elástica axisimétrica.

### Primeira comparação controlada axisimétrica

A fase `PHASE_RUN_FIRST_CONTROLLED_REFERENCE_COMPARISON` foi executada antes de
qualquer BUZ29/PENNY:

```text
FIRST_CONTROLLED_REFERENCE_COMPARISON_VALID
ANALYTIC_AXISYMMETRIC_CONTROLLED_REFERENCE
PHYSICAL_VALIDATION_NOT_CLAIMED
LEGACY_EQUIVALENCE_NOT_CLAIMED
BUZ29_PENNY_NOT_EXECUTED
RUNTIME_DISPATCH_NOT_ENABLED
PKN_BEHAVIOR_NOT_CHANGED
```

A trilha não-PKN permanece bloqueada até gate diagnóstico específico.

### Readiness BUZ67D/PKN antes de BUZ29/PENNY

BUZ67D/PKN foi classificado como referência diagnóstica controlada:

```text
BUZ67D_PKN_READY_FOR_DIAGNOSTIC_REFERENCE
BUZ29_PENNY_NOT_EXECUTED
RUNTIME_DISPATCH_NOT_ENABLED
PHYSICAL_VALIDATION_NOT_CLAIMED
LEGACY_EQUIVALENCE_NOT_CLAIMED
PKN_BEHAVIOR_NOT_CHANGED
```

Isso autoriza apenas a preparação de insumos BUZ29/PENNY; a execução
BUZ29/PENNY permanece bloqueada para fase futura.

### Insumos diagnósticos BUZ29/PENNY preparados

O manifesto diagnóstico BUZ29/PENNY foi preparado:

```text
BUZ29_PENNY_DIAGNOSTIC_INPUTS_PREPARED
EXECUTION_NOT_ALLOWED_YET
DIAGNOSTIC_ONLY
PHYSICAL_VALIDATION_NOT_CLAIMED
LEGACY_EQUIVALENCE_NOT_CLAIMED
RUNTIME_DISPATCH_NOT_ENABLED
```

Esse manifesto permite apenas decidir um gate futuro de execução diagnóstica.

### Gate de execução diagnóstica BUZ29/PENNY

O gate progressivo foi decidido:

```text
BUZ29_PENNY_DIAGNOSTIC_EXECUTION_ALLOWED_NEXT
EXECUTION_ALLOWED_NEXT_TRUE
BUZ29_PENNY_EXECUTED_NOW_FALSE
PHYSICAL_VALIDATION_NOT_CLAIMED
LEGACY_EQUIVALENCE_NOT_CLAIMED
RUNTIME_DISPATCH_NOT_ENABLED
```

A próxima fase pode executar apenas comparação diagnóstica. `PENNY_SHAPED`
permanece não físico, sem equivalência legada e isolado de dispatch runtime.

### Tentativa de execução diagnóstica BUZ29/PENNY

A execução foi bloqueada por ausência de runner diagnóstico seguro:

```text
BUZ29_PENNY_DIAGNOSTIC_RUN_BLOCKED
BUZ29_PENNY_DIAGNOSTIC_EXECUTION_BLOCKED_BY_MISSING_RUNNER
NO_RUNTIME_NON_PKN_RUNNER
BUZ29_PENNY_ADAPTER_INPUTS_PARTIAL
```

O writer e o adapter continuam disponíveis como componentes diagnósticos
isolados, mas ainda não existe caminho operacional para executar o candidato
BUZ29/PENNY sem nova integração C++ controlada.
