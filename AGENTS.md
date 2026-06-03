# AGENTS.md — lot-salt-suite

Este repositório integra simuladores de Leak-Off Test (LOT), Annular Pressure Buildup (APB)
e fluência de sal (Salt Creep). O código principal é C++20. O pós-processamento é Python.

## Contexto para agentes de código

Você está trabalhando em um projeto de simulação de poços de petróleo de alta complexidade.
O repositório tem três bases: código legado da tese (`legance/LOT_Tese/`), versão mais
moderna com JSON (`legance/LOT_APB_v5/`) e um solver FEM moderno de sal (`external/saltcreep/`).

O objetivo é criar código novo nos diretórios `src/`, `include/`, `apps/`, `cases/` etc.,
**sem modificar nenhum arquivo legado**. O diretório `external/saltcreep/` é uma
dependência vendorizada ativa: pode evoluir somente com escopo explícito, testes,
documentação e registro em `docs/dev-log.md`.

## Regras invioláveis para agentes

1. **PROIBIDO** editar qualquer arquivo em `legance/` ou `legacy/`.
2. **PROIBIDO** editar `external/saltcreep/` sem tarefa explícita de integração de sal, testes próprios e atualização documental.
3. **PROIBIDO** apagar arquivos existentes.
4. **PROIBIDO** mudar formulação física sem documentar em `docs/08_known_issues.md`.
5. **PROIBIDO** declarar validações como executadas em `docs/12_validation_results.md` sem rodar.
6. **PROIBIDO** copiar código de `external/saltcreep/src/` para `src/salt/` — use interface/adapter.
7. **PROIBIDO** misturar lógica de solver com parsing de entrada no mesmo arquivo.
8. **OBRIGATÓRIO** criar testes Catch2 para todo módulo C++ novo.
9. **OBRIGATÓRIO** validar YAML de caso contra schema antes de commitar.
10. **OBRIGATÓRIO** converter todas as unidades de campo para SI no parser (não no solver).
11. **OBRIGATÓRIO** informar arquivos alterados, testes executados e riscos ao final da tarefa.

## Política — C++ first, Python postprocess only

O motor primário de simulação do `lot-salt-suite` é C++.

Devem ser implementados primariamente em C++:

- modelos físicos;
- parsing de entrada e conversão de unidades;
- montagem de `CaseData`, runners e writers;
- solvers numéricos;
- modelos de LOT, APB, sal, leakoff, breakdown e dano;
- acoplamento LOT/APB/sal;
- integração com `external/saltcreep`.

Python é permitido somente para:

- pós-processamento;
- gráficos;
- geração de relatórios;
- auditorias externas auxiliares;
- utilitários pontuais de migração em `tools/`, claramente marcados como não-runtime.

Python **não** deve:

- gerar entradas de produção como parte do fluxo padrão;
- substituir módulos de solver C++;
- implementar modelos físicos usados pelo solver;
- decidir parâmetros físicos para simulações de produção;
- calibrar modelos automaticamente sem fase futura dedicada;
- acessar outputs legados como parte do caminho runtime do solver;
- tornar-se pré-processador obrigatório para simulações LOT/APB/sal normais.

Fluxo principal:

```text
YAML/JSON → C++ parser → C++ model/runner → C++ writer → CSV/JSON
```

Fluxo permitido de pós-processamento:

```text
CSV/JSON → Python plot/report → PNG/HTML
```

## Autorização operacional — Claude Code / Codex

Agentes estão autorizados a executar os itens abaixo **sem pedir confirmação a cada passo**, desde que estejam dentro do escopo da tarefa:

**Sempre autorizados:** `git status/log/diff`, leitura de arquivos, `cmake`, `cmake --build`, `ctest`, `pytest`, `lot-sim validate`, `lot-sim run`, `python tools/generate_docs_index.py`, `git add`, `git commit`, `git push` (quando a tarefa pedir), remoção de `build/` ou temporários da própria tarefa.

**Sempre requerem confirmação:** apagar arquivos do projeto (fora de `build/`), modificar `legance/`/`legacy/`/`external/saltcreep/` sem autorização explícita, sobrescrever `tests/baselines/`, alterar modelos físicos fora do escopo, `git push --force`, qualquer operação sobre credenciais ou secrets.

