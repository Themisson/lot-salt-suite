# Fase 11.9F — readiness BUZ29-PENNY após pressão e abertura

## Resumo executivo

A Fase 11.9F reavaliou o readiness BUZ29-PENNY após a evidência consumível de
pressão e abertura encontrada na 11.9E.

Resultado:

```text
previous_readiness = BUZ29_PENNY_CANDIDATE_PARTIAL
updated_readiness = BUZ29_PENNY_CANDIDATE_PARTIAL_BUT_DIAGNOSTIC_SAFE
can_start_11_10A = true
gate = BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A
recommended_next_phase = PHASE11_10A_START_BUZ29_PENNY_DIAGNOSTIC_ROUTE
axisymmetric_interpretation = PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
```

A 11.9F não executa BUZ29-PENNY, não cria YAML candidato e não valida BUZ29. Ela apenas reavalia o readiness após a evidência consumível de pressão e abertura encontrada na 11.9E.

## Contexto pós-11.9E

A Fase 11.9E encontrou evidência consumível para os dois bloqueios focais que
impediam a reavaliação do gate:

```text
pressure_history_status = PRESSURE_HISTORY_FOUND_CONSUMABLE
opening_time_status = OPENING_TIME_FOUND_CONSUMABLE
classification = BUZ29_PRESSURE_AND_OPENING_EVIDENCE_COMPLETE
can_reopen_11_10A_gate = true
```

A fonte é:

```text
legance/LOT_Tese/results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat
```

Esse output contém:

- `Time`, com 131 pontos de 0 a 13 min;
- blocos `dP`;
- blocos `dV_leakoff`;
- `V_outflow`;
- `Momento da quebra: 10.4`.

O visualizador legado `PressureDataVisualizer29D-RAA.py` documenta a conversão
de pressão usada no pós-processamento histórico:

```text
dPa = dP * 0.000145038
dPa[0, :] += initialPressure
```

## Readiness anterior

A Fase 11.9D havia registrado:

```text
updated_readiness = BUZ29_PENNY_CANDIDATE_PARTIAL
can_start_11_10A = false
gate = BUZ29_PENNY_PARTIAL_DO_NOT_START_11_10A
recommended_next_phase = PHASE11_9E_COMPLETE_BUZ29_PRESSURE_AND_OPENING_EVIDENCE
```

Naquele momento, pressão e abertura ainda não estavam consumíveis. A 11.9E
removeu essa lacuna focal.

## Evidência de pressão consumível

O histórico `Time` + blocos `dP` do `.dat` legado é suficiente para preparar
uma rota diagnóstica futura. Esse uso continua limitado:

- não é entrada runtime aprovada;
- não é validação física;
- não estabelece equivalência com o legado;
- não altera `lot-pkn`.

## Evidência de abertura consumível

O campo:

```text
Momento da quebra: 10.4
```

é consumível como marcador legado de abertura/fratura para preparação
diagnóstica. Em segundos:

```text
10.4 min = 624 s
```

Esse marcador não autoriza, por si só, calibração física ou equivalência
numérica.

## Campos ainda ausentes

Mesmo com pressão e abertura consumíveis, seguem não exportados diretamente no
`.dat` legado:

- `sigmaTheta`;
- `pw`;
- `margin`;
- `opened`.

Esses campos passam a ser caveats não bloqueantes para iniciar a 11.10A apenas
se a 11.10A for preparação diagnóstica, sem validação física e sem declarar
equivalência com o `LOT_Tese`.

## Caveat axissimétrico 1 rad

O modelo PennyShaped usado no projeto deve ser interpretado no contexto da formulação axissimétrica de 1 rad. Portanto, qualquer volume/proxy de fratura não deve ser automaticamente tratado como volume circular completo em 2π sem auditoria matemática específica.

Classificação:

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
```

Esse caveat não bloqueia automaticamente a 11.10A porque a próxima fase
permanece restrita a preparação diagnóstica. Ele bloqueia interpretações fortes
de volume, área, calibração física e equivalência 2π até uma auditoria
matemática específica.

## Readiness atualizado

```text
BUZ29_PENNY_CANDIDATE_PARTIAL_BUT_DIAGNOSTIC_SAFE
```

Esse status significa:

- BUZ29 ainda não está fisicamente validado;
- BUZ29 ainda não tem YAML candidato criado;
- BUZ29 ainda não tem study_id;
- a rota 11.10A pode começar somente como preparação diagnóstica controlada;
- a 11.10A deve preservar caveats sobre `sigmaTheta`, `pw`, `margin`,
  `opened` e interpretação axissimétrica.

## Gate para 11.10A

```text
BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A
```

## Decisão sobre iniciar 11.10A

```text
can_start_11_10A = true
```

Essa decisão autoriza apenas a fase:

```text
PHASE11_10A_START_BUZ29_PENNY_DIAGNOSTIC_ROUTE
```

Não autoriza:

- validação física BUZ29;
- equivalência com `LOT_Tese`;
- alteração de `lot-pkn`;
- alteração de `PknModel` ou `PknRunner`;
- criação automática de rota runtime oficial;
- interpretação de `fracture_volume_proxy_m3` como volume circular completo
  em 2π.

## Riscos remanescentes

- O output legado não exporta `sigmaTheta`, `pw`, `margin` ou `opened`
  diretamente.
- A pressão disponível depende da semântica histórica de `dP` e do visualizador
  legado.
- O marcador `Momento da quebra` é consumível como evento, mas não substitui um
  trace completo do critério.
- O adapter diagnóstico ainda precisa ser alimentado por uma especificação
  BUZ29 sem inventar parâmetros físicos.
- A interpretação de volume/proxy em formulação axissimétrica de 1 rad precisa
  de auditoria matemática futura antes de conclusões físicas fortes.

## Próxima fase recomendada

```text
PHASE11_10A_START_BUZ29_PENNY_DIAGNOSTIC_ROUTE
```

Essa próxima fase deve criar apenas uma rota diagnóstica controlada, mantendo
os caveats acima e sem promover BUZ29 a validação física.

## Resultado da 11.10A

A Fase 11.10A iniciou a preparação diagnóstica autorizada por este gate:

```text
classification = BUZ29_PENNY_DIAGNOSTIC_ROUTE_PARTIAL_STARTED
case = cases/validation/non_pkn/buz29_penny_candidate.yaml
index = cases/validation/non_pkn/studies_index.yaml
```

O candidato mantém explicitamente:

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
NOT_ACTIVE_SIMULATION_CASE
```

A 11.10A não executa BUZ29 e não cria uma rota oficial do `lot-sim`; ela apenas
formaliza o contrato de entrada para uma inspeção futura dos campos do adapter.

## Resultado da 11.10B

A inspeção adapter-ready foi executada na fase seguinte:

```text
classification = BUZ29_PENNY_ADAPTER_INPUTS_PARTIAL
adapter_ready = false
partial_adapter_ready = true
recommended_next_phase = PHASE11_10C_AUDIT_PENNY_SHAPED_MODEL_MATH_AXISYMMETRIC_1RAD
```

Esse resultado preserva o gate diagnóstico: BUZ29-PENNY ainda não é simulação
física, não é equivalência com o legado e não é caso runtime ativo.
