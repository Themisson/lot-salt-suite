# 03 — Formulação do Annular Pressure Buildup (APB)

**Status:** Planejado | **Última atualização:** 2026-06-04

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

## Pressao anular e interface com sal

Para o acoplamento LOT/PKN/sal, a pressao anular relevante e a pressao
compressiva atuante na parede do sal no trecho de interesse. Ela pode se tornar
uma entrada fisicamente adequada para `SaltCreepQuery.wall_pressure_Pa` quando
estiver disponivel como pressao absoluta por tempo e profundidade.

No estado atual do projeto, o modulo APB moderno ainda nao calcula nem expoe uma
serie temporal de pressao anular. Portanto, a Fase 9.1A apenas formaliza o
contrato: pressao anular absoluta pode alimentar o sal; pressao liquida PKN nao
deve ser usada como substituto fisico sem um mapeamento explicito.

Para fases futuras, APB deve ser tratado como fonte propria de pressao anular
absoluta por tempo e profundidade, nao como uma variacao do metodo
`HydrostaticPlusNetPressure`. Se APB fornecer historico operacional validado, o
acoplamento deve preferir um metodo explicito de pressao anular, separado de
qualquer incremento `p_net` da fratura PKN.

## Parâmetros de referência (LOT_APB_v5 — hard-coded)

| Parâmetro | Valor | Fonte |
|-----------|-------|-------|
| dt | 1.0 h | `main/main.cpp` |
| ctoldP | 1.0 bar | `main/main.cpp` |
| tolEq | 1E-8 | `main/main.cpp` |
| tac (estabilização) | 80 semanas | `main/main.cpp` |

Estes parâmetros devem migrar para o YAML de caso.
