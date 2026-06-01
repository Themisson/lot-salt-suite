# dev-log — lot-salt-suite

> **LEITURA OBRIGATÓRIA** para Claude Code e Codex na abertura de qualquer sessão.
> Auto-atualizado por `tools/update_devlog.py` após cada `git commit` ou `git push`.
> Invoke `/update-devlog` manualmente quando necessário.

---

## Estado atual do projeto

```
Fase ativa  : 6.4 implementada (PknModel fisico minimo em SI)
Branch      : main
Repositório : https://github.com/Themisson/lot-salt-suite
Último push : 2026-06-01
Testes C++  : 30 Catch2 (30 passaram em 2026-06-01)
Testes Py   : 0
Baselines   : 4 capturados (LOT_APB_v5)
Saltcreep   : sincronizado — WallPressureField + cases/apb/ adicionados
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
- [ ] Executar ensaio comparativo controlado R09 (`/(pi*22)` vs `/(pi*2)`) sem alterar legado
- [ ] Conectar LOT/PKN ao CLI somente apos contrato numerico testado

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

### [2026-06-01] Fase 6.4 — PknModel fisico minimo em SI — Codex
**Status:** Implementado nesta sessao.
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
