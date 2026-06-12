# Fase 11.9C — auditoria de evidência BUZ29-PENNY

## Resumo executivo

A Fase 11.9C auditou as fontes documentais e legadas disponíveis para decidir
se BUZ29 pode avançar para uma rota diagnóstica `PennyShaped`.

Resultado:

```text
classification = BUZ29_PENNY_EVIDENCE_PARTIAL
can_update_readiness = true
can_start_11_10a = false
recommended_next_phase = PHASE11_9D_UPDATE_BUZ29_PENNY_READINESS
```

A 11.9C não inicia a rota BUZ29-PENNY e não executa simulação. Ela apenas audita se há evidência suficiente para atualizar o readiness.

## Objetivo

O objetivo foi organizar as evidências faltantes apontadas pela 11.9B:
histórico de pressão, histórico de `sigmaTheta`, tempo de abertura, tempo desde
abertura, estado APB/sal e campos consumíveis pelo adapter diagnóstico.

## Fontes analisadas

| Fonte | Uso na auditoria |
|---|---|
| `legance/LOT_Tese/BUZ29-VISCO-first-well.cpp` | fonte legada principal, somente leitura |
| `legance/LOT_Tese/PressureDataVisualizer29D-RAA.py` | indício de leitura/plot de pressão 29D |
| `docs/57_buz29_visco_first_well_audit.md` | auditoria BUZ29 anterior |
| `docs/61_selected_non_pkn_model_math_audit.md` | fórmulas penny-shaped auditadas |
| `docs/66_penny_diagnostic_adapter_implementation.md` | adapter diagnóstico disponível |
| `docs/68_buz29_penny_candidate_readiness.md` | readiness anterior da 11.9B |
| `cases/validation/non_pkn/penny_shaped_synthetic_minimal.yaml` | caso sintético mínimo, não BUZ29 |

## Mapa de evidências

| Campo | Status | Consumível? | Fonte | Observação |
|---|---|---:|---|---|
| `pressure_history` | `PARTIAL` | `false` | `PressureDataVisualizer29D-RAA.py` | há ferramenta legada de visualização, mas não há histórico BUZ29 normalizado para o adapter |
| `sigmaTheta_history` | `MISSING` | `false` | readiness 11.9B | não há série BUZ29 consumível |
| `opening_time` | `MISSING` | `false` | readiness 11.9B | não há instante rastreável de abertura/fratura |
| `time_since_opening` | `MISSING` | `false` | readiness 11.9B | campo crítico para `elapsed_since_opening_min` permanece ausente |
| `apb_salt_state` | `PARTIAL` | `false` | auditoria BUZ29 11.6A | há setup APB, mas não trace alinhado ao critério |
| `fracture_state` | `PARTIAL` | `false` | auditoria BUZ29 11.6A | modelo ativo é penny-shaped, mas sem estado moderno consumível |
| `leakoff_state` | `PARTIAL` | `false` | fonte legada | há indícios de configuração, mas sem série normalizada |
| `fluid_state` | `PARTIAL` | `false` | auditoria BUZ29 11.6A | fluido foi parcialmente auditado, mas não fecha o contrato do adapter |
| `wellbore_geometry` | `PARTIAL` | `false` | auditoria BUZ29 11.6A | intervalo existe, contrato completo ainda não |
| `elastic_properties` | `PARTIAL` | `false` | auditoria matemática 11.7B | fórmulas existem, valores BUZ29 não estão empacotados |
| `penny_inputs` | `PARTIAL` | `false` | adapter + caso sintético | infraestrutura existe, mas faltam campos BUZ29 críticos |
| `legacy_trace` | `PARTIAL` | `false` | auditoria BUZ29 11.6A | saída legada é citada, mas não normalizada |

## Evidências encontradas

- Fonte primária BUZ29 first-well existe.
- O modelo ativo foi previamente identificado como `penny-shaped`.
- Fórmulas penny-shaped foram auditadas.
- Núcleo e adapter diagnóstico existem.
- Existe caso sintético mínimo, mas ele não valida BUZ29.

## Evidências parciais

- Pressão: há material legado de visualização/plot, mas não um histórico
  versionado e mapeado para o adapter.
- Estado APB/sal: o setup está documentado, mas falta trace consumível.
- Fluido, geometria e propriedades: existem parcialmente em auditorias
  anteriores, sem fechamento de contrato BUZ29-PENNY.

## Evidências ausentes

- Histórico `sigmaTheta` BUZ29.
- Tempo de abertura/fratura.
- Tempo desde abertura.
- Série alinhada de pressão, `sigmaTheta`, abertura e estado APB/sal.

## Gaps bloqueantes

```text
opening_time
penny_inputs
pressure_history
sigmaTheta_history
time_since_opening
```

## Classificação final

```text
BUZ29_PENNY_EVIDENCE_PARTIAL
```

A evidência permite atualizar o readiness na 11.9D, mas não permite iniciar a
11.10A nesta fase.

## Recomendação para 11.9D

A 11.9D deve consumir este mapa de evidência e manter o gate da 11.10A fechado,
a menos que uma regra explícita de diagnóstico parcial seguro seja satisfeita.

## Atualização 11.9D

A Fase 11.9D consumiu este mapa e registrou:

```text
updated_readiness = BUZ29_PENNY_CANDIDATE_PARTIAL
gate = BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A
can_start_11_10A = false
```

Como `pressure_history`, `opening_time` e `penny_inputs` não estão consumíveis,
a rota 11.10A permanece bloqueada.

## Atualização 11.9E

A Fase 11.9E aprofundou especificamente a busca por pressão e abertura no
output legado BUZ29 penny-shaped e encontrou evidência consumível para ambos:

```text
pressure_history_status = PRESSURE_HISTORY_FOUND_CONSUMABLE
opening_time_status = OPENING_TIME_FOUND_CONSUMABLE
classification = BUZ29_PRESSURE_AND_OPENING_EVIDENCE_COMPLETE
can_reopen_11_10A_gate = true
```

A fonte principal é
`legance/LOT_Tese/results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat`, que contém a série
`Time`, blocos `dP` e o marcador `Momento da quebra: 10.4`. O documento
detalhado está em `docs/72_buz29_pressure_opening_evidence_audit.md`.

Essa atualização não executa BUZ29-PENNY, não cria YAML candidato e não valida
fisicamente o caso. Ela recomenda a 11.9F para reavaliar readiness antes de
qualquer 11.10A.

## Atualização 11.9F

A Fase 11.9F reavaliou o readiness com a evidência consumível da 11.9E:

```text
updated_readiness = BUZ29_PENNY_CANDIDATE_PARTIAL_BUT_DIAGNOSTIC_SAFE
can_start_11_10A = true
gate = BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A
recommended_next_phase = PHASE11_10A_START_BUZ29_PENNY_DIAGNOSTIC_ROUTE
```

A decisão é estritamente diagnóstica. `sigmaTheta`, `pw`, `margin` e `opened`
continuam não exportados diretamente no `.dat`, e o caveat
`PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED` impede interpretar o
proxy de volume como volume circular completo em 2π sem auditoria matemática.
