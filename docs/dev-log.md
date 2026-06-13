# dev-log — lot-salt-suite

> **LEITURA OBRIGATÓRIA** para Claude Code e Codex na abertura de qualquer sessão.
> Auto-atualizado por `tools/update_devlog.py` após cada `git commit` ou `git push`.
> Invoke `/update-devlog` manualmente quando necessário.

---

## Estado atual do projeto

```
Fase ativa  : 11.11O sigma-theta diagnostic controlled validation
Branch      : main
Repositório : https://github.com/Themisson/lot-salt-suite
Último push : 2026-06-12
Testes C++  : 387/387 em 2026-06-12
Testes Py   : 936/936 em 2026-06-12
Baselines   : 4 capturados (LOT_APB_v5)
Saltcreep   : 133/133 Catch2 baseline + 133/133 Catch2 LSS Eigen + 31/31 Python em 2026-06-04
Eigen decisao: MIGRATION_COMPLETED
CMake 4     : SUPORTADO (CMAKE_POLICY_VERSION_MINIMUM 3.5, sem flag manual)
VS generator: SUPORTADO (LSS_LOT_SIM_EXECUTABLE via $<TARGET_FILE:lot-sim>)
WDAC tests  : SUPORTADO (LSS_ENABLE_CLI_SUBPROCESS_TESTS=OFF desativa apenas subprocess CLI)
```

### Próximas tarefas (Fase 6)

- [x] Definir governanca de `external/saltcreep/` como dependencia vendorizada ativa
- [x] Auditar caminho LOT/PKN nos legados sem modificar `legance/`
- [x] Catalogar modelos nao PKN como nao prioritarios
- [x] Criar contrato YAML/C++ LOT/PKN com casos sintaticos e migrado BUZ67D
- [x] Implementar `lot::BreakdownDetector` sintetico com testes Catch2
- [x] Criar esqueleto sintetico de `lot::PknModel` com testes Catch2
- [x] Auditar R09 antes de regressao numerica PKN legado x moderno
- [x] Implementar `lot::PknModel` fisico minimo em SI com series temporais sinteticas
- [x] Conectar LOT/PKN ao CLI moderno com saida CSV/JSON sem regressao legado
- [x] Executar ensaio comparativo controlado R09 (`/(pi*22)` vs `/(pi*2)`) sem alterar legado
- [x] Criar pos-processamento moderno minimo LOT/PKN para CSV/JSON sem regressao legado
- [x] Registrar politica C++ first, Python postprocess only
- [x] Implementar `LeakoffModel` C++ estruturado com testes Catch2
- [x] Auditar compatibilidade Eigen do saltcreep sem remover copias Eigen
- [x] Provar forcadamente que saltcreep compila/testa com `include/Eigen` (Fase 6.10B)
- [x] Migrar `include/Eigen` como modo integrado oficial do saltcreep com auto-deteccao (Fase 6.11)

### Achados críticos da auditoria (não alterar sem revisar docs/08_known_issues.md)

| ID | Achado | Impacto |
|----|--------|---------|
| FA01 | `e0` interno em **[1/min]** — LOTTeste.cpp divide por 60 explicitamente | Crítico |
| FA02 | Temperatura SESTSAL em **[°C]** — Q_R é parâmetro empírico, não físico em K | Alto |
| FA03 | Sinal: **compressão positiva** (mecânica dos solos) | Confirmado |
| FA04 | Acoplamento sal→APB é **sequencial fraco** (staggered) | Confirmado |

---

## Entradas de sessão

---

### [2026-06-12] Fase 11.11O — sigma-theta diagnostic controlled validation — Codex

**Status:** Implementado; commit/push executado ao final da fase se todos os
gates passarem.

**Fixtures criadas:**

```text
tests/fixtures/comparison/phase11_11o/
```

**Ferramenta criada:**

```text
tools/validate_phase11_11o_sigmatheta_diagnostic_controlled_cases.py
```

**Documento criado:**

```text
docs/115_sigmatheta_diagnostic_controlled_validation.md
```

**Status registrado:**

```text
PHASE11_11O_SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALIDATED
SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALID
LIMITED_GATE_CAN_BE_FED_DIAGNOSTICALLY
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
PKN_BEHAVIOR_NOT_CHANGED
```

**Proxima fase recomendada:**

```text
PHASE11_11P_DECIDE_DIAGNOSTIC_SIGMATHETA_GATE_READINESS
```

---

### [2026-06-12] Fase 11.11N — diagnostic sigma-theta source — Codex

**Status:** Implementado; commit/push executado ao final da fase se todos os
gates passarem.

**Implementacao C++ limitada:**

```text
lot.fracture.sigma_theta_diagnostic_input
```

**Status registrado:**

```text
SIGMATHETA_DIAGNOSTIC_SOURCE_IMPLEMENTED
LIMITED_GATE_CAN_BE_FED_DIAGNOSTICALLY
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_NOT_CHANGED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

**Documento criado:**

```text
docs/114_sigmatheta_diagnostic_source_implementation.md
```

**Proxima fase recomendada:**

```text
PHASE11_11O_VALIDATE_SIGMATHETA_DIAGNOSTIC_SOURCE_ON_CONTROLLED_CASES
```

---

### [2026-06-12] Fase 11.11M — limited_gate sigma-theta source plan — Codex

**Status:** Implementado; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/plan_phase11_11m_sigmatheta_source_completion.py
```

**Documento criado:**

```text
docs/113_limited_gate_remains_diagnostic_sigmatheta_source_plan.md
```

**Status registrado:**

```text
LIMITED_GATE_REMAINS_DIAGNOSTIC_SIGMATHETA_SOURCE_PLAN_RECORDED
implementation_performed = false
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_changed = false
penny_shaped_runtime_enabled = false
```

**Proxima fase recomendada:**

```text
PHASE11_11N_IMPLEMENT_OR_CONNECT_SIGMATHETA_SOURCE
```

---

### [2026-06-12] Fase 11.11H — limited_gate runtime readiness — Codex

**Status:** Implementado; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/decide_phase11_11h_limited_gate_runtime_readiness.py
```

**Documento criado:**

```text
docs/108_limited_gate_runtime_readiness_decision.md
```

**Status registrado:**

```text
PHASE11_11H_LIMITED_GATE_RUNTIME_READINESS_DECIDED
LIMITED_GATE_READY_FOR_DIAGNOSTIC_RUNTIME_USE
LIMITED_GATE_NOT_READY_FOR_PHYSICAL_DISPATCH
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_NOT_CHANGED
```

**Proxima fase recomendada:**

```text
PHASE11_11I_SPECIFY_REAL_SIGMATHETA_INITIAL_SOURCE_STRATEGY
```

### [2026-06-12] Fase 11.11G — limited_gate controlled validation — Codex

**Status:** Implementado; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/validate_phase11_11g_limited_gate_controlled_cases.py
```

**Documento criado:**

```text
docs/107_limited_gate_controlled_validation.md
```

**Status registrado:**

```text
PHASE11_11G_LIMITED_GATE_CONTROLLED_CASES_VALIDATED
LIMITED_GATE_CONTROLLED_CASES_VALID
PKN_OUTPUTS_UNCHANGED_WITH_LIMITED_GATE
DIAGNOSTIC_OUTPUT_ISOLATED
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

**Proxima fase recomendada:**

```text
PHASE11_11H_DECIDE_LIMITED_GATE_READINESS_FOR_RUNTIME_USE
```

### [2026-06-12] Fase 11.11F — limited_gate fixtures — Codex

**Status:** Implementado; commit/push executado ao final da fase se todos os
gates passarem.

**Fixtures criadas:**

```text
tests/fixtures/comparison/phase11_11f/
```

**Ferramenta criada:**

```text
tools/validate_phase11_11f_limited_gate_fixtures.py
```

**Documento criado:**

```text
docs/106_limited_gate_fixtures.md
```

**Status registrado:**

```text
PHASE11_11F_LIMITED_GATE_FIXTURES_DEFINED
LIMITED_GATE_FIXTURES_VALID
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
PKN_BEHAVIOR_CHANGE_NOT_ALLOWED
```

**Proxima fase recomendada:**

```text
PHASE11_11G_VALIDATE_LIMITED_GATE_ON_CONTROLLED_CASES
```

### [2026-06-12] Fase 11.11E — limited fracture gate runtime integration — Codex

**Status:** Implementado; commit/push executado ao final da fase se todos os
gates passarem.

**Helper C++ criado:**

```text
LimitedFractureGateRuntimeIntegration
```

**Documento criado:**

```text
docs/105_limited_fracture_gate_runtime_integration_implementation.md
```

**Status registrado:**

```text
PHASE11_11E_LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_IMPLEMENTED
LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_IMPLEMENTED
RUNTIME_DISPATCH_NOT_ENABLED
PKN_OUTPUTS_UNCHANGED_WITH_LIMITED_GATE
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

**Proxima fase recomendada:**

```text
PHASE11_11F_ADD_LIMITED_GATE_CASE_FIXTURES
```

### [2026-06-12] Fase 11.11D — limited fracture gate runtime integration spec — Codex

**Status:** Implementado; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/spec_phase11_11d_limited_fracture_gate_runtime_integration.py
```

**Documento criado:**

```text
docs/104_limited_fracture_gate_runtime_integration_spec.md
```

**Status registrado:**

```text
LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_SPECIFIED
IMPLEMENTATION_ALLOWED_NEXT_WITH_DISPATCH_DISABLED
PKN_BEHAVIOR_CHANGE_NOT_ALLOWED
BUZ29_EXECUTION_BLOCKED
```

**Proxima fase recomendada:**

```text
PHASE11_11E_IMPLEMENT_LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION
```

### [2026-06-12] Fase 11.11C — runtime wiring readiness decision — Codex

**Status:** Implementado; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/decide_phase11_11c_runtime_wiring_readiness.py
```

**Documento criado:**

```text
docs/103_runtime_wiring_readiness_decision.md
```

**Decisao:**

```text
RUNTIME_WIRING_READY_FOR_LIMITED_GATE_SPEC
```

**Restricoes preservadas:**

```text
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_DIAGNOSTIC_ONLY
```

**Proxima fase recomendada:**

```text
PHASE11_11D_SPECIFY_LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION
```

### [2026-06-12] Fase 11.11B — PKN diagnostic disabled/enabled comparison — Codex

**Status:** Implementado; commit/push executado ao final da fase se todos os
gates passarem.

**Objetivo:** provar que habilitar o diagnostico pre-runner de forma opt-in nao
altera `result.json` nem `timeseries.csv` dos casos LOT-PKN protegidos.

**Ferramenta criada:**

```text
tools/compare_phase11_11b_pkn_outputs_with_diagnostics.py
```

**Documento criado:**

```text
docs/102_pkn_diagnostic_pre_runner_regression_comparison.md
```

**Status registrado:**

```text
PHASE11_11B_PKN_OUTPUTS_COMPARED_WITH_DIAGNOSTICS
PKN_OUTPUTS_UNCHANGED_WITH_DIAGNOSTICS
DIAGNOSTIC_OUTPUT_ISOLATED
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
```

**Proxima fase recomendada:**

```text
PHASE11_11C_DECIDE_RUNTIME_WIRING_INTEGRATION_READINESS
```

### [2026-06-12] Fase 11.11A — diagnostic pre-runner controlled validation — Codex

**Status:** Implementado; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/validate_phase11_11a_diagnostic_pre_runner_controlled_cases.py
```

**Documento criado:**

```text
docs/101_diagnostic_pre_runner_controlled_validation.md
```

**Status registrado:**

```text
PHASE11_11A_DIAGNOSTIC_PRE_RUNNER_CONTROLLED_CASES_VALIDATED
DIAGNOSTIC_PRE_RUNNER_CONTROLLED_CASES_VALID
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
```

**Proxima fase recomendada:**

```text
PHASE11_11B_COMPARE_PKN_RESULTS_WITH_DIAGNOSTIC_DISABLED_ENABLED
```

### [2026-06-12] Fase 11.10Z — diagnostic pre-runner fixtures — Codex

**Status:** Implementado; commit/push executado ao final da fase se todos os
gates passarem.

**Objetivo:** adicionar fixtures pequenas para validar o contrato do diagnostico
pre-runner implementado na 11.10Y, sem alterar casos protegidos e sem executar
BUZ29-PENNY.

**Fixtures criadas:**

```text
tests/fixtures/comparison/phase11_10z/diagnostic_disabled_default.yaml
tests/fixtures/comparison/phase11_10z/diagnostic_enabled_pkn_pre_runner.yaml
tests/fixtures/comparison/phase11_10z/diagnostic_enabled_penny_pre_runner.yaml
tests/fixtures/comparison/phase11_10z/diagnostic_dispatch_true_invalid.yaml
tests/fixtures/comparison/phase11_10z/diagnostic_invalid_mode.yaml
tests/fixtures/comparison/phase11_10z/diagnostic_missing_sigmatheta_blocks.yaml
```

**Validador criado:**

```text
tools/validate_phase11_10z_diagnostic_pre_runner_fixtures.py
```

**Status registrado:**

```text
PHASE11_10Z_DIAGNOSTIC_PRE_RUNNER_FIXTURES_DEFINED
DIAGNOSTIC_PRE_RUNNER_FIXTURES_VALID
BUZ29_EXECUTION_BLOCKED
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
```

**Proxima fase recomendada:**

```text
PHASE11_11A_VALIDATE_DIAGNOSTIC_PRE_RUNNER_ON_CONTROLLED_CASES
```

### [2026-06-12] Fase 11.10Y — diagnostic pre-runner runtime gate — Codex

**Status:** Implementado; commit/push executado ao final da fase se todos os
gates passarem.

**Objetivo:** conectar `FractureGateRuntimeWiring` ao fluxo `lot-sim run` apenas
como diagnostico opt-in pre-runner, sem dispatch fisico e sem alterar o
comportamento padrao do PKN.

**Arquivos principais criados:**

```text
include/lot/FractureGateDiagnosticPreRunner.hpp
src/lot/FractureGateDiagnosticPreRunner.cpp
tests/cpp/test_fracture_gate_diagnostic_pre_runner.cpp
tools/audit_phase11_10y_diagnostic_pre_runner_runtime_gate.py
tests/python/test_audit_phase11_10y_diagnostic_pre_runner_runtime_gate.py
docs/99_diagnostic_pre_runner_runtime_gate.md
```

**Resultado esperado do gate:**

```text
PHASE11_10Y_DIAGNOSTIC_PRE_RUNNER_RUNTIME_GATE_IMPLEMENTED
DIAGNOSTIC_PRE_RUNNER_OPT_IN_IMPLEMENTED
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
PKN_BEHAVIOR_NOT_CHANGED
BUZ29_EXECUTION_BLOCKED
```

**Interpretacao:** o diagnostico grava `diagnostic_fracture_gate.json` quando
`lot.fracture.fracture_gate_diagnostics.enabled` e `true`. Com sigma_theta
inicial ausente, o bloqueio diagnostico esperado e
`FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE`. Isso nao habilita fratura
fisica e nao executa BUZ29-PENNY.

### [2026-06-12] Fase 11.10X — gate de integracao runtime do FractureGateRuntimeWiring — Codex

**Status:** Concluido; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/decide_phase11_10x_runtime_integration_gate.py
```

**Documento criado:**

```text
docs/98_runtime_integration_gate_for_fracture_wiring.md
```

**Resultado:**

```text
PHASE11_10X_RUNTIME_INTEGRATION_GATE_SPECIFIED
RUNTIME_INTEGRATION_GATE_SPECIFIED
DIAGNOSTIC_PRE_RUNNER_OPT_IN_SELECTED
RUNTIME_PHYSICAL_DISPATCH_NOT_ALLOWED
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_CHANGE_NOT_ALLOWED
```

**Interpretacao:** a fase audita o runtime atual
`apps/lot-sim.cpp -> run_pkn_case(data) -> PknModel{}.simulate(...)` e
seleciona a proxima integracao segura como diagnostica, pre-runner e opt-in.
A integracao futura deve ocorrer depois do parse/validacao e antes de
`run_pkn_case(data)`, com feature flag explicita e saida diagnostica isolada.
Dispatch fisico, BUZ29-PENNY e qualquer alteracao de comportamento PKN
permanecem bloqueados. A proxima fase recomendada e
`PHASE11_10Y_IMPLEMENT_DIAGNOSTIC_PRE_RUNNER_RUNTIME_GATE`.

---

### [2026-06-12] Fase 11.10W — implementar FractureGateRuntimeWiring — Codex

**Status:** Concluido; commit/push executado ao final da fase se todos os
gates passarem.

**Arquivos C++ criados:**

```text
include/lot/FractureGateRuntimeWiring.hpp
src/lot/FractureGateRuntimeWiring.cpp
tests/cpp/test_fracture_gate_runtime_wiring.cpp
```

**Ferramenta criada:**

```text
tools/audit_phase11_10w_fracture_gate_runtime_wiring.py
```

**Documento criado:**

```text
docs/97_fracture_gate_runtime_wiring_implementation.md
```

**Resultado:**

```text
PHASE11_10W_FRACTURE_GATE_RUNTIME_WIRING_IMPLEMENTED
FRACTURE_GATE_RUNTIME_WIRING_IMPLEMENTED
RUNTIME_EXECUTION_NOT_ENABLED
PKN_MODEL_NOT_CALLED
PENNY_ADAPTER_NOT_CALLED
BUZ29_EXECUTION_BLOCKED
```

**Interpretacao:** a fase implementa um helper C++ isolado que compoe
`FractureModelSelector`, `SigmaThetaInitialStateGuard` e
`PressureSigmaThetaFractureCriterionGuard` para retornar apenas status de gate
e elegibilidade de dispatch. `PknEligible` nao chama `PknModel`;
`PennyDiagnosticEligible` nao chama `PennyShapedDiagnosticAdapter`.
Parser/schema, CLI, `lot-pkn` e BUZ29-PENNY permanecem inalterados. A proxima
fase recomendada e `PHASE11_10X_SPECIFY_RUNTIME_INTEGRATION_GATE`.

---

### [2026-06-12] Fase 11.10V — plano de implementacao do runtime wiring do fracture gate — Codex

**Status:** Concluido; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/plan_phase11_10v_runtime_wiring_implementation.py
```

**Documento criado:**

```text
docs/96_fracture_gate_runtime_wiring_implementation_plan.md
```

**Resultado:**

```text
PHASE11_10V_RUNTIME_WIRING_IMPLEMENTATION_PLAN_SPECIFIED
RUNTIME_WIRING_IMPLEMENTATION_PLAN_SPECIFIED
RUNTIME_WIRING_IMPLEMENTATION_ALLOWED_NEXT
RUNTIME_EXECUTION_STILL_BLOCKED
BUZ29_EXECUTION_STILL_BLOCKED
PKN_BEHAVIOR_CHANGE_NOT_ALLOWED
```

**Interpretacao:** a fase especifica a proxima implementacao isolada de
`FractureGateRuntimeWiring`, mapeando as sete fixtures da 11.10U para testes
Catch2 futuros. A implementacao futura deve compor `FractureModelSelector`,
`SigmaThetaInitialStateGuard` e `PressureSigmaThetaFractureCriterionGuard`,
mas a 11.10V nao altera C++, runtime, parser/schema, CLI, `lot-pkn` ou casos.
BUZ29-PENNY permanece bloqueado. A proxima fase recomendada e
`PHASE11_10W_IMPLEMENT_FRACTURE_GATE_RUNTIME_WIRING`.

---

### [2026-06-12] Fase 11.10U — fixtures do wiring runtime do fracture gate — Codex

**Status:** Concluido; commit/push executado ao final da fase se todos os
gates passarem.

**Fixtures criadas:**

```text
tests/fixtures/comparison/phase11_10u/fracture_gate_runtime_wiring_scenarios.json
tests/fixtures/comparison/phase11_10u/fracture_gate_runtime_wiring_metadata.json
```

**Ferramenta criada:**

```text
tools/validate_phase11_10u_fracture_gate_runtime_wiring_fixtures.py
```

**Documento criado:**

```text
docs/95_fracture_gate_runtime_wiring_fixtures.md
```

**Resultado:**

```text
PHASE11_10U_FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_DEFINED
FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_VALID
RUNTIME_WIRING_NOT_IMPLEMENTED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_DIAGNOSTIC_ONLY
```

**Interpretacao:** a fase materializa sete cenarios sinteticos para o futuro
wiring do `fracture_initiation_gate`, cobrindo default PKN, PKN explicito,
`PENNY_SHAPED` diagnostico, bloqueios por sigma-theta guard, bloqueios pelo
criterio pressao x sigma-theta, KGD nao suportado e valor vazio explicito.
Nenhum runtime wiring foi implementado, BUZ29-PENNY nao foi executado e
`lot-pkn` permanece inalterado. A proxima fase recomendada e
`PHASE11_10V_SPECIFY_RUNTIME_WIRING_IMPLEMENTATION_PLAN`.

---

### [2026-06-12] Fase 11.10T — especificacao do wiring runtime do fracture gate — Codex

**Status:** Concluido; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/spec_phase11_10t_fracture_gate_runtime_wiring.py
```

**Documento criado:**

```text
docs/94_fracture_gate_runtime_wiring_spec.md
```

**Resultado:**

```text
PHASE11_10T_FRACTURE_GATE_RUNTIME_WIRING_SPECIFIED
FRACTURE_GATE_RUNTIME_WIRING_SPECIFIED
FRACTURE_MODEL_SELECTOR_REQUIRED
SIGMATHETA_INITIAL_STATE_GUARD_REQUIRED
PRESSURE_SIGMATHETA_CRITERION_GUARD_REQUIRED
RUNTIME_WIRING_NOT_IMPLEMENTED
DISPATCH_REMAINS_BLOCKED
```

**Interpretacao:** a fase especifica a sequencia futura
`FractureModelSelector -> SigmaThetaInitialStateGuard ->
PressureSigmaThetaFractureCriterionGuard -> dispatch`, mas nao implementa
runtime wiring. PKN permanece default retrocompativel. `PENNY_SHAPED` continua
diagnostico, nao fisicamente validado e nao equivalente ao legado. BUZ29-PENNY
permanece bloqueado. A proxima fase recomendada e
`PHASE11_10U_SPECIFY_RUNTIME_WIRING_TEST_FIXTURES`.

---

### [2026-06-12] Fase 11.10S — guard do criterio pressao x sigma-theta — Codex

**Status:** Concluido; commit/push executado ao final da fase se todos os
gates passarem.

**Arquivos C++ criados:**

```text
include/lot/PressureSigmaThetaFractureCriterionGuard.hpp
src/lot/PressureSigmaThetaFractureCriterionGuard.cpp
tests/cpp/test_pressure_sigma_theta_fracture_criterion_guard.cpp
```

**Ferramenta criada:**

```text
tools/audit_phase11_10s_pressure_sigmatheta_fracture_criterion_guard.py
```

**Documento criado:**

```text
docs/93_pressure_sigmatheta_fracture_criterion_guard_implementation.md
```

**Resultado:**

```text
PHASE11_10S_PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD_IMPLEMENTED
PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD_IMPLEMENTED
SIGMATHETA_COMPRESSION_POSITIVE_CRITERION_IMPLEMENTED
PRESSURE_GREATER_THAN_SIGMATHETA_SHORTCUT_FORBIDDEN
RUNTIME_DISPATCH_NOT_CHANGED
LOT_PKN_BEHAVIOR_NOT_CHANGED
```

**Interpretacao:** a fase implementa apenas o helper C++ isolado que avalia
`sigma_theta_current_compression_positive_Pa <= -tensile_strength_Pa` por meio
de `tensile_condition_Pa` e `fracture_margin_Pa`, com forma alternativa por
`fracture_threshold_pressure_Pa` somente quando explicitamente selecionada. A
fase nao integra runtime, nao altera parser/schema, `PknModel`, `PknRunner`,
CLI ou `lot-pkn`, e nao executa BUZ29-PENNY. A proxima fase recomendada e
`PHASE11_10T_SPECIFY_FRACTURE_GATE_RUNTIME_WIRING_WITH_GUARDS`.

---

### [2026-06-12] Fase 11.10R — especificacao do criterio pressao x sigma-theta — Codex

**Status:** Concluido; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/spec_phase11_10r_pressure_sigmatheta_fracture_criterion.py
```

**Documento criado:**

```text
docs/92_pressure_sigmatheta_fracture_criterion_spec.md
```

**Resultado:**

```text
PHASE11_10R_PRESSURE_SIGMATHETA_FRACTURE_CRITERION_SPECIFIED
PRESSURE_SIGMATHETA_FRACTURE_CRITERION_SPECIFIED
SIGMATHETA_COMPRESSION_POSITIVE_SIGN_CONVENTION_RESOLVED
PRESSURE_GREATER_THAN_SIGMATHETA_SHORTCUT_FORBIDDEN
DISPATCH_REMAINS_BLOCKED_UNTIL_CRITERION_GUARD_IMPLEMENTED
```

**Interpretação:** a fase especifica a algebra futura para o
`fracture_initiation_gate` com `sigma_theta` em convencao
compression-positive. O criterio preferencial e
`sigma_theta_current_compression_positive_Pa <= -tensile_strength_Pa`; a forma
alternativa por threshold exige `fracture_threshold_pressure_Pa` derivada de
`sigma_theta`, resistencia a tracao e referencial explicito. A fase nao altera
C++, parser/schema, `PknModel`, `PknRunner`, CLI ou `lot-pkn`, e nao executa
BUZ29-PENNY. A proxima fase recomendada e
`PHASE11_10S_IMPLEMENT_PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD`.

---

### [2026-06-12] Fase 11.10Q — especificacao do dispatch com sigma-theta guard — Codex

**Status:** Concluido; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/spec_phase11_10q_fracture_gate_dispatch_with_sigmatheta_guard.py
```

**Documento criado:**

```text
docs/91_fracture_gate_dispatch_with_sigmatheta_guard_spec.md
```

**Resultado:**

```text
PHASE11_10Q_FRACTURE_GATE_DISPATCH_WITH_SIGMATHETA_GUARD_SPECIFIED
FRACTURE_GATE_DISPATCH_WITH_SIGMATHETA_GUARD_SPECIFIED
SIGMATHETA_GUARD_REQUIRED_BEFORE_DISPATCH
FRACTURE_MODEL_SELECTOR_REQUIRED_BEFORE_DISPATCH
PRESSURE_SIGMATHETA_CRITERION_SPEC_REQUIRED
SIGN_CONVENTION_RESOLUTION_REQUIRED
DISPATCH_REMAINS_BLOCKED
```

**Interpretação:** a fase especifica o fluxo futuro
`FractureModelSelector -> SigmaThetaInitialStateGuard -> criterio pressao x
sigma_theta -> dispatch`. Ela nao integra o guard ao runtime, nao altera C++,
parser/schema ou `lot-pkn`, nao executa BUZ29-PENNY e mantem
`dispatch_allowed_next = false`. A proxima fase recomendada e
`PHASE11_10R_SPECIFY_PRESSURE_SIGMATHETA_FRACTURE_CRITERION`.

---

### [2026-06-12] Fase 11.10P — implementacao do guard sigma-theta inicial — Codex

**Status:** Concluido; commit/push executado ao final da fase se todos os
gates passarem.

**Arquivos C++ criados:**

```text
include/lot/SigmaThetaInitialStateGuard.hpp
src/lot/SigmaThetaInitialStateGuard.cpp
tests/cpp/test_sigma_theta_initial_state_guard.cpp
```

**Ferramenta criada:**

```text
tools/audit_phase11_10p_sigmatheta_initial_state_guard.py
```

**Documento criado:**

```text
docs/90_sigmatheta_initial_state_guard_implementation.md
```

**Resultado:**

```text
PHASE11_10P_SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED
SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED
RUNTIME_DISPATCH_NOT_CHANGED
PARSER_SCHEMA_NOT_CHANGED
LOT_PKN_BEHAVIOR_NOT_CHANGED
DISPATCH_REMAINS_BLOCKED
```

**Interpretação:** a fase implementa somente o helper isolado de validacao do
estado inicial `sigma_theta_compression_positive_Pa`. O guard bloqueia
sigma-theta ausente, invalido, fonte desconhecida, tempo incorreto,
referencial desconhecido, sinal desconhecido e incompatibilidade pressao x
sigma-theta. Ele ainda nao e integrado ao parser, schema, `PknModel`,
`PknRunner`, CLI ou runtime; BUZ29-PENNY nao e executado.

---

### [2026-06-12] Fase 11.10O — especificação do wiring sigma-theta inicial — Codex

**Status:** Concluído; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/spec_phase11_10o_sigmatheta_initial_state_wiring.py
```

**Documento criado:**

```text
docs/89_sigmatheta_initial_state_wiring_spec.md
```

**Resultado:**

```text
PHASE11_10O_SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED
SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED
ELASTIC_INITIAL_WELLBORE_STATE_SELECTED_AS_PREFERRED_SOURCE
FRACTURE_GATE_BLOCKED_UNTIL_SIGMATHETA_INITIALIZED
PRESSURE_SIGMATHETA_COMPATIBILITY_REQUIRED
DISPATCH_REMAINS_BLOCKED
```

**Interpretação:** a fase não implementa wiring, não altera C++/parser/schema
e não executa BUZ29-PENNY. Ela especifica o contrato futuro para
`sigma_theta_initial_compression_positive_Pa`, incluindo fonte preferencial
`ELASTIC_INITIAL_WELLBORE_STATE`, campos obrigatórios, regras de bloqueio do
gate, matriz pressão × sigma-theta e convenção `COMPRESSION_POSITIVE`.
`implementation_allowed_next = true` apenas para
`PHASE11_10P_IMPLEMENT_SIGMATHETA_INITIAL_STATE_WIRING_GUARD`;
`dispatch_allowed_next` e `runtime_execution_allowed_next` permanecem falsos.

---

### [2026-06-12] Fase 11.10N — auditoria do estado inicial sigma-theta — Codex

**Status:** Concluído; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/audit_phase11_10n_fracture_gate_initial_sigmatheta.py
```

**Documento criado:**

```text
docs/88_fracture_gate_initial_sigmatheta_audit.md
```

**Resultado:**

```text
PHASE11_10N_FRACTURE_GATE_INITIAL_SIGMATHETA_AUDITED
SIGMATHETA_INITIAL_STATE_MISSING
FRACTURE_GATE_REQUIRES_INITIAL_STATE_WIRING
PRESSURE_SIGMATHETA_SEMANTICS_PARTIAL_REQUIRES_ALIGNMENT
SIGN_CONVENTION_REQUIRES_REVIEW
DISPATCH_REMAINS_BLOCKED_UNTIL_GATE_SAFE
```

**Interpretação:** o runtime já possui rotas diagnósticas que consomem
`sigma_theta_static`, `sigma_theta_time_series` ou provider, mas ainda não
existe prova de um `sigma_theta_initial_after_drilling` calculado e alinhado
antes do gate de fratura. `fracture_model` permanece metadata/seleção; dispatch
físico e BUZ29-PENNY continuam bloqueados. Próxima fase recomendada:
`PHASE11_10O_SPECIFY_SIGMATHETA_INITIAL_STATE_WIRING`.

---

### [2026-06-12] Fase 11.10M — integração parser/schema de `fracture_model` — Codex

**Status:** Concluído; commit/push executado ao final da fase se todos os
gates passarem.

**Arquivos principais:**

```text
include/core/types.hpp
src/io/CaseParser.cpp
schemas/lot_case.schema.yaml
tests/cpp/test_case_parser.cpp
tools/audit_phase11_10m_fracture_model_parser_schema_integration.py
docs/87_fracture_model_parser_schema_integration.md
```

**Resultado:**

```text
PHASE11_10M_FRACTURE_MODEL_PARSER_SCHEMA_INTEGRATED
PKN_DEFAULT_WHEN_FRACTURE_MODEL_MISSING
PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY
RUNTIME_DISPATCH_NOT_ENABLED
SIGMATHETA_INITIAL_STATE_AUDIT_REQUIRED_BEFORE_DISPATCH
```

**Interpretação:** `lot.fracture.fracture_model` agora é aceito pelo schema e
interpretado pelo parser via `FractureModelSelector`. Campo ausente seleciona
`PKN`; `PENNY_SHAPED` explícito é apenas metadado diagnóstico, não validado e
sem dispatch runtime. BUZ29-PENNY continua bloqueado até auditoria do estado
inicial de `sigma_theta`.

---

### [2026-06-12] Fase 11.10L — especificação parser/schema de `fracture_model` — Codex

**Status:** Concluído; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/spec_phase11_10l_parser_schema_fracture_model_integration.py
```

**Documento criado:**

```text
docs/86_fracture_model_parser_schema_integration_spec.md
```

**Resultado:**

```text
PHASE11_10L_FRACTURE_MODEL_PARSER_SCHEMA_INTEGRATION_SPECIFIED
FRACTURE_MODEL_FIELD_LOT_FRACTURE_FRACTURE_MODEL
PKN_DEFAULT_PARSER_BEHAVIOR_REQUIRED
EXPLICIT_EMPTY_FRACTURE_MODEL_BLOCKED
UNSUPPORTED_FRACTURE_MODELS_BLOCKED
PARSER_SCHEMA_INTEGRATION_ALLOWED_NEXT
RUNTIME_EXECUTION_NOT_ALLOWED_NEXT
BUZ29_EXECUTION_NOT_ALLOWED_NEXT
```

**Interpretação:** a próxima fase pode integrar parser/schema com política
`SCHEMA_STRICT_CANONICAL_ONLY`, preservando PKN como default quando
`fracture_model` estiver ausente. Runtime não-PKN e BUZ29-PENNY continuam
bloqueados.

---

### [2026-06-12] Fase 11.10K — implementação do guard `fracture_model` — Codex

**Status:** Concluído; commit/push executado ao final da fase se todos os
gates passarem.

**Arquivos C++ criados:**

```text
include/lot/FractureModelSelector.hpp
src/lot/FractureModelSelector.cpp
tests/cpp/test_fracture_model_selector.cpp
```

**Ferramenta criada:**

```text
tools/audit_phase11_10k_fracture_model_selector_guard.py
```

**Documento criado:**

```text
docs/85_fracture_model_selector_guard_implementation.md
```

**Resultado:**

```text
PHASE11_10K_FRACTURE_MODEL_SELECTOR_GUARD_IMPLEMENTED
FRACTURE_MODEL_SELECTOR_GUARD_IMPLEMENTED
PKN_DEFAULT_WHEN_FRACTURE_MODEL_MISSING
PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY
EXPLICIT_EMPTY_FRACTURE_MODEL_BLOCKED
UNSUPPORTED_FRACTURE_MODELS_BLOCKED
PARSER_SCHEMA_RUNTIME_NOT_INTEGRATED
```

**Interpretação:** o guard agora existe como helper C++ isolado e testado.
Ausência de `fracture_model` defaulta para PKN; valor vazio explícito é erro;
`PENNY_SHAPED` continua opt-in diagnóstico, não validado e não equivalente ao
legado. A fase não integra parser, schema, CLI ou runtime e não executa
BUZ29-PENNY.

---

### [2026-06-12] Fase 11.10J — guard do seletor `fracture_model` — Codex

**Status:** Concluído; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/spec_phase11_10j_fracture_model_selector_guard.py
```

**Documento criado:**

```text
docs/84_fracture_model_selector_guard_spec.md
```

**Resultado:**

```text
FRACTURE_MODEL_SELECTOR_GUARD_SPECIFIED
PKN_DEFAULT_WHEN_ABSENT
EXPLICIT_EMPTY_FRACTURE_MODEL_REJECTED
PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY
UNSUPPORTED_FRACTURE_MODELS_BLOCKED
FRACTURE_INITIATION_GATE_REQUIRED
SIGMATHETA_SIGN_CONVENTION_REQUIRED
NO_RUNTIME_CHANGE_IN_11_10J
```

**Interpretação:** a ausência de `lot.fracture.fracture_model` preserva o
default PKN, enquanto valor vazio explícito deve ser erro. `PENNY_SHAPED`
continua opt-in diagnóstico, não validado fisicamente e sem equivalência legada.
A seleção não implica execução: ainda exige `fracture_initiation_gate` e
convenção explícita de sinal para `sigma_theta`.

---

### [2026-06-12] Fase 11.10I — seleção unificada `fracture_model` — Codex

**Status:** Concluído; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/decide_phase11_10i_unified_fracture_model_selection.py
```

**Documento criado:**

```text
docs/83_unified_fracture_model_selection.md
```

**Decisão arquitetural:**

```text
UNIFIED_LOT_FRACTURE_RUNTIME_SELECTED
PKN_DEFAULT_FRACTURE_MODEL
PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY
UNSUPPORTED_FRACTURE_MODELS_BLOCKED
FRACTURE_INITIATION_GATE_REQUIRED
SIGMATHETA_SIGN_CONVENTION_REQUIRED
```

**Interpretação:** a recomendação anterior de runner não-PKN fica reconciliada
como um futuro selector guard dentro de uma rota LOT/fracture unificada.
`lot.fracture.fracture_model` é o campo recomendado, `PKN` permanece default
quando ausente e `PENNY_SHAPED` segue opt-in explícito, diagnóstico, não
fisicamente validado e sem equivalência legada. A fase não implementa runner,
não altera C++, parser, schema ou `lot-pkn`, e não executa BUZ29-PENNY.

---

### [2026-06-12] Fase 11.10H — gate do runner diagnóstico não-PKN — Codex

**Status:** Concluído; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/decide_phase11_10h_non_pkn_diagnostic_runner_gate.py
```

**Documento criado:**

```text
docs/82_non_pkn_diagnostic_runner_gate.md
```

**Resultado:**

```text
NON_PKN_DIAGNOSTIC_RUNNER_SPEC_PARTIAL
RUNNER_IMPLEMENTATION_NOT_ALLOWED_IN_11_10H
BUZ29_RUNTIME_EXECUTION_NOT_ALLOWED
LOT_PKN_IMPACT_NOT_ALLOWED
```

**Interpretação:** adapter e writer PennyShaped existem e estão isolados, mas
o candidato BUZ29-PENNY continua parcial para execução. A fase autoriza apenas
especificar um runner diagnóstico futuro; não implementa runner, não executa
BUZ29-PENNY, não altera C++ e não toca no fluxo `lot-pkn`.

---

### [2026-06-12] Fase 11.10G — writer diagnóstico PennyShaped opt-in — Codex

**Status:** Concluído; commit/push executado ao final da fase se todos os
gates passarem.

**Arquivos C++ criados:**

```text
include/lot/PennyShapedDiagnosticWriter.hpp
src/lot/PennyShapedDiagnosticWriter.cpp
tests/cpp/test_penny_shaped_diagnostic_writer.cpp
```

**Ferramenta criada:**

```text
tools/check_phase11_10g_penny_writer_against_fixtures.py
```

**Documento criado:**

```text
docs/81_penny_diagnostic_writer_implementation.md
```

**Resultado:**

```text
PENNY_DIAGNOSTIC_WRITER_IMPLEMENTED_OPT_IN
NO_BUZ29_RUNTIME_EXECUTION
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
```

**Interpretação:** a fase implementa apenas o writer diagnóstico PennyShaped
opt-in. Ele emite JSON/CSV em memória, preserva valores internos em 1 rad,
calcula equivalentes volumétricos 2π com `source` explícito e rejeita flags que
confundiriam o artefato com validação física, equivalência legada ou caso
ativo. A fase não implementa runner não-PKN, não executa BUZ29-PENNY e não
altera `lot-pkn`.

---

### [2026-06-12] Fase 11.10F — especificação do writer diagnóstico PennyShaped — Codex

**Status:** Concluído; commit/push executado ao final da fase se todos os
gates passarem.

**Ferramenta criada:**

```text
tools/spec_phase11_10f_penny_diagnostic_writer.py
```

