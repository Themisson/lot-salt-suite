# AGENTS.md — docs/

Documentação técnica do lot-salt-suite.

## Arquivos

| Arquivo | Conteúdo |
|---------|---------|
| `index.html` | Manual técnico interativo offline-first |
| `00_project_overview.md` | Visão geral, escopo, decisões |
| `01_repository_inventory.md` | Inventário completo |
| `02_lot_formulation.md` | Formulação matemática LOT |
| `03_apb_formulation.md` | Formulação matemática APB |
| `04_salt_creep_models.md` | Modelos constitutivos de sal |
| `05_input_output_formats.md` | Schema YAML + JSON legado |
| `06_validation_plan.md` | Sequência V0-V9 |
| `07_target_architecture.md` | Diagrama de módulos |
| `08_known_issues.md` | Problemas conhecidos |
| `09_migration_plan.md` | Plano de migração de casos |
| `10_postprocessing_plan.md` | Organização do lotsaltpost |
| `11_cli_usage.md` | Documentação da CLI |
| `12_validation_results.md` | RESULTADOS REAIS (não editar sem executar) |
| `13_coupling_lot_apb_salt.md` | Algoritmo de acoplamento |
| `14_developer_workflow.md` | Guia do desenvolvedor |
| `15_changelog.md` | Log de mudanças |
| `16_saltcreep_governance.md` | Governanca de `external/saltcreep/` como dependencia vendorizada ativa |
| `17_lot_pkn_roadmap.md` | Roadmap da migracao LOT/PKN |
| `audits/lot_legacy_inventory.md` | Inventario LOT nos legados |
| `audits/pkn_legacy_path.md` | Caminho tecnico PKN legado |
| `audits/non_pkn_models_status.md` | Status dos modelos nao PKN |

## Regras críticas

1. `12_validation_results.md` NUNCA deve declarar validações sem execução real
2. Status em `index.html` baseado em `../tools/docs_status.yaml`
3. Atualizar `index.html` via `python ../tools/generate_docs_index.py`
4. Nunca comprometer index.html com links quebrados

## Subagente recomendado

`docs-sync` para manutenção, `docs-html-report` skill para geração.
