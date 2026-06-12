# Fase 11.9E — evidência BUZ29 de pressão e abertura

## Resumo executivo

A Fase 11.9E auditou, em modo somente leitura, se existem evidências mínimas
de pressão e abertura para o caso `BUZ29-VISCO-first-well` na rota
`PENNY_SHAPED`.

Resultado:

```text
pressure_history_status = PRESSURE_HISTORY_FOUND_CONSUMABLE
opening_time_status = OPENING_TIME_FOUND_CONSUMABLE
classification = BUZ29_PRESSURE_AND_OPENING_EVIDENCE_COMPLETE
can_reopen_11_10A_gate = true
recommended_next_phase = PHASE11_9F_REEVALUATE_BUZ29_PENNY_READINESS_AFTER_PRESSURE_OPENING
```

A 11.9E não executa BUZ29-PENNY, não cria YAML candidato e não valida BUZ29. Ela apenas audita se existem histórico de pressão e evidência de abertura consumíveis para reavaliar o gate.

## Contexto pós-11.9D

A Fase 11.9D manteve o readiness BUZ29-PENNY como parcial:

```text
updated_readiness = BUZ29_PENNY_CANDIDATE_PARTIAL
can_start_11_10A = false
gate = BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A
recommended_next_phase = PHASE11_9E_COMPLETE_BUZ29_PRESSURE_AND_OPENING_EVIDENCE
```

A lacuna focal da 11.9E era decidir se o repositório já continha evidência
legada suficiente para histórico de pressão e tempo de abertura, sem
instrumentar `legance/`.

## Fontes analisadas

| Fonte | Uso |
|---|---|
| `legance/LOT_Tese/BUZ29-VISCO-first-well.cpp` | Fonte legada principal, somente leitura. |
| `legance/LOT_Tese/results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat` | Output legado BUZ29 penny-shaped com `Time`, blocos `dP`, `dV_leakoff`, `V_outflow` e `Momento da quebra`. |
| `legance/LOT_Tese/PressureDataVisualizer29D-RAA.py` | Script legado que documenta a conversão de `dP` para psi e o offset `initPressure`. |
| `docs/57_buz29_visco_first_well_audit.md` | Auditoria do caso BUZ29 first-well. |
| `docs/58_non_pkn_model_roadmap.md` | Roadmap não-PKN. |
| `docs/68_buz29_penny_candidate_readiness.md` | Readiness prévio BUZ29-PENNY. |
| `docs/70_buz29_penny_evidence_audit.md` | Auditoria de evidência da 11.9C. |
| `docs/71_buz29_penny_readiness_update.md` | Gate de readiness da 11.9D. |
| `tools/audit_phase11_9c_buz29_penny_evidence.py` | Ferramenta de auditoria anterior. |
| `tools/update_phase11_9d_buz29_penny_readiness.py` | Ferramenta de atualização do gate anterior. |

## Evidência de pressão encontrada

O arquivo:

```text
legance/LOT_Tese/results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat
```

contém:

- vetor `Time` com 131 pontos de `0.0` a `13.0`;
- blocos `dP` por camada;
- blocos `dV_leakoff`;
- `V_outflow`.

O script `PressureDataVisualizer29D-RAA.py` usa:

```text
dPa = dP * 0.000145038
dPa[0, :] += initialPressure
```

e a fonte BUZ29 define:

```text
initPressure = "70.0"
```

Assim, a série de pressão é classificada como:

```text
PRESSURE_HISTORY_FOUND_CONSUMABLE
```

Ela é consumível como evidência para reavaliar readiness, não como validação
física nem como entrada runtime aprovada.

## Evidência de abertura/fratura encontrada

O mesmo `.dat` contém no final:

```text
Momento da quebra: 10.4
```

Esse valor é emitido pelo legado a partir de
`APB1da::checkPwAndSaveTime()` e usa a mesma escala temporal em minutos do
vetor `Time`. A auditoria também encontrou `dV_leakoff` positivo após o evento,
como evidência auxiliar de comportamento pós-abertura.

Status:

```text
OPENING_TIME_FOUND_CONSUMABLE
```

## Campos consumíveis

| Campo | Status | Valor/observação |
|---|---|---|
| Histórico de tempo | Consumível | `Time = 0.0 ... 13.0 min`, 131 pontos |
| Histórico de pressão | Consumível | `dP` por camada, com conversão documentada para psi no visualizador |
| Pressão inicial gráfica | Consumível como metadado | `initPressure = 70.0 psi` |
| Tempo de abertura | Consumível | `Momento da quebra = 10.4 min` |
| Primeiro `dV_leakoff` positivo | Auxiliar | detectado em `10.4 min` no output auditado |

## Campos não consumíveis

| Campo | Status | Observação |
|---|---|---|
| `sigmaTheta` BUZ29 | Não consumível nesta fase | O `.dat` não exporta série `sigmaTheta`; esta fase não instrumenta o legado. |
| `pw`, `margin`, `opened` explícitos | Não consumíveis nesta fase | O output contém `dP` e tempo de quebra, mas não exporta esses campos diretamente. |
| YAML BUZ29-PENNY candidato | Não criado | A 11.9E apenas reabre o gate para reavaliação futura. |

## Gaps bloqueantes

Para o escopo focal da 11.9E, os dois gaps mínimos foram removidos:

```text
pressure_history = consumable
opening_time = consumable
```

Ainda permanecem lacunas para uma rota BUZ29-PENNY executável:

- `sigmaTheta` BUZ29 não foi exportado diretamente;
- `pw`, `margin` e `opened` não foram exportados diretamente;
- o contrato completo do adapter ainda precisa ser reavaliado na 11.9F;
- nenhum YAML BUZ29-PENNY candidato deve ser criado nesta fase.

## Classificação final

```text
BUZ29_PRESSURE_AND_OPENING_EVIDENCE_COMPLETE
```

## Decisão sobre o gate da 11.10A

```text
can_reopen_11_10A_gate = true
```

Isso não inicia a 11.10A. A próxima etapa deve reavaliar formalmente o
readiness usando esta evidência nova.

## Próxima fase recomendada

```text
PHASE11_9F_REEVALUATE_BUZ29_PENNY_READINESS_AFTER_PRESSURE_OPENING
```

Essa fase deve decidir se a evidência de pressão e abertura é suficiente para
promover BUZ29 de candidato parcial para rota diagnóstica segura, ou se os
campos restantes (`sigmaTheta`, `pw`, `margin`, `opened`) ainda bloqueiam a
11.10A.

## Caveats

- Esta fase não executa simulação BUZ29.
- Esta fase não cria YAML BUZ29-PENNY candidato.
- Esta fase não valida BUZ29 fisicamente.
- Esta fase não altera `legance/`, `legacy/`, `external/saltcreep/`, C++,
  parser, schema, CLI, `PknModel`, `PknRunner` ou casos protegidos.
