# lot-salt-suite

Simulador integrado de **Leak-Off Test (LOT)**, **Annular Pressure Buildup (APB)**
e **fluência de sal (Salt Creep)** para poços de petróleo em formações salinas.

## Visão geral

Este repositório moderniza e integra três bases de código C++ em uma arquitetura
modular com:

- Executável único `lot-sim` com subcomandos (`run`, `validate`, `inspect`, `migrate`)
- Casos de simulação definidos em YAML (compatibilidade com JSON legado)
- Separação clara entre: geometria de poço, fluidos, rochas, sal, LOT, APB, térmico
- Testes de regressão contra os códigos legados da tese
- Integração com [saltcreep](external/saltcreep/) por interface adaptadora
- Pós-processamento Python no pacote `postprocess/lotsaltpost/`
- Documentação técnica navegável em [docs/index.html](docs/index.html)

## Estrutura principal

```
lot-salt-suite/
├── apps/               # Executável lot-sim
├── include/            # Headers C++20
├── src/                # Implementações C++
├── cases/              # Arquivos YAML de caso
├── schemas/            # Schemas de validação
├── tests/              # Catch2 + pytest + baselines
├── postprocess/        # Pacote lotsaltpost (Python)
├── tools/              # Scripts utilitários e migração
├── docs/               # Documentação técnica + index.html
├── legance/            # Legado congelado (LOT_Tese, LOT_APB_v5)
└── external/saltcreep/ # Dependência vendorizada ativa — edição controlada por tarefa explícita, testes e dev-log
```

## Início rápido

```bash
# Compilar (requer CMake 3.20+, compilador C++20)
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build -j

# Inspecionar um caso
./build/lot-sim inspect --case cases/validation/lot_simple.yaml

# Executar um caso
./build/lot-sim run --case cases/lot_apb_v5_migrated/score_mro_28.yaml --mode apb

# Migrar JSON legado para YAML
./build/lot-sim migrate --from-json legance/LOT_APB_v5/SCORE-MRO-28_input.json \
                        --to-yaml cases/lot_apb_v5_migrated/score_mro_28.yaml

# Executar validação de regressão
./build/lot-sim validate --suite regression

# Pós-processamento
cd postprocess && pip install -e .
lotsaltpost run postprocess/scripts/plot_lot_curve.py
```

## Bases legadas

| Base | Localização | Status |
|------|------------|--------|
| LOT_Tese | `legance/LOT_Tese/` | Congelado — referência histórica |
| LOT_APB_v5 | `legance/LOT_APB_v5/` | Congelado — referência principal |
| saltcreep | `external/saltcreep/` | Referência moderna — não duplicar |

> As bases legadas **não devem ser editadas**. Ver `CLAUDE.md` para regras completas.

## Documentação

- [Visão geral do projeto](docs/00_project_overview.md)
- [Inventário do repositório](docs/01_repository_inventory.md)
- [Formulação LOT](docs/02_lot_formulation.md)
- [Formulação APB](docs/03_apb_formulation.md)
- [Modelos de sal](docs/04_salt_creep_models.md)
- [Formatos de entrada/saída](docs/05_input_output_formats.md)
- [Plano de validação](docs/06_validation_plan.md)
- [Arquitetura-alvo](docs/07_target_architecture.md)
- [Problemas conhecidos](docs/08_known_issues.md)
- [Plano de migração](docs/09_migration_plan.md)
- [Manual interativo](docs/index.html)

## Fases do projeto

| Fase | Descrição | Status |
|------|-----------|--------|
| 0 | Inventário e preservação | Concluída |
| 1 | Estrutura do repositório | Em andamento |
| 2 | Documentação e index.html inicial | Em andamento |
| 3 | Agentes e skills | Em andamento |
| 4 | Baselines e regressão | Planejado |
| 5 | CLI e formatos de entrada | Planejado |
| 6 | Migração de casos legados | Planejado |
| 7 | Refatoração C++ | Planejado |
| 8 | Integração com saltcreep | Planejado |
| 9 | Pós-processamento | Planejado |
| 10 | Validação avançada | Planejado |
| 11 | Empacotamento e documentação final | Planejado |
| 12 | Publicação no GitHub | Planejado |

## Contribuindo

Leia obrigatoriamente `CLAUDE.md` (para Claude Code) ou `AGENTS.md` (para Codex)
antes de qualquer modificação.
