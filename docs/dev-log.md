# dev-log — lot-salt-suite

> **LEITURA OBRIGATÓRIA** para Claude Code e Codex na abertura de qualquer sessão.
> Auto-atualizado por `tools/update_devlog.py` após cada `git commit` ou `git push`.
> Invoke `/update-devlog` manualmente quando necessário.

---

## Estado atual do projeto

```
Fase ativa  : 5 em andamento (units + schema + CaseParser + CLI inspect)
Branch      : main
Repositório : https://github.com/Themisson/lot-salt-suite
Último push : 2026-06-01
Testes C++  : 12 Catch2 (12 passaram em 2026-06-01)
Testes Py   : 0
Baselines   : 4 capturados (LOT_APB_v5)
Saltcreep   : sincronizado — WallPressureField + cases/apb/ adicionados
```

### Próximas tarefas (Fase 5)

- [ ] R08 pendente: verificar unidade de `dt` em `legance/LOT_APB_v5/src/apb/apb_salt_1d.cpp`
- [x] `schemas/lot_case.schema.yaml`
- [x] `include/units/units.hpp` (conversões PPG→kg/m³, pol→m, etc.)
- [x] `include/core/types.hpp` (CaseData struct)
- [x] `include/io/CaseParser.hpp` + `src/io/CaseParser.cpp`
- [x] `apps/lot-sim.cpp` com subcomando `inspect`

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
