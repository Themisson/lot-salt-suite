# AGENTS.md — lot-salt-suite

Este repositório integra simuladores de Leak-Off Test (LOT), Annular Pressure Buildup (APB)
e fluência de sal (Salt Creep). O código principal é C++20. O pós-processamento é Python.

## Contexto para agentes de código

Você está trabalhando em um projeto de simulação de poços de petróleo de alta complexidade.
O repositório tem três bases: código legado da tese (`legance/LOT_Tese/`), versão mais
moderna com JSON (`legance/LOT_APB_v5/`) e um solver FEM moderno de sal (`external/saltcreep/`).

O objetivo é criar código novo nos diretórios `src/`, `include/`, `apps/`, `cases/` etc.,
**sem modificar nenhum arquivo legado**.

## Regras invioláveis para agentes

1. **PROIBIDO** editar qualquer arquivo em `legance/` ou `external/saltcreep/`.
2. **PROIBIDO** apagar arquivos existentes.
3. **PROIBIDO** mudar formulação física sem documentar em `docs/08_known_issues.md`.
4. **PROIBIDO** declarar validações como executadas em `docs/12_validation_results.md` sem rodar.
5. **PROIBIDO** copiar código de `external/saltcreep/src/` para `src/salt/` — use interface/adapter.
6. **PROIBIDO** misturar lógica de solver com parsing de entrada no mesmo arquivo.
7. **OBRIGATÓRIO** criar testes Catch2 para todo módulo C++ novo.
8. **OBRIGATÓRIO** validar YAML de caso contra schema antes de commitar.
9. **OBRIGATÓRIO** converter todas as unidades de campo para SI no parser (não no solver).
10. **OBRIGATÓRIO** informar arquivos alterados, testes executados e riscos ao final da tarefa.

## Leitura obrigatória antes de qualquer tarefa

```
docs/00_project_overview.md
docs/01_repository_inventory.md
docs/08_known_issues.md
```

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
└── external/saltcreep/      ← REFERÊNCIA (NÃO EDITAR, NÃO DUPLICAR)
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
- Eigen: referenciar de `external/saltcreep/include/Eigen/` via CMakeLists.txt
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