**Documento criado:**

```text
docs/80_penny_diagnostic_writer_spec.md
```

**Resultado:**

```text
writer_spec_status = PENNY_DIAGNOSTIC_WRITER_SPECIFIED
implementation_allowed = false
runtime_execution_allowed = false
requires_cpp_implementation_future = true
fixture_contract_valid = true
recommended_next_phase = PHASE11_10G_IMPLEMENT_PENNY_DIAGNOSTIC_WRITER_OPT_IN
```

**Interpretação:** a fase especifica o writer diagnóstico PennyShaped futuro,
mas não implementa C++, não executa BUZ29-PENNY, não altera `lot-pkn`, não
declara validação física e não declara equivalência com legado. A especificação
preserva as grandezas internas em 1 rad, equivalentes 2π com `source` e o
`volume_multiplier` como empírico, não como fator geométrico `2π`.

---

### [2026-06-12] Fase 11.10F-aux — restrição standalone do SESTSAL legado — Codex

**Status:** Concluído; commit executado ao final da fase se todos os gates
passarem.

**Ferramenta criada:**

```text
tools/audit_legacy_sestsal_standalone_constraint.py
```

**Documento criado:**

```text
docs/79_legacy_sestsal_standalone_constraint.md
```

**Resultado:**

```text
cause = LEGACY_SESTSAL_REQUIRES_APB1DA_COUPLING
gate = DO_NOT_USE_SESTSAL_STANDALONE_AS_VALIDATION_REFERENCE
secondary_cause = ELASTIC_DISPLACEMENT_REFERENCE_MISMATCH
secondary_gate = ALIGN_TOTAL_VS_PERTURBATION_DISPLACEMENT_BEFORE_COMPARISON
standalone_validation_supported = false
```

**Interpretação:** a auditoria registra que `Material::creepFunction(...)`
normaliza por `norm_sigd` sem guarda explícita para estado hidrostático puro.
Logo, testes que chamem SESTSAL legado isoladamente devem ser classificados
como unsupported; a referência válida do legado permanece o uso acoplado via
`APB1da`. Comparações de deslocamento total legado contra deslocamento
perturbacional moderno continuam bloqueadas sem alinhamento de referencial.

---

### [2026-06-12] Fase 11.10E — fixtures de saída diagnóstica PennyShaped — Codex

**Status:** Concluído; commit/push executado ao final da fase se todos os gates
passarem.

**Fixtures criados:**

```text
tests/fixtures/comparison/phase11_10e/penny_diagnostic_output_expected.json
tests/fixtures/comparison/phase11_10e/penny_diagnostic_output_expected.csv
tests/fixtures/comparison/phase11_10e/penny_diagnostic_output_metadata.json
```

**Ferramenta criada:**

```text
tools/validate_phase11_10e_penny_output_fixtures.py
```

**Documento criado:**

```text
docs/78_penny_diagnostic_output_fixtures.md
```

**Resultado:**

```text
fixture_status = PENNY_DIAGNOSTIC_OUTPUT_FIXTURES_VALID
implementation_status = FIXTURE_ONLY_NO_RUNTIME_WRITER
implementation_allowed = false
volume_multiplier_interpretation = VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
contract_materialized = AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_MATERIALIZED_AS_FIXTURE
recommended_next_phase = PHASE11_10F_SPECIFY_PENNY_DIAGNOSTIC_WRITER_IMPLEMENTATION
```

**Interpretação:** a fase materializa o contrato 1 rad ↔ 2π em fixtures
versionados e verificáveis, mas não implementa writer, não altera runtime, não
executa BUZ29-PENNY, não declara validação física e não transforma o fixture em
caso ativo.

---

### [2026-06-12] Fase 11.10D — contrato de saída 1 rad ↔ 2π — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/spec_phase11_10d_axisymmetric_output_contract.py
```

**Documento criado:**

```text
docs/77_axisymmetric_1rad_2pi_output_contract.md
```

**Resultado:**

```text
contract_status = AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_SPECIFIED
axisymmetric_angle_rad = 1.0
volume_conversion_factor_1rad_to_2pi = 6.283185307179586
volume_multiplier_semantics = VOLUME_MULTIPLIER_EMPIRICAL
implementation_allowed = false
recommended_next_phase = PHASE11_10E_DEFINE_PENNY_DIAGNOSTIC_OUTPUT_FIXTURES
```

**Interpretação:** a fase define contrato de saída, não runtime. O
`volume_multiplier` permanece empírico e não é fator geométrico `2π`. Toda
saída volumétrica física futura deve preservar o valor de origem em 1 rad e
reportar separadamente equivalente 2π com `source`/caveat.

---

### [2026-06-12] Fase 11.10C — auditoria matemática PennyShaped 1 rad — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/audit_phase11_10c_penny_math_axisymmetric_1rad.py
```

**Documento criado:**

```text
docs/76_penny_math_axisymmetric_1rad_audit.md
```

**Resultado:**

```text
primary_classification = PENNY_MATH_HYDRAULIC_DIAGNOSTIC_SCALING
secondary_classification = PENNY_MATH_AXISYMMETRIC_1RAD_PROXY
tertiary_classification = PENNY_MATH_LEGACY_INSPIRED_EMPIRICAL
pressure_semantics = PRESSURE_SEMANTICS_CLEAR
volume_multiplier_semantics = VOLUME_MULTIPLIER_EMPIRICAL
math_audit_passed = true
requires_code_correction = false
requires_output_contract = true
recommended_next_phase = PHASE11_10D_DEFINE_AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT
```

**Interpretação:** as relações de abertura e raio do `PennyShapedModel` são
dimensionalmente consistentes para uso diagnóstico hidráulico. O campo
`fracture_volume_proxy_m3` deve permanecer proxy axissimétrico de 1 rad, com
contrato explícito futuro para separar volume interno 1-rad de volume total
equivalente 2π. A fase não executa BUZ29-PENNY, não valida BUZ29 e não altera
código C++.

---

### [2026-06-12] Fase 11.10B — entradas adapter-ready BUZ29-PENNY — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/inspect_phase11_10b_buz29_penny_adapter_ready_inputs.py
```

**Documento criado:**

```text
docs/75_buz29_penny_adapter_ready_inputs.md
```

**Resultado:**

```text
classification = BUZ29_PENNY_ADAPTER_INPUTS_PARTIAL
adapter_ready = false
partial_adapter_ready = true
physically_validated = false
legacy_equivalent = false
active_simulation_case = false
recommended_next_phase = PHASE11_10C_AUDIT_PENNY_SHAPED_MODEL_MATH_AXISYMMETRIC_1RAD
```

**Interpretação:** pressão e abertura BUZ29 são evidências consumíveis, mas o
candidato ainda não possui todos os campos exigidos pelo
`PennyShapedDiagnosticAdapter` como entradas diretas e semanticamente prontas.
A próxima etapa segura é auditoria matemática da formulação axissimétrica de 1
rad, não execução BUZ29.

---

### [2026-06-12] Fase 11.10A — rota diagnóstica BUZ29-PENNY — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Artefatos criados:**

```text
cases/validation/non_pkn/buz29_penny_candidate.yaml
cases/validation/non_pkn/studies_index.yaml
tools/inspect_phase11_10a_buz29_penny_candidate.py
tests/python/test_inspect_phase11_10a_buz29_penny_candidate.py
docs/74_buz29_penny_diagnostic_route.md
```

**Resultado:**

```text
classification = BUZ29_PENNY_DIAGNOSTIC_ROUTE_PARTIAL_STARTED
route_started = true
physically_validated = false
legacy_equivalent = false
active_simulation_case = false
```

**Caveats obrigatórios:**

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
NOT_ACTIVE_SIMULATION_CASE
```

**Interpretação:** a 11.10A formaliza um candidato diagnóstico inativo. Ela não
executa BUZ29, não cria rota runtime oficial, não altera `lot-pkn`, não valida
fisicamente o caso e não declara equivalência com o legado. A próxima etapa
segura é `PHASE11_10B_INSPECT_BUZ29_PENNY_ADAPTER_READY_INPUTS`.

---

### [2026-06-12] Fase 11.9F — readiness BUZ29-PENNY após pressão e abertura — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/reevaluate_phase11_9f_buz29_penny_readiness.py
```

**Documento criado:**

```text
docs/73_buz29_penny_readiness_after_pressure_opening.md
```

**Resultado:**

```text
updated_readiness = BUZ29_PENNY_CANDIDATE_PARTIAL_BUT_DIAGNOSTIC_SAFE
can_start_11_10A = true
gate = BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A
recommended_next_phase = PHASE11_10A_START_BUZ29_PENNY_DIAGNOSTIC_ROUTE
axisymmetric_interpretation = PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
```

**Interpretação:** a 11.10A pode iniciar apenas como preparação diagnóstica.
A 11.9F não executa BUZ29-PENNY, não cria YAML candidato, não cria `study_id`,
não valida BUZ29 fisicamente e não declara equivalência com o legado. O proxy
de volume do `PennyShapedModel` deve ser tratado como formulação axissimétrica
de 1 rad, não como volume circular completo em 2π.

---

### [2026-06-12] Fase 11.9E — evidência BUZ29 de pressão e abertura — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/audit_phase11_9e_buz29_pressure_opening_evidence.py
```

**Documento criado:**

```text
docs/72_buz29_pressure_opening_evidence_audit.md
```

**Resultado:**

```text
pressure_history_status = PRESSURE_HISTORY_FOUND_CONSUMABLE
opening_time_status = OPENING_TIME_FOUND_CONSUMABLE
classification = BUZ29_PRESSURE_AND_OPENING_EVIDENCE_COMPLETE
can_reopen_11_10A_gate = true
recommended_next_phase = PHASE11_9F_REEVALUATE_BUZ29_PENNY_READINESS_AFTER_PRESSURE_OPENING
```

**Interpretação:** o output legado existente
`legance/LOT_Tese/results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat` contém série
`Time`, blocos `dP` e `Momento da quebra: 10.4`. A fase não executa BUZ29,
não cria YAML candidato e não valida fisicamente o caso; ela apenas reabre a
possibilidade de uma reavaliação formal do readiness na 11.9F.

---

### [2026-06-11] Fase 11.8B — gate de integração penny-shaped — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/decide_phase11_8b_penny_integration.py
```

**Documento criado:**

```text
docs/64_penny_integration_gate.md
```

**Decisão:**

```text
PENNY_ADAPTER_OPT_IN_SELECTED
selected_integration_path = diagnostic_adapter
recommended_next_phase = PHASE11_8C_PENNY_ADAPTER_SPEC
```

**Interpretação:** a fase seleciona apenas o caminho de adapter diagnóstico
opt-in. Não valida BUZ29, não declara equivalência com o legado e não cria rota
oficial do `lot-sim`.

---

### [2026-06-11] Fase 11.8A — núcleo mínimo penny-shaped — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**C++ criado:**

```text
include/lot/PennyShapedModel.hpp
src/lot/PennyShapedModel.cpp
tests/cpp/test_penny_shaped_model.cpp
```

**Documento criado:**

```text
docs/63_selected_non_pkn_model_minimal_implementation.md
```

**Resultado:**

```text
SELECTED_NON_PKN_MINIMAL_MODEL_IMPLEMENTED
selected_track = PENNY_SHAPED
runtime_integration = false
parser_schema_changed = false
physical_validation = false
```

**Interpretação:** a fase implementa apenas as fórmulas isoladas auditadas para
`penny_shaped`. Não conecta parser, schema oficial, CLI, PKN, BUZ29 ou runtime
LOT/APB/sal.

---

### [2026-06-11] Fase 11.7C — especificação YAML/IO penny-shaped — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/validate_phase11_7c_selected_model_yaml_spec.py
```

**Fixture criada:**

```text
tests/fixtures/comparison/phase11_7c_selected_model_case_fixture.yaml
```

**Documento criado:**

```text
docs/62_selected_non_pkn_model_yaml_io_spec.md
```

**Resultado:**

```text
SELECTED_MODEL_YAML_IO_SPECIFIED
schema_status = SPEC_FIXTURE_ONLY_NOT_RUNTIME_SCHEMA
recommended_next_phase = PHASE11_8A_MINIMAL_SELECTED_NON_PKN_MODEL
```

**Interpretação:** a fase congela o contrato de entradas/saídas para um núcleo
`penny_shaped` mínimo e isolado. Parser, schema oficial, runtime, CLI e casos
protegidos permanecem inalterados.

---

### [2026-06-11] Fase 11.7B — auditoria matemática penny-shaped — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/audit_phase11_7b_selected_model_math.py
```

**Documento criado:**

```text
docs/61_selected_non_pkn_model_math_audit.md
```

**Resultado:**

```text
SELECTED_MODEL_MATH_AUDITED
selected_track = PENNY_SHAPED
implementation_readiness = MINIMAL_IMPLEMENTATION_READY_DIAGNOSTIC_ONLY
recommended_next_phase = PHASE11_7C_SELECTED_MODEL_YAML_IO_SPEC
```

**Interpretação:** foram extraídas as relações legadas mínimas para abertura,
raio, fator de pressão e volume proxy penny-shaped. A fase não implementa
modelo moderno e não declara validação BUZ29.

---

### [2026-06-11] Fase 11.7A — decisão de trilha pós-BUZ29 — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/decide_phase11_7a_next_model_track.py
```

**Documento criado:**

```text
docs/60_phase11_7a_next_model_track_decision.md
```

**Decisão:**

```text
NEXT_MODEL_TRACK_SELECTED
selected_track = PENNY_SHAPED
recommended_next_phase = PHASE11_7B_LEGACY_MATH_AUDIT_SELECTED_MODEL
```

**Interpretação:** BUZ29-VISCO-first-well não deve ser convertido para PKN por
inferência. A primeira trilha não-PKN deve auditar a formulação
`penny-shaped`; esta fase não implementa modelo físico e não declara validação
do BUZ29.

---

### [2026-06-11] Fase 11.5D — maxima em summaries LOT/PKN — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/audit_phase11_5d_summary_maxima.py
```

**Documento criado:**

```text
docs/59_summary_fracture_leakoff_maxima.md
```

**Runner atualizado:**

```text
tools/run_lot_pkn_sensitivity_matrix.py
```

**Campos adicionados ao `summary.csv`:**

```text
max_fracture_volume_m3
max_leakoff_volume_m3
max_fracture_length_m
max_fracture_width_m
max_net_pressure_Pa
```

**Gate:** `SUMMARY_MAXIMA_PYTHON_ONLY_SAFE`. Os campos já existem em
`timeseries.csv`, então não houve alteração C++, parser, schema, writer ou
casos protegidos.

---

### [2026-06-11] Fase 11.6B — roadmap não-PKN — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/plan_phase11_6b_non_pkn_models.py
```

**Documento criado:**

```text
docs/58_non_pkn_model_roadmap.md
```

**Status registrado:**

```text
NON_PKN_MODEL_ROADMAP_RECORDED
NEXT_PHASE = PHASE11_6C_PENNY_SHAPED_FORMULATION_AUDIT
```

**Interpretação:** BUZ29-VISCO-first-well permanece fora de LOT/PKN moderno
porque o modelo ativo é `penny-shaped`. A próxima etapa segura é auditar a
formulação `penny-shaped`; KGD/circular e Zamora ficam em trilhas separadas.

---

### [2026-06-11] Fase 11.6A — auditoria BUZ29-VISCO-first-well — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/audit_phase11_6a_buz29_visco_first_well.py
```

**Documento criado:**

```text
docs/57_buz29_visco_first_well_audit.md
```

**Resultado:**

```text
BUZ29_VISCO_FIRST_WELL_SOURCE_FOUND
BUZ29_VISCO_FIRST_WELL_NOT_PKN
BUZ29_VISCO_FIRST_WELL_MODERN_YAML_NOT_READY
NEXT_PHASE_NON_PKN_ROADMAP
```

**Interpretação:** `BUZ29-VISCO-first-well.cpp` existe e contém parâmetros
úteis, mas o modelo ativo é `penny-shaped`; a linha PKN está comentada. A fase
não cria YAML moderno BUZ29 e recomenda roadmap não-PKN.

---

### [2026-06-11] Fase 11.5C — consolidação BUZ-67D modern-refined — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/summarize_phase11_5_buz67d_sensitivities.py
```

**Documento criado:**

```text
docs/56_buz67d_modern_refined_sensitivity_consolidation.md
```

**Status registrado:**

```text
BUZ67D_MODERN_REFINED_SENSITIVITIES_CONSOLIDATED
PHASE11_5C_BUZ67D_SENSITIVITY_CONSOLIDATED
NEXT_PHASE_BUZ29_VISCO_FIRST_WELL_AUDIT
```

**Interpretação:** `C_geom` controla rigidez aparente, pressão máxima e tempo
de abertura; `sink_timing` controla principalmente o atraso operacional do sink.
`C_geom=0.75x` permanece melhor ranking diagnóstico combinado, enquanto
`C_geom=0.55x` é melhor para pressão máxima. Nenhum dos dois é calibração
física.

---

### [2026-06-11] Fase 11.5B — matriz C_geom x sink_timing BUZ-67D — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Matriz criada:**

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_sink_timing_matrix_v2.yaml
```

**Estudo registrado:**

```text
buz67d_cgeom_sink_timing_sensitivity_v2
```

**Ferramenta criada:**

```text
tools/analyze_phase11_5b_cgeom_sink_timing.py
```

**Documento criado:**

```text
docs/55_buz67d_cgeom_sink_timing_sensitivity.md
```

**Resultado diagnóstico observado:**

```text
classification = CGEOM_SINK_TIMING_MATRIX_ANALYZED
scenario_count = 8
mean_opening_delta_next_minus_same_s = 0.0
mean_sink_delay_delta_next_minus_same_s = 30.0
mean_max_pressure_delta_next_minus_same_Pa = 1821956.0465000253
sink_delay_reproduced_where_expected = true
```

**Caveat:** a matriz separa efeitos diagnósticos de `C_geom` e
`sink_timing`, mas não estabelece calibração física nem equivalência estrita
com o legado.

---

### [2026-06-11] Fase 11.5A — matriz estendida C_geom BUZ-67D — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Matriz criada:**

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_extended_matrix_v2.yaml
```

**Estudo registrado:**

```text
buz67d_cgeom_extended_sensitivity_v2
```

**Ferramenta criada:**

```text
tools/analyze_phase11_5a_cgeom_extended.py
```

**Documento criado:**

```text
docs/54_buz67d_cgeom_extended_sensitivity.md
```

**Resultado diagnóstico observado:**

```text
classification = CGEOM_EXTENDED_SENSITIVITY_ANALYZED
scenario_count = 12
best_by_opening_time = cgeom_075_next_step
best_by_max_pressure = cgeom_055_next_step
best_by_combined_score = cgeom_075_next_step
```

**Caveat:** os fatores de `C_geom` são variações diagnósticas do baseline
modern-refined. Não constituem calibração física automática nem validação
independente do modelo.

---

### [2026-06-11] Fase 11.4B — verificador de resultados LOT/PKN — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/verify_lot_pkn_study_results.py
```

**Documento criado:**

```text
docs/53_verify_lot_pkn_study_results.md
```

**Resultado esperado:**

```text
LOT_PKN_STUDY_RESULTS_VERIFIER_ADDED
STUDY_MANIFEST_VERIFICATION_AVAILABLE
```

O verificador checa `study_manifest.json` v1, outputs esperados, `summary.csv`,
`metadata.json`, relatórios opcionais e status de cenários. A verificação é
operacional; não valida fisicamente o modelo nem declara equivalência com o
legado.

---

### [2026-06-11] Fase 11.4A — provenance de estudos LOT/PKN — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Contrato criado:**

```text
study_manifest.json schema_version = 1
```

**Documentos criados:**

```text
docs/51_lot_pkn_study_manifest.md
docs/52_study_provenance.md
```

**Resultado esperado:**

```text
STUDY_MANIFEST_SCHEMA_V1_ADDED
LOT_PKN_STUDY_PROVENANCE_RECORDED
```

O comando canônico `tools/run_lot_pkn_study.py` agora registra provenance de
estudo, matriz, `base_case`, ambiente, Git, executável `lot-sim`, outputs,
cenários e comandos de reprodução. `results/` permanece artefato local não
versionado.

---

### [2026-06-11] Fase 11.3C — comando canônico LOT/PKN study — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/run_lot_pkn_study.py
```

**Documento criado:**

```text
docs/50_run_lot_pkn_study.md
```

**Resultado esperado:**

```text
CANONICAL_LOT_PKN_STUDY_COMMAND_ADDED
BUZ67D_CGEOM_STUDY_END_TO_END_COMMAND_AVAILABLE
```

O comando resolve `study_id`, delega a execução ao wrapper por estudo, gera
relatório quando há outputs reais e cria `study_manifest.json` e
`run_commands.txt` no diretório local de `results/`.

---

### [2026-06-11] Fase 11.3B — execução de estudos por study_id — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/run_lot_pkn_sensitivity_study.py
```

**Documento criado:**

```text
docs/49_run_sensitivity_by_study_id.md
```

**Resultado esperado:**

```text
SENSITIVITY_STUDY_ID_EXECUTION_ADDED
BUZ67D_CGEOM_SENSITIVITY_V2_RUNNABLE_BY_STUDY_ID
```

O estudo `buz67d_cgeom_sensitivity_v2` pode ser resolvido a partir de
`cases/validation/sensitivity/studies_index.yaml` e executado por wrapper fino
que delega ao runner genérico. A fase não altera solver, schema, runtime C++ ou
casos protegidos.

---

### [2026-06-11] Fase 11.3A — execução verificada da matriz v2 BUZ-67D — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/verify_phase11_3a_v2_sensitivity_run.py
```

**Documento criado:**

```text
docs/48_buz67d_parametric_matrix_v2_execution.md
```

**Resultado observado:**

```text
PHASE11_3A_V2_SENSITIVITY_RUN_OK
V2_REPRODUCES_V1_DIAGNOSTICS
```

A matriz `buz67d_modern_refined_cgeom_sensitivity_v2` foi executada com o
runner genérico. Os casos derivados foram materializados em `results/`, não
versionados, e reproduziram os diagnósticos documentados da matriz v1 para os
cenários selecionados.

---

### [2026-06-11] Fase 11.2C — runner com matriz paramétrica v2 — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Runner atualizado:**

```text
tools/run_lot_pkn_sensitivity_matrix.py
```

**Matriz v2 criada:**

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix_v2.yaml
```

**Resultado esperado:**

```text
SENSITIVITY_RUNNER_SUPPORTS_PARAMETRIC_MATRIX_V2
BUZ67D_CGEOM_SENSITIVITY_V2_REGISTERED
```

O runner preserva matrizes v1 e, para `schema_version: 2`, materializa cenários
em `<output-dir>/materialized_cases/` antes de validar/rodar.

---

### [2026-06-11] Fase 11.2B — materializador de casos paramétricos — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/materialize_lot_pkn_parametric_matrix.py
```

**Documento criado:**

```text
docs/47_parametric_case_materialization.md
```

**Resultado esperado:**

```text
PARAMETRIC_CASE_MATERIALIZER_ADDED
```

O materializador consome matrizes `schema_version: 2`, aplica overrides em
cópias do `base_case`, grava YAMLs derivados fora de `cases/` por padrão e
registra `materialization_manifest.json`. A integração automática com o runner
fica para 11.2C.

---

### [2026-06-11] Fase 11.2A — schema v2 de matriz paramétrica — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Documento criado:**

```text
docs/46_parametric_matrix_schema.md
```

**Ferramenta criada:**

```text
tools/validate_lot_pkn_parametric_matrix.py
```

**Resultado esperado:**

```text
PARAMETRIC_MATRIX_SCHEMA_V2_SPECIFIED
PARAMETRIC_MATRIX_VALIDATOR_ADDED
```

O contrato v2 declara `base_case + scenario.overrides` e preserva o formato v1
baseado em `scenario.case`. A fase ainda não materializa casos derivados nem
altera o runner; isso fica para 11.2B/11.2C.

---

### [2026-06-11] Fase 11.1B — índice multi-estudo de sensibilidade — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Índice criado:**

```text
cases/validation/sensitivity/studies_index.yaml
```

**Ferramenta criada:**

```text
tools/list_lot_pkn_sensitivity_studies.py
```

**Documento criado:**

```text
docs/45_sensitivity_studies_index.md
```

**Resultado:**

```text
STAGE11_1B_MULTI_STUDY_INDEX_ADDED
BUZ67D_CGEOM_SENSITIVITY_REGISTERED_AS_STUDY
```

O estudo `buz67d_cgeom_sensitivity` registra a matriz BUZ-67D C_geom
`modern-refined` existente. O runner permanece inalterado nesta fase e continua
recebendo `--matrix`; resolução por `study_id` fica como evolução futura.

---

### [2026-06-11] Fase 11.1A — plano técnico da Etapa 11 — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Documento criado:**

```text
docs/44_stage11_parametric_infrastructure_plan.md
```

**Ferramenta criada:**

```text
tools/plan_stage11_parametric_infrastructure.py
```

**Resultado:**

```text
STAGE11_PARAMETRIC_INFRASTRUCTURE_PLAN_RECORDED
NEXT_PHASE_STAGE11_1B_MULTI_STUDY_MATRIX_INDEX
```

A Etapa 11 foi aberta com foco em infraestrutura paramétrica `modern-refined`:
índices de estudos, matrizes reutilizáveis, execução reproduzível e relatórios
multi-estudo. Solver, schemas e casos protegidos permanecem fora do escopo.

---

### [2026-06-11] Fase 10.31B — fechamento da Etapa 10 e handoff para Etapa 11 — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Documento criado:**

```text
docs/43_phase10_closure_and_stage11_handoff.md
```

**Ferramenta criada:**

```text
tools/summarize_phase10_closure.py
```

**Resultado:**

```text
PHASE10_CLOSED_READY_FOR_STAGE11
STAGE11_PARAMETRIC_INFRASTRUCTURE_RECOMMENDED
```

Etapa 10 fica formalmente encerrada como pacote BUZ-67D `modern-refined`
reproduzível, com matriz versionada, runner, reporter e documentação
operacional. O fechamento reafirma que não há equivalência estrita com
`LOT_Tese`, sigmaTheta runtime real ou calibração física automática de
`C_geom`.

---

### [2026-06-11] Fase 10.31A — pacote reproduzível BUZ-67D modern-refined — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/run_buz67d_modern_refined_package.py
```

**Documento criado:**

```text
docs/42_buz67d_modern_refined_reproducible_package.md
```

**Resultado:**

```text
BUZ67D_MODERN_REFINED_REPRODUCIBLE_PACKAGE_ADDED
BUZ67D_MODERN_REFINED_PACKAGE_RUNNER_ADDED
```

O pacote orquestra validações mínimas, validações dos casos da matriz,
execução da matriz BUZ-67D `modern-refined` e geração de relatório
JSON/Markdown. Os artefatos permanecem locais em `results/` e não devem ser
versionados. A sensibilidade continua diagnóstica; `0.75x` não é calibração
automática nem validação física.

---

### [2026-06-11] Fase 10.30C — gerador de relatório de sensibilidade LOT/PKN — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Ferramenta criada:**

```text
tools/report_lot_pkn_sensitivity_matrix.py
```

**Documento criado:**

```text
docs/41_sensitivity_reporting.md
```

**Resultado:**

```text
SENSITIVITY_REPORT_GENERATED
```

O relatório consome `summary.csv` e `metadata.json` do runner genérico e emite
JSON/Markdown reproduzíveis. Com alvos legados documentados para BUZ-67D, o
ranking diagnóstico identifica `0.75x` por abertura e score combinado, e
`0.60x` por pressão máxima. Isso permanece pós-processamento diagnóstico, não
calibração automática.

---

### [2026-06-11] Fase 10.30B — execução verificada da matriz BUZ-67D versionada — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Runner usado:**

```text
tools/run_lot_pkn_sensitivity_matrix.py
```

**Verificador criado:**

```text
tools/verify_phase10_30b_sensitivity_run.py
```

**Documento criado:**

```text
docs/40_buz67d_versioned_sensitivity_run.md
```

**Resultado:**

```text
VERSIONED_SENSITIVITY_RUN_OK
```

A matriz versionada executou 10 cenários. O cenário `0.75x` abriu em `510 s`,
o baseline `1.0x` abriu em `660 s`, `1.25x` não abriu na janela e `same_step`
preservou abertura em `660 s` com `sink_delay = 0 s`. Esses resultados seguem
como sensibilidade diagnóstica, não calibração automática nem validação física.

---

### [2026-06-11] Fase 10.30A — matriz versionada BUZ-67D modern-refined — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Matriz criada:**

```text
cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml
```

**Documento criado:**

```text
docs/39_buz67d_modern_refined_cgeom_matrix.md
```

**Resultado:**

```text
VERSIONED_BUZ67D_CGEOM_SENSITIVITY_MATRIX_ADDED
```

A matriz referencia os cenários `0.60x..1.25x` e `same_step` já versionados,
passou em `dry-run` pelo runner genérico e permanece diagnóstica: não é
calibração automática nem rota `legacy-equivalence`.

---

### [2026-06-11] Fase 10.29C — auditoria dedicada BUZ-29D — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Documento criado:**

```text
docs/38_buz29d_legacy_audit.md
```

**Ferramenta criada:**

```text
tools/audit_phase10_29c_buz29d_case.py
```

**Resultado:**

```text
BUZ29D_LEGACY_AUDIT_RECORDED
BUZ29D_MODERN_YAML_NOT_READY
```

BUZ-29D possui fontes e saídas legadas, mas os fontes ativos auditados não
formam um caso PKN moderno pronto. Nenhum YAML moderno BUZ-29D foi criado.

---

### [2026-06-11] Fase 10.29B — runner genérico de sensibilidade LOT/PKN — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Documento criado:**

```text
docs/37_sensitivity_runner.md
```

**Ferramenta criada:**

```text
tools/run_lot_pkn_sensitivity_matrix.py
```

**Resultado:**

```text
GENERIC_LOT_PKN_SENSITIVITY_RUNNER_ADDED
```

O runner aceita matriz YAML, valida e roda cenários `lot-pkn`, sumariza
`timeseries.csv` e gera `summary.csv`/`metadata.json`. A ferramenta permanece
diagnóstica em `tools/` e não altera runtime C++ nem casos protegidos.

---

### [2026-06-11] Fase 10.29A — sensibilidade refinada BUZ-67D — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Documento criado:**

```text
docs/36_phase10_29a_buz67d_refined_sensitivity.md
```

**Ferramenta criada:**

```text
tools/compare_phase10_29a_refined_sensitivity.py
```

**Resultado:**

```text
REFINED_SENSITIVITY_COMPLETED
REFINED_SENSITIVITY_BEST_DIAGNOSTIC_FACTOR_FOUND
REFINED_SENSITIVITY_OPENING_DOMINATED_BY_COMPLIANCE
```

Melhor fator por abertura e score combinado: `0.75x`. Melhor fator por pressão
máxima isolada: `0.60x`. O resultado permanece sensibilidade diagnóstica, não
calibração automática.

---

### [2026-06-11] Fase 10.28C — matriz de sensibilidade modern-refined — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Documento criado:**

```text
docs/35_phase10_28c_modern_refined_diagnostic.md
```

**Ferramenta criada:**

```text
tools/compare_phase10_28c_modern_refined_route.py
```

**Casos criados:**

```text
cases/validation/sensitivity/buz67d_modern_refined_sens_baseline.yaml
cases/validation/sensitivity/buz67d_modern_refined_sens_cgeom_075.yaml
cases/validation/sensitivity/buz67d_modern_refined_sens_cgeom_125.yaml
cases/validation/sensitivity/buz67d_modern_refined_sens_same_step.yaml
```

**Resultado:**

```text
PHASE10_28C_SENSITIVITY_MATRIX_RUN_OK
```

O cenário `0.75x C_geom` aproximou a abertura de `510 s`; `1.25x C_geom` não
abriu na janela executada; `same_step` removeu o atraso de sink. O resultado é
diagnóstico de sensibilidade, não calibração automática e não regressão
legacy-equivalence.

---

### [2026-06-11] Fase 10.28B — gate BUZ-29D ou sensibilidade — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Documento criado:**

```text
docs/34_phase10_28b_additional_or_sensitivity_gate.md
```

**Ferramenta criada:**

```text
tools/plan_phase10_28b_additional_or_sensitivity.py
```

**Decisão:**

```text
ADDITIONAL_WELL_BLOCKED_SENSITIVITY_SELECTED
SENSITIVITY_MATRIX_READY_FOR_10_28C
```

BUZ-29D foi localizado no legado, mas não ficou pronto como caso PKN moderno
sem auditoria adicional. A Fase 10.28C deve executar a matriz BUZ-67D
`modern-refined` S0-S3, sem classificar divergência temporal como erro físico
ou regressão legacy-equivalence.

---

### [2026-06-11] Fase 10.28A — pacote modern-refined para casos adicionais — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Documento criado:**

```text
docs/33_phase10_28a_modern_refined_validation_package.md
```

**Ferramenta criada:**

```text
tools/plan_phase10_28a_modern_refined_validation.py
```

**Status:**

```text
PHASE=10.28A
MODE=MODERN_REFINED_VALIDATION_PACKAGE
LEGACY_EQUIVALENCE=SEPARATE_TRACK
BASE_CASE=BUZ67D_MODERN_REFINED
NEXT_GATE=ADDITIONAL_WELLS_OR_SENSITIVITY_MATRIX
PROTECTED_SCOPE_UNCHANGED=true
```

**Interpretação:** a próxima validação `modern-refined` deve usar casos/poços
adicionais somente se houver dados completos. Se não houver, a rota correta é
uma matriz formal de sensibilidade BUZ-67D, sem misturar exigências de
`legacy-equivalence`.

---

### [2026-06-11] Fase 10.27C — roadmap pós-10.27 — Codex

**Status:** Publicado em `5888401`.

**Documento criado:**

```text
docs/32_post_10_27_roadmap.md
```

**Ferramenta criada:**

```text
tools/plan_phase10_27c_next_steps.py
```

**Status:**

```text
POST_10_27_ROADMAP_RECORDED
NEXT_PHASE_MODERN_REFINED_VALIDATION_OR_SENSITIVITY
```

**Próxima fase recomendada:** `10.28A — modern-refined validation package for
additional wells/cases`, seguida por sensibilidade `10.28B` e gráficos
`10.28C`, antes de qualquer solver APBSalt1D equivalente ou integração runtime
de sal.

---

### [2026-06-11] Fase 10.27B — pacote BUZ-67D modern-refined — Codex

**Status:** Publicado em `096b245`.

**Documento criado:**

```text
docs/31_buz67d_modern_refined_validation.md
```

**Ferramenta criada:**

```text
tools/summarize_phase10_27b_modern_refined.py
```

**Status:**

```text
BUZ67D_MODERN_REFINED_VALIDATION_DOCUMENTED
MODERN_REFINED_NOT_LEGACY_EQUIVALENT
PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY
APBSALT1D_SAMPLING_BRIDGE_BLOCKED
```

**Interpretação:** BUZ-67D fica consolidado como pacote diagnóstico
`modern-refined`. A escala de pressão e o `sink_delay_s = 30 s` sustentam a rota
diagnóstica, mas abertura em `660 s` permanece diferença documentada, não erro
automático nem regressão estrita contra o `LOT_Tese`.

---

### [2026-06-11] Fase 10.27A — matriz legacy-equivalence vs modern-refined — Codex

**Status:** Publicado em `bbf1e7d`.

**Ferramenta criada:**

```text
tools/decide_phase10_27a_legacy_vs_modern_mode.py
```

**Documento principal criado:**

```text
docs/30_legacy_equivalence_vs_modern_refined.md
```

**Decisão padrão:**

```text
NEXT_PHASE_MODERN_REFINED_DOCUMENTATION_AND_VALIDATION
```

**Gate registrado:**

```text
LEGACY_EQUIVALENCE_VS_MODERN_REFINED_DECISION_RECORDED
```

**Classificações:**

```text
LEGACY_EQUIVALENCE_MODE_REQUIRED_FOR_REGRESSION
MODERN_REFINED_MODE_ACCEPTABLE_FOR_ANALYSIS
MODERN_REFINED_MODE_NOT_LEGACY_EQUIVALENT
PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY
APBSALT1D_SAMPLING_BRIDGE_BLOCKED
APBSALT1D_SOLVER_EQUIVALENCE_REQUIRED_FOR_STRICT_MATCH
CONSTANT_GEOMETRIC_REMAINS_DIAGNOSTIC_BASELINE
SIGMATHETA_RUNTIME_STILL_FUTURE_WORK
```

**Interpretação:** equivalência com o legado passa a ser um modo de regressão,
não sinônimo de validação física. A abertura moderna em `660 s` não deve ser
tratada automaticamente como erro fora do modo `legacy-equivalence`; para
exigir `510 s`, a geometria APBSalt1D precisa ser consumida de forma real.

---

### [2026-06-11] Fase 10.26D — APBSalt1D sampling bridge para `sigmaTheta` — Codex

**Status:** Publicado em `3d0dc61`.

**Gate:**

```text
APBSALT1D_SAMPLING_BRIDGE_BLOCKED_NO_SPATIAL_SAMPLES
```

**Classificação:**

```text
APBSALT1D_SAMPLING_BRIDGE_METADATA_ONLY
```

**Caso criado:**

```text
cases/validation/buz67d_pkn_legacy_apbsalt1d_sampling_bridge.yaml
```

**Ferramenta criada:**

```text
tools/compare_phase10_26d_apbsalt1d_sampling_bridge.py
```

**Interpretação:** a metadata APBSalt1D continua declarada, validada e
rastreável, mas o caminho numérico atual é `sigma_theta_time_series`. Essa rota
não possui amostras espaciais, raio, índice de elemento ou ponto de Gauss que
permita remapear `legacy_elem0_sig_2_0`. Assim, a fase não altera
`sigmaTheta`, não muda a abertura BUZ-67D e não libera correção de
`pressure_source`/timing.

**Próxima recomendação:**

```text
NEXT_PHASE_IMPLEMENT_WALL_STRESS_SAMPLING_PROVIDER
```

---

### [2026-06-11] Fase 10.26C — decisão de consumo APBSalt1D para `sigmaTheta` — Codex

**Status:** Publicado em `98fc0ba`.

**Ferramenta criada:**

```text
tools/decide_phase10_26c_apbsalt1d_consumption.py
```

**Decisão:**

```text
apbsalt1d_consumption_status = APBSALT1D_METADATA_ONLY_CONFIRMED
next_phase_recommendation = NEXT_PHASE_IMPLEMENT_SAMPLING_BRIDGE
pressure_source_timing_gate = BLOCKED_UNTIL_APBSALT1D_GEOMETRY_IS_CONSUMED_OR_REJECTED
```

**Capacidades existentes:** malha radial L3 (`build_mesh_L3`), `outer_radius_m`,
`radial_elements`, `integration_order = 3` via `AxisymL3`,
`SaltWallStressDiagnostics` e contrato `SigmaThetaProvider`.

**Capacidades ausentes:** `mesh_ratio_configurable`, amostragem
`legacy_elem0_sig_2_0`, provider runtime de `SaltWallStressDiagnostics` para LOT
e ponte sem dependencia circular entre `lot/`, `coupling/` e `salt/`.

**Interpretação:** a metadata APBSalt1D da 10.26B continua nao consumida. Nao ha
base para corrigir `pressure_source`/timing antes de implementar uma ponte de
amostragem ou documentar formalmente a nao equivalencia da malha moderna.

---

### [2026-06-11] Fase 10.26B — modo APBSalt1D legado-equivalente para `sigmaTheta` — Codex

**Status:** Implementado localmente; testes passaram; commit/push pendentes.

**Gate:** `APBSALT1D_EQUIVALENCE_MODE_IMPLEMENTATION_ALLOWED`, mas sem provider
runtime real de tensão de parede nesta fase.

**Configuração declarada:**

```text
mode = apbsalt1d_legacy_equivalent
outer_radius_m = 8.0
radial_elements = 15
ratio = 10.0
integration_order = 3
sampling = legacy_elem0_sig_2_0
consumption_status = APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED
```

**Caso criado:**

```text
cases/validation/buz67d_pkn_legacy_apbsalt1d_equiv_sigma_theta.yaml
```

**Ferramenta criada:**

```text
tools/compare_phase10_26b_apbsalt1d_equivalence.py
```

**Classificação esperada enquanto metadata-only:**

```text
APBSALT1D_EQUIVALENCE_METADATA_ONLY
```

**Resultado BUZ-67D observado:**

```text
legacy_opening_time_s = 510.0
modern_opening_time_s = 660.0
opening_time_error_s = 150.0
legacy_sink_delay_s = 30.0
modern_sink_delay_s = 30.0
relative_error_max_pressure = -0.02468924338685035
sigmaTheta_source_status = APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED
apbsalt1d_geometry_status = APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED
```

**Interpretação:** o bloco `sigma_theta_runtime_geometry` agora é parseado,
validado e rastreável em `CaseData`, mas ainda não é consumido por
`SaltWallStressDiagnostics`, `SaltCreepTimeBridge` ou outro provider runtime. A
série refinada `sigmaTheta(t)` continua sendo a fonte numérica do diagnóstico.
Logo, qualquer deslocamento remanescente de abertura não deve ser reclassificado
como erro de `pressure_source`/timing até que a geometria APBSalt1D seja
consumida ou formalmente descartada.

---

### [2026-06-11] Fase 10.26A — auditoria `pressure_source`/timing do critério `sigmaTheta` — Codex

**Status:** Implementada e publicada em `009b722`; adendo geometrico em andamento.

**Ferramenta criada:**

```text
tools/analyze_phase10_26a_pressure_source_timing.py
```

**Inputs auditados:**

```text
results/comparison/phase10_22c/legacy_unified_balance_opening_trace.csv
results/comparison/phase10_25b/modern_sigma_theta_refined_timeseries/timeseries.csv
```

**Classificação original antes do adendo geométrico:**

```text
cause = MISSING_PRESSURE_TRACE_FIELDS
gate = MODERN_TRACE_EXPORT_REQUIRED
```

**Classificação final com adendo geométrico:**

```text
cause = SIGMATHETA_MESH_OR_DOMAIN_MISMATCH
gate = LEGACY_EQUIVALENCE_REQUIRES_MESH_MATCHING