## Leitura obrigatória antes de qualquer tarefa

```
docs/dev-log.md              ← SEMPRE, PRIMEIRO (estado atual, fase ativa, próximas tarefas)
docs/00_project_overview.md
docs/01_repository_inventory.md
docs/08_known_issues.md      ← FA01-FA04: convenções físicas invioláveis
```

O `docs/dev-log.md` contém o estado atual do projeto, fase ativa,
achados críticos da auditoria (FA01-FA04) e próximas tarefas.
**Leia-o primeiro em toda sessão.**

Para tarefas específicas:

- LOT: também leia `docs/02_lot_formulation.md`
- APB: também leia `docs/03_apb_formulation.md`
- Sal: também leia `docs/04_salt_creep_models.md`
- Migração: também leia `docs/09_migration_plan.md`
- Validação: também leia `docs/06_validation_plan.md`

## Estrutura do repositório

```
lot-salt-suite/
├── apps/lot-sim.cpp         ← Único executável
├── include/<modulo>/        ← Headers C++20 (interfaces públicas)
├── src/<modulo>/            ← Implementações C++
├── cases/                   ← Arquivos YAML de caso
├── schemas/                 ← Schemas de validação
├── tests/cpp/               ← Catch2
├── tests/python/            ← pytest
├── tests/baselines/         ← IMUTÁVEL — saídas congeladas dos legados
├── postprocess/lotsaltpost/ ← Pacote Python de pós-processamento
├── tools/                   ← Scripts utilitários
├── docs/                    ← Documentação técnica + index.html
├── legance/                 ← CONGELADO (legado físico, NÃO EDITAR)
└── external/saltcreep/      ← DEPENDÊNCIA VENDORIZADA ATIVA (EDIÇÃO CONTROLADA, NÃO DUPLICAR)
```

## Módulos C++ e suas responsabilidades

| Módulo | Responsabilidade |
|--------|-----------------|
| `core` | Tipos: Stress, Strain, StressState, VectorField |
| `io` | Parser YAML+JSON → CaseData; escritor CSV/JSON |
| `units` | Conversão PPG↔kg/m³, pol↔m, psi↔Pa, cP↔Pa·s, bar↔Pa, °F↔°C↔K |
| `wellbore` | Geometria: raio, profundidades, revestimentos, cimentações, anulares, sapata |
| `fluids` | PVT: densidade f(P,T), compressibilidade, viscosidade |
| `thermal` | Perfil T(z) analítico; futuramente condução radial 1D/2D |
| `rocks` | Elástico isotrópico; propriedades por camada litológica |
| `salt` | SaltCreepInterface + adapters para saltcreep e SESTSAL |
| `lot` | Fratura: geometrias, pressão de fratura, leakoff, curva P×V |
| `apb` | Balanço anular: pressurização, leakage, ventilação |
| `geomechanics` | Tensão geostática, pressão de poros, estado inicial |
| `coupling` | Orquestrador: LOT → sal → APB → acoplamento |
| `validation` | Carrega baseline, compara campos, calcula erros |
| `cli` | Subcomandos: run, validate, inspect, migrate |

## Convenções de codificação

- C++20; sem `using namespace std` em headers
- Smart pointers, RAII; sem `new`/`delete` em código novo
- Headers em `include/<modulo>/`; `.cpp` em `src/<modulo>/`
- Um executável principal: `apps/lot-sim.cpp`
- Eigen: `include/Eigen/` é o Eigen oficial do `lot-salt-suite`; `external/saltcreep/include/Eigen/` permanece preservado para o saltcreep
- yaml-cpp e Catch2 via FetchContent

## Formato de entrega ao final de cada tarefa

```
## Arquivos alterados
- path/to/file.cpp — motivo

## Testes executados
- ctest: N testes, N passaram

## Comparação numérica
- Campo X: erro L2 = Y%

## Riscos remanescentes
- Descrição do risco

## Documentação atualizada
- docs/XX_arquivo.md — o que foi atualizado
```
