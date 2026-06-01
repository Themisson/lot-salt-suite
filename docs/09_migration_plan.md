# 09 — Plano de Migração

**Status:** Planejado | **Última atualização:** 2026-06-01

## Ordem de migração de casos

| Prioridade | Caso | Tipo | Destino |
|-----------|------|------|---------|
| 1 | SCORE-MRO-28_input.json | APB completo | cases/lot_apb_v5_migrated/ |
| 2 | 8-BUZ-67D-RJS-VISCO-elliptical.cpp | LOT+APB+Sal | cases/lot_tese_migrated/ |
| 3 | LOTTeste.cpp | LOT simples | cases/lot_tese_migrated/ |
| 4 | BUZ29-VISCO-DELL_PC_APTO.cpp | APB validação | cases/lot_tese_migrated/ |
| 5 | Demais BUZ29-* | APB+Sal cenários | cases/lot_tese_migrated/ |

## Mapeamento JSON → YAML (LOT_APB_v5)

| Campo JSON | Campo YAML | Transformação |
|-----------|-----------|--------------|
| `duration` | `time.total_h` | Converter `duration_unit` → horas |
| `airgap` | `wellbore.airgap_m` | Direto se metros |
| `temperature.data[].md[]` | `temperature.data[].depth_m[]` | Renomear |
| `solids[]` | `casings[]` + `cements[]` | Separar por tipo |
| `top_packer` | `apb.top_packer_m` | Mover para seção APB |
| `salt_creep_enabled` | `salt.enabled` | Renomear |
| `id_operation` | `metadata.legacy_id` | Preservar como referência |

## Parâmetros hard-coded a adicionar ao YAML

Os seguintes parâmetros estão no `main.cpp` do LOT_APB_v5 e precisam ir para YAML:

`yaml
time:
  solver:
    tol_pressure_bar: 1.0      # ctoldP
    tol_eq: 1.0e-8             # tolEq
    stabilization_days: 1.0    # dtac
    dt_h: 1.0                  # dt
  scheme: explicit             # adaptative = false
`

## Processo de validação de migração

1. Capturar baseline do legado
2. Criar YAML com campos mapeados
3. Executar novo código com YAML
4. Comparar contra baseline (tolerância: L2 < 1%)
5. Documentar em docs/12_validation_results.md
