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

**Atenção:** A formulação completa PKN ainda não está validada contra o legado
porque R09 permanece blocker para regressão numérica. A Fase 6.2 cria apenas o
contrato de entrada, os tipos C++ e testes sintéticos.

Campos a documentar:
- Relação pressão-volume antes da fratura (regime elástico)
- Critério de iniciação de fratura
- Geometrias suportadas: circular, elliptical, penny-shaped, PKN
- Modelo de leakoff (filtração de fluido na parede)
- Integração com deformação da rocha salina

## Contrato LOT/PKN sintético (Fase 6.2)

O caminho moderno inicial usa `simulation.mode: lot-pkn`, `lot.model: pkn` e
`lot.fracture.geometry: pkn`. O parser converte taxa de injecao, tempos,
comprimentos e pressao de breakdown para SI antes de preencher `CaseData`.

Campos principais:

| Campo | Unidade interna | Observacao |
|-------|-----------------|------------|
| `lot.injection.rate` | m3/s | Aceita `m3_s`, `m3_min`, `m3_h`, `bbl_min` e `bpm`. |
| `lot.injection.schedule.total_time` | s | Tempo total do contrato LOT/PKN. |
| `lot.injection.schedule.dt` | s | Passo coerente com a taxa usada pelo modelo. |
| `lot.injection.schedule.accommodation_time` | s | Tempo sem injecao/variacao operacional antes do carregamento. |
| `lot.fracture.height` | m | Altura PKN de entrada; no legado pode ser calculada e esta sob revisao. |
| `lot.fracture.initial_width` | m | Largura inicial sintética. |
| `lot.fracture.breakdown.pressure` | Pa | Limiar do detector por pressao, quando usado. |

O detector `derivative_drop` opera em series sintéticas `time_s`,
`volume_m3` e `pressure_Pa`. Ele nao usa resultados legados.

## Parâmetros de referência (extraídos do legado)

| Parâmetro | Valor típico | Unidade | Fonte |
|-----------|-------------|---------|-------|
| Viscosidade fluido LOT | 3.0 | cP | `setLeakoffProps("pa_min", 3., "pkn")` em casos PKN auditados |
| Profundidade sapata | 4374 | m | `8-BUZ-67D-RJS-VISCO.cpp` |

## Convenção de sinais

Compressao positiva, conforme FA03 em `docs/08_known_issues.md`.