pressure_source_timing_cause_before_geometry_gate = MISSING_PRESSURE_TRACE_FIELDS
pressure_source_timing_gate_before_geometry_gate = MODERN_TRACE_EXPORT_REQUIRED
```

**Melhor candidato derivado:**

```text
pressure_source = wellbore_pressure_after_Pa
pressure_status = derived_current_wellbore_pressure_Pa
sigmaTheta_timing = sigmaTheta(time_i + dt)
record_timing = record_opening_at_step_start
predicted_opening_time_s = 600.0
opening_time_error_s = 90.0
classification = OPENING_TOO_LATE
```

**Campos ausentes no CSV moderno:** `wellbore_pressure_before_Pa`,
`wellbore_pressure_trial_Pa`, `wellbore_pressure_after_Pa`,
`delta_pressure_Pa`, `sigma_theta_compression_positive_Pa` por passo,
`sigma_theta_margin_Pa` por passo e `fracture_initiation_time_s` por linha.

**Conclusão corrigida:** nenhuma combinação derivada dos campos atuais reproduz a
abertura legada em `510 s`, mas a decisão de corrigir `pressure_source`/timing
fica bloqueada. O `APBSalt1D` legado usa `outer_radius_m = 8 m`, `nelem = 15`,
`ratio = 10`, `integration_order = 3` e amostra
`mdl->getElem(0)->getSigmaTheta()`, enquanto o caminho moderno diagnostico ainda
nao reproduz explicitamente esse dominio/malha/ponto. A próxima fase deve primeiro
rodar uma equivalencia de malha APBSalt1D no moderno; so depois retomar
`pressure_source`/timing.

---

### [2026-06-11] Fase 10.26A — adendo geometrico APBSalt1D — Codex

**Status:** Implementado localmente; commit/push pendente.

**Motivo:** antes de classificar o deslocamento de abertura moderno (`660 s`) como
erro de `pressure_source` ou timing, foi exigida auditoria do dominio radial,
malha e ponto de amostragem do `sigmaTheta` legado.

**Evidência legado:**

```text
legance/LOT_Tese/include/apb/apb_salt_1d.h
outer_diam_m = 16 m
outer_radius_m = 8 m
nelem = 15
ratio = 10
integration_order = 3

legance/LOT_Tese/src/apb/apb_salt_1d.cpp
inner_radius_m = (diam_in / 2) * 0.0254
sigmaTheta = mdl->getElem(0)->getSigmaTheta()
```

**Evidência moderno:**

```text
LotSaltBridgeConfigOptions default outer_radius_m = 1.556
LotSaltBridgeConfigOptions default radial_elements = 40
SaltCreepTimeBridgeConfig default outer_radius_m = 1.556
SaltCreepTimeBridgeConfig default radial_elements = 40
StressSampler::sample_wall_gauss_points seleciona menor r_m
```

**Classificações adicionadas:**

```text
SIGMATHETA_MESH_OR_DOMAIN_MISMATCH
SIGMATHETA_SAMPLING_POINT_MISMATCH
MODERN_MESH_NOT_LEGACY_EQUIVALENT
MODERN_REFINED_MESH_POTENTIALLY_MORE_REALISTIC
LEGACY_EQUIVALENCE_REQUIRES_MESH_MATCHING
TIMING_ANALYSIS_INCONCLUSIVE
```

**Gate atualizado:**

```text
LEGACY_EQUIVALENCE_REQUIRES_MESH_MATCHING
```

**Próxima fase recomendada:** 10.26B deve reproduzir opt-in a configuração
APBSalt1D legado no moderno (`outer_radius_m = 8 m`, `radial_elements = 15`,
`ratio = 10`, `integration_order = 3`, mesmo ponto de amostragem de
`sigmaTheta`) antes de qualquer correção de `pressure_source`/timing.

---

### [2026-06-11] Fase 10.25C — decisão da fonte `sigmaTheta` — Codex

**Status:** Implementada localmente; commit/push pendente.

**Ferramenta criada:**

```text
tools/decide_phase10_25c_sigma_theta_source.py
```

**Inputs comparados:**

```text
results/comparison/phase10_24c/phase10_24c_summary.csv
results/comparison/phase10_25b/phase10_25b_summary.csv
```

**Decisão:**

```text
NEXT_MODEL_PRESSURE_SOURCE_TIMING_REVIEW
```

**Racional:** 10.24C e 10.25B mantêm `opening_time_error_s = 150.0` com
pressão máxima, pressão na abertura, pressão final e sink delay em faixa
diagnóstica boa. A série refinada não corrigiu a abertura deslocada, então a
próxima auditoria deve focar `pressure_source`/timing (`before`, `trial`,
`after`) e o instante de amostragem do provider, antes de conectar
`SaltWallStressDiagnostics` como fonte runtime.

**Escopo:** decisão documental/diagnóstica; nenhum `results/` versionado; nenhum
default runtime alterado.

---

### [2026-06-11] Fase 10.25B — diagnóstico BUZ67D com série `sigmaTheta` refinada — Codex

**Status:** Implementada localmente; commit/push pendente.

**Caso criado:**

```text
cases/validation/buz67d_pkn_legacy_sigma_theta_refined_timeseries.yaml
```

**Ferramenta criada:**

```text
tools/compare_phase10_25b.py
```

**Classificação observada:**

```text
SIGMA_THETA_REFINED_TIMESERIES_PRESSURE_OK_OPENING_SHIFTED
```

**Métricas principais:**

```text
legacy_first_opened_time_s = 510.0
modern_fracture_initiation_time_s = 660.0
opening_time_error_s = 150.0

legacy_sink_delay_s = 30.0
modern_sink_delay_s = 30.0
sink_delay_error_s = 0.0

relative_error_max_pressure = -0.02468924338685035
pressure_at_opening_relative_error = 0.008415423398363079
final_pressure_relative_error = -0.009582917751452825
```

**Conclusão:** a série refinada de 44 pontos melhora a rastreabilidade da fonte
`sigmaTheta`, mas não corrige a abertura moderna deslocada. A escala de pressão
e o sink delay permanecem bons. A Fase 10.25C deve decidir se a próxima revisão
deve focar em `pressure_source`/timing, mapeamento de ponto/camada/tempo ou
fonte runtime real de `SaltWallStressDiagnostics`.

**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/`,
`tests/baselines/`, `postprocess/` ou `results/` deve ser versionado.

---

### [2026-06-11] Fase 10.25A — extração refinada da série `sigmaTheta` do LOT_Tese — Codex

**Status:** Implementada localmente; commit/push pendente.

**Gate:** `SIGMA_THETA_REFINED_PROVIDER_UPDATE_ALLOWED`.

**Classificações:**

```text
SIGMA_THETA_REFINED_SERIES_COMPLETE
SIGMA_THETA_YAML_SERIES_TOO_SPARSE
SIGMA_THETA_SOURCE_MISMATCH_EXPLAINS_OPENING_SHIFT
```

**Objetivo:** instrumentar temporariamente o `LOT_Tese` no ponto exato do
critério legado `pw > sigmaTheta` para extrair uma série refinada
`sigma_theta_compression_positive_Pa(t)` por passo temporal, sem commitar
alterações em `legance/`.

**Ferramenta criada:**

```text
tools/analyze_phase10_25a_sigma_theta_refined.py
```

**Trace auditado gerado fora do Git:**

```text
results/comparison/phase10_25a/legacy_sigma_theta_refined_trace.csv
results/comparison/phase10_25a/sigma_theta_refined_series.csv
results/comparison/phase10_25a/sigma_theta_refined_summary.json
results/comparison/phase10_25a/legacy_sigma_theta_refined_audit.patch
```

**Resultados principais:**

```text
number_of_sigmaTheta_points = 44
primary_idAnnular = 1
primary_idLayer = 7
time_range = 30.0 .. 1320.0 s
legacy_first_opened_time_s = 510.0
legacy_first_opened_step = 721
legacy_first_pw_Pa = 66769500.0
legacy_first_sigmaTheta_Pa = 66666600.0
legacy_first_margin_Pa = 102865.0
legacy_first_sink_positive_time_s = 540.0
sink_delay_s = 30.0
sigmaTheta_at_510s = 66666600.0
sigmaTheta_at_660s = 65445500.0
n_points_yaml = 3
time_range_yaml = 480.0 .. 540.0 s
sigmaTheta_at_660s_yaml = 66666600.0
max_abs_difference_between_yaml_and_refined = 7079400.0
mean_abs_difference_between_yaml_and_refined = 1831338.6363636365
```

**Interpretação:** a série 10.24B era uma fixture mínima de três pontos e não
representava a queda temporal refinada de `sigmaTheta` observada no caminho
legado. A diferença é suficiente para explicar, em nível diagnóstico, o
deslocamento da abertura moderna para `660 s`. A próxima fase permitida é criar
um novo caso diagnóstico com a série refinada, sem substituir o caso 10.24B.

**Escopo:** `legance/LOT_Tese/` foi modificado apenas temporariamente para
instrumentação, o patch foi salvo em `results/`, e os arquivos legados foram
restaurados antes de qualquer commit. Nenhum arquivo em `results/` deve ser
versionado.

---

### [2026-06-11] Fase 10.24C — diagnóstico final `sigma_theta_time_series` BUZ67D — Codex

**Status:** Concluída, commitada e enviada em `6dd7f6d`.

**Classificação final:** `SIGMA_THETA_TIMESERIES_PRESSURE_OK_OPENING_SHIFTED`.

**Próxima recomendação:** `NEXT_MODEL_SIGMA_THETA_TIMESERIES_NEEDS_BETTER_SOURCE`.

**Objetivo:** diagnosticar o caso BUZ67D com `constant_geometric`,
`sigma_theta_time_series`, `sink_timing: next_step`, pressão inicial, schedule
injeção+shut-in e drill pipe, sem alterar o runtime padrão.

**Ferramenta criada:**

```text
tools/compare_phase10_24c.py
```

**Resultado:**

```text
max_pressure_legacy_Pa = 69035836.1743195
max_pressure_modern_Pa = 67331393.612597
relative_error_max_pressure = -0.02468924338685035

legacy_first_opened_time_s = 510.0
modern_fracture_initiation_time_s = 660.0
opening_time_error_s = 150.0

legacy_sink_delay_s = 30.0
modern_sink_delay_s = 30.0
sink_delay_error_s = 0.0

legacy_pressure_at_opening_Pa = 66769500.0
modern_pressure_at_opening_Pa = 67331393.612597
pressure_at_opening_relative_error = 0.008415423398363079

final_pressure_relative_error = -0.009582917751452825
```

**Conclusão:** a escala de pressão, a pressão no ponto moderno de abertura, o
sink delay e o final de shut-in estão coerentes em nível diagnóstico, mas a
abertura permanece deslocada. A série temporal mínima da 10.24B não é fonte
física suficiente para promover runtime de sal; a próxima fase deve melhorar a
fonte `sigmaTheta` temporal ou auditar o cruzamento de pressão trial.

---

### [2026-06-11] Fase 10.24B — sigma_theta_time_series diagnóstico — Codex

**Status:** Concluída, commitada e enviada em `6fa005b`.

**Classificação:** `SIGMA_THETA_TIMESERIES_DIAGNOSTIC_ONLY`.

**Objetivo:** expor uma fonte temporal opt-in de
`sigma_theta_compression_positive_Pa` para o `volumetric_balance`, usando o
contrato `SigmaThetaProvider` da Fase 10.24A, sem conectar `saltcreep`,
`SaltCreepTimeBridge`, `SaltWallStressDiagnostics` ou alterar o default runtime.

**Implementação:** adicionado `SigmaThetaTimeSeriesProvider` em `lot/`, com
interpolação linear e clamp fora do intervalo. O schema e o parser aceitam:

```text
lot.fracture.initiation.type = sigma_theta_time_series
pressure_source = wellbore_pressure_trial_Pa
comparison = legacy_algebra
sigma_theta_series.interpolation = linear
sigma_theta_series.out_of_range = clamp
```

**Caso controlado criado:**

```text
cases/validation/buz67d_pkn_legacy_sigma_theta_timeseries.yaml
```

O caso usa uma série mínima derivada da trace unificada 10.22C (`480 s`,
`510 s`, `540 s`; `sigmaTheta = 66666600 Pa`) para validar o wiring
`YAML -> CaseParser -> CaseData -> PknRunner -> SigmaThetaProvider -> PknModel`.

**Ferramenta criada:**

```text
tools/compare_phase10_24b.py
```

**Resultado diagnóstico local:**

```text
classification = SIGMA_THETA_TIMESERIES_PRESSURE_OK_OPENING_SHIFTED
max_pressure_legacy_Pa = 69035836.1743195
max_pressure_modern_Pa = 67331393.612597
relative_error_max_pressure = -0.02468924338685035
modern_fracture_initiation_time_s = 660.0
modern_first_sink_positive_time_s = 690.0
modern_sink_delay_s = 30.0
```

**Preservações:** `pkn_direct` continua ignorando provider runtime; casos
protegidos não foram alterados; a rota não é default; não há validação física de
fratura.

---

### [2026-06-11] Fase 10.24A — contrato SigmaThetaProvider runtime — Codex

**Status:** Concluída, commitada e enviada em `b81ea57`.

**Gate:** `SIGMA_THETA_PROVIDER_CONTRACT_IMPLEMENTATION_ALLOWED`.

**Objetivo:** criar um contrato neutro e opt-in para que o runtime LOT/PKN possa
consultar `sigma_theta_compression_positive_Pa` sem depender de
`external/saltcreep/`, `SaltCreepTimeBridge`, `SaltWallStressDiagnostics` ou
`coupling/`.

**Implementacao:** foi criado `include/lot/SigmaThetaProvider.hpp` com
`SigmaThetaRuntimePoint` e a interface `SigmaThetaProvider`. O `PknInput` agora
aceita `FractureInitiationCriterion::SigmaThetaProviderRuntime` e um
`std::shared_ptr<const SigmaThetaProvider> sigma_theta_provider`. O `PknModel`
usa essa rota apenas no
`volumetric_balance` quando explicitamente configurada, avaliando:

```text
margin_Pa = wellbore_pressure_trial_Pa - sigma_theta_compression_positive_Pa
opened = margin_Pa > 0
```

**Diagnosticos exportados:** `sigma_theta_provider_type`,
`sigma_theta_source`, `sigma_theta_lookup_time_s`, `sigma_theta_layer_id` e
`sigma_theta_mapping_status`.

**Preservacoes:** sem provider, `constant_pressure` e `sigma_theta_static`
permanecem como antes; `pkn_direct` ignora a rota runtime; nenhum YAML, parser
ou caso default foi alterado. Nao ha provider real de saltcreep nesta fase.

---

### [2026-06-10] Fase 10.23A — sink timing next_step opt-in — Codex

**Status:** Implementada localmente; commit/push pendente.

**Objetivo:** adicionar a rota opt-in `lot.fracture.balance.sink_timing:
next_step` ao `volumetric_balance`, preservando o default `same_step` e sem
alterar `pkn_direct`.

**Implementacao:** `PknInput` agora possui `FractureSinkTiming`; o parser aceita
`same_step` e `next_step`; o schema documenta o novo campo; o `PknModel` posterga
apenas o sink de fratura/leakoff no passo em que a fratura abre quando a opcao
`next_step` e usada. O volume acumulado antes da abertura nao e aplicado de uma
vez, pois os acumuladores historicos continuam avancando a cada passo.

**Novos diagnosticos exportados:** `sink_timing`, `sink_deferred_this_step`,
`sink_active_this_step`, `fracture_initiated_before_step`,
`fracture_initiated_after_step`, `fracture_started_this_step`,
`fracture_sink_applied_m3` e `leakoff_sink_applied_m3`.

**Caso controlado criado:**

```text
cases/validation/buz67d_pkn_legacy_compliance_next_step_sink.yaml
```

**Ferramenta criada:**

```text
tools/compare_phase10_23a.py
```

**Resultado diagnostico:** `NEXT_STEP_SINK_EFFECTIVE`.

| Rota | Inicio abertura moderno [s] | Primeiro sink positivo [s] | Atraso [s] | Max pressure [Pa] | Erro vs legado |
|---|---:|---:|---:|---:|---:|
| legado 10.22C | `510.0` | `540.0` | `30.0` | `69035836.1743195` | n/a |
| `same_step` | `690.0` | `690.0` | `0.0` | `67331393.612597` | `-0.02468924338685035` |
| `next_step` | `690.0` | `720.0` | `30.0` | `69176810.81439006` | `0.0020420501565967626` |

**Caveat:** esta fase alinha a cronologia diagnostica do sink com a evidencia
legada da 10.22C, mas nao valida equivalencia fisica moderna nem libera
`pressure_tabulated_geometric` ou qualquer novo modelo runtime.

---

### [2026-06-10] Fase 10.23B — diagnostico BUZ-67D combinado — Codex

**Status:** Implementada localmente; commit/push pendente.

**Objetivo:** testar um caso BUZ-67D opt-in combinando `constant_geometric`
da 10.19C, `sigma_theta_static` da 10.22C e `sink_timing: next_step` da 10.23A.

**Caso criado:**

```text
cases/validation/buz67d_pkn_legacy_compliance_sigma_theta_next_step.yaml
```

**Ferramenta criada:**

```text
tools/compare_phase10_23b.py
```

**Resultado diagnostico:** `COMBINED_DIAGNOSTIC_PRESSURE_OK_OPENING_SHIFTED`.

| Campo | Legado | Moderno combinado |
|---|---:|---:|
| `max_pressure_Pa` | `69035836.1743195` | `67331393.612597` |
| `relative_error_max_pressure` | n/a | `-0.02468924338685035` |
| `first_opened_time_s` | `510.0` | `660.0` |
| `first_sink_positive_time_s` | `540.0` | `690.0` |
| `sink_delay_s` | `30.0` | `30.0` |
| `pressure_at_opening_Pa` | `66769500.0` | `67331393.612597` |

**Caveat:** a escala de pressao e o atraso de sink estao bons para diagnostico,
mas a abertura moderna continua deslocada. A fase nao valida fisica de fratura,
nao implementa sigma-theta runtime, nao implementa Zamora e nao libera
`pressure_tabulated_geometric`.

---

### [2026-06-10] Fase 10.23C — decisao do proximo modelo — Codex

**Status:** Implementada localmente; commit/push pendente.

**Objetivo:** consumir os summaries das Fases 10.23A e 10.23B para decidir o
proximo caminho sem implementar novo solver.

**Ferramenta criada:**

```text
tools/decide_phase10_23c_next_model.py
```

**Decisao:** `NEXT_MODEL_SIGMA_THETA_RUNTIME`.

**Justificativa:** a 10.23B manteve a pressao maxima dentro de `+-10%` e
reproduziu `sink_delay_s = 30 s`, mas a abertura moderna ainda ficou em `660 s`
contra `510 s` no legado. Portanto, o gargalo remanescente e o criterio de
abertura/sigma-theta, nao a cronologia do sink.

**Gate:** `pressure_tabulated_geometric` continua bloqueado; `constant_geometric`
permanece diagnostico; a proxima fase deve priorizar sigma-theta runtime opt-in
ou um criterio de abertura mais fiel.

---

### [2026-06-10] Fase 10.22C — trace legado unificado de balanco, abertura e sink — Codex

**Status:** Implementada localmente; commit/push pendente.

**Objetivo:** instrumentar temporariamente o `LOT_Tese` para capturar, no mesmo
trace, termos do balanco, `pw`, `sigmaTheta`, `margin`, criterio `opened` e
inicio de sink (`dV_leakoff > 0`), sem versionar nenhuma alteracao em `legance/`
e sem alterar solver moderno.

**Ferramenta criada:**

```text
tools/analyze_phase10_22c_unified_legacy_trace.py
```

**Teste criado:**

```text
tests/python/test_analyze_phase10_22c_unified_legacy_trace.py
```

**Fixture criada:**

```text
tests/fixtures/comparison/phase10_22c_unified_trace_fixture.csv
```

**Resultado diagnostico do trace real:**

| Campo | Valor |
|-------|-------|
| `trace_classification` | `UNIFIED_TRACE_COMPLETE` |
| `opening_classification` | `OPENING_CRITERION_CONFIRMED` |
| `sink_classification` | `SINK_TIMING_CONFIRMED` |
| `phase_dependence_classification` | `PHASE_DEPENDENCE_EXPLAINED_BY_SINK` |
| `first_opened_time_s` | `510.0` |
| `first_sink_positive_time_s` | `540.0` |
| `sink_delay_s` | `30.0` |
| `first_pw_Pa` | `66769500.0` |
| `first_sigmaTheta_Pa` | `66666600.0` |
| `first_margin_Pa` | `102865.0` |
| `row_counts` | `56146 total`, `48744 balance`, `7402 opening` |

**Gate:** `LEGACY_OPENING_AND_SINK_TRACE_READY_FOR_REVIEW`.

**Caveat:** esta fase confirma a cronologia interna do legado, mas nao valida
equivalencia fisica moderna nem libera `pressure_tabulated_geometric` para
runtime.

---

### [2026-06-10] Fase 10.22B — compliance geometrica direta termo-a-termo — Codex

**Status:** Implementada localmente; commit/push pendente.

**Objetivo:** consumir o trace termo-a-termo da 10.22A e extrair
`C_geom_accumulated` e `C_geom_incremental` diretamente de `dV`, `Vi` e `dP`,
sem alterar solver moderno, sem implementar `pressure_tabulated_geometric` e
sem mexer em `legance/`.

**Ferramenta criada:**

```text
tools/extract_phase10_22b_termwise_geometric_compliance.py
```

**Teste criado:**

```text
tests/python/test_extract_phase10_22b_termwise_geometric_compliance.py
```

**Fixture criado:**

```text
tests/fixtures/comparison/phase10_22b_termwise_geometric_fixture.csv
```

**Formulas:**

```text
C_geom_accumulated = dV_total_m3_rad / (Vi_m3_rad*dP_Pa)
C_geom_incremental = dV_increment_m3_rad / (Vi_m3_rad*dP_increment_Pa)
```

**Regime source:**

```text
known_from_previous_phase_not_from_this_trace
```

**Resultados pre-abertura:**

| Serie | mean [1/Pa] | median [1/Pa] | std [1/Pa] | CV | Classificacao |
|---|---:|---:|---:|---:|---|
| acumulada | `4.442167504384874e-10` | `1.5922475242866133e-10` | `4.226787367855454e-10` | `0.9515146296674275` | `TERMWISE_GEOM_COMPLIANCE_NOISY` |
| incremental | `-3.8475791443484577e-8` | `1.508743863244543e-10` | `1.2633036771277306e-7` | `3.283372816341784` | `TERMWISE_GEOM_COMPLIANCE_NOISY` |

**Comparacoes:**

```text
C_geom_constant_10_19C = 1.8571966938610005e-8
C_geom_elastic_10_20C = 1.7242805809704984e-10
pre_opening_accumulated_ratio_to_constant_10_19C = 0.023918670106771914
pre_opening_incremental_ratio_to_constant_10_19C = -2.0717133285164167
pre_opening_accumulated_ratio_to_elastic_10_20C = 2.5762440019388455
```

**Gate:**

```text
LEGACY_OPENING_TRACE_STILL_REQUIRED
TERMWISE_GEOM_COMPLIANCE_INSUFFICIENT_FOR_MODEL
TERMWISE_GEOM_COMPLIANCE_PHASE_DEPENDENT
ELASTIC_MODEL_REQUIRES_SCALING
```

**Conclusao:** a serie direta e diagnostica, mas ruidosa e dependente de fase.
`pressure_tabulated_geometric` permanece bloqueado ate existir trace
complementar com `opened/sigmaTheta/margin` no mesmo registro.

---

### [2026-06-10] Fase 10.22A — auditoria direta do balanco legado termo-a-termo — Codex

**Status:** Implementada localmente; commit/push pendente.

**Objetivo:** instrumentar temporariamente o `LOT_Tese` para exportar os termos
ativos do balanco de pressao PKN, executar o caso BUZ67D legado, restaurar
`legance/LOT_Tese/` e analisar a reconstrução de `dP` sem alterar runtime
moderno.

**Formula confirmada em `APB1da::calculateLOTFracturedSaltRock(...)`:**

```text
dP = alpha*dT/k + (Vq - dV + dMl/(rho_f2*FC))/(Vi*k)
```

**Ferramenta criada:**

```text
tools/analyze_phase10_22a_legacy_balance_terms.py
```

**Teste criado:**

```text
tests/python/test_analyze_phase10_22a_legacy_balance_terms.py
```

**Fixture criado:**

```text
tests/fixtures/comparison/phase10_22a_balance_terms_fixture.csv
```

**Resultados do trace legado real:**

| Métrica | Valor |
|---|---:|
| `max_abs_residual_Pa` | `1.862645149230957e-9` |
| `mean_abs_residual_Pa` | `4.215656166620175e-10` |
| primeiro sink volumetrico positivo | `540 s` |
| `mean_thermal_fraction` pre-abertura | `0.7237524643800288` |
| `mean_volumetric_fraction` pre-abertura | `0.27624753561997123` |
| `mean_C_eff_termwise_1_Pa` pre-abertura | `-2.2595356091978464e-7` |
| `median_C_eff_termwise_1_Pa` pre-abertura | `5.934858409233096e-10` |
| `std_C_eff_termwise_1_Pa` pre-abertura | `7.648603719350452e-7` |
| `cv_C_eff_termwise` pre-abertura | `3.3850334945886376` |

**Classificações:**

```text
LEGACY_BALANCE_TRACE_PARTIAL
LEGACY_BALANCE_TRACE_SIGN_CONFIRMED
LEGACY_BALANCE_RECONSTRUCTION_MATCHES_DP
```

**Campos ainda ausentes no mesmo trace:**

```text
T_final_C
sigmaTheta_Pa
margin_Pa
opened
opened_before_step
opened_after_step
```

**Conclusão:** a Fase 10.22A confirma a algebra termo-a-termo do balanco legado
e fecha a ambiguidade de sinal da reconstrução de `dP`, mas ainda nao abre
validacao fisica Level 1 nem libera `pressure_tabulated_geometric` como rota
runtime. A proxima fase pode tentar uma rota diagnostica com compliance
termo-a-termo ou reinstrumentar `opened/sigmaTheta` no mesmo trace, mantendo
tudo opt-in.

---

### [2026-06-10] Fase 10.21C — compliance aparente corrigida por perfil termico — Codex

**Status:** Implementada localmente; commit/push pendente.

**Objetivo:** extrair uma serie diagnostica de compliance aparente corrigida
pelo termo termico `alpha*dT/k`, sem alterar runtime C++, sem modificar
`legance/LOT_Tese/` e sem implementar `pressure_tabulated_geometric`.

**Ferramenta criada:**

```text
tools/extract_phase10_21c_thermal_corrected_compliance.py
```

**Teste criado:**

```text
tests/python/test_extract_phase10_21c_thermal_corrected_compliance.py
```

**Fonte usada:**

```text
legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp
results/comparison/level1_buz67d/legacy_audit/buz67d_audit_timeseries.csv
```

**Perfil termico reconstruido por interpolacao linear em `profTeste = 4374 m`:**

```text
T_initial_degC = 89.17547550432276
T_final_degC = 92.31236311239194
DTmax_degC = 3.1368876080691734
alpha = 8.0e-4 1/degC
k = 6.4e-10 1/Pa
```

**Classificacao final:**

```text
THERMAL_CORRECTED_COMPLIANCE_SIGN_AMBIGUOUS
```

**Valores pre-abertura principais:**

```text
raw mean C_eff = 8.737997966365286e-8 1/Pa
thermal-subtract mean C_eff = 1.1972273085205066e-7 1/Pa
thermal-subtract median C_eff = 1.0434903008590042e-7 1/Pa
thermal-subtract std C_eff = 4.400544383923113e-8 1/Pa
thermal-subtract CV C_eff = 0.36756131042159057
thermal-subtract mean C_geom = 1.1908273085205067e-7 1/Pa
thermal-subtract median C_geom = 1.0370903008590043e-7 1/Pa
thermal-subtract std C_geom = 4.4005443839231133e-8 1/Pa
thermal-subtract CV C_geom = 0.36953673739565013
subtract_vs_pressure correlation = -0.5906712267376746
subtract_vs_time correlation = -0.5671142417359523
ratio to C_geom constant 10.19C = 6.411961169523989
negative mechanical pressure points = 4
non-positive mechanical pressure increments = 1
```

**Gate:**

```text
THERMAL_CORRECTION_EXTRACTED_DIAGNOSTIC_ONLY
PRESSURE_TABULATED_STILL_BLOCKED_MISSING_BALANCE_TERMS
PRESSURE_TABULATED_STILL_BLOCKED_SIGN_CONVENTION_AMBIGUOUS
```

**Decisao:** nao implementar `pressure_tabulated_geometric`. A serie corrigida
e util para auditoria, mas ainda depende da resolucao da convencao de sinal e
da exportacao conjunta de `dV_geom`, `dMl`, `dV_leakoff`, `k`, `dT` e `opened`.

---

### [2026-06-10] Fase 10.20A — auditoria e formulacao de compliance mecanica anular/wellbore — Codex

**Status:** Commitada e enviada para `origin/main` em `c33801e`.

**Gate:** `MECHANICAL_COMPLIANCE_FORMULATION_PARTIAL`.

**Objetivo:** auditar como o legado calcula `dV` geometrico e formular uma
rota mecanica simples, opt-in e testavel para substituir gradualmente o proxy
constante da Fase 10.19C.

**Achado legado:**

```text
dV = 0.5 * thickness * ((b + u_outer)^2 - (a + u_inner)^2) - Vi
dP = (alpha*dT - (-Vq + dV - dMl/(rho*FC))) / Vi / k
```

`u_inner` e `u_outer` vêm de `APB1da::getNodalDisplacement()`, que resolve o
equilibrio radial do tier e, quando a rocha externa e sal viscoelastico, usa
`APBSalt1D::solveThermalViscoStep(dt)` na fronteira externa.

**Ferramenta criada:**

```text
tools/audit_phase10_20a_mechanical_compliance.py
```

**Resultado BUZ67D da estimativa simples:**

```text
C_geom_diag_10_19C = 1.8571966938610005e-8 1/Pa
C_geom_elastic_simple = 1.7242805809704984e-10 1/Pa
ratio_to_diagnostic = 0.009284318600556103
predicted_first_dP_elastic_simple = 43639672.35675541 Pa
```

**Decisao:** prosseguir para 10.20B com `elastic_annular_simple`, mas apenas
como rota experimental/opt-in. A expectativa e que o diagnostico 10.20C mostre
se o modelo simples e subcompliant para BUZ67D.

**Testes executados:**

```text
cmake -S . -B build: passou
cmake --build build --config Debug -j: passou
ctest --test-dir build -C Debug --output-on-failure: 237/237 passaram
python -m pytest tests/python/: 84/84 passaram
python tools/audit_phase10_20a_mechanical_compliance.py --help: passou
python tools/generate_docs_index.py: passou
git diff --check: passou
```

**Caveat:** nenhuma equacao legado foi alterada; `legance/LOT_Tese/` foi
somente lido. O gate Level 1 permanece fechado para validacao fisica.

---

### [2026-06-10] Fase 10.20B — modelo `elastic_annular_simple` opt-in — Codex

**Status:** Commitada e enviada para `origin/main` em `b87e008`.

**Objetivo:** implementar o modelo mecanico reduzido escolhido na 10.20A como
rota opt-in no `volumetric_balance`, preservando `constant_geometric`,
`pkn_direct` e casos sem compliance.

**Formula implementada:**

```text
c_inner = r_inner^2 / (E_inner * t_inner)
c_outer = (1 + nu_outer) * r_outer / E_outer
C_geom = 2 * (r_outer*c_outer + r_inner*c_inner) / (r_outer^2 - r_inner^2)
C_eff = C_fluid + C_geom
dP = dV_eff / (C_eff * V_annular)
```

**Campos adicionados ao contrato:**

```text
lot.volumetric_balance.compliance.model = elastic_annular_simple
inner_boundary.radius
inner_boundary.wall_thickness
inner_boundary.young_modulus
inner_boundary.poisson_ratio
formation.radius
formation.young_modulus
formation.poisson_ratio
mechanical_compliance_status
```

**Caveat:** o modelo e experimental/opt-in e nao representa APB/sal acoplado,
Zamora, fluencia temporal ou sistema de rigidez completo do legado.

**Testes executados:** `ctest` 242/242, `pytest` 84/84, validacoes LOT/PKN
controladas e runs de regressao `lot-pkn`.

---

### [2026-06-10] Fase 10.20C — diagnostico BUZ67D com `elastic_annular_simple` — Codex

**Status:** Commitada e enviada para `origin/main` em `aad0a9c`.

**Caso criado:**

```text
cases/validation/buz67d_pkn_legacy_elastic_compliance.yaml
```

**Ferramenta criada:**

```text
tools/compare_phase10_20c.py
```

**Objetivo:** comparar, no caso BUZ67D controlado, legado auditado, moderno sem
compliance, moderno com `constant_geometric` da 10.19C e moderno com
`elastic_annular_simple` da 10.20B.

**Metricas observadas:**

```text
legacy_first_dP_Pa = 1845413.7784679066
modern_first_dP_no_compliance_Pa = 55397022.29498486
modern_first_dP_constant_compliance_Pa = 1845417.2017930523
modern_first_dP_elastic_compliance_Pa = 43639672.35675542
max_pressure_legacy_Pa = 69035836.1743195
max_pressure_elastic_compliance_Pa = 70371887.52990527
relative_error_max_pressure = 0.019353011850427385
fracture_initiation_time_legacy_s = 510.0
fracture_initiation_time_elastic_s = 30.0
C_geom_constant_10_19C = 1.8571966938610005e-8
C_geom_elastic_10_20C = 1.7242805809704984e-10
C_eff_elastic_10_20C = 8.124280580970498e-10
```

**Classificacao:** `ELASTIC_COMPLIANCE_UNDERCOMPLIANT`.

O modelo elastico simples melhora a escala frente a compressao pura de fluido,
mas ainda e muito menos complacente que o proxy `constant_geometric` inferido
do legado. Ele abre no primeiro passo (`30 s`) contra `510 s` no legado
auditado. A conclusao e diagnostica: nao promover para default, nao calibrar
silenciosamente e nao declarar validacao fisica.

---

### [2026-06-10] Fase 10.21B — auditoria termica/compressibilidade antes de tabela — Codex

**Status:** Implementada localmente; commit/push pendente.

**Objetivo:** executar o adendo obrigatorio antes de qualquer implementacao de
`pressure_tabulated_geometric`, auditando se a compliance aparente da 10.21A
absorve efeitos termicos e se a compressibilidade moderna bate com o legado.

**Fonte auditada:** leitura read-only de:

```text
legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp
legance/LOT_Tese/src/apb_code/APB1da.cpp
legance/LOT_Tese/include/apb_code/APB1da.h
results/comparison/level1_buz67d/legacy_audit/legacy_native_output.dat
```

**Formula legado ativa:**

```text
dP = (alpha*dT - (-Vq + dV - dMl/(rho*FC))) / Vi / k
```

**Resultado do caso BUZ67D PKN:**

```text
alpha_legacy = 8.0e-4 1/degC
k_legacy = 6.4e-10 1/Pa
C_fluid_modern = 6.4e-10 1/Pa
compressibility_difference_percent = 0.0
compressibility_status = COMPRESSIBILITY_CONFIRMED_MATCHING_LEGACY
```

Para o layer 16, ponto de influencia final do intervalo 4360-4374 m:

```text
T_initial = 91.16029460257798 degC
T_final = 94.53942838746772 degC
DTmax = 3.3791337848897456 degC
dT_at_8_5_min = 3.282587105 degC
thermal_pressure_equivalent_at_8_5_min = 4.10323388125e6 Pa
dP_at_8_5_min = 8.131435236e6 Pa
thermal_fraction_at_8_5_min = 0.5046137320363699
```

Estatisticas pre-abertura do layer 16:

```text
mean_thermal_fraction = 0.8670835951244072
median_thermal_fraction = 0.7838609981108711
max_abs_thermal_fraction = 1.5259151388269308
thermal_status = THERMAL_EFFECT_DOMINANT
```

**Gate resultante:**

```text
THERMAL_EFFECT_NEEDS_CORRECTION_BEFORE_TABULATION
PRESSURE_TABULATED_COMPLIANCE_BLOCKED_THERMAL_EFFECT_RELEVANT
```

**Decisao:** nao implementar `pressure_tabulated_geometric` com a serie bruta
da 10.21A. A proxima fase deve produzir uma serie corrigida por termo termico
ou reinstrumentar temporariamente o legado para exportar `dT`, `alpha`, `k`,
`dV_geom`, `dMl` e `dV_leakoff` no mesmo trace.

---

### [2026-06-10] Fase 10.21A — extracao da compliance aparente legado LOT_Tese — Codex

**Status:** Commitada e enviada para `origin/main` em `d8759cc`.

**Ferramenta criada:**

```text
tools/extract_phase10_21a_apparent_compliance.py
```

**Fonte usada:** `results/comparison/level1_buz67d/legacy_audit/buz67d_audit_timeseries.csv`.
`legance/LOT_Tese/` nao foi modificado; a extracao usa o trace auditado ja
existente e registra os campos ausentes em metadata.

