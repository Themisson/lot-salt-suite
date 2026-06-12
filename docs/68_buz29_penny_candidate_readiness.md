# Fase 11.9B — readiness BUZ29 para rota PennyShaped

## Resumo executivo

A Fase 11.9B avalia se BUZ29 ja possui evidência suficiente para iniciar uma
rota diagnóstica `PennyShaped` moderna.

Resultado:

```text
readiness = BUZ29_PENNY_CANDIDATE_PARTIAL
gate = BUZ29_PENNY_READINESS_PARTIAL_DO_NOT_START_11_10A
can_start_11_10a = false
```

Portanto, a Fase 11.10A não deve ser executada ainda.

## Evidências presentes

| Evidência | Status |
|---|---|
| Fonte BUZ29 ativa penny-shaped | presente |
| Fórmulas penny-shaped auditadas | presente |
| Núcleo `PennyShapedModel` implementado | presente |
| Adapter diagnóstico opt-in implementado | presente |
| Caso sintético mínimo | presente |

## Evidências ausentes

| Evidência | Status |
|---|---|
| Histórico de pressão BUZ29 adequado ao adapter | ausente |
| Histórico `sigmaTheta` BUZ29 adequado ao adapter | ausente |
| Tempo desde abertura BUZ29 rastreável | ausente |
| Estado APB/sal BUZ29 alinhado ao critério legado | ausente |

## Decisão

BUZ29 é candidato parcial para a trilha `PENNY_SHAPED`, mas ainda não está
pronto para YAML diagnóstico moderno. Criar um caso BUZ29 agora exigiria
inventar ou inferir campos críticos de pressão, `sigmaTheta`, tempo desde
abertura e estado APB/sal.

## Próxima fase recomendada

```text
PHASE11_9C_COMPLETE_BUZ29_PENNY_EVIDENCE
```

Essa próxima fase deve completar a evidência BUZ29 antes de qualquer tentativa
de `PHASE11_10A_BUZ29_PENNY_DIAGNOSTIC_ROUTE`.

## Phase 11.9C evidence audit

A Fase 11.9C executou uma auditoria de evidências sem iniciar simulação BUZ29:

```text
classification = BUZ29_PENNY_EVIDENCE_PARTIAL
can_update_readiness = true
can_start_11_10a = false
recommended_next_phase = PHASE11_9D_UPDATE_BUZ29_PENNY_READINESS
```

O mapa de evidências registrou pressão como `PARTIAL`, `sigmaTheta` como
`MISSING`, tempo de abertura como `MISSING`, tempo desde abertura como
`MISSING` e estado APB/sal como `PARTIAL`. Nenhum desses campos críticos ficou
consumível para o adapter nesta fase.

## Phase 11.9D readiness update

A Fase 11.9D consumiu o mapa da 11.9C e manteve o gate fechado:

```text
updated_readiness = BUZ29_PENNY_CANDIDATE_PARTIAL
can_start_11_10A = false
gate = BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A
recommended_next_phase = PHASE11_9E_COMPLETE_BUZ29_PRESSURE_AND_OPENING_EVIDENCE
```

O status não foi promovido para rota diagnóstica segura porque pressão,
`sigmaTheta`, tempo de abertura, tempo desde abertura e inputs BUZ29 do adapter
seguem não consumíveis.

## Phase 11.9E pressure/opening evidence

A Fase 11.9E refinou a busca nos outputs legados existentes e encontrou os
dois campos mínimos que motivaram a fase:

```text
pressure_history_status = PRESSURE_HISTORY_FOUND_CONSUMABLE
opening_time_status = OPENING_TIME_FOUND_CONSUMABLE
classification = BUZ29_PRESSURE_AND_OPENING_EVIDENCE_COMPLETE
can_reopen_11_10A_gate = true
recommended_next_phase = PHASE11_9F_REEVALUATE_BUZ29_PENNY_READINESS_AFTER_PRESSURE_OPENING
```

O histórico de pressão vem de `Time` + blocos `dP` em
`7-BUZ-29D-RJS10_PENNY-SHAPED.dat`, com conversão documentada no visualizador
legado. O tempo de abertura vem do campo `Momento da quebra: 10.4`.

Essa evidência não inicia a 11.10A automaticamente. Ela apenas remove a lacuna
focal de pressão/abertura e exige uma fase 11.9F para reavaliar o readiness
com os demais campos ainda não exportados diretamente (`sigmaTheta`, `pw`,
`margin`, `opened`).

## Phase 11.9F readiness reevaluation

A Fase 11.9F consumiu a evidência de pressão e abertura da 11.9E e atualizou o
readiness:

```text
updated_readiness = BUZ29_PENNY_CANDIDATE_PARTIAL_BUT_DIAGNOSTIC_SAFE
can_start_11_10A = true
gate = BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A
recommended_next_phase = PHASE11_10A_START_BUZ29_PENNY_DIAGNOSTIC_ROUTE
```

Esse gate permite apenas iniciar a preparação diagnóstica 11.10A. Ele não cria
YAML BUZ29-PENNY, não executa BUZ29 e não valida fisicamente o caso.

Novo caveat obrigatório:

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
```

O proxy de volume do `PennyShapedModel` não deve ser tratado automaticamente
como volume circular completo em 2π.

## Caveats

- Esta fase não cria YAML BUZ29.
- Esta fase não valida BUZ29.
- Esta fase não declara equivalência com LOT_Tese.
- Esta fase não altera solver, parser, schema, CLI ou casos protegidos.
