# Phase 11.7A next model track decision

## Resumo executivo

A Fase 11.7A consolida a auditoria BUZ29-VISCO-first-well e o roadmap não-PKN
para escolher a primeira trilha técnica fora do PKN.

Resultado:

```text
status = NEXT_MODEL_TRACK_SELECTED
selected_track = PENNY_SHAPED
recommended_next_phase = PHASE11_7B_LEGACY_MATH_AUDIT_SELECTED_MODEL
```

A decisão da 11.7A seleciona uma trilha técnica prioritária. Ela não implementa
modelo físico novo e não declara validação física do BUZ29.

## Evidência considerada

| Fonte | Evidência |
|---|---|
| `docs/57_buz29_visco_first_well_audit.md` | BUZ29 first-well existe, mas o modelo ativo é `penny-shaped`; a linha PKN está comentada. |
| `docs/58_non_pkn_model_roadmap.md` | A rota prioritária não-PKN recomendada é `penny_shaped`. |
| `docs/59_summary_fracture_leakoff_maxima.md` | Summaries LOT/PKN já expõem máximos úteis para diagnósticos futuros. |
| `docs/56_buz67d_modern_refined_sensitivity_consolidation.md` | BUZ-67D segue como rota LOT/PKN modern-refined executável. |
| `docs/44_stage11_parametric_infrastructure_plan.md` | Etapa 11 continua separando infraestrutura diagnóstica de mudanças de solver. |

## Resultado da auditoria BUZ29

```text
buz29_classification = BUZ29_VISCO_FIRST_WELL_NOT_PKN
modern_pkn_ready = false
active_model = PENNY_SHAPED
pkn_evidence = COMMENT_ONLY
```

Isso bloqueia `BUZ29_PKN_YAML` como próxima trilha imediata.

## Trilhas candidatas

| Trilha | Status | Justificativa |
|---|---|---|
| `PENNY_SHAPED` | `SELECTED` | É o modelo ativo auditado em BUZ29-VISCO-first-well. |
| `BUZ29_PKN_YAML` | `BLOCKED` | A evidência PKN é comentada ou output-only. |
| `KGD_CIRCULAR` | `DEFERRED` | Aparece em variantes relacionadas, mas não é o driver ativo do first-well. |
| `KGD_ELLIPTICAL` | `DEFERRED` | Deve permanecer trilha opcional separada. |
| `ZAMORA_COMPOSITIONAL_FLUID` | `BLOCKED` | Exige gate próprio de modelo de fluido. |

## Trilha escolhida

```text
PENNY_SHAPED
```

## Justificativa técnica

Selecionar `PENNY_SHAPED` preserva a evidência observada no legado e evita
converter BUZ29 para PKN por conveniência. A próxima etapa correta é auditar a
matemática penny-shaped antes de qualquer especificação YAML oficial ou C++.

## Riscos

- A formulação penny-shaped pode depender de convenções legadas ainda não
  isoladas.
- O caso BUZ29 pode misturar efeitos de fratura, fluido e sal que devem
  permanecer separados.
- Um núcleo mínimo moderno só deve ser implementado se a auditoria matemática
  da 11.7B extrair equações e unidades suficientes.

## Próxima fase recomendada

```text
PHASE11_7B_LEGACY_MATH_AUDIT_SELECTED_MODEL
```