**Formula legada auditada:**

```text
dP = (alpha*dT - (-Vq + dV - dMl/(rho*FC))) / Vi / k
```

**Formula reduzida usada na extracao:**

```text
C_eff_apparent = delta_Vq_m3_rad / (Vi_m3_rad * delta_dP_Pa)
C_geom_apparent = C_eff_apparent - k
```

Como o trace auditado nao exporta `dV_geom_m3_rad`, `dMl_term_m3_rad`,
`dV_leakoff_m3_rad`, `k_1_Pa` ou `opened`, a fase classifica a serie como
estimativa reduzida, nao como reconstrução completa do balanço legado.

**Resultado BUZ67D pre-abertura:**

```text
classification = APPARENT_COMPLIANCE_PRESSURE_DEPENDENT
mean_C_eff_apparent = 8.737997966365286e-8 1/Pa
median_C_eff_apparent = 9.689922710105396e-8 1/Pa
std_C_eff_apparent = 2.1166626874556158e-8 1/Pa
cv_C_eff_apparent = 0.24223657359536746
min_C_eff_apparent = 1.9211966938609834e-8 1/Pa
max_C_eff_apparent = 1.0000066303924978e-7 1/Pa
correlation_vs_pressure = 0.7678090262667732
correlation_vs_time = 0.7435993542398455
```

O primeiro passo reproduz a compliance efetiva da 10.19C, mas a media
pre-abertura e cerca de `4.67x` maior que o proxy constante da 10.19C. O modelo
`elastic_annular_simple` da 10.20C representa apenas cerca de `0.20%` dessa
media aparente. Recomendacao para 10.21B: formular rota tabulada/pressure-
dependent ou calibracao opt-in explicita, sem alterar o default.

---

### [2026-06-10] Fase 10.19C — compliance geometrica opt-in no balanco volumetrico LOT — Codex

**Status:** Commitada e enviada para `origin/main` em `d6ff741`.

**Objetivo:** adicionar ao `volumetric_balance` uma compliance geometrica
constante, opt-in e diagnostica, para testar a causa raiz identificada na
Fase 10.19B sem alterar `pkn_direct`, sem conectar APB/sal e sem tornar a rota
default.

**Caso criado:**

```text
cases/validation/buz67d_pkn_legacy_compliance.yaml
```

**Ferramenta criada:**

```text
tools/compare_phase10_19c.py
```

**Formula implementada:**

```text
C_eff = C_fluid + C_geom
dP = dV_eff / (C_eff * V_annular)
```

**Valores diagnosticos:**

```text
C_fluid = 6.4e-10 1/Pa
C_geom = 1.8571966938610005e-8 1/Pa
C_eff = 1.9211966938610006e-8 1/Pa
```

**Resultado local:**

```text
classification = COMPLIANCE_EFFECTIVE
legacy_first_dP_Pa = 1845413.7784679066
modern_first_dP_no_compliance_Pa = 55397022.29498486
modern_first_dP_with_compliance_Pa = 1845417.2017930523
max_pressure_legacy_Pa = 69035836.1743195
max_pressure_with_compliance_Pa = 67331393.612597
relative_error_max_pressure = -0.02468924338685035
fracture_initiation_time_s = 690.0
```

**Testes executados:**

```text
cmake --build build --config Debug -j: passou
ctest --test-dir build -C Debug --output-on-failure: 237/237 passaram
python -m pytest tests/python/: 81/81 passaram
python tools/compare_phase10_19c.py --help: passou
python tools/compare_phase10_19c.py ...: COMPLIANCE_EFFECTIVE
```

**Validacoes manuais:**

```text
lot_pkn_minimal.yaml: OK
lot_pkn_with_leakoff.yaml: OK
buz67d_pkn.yaml: OK
buz67d_pkn_legacy_aligned.yaml: OK
buz67d_pkn_legacy_sigma_theta_static.yaml: OK
buz67d_pkn_legacy_compliance.yaml: OK
```

**Caveat:** a rota e `GEOMETRIC_COMPLIANCE_DIAGNOSTIC_ONLY`. O valor foi
inferido do primeiro passo legado e nao representa ainda um modelo mecanico
validado de revestimento, formacao, sal ou APB.

---

### [2026-06-10] Fase 10.19B — auditoria de vazao, volume e complacencia pre-fratura — Codex

**Status:** Implementada e validada localmente; commit/push pendente.

**Objetivo:** auditar se a abertura precoce da rota `sigma_theta_static` vinha
de vazao, unidade, fator `2*pi`, incremental/acumulado ou ausência de
complacencia geometrica no balanço moderno.

**Ferramenta criada:**

```text
tools/audit_phase10_19b_flowrate_balance.py
```

**Resultado:**

```text
classification = FLOWRATE_CONVENTION_MATCHES_LEGACY
root_cause_classification = ROOT_CAUSE_MISSING_GEOMETRIC_COMPLIANCE
```

**Numeros principais:**

```text
Q_total_m3_min = 0.0794935
Q_rad_m3_min = 0.01265178346867558
Q_rad_m3_s = 0.00021086305781125968
dV_inj_first_step_rad_m3 = 0.00632589173433779
V_annular_rad_m3 = 0.17842518895535997
C_fluid = 6.4e-10 1/Pa
dP_theoretical_rad_Pa = 55396919.53121999
legacy_first_dP_Pa = 1845413.7784679066
legacy_first_dP_over_theoretical = 0.03331256651017148
```

**Conclusao:** a conversao de vazao/convenção total-vs-radiano nao e causa
raiz. O salto moderno de primeiro passo e compativel com compressao pura do
fluido. A diferenca remanescente e atribuida ao termo geometrico `dV`/complacencia
do legado:

```text
dP = (alpha*dT - (-Vq + dV - dMl/(rho*FC))) / Vi / k
```

**Decisao:** nenhuma correcao C++ foi aplicada. A proxima fase deve planejar
`annular_compliance`/`wellbore_compliance` opt-in, sem ajuste empirico.

---

### [2026-06-10] Fase 10.19A — arquitetura opt-in para sigma-theta runtime no LOT/PKN — Codex

**Status:** Implementada e validada localmente; commit/push pendente.

**Gate:** `SIGMA_THETA_STATIC_PROVIDER_IMPLEMENTATION_ALLOWED`.

**Objetivo:** criar uma rota opt-in para fornecer
`sigma_theta_compression_positive_Pa` ao `volumetric_balance` sem fazer
`PknModel` depender de `saltcreep`, `SaltCreepTimeBridge` ou `coupling/`.

**Arquitetura:**

```text
YAML -> CaseParser -> CaseData -> PknRunner -> PknInput -> PknModel
```

**Novo YAML opt-in:**

```text
lot.fracture.initiation.type = sigma_theta_static
pressure_source = wellbore_pressure_Pa
comparison = legacy_algebra
```

**Algebra:**

```text
margin_Pa = wellbore_pressure_trial_Pa - sigma_theta_compression_positive_Pa
opened = margin_Pa > 0
```

**Caso diagnóstico criado:**

```text
cases/validation/buz67d_pkn_legacy_sigma_theta_static.yaml
```

**Ferramenta diagnóstica criada:**

```text
tools/compare_phase10_19a.py
```

**Resultado BUZ67D 10.19A:**

```text
classification = SIGMA_THETA_STATIC_OPENED_TOO_EARLY
fracture_initiation_time_s = 30.0
fracture_initiation_pressure_Pa = 82129237.46813472
fracture_initiation_sigma_theta_Pa = 67342521.84592447
fracture_initiation_margin_Pa = 14786715.62221025
max_pressure_10_19A = 26732215.17314985 Pa
relative_error_max_10_19A = -0.6127777013426845
```

**Caveat:** `sigma_theta_static` prova o contrato de provider, mas ainda nao e
validacao fisica. O proxy estatico nao substitui `SaltWallStressDiagnostics`
runtime e nao reproduz a altura de influencia legada.

**Proximo passo recomendado:** Fase 10.19B em modo auditoria/planejamento para
definir um provider runtime opt-in de `SigmaThetaInfluenceLayer`, sem alterar o
default `lot-sim run --mode lot-pkn`.

---

### [2026-06-10] Fase 10.18F — auditoria instrumentada do traço de fratura — Codex

**Status:** Implementada e validada localmente; commit/push pendente.

**Objetivo:** instrumentar temporariamente o `LOT_Tese` para observar a ordem
entre `pw > sigmaTheta` e a entrada do sink de fratura/leakoff, reconstruir o
traço moderno do caso estático 10.18E e decidir se havia evidência para uma
correção local no `PknModel`.

**Instrumentação legada temporária:**

```text
legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp
legance/LOT_Tese/src/apb_code/APB1da.cpp
```

As linhas adicionadas foram marcadas com `// AUDIT: Phase 10.18F` durante a
auditoria e removidas antes do commit. `legance/` permanece sem diff
versionável.

**Artefatos locais, não versionados:**

```text
results/comparison/phase10_18f/legacy_trace/buz67d_fracture_trace.csv
results/comparison/phase10_18f/legacy_trace/legacy_fracture_trace_summary.json
results/comparison/phase10_18f/legacy_trace/legacy_fracture_trace_summary.csv
results/comparison/phase10_18f/modern_trace/buz67d_modern_trace.csv
results/comparison/phase10_18f/trace_comparison/trace_comparison.csv
results/comparison/phase10_18f/trace_comparison/trace_comparison_metadata.json
```

**Resultado legado:**

- primeiro `opened`: `510 s`;
- `pw_Pa`: `66769490.24425595`;
- `sigmaTheta_Pa`: `66666624.79984049`;
- `margin_Pa`: `102865.444415465`;
- sink no primeiro `opened`: `0.0 m3`;
- primeiro sink positivo: `540 s`;
- classificação local: `LEGACY_SINK_NEXT_STEP`.

**Resultado moderno 10.18E:**

- primeiro `fracture_initiated_after`: `30 s`;
- primeiro sink positivo: `30 s`;
- `criterion_pressure_Pa`: `82129237.46813472`;
- `breakdown_threshold_Pa`: `8131435.236221395`;
- `wellbore_pressure_after_Pa`: `26732215.17314985`.

**Classificação:**

```text
root_cause_classification = OTHER
correction_allowed = false
```

O moderno abre antes do critério legado sigma-theta. Portanto, a divergência é
classificada como mismatch de critério, não como bug local comprovado na ordem
do sink. Nenhuma correção C++ foi implementada nesta fase.

**Ferramentas adicionadas:**

```text
tools/analyze_legacy_fracture_trace.py
tools/trace_modern_fracture_balance.py
tools/compare_fracture_traces.py
tests/python/test_fracture_trace_tools.py
```

**Próximo passo recomendado:** projetar uma rota opt-in para
`SigmaThetaInfluenceLayer` alimentar o critério de abertura do
`volumetric_balance`, preservando `lot-sim run --mode lot-pkn` sem acoplamento
implícito.

---

### [2026-06-08] Fase 10.18E — calibração diagnóstica do threshold estático de breakdown — Codex

**Status:** Publicada em `b8c887a`.

**Objetivo:** extrair do audit legado um threshold rastreável de início de
fratura e testar se `fracture.breakdown.pressure` calibrado melhora o modo
`volumetric_balance`.

**Fonte legada:**

```text
results/comparison/level1_buz67d/legacy_audit/buz67d_audit_timeseries.csv
results/comparison/level1_buz67d/legacy_audit/legacy_native_output.dat
Momento da quebra: 8.5
```

**Extração:**

- `breakdown_time_s = 510.0`;
- `breakdown_pressure_Pa = 67342521.84592447` (`pw_Pa` absoluto legado);
- `breakdown_delta_pressure_Pa = 8131435.236221395`;
- `modern_static_threshold_Pa = 8131435.236221395`;
- linha selecionada: `layer = 16`, `annular_index = 1`, maior `pw_Pa` no
  instante do evento.

**Caso criado:**

```text
cases/validation/buz67d_pkn_legacy_static_breakdown.yaml
```

O caso usa o delta legado em `fracture.breakdown.pressure`, porque o
`PknModel` atual interpreta esse campo como threshold incremental acima de
`initial_pressure_Pa`.

**Resultado diagnóstico:**

| Modo | Max pressure | Erro relativo contra legado |
|---|---:|---:|
| Legado auditado | `69.035836 MPa` | `0.000` |
| 10.18B | `82.129237 MPa` | `+0.190` |
| 10.18C | `26.732215 MPa` | `-0.613` |
| 10.18E | `26.732215 MPa` | `-0.613` |

Classificação:

```text
STATIC_BREAKDOWN_OPENED_TOO_EARLY
```

O primeiro sink moderno em 10.18E ocorre em `30 s`, antes do marcador legado de
`510 s`. A fase confirma que calibrar apenas `fracture.breakdown.pressure` não
reproduz o critério legado `pw > sigmaTheta`.

**Artefatos locais gerados, não versionados:**

```text
results/comparison/phase10_18e/breakdown_threshold.json
results/comparison/phase10_18e/breakdown_threshold.csv
results/comparison/phase10_18e/phase10_18e_summary.csv
results/comparison/phase10_18e/phase10_18e_metadata.json
results/comparison/phase10_18e/*.png
```

**Arquivos novos versionáveis:**

- `tools/extract_phase10_18e_breakdown_threshold.py`;
- `tools/compare_phase10_18e.py`;
- `tests/python/test_phase10_18e_breakdown_threshold.py`;
- `cases/validation/buz67d_pkn_legacy_static_breakdown.yaml`.

**Não alterado:** legado, saltcreep, parser, CaseData, C++ solver, CLI,
baselines e postprocess.

---

### [2026-06-08] Compatibilidade Codex skills — frontmatter YAML — Codex

**Status:** Corrigido.

O Codex CLI `v0.137.0` passou a recusar `SKILL.md` locais sem frontmatter YAML
delimitado por `---`. O erro aparecia ao abrir o repositório:

```text
Skipped loading 7 skill(s) due to invalid SKILL.md files
missing YAML frontmatter delimited by ---
```

**Causa:** os arquivos existiam e estavam versionados em `.agents/skills/`, mas
sete deles usavam apenas o formato antigo com cabeçalho Markdown
`# SKILL: ...`. Portanto, o problema não era `git pull` deixando de puxar
arquivos; era incompatibilidade de formato com a versão nova do Codex.

**Correção:** adicionados `name` e `description` em frontmatter YAML aos skills:

- `.agents/skills/cpp-refactor/SKILL.md`;
- `.agents/skills/docs-html-report/SKILL.md`;
- `.agents/skills/formulation-audit/SKILL.md`;
- `.agents/skills/lot-salt-integration/SKILL.md`;
- `.agents/skills/postprocess-report/SKILL.md`;
- `.agents/skills/update-devlog/SKILL.md`;
- `.agents/skills/validation-benchmark/SKILL.md`.

**Validação local:** todos os `SKILL.md` em `.agents/skills/` agora começam com
`---` e contêm `name:` e `description:`.

---

### [2026-06-07] Fase 10.18D — gate sigma-theta para fratura runtime — Codex

**Status:** Auditoria concluída; implementação runtime bloqueada pelo gate.

**Gate:** `SIGMA_THETA_AVAILABLE_DIAGNOSTIC_ONLY`.

**Resultado:** `sigma_theta_compression_positive_Pa` existe no diagnóstico
moderno, mas ainda não é fonte runtime para `lot-sim run --mode lot-pkn`.

**Origem confirmada:**

```text
external/saltcreep stress_utils::sigma_theta_compression_positive(sigma)
  -> SaltWallStressDiagnostics::wall_samples
  -> LotSaltSigmaThetaDiagnostic
  -> SigmaThetaBreakdownPoint::sigma_theta_compression_positive_Pa
```

**Critério moderno existente:**

```text
margin_Pa = pressure_Pa - sigma_theta_compression_positive_Pa
opened = margin_Pa > 0
```

**Pressão correta para o critério legado:** `wellbore_pressure_Pa`, porque o
legado compara `pw = pi + dP`, não `p_net`.

**Bloqueio:** o runtime LOT/PKN atual executa
`CaseParser -> PknRunner -> PknModel -> ResultWriter` sem instanciar
`SaltCreepTimeBridge`, sem coletar `SaltWallStressDiagnostics` e sem mapear a
altura de influência para um `wall_gp_*`.

**Decisão:** não implementar `fracture.initiation.type = sigma_theta` nesta
fase. Isso exigiria redesenho de coupling ou duplicação da álgebra de
`LotSaltSigmaThetaBreakdown` dentro de `lot/`.

**Escopo preservado:** nenhum código C++, parser, YAML, schema, `legacy/`,
`legance/`, `external/saltcreep/`, baseline ou postprocess foi alterado.

**Próxima etapa recomendada:** planejar um orquestrador opt-in que forneça
`SigmaThetaInfluenceLayer` ao balanço volumétrico sem alterar o default
`lot-sim run --mode lot-pkn`.

---

### [2026-06-07] Fase 10.18C — fratura/leakoff no balanço volumétrico — Codex

**Status:** Implementada, testada e pronta para commit/push conforme gate da fase.

**Gate:** `FRACTURE_VOLUME_BALANCE_IMPLEMENTATION_ALLOWED_PRESSURE_THRESHOLD_APPROXIMATION`.

**Critério legado auditado:**

```text
P_simulacao = line_up[lu].pi(idAnnular) + line_up[lu].dP(idAnnular)
fratura inicia quando |P_simulacao| > |sigma_tangencial(altura_de_influencia)|
```

**Classificação do critério legado:** `PARTIALLY_EXTRACTED_NOT_REPRODUCED_IN_PKN_MODEL`.

**Implementação moderna:**
- `volumetric_balance` passa a tratar `fracture.breakdown.pressure > 0` como
  aproximação opt-in para habilitar sinks de fratura/leakoff.
- No passo em que o limiar simplificado é cruzado, o balanço já pode descontar:
  `dV_eff = dV_inj - dV_fracture_increment - dV_leakoff_increment`.
- Se `fracture.breakdown.pressure` estiver ausente ou for zero, a abertura fica
  desativada e os sinks de fratura/leakoff não entram no balanço.
- `pkn_direct` permanece inalterado.

**Diagnóstico BUZ67D controlado:**
- legado auditado `max(pw_Pa) = 69.035836 MPa`;
- reconstrução moderna sem sinks `max = 1411.657773 MPa`;
- moderno 10.18C acoplado `max(wellbore_pressure_Pa) = 26.732215 MPa`;
- sink total de fratura/leakoff no moderno 10.18C: `0.993671 m3`.

**Conclusão:** a infraestrutura de sink volumétrico funciona, mas o placeholder
`fracture.breakdown.pressure = 1 Pa` abre a fratura cedo demais. A fase não
declara melhoria numérica nem validação física; apenas estabelece a rota opt-in
para estudos futuros.

**Diagnóstico local não versionado:**
- `results/comparison/phase10_18c/phase10_18c_summary.csv`;
- `results/comparison/phase10_18c/phase10_18c_metadata.json`;
- `results/comparison/phase10_18c/pressure_vs_time_fracture_volume_coupling.png`;
- `results/comparison/phase10_18c/pressure_vs_injected_volume_fracture_volume_coupling.png`.

**Restrição:** não implementou Zamora, fluido composicional, casing elástico,
APB/sal feedback, nova formulação PKN, dano, fechamento complexo ou critério
moderno por `sigmaTheta`/`margin`/`opened`.

---

### [2026-06-07] Fase 10.18B — pressão inicial e schedule com shut-in — Codex

**Status:** Implementada, testada e pronta para commit/push conforme gate da fase.

**Gate 1:** `PRE_EXISTING_PRESSURE_CONFIRMED_IMPLEMENTATION_ALLOWED`.

**Gate 2:** `SHUTIN_CONFIRMED_IMPLEMENTATION_ALLOWED`.

**Classificação do diagnóstico de pressão inicial:**
`PRE_EXISTING_PRESSURE_FIX_PARTIAL_OTHER_FACTORS_REMAIN`.

**Auditoria legada:**
- `Fluids::getPFpressure(depth, seabed, rho)` calcula pressão hidrostática
  preexistente como `p_ref + 9.81 * rho_ppg * 119.826427 * depth`.
- `Layers` armazena essa pressão em `line_up[lu].pi(idAnnular)`.
- `APB1da` usa `pw = pi + dP`.
- O audit CSV BUZ67D registra em `t=0`: `pw_Pa = 26732215.17314985` e
  `dP = 0`.

**Implementação moderna:**
- `lot.initial_pressure` foi adicionado como campo opcional.
- `PknInput` e `PknResult` carregam `initial_pressure_Pa`.
- `volumetric_balance` passa a calcular
  `wellbore_pressure_Pa = initial_pressure_Pa + dP_balance_accumulated`.
- `lot.injection.schedule.phases` foi adicionado como rota opt-in.
- O caso `buz67d_pkn_legacy_aligned.yaml` agora representa:
  `12.5 min` de injeção e `9.5 min` de shut-in, total `1320 s`.

**Diagnóstico:**
- legado auditado `max(pw_Pa) = 69.035836 MPa`;
- moderno 10.18A `max(wellbore_pressure_Pa) = 55.397022 MPa`;
- moderno 10.18B `max(wellbore_pressure_Pa) = 82.129237 MPa`;
- diferença relativa contra legado: `0.198` na 10.18A e `0.190` na 10.18B.

**Conclusão:** a pressão inicial é parte confirmada do contrato legado, e o
schedule com shut-in fecha a faixa temporal `0..1320 s`, mas a soma isolada da
pressão inicial no balanço simplificado superestima a pressão máxima legada.
Não há validação física.

**Artefatos locais não versionados:**
- `results/comparison/phase10_18b/phase10_18b_summary.csv`;
- `results/comparison/phase10_18b/phase10_18b_metadata.json`;
- `results/comparison/phase10_18b/pressure_vs_time_full_cycle.png`;
- `results/comparison/phase10_18b/injected_volume_vs_pressure_full_cycle.png`;
- `results/comparison/phase10_18b/injection_rate_vs_time.png`;
- `results/comparison/phase10_18b/pressure_comparison_all_modes.png`.

**Restrição:** não implementou Zamora, fluido composicional, APB/sal feedback,
casing elástico, novas equações de fratura ou validação de `sigmaTheta`,
`margin` e `opened`.

---

### [2026-06-07] Fase 10.18A — diagnóstico visual do modo volumetric_balance — Codex

**Status:** Implementada, testada e pronta para commit/push conforme gate da fase.

**Classificação:** `VOLUMETRIC_BALANCE_CLOSER_TO_LEGACY`.

**Gate:** `IMPLEMENTATION_ALLOWED_RUN_DIAGNOSTIC`.

**Objetivo:** comparar visualmente, sem validação física, a curva legada
auditada `pw_Pa`, a rota moderna `pkn_direct` (`net_pressure_Pa`) e a rota
moderna opt-in `volumetric_balance` (`wellbore_pressure_Pa`) para o caso
controlado BUZ67D.

**Execução:**
- legado auditado reutilizado de
  `results/comparison/level1_buz67d/legacy_audit/buz67d_audit_timeseries.csv`;
- run moderno `volumetric_balance` gerado em
  `results/comparison/phase10_18a/modern_volumetric`;
- run moderno `pkn_direct` temporário gerado em
  `results/comparison/phase10_18a/modern_direct`;
- ferramenta criada: `tools/compare_phase10_18a.py`.

**Resultado diagnóstico:**
- `max(pw_Pa)` legado auditado: `6.9035836e7 Pa`;
- `max(net_pressure_Pa)` moderno `pkn_direct`: `3.0847520e7 Pa`;
- `max(wellbore_pressure_Pa)` moderno `volumetric_balance`: `5.5397022e7 Pa`;
- diferença relativa no máximo contra legado: `0.553` para `pkn_direct` e
  `0.198` para `volumetric_balance`.

**Artefatos locais não versionados:**
- `results/comparison/phase10_18a/phase10_18a_summary.csv`;
- `results/comparison/phase10_18a/phase10_18a_metadata.json`;
- `results/comparison/phase10_18a/injected_volume_vs_pressure_volumetric.png`;
- `results/comparison/phase10_18a/pressure_vs_time_volumetric.png`;
- `results/comparison/phase10_18a/volume_balance_components.png`.

**Restrição:** diagnóstico apenas. Não declara equivalência numérica, validação
física, comparação de `sigmaTheta`, `margin`, `opened`, dano ou ruptura. Não
implementa shut-in, acomodação pré-injeção ou Zamora.

---

### [2026-06-07] Fase 10.17A — auditoria de balanço volumétrico LOT — Codex

**Status:** Implementada nesta sessao, aguardando commit/push conforme politica da fase.

**Classificacao:** `IMPLEMENTATION_ALLOWED_OPTIONAL_BALANCE_MODE`.

**Objetivo:** Auditar a diferenca entre o balanço volumetrico legado do
`LOT_Tese` e a pressao direta PKN moderna antes de criar qualquer modo novo.

**Evidencia legada:**
- `APB1da(..., LOT=true, idQ=6, Q=0.5, t_no_injection=9.5)` define o
  carregamento BUZ67D PKN.
- `Conv_bbmin_m3min(Q)` converte a vazao com convencao interna por radiano.
- `Vi = 0.5 * (R_outer^2 - R_inner^2) * thickness` entra no balanço.
- `Fluid::kt` vem de `setPFluid(..., 6.40E-10)`.
- `AssemblyFML` usa termos proporcionais a `Vq/Vi/k` e `dV/Vi/k`.
- `calculateLOTFracturedSaltRock()` usa `pw = pi + dP` e `pw > sigmaTheta`.

**Evidencia moderna:**
- `PknModel` calcula `net_pressure_Pa = E' * w / h`.
- `FluidData.compressibility_per_Pa` e volume anular estao disponiveis, mas nao
  participam da pressao PKN direta.

**Artefato:** `tests/fixtures/comparison/phase10_17_balance_audit.json`.

**Gate:** permitido implementar modo opcional `volumetric_balance`, preservando
`pkn_direct` como default e sem declarar validacao fisica.

---

### [2026-06-07] Fase 10.17B — modo opcional de balanço volumétrico LOT — Codex

**Status:** Implementada nesta sessao, aguardando commit/push conforme politica da fase.

**Classificacao:** `OPTIONAL_BALANCE_MODE_IMPLEMENTED_NO_DEFAULT_CHANGE`.

**Objetivo:** Adicionar uma rota moderna opt-in para estimar
`wellbore_pressure_Pa` por balanço volumetrico anular, sem substituir
`net_pressure_Pa` e sem alterar o default `pkn_direct`.

**Implementacao:**
- `lot.pressure_model.type` aceita `pkn_direct` e `volumetric_balance`.
- `pkn_direct` permanece default quando o bloco YAML esta ausente.
- `PknModel` calcula uma serie separada `wellbore_pressure_Pa` quando o modo
  opt-in esta ativo.
- `ResultWriter` exporta campos de diagnostico de balanço no CSV/JSON.
- `cases/validation/buz67d_pkn_legacy_aligned.yaml` ativa
  `volumetric_balance` para o caso controlado.

**Restricao:** a rota e diagnostica. Nao valida pressao, ruptura, abertura de
fratura ou equivalencia fisica com `pw = pi + dP` legado.

---

### [2026-06-07] Fase 10.17C — plano de acomodação, shut-in e Zamora — Codex

**Status:** Implementada como planejamento documental, aguardando commit/push
conforme politica da fase.

**Classificacao:** `PLANNED_NO_RUNTIME_CHANGE`.

**Objetivo:** Registrar os proximos contratos antes de implementar mecanismos
que mudam a fisica operacional do LOT.

**Planejado:**
- `OperationSchedule` com fases `accommodation`, `injection` e `shutin`.
- Shut-in/no-injection como volume injetado constante apos o fim da injecao.
- Interface futura `FluidModel` em C++.
- `ZamoraFluidModel` experimental e opt-in apos auditoria dedicada de unidades.

**Evidencia read-only:** `LOT_APB_v5` contem `Zamora`,
`Zamora_Coefficients`, `setZamora*`, `attZamora*` e getters por profundidade
para densidade, pressao, compressibilidade e expansao termica.

**Restricao:** nenhum runtime, parser, caso YAML padrao ou codigo legado foi
alterado por esta fase.

---

### [2026-06-07] Fase 10.16 — volume anular BUZ67D com drill pipe — Codex

**Status:** Implementada nesta sessao, sem commit/push por instrucao da fase.

**Classificacao:** `DRILLPIPE_ANNULAR_VOLUME_DIAGNOSTIC_EXPORTED`.

**Objetivo:** Corrigir a geometria diagnostica de volume anular do caso
controlado BUZ67D para descontar o drill pipe legado, preservando a convencao
per-radian do `LOT_Tese`.

**Evidencia legada:**
- `Solids.h` define `di` e `de` como diametros em polegadas.
- `Solids::getRi_m()/getRe_m()` convertem polegadas para metro e dividem por 2.
- `Layers.cpp` calcula `Vi = 0.5 * (R_outer^2 - R_inner^2) * thickness`.
- O BUZ67D PKN declara drill pipe `di = 4.67 in`, `de = 5.5 in`.

**Implementacao moderna:** adiciona `wellbore.drill_pipe` ao parser/schema,
utilitario `wellbore::annular_volume_per_radian_m3`, e exportacao de
`initial_annular_volume_per_radian_m3` e `initial_annular_volume_m3` no
`result.json`.

**Escopo fisico:** diagnostico apenas. `PknModel` nao consome volume anular e
`net_pressure_Pa` continua sem equivalencia semantica declarada com `pw_Pa`
legado.

---

### [2026-06-07] Fase 10.15B — audit run visual legado-moderno — Codex

**Status:** Implementada nesta sessao, sem commit/push por instrucao da fase.

**Classificacao:** `LEVEL1B_LEGACY_AUDIT_VISUAL_DIAGNOSTIC_COMPLETE`.

**Objetivo:** Instrumentar temporariamente `legance/LOT_Tese/` apenas para
auditoria, executar o caso BUZ-67D PKN legado, exportar `pw_Pa` e volume
injetado ja calculados pelo legado, e gerar diagnosticos visuais contra a saida
moderna controlada sem declarar validacao fisica.

**Instrumentacao legada:** temporaria, nao comitavel, restaurada ao final.
O patch usado na execucao foi salvo em:

```text
results/comparison/level1_buz67d/legacy_audit/legacy_audit.patch
```

**Arquivos legados temporariamente instrumentados:**
- `legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp` — redirecionamento de
  output para `results/comparison/...`, desativacao de chamada Python/pause.
- `legance/LOT_Tese/src/apb_code/APB1da.cpp` — export CSV auditado em
  `saveFile`, com valores ja calculados: `time_min`, `time_s`, `pw_Pa`,
  `injected_volume_m3`, `Q_raw`, `Q_SI_m3_per_min`,
  `initial_annular_volume_m3`, `dP`.

**Execucao legada auditada:**
- Build: `g++ 16.1.0`, flags `-std=c++17 -w -fpermissive`.
- Binario local: `results/comparison/level1_buz67d/legacy_audit/lot_tese_pkn_audit.exe`.
- Stdout: `results/comparison/level1_buz67d/legacy_audit/legacy_audit_stdout.txt`.
- CSV auditado: `results/comparison/level1_buz67d/legacy_audit/buz67d_audit_timeseries.csv`.
- Linhas auditadas: `900`.
- Tempos agregados: `45`.
- Faixa temporal legada auditada: `0..1320 s`, incluindo fase sem injecao.

**Diagnosticos gerados:**
- `results/comparison/level1_buz67d/injected_volume_vs_pressure.csv`.
- `results/comparison/level1_buz67d/injected_volume_vs_pressure.png`.
- `results/comparison/level1_buz67d/pressure_vs_time_diagnostic.png`.
- `results/comparison/level1_buz67d/annular_volume_comparison.csv`.
- `results/comparison/level1_buz67d/level1b_metadata.json`.

**Bloqueio esperado:** `annular_volume_comparison_status =
BLOCKED_MISSING_VOLUME`, porque o moderno `result.json` nao exporta
`initial_annular_volume_m3`.

**Gate atualizado:** `tests/fixtures/comparison/level1_readiness_gate.json`
permanece com:

```text
level1_ready = false
physical_validation = false
numeric_equivalence = false
pressure_semantic_equivalence = false
awaiting_human_review = true
```

**Caveat central:** `Legacy pw_Pa` e `Modern net_pressure_Pa` podem ter
semanticas diferentes. Esta fase e diagnostica apenas; nao valida equivalencia
fisica, abertura de fratura, dano, ruptura, tensores ou estado tensional.

---

### [2026-06-07] Fase 10.15A — diagnostico Level 1 temporal/estrutural — Codex

**Status:** Implementada nesta sessao, sem commit/push por instrucao da fase.

**Classificacao:** `LEVEL1_STRUCTURAL_DIAGNOSTIC_COMPLETE`.

**Objetivo:** Executar o caso controlado BUZ67D legacy-aligned, extrair a saida
legada completa e gerar diagnostico visual temporal/estrutural em `results/`,
sem validacao fisica e sem versionar outputs gerados.

**Execucao moderna:**
- Caso: `cases/validation/buz67d_pkn_legacy_aligned.yaml`.
- Comando: `lot-sim run --case ... --mode lot-pkn --output results/comparison/level1_buz67d/modern`.
- Saida: `result.json`, `timeseries.csv`.
- Time range moderno: `0..750 s`.
- Time steps: `26`.
- `dt_s_mean = 30`.

**Extracao legada:**
- Fonte: `legance/LOT_Tese/results/8-BUZ-67D-PKN.dat`.
- Saida: `results/comparison/level1_buz67d/legacy`.
- Registros extraidos: `5460`.
- Time range raw: `0..12.5 min`.
- Time range convertido: `0..750 s`.

**Diagnostico Level 1:**
- Criado `tools/compare_level1.py`.
- Criados outputs ignorados em `results/comparison/level1_buz67d/`.
- `level1_summary.csv` registra:
  - legado: `5460 records`, `26 time steps`, `0..750 s`, `dt medio 30 s`;
  - moderno: `26 records`, `26 time steps`, `0..750 s`, `dt medio 30 s`.
- PNGs gerados:
  - `time_coverage.png`;
  - `record_count.png`;
  - `pressure_range_diagnostic.png`;
  - `fields_availability.png`.

**Gate Level 1:**
- `tests/fixtures/comparison/level1_readiness_gate.json` atualizado para
  `LEVEL1_STRUCTURAL_DIAGNOSTIC_COMPLETE`.
- `level1_ready = false`.
- `physical_validation = false`.
- `numeric_equivalence = false`.
- `awaiting_human_review = true`.

**Caveats:**
- `legacy dP` nao e declarado equivalente a `modern net_pressure_Pa`.
- `Layer` legado 1-based nao foi mapeado para indices modernos.
- `sigmaTheta`, `pw`, `margin` e `opened` seguem indisponiveis.
- Os graficos sao diagnosticos, nao validacao fisica.

**Escopo preservado:**
- Nenhuma alteracao em C++, CMake, parser, `CaseData`, CLI, YAMLs, `src/`,
  `include/`, `apps/`, `legance/`, `legacy/`, `external/saltcreep/`,
  baselines ou postprocess.

**Proxima etapa recomendada:** Revisao humana dos graficos antes de decidir
entre Level 2 ou investigacao de divergencias.

---

### [2026-06-07] Fase 10.14EF — parametros legados e caso BUZ67D legacy-aligned — Codex

**Status:** Implementada nesta sessao, sem commit/push por instrucao da fase.

**Classificacao:** `LEVEL1_CONTROLLED_EQUIVALENT_CASE_CREATED_RUN_PENDING`.

**Objetivo:** Extrair parametros legados BUZ67D/PKN em modo read-only e criar um
caso moderno controlado em `cases/validation/`, sem alterar o caso migrado
existente e sem executar `lot-sim run` no caso novo.

**Fontes inspecionadas:**
- `legance/LOT_Tese/results/8-BUZ-67D-PKN.dat`.
- `legance/LOT_Tese/results/8-BUZ-67D-PKN-INC_DT_FULL.dat`.
- `tests/fixtures/comparison/legacy_buz67d_sample.dat`.
- `legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp`.
- `legance/LOT_Tese/include/apb_code/APB1da.h`.
- `legance/LOT_Tese/src/apb_code/APB1da.cpp`.
- `legance/LOT_Tese/include/apb_code/Fluids.h`.
- `legance/LOT_Tese/src/apb_code/Fluids.cpp`.
- `legance/LOT_Tese/include/apb_code/Rock.h`.

**Parametros extraidos:**
- Temporal: `dt = 0.5 min`, `tend = 12.5 min`, `t_no_injection = 9.5 min`.
- Injecao: `Q = 0.5`, `idQ = 6`, comentario legado `0.5 bpm`.
- Geometria: `profTeste = 4374 m`, casing `12.376/14 in`, open hole `13.5 in`.
- Fluido: `density = 11.5 ppg`, `alpha = 8E-4`, `kt = 6.40E-10 Pa^-1`,
  `viscosity = 3 cP`.
- Sal/formacao: halita ativa, `E = 20.4E9 Pa`, `nu = 0.36`, `sg = 2200`,
  `sig0 = 9.92E6 Pa`, `T0 = 86 C`, `n1 = 3.36`, `n2 = 7.55`.
- PKN: `setLeakoffProps("pa_min", 3., "pkn")`.

**Artefatos criados:**
- `tests/fixtures/comparison/buz67d_legacy_parameters.json`.
- `cases/validation/buz67d_pkn_legacy_aligned.yaml`.
- `tests/python/test_legacy_aligned_case.py`.

**Gate Level 1:**
- `tests/fixtures/comparison/level1_readiness_gate.json` atualizado para
  `LEVEL1_CONTROLLED_EQUIVALENT_CASE_CREATED_RUN_PENDING`.
- `level1_ready = false`.
- `physical_validation = false`.
- `numeric_equivalence = false`.

**Validacao:**
- `lot-sim validate --case cases/validation/buz67d_pkn_legacy_aligned.yaml`
  passou.
- A fase nao executou `lot-sim run` no novo caso por restricao de escopo.

**Escopo preservado:**
- Nenhuma alteracao em C++, CMake, parser, `CaseData`, CLI, `src/`, `include/`,
  `apps/`, `legance/`, `legacy/`, `external/saltcreep/`, baselines ou
  postprocess.
- `cases/lot_tese_migrated/buz67d_pkn.yaml`,
  `cases/validation/lot_pkn_minimal.yaml` e
  `cases/validation/lot_pkn_with_leakoff.yaml` permanecem inalterados.

**Proxima etapa recomendada:** Fase 10.15A — executar `lot-sim run` no caso
legacy-aligned e comparar apenas Level 1 temporal/estrutural, sem validacao
fisica.

---

### [2026-06-07] Fase 10.14D — evidence gate temporal para Level 1 — Codex

**Status:** Implementada nesta sessao, sem commit/push por instrucao da fase.

**Classificacao:** `LEVEL1_TIME_UNIT_RESOLVED_CASE_EQUIVALENCE_PENDING`.

**Objetivo:** Registrar a unidade temporal legada confirmada por contexto do
autor e manter um gate documental/testavel impedindo promocao indevida para
comparacao Level 1.

**Evidencia temporal:**
- Tipo: `author_provided_context`.
- Contexto: `APB1da` usa minutos para `dt`, `ttime` e para o campo `Time`
  exportado nos `.dat` LOT_Tese.
- Conversao permitida: `time_s = Time_raw * 60.0`.
- Fixture legado: `0..12.5 min`, equivalente a `0..750 s`.
- Fixture moderno reduzido: `0..420 s`.

