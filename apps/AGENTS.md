# AGENTS.md — apps/

Contém apenas o executável principal `lot-sim.cpp`.

## Regras

1. `apps/lot-sim.cpp` deve ser mínimo: parse de CLI e chamada para módulos
2. Toda lógica deve estar em `src/cli/` ou nos módulos respectivos
3. Sem parâmetros físicos em `apps/`
4. Sem includes de `legance/` ou `external/saltcreep/`

## Estrutura de lot-sim.cpp

`cpp
int main(int argc, char* argv[]) {
    auto cmd = cli::parse(argc, argv);
    return cmd->execute();
}
`
"@

"cases\AGENTS.md" = @"
# AGENTS.md — cases/

Arquivos YAML de caso de simulação.

## Estrutura

`
cases/
├── lot_tese_migrated/   # YAMLs convertidos dos main.cpp da tese
├── lot_apb_v5_migrated/ # YAMLs convertidos dos JSONs do LOT_APB_v5
├── validation/          # Casos analíticos de validação
└── coupled/             # Casos LOT-APB-sal acoplados
`

## Regras

1. Todo YAML deve passar na validação do schema em `schemas/`
2. Todo YAML migrado deve ter campo `metadata.legacy_source`
3. Todo YAML deve ter campo `metadata.mode` especificado
4. Parâmetros físicos nunca em unidades mistas no mesmo arquivo
5. Preferir SI; usar campo `units:` para declarar unidades de entrada

## Como criar um novo caso

`ash
lot-sim inspect --case cases/meu_caso.yaml  # validar schema
lot-sim run --case cases/meu_caso.yaml --mode lot  # executar
`
"@

"schemas\AGENTS.md" = @"
# AGENTS.md — schemas/

Schemas de validação YAML/JSON para casos do lot-salt-suite.

## Regras

1. Schema é imutável sem aprovação explícita
2. Mudança de schema = versão nova (campo `schema_version`)
3. Não remover campos sem ciclo de deprecação documentado
4. Todo campo obrigatório deve ter exemplo em docs/05_input_output_formats.md

## Arquivos esperados

- `lot_case.schema.yaml` — schema principal do caso
- `apb_case.schema.yaml` — extensão para campos APB
- `material.schema.yaml` — propriedades de material
- `output.schema.json` — formato de saída

## Validação

`ash
python tools/inspect_case.py --schema schemas/lot_case.schema.yaml --case cases/exemplo.yaml
`
"@

"tests\AGENTS.md" = @"
# AGENTS.md — tests/

Testes unitários, de regressão e baselines.

## Estrutura

`
tests/
├── cpp/         # Catch2 — testes C++
├── python/      # pytest — testes Python
├── regression/  # Scripts de comparação automática
└── baselines/   # IMUTÁVEL — saídas congeladas dos legados
`

## Regras críticas

1. `tests/baselines/` é IMUTÁVEL — alterar apenas com aprovação explícita
2. Nunca relaxar tolerância de regressão sem aprovação
3. Testes de regressão devem comparar contra baseline, não contra resultado atual
4. Toda tarefa C++ finalizada deve ter ctest 100% verde
5. Toda tarefa Python finalizada deve ter pytest 100% verde

## Como executar

`ash
cmake --build build -j && ctest --test-dir build --output-on-failure
pytest tests/python -q
`

## Subagente recomendado

`verifier` — roda testes antes de declarar conclusão.
`validation-benchmark` — para criação e análise de baselines.
