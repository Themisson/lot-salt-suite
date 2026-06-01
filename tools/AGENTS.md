# AGENTS.md — tools/

Scripts utilitários: migração, inspeção, geração de documentação.

## Arquivos esperados

| Script | Função |
|--------|--------|
| `migrate_lot_apb_json_to_yaml.py` | Converter JSON legado → YAML |
| `migrate_lot_tese_cpp_case.py` | Extrair parâmetros de main.cpp → YAML |
| `compare_results.py` | Comparar dois conjuntos de resultados |
| `generate_docs_index.py` | Regenerar docs/index.html |
| `inspect_case.py` | Validar YAML contra schema |
| `run_baselines.py` | Executar suíte completa de regressão |
| `docs_status.yaml` | Fonte de verdade para status do index.html |

## Regras

1. Scripts de migração não modificam arquivos legados — apenas criam arquivos novos
2. `docs_status.yaml` é fonte única de verdade para status de seções do index.html
3. Não hardcode de caminhos absolutos
4. Todo script deve ter `--help` funcional
5. Toda ferramenta deve ter pelo menos um teste pytest