**Gate Level 1:**
- `level1_ready = false`.
- `physical_validation = false`.
- `numeric_equivalence = false`.
- Par BUZ67D/PKN classificado como `SIMILAR_CASE`, nao `SAME_CASE`.
- Busca de par melhor nesta fase: `NO_BETTER_PAIR_FOUND`.

**Implementacao:**
- Criado `docs/15_field_normalization.md`.
- Criado `tests/fixtures/comparison/level1_readiness_gate.json`.
- Atualizado `tests/fixtures/comparison/field_mapping_level0.json`.
- Atualizado `tests/python/test_comparison_field_mapping_level0.py`.
- Criado `tests/python/test_level1_readiness_gate.py`.
- Atualizado `tests/fixtures/comparison/README.md`.

**Bloqueios preservados:**
- Nao comparar `sigmaTheta`, `pw`, `margin`, `opened`, `hoop_state`, `j2`,
  von Mises, dano ou fratura.
- Nao assumir equivalencia de `dP` legado com `net_pressure_Pa` moderno.
- Nao assumir equivalencia de `Layer` legado com `wall_gp_*` moderno.

**Escopo preservado:**
- Nenhuma alteracao em C++, CMake, parser, `CaseData`, CLI, YAMLs, `src/`,
  `include/`, `apps/`, `legance/`, `legacy/`, `external/saltcreep/`,
  baselines ou postprocess.

**Proxima etapa recomendada:** revisar a Fase 10.14D; se limpa, commitar como
`test(validation): add level 1 temporal evidence gate`.

---

### [2026-06-07] Fase 10.14C — normalizacao documental de campos legacy-modern — Codex

**Status:** Implementada nesta sessao, sem commit/push por instrucao da fase.

**Classificacao:** `LEVEL0_FIELD_MAPPING_DOCUMENTED_NO_PHYSICAL_VALIDATION`.

**Objetivo:** Formalizar um mapeamento documental e testavel dos campos
legacy-modern para comparacao Nível 0, sem comparacao fisica, sem equivalencia
numerica e sem alterar runtime.

**Implementacao:**
- Criado `tests/fixtures/comparison/field_mapping_level0.json`.
- Criado `tests/python/test_comparison_field_mapping_level0.py`.
- Atualizado `tests/fixtures/comparison/README.md`.
- O mapeamento registra `physical_validation = false` e
  `numeric_equivalence = false`.
- `Time` legado -> `time_s` moderno foi classificado como
  `BLOCKED_UNKNOWN_UNIT`.
- `Layer` legado foi classificado como `BLOCKED_NON_EQUIVALENT_INDEX`.
- `dP` legado -> `net_pressure_Pa` moderno foi classificado como
  `BLOCKED_SEMANTIC_AMBIGUITY`.
- `sigmaTheta`, `pw`, `margin` e `opened` foram classificados como
  `NOT_AVAILABLE_FOR_COMPARISON`.

**Unidade temporal legada:**
- `APB1da::saveFile()` escreve o bloco `Time` a partir de `ttime`.
- `APB1da::Solve()` incrementa `t` com `t += dt` e adiciona `t` a `ttime`.
- O `.dat` legado nao declara a unidade fisica de `ttime`.
- O fixture legado possui `Time raw = 0.0 .. 12.5`; o fixture moderno possui
  `time_s = 0.0 .. 420.0`.
- Conclusao: `Legacy temporal unit remains BLOCKED_UNKNOWN_UNIT; temporal
  numeric comparison remains suspended.`

**Escopo preservado:**
- Nao houve alteracao em C++, CMake, YAMLs, schemas, parser, `CaseData`, CLI,
  LOT/APB, `external/saltcreep/`, `legacy/`, `legance/`, baselines ou
  postprocess.

**Proxima etapa recomendada:** Fase 10.14D — normalizacao temporal controlada
ou bloqueio formal definitivo.

---

### [2026-06-07] Fase 10.14B — comparação Nível 0 com dados reais reduzidos — Codex

**Status:** Implementada nesta sessao, sem commit/push por instrucao da fase.

**Classificacao:** `LEVEL0_REAL_REDUCED_FIXTURES_ESTABLISHED_NO_PHYSICAL_VALIDATION`.

**Objetivo:** Complementar os fixtures temporarios da Fase 10.14A com um
conjunto pequeno de arquivos reais reduzidos, versionados e apropriados para validar o
contrato estrutural Nível 0 sem processar outputs legados grandes.

**Implementacao:**
- Criado `tests/fixtures/comparison/`.
- Adicionados `legacy_buz67d_sample.dat`,
  `legacy_score_mro28_sample.json`, `modern_buz67d_sample.csv` e `README.md`.
- Criado `tests/python/test_comparison_level0.py`.
- O fixture `.dat` e um recorte de
  `legance/LOT_Tese/results/8-BUZ-67D-PKN.dat`.
- O fixture JSON e um bloco temporal reduzido de
  `legance/LOT_APB_v5/SCORE-MRO-28_output.json`.
- O fixture CSV moderno e um recorte de `lot-sim run --mode lot-pkn` do caso
  BUZ67D migrado.
- Criado `tests/fixtures/legacy_modern_level0/buz67d_reduced/`.
- Adicionados `legacy_points.csv`, `legacy_summary.csv`, `modern_points.csv` e
  `modern_summary.csv` reduzidos.
- O lado legado representa linhas ja extraidas de
  `legance/LOT_Tese/results/8-BUZ-67D-PKN.dat`.
- O lado moderno representa linhas reduzidas de uma saida moderna
  `lot-sim run --mode lot-pkn` do caso BUZ67D migrado.
- `tests/python/test_compare_legacy_modern_level0.py` passou a testar esse par
  versionado alem dos fixtures temporarios.

**Escopo e caveats:**
- A comparacao segue limitada a sanidade estrutural Nível 0.
- A fase nao compara `sigmaTheta`, `pw`, `margin`, `opened`, `hoop_state`,
  `j2`, von Mises, dano ou fratura.
- A unidade temporal legada continua desconhecida.
- `Layer` legado continua nao equivalente a `wall_gp_*`.
- Nao ha validacao fisica legado-moderno.

**Escopo preservado:**
- Nao houve alteracao em codigo C++, CMake, YAMLs, schemas, parser,
  `CaseData`, CLI, LOT/APB, `external/saltcreep/`, `legacy/`, `legance/`,
  baselines ou postprocess.

**Proxima etapa recomendada:** revisar a Fase 10.14B; se limpa, commitar junto
com a Fase 10.14A ou em commit dedicado de testes de validacao.

---

### [2026-06-07] Fase 10.14A — comparação Nível 0 com fixtures Python — Codex

**Status:** Implementada nesta sessao, sem commit/push por instrucao da fase.

**Classificacao:** `LEVEL0_STRUCTURAL_CONTRACT_ESTABLISHED_NO_PHYSICAL_VALIDATION`.

**Objetivo:** Criar a primeira comparacao executavel legado-moderno em Nível 0,
limitada a sanidade estrutural e baseada somente em fixtures temporarios. A
fase valida o contrato antes de uma ferramenta real e nao processa outputs
legados grandes.

**Implementacao:**
- Criado `tests/python/test_compare_legacy_modern_level0.py`.
- O teste cria `legacy_points.csv`, `legacy_summary.csv`, `modern_points.csv`
  e `modern_summary.csv` dentro de `TemporaryDirectory`.
- A comparacao calcula `legacy_n_records`, `legacy_n_times`,
  `legacy_time_min_raw`, `legacy_time_max_raw`, `legacy_n_layers`,
  `modern_n_points`, `modern_n_steps`, `modern_time_min_s`,
  `modern_time_max_s` e `modern_n_samples_per_step`.
- O alinhamento temporal legado-moderno permanece marcado como
  `requires_time_unit_normalization`.
- O alinhamento `Layer` legado versus `wall_gp_*` moderno permanece marcado
  como `requires_layer_mapping`.

**Caveats obrigatorios emitidos:**
- unidade temporal legada desconhecida;
- `Layer` legado 1-based nao equivalente a `wall_gp_*`;
- `sigmaTheta`, `pw`, `margin` e `opened` nao exportados pelo legado;
- comparacao apenas estrutural, sem validacao fisica.

**Escopo preservado:**
- Nao houve alteracao em codigo C++, CMake, YAMLs, schemas, parser,
  `CaseData`, CLI, LOT/APB, `external/saltcreep/`, `legacy/`, `legance/`,
  baselines ou postprocess.

**Proxima etapa recomendada:** criar uma ferramenta opt-in
`tools/compare_legacy_modern_level0_level1.py` somente depois de revisar e
commitar este contrato de fixtures.

---

### [2026-06-07] Fase 10.13 — estratégia de comparação legado ↔ moderno — Codex

**Status:** Auditoria documental concluida nesta sessao, sem commit/push por
instrucao da fase.

**Objetivo:** Definir a estrategia de comparacao entre os outputs legados ja
extraiveis (`LOT_Tese` `.dat` e `LOT_APB_v5` JSON) e os artefatos modernos do
diagnostico sigma-theta, sem implementar comparacao numerica, sem instrumentar
legado e sem alterar runtime.

**Documento criado:**
- `docs/14_comparison_strategy.md`.

**Conteudo registrado:**
- Inventario dos campos legados extraidos pela Fase 10.12B.
- Inventario dos campos modernos exportados por `points.csv`, `summary.csv` e
  `metadata.json` do writer sigma-theta.
- Matriz de comparabilidade com 23 pares, usando as classes `direct`,
  `transform`, `qualitative` e `blocked`.
- Distribuicao por comparabilidade: `direct = 3`, `transform = 6`,
  `qualitative = 5`, `blocked = 9`.
- Distribuicao por prioridade: `P0 = 4`, `P1 = 5`, `P2 = 7`, `P3 = 7`.
- Sequencia recomendada em cinco niveis, de sanidade estrutural ate campos de
  acoplamento fisico.
- Casos minimos recomendados para Nivel 0 e Nivel 1.
- Pre-requisitos tecnicos, riscos de falso-positivo/falso-negativo e decisao
  sobre instrumentacao futura.

**Escopo preservado:**
- Nao houve alteracao em C++, testes, CMake, parser, `CaseData`, CLI, YAMLs,
  schemas, `external/saltcreep/`, `legance/`, `legacy/`, baselines ou
  postprocess.

**Resultado:** Documento de estrategia criado e referenciado em
`docs/13_coupling_lot_apb_salt.md`.

---

### [2026-06-07] Fase 10.12B — extrator read-only de outputs legados — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar uma ferramenta nao-runtime em `tools/` para extrair campos
ja exportados por outputs legados do `LOT_Tese` e do `LOT_APB_v5`, sem
instrumentar `legance/`, sem executar o legado e sem comparar numericamente com
o diagnostico sigma-theta moderno.

**Implementacao:**
- Criado `tools/extract_legacy_lot_outputs.py`.
- Criado `tests/python/test_extract_legacy_lot_outputs.py` com fixtures
  minimos temporarios para `.dat` do `LOT_Tese`, JSON do `LOT_APB_v5`,
  `Momento da quebra`, entrada por diretorio e metadados.
- A ferramenta aceita arquivos ou diretorios em `--input` e escreve em
  `--output-dir`:
  - `legacy_points.csv`;
  - `legacy_summary.csv`;
  - `legacy_metadata.json`.
- Para `.dat`, o parser expande blocos `Time`/`Layer`/campo/matriz e preserva
  `time_raw`; a unidade temporal permanece `unknown`.
- Para JSON v5, o parser extrai pressoes, volumes, vazamentos e deslocamentos
  quando presentes, convertendo `psi -> Pa` com `1 psi = 6894.757293168 Pa`.
- `pw`, `sigmaTheta`, `margin` e `opened` sao marcados como ausentes sem
  instrumentacao.

**Escopo preservado:**
- Nao houve alteracao em C++, CMake, parser, `CaseData`, CLI, YAMLs, schemas,
  LOT/APB, `ResultWriter`, `apps/lot-sim.cpp`, `legance/`, `legacy/`,
  `external/saltcreep/`, baselines ou postprocess.

**Testes e verificacoes executados:**
- `python -m pytest tests/python/test_extract_legacy_lot_outputs.py`: 5/5
  passaram.
- `python -m unittest discover -s tests\python`: 8/8 passaram.
- Extracao real `legance/LOT_Tese/results`: 54 inputs processados,
  8.855.768 registros em `results/legacy_extract/LOT_Tese`.
- Extracao real `legance/LOT_APB_v5/SCORE-MRO-28_output.json`: 1 input
  processado, 297 registros em
  `results/legacy_extract/LOT_APB_v5_SCORE_MRO_28_sample`.
- Validacoes `lot-sim validate` passaram para os tres casos LOT/PKN principais.
- `lot-sim run --mode lot-pkn` passou para os tres casos LOT/PKN principais.
- `python tools/generate_docs_index.py` executado.
- `git diff --check` passou com aviso CRLF conhecido em `docs/dev-log.md`.
- Escopo protegido verificado vazio.

**Resultado:** Implementado e validado localmente nesta sessao, aguardando
revisao/commit.

---

### [2026-06-04] Fase 10.11B — mapeamento `LOT_Tese` para sigma-theta moderno — Codex

**Status:** Documentacao/formulacao concluida nesta sessao, sem commit/push por
instrucao da fase.

**Objetivo:** Formalizar o contrato de mapeamento entre o criterio legado
`LOT_Tese` e os campos do diagnostico sigma-theta moderno, sem comparacao
numerica, sem instrumentar `legance/` e sem alterar runtime.

**Mapeamento documentado:**
- `pw = line_up[lu].pi(idAnnular) + line_up[lu].dP(idAnnular)` -> pressao de
  poco/anular usada contra a parede/rocha vizinha, unidade aparente Pa.
- `sigmaTheta = -line_up[lu].mdl->getSigmaTheta()` ->
  `sigma_theta_compression_positive_Pa`.
- `dP_leakoff = pw - sigmaTheta` -> `margin_Pa`.
- `pw > sigmaTheta` -> `opened` e `legacy_algebra_opened`, apenas como algebra
  legada/experimental.
- `line_up[lu].depth_influence` e `line_up[lu].thickness` foram registrados
  como profundidade e altura de influencia do legado, ainda sem equivalencia
  plena com `wall_gp_*` moderno.

**Lacunas registradas:**
- `LOT_Tese` calcula `pw`, `sigmaTheta`, `margin` e `opened`, mas nao exporta
  diretamente esses campos no `.dat` principal identificado.
- Unidade temporal precisa ser confirmada por causa do historico FA01.
- `LOT_APB_v5` exporta pressao em psi em JSON; o diagnostico moderno usa Pa.
- `getElem(0)` e amostra mais interna/proxima da parede, nao extrapolacao exata.
- Comparacao numerica direta exigira extractor legado, instrumentacao controlada
  ou comparacao limitada aos campos ja exportados.

**Escopo preservado:**
- Nao houve alteracao em C++, testes, CMake, parser, `CaseData`, CLI, YAMLs,
  schemas, `legance/`, `legacy/`, `external/saltcreep/`, baselines ou
  postprocess.

**Resultado:** Contrato documental registrado em `docs/13_coupling_lot_apb_salt.md`
e status `phase_10_11b_lot_tese_sigma_theta_mapping: completed` adicionado em
`tools/docs_status.yaml`.

---

### [2026-06-04] Fase 10.10 — exportacao da matriz sigma-theta — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Provar que o writer experimental `LotSaltSigmaThetaDiagnosticWriter`
consegue exportar a matriz de tres cenarios sigma-theta criada na Fase 10.8B.

**Implementacao:**
- Adicionado teste integrado em
  `tests/cpp/test_lot_salt_sigma_theta_diagnostic_writer.cpp`.
- O teste usa `cases/validation/lot_pkn_minimal.yaml` e constrói tres cenarios:
  - sem geostatica;
  - geostatica sintetica explicita com `-2 MPa`;
  - geostatica litostatica via `with_lithostatic_geostatic(...)`.
- Cada cenario executa `run_lot_salt_sigma_theta_experimental(...)`.
- A matriz e exportada com `write_lot_salt_sigma_theta_diagnostics(...)` para
  diretorio temporario do teste, gerando `points.csv`, `summary.csv` e
  `metadata.json`.
- O teste verifica que os tres cenarios aparecem nos tres artefatos e que a
  contagem de linhas de `points.csv` corresponde a soma dos pontos diagnosticos
  dos tres resultados.

**Escopo preservado:**
- Nao altera writer, driver, diagnostico, breakdown, bridge, CLI, parser,
  `CaseData`, `ResultWriter`, LOT/APB, YAMLs, schemas, saltcreep, legados,
  baselines ou postprocess.
- Nao usa `results/` de producao.
- Nao compara com `LOT_Tese`, nao cria HTML e nao chama pos-processamento
  Python.

**Testes executados:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure`: 203/203 passaram.
- Filtro `writer|Writer|scenario|Scenario|sigma_theta|SigmaTheta|diagnostic|Diagnostic|coupling|Coupling`: 47/47 passaram.
- Filtro `LOT PKN.*identical`: 2/2 passaram.
- `python tools/generate_docs_index.py` executado.
- Validacoes manuais `validate` passaram para:
  - `cases/validation/lot_pkn_minimal.yaml`
  - `cases/validation/lot_pkn_with_leakoff.yaml`
  - `cases/lot_tese_migrated/buz67d_pkn.yaml`
- `run --mode lot-pkn` passou para os tres casos, com saidas em:
  - `results/phase10_10_minimal`
  - `results/phase10_10_leakoff`
  - `results/phase10_10_buz67d`

**Resultado:** Implementado e validado localmente, aguardando revisao/commit.

---

### [2026-06-04] Fase 10.9B — writer experimental CSV/JSON sigma-theta — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar um writer experimental opt-in para exportar resultados de
`LotSaltSigmaThetaDriverResult` em `points.csv`, `summary.csv` e
`metadata.json`, sem conectar ao CLI, sem alterar `ResultWriter` e sem tornar a
saida oficial do simulador.

**Implementacao:**
- Criada API `LotSaltSigmaThetaDiagnosticWriter` em `coupling/`.
- O writer consome cenarios ja calculados pelo driver sigma-theta e escreve:
  - `points.csv`, granular por ponto diagnostico em ordem time-major;
  - `summary.csv`, agregado por cenario;
  - `metadata.json`, com origem experimental, arquivos e caveats.
- A validacao exige `case_id`, `scenario_id`, `scenario_label`, resultado,
  diagnostico e tensao de parede validos, series PKN compatíveis e quantidade
  de pontos igual a `n_steps * n_wall_samples`.
- A fase nao altera `LotSaltSigmaThetaDriver`, `LotSaltSigmaThetaDiagnostic`,
  `LotSaltSigmaThetaBreakdown`, `SaltCreepTimeBridge`, `ResultWriter`,
  `apps/lot-sim.cpp`, parser, `CaseData`, YAMLs, LOT/APB, saltcreep, legados,
  baselines ou postprocess.

**Testes executados:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure`: 202/202 passaram.
- Filtro `writer|Writer|sigma_theta|SigmaTheta|diagnostic|Diagnostic|driver|Driver|coupling|Coupling`: 46/46 passaram.
- Filtro `LOT PKN.*identical`: 2/2 passaram.
- `python tools/generate_docs_index.py` executado.
- Validacoes manuais `validate` passaram para:
  - `cases/validation/lot_pkn_minimal.yaml`
  - `cases/validation/lot_pkn_with_leakoff.yaml`
  - `cases/lot_tese_migrated/buz67d_pkn.yaml`
- `run --mode lot-pkn` passou para os tres casos, com saidas em:
  - `results/phase10_9b_minimal`
  - `results/phase10_9b_leakoff`
  - `results/phase10_9b_buz67d`

**Resultado:** Implementado e validado localmente, aguardando revisao/commit.

---

### [2026-06-04] Fase 10.8B — matriz interna de cenarios sigma-theta — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar uma matriz interna controlada para comparar o diagnostico
sigma-theta em tres cenarios de confinamento, sem envolver `LOT_Tese`, sem
exportador CSV/JSON e sem alterar runtime.

**Implementacao:**
- Adicionado test case em `tests/cpp/test_lot_salt_sigma_theta_driver.cpp`.
- A matriz usa `cases/validation/lot_pkn_minimal.yaml` via parser real.
- Os tres cenarios comparados sao:
  - sem geostatica;
  - geostatica sintetica explicita com `geostatic_* = -2 MPa`;
  - geostatica litostatica via `with_lithostatic_geostatic(...)`.
- Helpers locais ao teste calculam `compressive_count`, `neutral_count`,
  `tensile_count`, min/max de
  `sigma_theta_compression_positive_Pa`, min/max de `margin_Pa`,
  `any_opened` e `any_legacy_algebra_opened`.
- Cada cenario verifica resultado valido, tensao de parede valida,
  diagnostico valido, pontos nao vazios, summary finito e `step_count`
  preservado.

**Observacao do snapshot atual:**
- Sem geostatica: 21 pontos `Tensile`.
- Geostatica sintetica `-2 MPa`: sem pontos `Compressive`.
- Geostatica litostatica: 21 pontos `Compressive`.

**Limites deliberados:**
- Nenhuma API publica foi criada.
- Nao houve alteracao em `LotSaltSigmaThetaDriver`,
  `LotSaltSigmaThetaDiagnostic`, `LotSaltSigmaThetaBreakdown`,
  `LotSaltBridgeConfigBuilder`, `LotSaltLithostaticContext`,
  `SaltCreepTimeBridge`, parser, `CaseData`, CLI, LOT/APB, YAMLs, schemas,
  `external/saltcreep/`, legados, baselines ou postprocess.
- A matriz permanece experimental/opt-in, usa snapshot unico e nao e
  validacao fisica de fratura.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

**Verificacao:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure`: 196/196 passaram.
- Filtro `scenario|Scenario|lithostatic|Lithostatic|driver|Driver|sigma_theta|SigmaTheta|coupling|Coupling`: 42/42 passaram.
- Filtro `LOT PKN.*identical`: 2/2 passaram.
- Teste isolado da matriz confirmou:
  - sem geostatica: 21 pontos `Tensile`;
  - geostatica sintetica `-2 MPa`: 0 pontos `Compressive`;
  - geostatica litostatica: 21 pontos `Compressive`;
  - todos os cenarios preservaram `step_count = 0`.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando
  `results/phase10_8b_minimal`, `results/phase10_8b_leakoff` e
  `results/phase10_8b_buz67d`.

---

### [2026-06-04] Fase 10.7 — teste integrado com geostatica litostatica — Codex

**Status:** Concluido e publicado em `bff4f14`.

**Objetivo:** Adicionar um teste integrado end-to-end para a rota opt-in:
`CaseData -> with_lithostatic_geostatic -> make_lot_salt_bridge_config ->
SaltCreepTimeBridge -> run_lot_salt_sigma_theta_experimental`.

**Implementacao:**
- Adicionado test case em `tests/cpp/test_lot_salt_sigma_theta_driver.cpp`.
- O teste usa `cases/validation/lot_pkn_minimal.yaml` via parser real.
- `with_lithostatic_geostatic()` preenche a geostatica litostatica em
  `LotSaltBridgeConfigOptions`.
- `make_lot_salt_bridge_config()` produz config com
  `geostatic_enabled=true`, tensoes geostaticas negativas e
  `fix_outer_wall=true`.
- O driver sigma-theta experimental roda sobre o bridge sem avancar o estado
  temporal (`step_count` preservado).
- O teste verifica resultado valido, tensao de parede valida, diagnostico
  valido, pontos diagnosticos nao vazios e estado hoop rastreavel.

**Limites deliberados:**
- Nenhuma nova API foi criada.
- `LotSaltLithostaticContext`, `LotSaltBridgeConfigBuilder`,
  `SaltCreepTimeBridge`, driver/diagnosticos sigma-theta, parser, `CaseData`,
  CLI, LOT/APB, YAMLs, schemas, `external/saltcreep/`, legados, baselines e
  postprocess nao foram alterados.
- O teste permanece experimental/opt-in e nao representa validacao fisica de
  fratura ou acoplamento temporal.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

**Verificacao:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure`: 195/195 passaram.
- Filtro `lithostatic|Lithostatic|driver|Driver|sigma_theta|SigmaTheta|bridge_config|BridgeConfig|coupling|Coupling`: 52/52 passaram.
- Filtro `LOT PKN.*identical`: 2/2 passaram.
- Teste isolado da Fase 10.7 confirmou `geostatic_* = -63547092 Pa`,
  `fix_outer_wall=true`, `step_count` preservado em 0 e estado hoop
  rastreavel; houve ao menos um estado `Compressive` no snapshot observado.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando
  `results/phase10_7_minimal`, `results/phase10_7_leakoff` e
  `results/phase10_7_buz67d`.

---

### [2026-06-04] Fase 10.6B — contexto litostatico opt-in para geostatica — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar um helper experimental opt-in em `coupling/` para derivar
uma geostatica litostatica isotropica simples a partir de `CaseData`, sem
alterar parser, `CaseData`, builder principal automaticamente ou runtime LOT.

**Implementacao:**
- Criado `include/coupling/LotSaltLithostaticContext.hpp`.
- Criado `src/coupling/LotSaltLithostaticContext.cpp`.
- Criado `tests/cpp/test_lot_salt_lithostatic_context.cpp`.
- `make_lot_salt_lithostatic_context(data)` seleciona a layer que contem
  `lot.shoe_depth_m`, resolve a rocha por `layer.rock_id`, valida
  `rock.density_kg_m3 > 0` e calcula `rho_rock * g * depth`.
- `with_lithostatic_geostatic(options, data)` retorna options com
  `geostatic_enabled=true` e as tres tensoes geostaticas iguais a
  `-lithostatic_pressure_Pa`.

**Limites deliberados:**
- A aproximacao e isotropica e nao representa tensor in situ real.
- Nao inclui tectonica, pressao de poros, anisotropia ou closure stress.
- Nao identifica automaticamente se a rocha e sal.
- CLI, parser, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter`,
  `SaltCreepTimeBridge`, diagnosticos sigma-theta, pressure map, coupling
  config builder, hydrostatic context, YAMLs, schemas, LOT/APB, sal,
  `external/saltcreep/`, legados, baselines e postprocess nao foram alterados.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

**Verificacao:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure`: 194/194 passaram.
- Filtro `lithostatic|Lithostatic|bridge_config|BridgeConfig|sigma_theta|SigmaTheta|driver|Driver|coupling|Coupling`: 51/51 passaram.
- Filtro `LOT PKN.*identical`: 2/2 passaram.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando
  `results/phase10_6b_minimal`, `results/phase10_6b_leakoff` e
  `results/phase10_6b_buz67d`.

---

### [2026-06-04] Fase 10.5B — classificacao explicita de hoop tensile state — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Permitir que o diagnostico experimental `sigma_theta` represente
explicitamente estados tangenciais trativos em vez de rejeitar
`sigma_theta_compression_positive_Pa < 0` por excecao.

**Implementacao:**
- Adicionado `SigmaThetaHoopState` com estados `Compressive`, `Neutral` e
  `Tensile`.
- Adicionados `classify_sigma_theta_hoop_state()` e `to_string()`.
- `SigmaThetaBreakdownPoint` passou a carregar `hoop_state`,
  `tensile_hoop_state`, `legacy_algebra_opened` e `caveat`.
- `LotSaltSigmaThetaBreakdown` continua rejeitando `NaN`/`Inf`, mas nao rejeita
  mais `sigma_theta_compression_positive_Pa < 0`.
- `LotSaltSigmaThetaDiagnostic` tambem aceita amostras trativas de
  `SaltWallStressDiagnostics` e preserva o estado/caveat no resultado.
- Testes do driver builder -> bridge -> driver deixam de sobrescrever
  `bridge_config.wall_pressure_Pa = 0.0`; a pressao hidrostatica derivada pelo
  builder agora pode produzir estado `Tensile` rastreavel.

**Limites deliberados:**
- `opened` em estado `Tensile` representa apenas algebra experimental/legada
  (`pressure > -getSigmaTheta()`), nao criterio fisico validado.
- CLI, parser, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter`,
  `SaltCreepInterface`, `SaltCreepResponse`, adapters de sal, bridge, pressure
  map, builders hidrostatico/bridge, YAMLs, schemas, LOT/APB, sal,
  `external/saltcreep/`, legados, baselines e postprocess nao foram alterados.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 186/186.
- Filtro `sigma_theta|SigmaTheta|diagnostic|Diagnostic|driver|Driver|
  coupling|Coupling` passou com 36/36.
- Filtro `LOT PKN.*identical` passou com 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase10_5b_minimal`, `results/phase10_5b_leakoff` e
  `results/phase10_5b_buz67d`.

---

### [2026-06-04] Fase 10.4 — geostatica explicita e teste builder-bridge-driver — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Expandir `LotSaltBridgeConfigOptions` com geostatica explicita e
testar a cadeia experimental `CaseData -> LotSaltBridgeConfigBuilder ->
SaltCreepTimeBridge -> LotSaltSigmaThetaDriver`.

**Fase 10.4A — geostatica explicita:**
- `LotSaltBridgeConfigOptions` recebeu
  `geostatic_radial_stress_Pa`, `geostatic_hoop_stress_Pa` e
  `geostatic_vertical_stress_Pa`.
- `geostatic_enabled=true` agora preenche as tres tensoes no
  `SaltCreepTimeBridgeConfig` e marca `fix_outer_wall=true`.
- Tensoes geostaticas precisam ser finitas; `NaN`/`Inf` sao rejeitados.
- O default sem geostatica preserva a Fase 10.3.

**Fase 10.4B — cadeia integrada:**
- Adicionados testes que parseiam `lot_pkn_minimal.yaml`, constroem
  `SaltCreepTimeBridgeConfig` pelo builder, instanciam `SaltCreepTimeBridge` e
  chamam `run_lot_salt_sigma_theta_experimental(data, bridge)`.
- A cadeia foi testada sem geostatica e com geostatica explicita.
- O driver continua usando snapshot unico e nao avanca o bridge.

**Limites deliberados:**
- Geostatica vem de options, nao de `CaseData`.
- Nenhuma tensao litostatica e calculada automaticamente.
- CLI, parser, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter`,
  `SaltCreepTimeBridge`, driver, diagnostic, pressure map, YAMLs, schemas,
  LOT/APB, sal, `external/saltcreep/`, legados, baselines e postprocess nao
  foram alterados.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 180/180.
- Filtro `bridge_config|BridgeConfig|sigma_theta|SigmaTheta|wall_stress|
  WallStress|time_bridge|TimeBridge|saltcreep` passou com 48/48.
- Filtro `LOT PKN.*identical` passou com 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase10_4_minimal`, `results/phase10_4_leakoff` e
  `results/phase10_4_buz67d`.
- `git diff --check` passou com aviso CRLF conhecido em `docs/dev-log.md`.

---

### [2026-06-04] Fase 10.3 — `LotSaltBridgeConfigBuilder` experimental — Codex

**Status:** Implementado nesta sessao, sem commit/push ate a verificacao final.

**Objetivo:** Criar um helper experimental opt-in em `coupling/` para montar
`SaltCreepTimeBridgeConfig` a partir de `CaseData` e options explicitas, sem
construir nem avancar o bridge.

**Implementacao:**
- Criado `include/coupling/LotSaltBridgeConfigBuilder.hpp`.
- Criado `src/coupling/LotSaltBridgeConfigBuilder.cpp`.
- Criado `tests/cpp/test_lot_salt_bridge_config_builder.cpp`.
- O helper seleciona a unica layer que contem `lot.shoe_depth_m`, resolve a
  rocha via `layer.rock_id`, copia `E_Pa` e `nu`, usa geometria/temperatura das
  options e deriva `wall_pressure_Pa` inicial via `LotSaltHydrostaticContext`.

**Limites deliberados:**
- `SaltCreepTimeBridge` nao e construido pelo helper.
- `bridge.advance_to()`, `bridge.advance_by()` e
  `bridge.wall_stress_diagnostics()` nao sao chamados pelo helper.
- Geostatica nao e inferida de `CaseData`; `geostatic_enabled=true` e rejeitado
  nesta fase.
- `height_m = lot.fracture_height_m` e aproximacao experimental documentada.
- CLI, parser, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter`, YAMLs,
  LOT/APB, sal, `external/saltcreep/`, legados, baselines e postprocess
  permanecem fora do escopo.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 175/175.
- Filtro `bridge_config|BridgeConfig|bridge|Bridge|driver|Driver|
  sigma_theta|SigmaTheta|wall_stress|WallStress|coupling|Coupling` passou com
  54/54.
- Filtro `LOT PKN.*identical` passou com 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase10_3_minimal`, `results/phase10_3_leakoff` e
  `results/phase10_3_buz67d`.

---

### [2026-06-04] Fase 10.2B — `LotSaltSigmaThetaDriver` experimental opt-in — Codex

**Status:** Implementado nesta sessao, sem commit/push ate a verificacao final.

**Objetivo:** Criar um driver experimental opt-in em `coupling/` que recebe
`CaseData`, `SaltCreepTimeBridge&` ja configurado e
`LotSaltCouplingConfigOptions`, executando a cadeia diagnostica:

```text
CaseData -> LotSaltCouplingConfigBuilder -> run_pkn_case(data)
         -> bridge.wall_stress_diagnostics()
         -> evaluate_lot_salt_sigma_theta_series(...)
```

**Implementacao:**
- Criado `include/coupling/LotSaltSigmaThetaDriver.hpp`.
- Criado `src/coupling/LotSaltSigmaThetaDriver.cpp`.
- Criado `tests/cpp/test_lot_salt_sigma_theta_driver.cpp`.
- O resultado composto carrega `PknRun`, `LotSaltCouplingConfig`,
  `SaltWallStressDiagnostics`, `LotSaltSigmaThetaDiagnosticResult`, `valid` e
  `caveat`.

**Limites deliberados:**
- O driver nao constroi `SaltCreepTimeBridgeConfig`.
- O driver nao chama `bridge.advance_to()` nem `bridge.advance_by()`.
- O driver nao constroi nem chama `SaltCreepSaltcreepAdapter`.
- O driver nao chama `SaltCreepInterface`.
- O driver nao chama `evaluate_lot_salt_step()`.
- O driver usa snapshot unico de tensao do bridge e nao sincroniza tensoes do
  sal com cada passo PKN.
- CLI, parser, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter`, YAMLs,
  LOT/APB, `external/saltcreep/`, legados, baselines e postprocess permanecem
  fora do escopo.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 167/167.
- Filtro `driver|Driver|sigma_theta|SigmaTheta|diagnostic|Diagnostic|
  wall_stress|WallStress|coupling|Coupling` passou com 28/28.
- Filtro `LOT PKN.*identical` passou com 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase10_2b_minimal`, `results/phase10_2b_leakoff` e
  `results/phase10_2b_buz67d`.

---

### [2026-06-04] Fase 10.1 — `LotSaltSigmaThetaDiagnostic` opt-in — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar um helper puro em `coupling/` para diagnostico experimental
end-to-end por `sigma_theta`, recebendo `PknResult`, `LotSaltCouplingConfig` e
`SaltWallStressDiagnostics`.

**Implementacao:**
- Criado `include/coupling/LotSaltSigmaThetaDiagnostic.hpp`.
- Criado `src/coupling/LotSaltSigmaThetaDiagnostic.cpp`.
- Criado `tests/cpp/test_lot_salt_sigma_theta_diagnostic.cpp`.
- O helper monta `LotSaltPressureMapInput`, chama
  `map_lot_pkn_to_salt_wall_pressure()` e usa
  `LotSaltPressureMapResult.wall_pressure_Pa` no criterio experimental.
- Cada `SaltWallStressSample` vira uma `SigmaThetaInfluenceLayer` deterministica
  `wall_gp_<indice>`, preservando metadados de ponto de Gauss, elemento,
  coordenadas, profundidade, tensao media, `J2` e von Mises no resultado.

**Limites deliberados:**
- O helper nao chama `SaltCreepInterface`.
- O helper nao chama `SaltCreepTimeBridge`.
- O helper nao chama `SaltCreepSaltcreepAdapter`.
- `LotSaltCouplingStep`, `LotSaltPressureMap`,
  `LotSaltSigmaThetaBreakdown`, `LotSaltHydrostaticContext`,
  `LotSaltCouplingConfigBuilder`, parser, `CaseData`, LOT/APB, CLI, YAMLs,
  `external/saltcreep/`, legados, baselines e postprocess nao foram alterados.
- `SaltWallStressDiagnostics` e snapshot fornecido pelo chamador; a fase nao
  garante sincronizacao temporal com cada passo PKN.
- O diagnostico permanece experimental, opt-in e nao validado como criterio
  fisico de fratura.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 164/164.
- Filtro `sigma_theta|SigmaTheta|diagnostic|Diagnostic|wall_stress|WallStress|
  coupling|Coupling` passou com 25/25.
- Filtro `LOT PKN.*identical` passou com 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase10_1_minimal`, `results/phase10_1_leakoff` e
  `results/phase10_1_buz67d`.

---

### [2026-06-04] Fase 9.9B — `SaltWallStressDiagnostics` opt-in — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Expor diagnostico opt-in de tensao de parede a partir de
`SaltCreepTimeBridge`, usando DTOs publicos do LSS e sem expor headers de
`external/saltcreep/` na API publica.

**Pre-verificacao do saltcreep:**
- `StressSampler` usa namespace real `stress_sampler`.
- A assinatura real usada e
  `stress_sampler::sample_wall_gauss_points(const Mesh&, const Element&,
  const TimeState&, double depth_origin_m)`.
- O tipo real `StressSample` carrega `gp_id`, `element_id`, `local_gp_id`,
  `r_m`, `z_m`, `depth_m`, `sigma`, `deviatoric`, `mean_stress_Pa`,
  `J2_Pa2` e `sigma_ef_Pa`.
- `TimeIntegrator::state()` retorna `const TimeState&`.
- O `SaltCreepTimeBridge::Impl` ja possui `mesh`, `element` e `integrator`.

**Implementacao:**
- Criado `SaltWallStressDiagnostics` com amostras de tensao de parede em tipos
  LSS puros.
- `SaltCreepTimeBridge::wall_stress_diagnostics()` converte internamente os
  `StressSample` do saltcreep para DTOs LSS.
- `sigma_theta_compression_positive_Pa` e obtido por
  `stress_utils::sigma_theta_compression_positive(sample.sigma)`.
- A amostra de parede e o ponto de Gauss mais proximo da parede interna, sem
  extrapolacao para `r = Ri`.

**Limites deliberados:**
- `SaltCreepInterface` e `SaltCreepResponse` nao foram alterados.
- `LotSaltSigmaThetaBreakdown` nao foi alterado.
- O diagnostico nao e chamado pelo CLI e nao altera `lot-sim run --mode
  lot-pkn`.
- `deviatoric`, `J2` e von Mises sao expostos como diagnostico, mas nao viram
  criterio fisico validado de fratura.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 158/158.
- Filtro `wall_stress|WallStress|stress_diagnostics|StressDiagnostics|
  sigma_theta|SigmaTheta|bridge|Bridge|coupling|Coupling` passou com 37/37.
- Filtro `LOT PKN.*identical` passou com 2/2.

---

### [2026-06-04] Fase 9.8 — diagnostico experimental por `sigma_theta` — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar `LotSaltSigmaThetaBreakdown` como diagnostico puro em
`coupling/` para comparar uma pressao de parede contra
`sigma_theta_compression_positive_Pa` por camada/altura de influencia.

**Criterio implementado:**

```text
margin_Pa = pressure_Pa - sigma_theta_compression_positive_Pa
opened = margin_Pa > 0
```

Igualdade nao indica abertura. A funcao de serie retorna pontos em ordem
deterministica tempo externo/camada interna.

**Convencao de sinal:**
- A API recebe `sigma_theta_compression_positive_Pa` ja convertido.
- Para reproduzir o legado quando `getSigmaTheta()` retornar compressao
  negativa, o chamador deve usar `sigma_theta_compression_positive_Pa =
  -getSigmaTheta()`.
- Nenhuma conversao automatica de sinal foi implementada.

**Limites deliberados:**
- O diagnostico nao chama `SaltCreepInterface`.
- `getDeviatoricStress()` foi mantido como candidato futuro e nao foi
  implementado.
- `LotSaltPressureMap`, `LotSaltCouplingStep`, `LotSaltHydrostaticContext`,
  `LotSaltCouplingConfigBuilder`, `PknRunner`, `PknModel`, parser,
  `CaseData`, CLI, YAMLs, LOT/APB, sal externo, baselines e postprocess nao
  foram alterados.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 153/153.
- Filtro `sigma_theta|SigmaTheta|breakdown|Breakdown|coupling|Coupling`
  passou com 14/14.
- Filtro `LOT PKN.*identical` passou com 2/2.
- `lot-sim validate` e `lot-sim run --mode lot-pkn` passaram para os casos
  `lot_pkn_minimal.yaml`, `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.

