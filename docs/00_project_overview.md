# 00 — Visão Geral do Projeto

**Status:** Planejado | **Última atualização:** 2026-06-01

## Objetivo

O `lot-salt-suite` integra três bases de código para criar um simulador modular de:

- **Leak-Off Test (LOT)** — determinação de pressão de fratura em poços
- **Annular Pressure Buildup (APB)** — pressurização de anulares selados
- **Fluência de sal (Salt Creep)** — comportamento viscoelástico de rochas salinas

## Motivação

O código da tese (`legance/LOT_Tese/`) usa múltiplos arquivos `main.cpp` como "casos de simulação",
com parâmetros físicos inteiramente hard-coded. Isso impossibilita automação, versionamento de casos
e validação sistemática. A versão `LOT_APB_v5/` melhorou com entrada JSON, mas o solver ainda
mistura múltiplas responsabilidades em uma única classe (`APB1da`).

## Bases do projeto

| Base | Localização | Papel |
|------|------------|-------|
| LOT_Tese | `legance/LOT_Tese/` | Referência histórica — CONGELADA |
| LOT_APB_v5 | `legance/LOT_APB_v5/` | Base principal de migração — CONGELADA |
| saltcreep | `external/saltcreep/` | Referência de sal/FEM — NÃO DUPLICAR |

## Decisões arquiteturais

1. **YAML como formato principal** de caso; JSON aceito por compatibilidade
2. **Executável único** `lot-sim` com subcomandos e flags
3. **Interface/adapter** para integrar saltcreep sem duplicar código
4. **Baselines obrigatórios** antes de qualquer refatoração
5. **SI internamente** — conversões somente no parser (`include/units/`)

## Leitura recomendada

- [docs/07_target_architecture.md](07_target_architecture.md) — módulos e interfaces
- [docs/02_lot_formulation.md](02_lot_formulation.md) — física do LOT
- [docs/06_validation_plan.md](06_validation_plan.md) — sequência de validação
