# 03 — Formulação do Annular Pressure Buildup (APB)

**Status:** Planejado | **Última atualização:** 2026-06-01

> Formulação a extrair do legado via `/formulation-audit` antes de implementar módulo `apb/`.

## Conceito físico

O APB ocorre em anulares selados quando o fluido se expande devido ao aumento de
temperatura. A pressão aumenta porque o anular tem volume constante.

## Balanço de massa no anular (a documentar)

Campos a documentar:
- Equação de balanço de massa (compressibilidade do fluido × sólidos)
- Termo de temperatura (dilatação térmica)
- Leakage (vazamento pelo packer ou cimentação)
- Ventilação (venting controlado)
- Integração com deformação viscoelástica do sal

## Parâmetros de referência (LOT_APB_v5 — hard-coded)

| Parâmetro | Valor | Fonte |
|-----------|-------|-------|
| dt | 1.0 h | `main/main.cpp` |
| ctoldP | 1.0 bar | `main/main.cpp` |
| tolEq | 1E-8 | `main/main.cpp` |
| tac (estabilização) | 80 semanas | `main/main.cpp` |

Estes parâmetros devem migrar para o YAML de caso.