---

### [2026-06-04] Fase 9.7A — limitacoes de inferencia de breakdown no PKN atual — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Documentar que o fluxo PKN moderno atual ainda nao fornece um
evento fisico robusto de breakdown nem `p_net_at_breakdown`.

**Conclusao documental:**
- `breakdown_pressure_Pa` e parseado, validado e repassado para `PknInput`, mas
  nao controla diretamente o inicio da fratura, a geracao das series PKN ou
  `PknResult.net_pressure_series_Pa`.
- `PknModel` gera uma resposta PKN ja iniciada/ativa, nao uma rampa
  pre-breakdown ate ruptura.
- `PknResult` ainda nao expoe `breakdown_step`, `breakdown_time_s`,
  `p_net_at_breakdown` ou `fracture_initiation_step`.
- `p_net_at_breakdown` nao deve ser inferido por primeiro `p_net > 0`, primeiro
  `width`, `length` ou `volume` positivo, `breakdown_pressure_Pa` ou aplicacao
  direta de `BreakdownDetector` sobre `net_pressure_series_Pa`.
- `BreakdownDetector` continua adequado para curvas pressao-volume absolutas,
  observadas ou estimadas, mas nao para a serie PKN isolada de pressao liquida.
- `BreakdownReferencedPressure` permanece candidato futuro, nao implementado,
  nao default runtime e bloqueado pela ausencia de `p_net_at_breakdown` /
  `breakdown_step` robustos.

**Caminho futuro registrado:**
- Possivel `PknBreakdownDiagnostics` opt-in, separado do solver e marcado como
  heuristico ate existir pressao absoluta, curva LOT validada, closure stress,
  tensao minima horizontal, pressao de poros ou referencia externa robusta.

**Limite deliberado:**
- Nenhum codigo C++ foi alterado.
- `CMakeLists.txt`, testes, YAMLs, parser, `CaseData`, `PknRunner`,
  `PknModel`, `ResultWriter`, `apps/lot-sim.cpp`, `external/saltcreep/`,
  `legacy/`, `legance/`, baselines e postprocess nao foram alterados.

---

### [2026-06-04] Fase 9.6A — `BreakdownReferencedPressure` candidato futuro — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Documentar `BreakdownReferencedPressure` como metodo candidato
futuro para mapeamento LOT/PKN -> sal, sem implementar codigo runtime.

**Formula conceitual registrada:**

```text
p_wall = p_breakdown + (p_net_current - p_net_at_breakdown)
```

**Classificacao documental:**
- `status: candidate future method`;
- `implementation: not implemented`;
- `runtime default: no`;
- `physical validation: pending`;
- requer `breakdown_pressure_Pa` fisicamente valido e `p_net_at_breakdown` ou
  `breakdown_step` robusto.

**Motivo para nao implementar ainda:**
- `LotConfig.breakdown_pressure_Pa` e parseado de
  `lot.fracture.breakdown.pressure` e hoje funciona como parametro/threshold
  do contrato, nao como serie temporal de pressao absoluta do poco.
- `PknModel` calcula `PknResult.net_pressure_series_Pa` por
  `p_net = E' * w / h`, independente de `breakdown_pressure_Pa` na evolucao da
  serie.
- `PknResult` ainda nao expoe `p_net_at_breakdown`,
  `net_pressure_at_breakdown`, `breakdown_step`, `breakdown_time_s` ou
  `fracture_initiation_step`.
- `cases/lot_tese_migrated/buz67d_pkn.yaml` contem
  `breakdown_pressure_Pa = 1 Pa` como placeholder/R09_PENDING_REVIEW e nao pode
  validar fisicamente esse metodo.

**Documentacao atualizada:**
- `docs/13_coupling_lot_apb_salt.md` recebeu a secao do candidato
  `BreakdownReferencedPressure`, comparacao com `HydrostaticPlusNetPressure`,
  condicao especial do BUZ67D, opcoes futuras e separacao conceitual de APB.
- `docs/02_lot_formulation.md` registra o status atual de
  `breakdown_pressure_Pa` e a ausencia de campos de breakdown em `PknResult`.
- `tools/docs_status.yaml` registra a Fase 9.6A como concluida.

**Limite deliberado:**
- Nenhum codigo C++ foi alterado.
- `CMakeLists.txt`, testes, YAMLs, parser, `CaseData`, `PknRunner`,
  `PknModel`, `ResultWriter`, `apps/lot-sim.cpp`, `external/saltcreep/`,
  `legacy/`, `legance/`, baselines e postprocess nao foram alterados.

---

### [2026-06-04] Fase 9.5A — formulacao fisica de `HydrostaticPlusNetPressure` — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Documentar formalmente as limitacoes fisicas do metodo
`HydrostaticPlusNetPressure` antes de qualquer wiring runtime ou acoplamento
operacional.

**Conclusao documental:**
- `HydrostaticPlusNetPressure` permanece `provisional approximation / opt-in only`.
- A validacao fisica do metodo ainda nao esta concluida.
- O metodo nao deve virar default runtime.
- O uso permitido fica restrito a estudos controlados, testes de cadeia e
  aproximacoes preliminares.

**Motivo fisico:**
- `PknResult.net_pressure_series_Pa` vem de `p_net = E' * w / h`.
- `p_net` e pressao liquida PKN associada a abertura elastica da fratura.
- `p_net` nao carrega explicitamente `sigma_closure`, tensao horizontal minima,
  pressao de poros, tensao radial geostatica ou referencia geomecanica completa.
- `SaltCreepQuery.wall_pressure_Pa` deve representar pressao compressiva
  absoluta na parede do sal ou condicao radial equivalente bem definida.

**Documentacao atualizada:**
- `docs/13_coupling_lot_apb_salt.md` recebeu a classificacao formal do metodo,
  status dos mapeamentos existentes, candidatos futuros e checklist minima antes
  de wiring runtime.
- `docs/02_lot_formulation.md` reforca que `p_net` nao inclui closure stress,
  tensao minima horizontal, pressao de poros ou referencia geomecanica completa.
- `docs/03_apb_formulation.md` registra que APB futuro deve fornecer pressao
  anular absoluta por tempo/profundidade por metodo proprio, separado de
  `HydrostaticPlusNetPressure`.
- `tools/docs_status.yaml` registra a Fase 9.5A como concluida.

**Limite deliberado:**
- Nenhum codigo C++ foi alterado.
- `CMakeLists.txt`, testes, YAMLs, parser, `CaseData`, `PknRunner`,
  `PknModel`, `ResultWriter`, `apps/lot-sim.cpp`, `external/saltcreep/`,
  `legacy/`, `legance/`, baselines e postprocess nao foram alterados.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

---

### [2026-06-04] Fase 9.4B — `LotSaltCouplingConfigBuilder` opt-in — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar um builder opt-in em `coupling/` para montar
`LotSaltCouplingConfig` a partir de `LotSaltHydrostaticContext` ou diretamente
de `CaseData`, sem alterar `evaluate_lot_salt_step()`, CLI, parser, `CaseData`
ou o fluxo `lot-sim run --mode lot-pkn`.

**Mudanca implementada:**
- Criado `include/coupling/LotSaltCouplingConfigBuilder.hpp`.
- Criado `src/coupling/LotSaltCouplingConfigBuilder.cpp`.
- Criado `tests/cpp/test_lot_salt_coupling_config_builder.cpp`.
- `CMakeLists.txt` passou a incluir o novo source e o novo teste no target
  existente.

**Regra implementada:**
- O builder a partir de `LotSaltHydrostaticContext` copia
  `hydrostatic_pressure_Pa` e `depth_m` do contexto.
- `surface_pressure_Pa`, `temperature_K`, `radial_position_m` e
  `pressure_map_method` vêm de `LotSaltCouplingConfigOptions`.
- O default local do builder e `HydrostaticPlusNetPressure`.
- O default global de `LotSaltCouplingConfig` permanece
  `ExperimentalNetPressureProxy`.

**Limite deliberado:**
- `LotSaltCouplingStep` nao foi alterado.
- `LotSaltPressureMap` nao foi alterado.
- `CaseParser`, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter` e
  `apps/lot-sim.cpp` nao foram alterados.
- O builder nao e chamado por `lot-sim` nem por `PknRunner`.
- A fase habilita apenas encadeamento opt-in testavel, nao acoplamento fisico
  completo.

**Testes/builds executados:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou: 146/146.
- `ctest --test-dir build -C Debug --output-on-failure -R "config_builder|ConfigBuilder|hydrostatic|Hydrostatic|pressure_map|lot_salt|coupling|Coupling|units"` passou: 30/30.
- `ctest --test-dir build -C Debug --output-on-failure -R "LOT PKN.*identical"` passou: 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase9_4b_minimal`, `results/phase9_4b_leakoff` e
  `results/phase9_4b_buz67d`.

---

### [2026-06-04] Fase 9.3B — `LotSaltHydrostaticContext` em `coupling/` — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar um helper puro em `coupling/` para derivar
`hydrostatic_pressure_Pa` a partir de `CaseData` ja parseado, sem alterar parser,
runner, YAMLs ou fluxo `lot-sim run --mode lot-pkn`.

**Mudanca implementada:**
- Criado `include/coupling/LotSaltHydrostaticContext.hpp`.
- Criado `src/coupling/LotSaltHydrostaticContext.cpp`.
- Criado `tests/cpp/test_lot_salt_hydrostatic_context.cpp`.
- `CMakeLists.txt` passou a incluir o novo source e o novo teste no target
  existente.

**Regra implementada:**
- Usa `CaseData.lot.shoe_depth_m` como profundidade.
- Seleciona exatamente um `AnnularData` que contem a sapata.
- Seleciona `FluidData` pelo `annular.fluid_id`.
- Calcula `hydrostatic_pressure_Pa` com
  `units::hydrostatic_pressure_Pa(fluid.density_kg_m3, shoe_depth_m)`.

**Limite deliberado:**
- `LotSaltPressureMap` nao foi alterado.
- `LotSaltCouplingStep` nao foi alterado.
- `CaseParser`, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter` e
  `apps/lot-sim.cpp` nao foram alterados.
- O helper nao usa `wellbore`, `surface_pressure_Pa`, `weight_lb_per_gal` ou
  `hydrostatic_depth_profile` nesta fase.
- O helper ainda nao esta conectado automaticamente ao coupling step.
- `lot-sim run --mode lot-pkn` segue desacoplado do sal.

**Testes/builds executados:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou: 139/139.
- `ctest --test-dir build -C Debug --output-on-failure -R "hydrostatic|Hydrostatic|pressure_map|lot_salt|coupling|Coupling|units"` passou: 23/23.
- `ctest --test-dir build -C Debug --output-on-failure -R "LOT PKN.*identical"` passou: 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase9_3b_minimal`, `results/phase9_3b_leakoff` e
  `results/phase9_3b_buz67d`.

---

### [2026-06-04] Fase 9.2B — Utilitarios hidrostaticos puros em `units/` — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Fornecer a base matematica reutilizavel para calcular pressao
hidrostatica sem automatizar ainda o fluxo `YAML -> CaseParser -> CaseData ->
coupling`.

**Mudanca implementada:**
- `include/units/units.hpp` recebeu:
  - `hydrostatic_pressure_Pa(density_kg_m3, depth_m, g)`;
  - `ppg_hydrostatic_pressure_Pa(ppg, depth_m, g)`;
  - `surface_plus_hydrostatic_pressure_Pa(surface_pressure_Pa,
    density_kg_m3, depth_m, g)`.
- As novas funcoes usam validacao robusta e rejeitam NaN, infinito, densidade
  negativa, ppg negativo, profundidade negativa, gravidade nao positiva e
  pressao de superficie negativa.
- `tests/cpp/test_units.cpp` cobre calculo SI, calculo por ppg, superficie +
  hidrostatica, profundidade zero e entradas invalidas.

**Limite deliberado:**
- `LotSaltPressureMap` nao foi alterado.
- `LotSaltCouplingStep` nao foi alterado.
- `CaseParser` e `CaseData` nao foram alterados.
- `HydrostaticPlusNetPressure` continua recebendo `hydrostatic_pressure_Pa`
  pronta.
- `lot-sim run --mode lot-pkn` segue desacoplado do sal.

**Testes/builds executados:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou: 131/131.
- `ctest --test-dir build -C Debug --output-on-failure -R "units|hydrostatic|pressure_map|lot_salt|coupling|Coupling"` passou: 12/12.
- `ctest --test-dir build -C Debug --output-on-failure -R "LOT PKN.*identical"` passou: 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase9_2b_minimal`, `results/phase9_2b_leakoff` e
  `results/phase9_2b_buz67d`.

---

### [2026-06-04] Fase 9.1B — `LotSaltPressureMap` explicito para LOT/PKN -> sal — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Remover o uso direto de `PknResult.net_pressure_series_Pa` como
`SaltCreepQuery.wall_pressure_Pa` dentro de `evaluate_lot_salt_step()`,
mantendo o comportamento default da Fase 9.0 por compatibilidade.

**Mudanca implementada:**
- Criado `include/coupling/LotSaltPressureMap.hpp`.
- Criado `src/coupling/LotSaltPressureMap.cpp`.
- Criado `tests/cpp/test_lot_salt_pressure_map.cpp`.
- `LotSaltCouplingConfig` recebeu `pressure_map_method`,
  `absolute_wellbore_pressure_Pa`, `hydrostatic_pressure_Pa`,
  `surface_pressure_Pa` e `depth_m`.
- `LotSaltCouplingStepResult` passou a expor `pressure_map`.
- `evaluate_lot_salt_step()` monta `LotSaltPressureMapInput`, chama
  `map_lot_pkn_to_salt_wall_pressure()` e usa
  `LotSaltPressureMapResult.wall_pressure_Pa` na query do sal.

**Metodos implementados:**
- `ExperimentalNetPressureProxy`: `wall_pressure_Pa = net_pressure_Pa`,
  `physically_absolute = false`. Default temporario para compatibilidade com
  a Fase 9.0.
- `AbsoluteWellborePressure`: usa `absolute_wellbore_pressure_Pa` e ignora
  `net_pressure_Pa`, com `physically_absolute = true`.
- `HydrostaticPlusNetPressure`: soma `surface_pressure_Pa`,
  `hydrostatic_pressure_Pa` e `net_pressure_Pa`, com
  `physically_absolute = true`. O calculo `rho*g*depth` ainda nao foi integrado
  ao `coupling/`.

**Escopo preservado:**
- Nenhum arquivo em `external/saltcreep/`, `legacy/`, `legance/`,
  `tests/baselines/`, `postprocess/`, `src/lot/`, `include/lot/`,
  `src/apb/`, `include/apb/`, `src/io/`, `include/io/`,
  `PknRunner`, `PknModel`, `CaseParser`, `ResultWriter` ou
  `apps/lot-sim.cpp` foi alterado.
- `lot-sim run --mode lot-pkn` segue desacoplado do sal.

**Testes/builds executados:**
- `cmake --build build --config Debug -j`: OK.
- `ctest --test-dir build -C Debug --output-on-failure`: 127/127 passaram.
- `ctest --test-dir build -C Debug --output-on-failure -R "pressure_map|lot_salt|coupling|Coupling"`:
  8/8 passaram.
- `ctest --test-dir build -C Debug --output-on-failure -R "PressureMap|pressure_map|lot_salt|coupling|Coupling"`:
  12/12 passaram.
- `ctest --test-dir build -C Debug --output-on-failure -R "LOT PKN result is identical"`:
  1/1 passou; filtro ampliado `LOT PKN.*identical` passou 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results\phase9_1b_minimal`, `results\phase9_1b_leakoff` e
  `results\phase9_1b_buz67d`.

---

### [2026-06-04] Fase 9.1A — Formalizacao documental da pressao de parede LOT/PKN/sal — Codex

**Status:** Concluido nesta sessao como fase documental/formulacional.

**Objetivo:** Formalizar o contrato de pressao entre o resultado LOT/PKN e a
interface de sal antes de implementar `LotSaltPressureMap`.

**Conclusao fisica documentada:**
- `PknResult.net_pressure_series_Pa` representa a pressao liquida PKN.
- No modelo PKN minimo, `p_net = E' * w / h`.
- `p_net` e uma pressao relativa de fratura associada a abertura `w` e ao
  modulo plano `E'`; nao e pressao absoluta de poco, pressao anular ou pressao
  fisica de parede do sal.
- `SaltCreepQuery.wall_pressure_Pa` deve representar uma pressao compressiva
  absoluta aplicada na parede do sal, ou uma condicao radial equivalente
  explicitamente definida.

**Contrato preparado para Fase 9.1B:**
- Documentados os metodos candidatos `ExperimentalNetPressureProxy`,
  `AbsoluteWellborePressure` e `HydrostaticPlusNetPressure`.
- Documentados dados disponiveis hoje (`net_pressure_series_Pa`,
  `breakdown_pressure_Pa`, densidade de fluido, campos hidrostaticos quando
  aplicaveis, profundidade da sapata, anulares e gradiente ppg).
- Documentados dados ausentes ou ainda nao integrados: pressao absoluta por
  tempo, pressao de bombeio/superficie por tempo, pressao na sapata por tempo,
  pressao anular APB por tempo, pressao de poros, closure stress, tensao radial
  geostatica, `wellbore` persistido em `CaseData`, estado APB calculado e regra
  explicita para converter PKN em pressao absoluta.
- Proposta API conceitual para `LotSaltPressureMap`.

**Arquivos alterados:**
- `docs/13_coupling_lot_apb_salt.md`
- `docs/02_lot_formulation.md`
- `docs/03_apb_formulation.md`
- `docs/dev-log.md`
- `tools/docs_status.yaml`
- `docs/index.html`

**Escopo preservado:**
- Nenhum codigo C++, CMake, teste, caso YAML, `external/saltcreep/`, `legacy/`,
  `legance/`, baseline ou `postprocess/` foi alterado.
- Nenhum commit ou push foi executado por instrucao da fase.

---

### [2026-06-04 09:21] `c6c5867` — Themisson
**Commit:** `feat(coupling): add experimental salt injection point for LOT/PKN (Fase 9.0)`
**Testes C++:** 20 arquivos | **Testes Python:** 1 arquivos
**Último resultado ctest:** All tests passed (6 assertions in 1 test case)
**Arquivos alterados:**
- `CMakeLists.txt`
- `docs/13_coupling_lot_apb_salt.md`
- `docs/16_saltcreep_governance.md`
- `docs/index.html`
- `include/coupling/LotSaltCouplingStep.hpp`
- `src/coupling/LotSaltCouplingStep.cpp`
- `tests/cpp/test_lot_pkn_salt_coupling_step.cpp`
- `tools/docs_status.yaml`

---

### [2026-06-04] Fase 9.0 — Ponto experimental de injecao em coupling/ — Claude Code

**Status:** Concluido nesta sessao.

**Objetivo:** Criar o primeiro ponto de chamada real de `SaltCreepInterface` a
partir de um resultado LOT/PKN, em caminho experimental separado em `coupling/`,
sem alterar `PknRunner`, `PknModel`, `lot-sim` ou o caminho padrao `lot-pkn`.

**Mudanca implementada:**
- Criado `include/coupling/LotSaltCouplingStep.hpp` com `LotSaltCouplingConfig`,
  `LotSaltCouplingStepResult` e `evaluate_lot_salt_step()`.
- Criado `src/coupling/LotSaltCouplingStep.cpp` com a implementacao que
  constroi `SaltCreepQuery` a partir de `PknResult.time_series_s[step_index]`
  e `net_pressure_series_Pa[step_index]` e chama `salt.evaluate_wall_response()`.
- Criado `tests/cpp/test_lot_pkn_salt_coupling_step.cpp` com 6 testes Catch2.
- `CMakeLists.txt` atualizado para incluir o novo fonte e teste no mesmo commit
  (prevencao do problema `cb61159`).

**Prova central:**
- `SpySaltCreepInterface::call_count() == 1` apos uma chamada a `evaluate_lot_salt_step`.
- `SpySaltCreepInterface::call_count() == 3` apos tres chamadas consecutivas.
- Isso contrasta com a Fase 8.1, onde `call_count() == 0` porque o spy nunca foi injetado.

**Limite deliberado — fisico:**
- `net_pressure_series_Pa[step_index]` e usado como `wall_pressure_Pa` apenas
  como sinal experimental de demonstracao. Ele nao representa a pressao anular
  real de parede no sal. O mapeamento fisico correto (pressao anular/poco ->
  condicao de contorno do sal) fica pendente para fase futura.
- A funcao e feedforward: nao retroalimenta PKN, nao altera `PknResult`.
- APB nao foi conectado ao sal.
- Sem acoplamento fisico completo.

**Limite deliberado — estrutural:**
- `PknRunner`, `PknModel`, `CaseParser`, `ResultWriter` e `apps/lot-sim.cpp`
  nao foram alterados.
- `lot-sim run --mode lot-pkn` produz resultados identicos ao estado anterior.
- Nenhum arquivo em `external/saltcreep/`, `legance/`, `legacy/`, `src/lot/`,
  `include/lot/`, `src/apb/`, `include/apb/`, `src/io/`, `include/io/`,
  `tests/baselines/` ou `postprocess/` foi alterado.

**Testes/builds executados:**
- `cmake --build build --config Debug -j`: OK.
- `ctest --test-dir build -C Debug --output-on-failure`
  Resultado: 118/118 Catch2 passaram (era 112 antes da Fase 9.0).
- `ctest -R "lot_salt|coupling|Coupling|salt_coupling"`: 6/6 novos testes.
- `ctest -R "LOT PKN result is identical"`: 1/1 (Fase 8.1 continua passando).

**Validacao manual CLI:**
- `cases/validation/lot_pkn_minimal.yaml`: `validate` OK, `run` OK.
- `cases/validation/lot_pkn_with_leakoff.yaml`: `validate` OK, `run` OK.
- `cases/lot_tese_migrated/buz67d_pkn.yaml`: `validate` OK, `run` OK.
- Saidas geradas em `results/phase9_minimal`, `results/phase9_leakoff`,
  `results/phase9_buz67d`.

---

### [2026-06-04] Auditoria/sync `external/saltcreep` — APB CSV e diagnostico de tensao — Codex

**Status:** Concluido nesta sessao.

**Objetivo:** Revisar as atualizacoes feitas em `external/saltcreep/`, restaurar
a compatibilidade do build integrado com `include/Eigen`, validar os builds
`build_baseline` e `build_lss_eigen`, e confirmar que o `lot-salt-suite`
continua funcional com as novas fontes vendorizadas.

**Mudanca de integracao aplicada:**
- `external/saltcreep/CMakeLists.txt` preserva novamente a opcao
  `LSS_SALTCREEP_FORCE_LSS_EIGEN`, o proxy `lss_eigen_proxy/Eigen`, a macro
  `LSS_SALTCREEP_EIGEN_MODE` e o teste diagnostico `tests/test_eigen_source.cpp`.
- O build MSVC do saltcreep recebeu `/FS` para evitar disputa de escrita de PDB
  durante builds paralelos.
- O `CMakeLists.txt` raiz passou a compilar as novas dependencias vendorizadas
  `TimeDepthTable.cpp` e `StressSampler.cpp`, necessarias para os campos CSV e
  diagnosticos de tensao do `external/saltcreep`.

**Atualizacoes detectadas no saltcreep:**
- Pressao e temperatura de parede por CSV operacional `t,z`.
- Casos APB 1D/2D com historico de lama e temperatura.
- `StressSampler` e saidas `wall_stress.csv`/`stress_profile.csv`.
- Pos-processamento e benchmark dedicados a pressao de parede.
- Diretorio `external/saltcreep/legacy/` adicionado como referencia interna do
  subprojeto vendorizado.

**Testes/builds executados:**
- `cmake -S external\saltcreep -B external\saltcreep\build_baseline -DCMAKE_BUILD_TYPE=Debug -DLSS_SALTCREEP_FORCE_LSS_EIGEN=OFF`
- `cmake --build external\saltcreep\build_baseline --config Debug -j`
- `ctest --test-dir external\saltcreep\build_baseline -C Debug --output-on-failure -j 4`
  passou 133/133 testes.
- `cmake -S external\saltcreep -B external\saltcreep\build_lss_eigen -DCMAKE_BUILD_TYPE=Debug -DLSS_SALTCREEP_FORCE_LSS_EIGEN=ON`
- `cmake --build external\saltcreep\build_lss_eigen --config Debug -j`
- `ctest --test-dir external\saltcreep\build_lss_eigen -C Debug --output-on-failure -j 4`
  passou 133/133 testes.
- `python -m unittest discover -s external\saltcreep\tests\python -p "test_*.py"`
  passou 31/31 testes, com 7 skips esperados.
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
  passou 112/112 testes.
- `ctest --test-dir build -C Debug --output-on-failure -R "SaltCreep|saltcreep|salt|bridge"`
  passou 59/59 testes.
- `ctest --test-dir build -C Debug --output-on-failure -R "Saltcreep backend"`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `cases/validation/lot_pkn_minimal.yaml` retornou `OK` em `validate` e `run`.
- `cases/validation/lot_pkn_with_leakoff.yaml` retornou `OK` em `validate` e `run`.
- `cases/lot_tese_migrated/buz67d_pkn.yaml` retornou `OK` em `validate` e `run`.
- Os casos saltcreep `apb_1d_constant_mud.yaml`,
  `apb_1d_schedule_mud_temperature.yaml` e `apb_2d_layered_schedule_Q8.yaml`
  executaram com fechamento final finito.

**Escopo preservado:**
- Nenhum arquivo em `legance/`, `legacy/` raiz, `tests/baselines/`,
  modelos LOT/PKN/APB, parser/writer raiz ou modelos fisicos raiz foi alterado.
- As mudancas em `external/saltcreep/` foram tratadas como dependencia
  vendorizada ativa, com build/testes proprios e registro documental.

---

### [2026-06-04 07:06] `aedace9` — Themisson
**Commit:** `docs(audit): record post-commit audit findings for Fases 8.0-8.1`
**Testes C++:** 19 arquivos | **Testes Python:** 1 arquivos
**Último resultado ctest:** All tests passed (176 assertions in 1 test case)
**Arquivos alterados:**
- `docs/index.html`
- `tools/docs_status.yaml`

---

### [2026-06-04] Fase 8.1 — Substitutibilidade LOT/PKN com adapter saltcreep ocioso — Codex

**Status:** Concluido nesta sessao.

**Objetivo:** Provar que a presenca/construcao de `SaltCreepSaltcreepAdapter`
nao altera resultados LOT/PKN enquanto o caminho fisico LOT/PKN ainda nao chama
sal.

**Mudanca implementada:**
- Criado `tests/cpp/test_lot_pkn_salt_adapter_substitutability.cpp`.
- O teste executa `lot_pkn_minimal.yaml` e `lot_pkn_with_leakoff.yaml` em duas
  condicoes: referencia com `NullSaltCreepInterface` presente e adapter real
  construido/disponivel, mas ocioso.
- A comparacao e exata em memoria para `PknResult` e byte a byte para
  `result.json` e `timeseries.csv`.
- Um spy local de `SaltCreepInterface` e o contador `backend_build_count()` do
  adapter confirmam que o sal nao foi chamado pelo fluxo LOT/PKN.

**Resultado de isolamento:**
- `SaltCreepSaltcreepAdapter::backend_build_count() == 0`.
- `SaltCreepAdapterState::step_count() == 0`.
- `SpySaltCreepInterface::call_count() == 0`.
- Resultados LOT/PKN identicos com e sem adapter real presente.

**Limite deliberado:**
- Nao foi criado ponto de injecao em `PknRunner`.
- Nao ha acoplamento LOT-sal, PKN-sal ou APB-sal.
- Nenhum arquivo em `external/saltcreep/`, modelos fisicos, LOT/PKN, APB,
  parser, writer, baselines, `legance/` ou `legacy/` foi alterado.
- Nenhum commit ou push foi executado por instrucao explicita desta fase.

**Testes/builds executados:**
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 112/112 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt|bridge" --output-on-failure`
  passou 59/59 testes.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `cases/validation/lot_pkn_minimal.yaml` retornou `OK` em `validate` e `run`.
- `cases/validation/lot_pkn_with_leakoff.yaml` retornou `OK` em `validate` e `run`.
- `cases/lot_tese_migrated/buz67d_pkn.yaml` retornou `OK` em `validate` e `run`.
- Saidas manuais geradas em:
  `results\lot_pkn_minimal_substitutability_review`,
  `results\lot_pkn_with_leakoff_substitutability_review` e
  `results\buz67d_pkn_substitutability_review`.

---

### [2026-06-04] Auditoria pos-commit — Fases 8.0 e 8.1 — Claude Code

**Status:** Aprovado com ressalva. Correcoes documentais aplicadas.

**HEAD auditado:** `fada793` (test(salt): prove structural LOT PKN isolation with idle adapter)
**Fase 8.0:** `cb61159` (feat(salt): accept dynamic wall pressure in bridge and adapter)

**Estado verificado:**
- Working tree limpo e sincronizado com `origin/main`.
- 112/112 Catch2 passaram. Tres casos LOT/PKN validaram e rodaram.
- Escopo protegido preservado (sem toque em `external/saltcreep/`, `legance/`, `legacy/`,
  `tests/baselines/`, `postprocess/`, `src/lot`, `include/lot`, `src/apb`, `include/apb`,
  `src/io`, `include/io`).

**Filtro ctest correto para os testes da Fase 8.1:**

```bash
ctest --test-dir build -C Debug --output-on-failure -R "LOT PKN result is identical"
```

O filtro `-R "substitutab"` nao encontra os testes porque os nomes dos test cases
comecam com "LOT PKN result is identical with null salt or idle saltcreep adapter".

**Ressalva — commit intermediario `cb61159` nao compila isoladamente:**

O `CMakeLists.txt` do commit `cb61159` (Fase 8.0) referencia:

```text
tests/cpp/test_lot_pkn_salt_adapter_substitutability.cpp
```

antes desse arquivo existir no repositorio. O arquivo foi criado apenas no commit
seguinte, `fada793` (Fase 8.1). Qualquer checkout ou `git bisect` que landing em
exatamente `cb61159` resultaria em falha de build por arquivo ausente.

Nao e possivel corrigir sem reescrever historico publicado (proibido pela politica
do projeto). Mitigacao para `git bisect`:

```bash
git bisect skip cb61159
```

**Correcoes documentais aplicadas nesta entrada:**
- Caminho de `buz67d_pkn.yaml` corrigido para `cases/lot_tese_migrated/buz67d_pkn.yaml`
  na entrada da Fase 8.1.
- `tools/docs_status.yaml`: `last_updated` atualizado para `2026-06-04`.
- `docs/index.html` regenerado.

---

### [2026-06-03] Fase 8.0 — Pressao dinamica no SaltCreepTimeBridge e Adapter — Codex

**Status:** Concluido nesta sessao.

**Objetivo:** Permitir que `SaltCreepTimeBridge` e
`SaltCreepSaltcreepAdapter` aceitem pressao de parede variavel por passo/query
temporal, mantendo o caso de pressao constante como comportamento valido e
mantendo LOT/PKN/APB desacoplados.

**Mudanca implementada:**
- `SaltCreepTimeBridge` ganhou sobrecargas `advance_by(dt_s, wall_pressure_Pa)`
  e `advance_to(target_time_s, wall_pressure_Pa)`.
- A implementacao interna passou a usar um campo de pressao por degrau para que
  o `TimeIntegrator` veja a diferenca entre a pressao do inicio e do fim do
  passo.
- As sobrecargas antigas sem pressao continuam preservadas e usam a pressao
  inicial configurada.
- `SaltCreepSaltcreepAdapter::evaluate_wall_response()` passou a encaminhar
  `query.wall_pressure_Pa` para o bridge, removendo a rejeicao de pressao
  dinamica.
- Criado `tests/cpp/test_salt_creep_time_bridge_dynamic_pressure.cpp`.
- Testes do adapter foram atualizados para cobrir pressao dinamica, tempo
  inicial configurado e rejeicao de pressao dinamica invalida.

**Limite deliberado:**
- A pressao dinamica e aceita apenas no contrato bridge/adapter por query
  temporal; LOT/PKN/APB ainda nao alimentam o adapter automaticamente.
- O bridge continua usando material elastico e campo termico neutro nesta prova.
- Nenhum arquivo em `external/saltcreep/`, modelos fisicos, LOT/PKN, APB,
  parser, writer, baselines, `legance/` ou `legacy/` foi alterado.
- Nenhum commit ou push foi executado por instrucao explicita desta fase.

**Testes/builds executados:**
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 110/110 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt|bridge" --output-on-failure`
  passou 57/57 testes de contrato/adapter/backend/bridge de sal.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_dynamic_pressure_review`.

---

### [2026-06-03] Fase 7.9 — Adapter conectado ao SaltCreepTimeBridge — Codex

**Status:** Concluido nesta sessao.

**Objetivo:** Fazer `SaltCreepSaltcreepAdapter` usar `SaltCreepTimeBridge`
persistente como backend temporal interno, mantendo LOT/PKN/APB desacoplados.

**Mudanca implementada:**
- `SaltCreepSaltcreepAdapter` passou a mapear `SaltCreepAdapterConfig` para
  `SaltCreepTimeBridgeConfig`.
- O `BackendCache` opaco do adapter agora guarda um `SaltCreepTimeBridge`.
- `evaluate_wall_response()` avanca o bridge ate `query.time_s`, converte o
  resultado para `SaltCreepResponse` e registra `SaltCreepAdapterState`.
- O target principal deixou de compilar diretamente os fontes minimos do
  `external/saltcreep`; a rota temporal fica atras de
  `lss_saltcreep_time_bridge`.
- Criado `tests/cpp/test_salt_creep_saltcreep_adapter_time_bridge.cpp`.
- Criado `docs/29_saltcreep_adapter_time_bridge_connection.md`.

**Politica de pressao:** Nesta fase, `query.wall_pressure_Pa` deve ser igual a
`config.wall_pressure.initial_wall_pressure_Pa`. Pressao dinamica e rejeitada
ate o bridge suportar historico/campo temporal de pressao.

**Limite deliberado:**
- O bridge usa material elastico, campo termico neutro e pressao constante.
- LOT/PKN/APB seguem sem instanciar o adapter de sal.
- Nenhum arquivo em `external/saltcreep/`, modelos fisicos, LOT/PKN, APB,
  parser ou writer foi alterado.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 102/102 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt|bridge" --output-on-failure`
  passou 49/49 testes de contrato/adapter/backend/bridge de sal.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_adapter_bridge_review`.

---

### [2026-06-03] Fase 7.8 — Target bridge para TimeIntegrator — Codex

**Status:** Concluido nesta sessao.

**Objetivo:** Criar uma camada C++/CMake intermediaria para compilar e executar
`TimeIntegrator::advance()` sem vazar os headers de I/O do `external/saltcreep`
para os headers publicos ou targets principais do `lot-salt-suite`.

**Classificacao:** `TIME_BRIDGE_CONNECTED`.

**Mudanca implementada:**
- Criado `include/salt/SaltCreepTimeBridge.hpp` com API publica SI limpa.
- Criado `src/salt/SaltCreepTimeBridge.cpp`, unico arquivo do LSS que inclui
  `solver/TimeIntegrator.hpp`.
- Criado target CMake isolado `lss_saltcreep_time_bridge` com include order:
  proxy Eigen, `external/saltcreep/include`, depois `include/`.
- Criado target Catch2 `saltcreep_time_bridge_tests`, sem include publico para
  `external/saltcreep/include`.
- Criado `tests/cpp/test_salt_creep_time_bridge.cpp`.
- Criado `docs/28_saltcreep_time_bridge.md`.

**Limite deliberado:**
- O bridge ainda nao e chamado por `SaltCreepSaltcreepAdapter`.
- LOT/PKN/APB seguem desacoplados do sal temporal.
- Nenhum arquivo em `external/saltcreep/`, modelos fisicos, LOT/PKN, APB,
  parser ou writer foi alterado.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 97/97 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt|Bridge" --output-on-failure`
  passou 44/44 testes de contrato/adapter/backend/bridge de sal.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_time_bridge_review`.

---

### [2026-06-03] Fase 7.7 — Estado temporal persistido sem TimeIntegrator — Codex

**Status:** Concluido nesta sessao.

**Objetivo:** Resolver a fronteira tecnica do `TimeIntegrator` antes de tentar
usa-lo no adapter principal e persistir a rota minima do backend entre queries.

**Classificacao:** `TEMPORAL_STATE_READY_WITHOUT_TIMEINTEGRATOR` para o adapter
principal; `TIMEINTEGRATOR_BLOCKED_BY_INCLUDE_BOUNDARY` para a tentativa de
trazer `TimeIntegrator` ao target `lot-sim`/`lot_sim_tests`.

**Mudanca implementada:**
- Criado `docs/audits/saltcreep_timeintegrator_include_boundary.md`.
- Criado `docs/27_saltcreep_adapter_temporal_state.md`.
- `SaltCreepSaltcreepAdapter` passou a ter cache privado e opaco para
  elemento, material, malha, matriz de rigidez, vetor geostatico e graus fixos.
- `evaluate_wall_response()` continua montando somente a pressao de parede da
  query e registrando resposta em `SaltCreepAdapterState`.
- Criado `tests/cpp/test_salt_creep_saltcreep_adapter_temporal_state.cpp`.

**Limite deliberado:**
- `TimeIntegrator` nao foi conectado ao adapter principal porque
  `external/saltcreep/include/solver/TimeIntegrator.hpp` inclui
  `io/CaseParser.hpp`, nome que tambem existe em `include/io/CaseParser.hpp`.
- Nenhum arquivo em `external/saltcreep/`, LOT/PKN, APB ou modelos fisicos foi
  alterado.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 91/91 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt" --output-on-failure`
  passou 38/38 testes de contrato/adapter/backend de sal.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_adapter_temporal_state`.

---

### [2026-06-03] Revisão 7.6 — patch documental radial_strain — Claude Code

**Status:** Patch aplicado.

**Achado:** `radial_strain = u_r / r_i` é tecnicamente `ε_θ` (hoop strain),
não `ε_r` (radial strain). O sinal está correto para o contrato de dados, mas
a nomenclatura pode confundir em fases futuras com fluência real.

**Patch:** adicionada nota explicativa em
`docs/26_saltcreep_adapter_backend_minimum.md` clarificando a aproximação usada
e quando ela deve ser revisada.

**Verificações:** 88/88 Catch2 passaram. 3 validates LOT/PKN: OK.

---

### [2026-06-03] Fase 7.6 — Backend minimo do adapter saltcreep — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Conectar `SaltCreepSaltcreepAdapter::evaluate_wall_response()` a
uma rota real minima do backend `external/saltcreep`, mantendo LOT/PKN/APB
desacoplados do sal.

**Mudanca implementada:**
- `SaltCreepSaltcreepAdapter::is_available()` passa a retornar `true` para
  configuracoes suportadas pelo backend minimo.
- `state_` passa a ser `mutable` por constancia logica, permitindo registrar
  respostas em `evaluate_wall_response() const`.
- `evaluate_wall_response()` monta e executa uma rota elastica/geostatica com
  `build_mesh_L3`, `AxisymL3`, `ElasticIsotropic`, `Assembler`,
  `ConstantWallPressureField` e `ElasticSolver`.
- Criado `tests/cpp/test_salt_creep_saltcreep_adapter_backend.cpp`.
- Criado `docs/26_saltcreep_adapter_backend_minimum.md`.

**Limite deliberado:**
- `TimeIntegrator` permanece nos targets Catch2 controlados separados nesta
  fase. Ele nao foi linkado ao target principal para evitar conflito de include
  entre `external/saltcreep/include/io/CaseParser.hpp` e
  `include/io/CaseParser.hpp`.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 88/88 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt" --output-on-failure`
  passou 35/35 testes de contrato/adapter de sal.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_adapter_backend_review`.

**Verificacao de desacoplamento:**
- Busca em `src/lot`, `include/lot`, `apps/lot-sim.cpp`, `src/io` e
  `include/io` nao encontrou instanciacao de `SaltCreepSaltcreepAdapter` nem
  uso de `SaltCreepInterface` no caminho LOT/PKN.

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter`, `CaseParser`,
  `src/lot/`, `include/lot/`, APB e modelos fisicos sem alteracao.
