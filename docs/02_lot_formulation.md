# 02 — Formulação do Leak-Off Test (LOT)

**Status:** Planejado | **Última atualização:** 2026-06-01

> Este documento descreve a formulação matemática implementada no código legado e
> a ser reproduzida no código novo. **Não alterar formulação sem documentar aqui primeiro.**

## Conceito físico

O LOT determina a pressão de fratura hidráulica da formação adjacente à sapata
do revestimento. Fluido é bombeado no poço em taxa controlada; a pressão é monitorada
enquanto o volume injetado aumenta. O ponto de desvio na curva P×V indica abertura
da fratura.

## Diagrama de estados

`
Pressurização linear → Ponto de Leak-Off → Propagação de fratura → Fechamento
     (elástico)           (LOT_pressure)       (leakoff rate)       (closure)
`

## Formulação de fratura (a documentar após auditoria)

**Atenção:** A formulação completa deve ser extraída do código legado via skill
`/formulation-audit` e documentada aqui antes de implementar o módulo `lot/`.

Campos a documentar:
- Relação pressão-volume antes da fratura (regime elástico)
- Critério de iniciação de fratura
- Geometrias suportadas: circular, elliptical, penny-shaped, PKN
- Modelo de leakoff (filtração de fluido na parede)
- Integração com deformação da rocha salina

## Parâmetros de referência (extraídos do legado)

| Parâmetro | Valor típico | Unidade | Fonte |
|-----------|-------------|---------|-------|
| Viscosidade fluido LOT | 3.0 | cP | `setLeakoffProps("pa_min", 3., "elliptical")` |
| Profundidade sapata | 4374 | m | `8-BUZ-67D-RJS-VISCO.cpp` |

## Convenção de sinais (a verificar)

> PENDENTE — executar skill `/formulation-audit` para confirmar convenção.
