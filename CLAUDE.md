# CLAUDE.md — lot-salt-suite

Este repositório moderniza, corrige, documenta e integra simuladores de
Leak-Off Test (LOT), Annular Pressure Buildup (APB) e fluência de sal (Salt Creep).
O código principal é C++20. O pós-processamento é Python. O repositório
`external/saltcreep` é a dependência vendorizada ativa para o solver moderno de sal.

## Fontes legadas (CONGELADAS — não editar)

- `legance/LOT_Tese/` — código usado na tese. Muitos `main` de caso hard-coded. **NÃO EDITAR.**
- `legance/LOT_APB_v5/` — versão mais moderna com entrada JSON. **NÃO EDITAR DIRETAMENTE.**
- `external/saltcreep/` — solver FEM moderno de fluência; dependência vendorizada ativa. **EDIÇÃO CONTROLADA, NÃO DUPLICAR.**
- `legacy/` — espelho organizacional (não-editável) apontando para os legados acima.

> **ATENÇÃO:** O diretório físico é `legance/` (não `legacy/`). Isso é herança histórica.
> Todo código novo usa `legacy/` como convenção de nomenclatura nos docs.

## Objetivo técnico

Criar uma arquitetura modular C++ com:

- executável único `lot-sim` controlado por subcomandos e flags;
- casos definidos em YAML (compatibilidade temporária com JSON do LOT_APB_v5);
- módulos separados para: wellbore, fluids, rocks, salt, lot, apb, thermal, coupling;
- testes unitários (Catch2) e de regressão contra legados;
- integração com `saltcreep` por interface/adapter, nunca por cópia direta;
- pós-processamento Python no pacote `postprocess/lotsaltpost/`;
- documentação técnica em `docs/` com `docs/index.html` navegável.

## Regras invioláveis

1. **Não editar** qualquer arquivo em `legance/` ou `legacy/`.
2. **Não editar** `external/saltcreep/` sem escopo explícito de integração de sal, testes, documentação e registro em `docs/dev-log.md`.
3. **Não apagar** resultados ou baselines existentes.
4. **Não alterar formulação física** sem registrar em `docs/08_known_issues.md` e `docs/15_changelog.md`.
5. **Não misturar** refatoração estrutural com mudança de formulação no mesmo commit.
6. **Não mudar** convenção de sinais sem documentação explícita.
7. **Não mudar** unidades internas sem documentação explícita.
8. **Internamente, sempre SI** (Pa, m, kg, K, s). Conversões somente em `include/units/`.
9. **Conversões de unidade** devem ficar exclusivamente em `include/units/units.hpp`.
10. **Todo novo módulo** deve ter pelo menos um teste Catch2 antes do merge.
11. **Toda migração de caso** deve comparar resultado novo contra baseline legado.
12. **`docs/12_validation_results.md`** nunca deve declarar validações como executadas sem rodá-las.
13. **`docs/index.html`** status de seção = "validado" somente após CI verde documentado.

## Antes de modificar código

**Primeira leitura — sempre:** `docs/dev-log.md`
(contém o estado atual do projeto, fase ativa, próximas tarefas e achados críticos)

Depois leia na ordem abaixo conforme a tarefa:

1. `docs/dev-log.md` ← **OBRIGATÓRIO, SEMPRE**
2. `docs/00_project_overview.md`
3. `docs/01_repository_inventory.md`
3. `docs/02_lot_formulation.md` (se tocar em LOT)
4. `docs/03_apb_formulation.md` (se tocar em APB)
5. `docs/04_salt_creep_models.md` (se tocar em sal)
6. `docs/06_validation_plan.md`
7. `docs/08_known_issues.md`
8. Arquivo relevante em `legance/` para comparação

Depois: produza um plano curto e implemente apenas a tarefa solicitada.

## C++

- C++20 em todo código novo (salvo restrição explícita).
- Evitar `using namespace std;` em qualquer header.
- Evitar `new`/`delete` em código novo — usar RAII e smart pointers.
- Classes públicas em `include/<modulo>/`; implementações em `src/<modulo>/`.
- Único executável principal: `apps/lot-sim.cpp`.
- Eigen: não duplicar; referenciar o vendorizado em `external/saltcreep/include/Eigen/`
  ou criar um único include path no CMakeLists.txt apontando para ele.
- yaml-cpp via FetchContent (ver CMakeLists.txt).
- Catch2 v3 via FetchContent para testes.
- Não usar `printf`; preferir `std::format` (C++20) ou streams com flags.

## Python

- Pós-processamento em `postprocess/lotsaltpost/` como pacote reutilizável.
- Type hints obrigatórios em toda função pública.
- Evitar caminhos absolutos; usar `pathlib.Path`.
- Separar: leitura (`io.py`), métricas (`compare.py`), gráficos (`plots.py`), relatório (`report.py`).
- Toda comparação deve produzir tabela de erro (L2, L∞, diferença máxima por campo).
- pytest para todos os testes em `tests/python/`.

## Organização de casos

- Casos novos: YAML em `cases/` validados contra schema em `schemas/`.
- Casos legados: manter em `legance/` sem tocar; criar YAMLs equivalentes em `cases/lot_tese_migrated/` ou `cases/lot_apb_v5_migrated/`.
- Baselines capturados de legados: `tests/baselines/` (imutáveis sem aprovação explícita).

## Estratégia de integração com saltcreep

- Interface: `include/salt/SaltCreepInterface.hpp` (abstrata).
- Adapter: `SaltCreepSaltcreepAdapter` usando modelos do `external/saltcreep`.
- Adapter legado: `SaltCreepSESTSALAdapter` para compatibilidade com SESTSAL interno.
- Proibido: copiar código de `external/saltcreep/src/constitutive/` para `src/salt/`.
- Permitido: evoluir `external/saltcreep/` para pressao de parede, dano,
  pos-processamento e acoplamento quando houver tarefa explicita, testes e
  documentacao.

## Critério de conclusão de qualquer tarefa

Ao final de cada tarefa, informar:

- arquivos criados ou alterados;
- por que foram alterados;
- testes executados e resultados;
- resultados numéricos comparados (se aplicável);
- riscos remanescentes;
- documentação atualizada.

## Skill disponíveis

Use as skills disponíveis no Claude Code para tarefas especializadas:

- `/formulation-audit` — auditar formulações físicas e convenções
- `/cpp-refactor` — refatorar C++ sem alterar formulação
- `/validation-benchmark` — criar/executar testes de regressão
- `/postprocess-report` — melhorar pós-processamento Python
- `/docs-html-report` — atualizar `docs/index.html` e Markdown
- `/lot-salt-integration` — integrar LOT/APB com saltcreep