- Nenhum script Python novo e nenhum acoplamento LOT/sal implementado.

---

### [2026-06-03] Fase 7.5 — Configuracao e state machine do adapter saltcreep — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Adicionar `SaltCreepAdapterConfig` e `SaltCreepAdapterState` para
preparar o futuro adapter real do `external/saltcreep`, mantendo o backend
desligado, `is_available() = false` e sem acoplar LOT/PKN/APB ao sal.

**Mudanca implementada:**
- Criados `include/salt/SaltCreepAdapterConfig.hpp` e
  `src/salt/SaltCreepAdapterConfig.cpp`.
- Criados `include/salt/SaltCreepAdapterState.hpp` e
  `src/salt/SaltCreepAdapterState.cpp`.
- `SaltCreepSaltcreepAdapter` agora aceita configuracao SI validada, inicializa
  estado local e expoe `config()` / `state()`.
- `evaluate_wall_response()` permanece neutro e nao chama o backend real.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 82/82 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt" --output-on-failure`
  passou 29/29 testes de contrato/adapter de sal.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_salt_adapter_config_state`.

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter`, `CaseParser`,
  `src/lot/`, `include/lot/`, APB e modelos fisicos sem alteracao.
- Nenhum script Python novo e nenhum acoplamento LOT/sal implementado.

---

### [2026-06-03] Fase 7.4 — Tempo, geostatica e termico neutro no backend saltcreep — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Evoluir o caso controlado do backend `external/saltcreep` para
exercitar tempo, campo termico constante neutro, geostatica simplificada e
pressao de parede constante, sem ligar o backend ao adapter real e sem acoplar
LOT/PKN/APB ao sal.

**Auditoria:**
- Criado `docs/audits/saltcreep_backend_time_geostatic_case.md`.
- Classificacao: `TIME_THERMAL_GEOSTATIC_CONTROLLED_TEST_READY`.
- Achado: `TimeIntegrator` aceita `ThermalField`, vetor geostatico por ponto de
  Gauss, `WallPressureField` opcional e passos `advance(dt_s)`.

**Mudanca implementada:**
- Criado `tests/cpp/test_saltcreep_backend_time_geostatic_case.cpp`.
- `CMakeLists.txt` adiciona target separado
  `saltcreep_backend_time_geostatic_tests`.
- O teste usa `ElasticIsotropic`, `ProfileField::make_constant()` com
  `alpha_thermal = 0`, `ConstantWallPressureField`, geostatica explicita e
  `TimeIntegrator::advance()`.

**Resultado tecnico:**
- Caso neutro: dois passos temporais preservam a resposta elastica estatica
  contra `ElasticSolver`.
- Caso geostatico: compressao uniforme simplificada com parede externa fixa
  produz `u_r < 0`, fechamento positivo e `wall_closure_pct() > 0`.
- Nenhum output versionado e gerado pelo teste.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 68/68 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.

**Escopo alterado:**
- `CMakeLists.txt`
- `tests/cpp/test_saltcreep_backend_time_geostatic_case.cpp`
- `docs/audits/saltcreep_backend_time_geostatic_case.md`
- `docs/audits/saltcreep_backend_controlled_case.md`
- `docs/audits/saltcreep_radial_displacement_sign_audit.md`
- `docs/24_saltcreep_adapter_design.md`
- `docs/13_coupling_lot_apb_salt.md`
- `docs/16_saltcreep_governance.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/dev-log.md`
- `tools/docs_status.yaml`
- `docs/index.html`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `SaltCreepSaltcreepAdapter::is_available()` permanece `false`.
- `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter`, `CaseParser`,
  `src/lot/`, `include/lot/`, APB e modelos fisicos sem alteracao.
- Nenhum script Python novo e nenhum acoplamento LOT/sal implementado.

---

### [2026-06-03] Fase 7.3 — Caso C++ controlado do backend saltcreep — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Provar uma rota C++ direta e isolada para instanciar o nucleo do
`external/saltcreep` em um caso elastico sintetico, sem conectar o backend ao
`SaltCreepSaltcreepAdapter` real e sem acoplar LOT/PKN ao sal.

**Mudanca implementada:**
- Criado `tests/cpp/test_saltcreep_backend_controlled_case.cpp`.
- `CMakeLists.txt` adiciona o target separado
  `saltcreep_backend_controlled_tests`, que compila somente fontes minimas do
  backend para o caso de Lame.
- O target usa um proxy de Eigen no build dir, copiado de `include/Eigen/`,
  antes de `external/saltcreep/include`, preservando o Eigen oficial do projeto
  sem alterar as copias versionadas.
- Criado `docs/audits/saltcreep_backend_controlled_case.md`.

**Resultado tecnico:**
- Pressao interna positiva aplicada via `ConstantWallPressureField` produz
  deslocamento radial de parede para fora (`u_r > 0`) e fechamento nulo.
- Pressao externa/confinante positiva produz deslocamento para dentro
  (`u_r < 0`) e fechamento positivo `max(0, -u_r)`.
- Ambos os casos batem a solucao analitica de Lame no raio interno com erro
  relativo menor que `1e-6`.
- Hipoteses do caso: elasticidade linear, pequenas deformacoes, sem fluencia,
  sem dano, sem acoplamento termico e geometria sintetica.
- Conclusao: a API C++ direta do backend e viavel para caso elastico controlado,
  mas o adapter real ainda exige configuracao completa de malha, material,
  temperatura, geostatica, pressoes e integrador.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 66/66 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.

**Escopo alterado:**
- `CMakeLists.txt`
- `tests/cpp/test_saltcreep_backend_controlled_case.cpp`
- `docs/audits/saltcreep_backend_controlled_case.md`
- `docs/audits/saltcreep_radial_displacement_sign_audit.md`
- `docs/24_saltcreep_adapter_design.md`
- `docs/13_coupling_lot_apb_salt.md`
- `docs/16_saltcreep_governance.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/dev-log.md`
- `tools/docs_status.yaml`
- `docs/index.html`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `SaltCreepSaltcreepAdapter::is_available()` permanece `false`.
- `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter`, `CaseParser`,
  `src/lot/`, `include/lot/`, APB e modelos fisicos sem alteracao.
- Nenhum script Python novo e nenhum acoplamento LOT/sal implementado.

---

### [2026-06-03] Fase 7.2 — SaltCreepSaltcreepAdapter experimental e isolado — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Criar o primeiro adapter C++ concreto para preparar a integracao
com `external/saltcreep`, mantendo LOT/PKN, APB e o backend de sal sem
acoplamento fisico nesta fase.

**Auditoria de sinal radial:**
- Criado `docs/audits/saltcreep_radial_displacement_sign_audit.md`.
- Resultado: `SIGN_CONFIRMED_FOR_WALL_DISPLACEMENT_OUTPUT`.
- Evidencias auditadas: `wall_displacement_m()` retorna `state_.u_total[0]`,
  `wall_closure_pct()` calcula `-u_r/Ri*100`, `TimeOutput.cpp` grava
  `wall_disp_m` assinado e `u_wall_m` positivo, e testes do saltcreep exigem
  `wall_displacement_m() < 0` para fechamento.

**Mudanca implementada:**
- `include/salt/SaltCreepSaltcreepAdapter.hpp` define o adapter experimental.
- `src/salt/SaltCreepSaltcreepAdapter.cpp` implementa validacao de query,
  `is_available() = false`, resposta neutra valida e
  `radial_closure_from_displacement()`.
- `tests/cpp/test_salt_creep_saltcreep_adapter.cpp` cobre compilacao,
  disponibilidade documentada, resposta neutra, rejeicoes de query invalida e
  convencao `radial_closure_m = max(0, -radial_displacement_m)`.
- O backend real nao foi conectado porque ainda nao ha API simples do tipo
  "avaliar resposta de parede"; a execucao real exige malha, elemento,
  material, temperatura, geostatica, pressao de parede e integrador.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 64/64 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_salt_adapter_review`.

**Escopo alterado:**
- `CMakeLists.txt`
- `include/salt/SaltCreepSaltcreepAdapter.hpp`
- `src/salt/SaltCreepSaltcreepAdapter.cpp`
- `tests/cpp/test_salt_creep_saltcreep_adapter.cpp`
- `docs/audits/saltcreep_radial_displacement_sign_audit.md`
- `docs/24_saltcreep_adapter_design.md`
- `docs/13_coupling_lot_apb_salt.md`
- `docs/16_saltcreep_governance.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/22_saltcreep_interface_contract.md`
- `docs/23_lot_salt_sign_convention.md`
- `docs/dev-log.md`
- `tools/docs_status.yaml`
- `docs/index.html`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter`, `CaseParser`,
  `src/lot/`, `include/lot/`, `src/io/` e `include/io/` sem alteracao.
- Nenhum script Python novo, nenhum adapter real, nenhuma chamada ao saltcreep e
  nenhum acoplamento LOT/sal implementado.

---

### [2026-06-03] Revisão 7.1 — patch mínimo radial_closure_m — Claude Code

**Status:** Patch aplicado e commitado.

**Achado:** `NullSaltCreepInterface::evaluate_wall_response` em `src/salt/SaltCreepInterface.cpp`
atribuía explicitamente `radial_displacement_m`, `radial_strain` e
`effective_closure_pressure_Pa`, mas omitia `radial_closure_m`. O campo estava
correto via default do struct, mas a omissão era inconsistente e potencialmente
confusa para futuros leitores e adapters.

**Patch:** adicionada linha `response.radial_closure_m = 0.0;` para tornar a
implementação self-documenting, consistente com todos os outros campos.

**Verificações:**
- 57/57 Catch2 passaram após o patch.
- 3 validates LOT/PKN: OK.
- `external/saltcreep/`, `legance/`, `legacy/`, `PknModel`, `PknRunner`,
  `LeakoffModel`, `ResultWriter`, `CaseParser` e baselines intocados.

---

### [2026-06-03] Fase 7.1 — Convencao de sinais LOT-saltcreep — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Fixar o contrato de sinais, unidades e fronteira de dados entre
LOT/PKN e um futuro adapter para `external/saltcreep`, sem acoplamento fisico e
sem alterar solver/modelos.

**Mudanca implementada:**
- `SaltCreepResponse` passa a expor `radial_closure_m` como magnitude positiva
  de fechamento.
- O contrato LOT-sal define `wall_pressure_Pa >= 0` como pressao compressiva
  positiva.
- `radial_displacement_m` e deslocamento radial assinado: positivo para fora e
  negativo para dentro.
- `radial_closure_m = max(0, -radial_displacement_m)`.
- `radial_strain` segue o sinal do deslocamento radial.
- `effective_closure_pressure_Pa >= 0` permanece compressivo positivo.
- `docs/23_lot_salt_sign_convention.md` criado como referencia central.

**Testes/builds executados:**
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 57/57 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.

**Escopo alterado:**
- `include/salt/SaltCreepTypes.hpp`
- `tests/cpp/test_salt_creep_interface.cpp`
- `docs/08_known_issues.md`
- `docs/13_coupling_lot_apb_salt.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/22_saltcreep_interface_contract.md`
- `docs/23_lot_salt_sign_convention.md`
- `docs/dev-log.md`
- `tools/docs_status.yaml`
- `docs/index.html`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `PknModel`, `LeakoffModel`, `PknRunner`, `ResultWriter`, `CaseParser`,
  `src/lot/` e `include/lot/` sem alteracao.
- Nenhum adapter real, chamada ao saltcreep ou acoplamento LOT/sal implementado.

---

### [2026-06-03] Fase 7.0 — SaltCreepInterface C++ minima e nao acoplada — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Criar uma fronteira C++ minima, testavel e estavel para futura
integracao LOT/APB/sal, sem acoplar `PknModel` ao sal e sem chamar
`external/saltcreep`.

**Mudanca implementada:**
- `include/salt/SaltCreepTypes.hpp` define `WallPressureSample`,
  `SaltCreepQuery` e `SaltCreepResponse` em SI.
- `include/salt/SaltCreepInterface.hpp` define a interface abstrata e
  `NullSaltCreepInterface`.
- `src/salt/SaltCreepInterface.cpp` valida entradas finitas e rejeita tempo,
  pressao, temperatura e posicao radial invalidos.
- `NullSaltCreepInterface` retorna `is_available() = false` e resposta neutra
  valida (`u_r = 0`, `strain = 0`, `effective_closure_pressure_Pa = 0`,
  `valid = true`) para query valida.
- `tests/cpp/test_salt_creep_interface.cpp` adiciona 9 testes Catch2 do
  contrato.

**Testes/builds executados:**
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 56/56 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`; fallback WDAC `OFF` nao foi necessario.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_salt_interface_review`.

**Escopo alterado:**
- `include/salt/SaltCreepTypes.hpp`
- `include/salt/SaltCreepInterface.hpp`
- `src/salt/SaltCreepInterface.cpp`
- `tests/cpp/test_salt_creep_interface.cpp`
- `docs/22_saltcreep_interface_contract.md`
- `CMakeLists.txt`
- `docs/07_target_architecture.md`
- `docs/13_coupling_lot_apb_salt.md`
- `docs/16_saltcreep_governance.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/dev-log.md`
- `tools/docs_status.yaml`
- `docs/index.html`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `PknModel`, `LeakoffModel`, `PknRunner`, `ResultWriter`, `CaseParser` e APB
  sem alteracao.
- Nenhum script Python novo e nenhum acoplamento fisico implementado.

---

### [2026-06-03] docs — permissões operacionais Claude Code — Claude Code

**Status:** Concluído.

**Objetivo:** Codificar política permanente de autorização operacional para reduzir
confirmações desnecessárias durante desenvolvimento, sem relaxar restrições de segurança.

**Arquivos alterados:**
- `CLAUDE.md` — nova seção "Autorização operacional — Claude Code" com tabelas allow/confirm
- `AGENTS.md` — nova seção compacta "Autorização operacional — Claude Code / Codex"
- `docs/14_developer_workflow.md` — nova seção "Claude Code operational permissions"
- `.claude/settings.json` — `git push` movido de deny para allow; `git push --force` permanece em deny; adicionados paths `build/Debug/lot-sim.exe`, `Release`, `RelWithDebInfo`
- `docs/dev-log.md` — esta entrada
- `docs/index.html` — regenerado

**Nenhum código C++, CMake, solver ou arquivo de teste foi alterado.**

---

### [2026-06-03] Fase 6.12B — CLI subprocess tests opcionais para Windows WDAC — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Permitir que ambientes Windows com WDAC/Smart App Control bloqueando
binarios nao assinados executem toda a suite Catch2 sem os dois testes que spawnam
`lot-sim.exe` como subprocesso, mantendo o padrao `ON` para CI e maquinas normais.

**Mudanca implementada:**
- `CMakeLists.txt` adiciona `option(LSS_ENABLE_CLI_SUBPROCESS_TESTS ... ON)`.
- `lot_sim_tests` recebe `LSS_ENABLE_CLI_SUBPROCESS_TESTS=1` quando a opcao esta `ON`
  e `=0` quando esta `OFF`.
- `tests/cpp/test_pkn_runner.cpp` compila os dois testes `CLI run succeeds...` somente
  quando a macro esta ativa; no modo `OFF`, registra um teste sentinela
  `CLI subprocess tests disabled by CMake option`.
- `docs/14_developer_workflow.md` documenta o fluxo Windows WDAC/Smart App Control com
  `-DLSS_ENABLE_CLI_SUBPROCESS_TESTS=OFF` e validacao manual de CLI.

**Testes/builds executados:**
- Modo padrao `ON`: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`,
  `cmake --build build --config Debug -j`, `ctest --test-dir build -C Debug --output-on-failure`.
  Resultado: 47/47 Catch2 passaram nesta execucao.
- Modo `OFF`: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug -DLSS_ENABLE_CLI_SUBPROCESS_TESTS=OFF`,
  `cmake --build build --config Debug -j`, `ctest --test-dir build -C Debug --output-on-failure`.
  Resultado: 46/46 Catch2 passaram; os dois testes de subprocesso foram substituidos por
  um teste sentinela.
- Validates manuais: `lot_pkn_minimal.yaml`, `lot_pkn_with_leakoff.yaml` e
  `buz67d_pkn.yaml` retornaram `OK`.
- Run manual: `lot_pkn_minimal.yaml --mode lot-pkn` gerou `result.json` e
  `timeseries.csv` em `results\lot_pkn_minimal_wdac_manual`.

**Escopo alterado:**
- `CMakeLists.txt`
- `tests/cpp/test_pkn_runner.cpp`
- `docs/14_developer_workflow.md`
- `docs/dev-log.md`
- `docs/index.html`
- `tools/docs_status.yaml`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/` e `tests/baselines/` preservados.
- Modelos fisicos, `PknModel`, `LeakoffModel`, `PknRunner`, `ResultWriter` e
  `CaseParser` sem alteracao.

---

### [2026-06-02] Fase 6.12 — Compatibilidade Windows Visual Studio / CMake 4 — Claude Code
**Status:** Concluido nesta sessao.

**Objetivo:** Corrigir dois problemas ao buildar em nova maquina Windows com VS2026 e CMake 4.3:
1. yaml-cpp via FetchContent falhava com CMake 4 (`Compatibility with CMake < 3.5 has been removed`)
2. Testes CLI em `test_pkn_runner.cpp` procuravam `build/lot-sim.exe` mas VS usa `build/Debug/lot-sim.exe`

**Mudancas implementadas:**

**1. CMakeLists.txt — compatibilidade CMake 4:**
- Adicionado `set(CMAKE_POLICY_VERSION_MINIMUM 3.5 ...)` antes de `FetchContent_MakeAvailable(yaml-cpp)`.
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug` agora funciona sem flag manual em CMake 4.

**2. CMakeLists.txt — path do executavel via generator expression:**
- `target_compile_definitions(lot_sim_tests PRIVATE LSS_LOT_SIM_EXECUTABLE="$<TARGET_FILE:lot-sim>")` no target `lot_sim_tests`.
- Resolve para caminho absoluto correto em qualquer gerador (single-config e multi-config).

**3. CMakeLists.txt — catch_discover_tests em modo PRE_TEST:**
- `DISCOVERY_MODE PRE_TEST` evita erro `unknown error` no post-build step do MSBuild.
- Descuberta de testes adiada para o momento em que `ctest` e invocado.

**4. tests/cpp/test_pkn_runner.cpp — funcao lot_sim_executable() robusta:**
- Usa `LSS_LOT_SIM_EXECUTABLE` (definido pelo CMake via generator expression).
- Fallback: probe Debug/Release/RelWithDebInfo/MinSizeRel e raiz `build/`.

**Resultados:**
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`: OK sem flag manual
- `cmake --build build --config Debug -j`: OK, `build\Debug\lot-sim.exe` e `build\Debug\lot_sim_tests.exe`
- `ctest --test-dir build -C Debug --output-on-failure`: **45/47 passaram**
- 2 testes CLI falharam exclusivamente por WDAC enforcement mode nesta maquina
  (`UsermodeCodeIntegrityPolicyEnforcementStatus = 2`). O path para `lot-sim.exe` esta correto;
  o kernel bloqueia CreateProcess para binarios nao assinados.
  Workaround: desabilitar Smart App Control ou assinar os binarios.
  Ver `docs/14_developer_workflow.md` — secao "Windows / Visual Studio / CMake 4".

**Escopo alterado:**
- `CMakeLists.txt` — tres patches: CMAKE_POLICY_VERSION_MINIMUM, LSS_LOT_SIM_EXECUTABLE, DISCOVERY_MODE PRE_TEST
- `tests/cpp/test_pkn_runner.cpp` — lot_sim_executable() robusto com fallback multi-config
- `docs/14_developer_workflow.md` — secao "Windows / Visual Studio / CMake 4 notes"
- `docs/dev-log.md`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/` — preservados
- `include/Eigen/` — preservado
- Modelos fisicos, PknModel, LeakoffModel, PknRunner, CaseParser, ResultWriter — sem alteracao
- Baselines — preservados

---

### [2026-06-01 21:51] `eac8fac` — Themisson
**Commit:** `feat(saltcreep): migrate to lss Eigen by default via auto-detection (Fase 6.11)`
**Testes C++:** 7 arquivos | **Testes Python:** 1 arquivos
**Último resultado ctest:** nenhum (módulos ainda não implementados)
**Arquivos alterados:**
- `docs/13_coupling_lot_apb_salt.md`
- `docs/16_saltcreep_governance.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/20_saltcreep_eigen_migration_plan.md`
- `docs/21_saltcreep_eigen_migration_result.md`
- `docs/index.html`
- `tools/docs_status.yaml`

**⚠ Modificações em external/saltcreep/:**
- `external/saltcreep/CMakeLists.txt`
> Atualizar a seção 'Modificações em andamento no saltcreep' abaixo.

---

### [2026-06-01] Fase 6.11 — Migracao controlada Eigen oficial no saltcreep — Claude Code
**Status:** Concluido nesta sessao.
**Decisao:** `MIGRATION_COMPLETED`

**Objetivo:** Tornar `include/Eigen` o Eigen ativo do saltcreep por padrao no contexto do
`lot-salt-suite`, sem flags manuais, preservando `external/saltcreep/include/Eigen` como fallback.

**Mudanca implementada:**
- `external/saltcreep/CMakeLists.txt` agora auto-detecta o contexto `lot-salt-suite` verificando
  se `../../include/Eigen` existe. Se sim, `LSS_SALTCREEP_FORCE_LSS_EIGEN` default = `ON`.
- Fora da arvore do projeto (standalone), o default e `OFF` (Eigen interno — sem quebra).
- Mensagem de fallback atualizada: `Saltcreep Eigen mode: internal fallback`.

**Tres provas objetivas (build migrado sem flag manual):**
1. CMake configure: `Saltcreep Eigen mode: lot-salt-suite include/Eigen (proxy at ...)`
2. `tests_unit.vcxproj` `AdditionalIncludeDirectories`: `lss_eigen_proxy` PRIMEIRO
3. Macro runtime `test_eigen_source`: `LSS_SALTCREEP_EIGEN_MODE = lss`

**Testes/builds executados:**
- Build migrado (auto-detect ON, sem flag): 126/126 Catch2 passaram
- Caso APB `mud_gradient_1d_8p5ppg.yaml`: `closure=0.300817%` (identico ao baseline)
- lot-salt-suite: 47/47 Catch2, validates OK (3 casos), run lot-pkn OK

**Escopo alterado:**
- `external/saltcreep/CMakeLists.txt` — auto-deteccao de contexto, default ON dentro de lot-salt-suite
- `docs/20_saltcreep_eigen_migration_plan.md` — decisao `MIGRATION_COMPLETED`, opcao D
- `docs/16_saltcreep_governance.md` — politica Eigen atualizada
- `docs/13_coupling_lot_apb_salt.md` — nota de dependencia Eigen atualizada
- `docs/17_lot_pkn_roadmap.md` — Fase 6.11 registrada
- `docs/21_saltcreep_eigen_migration_result.md` — criado com resultado completo
- `docs/dev-log.md`, `tools/docs_status.yaml`

**Nao alterado:**
- `external/saltcreep/include/Eigen/` — preservado
- `include/Eigen/` — preservado
- `legance/`, `legacy/`, `tests/baselines/` — preservados
- Modelos fisicos, casos e resultados do saltcreep — preservados
- `PknModel`, `LeakoffModel`, `PknRunner`, `ResultWriter`, `CaseParser` — sem alteracao

---

### [2026-06-01] Fase 6.10B — Prova forcada Eigen oficial no saltcreep — Claude Code
**Status:** Concluido nesta sessao.
**Decisao:** `PROVEN_SAFE_TO_MIGRATE`

**Problema resolvido:** A Fase 6.10 usou `CMAKE_CXX_FLAGS=-I...` para adicionar `include/` ao
build experimental do saltcreep, mas o gerador Visual Studio listava `external/saltcreep/include`
ANTES do include forcado no `AdditionalIncludeDirectories` do `.vcxproj`. Portanto a Fase 6.10
nao provou que o saltcreep usou de fato `include/Eigen`.

**Solucao implementada:**
- `external/saltcreep/CMakeLists.txt` recebeu `option(LSS_SALTCREEP_FORCE_LSS_EIGEN ... OFF)`.
- Quando `ON`: o CMake cria `${CMAKE_BINARY_DIR}/lss_eigen_proxy/` com apenas `Eigen/` (copiado
  de `include/Eigen/`) e o adiciona com `BEFORE PRIVATE` antes de `PRIVATE include`.
- Isso garante que `<Eigen/Core>` resolva para o proxy (LSS Eigen) primeiro, sem conflitar com
  headers relativos do saltcreep como `"io/CaseParser.hpp"`.
- `external/saltcreep/tests/test_eigen_source.cpp` confirma o modo em runtime via macro
  `LSS_SALTCREEP_EIGEN_MODE` setada pelo CMake.

**Tres provas objetivas:**
1. CMake configure: `Saltcreep Eigen mode: lot-salt-suite include/Eigen (proxy at ...)`
2. `tests_unit.vcxproj` `AdditionalIncludeDirectories`: `lss_eigen_proxy` PRIMEIRO, `saltcreep/include` SEGUNDO
3. Macro runtime `test_eigen_source`: baseline→`internal`, forcado→`lss`

**Testes/builds executados:**
- Baseline (`OFF`): 126/126 Catch2 passaram em 996.27 s
- Forcado (`ON`): 126/126 Catch2 passaram em 1024.06 s
- Caso APB `mud_gradient_1d_8p5ppg.yaml`: baseline `closure=0.300817%`, forcado `closure=0.300817%`
- lot-salt-suite: 47/47 Catch2, validates OK, run lot-pkn OK

**Escopo alterado:**
- `external/saltcreep/CMakeLists.txt` — opcao + proxy dir + BEFORE PRIVATE + macro
- `external/saltcreep/tests/test_eigen_source.cpp` — criado (diagnostico)
- `docs/audits/saltcreep_eigen_compatibility_audit.md` — Fase 6.10B documentada
- `docs/20_saltcreep_eigen_migration_plan.md` — decisao `PROVEN_SAFE_TO_MIGRATE`
- `docs/16_saltcreep_governance.md`, `docs/13_coupling_lot_apb_salt.md`, `docs/17_lot_pkn_roadmap.md`
- `docs/dev-log.md`, `tools/docs_status.yaml`
- `.claude/settings.json` — permissao granular para `external/saltcreep/CMakeLists.txt`

**Nao alterado:**
- `external/saltcreep/include/Eigen/` — preservado
- `include/Eigen/` — preservado
- `legance/`, `legacy/`, `tests/baselines/` — preservados
- Modelos fisicos, casos e resultados do saltcreep — preservados

---

### [2026-06-01] Fase 6.10 — Auditoria Eigen do saltcreep — Codex
**Status:** Concluido nesta sessao.
**Testes/comandos saltcreep:** `cmake -S external/saltcreep -B external/saltcreep/build_baseline -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`, `cmake --build external/saltcreep/build_baseline -j`, `ctest --test-dir external/saltcreep/build_baseline --output-on-failure -j 4`, build experimental em `external/saltcreep/build_lss_eigen` com `include/Eigen` no include path, e `ctest` equivalente.
**Resultado saltcreep:** baseline 125/125 testes passaram em 1028.24 s; build experimental 125/125 testes passaram em 1020.63 s.
**Casos saltcreep executados:** `external/saltcreep/cases/tcc/lame_test.yaml` e `external/saltcreep/cases/apb/mud_gradient_1d_8p5ppg.yaml` nos dois builds. O caso APB reportou `closure=0.300817%` em ambos.
**Testes/comandos lot-salt-suite:** `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build -j`, `ctest --test-dir build --output-on-failure`, `lot-sim validate --case` para `lot_pkn_minimal.yaml` e `lot_pkn_with_leakoff.yaml`, e `lot-sim run --mode lot-pkn` para `lot_pkn_minimal.yaml`.
**Resultado lot-salt-suite:** 47/47 testes Catch2 passaram; validates retornaram `OK`; run gerou `result.json` e `timeseries.csv` em `results\lot_pkn_minimal_saltcreep_eigen_review`.
**Escopo:** nenhum arquivo em `external/saltcreep/`, `legance/`, `legacy/`, `tests/baselines/` ou `include/Eigen/` foi removido ou alterado.

**Conclusao:**
- O `saltcreep` permanece compativel com a copia Eigen vendorizada.
- O build experimental tolera `include/Eigen` no include path, mas o Visual Studio ainda coloca `external/saltcreep/include` antes de `include/`.
- A migracao real para `include/Eigen` deve ser opcao CMake futura, nao mudanca implicita.

**Documentos criados/alterados:**
- `docs/audits/saltcreep_eigen_compatibility_audit.md`.
- `docs/20_saltcreep_eigen_migration_plan.md`.
- `docs/16_saltcreep_governance.md`, `docs/13_coupling_lot_apb_salt.md`, `docs/17_lot_pkn_roadmap.md`.

---

### [2026-06-01] Revisao commit 9048683 — LeakoffModel e Eigen/CMake — Codex
**Status:** Aprovado com ressalvas corrigidas nesta sessao.
**Commit revisado:** `9048683 feat(lot): add structured leakoff model`.
**Testes/comandos:** `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build -j`, `ctest --test-dir build --output-on-failure`, `lot-sim validate --case` para os tres contratos LOT/PKN e `lot-sim run --mode lot-pkn` para os dois casos modernos de validacao.
**Resultado:** 47/47 testes Catch2 passaram; validates e runs retornaram `OK` e geraram `result.json`/`timeseries.csv` em `results\lot_pkn_minimal_leakoff_review` e `results\lot_pkn_with_leakoff_review`.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/`, `tests/baselines/` ou `postprocess/scripts/` foi alterado.

**Patches de revisao:**
- `CMakeLists.txt` agora formaliza `lss_eigen`/`lss::eigen` apontando para `include/Eigen`, sem adicionar `external/saltcreep/include` aos targets modernos.
- `AGENTS.md`, `CLAUDE.md`, `include/AGENTS.md` e `docs/16_saltcreep_governance.md` documentam que `include/Eigen` e o Eigen oficial do `lot-salt-suite` e que a copia do saltcreep deve ficar preservada.
- `PknModel` passa a rejeitar tambem `input.leakoff.coefficient_m_sqrt_s` e `input.leakoff.constant_rate_m3_s` negativos.
- `tests/cpp/test_leakoff_model.cpp` cobre a rejeicao dos campos estruturados negativos.

**Ressalva remanescente:** ainda nao existe um target `saltcreep_eigen` no CMake raiz porque `external/saltcreep` nao e buildado por este target nesta fase. Registrar como candidata a Fase 6.10 se o adapter saltcreep entrar no build.

---

### [2026-06-01] Fase 6.9 — LeakoffModel C++ estruturado — Codex
**Status:** Implementado nesta sessao.
**Testes/comandos:** `cmake --build build --config Debug`, `ctest --test-dir build --output-on-failure` e `lot-sim validate --case` para `lot_pkn_minimal.yaml`, `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml` executados com sucesso.
**Resultado:** 46/46 testes Catch2 passaram; os tres contratos YAML LOT/PKN retornaram `OK`.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/`, `tests/baselines/`, `postprocess/scripts/` ou `.dat` foi alterado/usado.

**Mudanca principal:**
- `lot::LeakoffModel` agora encapsula `none`, `constant_rate`, `carter` minimo e `synthetic_constant` de compatibilidade.
- `PknModel` substituiu o calculo embutido de leakoff pela chamada ao modulo estruturado e continua limitando `V_leakoff <= V_inj`.
- Parser/schema aceitam `constant_rate_m3_s` e o modelo `constant_rate`, mantendo `synthetic_constant`.
- Carter permanece forma estrutural/monotonica minima, nao calibracao fisica dependente de pressao.

**Arquivos criados/alterados:**
- `src/lot/LeakoffModel.cpp`, `include/lot/LeakoffModel.hpp`, `include/lot/LotTypes.hpp`.
- `src/lot/PknModel.cpp`, `include/lot/PknInput.hpp`, `src/lot/PknRunner.cpp`.
- `include/core/types.hpp`, `src/io/CaseParser.cpp`, `schemas/lot_case.schema.yaml`.
- `include/Eigen/` — Eigen header-only mantido em `include/` para calculos futuros do simulador.
- `tests/cpp/test_leakoff_model.cpp`, `CMakeLists.txt`.
- `docs/02_lot_formulation.md`, `docs/05_input_output_formats.md`, `docs/12_validation_results.md`, `docs/17_lot_pkn_roadmap.md`, `tools/docs_status.yaml`, `docs/index.html`.

**Proxima etapa recomendada:** tornar o `PknModel` mais rigoroso quanto ao tempo desde breakdown e consolidar `BreakdownCriterion` C++ antes de iniciar adapters LOT/saltcreep.

---

### [2026-06-01] Fase 6.8 — Política C++ first, Python postprocess only — Codex
**Status:** Implementado nesta sessao.
**Testes/comandos:** `python tools\generate_docs_index.py`, `git diff --name-only` e `git status` executados. Fase documental; `ctest` nao foi executado porque nao houve alteracao em C++, CMake, schema ou testes.
**Escopo:** somente documentos de governanca e manual gerado. Nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/`, `tests/baselines/`, `apps/`, `tests/` ou `postprocess/scripts/` foi alterado. Em `include/` e `src/`, apenas `AGENTS.md` de governanca foram atualizados.

**Politica registrada:**
- Motor de simulacao primario e C++.
- Parser, conversao de unidades, modelos fisicos, runners, writers, leakoff, breakdown, dano, acoplamento LOT/APB/sal e integracao com `external/saltcreep` devem ser C++.
- Python fica restrito a pos-processamento, graficos, relatorios, auditorias externas e migracoes pontuais nao-runtime em `tools/`.
- Fluxo runtime: `YAML/JSON -> C++ parser -> C++ model/runner -> C++ writer -> CSV/JSON`.
- Fluxo Python permitido: `CSV/JSON -> Python plot/report -> PNG/HTML`.

**Arquivos alterados:**
- `AGENTS.md`, `CLAUDE.md`, `postprocess/AGENTS.md`, `src/AGENTS.md`, `include/AGENTS.md`.
- `docs/10_postprocessing_plan.md`, `docs/14_developer_workflow.md`, `docs/17_lot_pkn_roadmap.md`, `docs/07_target_architecture.md`, `docs/13_coupling_lot_apb_salt.md`.
- `docs/dev-log.md`, `tools/docs_status.yaml`, `docs/index.html`.

**Proxima etapa recomendada:** implementar `LeakoffModel` C++ com testes Catch2, depois evoluir `PknModel`, `BreakdownCriterion` e adapter LOT/saltcreep em C++.

---

### [2026-06-01] Fase 6.7 — Pós-processamento moderno LOT/PKN — Codex
**Status:** Implementado nesta sessao.
**Testes:** `python -m unittest discover tests\python` executado; 3/3 passaram. `python -m pytest tests\python` foi tentado, mas o ambiente local nao possui `pytest` instalado.
**Execucao CLI moderna:** `.\build\lot-sim.exe run --case cases\validation\lot_pkn_minimal.yaml --mode lot-pkn --output results\lot_pkn_minimal` e `.\build\lot-sim.exe run --case cases\validation\lot_pkn_with_leakoff.yaml --mode lot-pkn --output results\lot_pkn_with_leakoff` executados com sucesso.
**Pós-processamento:** `python postprocess\scripts\lot_pkn_report.py --run-dir results\lot_pkn_minimal --output reports\lot_pkn_minimal` e `python postprocess\scripts\lot_pkn_report.py --run-dir results\lot_pkn_with_leakoff --output reports\lot_pkn_with_leakoff` geraram 5 PNGs e `report.html` para cada caso.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/`, `tests/baselines/`, `include/`, `src/` ou `apps/` foi alterado. `results/` e `reports/` permanecem fora do versionamento.

**Resultado:**
- `postprocess/scripts/lot_pkn_report.py` valida arquivos de entrada, colunas obrigatorias, `NaN`/`Inf` e gera relatorio HTML.
- Relatorios sao rotulados como `Modern synthetic LOT/PKN output - no legacy regression`.
- Nao houve leitura de `.dat`, comparacao com legado ou declaracao de validacao legado x moderno.
- R09 continua `MITIGATED_FOR_AUDITED_PKN_CASES; BLOCKER_FOR_IDQ4_REGRESSION`.

**Arquivos criados/alterados:**
- `postprocess/scripts/lot_pkn_report.py` — script de graficos/relatorio.
- `tests/python/test_lot_pkn_postprocess.py` e `tests/fixtures/lot_pkn_modern/` — testes e fixture minima.
- `.gitignore` — inclui `reports/`.
- `docs/10_postprocessing_plan.md`, `docs/11_cli_usage.md`, `docs/12_validation_results.md`, `docs/17_lot_pkn_roadmap.md`, `tools/docs_status.yaml`, `docs/index.html` — documentacao/status atualizados.

**Proxima etapa recomendada:** evoluir leakoff/breakdown moderno ou confirmar metadados de `idQ` antes de qualquer comparacao legado x moderno.

---

### [2026-06-01] Fase 6.6 — Ensaio controlado R09 `/22` vs `/2` — Codex
**Status:** Implementado nesta sessao.
**Classificacao R09:** `MITIGATED_FOR_AUDITED_PKN_CASES; BLOCKER_FOR_IDQ4_REGRESSION`.
**Testes/comandos:** `python tools\audit_r09_pkn_conversion.py`, `python tools\generate_docs_index.py` e `python tools\generate_docs_index.py --dry-run` executados com sucesso. Nao houve alteracao C++, portanto `ctest` nao foi reexecutado nesta fase.
**Escopo:** inspecao somente leitura de `legance/LOT_Tese/` e `legance/LOT_APB_v5/`; nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/` foi alterado.

**Resultado:**
- `Conv_bbmin_m3h(Q) = Q * 9.53924 / M_PI / 22` pertence ao ramo `idQ == 4`.
- `Conv_bbmin_m3min(Q) = Q * 0.158987 / M_PI / 2` pertence ao ramo `idQ == 6`.
- Os casos PKN auditados `8-BUZ-67D-RJS-VISCO-pkn.cpp` e `9-BUZ-39DA-RJS-VISCO-2.cpp` usam `idQ == 6`; portanto, nao passam pelo literal `/22`.
- Para a mesma base `Q * 9.53924`, `/22` produz `1/11` do valor de `/2`.

**Arquivos criados/alterados:**
- `docs/audits/R09_pkn_conversion_experiment.md` — relatorio da Fase 6.6.
- `docs/audits/R09_pkn_conversion_table.csv` — tabela analitica gerada pelo script.
- `tools/audit_r09_pkn_conversion.py` — script independente do legado.
- `docs/08_known_issues.md`, `docs/12_validation_results.md`, `docs/17_lot_pkn_roadmap.md`, `tools/docs_status.yaml`, `tools/generate_docs_index.py`, `docs/index.html` — status e manual atualizados.

**Proxima etapa recomendada:** criar pos-processamento moderno/compare qualitativo cuidadosamente rotulado para os dois PKN auditados, ou confirmar metadados de geracao dos `.dat` antes de qualquer regressao quantitativa.

---

### [2026-06-01] Revisao Fase 6.5 — LOT/PKN CSV/JSON — Codex
**Status:** Aprovado com ressalvas corrigidas nesta sessao.
**Commit revisado:** `f18bca1 feat(lot): run pkn cases to csv json`.
**Testes:** `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build -j` e `ctest --test-dir build --output-on-failure` executados; 37/37 passaram apos inclusao de teste negativo do `ResultWriter`.
**Validacao CLI:** `lot-sim validate --case` retornou `OK` para `cases/validation/lot_pkn_minimal.yaml`, `cases/validation/lot_pkn_with_leakoff.yaml` e `cases/lot_tese_migrated/buz67d_pkn.yaml`.
**Validacao schema:** os tres YAMLs LOT/PKN foram validados contra `schemas/lot_case.schema.yaml`.
**Execucao CLI:** `lot-sim run --mode lot-pkn` executou `lot_pkn_minimal.yaml` e `lot_pkn_with_leakoff.yaml`, gerando `result.json` e `timeseries.csv` em `results\lot_pkn_minimal_review` e `results\lot_pkn_with_leakoff_review`.
**Escopo:** `legance/`, `legacy/`, `external/saltcreep/` e `tests/baselines/` permaneceram intocados; `results/` permanece ignorado pelo git.

**Patches aplicados na revisao:**
- `docs/05_input_output_formats.md` — removido trecho PowerShell/hashtable colado indevidamente no Markdown e mantida documentacao limpa de saida CSV futura.
- `src/io/ResultWriter.cpp` e `tests/cpp/test_result_writer.cpp` — writer agora rejeita valores nao finitos antes de gravar CSV/JSON, com teste Catch2 dedicado.
- `docs/index.html` — regenerado a partir dos Markdown corrigidos.

**Conclusao:** fluxo moderno `YAML -> CaseParser -> PknInput -> PknModel -> PknResult -> CSV/JSON` aprovado para a Fase 6.5. Nao houve regressao contra legado; R09 permanece blocker para comparacao legado x moderno.

---

### [2026-06-01] Template SaltCreep no manual gerado — Codex
**Status:** Implementado nesta sessao.
**Testes:** `python tools\generate_docs_index.py` e `python tools\generate_docs_index.py --dry-run` executados com sucesso. Verificacao estrutural confirmou sidebar, busca, fontes Fraunces/Hanken/IBM Plex Mono, hero, cards de metricas, links de navegacao agrupados, 21 secoes e script de destaque/copia.
**Escopo:** `external/saltcreep/docs/index.html` foi usado apenas como referencia visual; nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/` foi alterado.

**Mudanca principal:**
- `tools/generate_docs_index.py` agora gera `docs/index.html` no layout do manual SaltCreep: sidebar fixa escura, busca na navegacao, grupos de documentos, hero editorial, metricas em cards, conteudo em largura de leitura, blocos de codigo com botao de copia e responsividade mobile.
- Como o manual SaltCreep vendorizado e mantido manualmente, o padrao visual foi adaptado no gerador local sem depender de arquivos de `external/saltcreep/`.

**Observacao:** tentativa de abrir o HTML no navegador interno falhou por erro local do runtime da sandbox (`windows sandbox failed: spawn setup refresh`); a verificacao seguiu por geracao deterministica e inspeção estrutural do HTML.

---

### [2026-06-01] Fase 6.5 — Execucao moderna LOT/PKN CSV/JSON — Codex
**Status:** Implementado nesta sessao.
**Testes:** `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build -j` e `ctest --test-dir build --output-on-failure` executados; 36/36 passaram.
**Validacao CLI:** `lot-sim validate --case` retornou `OK` para `cases/validation/lot_pkn_minimal.yaml`, `cases/validation/lot_pkn_with_leakoff.yaml` e `cases/lot_tese_migrated/buz67d_pkn.yaml`.
**Execucao CLI:** `lot-sim run --mode lot-pkn` executou `lot_pkn_minimal.yaml` e `lot_pkn_with_leakoff.yaml`, gerando `result.json` e `timeseries.csv` em `results\lot_pkn_minimal` e `results\lot_pkn_with_leakoff`.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/` foi alterado. `results/` permanece ignorado pelo git.

**Arquivos criados/alterados:**
- `include/lot/PknRunner.hpp`, `src/lot/PknRunner.cpp` — convertem `CaseData` em `PknInput` e executam `PknModel`.
- `include/io/ResultWriter.hpp`, `src/io/ResultWriter.cpp` — gravam `result.json` e `timeseries.csv`.
- `apps/lot-sim.cpp` — adiciona `run --case ... --mode lot-pkn --output ...`.
- `tests/cpp/test_pkn_runner.cpp`, `tests/cpp/test_result_writer.cpp` — cobrem runner, writer e CLI.
- `include/core/types.hpp`, `src/io/CaseParser.cpp`, `schemas/lot_case.schema.yaml`, `cases/validation/lot_pkn_with_leakoff.yaml` — mantem viscosidade e coeficiente de leakoff em SI no contrato moderno.
- `docs/11_cli_usage.md`, `docs/05_input_output_formats.md`, `docs/12_validation_results.md`, `docs/17_lot_pkn_roadmap.md`, `tools/docs_status.yaml`, `docs/index.html` — documentacao/status atualizados.

**R09:** permanece blocker para validacao numerica legado x moderno. Esta fase nao executou regressao contra `.dat`, `legance/LOT_Tese` ou `legance/LOT_APB_v5`.

**Proxima etapa recomendada:** criar ensaio comparativo controlado de R09 ou evoluir leakoff/breakdown com fixtures modernas pequenas, mantendo legado fora do caminho de validacao.

---

### [2026-06-01] Template visual do manual tecnico — Codex
**Status:** Implementado nesta sessao.
**Testes:** `python tools\generate_docs_index.py` e `python tools\generate_docs_index.py --dry-run` executados com sucesso. Verificacao estrutural do HTML confirmou 21 secoes documentais, 4 cards de status e sumario com links ancorados.
**Escopo:** apenas gerador do manual e HTML gerado foram alterados; nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/` foi alterado.

**Mudanca principal:**
- `tools/generate_docs_index.py` passa a gerar o `docs/index.html` com layout claro inspirado no resumo executivo anexado: header em gradiente, sumario sticky em chips, cards de status, secoes amplas, tabelas legiveis, blocos de codigo contrastados e responsividade mobile.
- O sumario usa o primeiro titulo real de cada Markdown em vez de nomes tecnicos de arquivo.
- O aviso de validacao foi alinhado ao estado atual: sem regressao numerica legado x moderno validada, mas com testes sinteticos/contratuais registrados.

**Observacao:** tentativa de abrir o HTML no navegador interno falhou por erro local do runtime da sandbox; a verificacao seguiu por geracao deterministica e inspeção estrutural do HTML.

---

### [2026-06-01] Fase 6.4 — PknModel fisico minimo em SI — Codex
**Status:** Implementado nesta sessao.
**Commit:** `537f4cc feat(lot): implement minimal SI PKN model`.
**Testes:** `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build -j` e `ctest --test-dir build --output-on-failure` executados; 30/30 passaram.
**Validacao CLI:** `lot-sim validate --case` retornou `OK` para `cases/validation/lot_pkn_minimal.yaml`, `cases/validation/lot_pkn_with_leakoff.yaml` e `cases/lot_tese_migrated/buz67d_pkn.yaml`.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/` foi alterado.

**Modelo implementado:**
- `lot::PknModel::simulate` gera serie temporal em SI usando `rate_m3_s`, `dt_s`, `total_time_s`, `accommodation_time_s`, altura de fratura, modulo plano e viscosidade.
- A largura usa escala PKN minima proporcional a `(mu * Q^2 * t / (E' * h))^(1/5)`, com piso numerico e largura inicial.
- O volume injetado e `Q * max(0, t - tac)`; o volume de fratura e o volume injetado menos leakoff acumulado simplificado.
- A pressao liquida e estimada por `E' * width / h`; resultados escalares e series sao finitos e nao negativos.

**R09:** permanece blocker para validacao numerica legado x moderno. Esta fase nao executou regressao contra `.dat` legado nem usou `buz67d_pkn.yaml` como baseline numerico.

**Proxima etapa recomendada:** conectar o modelo ao subcomando `run` apenas depois de definir output numerico e manter R09 separado como ensaio comparativo controlado.

---

### [2026-06-01] Fase 6.3 — Auditoria R09 `/ M_PI / 22` — Codex
**Status:** Auditoria documental implementada nesta sessão.
**Testes:** `git diff --name-only` executado; `ctest` nao executado porque apenas documentacao/status foram alterados.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/`, `include/lot/`, `src/lot/` ou `tests/baselines/` foi alterado.

**Classificacao R09:** `NAO RESOLVIDO: requer ensaio numerico comparativo`.

**Achados principais:**
- `/ M_PI / 22` aparece uma unica vez em `legance/LOT_Tese/src/apb_code/APB1da.cpp`, funcao `Conv_bbmin_m3h(double Q)`, ramo `idQ == 4`.
- Os casos PKN auditados (`8-BUZ-67D-RJS-VISCO-pkn.cpp` e `9-BUZ-39DA-RJS-VISCO-2.cpp`) usam `idQ == 6`, que chama `Conv_bbmin_m3min(Q) = Q * 0.158987 / M_PI / 2`.
- `LOT_APB_v5` nao contem `/ M_PI / 22` no caminho auditado.
- Dimensionalmente, `22` e adimensional; preserva unidade, mas muda `Qinj` por fator 11 contra a hipotese `/ M_PI / 2`.

**Arquivos criados/alterados:**
- `docs/audits/R09_pkn_mpi22_audit.md` — relatorio completo da auditoria
- `docs/08_known_issues.md` — R09 atualizado: escopo reduzido, ainda blocker
- `docs/17_lot_pkn_roadmap.md` — fase 6.3 e proximos passos
- `docs/12_validation_results.md` — auditoria registrada sem validacao numerica
- `docs/dev-log.md`, `tools/docs_status.yaml`, `docs/index.html` — status/indice atualizados

**Proxima etapa recomendada:** ensaio comparativo controlado fora de `legance/` ou implementacao fisica minima em SI sem usar `.dat` legado como baseline.

---

### [2026-06-01 15:44] `d41076e` — Themisson
**Commit:** `docs: patch review Fase 6.2 — README saltcreep policy + roadmap fora de escopo`
**Testes C++:** 4 arquivos | **Testes Python:** 0 arquivos
**Último resultado ctest:** All tests passed (2 assertions in 1 test case)
**Arquivos alterados:**
- `README.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/index.html`

---

### [2026-06-01] Fase 6.2 — Contrato LOT/PKN YAML+C++ — Codex
**Status:** Implementado nesta sessão.
**Testes C++:** 27 Catch2 | **Resultado ctest:** 27 passaram.
**Validação YAML/schema:** `lot_pkn_minimal.yaml`, `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml` validaram contra `schemas/lot_case.schema.yaml`.
**CLI:** `.\build\lot-sim.exe validate --case ...` executado nos 3 casos LOT/PKN com `OK`.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/` foi alterado.

**Arquivos criados:**
- `include/lot/LotTypes.hpp`
- `include/lot/InjectionSchedule.hpp`
- `include/lot/LeakoffModel.hpp`
- `include/lot/PknInput.hpp`
- `include/lot/PknResult.hpp`
- `include/lot/BreakdownDetector.hpp`
- `include/lot/PknModel.hpp`
- `src/lot/BreakdownDetector.cpp`
- `src/lot/PknModel.cpp`
- `tests/cpp/test_breakdown_detector.cpp`
- `tests/cpp/test_pkn_model_synthetic.cpp`
- `cases/validation/lot_pkn_minimal.yaml`
- `cases/validation/lot_pkn_with_leakoff.yaml`
- `cases/lot_tese_migrated/buz67d_pkn.yaml`

**Arquivos alterados:**
- `schemas/lot_case.schema.yaml` — aceita `simulation.mode: lot-pkn` e contrato LOT/PKN
- `include/core/types.hpp` — `LotConfig` expandido com campos SI do contrato PKN
- `src/io/CaseParser.cpp` — parsing e conversao SI para taxa, tempo, comprimento e pressao
- `tests/cpp/test_case_parser.cpp` — cobertura dos novos YAMLs LOT/PKN
- `CMakeLists.txt` — inclui modulo `lot` e novos testes
- `docs/02_lot_formulation.md`, `docs/05_input_output_formats.md`, `docs/12_validation_results.md`, `docs/17_lot_pkn_roadmap.md` — contrato e ressalvas documentados
- `tools/docs_status.yaml`, `docs/index.html` — status/indice atualizados

**R09:** permanece blocker para validacao numerica contra legado. Nenhuma regressao PKN legado x moderno foi declarada.

**Proxima etapa recomendada:** auditar R09 (`/ M_PI / 22`) ou evoluir `PknModel` com formulacao controlada, ainda sem usar baseline legado como verdade numerica.

---

### [2026-06-01 15:25] `75adb3c` — Themisson
**Commit:** `docs: patch review Fase 6.0/6.1 — R09 blocker + roadmap step 4.5`
**Testes C++:** 2 arquivos | **Testes Python:** 0 arquivos
**Último resultado ctest:** All tests passed (2 assertions in 1 test case)
**Arquivos alterados:**
- `docs/08_known_issues.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/index.html`

---

### [2026-06-01] Fase 6.0/6.1 — Governanca saltcreep e auditoria LOT/PKN — Codex
**Status:** Documentacao e auditoria implementadas nesta sessão.
**Testes:** `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build -j` e `ctest --test-dir build --output-on-failure` executados; 15/15 passaram. Nenhuma validacao numerica declarada.
**Escopo:** nenhum arquivo em `legance/`, `legacy/` ou `external/saltcreep/` foi alterado.

**Decisoes:**
- `external/saltcreep/` passa a ser dependencia vendorizada ativa, com edicao controlada por escopo explicito, testes, documentacao e dev-log.
- A primeira migracao moderna de LOT deve priorizar o caminho PKN auditado em `legance/LOT_Tese/`.
- Modelos circular, eliptico e penny-shaped ficam catalogados, mas fora do primeiro caminho critico.

**Achados principais:**
- O caminho PKN passa por `Fluids::setLeakoffProps(..., "pkn")`, `idTypeFracture == 2` e `APB1da::calculateLOTFracturedSaltRock(...)`.
- O legado mistura conversao de vazao com fator geometrico; uma conversao contem expressao suspeita `/ M_PI / 22`.
- O bloco PKN mistura tempo absoluto e tempo desde breakdown em trechos auditados.
- O volume PKN legado usa forma simplificada e tem alternativa comentada, exigindo decisao documentada antes de validacao.

**Arquivos adicionados/alterados:**
- `docs/16_saltcreep_governance.md` — politica de dependencia ativa para saltcreep
- `docs/17_lot_pkn_roadmap.md` — roadmap da primeira entrega LOT/PKN
- `docs/audits/lot_legacy_inventory.md` — inventario LOT nos legados
- `docs/audits/pkn_legacy_path.md` — rota tecnica PKN legado
- `docs/audits/non_pkn_models_status.md` — status dos modelos nao PKN
- `AGENTS.md` e `CLAUDE.md` — regras ajustadas para saltcreep vendorizado ativo
- `docs/07_target_architecture.md` e `docs/13_coupling_lot_apb_salt.md` — arquitetura e acoplamento atualizados

---

### [2026-06-01 14:45] `89d03e0` — Themisson
**Commit:** `docs: clarify dt unit coupling with creep rate`
**Testes C++:** 2 arquivos | **Testes Python:** 0 arquivos
**Último resultado ctest:** All tests passed (2 assertions in 1 test case)
**Arquivos alterados:**
- `docs/08_known_issues.md`

---

### [2026-06-01] Ajuste R08 — Codex + orientação do usuário
**Status:** Documentação ajustada nesta sessão.
**Testes:** não executados (mudança somente documental)

**Correção conceitual:**
- `dt` não é sempre horas ou minutos por natureza; ele deve ser coerente com a unidade temporal da taxa de deformação do backend ativo.
- No `LOT_APB_v5`, a auditoria segue indicando `dt` em [h].
- Se a taxa estiver em [1/s], [1/min] ou [1/h], o passo temporal correspondente deve estar em segundos, minutos ou horas, respectivamente, ou ser convertido explicitamente na fronteira.
- `tac`/tempo de acomodação é o intervalo inicial sem incrementos térmicos ou injeção/variação operacional de fluidos.

**Arquivos alterados:**
- `docs/08_known_issues.md` — R08 reescrito como regra dimensional geral + conclusão específica para `LOT_APB_v5`

---

### [2026-06-01] Fase 5-E — Codex
**Status:** Implementado nesta sessão.
**Testes C++:** 15 Catch2 | **Resultado ctest:** 15 passaram
**Validação YAML:** `cases/validation/lot_minimal.yaml` e `cases/validation/lot_double_mechanism_reference.yaml` válidos contra `schemas/lot_case.schema.yaml`

**Arquivos adicionados/alterados:**
- `docs/08_known_issues.md` — R08 resolvido: `dt` do wrapper APB/SESTSAL em [h], com risco lateral documentado
- `src/io/CaseParser.cpp` — valida listas mínimas e referências `annulars[].fluid`/`layers[].rock`
- `tests/cpp/test_case_parser.cpp` — testes de referências inválidas e lista obrigatória vazia
- `schemas/lot_case.schema.yaml` — `minItems` para listas semanticamente obrigatórias
- `apps/lot-sim.cpp` — subcomando `validate --case`

**Execução manual:**
`lot-sim validate --case cases/validation/lot_minimal.yaml` imprime `OK: lot_minimal_validation`.

---

### [2026-06-01] Fase 5-A..5-D — Codex
**Status:** Implementado nesta sessão.
**Testes C++:** 12 Catch2 | **Resultado ctest:** 12 passaram
**Validação YAML:** `cases/validation/lot_minimal.yaml` e `cases/validation/lot_double_mechanism_reference.yaml` válidos contra `schemas/lot_case.schema.yaml`

**Arquivos adicionados/alterados:**
- `include/units/units.hpp` — conversões header-only C++20, incluindo PPG, pol, psi, bar, cP, temperatura, torque e gradiente hidrostático
- `include/core/types.hpp` — structs de `CaseData` e subestruturas com FA01/FA02 documentadas nos campos
- `include/io/CaseParser.hpp` + `src/io/CaseParser.cpp` — parser YAML com conversões para SI e validações mínimas
- `schemas/lot_case.schema.yaml` — schema principal comentado, incluindo `hydrostatic_depth_profile`
- `cases/validation/lot_minimal.yaml` — caso mínimo LOT sem sal, validável
- `cases/validation/lot_double_mechanism_reference.yaml` — caso pequeno para testar FA01/FA02
- `apps/lot-sim.cpp` — subcomando `inspect --case`
- `tests/cpp/test_units.cpp` + `tests/cpp/test_case_parser.cpp` — cobertura inicial Catch2
- `CMakeLists.txt` — targets `lot-sim` e `lot_sim_tests`; workaround local para `yaml-cpp` com GCC 16

**Execução manual:**
`lot-sim inspect --case cases/validation/lot_minimal.yaml` imprime resumo do caso sem erro.

---

### [2026-06-01 12:17] `13eb5c3` — Themisson
**Commit:** `feat(saltcreep): sync saltcreep with LOT/APB integration updates`
**Testes C++:** 0 arquivos | **Testes Python:** 0 arquivos
**Último resultado ctest:** nenhum (módulos ainda não implementados)

**⚠ Modificações em external/saltcreep/:**
- `external/saltcreep/.gitignore`
- `external/saltcreep/AGENTS.md`
- `external/saltcreep/CLAUDE.md`
- `external/saltcreep/CMakeLists.txt`
- `external/saltcreep/cases/apb/mud_gradient_1d_8p5ppg.yaml`
- `external/saltcreep/cases/apb/mud_gradient_2d_Q8_8p5ppg.yaml`
- `external/saltcreep/cases/sestsal/base_model.yaml`
- `external/saltcreep/cases/sestsal/base_model2D.yaml`
- … e mais 38 arquivos
> Atualizar a seção 'Modificações em andamento no saltcreep' abaixo.

---

### [2026-06-01 11:47] `3b45136` — Themisson
**Commit:** `feat: add dev-log system with auto-update hook`
**Testes C++:** 0 arquivos | **Testes Python:** 0 arquivos
**Último resultado ctest:** nenhum (módulos ainda não implementados)
**Arquivos alterados:**
- `.agents/skills/update-devlog/SKILL.md`
- `.claude/settings.json`
- `.claude/skills/update-devlog/SKILL.md`
- `AGENTS.md`
- `CLAUDE.md`
- `tools/update_devlog.py`

---

### [2026-06-01 10:36] `4739d4b` — Themisson
**Commit:** `docs: formulation audit results (Fase 3 /formulation-audit)`
**Fase:** 3 — Auditoria de formulação
**Arquivos alterados:**
- `docs/08_known_issues.md` — FA01-FA04 documentados com evidência de código
- `docs/12_validation_results.md` — seção de baselines atualizada
- `docs/index.html` — regenerado com novos achados
**Saltcreep:** não alterado neste commit
**Testes:** nenhum (documentação)
**Resultado:** Convenções de sinais, unidades de e0 e temperatura confirmadas

---

### [2026-06-01 10:30] `4f9957a` — Themisson
**Commit:** `feat: capture LOT_APB_v5 baseline outputs (Fase 4)`
**Fase:** 4 — Baselines
**Arquivos alterados:**
- `.gitignore` — excluir inputs pesados (57MB) e detailed_output (29MB)
- `docs/12_validation_results.md` — metadados reais de compilação
- `tests/baselines/apbv5_SCORE-MRO-28_output.json` (47 KB) ← **BASELINE PRINCIPAL**
- `tests/baselines/apbv5_SCORE-MRO-28_original_output.json` (27 KB)
- `tests/baselines/apbv5_SCORE-MRO-28_Ev_temp_output.json` (47 KB)
**Nota compilação:** g++16.1 + `-w -fpermissive` (Eigen antigo × GCC16 incompatibilidade)
**Testes:** LOT_APB_v5 executado com 3 JSONs — output gerado em 0.1–0.3s

---

### [2026-06-01 10:04] `72c8ca4` — Themisson
**Commit:** `chore: add external/saltcreep as vendored reference (8.5MB)`
**Fase:** 1 — Estrutura
**Saltcreep:** adicionado como cópia controlada (sem .git próprio no workspace)
**Regra:** NÃO editar, NÃO duplicar modelos constitutivos

---

### [2026-06-01 10:04] `7dc3959` — Themisson
**Commit:** `chore: exclude legance/ from git (400MB legacy code — local only)`
**Fase:** 1 — Estrutura
**Nota:** `legance/` (400MB) excluído permanentemente do git — apenas local

---

### [2026-06-01 10:03] `78d17df` — Themisson
**Commit:** `docs: add 16 technical docs, interactive index.html and AGENTS.md per directory`
**Fase:** 2 — Documentação
**Entregáveis:**
- `docs/00_project_overview.md` … `docs/15_changelog.md` (16 arquivos)
- `docs/index.html` (66KB, 16 seções, offline-first)
- `tools/docs_status.yaml` + `tools/generate_docs_index.py`
- 11 × `AGENTS.md` por diretório

---

### [2026-06-01 10:03] `623ec68` — Themisson
**Commit:** `feat: add Claude Code agents, skills and Codex agent configuration`
**Fase:** 3 — Agentes e skills
**Entregáveis:**
- `.claude/agents/`: cpp-pro, verifier, legacy-explorer, docs-sync, salt-adapter
- `.claude/skills/` + `.agents/skills/`: formulation-audit, cpp-refactor, validation-benchmark, postprocess-report, docs-html-report, lot-salt-integration
- `.claude/settings.json`: Allow/Deny configurado
- `.codex/agents/`: cpp-pro.toml, expert-cpp-software-engineer.toml

---

### [2026-06-01 10:02] `a0502d7` — Themisson
**Commit:** `chore: initialize lot-salt-suite project structure`
**Fase:** 1 — Estrutura inicial
**Entregáveis:** CLAUDE.md, AGENTS.md, README.md, .gitignore, CMakeLists.txt, pyproject.toml

---

## Seção: Modificações em external/saltcreep — histórico

### [2026-06-01] Sincronização 1 — WallPressureField + APB cases

**Status:** Concluído e commitado (`13eb5c3`)

**Novos arquivos adicionados:**

| Arquivo | Relevância para lot-salt-suite |
|---------|-------------------------------|
| `include/solver/WallPressureField.hpp` | Interface-chave para pressão de lama → sal |
| `src/solver/WallPressureField.cpp` | Confirma FC=119.826 (mesmo valor que APB1da) |
| `cases/apb/mud_gradient_1d_8p5ppg.yaml` | Formato YAML para casos APB com gradiente de lama |
| `cases/apb/mud_gradient_2d_Q8_8p5ppg.yaml` | Variante 2D Q8 do caso APB |
| `post/saltpost/diameter.py` | Rastreamento de diâmetro — útil para APB |
| `post/saltpost/layers.py` | Pós-processamento por camada |
| `tests/cpp/test_wall_pressure_field.cpp` | Testes Catch2 para WallPressureField |

**Arquivos modificados (impacto):**

| Arquivo | O que mudou |
|---------|------------|
| `include/solver/Assembler.hpp` | Suporte a WallPressureField como BC |
| `include/solver/TimeIntegrator.hpp` | Conexão com WallPressureField |
| `include/io/CaseParser.hpp` | Novo modo `fluid.mode: hydrostatic_depth_profile` |
| `src/io/CaseParser.cpp` | Parser para o novo modo de fluido APB |

**Impacto direto no design da Fase 8 (SaltCreepInterface):**

```
WallPressureField é a ponte que faltava:
  lot-salt-suite/include/salt/SaltCreepInterface.hpp
    recebe WallPressureField* como parâmetro
    ou como dependência injetada no SaltCreepSaltcreepAdapter

Fluxo confirmado:
  APBSolver → WallPressureField → SaltCreepSaltcreepAdapter
    → saltcreep::Assembler → deformação viscosa → δV anular → δP APB

Constante confirmada: kLbPerGalToKgPerM3 = 119.826 (saltcreep)
                      FC = 119.826427 (APB1da legado)  ← mesmo valor
```

**fluid.mode novo no YAML saltcreep:**
```yaml
fluid:
  mode: hydrostatic_depth_profile  # novo
  weight_lb_per_gal: 8.5
  surface_pressure_Pa: 0.0
```
→ Este modo deve ser incorporado ao schema `schemas/lot_case.schema.yaml` na Fase 5.

---

### [2026-06-11] Fase 11.8C — Especificação do adapter diagnóstico PennyShaped

**Status:** Concluído.

**Classificação:** `PENNY_ADAPTER_SPEC_VALID`.

**Entregáveis:**
- `docs/65_penny_diagnostic_adapter_spec.md`
- `tests/fixtures/comparison/phase11_8c_penny_adapter_input.yaml`
- `tools/validate_phase11_8c_penny_adapter_spec.py`
- `tests/python/test_validate_phase11_8c_penny_adapter_spec.py`

**Escopo:** especificação/fixture/validador apenas. Não altera C++, CMake,
parser, schema, CLI, `PknModel`, `PknRunner`, casos protegidos ou runtime
`lot-pkn`.

**Próxima fase:** `PHASE11_8D_PENNY_DIAGNOSTIC_ADAPTER_IMPLEMENTATION`.

---

### [2026-06-11] Fase 11.8D — Adapter diagnóstico PennyShaped

**Status:** Concluído.

**Classificação:** `PENNY_SHAPED_DIAGNOSTIC_ADAPTER_IMPLEMENTED`.

**Entregáveis:**
- `include/lot/PennyShapedDiagnosticAdapter.hpp`
- `src/lot/PennyShapedDiagnosticAdapter.cpp`
- `tests/cpp/test_penny_shaped_diagnostic_adapter.cpp`
- `docs/66_penny_diagnostic_adapter_implementation.md`

**Escopo:** adapter C++ opt-in em torno de `PennyShapedModel`. Não altera
parser, schema, CLI, `PknModel`, `PknRunner`, casos protegidos ou semântica
`lot-pkn`.

**Próxima fase:** `PHASE11_9A_PENNY_SYNTHETIC_MINIMAL_CASE`.

---

### [2026-06-11] Fase 11.9A — Caso sintético mínimo PennyShaped

**Status:** Concluído.

**Classificação:** `PENNY_SYNTHETIC_CASE_CREATED`.

**Entregáveis:**
- `cases/validation/non_pkn/penny_shaped_synthetic_minimal.yaml`
- `tools/verify_phase11_9a_penny_synthetic_case.py`
- `tests/python/test_verify_phase11_9a_penny_synthetic_case.py`
- `docs/67_penny_synthetic_minimal_case.md`

**Escopo:** caso/verificador diagnóstico. Não altera parser, schema, CLI,
`PknModel`, `PknRunner`, casos protegidos ou semântica `lot-pkn`.

**Próxima fase:** `PHASE11_9B_BUZ29_PENNY_READINESS`.

---

### [2026-06-11] Fase 11.9B — Readiness BUZ29 PennyShaped

**Status:** Concluído.

**Classificação:** `BUZ29_PENNY_CANDIDATE_PARTIAL`.

**Gate:** `BUZ29_PENNY_READINESS_PARTIAL_DO_NOT_START_11_10A`.

**Entregáveis:**
- `tools/check_phase11_9b_buz29_penny_readiness.py`
- `tests/python/test_check_phase11_9b_buz29_penny_readiness.py`
- `docs/68_buz29_penny_candidate_readiness.md`

**Decisão:** BUZ29 ainda não está pronto para YAML diagnóstico
`PennyShaped`. Faltam histórico de pressão, `sigmaTheta`, tempo desde abertura
e estado APB/sal em contrato consumível.

**Próxima fase recomendada:** `PHASE11_9C_COMPLETE_BUZ29_PENNY_EVIDENCE`.
`PHASE11_10A` não foi executada.

---

### [2026-06-12] Fase 11.9C — Evidência BUZ29 PennyShaped — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Classificação:** `BUZ29_PENNY_EVIDENCE_PARTIAL`.

**Entregáveis:**
- `tools/audit_phase11_9c_buz29_penny_evidence.py`
- `tests/python/test_audit_phase11_9c_buz29_penny_evidence.py`
- `docs/70_buz29_penny_evidence_audit.md`

**Decisão:** a evidência BUZ29-PENNY permanece parcial. Há fonte legada e
indícios documentais, mas pressão, `sigmaTheta`, tempo de abertura, tempo desde
abertura e estado APB/sal ainda não estão consumíveis para o
`PennyShapedDiagnosticAdapter`.

**Gate:** `PHASE11_9D_UPDATE_BUZ29_PENNY_READINESS`.

`PHASE11_10A` não foi executada nesta fase.

---

### [2026-06-12] Fase 11.9D — Atualização de readiness BUZ29 PennyShaped — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Readiness anterior:** `BUZ29_PENNY_CANDIDATE_PARTIAL`.

**Evidência 11.9C:** `BUZ29_PENNY_EVIDENCE_PARTIAL`.

**Readiness atualizado:** `BUZ29_PENNY_CANDIDATE_PARTIAL`.

**Gate:** `BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A`.

**can_start_11_10A:** `false`.

**Entregáveis:**
- `tools/update_phase11_9d_buz29_penny_readiness.py`
- `tests/python/test_update_phase11_9d_buz29_penny_readiness.py`
- `docs/71_buz29_penny_readiness_update.md`

**Próxima fase recomendada:**
`PHASE11_9E_COMPLETE_BUZ29_PRESSURE_AND_OPENING_EVIDENCE`.

`PHASE11_10A` permanece bloqueada.

---

### [2026-06-12] Fase 11.11I — Estratégia de fonte real de sigma-theta inicial — Codex

**Status:** Concluído; commit/push planejado ao final da fase.

**Classificação:** `REAL_SIGMATHETA_INITIAL_SOURCE_STRATEGY_SPECIFIED`.

**Fonte primária:** `ELASTIC_INITIAL_WELLBORE_STATE`.

**Fallbacks:** `EXPLICIT_DIAGNOSTIC_INPUT`, `SYNTHETIC_FIXTURE`.

**Premissa física registrada:** `t = 0` do LOT não é `t = 0` da perfuração.
O estado inicial deve representar a condição pós-perfuração e pré-LOT.

**Decisão:** `LEGACY_DIAGNOSTIC_TRACE` permanece fonte diagnóstica, não fonte
de validação física automática.

**Entregáveis:**
- `tools/spec_phase11_11i_real_sigmatheta_initial_source_strategy.py`
- `tests/python/test_spec_phase11_11i_real_sigmatheta_initial_source_strategy.py`
- `docs/109_real_sigmatheta_initial_source_strategy.md`

**Próxima fase recomendada:**
`PHASE11_11J_AUDIT_RUNTIME_SIGMATHETA_AND_PRESSURE_AVAILABILITY`.

---

### [2026-06-12] Fase 11.11J — Auditoria runtime sigma-theta/pressão — Codex

**Status:** Concluído; commit/push planejado ao final da fase.

**Classificação:** `RUNTIME_SIGMATHETA_PRESSURE_AVAILABILITY_AUDITED`.

**Resultado:**

```text
sigma_theta_initial_runtime_available = false
sigma_theta_current_runtime_available = false
wellbore_pressure_runtime_available = true
pressure_semantics_resolved = false
sign_convention_resolved = false
reference_frame_resolved = false
runtime_real_wiring_allowed_next = false
```

**Decisão:** o runtime real ainda não possui fonte sigma-theta inicial/current
com semântica suficiente para wiring físico do `limited_gate`.

**Entregáveis:**
- `tools/audit_phase11_11j_runtime_sigmatheta_pressure_availability.py`
- `tests/python/test_audit_phase11_11j_runtime_sigmatheta_pressure_availability.py`
- `docs/110_runtime_sigmatheta_pressure_availability_audit.md`

**Próxima fase recomendada:**
`PHASE11_11K_SPECIFY_POST_DRILLING_INITIAL_STATE_INTEGRATION`.

---

### [2026-06-12] Fase 11.11K — Especificação de estado inicial pós-perfuração — Codex

**Status:** Concluído; commit/push planejado ao final da fase.

**Classificação:** `POST_DRILLING_INITIAL_STATE_INTEGRATION_SPECIFIED_BUT_SOURCE_MISSING`.

**Contrato:** `PostDrillingInitialState`.

**Campos semânticos principais:**

```text
state_time = POST_DRILLING_BEFORE_LOT
sign_convention = COMPRESSION_POSITIVE
reference_frame = WELLBORE_WALL_TOTAL_STRESS
pressure_reference = WELLBORE_PRESSURE
source_status = MISSING_RUNTIME_SIGMATHETA_SOURCE
implementation_allowed_next = false
runtime_dispatch_allowed_next = false
buz29_execution_allowed_next = false
```

**Decisão:** o contrato está especificado, mas ainda sem fonte runtime real de
sigma-theta inicial/current.

**Entregáveis:**
- `tools/spec_phase11_11k_post_drilling_initial_state_integration.py`
- `tests/python/test_spec_phase11_11k_post_drilling_initial_state_integration.py`
- `docs/111_post_drilling_initial_state_integration_spec.md`

**Próxima fase recomendada:**
`PHASE11_11L_DECIDE_LIMITED_GATE_REAL_SIGMATHETA_READINESS`.

---

### [2026-06-12] Fase 11.11L — Decisão limited_gate real sigma-theta — Codex

**Status:** Concluído; commit/push planejado ao final da fase.

**Classificação:** `LIMITED_GATE_REMAINS_DIAGNOSTIC_BLOCKED_BY_REAL_SOURCE`.

**Decisão:**

```text
implementation_allowed_next = false
runtime_dispatch_allowed_next = false
buz29_execution_allowed_next = false
pkn_behavior_change_allowed = false
```

**Motivo:** faltam fontes runtime reais de `sigma_theta_initial` e
`sigma_theta_current`; a semântica de pressão, sinal e referencial ainda não
estão resolvidos para gate real.

**Entregáveis:**
- `tools/decide_phase11_11l_limited_gate_real_sigmatheta_readiness.py`
- `tests/python/test_decide_phase11_11l_limited_gate_real_sigmatheta_readiness.py`
- `docs/112_limited_gate_real_sigmatheta_readiness_decision.md`

**Próxima fase recomendada:**
`PHASE11_11M_KEEP_LIMITED_GATE_DIAGNOSTIC_AND_PLAN_SIGMATHETA_SOURCE`.

---

### [2026-06-12] Fase 11.11P — Readiness do gate sigma-theta diagnóstico — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Classificação:** `DIAGNOSTIC_SIGMATHETA_GATE_READY`.

**Decisão:**

```text
ready_for_diagnostic_use = true
ready_for_physical_validation = false
ready_for_physical_dispatch = false
ready_for_real_source_integration_spec = true
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_change_allowed = false
penny_shaped_runtime_enabled = false
```

**Interpretação:** o gate alimentado por `sigma_theta_diagnostic_input` está
pronto para uso diagnóstico controlado. O estado `Reached` continua sendo
elegibilidade diagnóstica, não execução física de fratura.

**Entregáveis:**
- `tools/decide_phase11_11p_diagnostic_sigmatheta_gate_readiness.py`
- `tests/python/test_decide_phase11_11p_diagnostic_sigmatheta_gate_readiness.py`
- `docs/116_diagnostic_sigmatheta_gate_readiness_decision.md`

**Próxima fase recomendada:**
`PHASE11_11Q_SPECIFY_REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH`.

---

### [2026-06-13] Fase 11.11Q — Caminho de integração da fonte real sigma-theta — Codex

**Status:** Concluído; commit/push executado ao final da fase.

**Classificação:** `REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH_SPECIFIED`.

**Decisão:**

```text
primary_real_source = ELASTIC_INITIAL_WELLBORE_STATE
secondary_real_source = APB_SALT_COUPLED_STATE
future_real_source = SALT_CREEP_PRE_LOT_STATE
diagnostic_only_sources = EXPLICIT_DIAGNOSTIC_INPUT, SYNTHETIC_FIXTURE
legacy_trace_physical_validation_allowed = false
implementation_allowed_next = false
runtime_dispatch_allowed_next = false
buz29_execution_allowed_next = false
pkn_behavior_change_allowed = false
```

**Contrato futuro:** `PostDrillingSigmaThetaProvider`, ainda nao implementado.

**Entregáveis:**
- `tools/spec_phase11_11q_real_sigmatheta_source_integration_path.py`
- `tests/python/test_spec_phase11_11q_real_sigmatheta_source_integration_path.py`
- `docs/117_real_sigmatheta_source_integration_path.md`

**Próxima fase recomendada:**
`PHASE11_11R_CREATE_POST_DRILLING_SIGMATHETA_PROVIDER_FIXTURES`.
