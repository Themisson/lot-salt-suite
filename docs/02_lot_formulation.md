# 02 — Formulação do Leak-Off Test (LOT)

**Status:** Planejado | **Última atualização:** 2026-06-04

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

## Formulação de fratura PKN minima em SI

**Atenção:** a formulação PKN moderna ainda não está validada contra o legado
porque R09 permanece blocker para regressão numérica. A Fase 6.4 implementa uma
base física mínima em SI para testes dimensionais e evolução incremental, sem
usar `.dat` legado como baseline.

O `lot::PknModel` recebe `PknInput` ja convertido para SI. O parser e o schema
continuam responsaveis por unidades de campo; o solver nao le YAML/JSON.

Para cada instante:

```text
t_ativo = max(0, t - t_acomodacao)
V_inj = Q * t_ativo
w = max(w0, 2.5 * (mu * Q^2 * t_ativo / (E' * h))^(1/5), 1e-9 m)
V_frac = max(0, V_inj - V_leakoff)
L = V_frac / (w * h)
p_net = E' * w / h
```

onde `Q` e a taxa de injecao [m3/s], `mu` e a viscosidade [Pa.s], `E'` e o
modulo plano [Pa], `h` e a altura PKN [m], `w0` e a abertura inicial [m] e
`t_acomodacao` e o tempo sem incremento operacional.

O campo `PknResult.net_pressure_series_Pa` armazena essa serie `p_net`. Ela e
uma pressao liquida PKN, relativa a mecanica da fratura e a abertura `w`.
`p_net` nao e pressao absoluta de poco, nao e pressao anular e nao representa,
isoladamente, a pressao compressiva de parede que deve ser enviada ao sal.
Na formulacao moderna atual, `p_net` tambem nao carrega explicitamente
`sigma_closure`, tensao horizontal minima, pressao de poros ou uma referencia
geomecanica completa. Portanto, qualquer uso de `p_net` como incremento de
pressao absoluta deve ser declarado como hipotese de mapeamento, nao como
consequencia direta do `PknModel`.

Para acoplamento LOT/PKN/sal, `p_net` precisa passar por um mapeamento fisico
explicito antes de preencher `SaltCreepQuery.wall_pressure_Pa`. O contrato
detalhado e os metodos candidatos para esse mapeamento ficam em
`docs/13_coupling_lot_apb_salt.md`.

O leakoff fica encapsulado em `lot::LeakoffModel` e e acumulado em volume
com entradas SI. O modelo fechado (`none`) preserva o volume acumulado anterior
com incremento zero. A taxa constante (`constant_rate`) usa:

```text
dV_leakoff = q_L * dt
V_leakoff = V_leakoff_anterior + dV_leakoff
```

onde `q_L` e `constant_rate_m3_s` [m3/s].

O modelo Carter implementado nesta fase e uma forma estrutural minima,
nao calibrada por pressao, usando coeficiente `C_L` [m/sqrt(s)] e area exposta
[m2]:

```text
dV_leakoff = 2 * C_L * A_leakoff * (sqrt(t + dt) - sqrt(t))
V_leakoff = V_leakoff_anterior + dV_leakoff
```

Para compatibilidade com os YAMLs e testes das fases anteriores,
`synthetic_constant` continua aceito como aproximacao acumulada simplificada:

```text
A_leakoff ~= 2 * h * L_anterior
dV_leakoff = C_L * A_leakoff * sqrt(dt)
```

No acoplamento PKN, o volume acumulado de leakoff e limitado por `V_inj` para
preservar volumes de fratura nao negativos. O modulo rejeita `dt <= 0`, tempo,
area, coeficientes, taxas e acumulados negativos ou nao finitos.

Hipoteses desta fase:
- Geometria PKN com altura constante imposta pelo usuario.
- Propagacao ativada desde o inicio do tempo ativo; o acoplamento com
  `BreakdownDetector` ainda nao esta conectado ao CLI.
- Fluido newtoniano com viscosidade constante.
- Sem acoplamento sal/APB e sem fechamento/descarga.
- `dt`, tempo total e tempo de acomodacao sao definidos no contrato de entrada.
- Todos os resultados expostos pelo modelo sao em SI e devem ser finitos e nao
  negativos nos testes sinteticos.

Campos ainda fora desta fase:
- Relacao pressao-volume pre-fratura em regime elastico.
- Criterio fisico completo de iniciacao de fratura.
- Geometrias circular, elliptical e penny-shaped.
- Leakoff Carter calibrado por pressao e historico fisico completo.
- Integracao com deformacao de sal.

## Contrato LOT/PKN sintético (Fase 6.2)

O caminho moderno inicial usa `simulation.mode: lot-pkn`, `lot.model: pkn` e
`lot.fracture.geometry: pkn`. O parser converte taxa de injecao, tempos,
comprimentos e pressao de breakdown para SI antes de preencher `CaseData`.
Atualmente `LotConfig.breakdown_pressure_Pa` vem de
`lot.fracture.breakdown.pressure` e deve ser tratado como parametro/threshold
de breakdown do contrato de entrada. Ele nao constitui, por si so, uma serie
temporal de pressao absoluta do poco ou da sapata.

No estado atual, `PknRunner` repassa esse valor para `PknInput.breakdown`, mas
`PknModel` calcula a serie `PknResult.net_pressure_series_Pa` pela relacao
`p_net = E' * w / h`, independente de `breakdown_pressure_Pa` na evolucao da
serie. Esse valor tambem pode aparecer como `input.net_pressure_Pa`, mas nao
controla diretamente:

- o inicio da fratura no `PknModel`;
- a geracao das series PKN;
- `PknResult.net_pressure_series_Pa`;
- `PknResult.fracture_length_series_m`;
- `PknResult.fracture_width_series_m`.

Assim, no fluxo moderno atual, `breakdown_pressure_Pa` deve ser entendido como
parametro/threshold/metadado do contrato LOT/PKN, nao como evento dinamico
resolvido na serie temporal.

O `PknModel` gera uma resposta PKN ja iniciada/ativa, nao uma rampa
pre-breakdown ate a ruptura. Tambem nao existem em `PknResult` campos como:

- `breakdown_step`;
- `breakdown_time_s`;
- `p_net_at_breakdown`;
- `fracture_initiation_step`;
- `net_pressure_at_breakdown`.

Inferir esses valores diretamente da serie atual nao e robusto, porque a
formulacao PKN moderna ja propaga a partir do tempo ativo e pode carregar
largura minima/valores numericos que nao representam um evento fisico claro de
breakdown.

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

---

## Auditoria de balanço volumétrico LOT — Fase 10.17A

**Status:** `IMPLEMENTATION_ALLOWED_OPTIONAL_BALANCE_MODE`.

A Fase 10.17A auditou a diferença estrutural entre o LOT legado da tese e o
caminho moderno `lot-pkn`. A conclusão é que o legado calcula pressão de poço
por um balanço volumétrico anular, enquanto o moderno atual calcula apenas a
pressão líquida PKN direta:

```text
p_net = E' * w / h
```

Essa diferença é suficiente para justificar uma rota moderna opcional, mas não
autoriza mudar o default runtime nem declarar validação física.

Artefato rastreável:

```text
tests/fixtures/comparison/phase10_17_balance_audit.json
```

### Evidências do LOT_Tese

| Conceito | Evidência legada | Interpretação |
|---|---|---|
| Taxa de injeção | `APB1da(..., LOT=true, idQ=6, Q=0.5, t_no_injection=9.5)` | Caso BUZ67D PKN injeta `0.5 bbl/min` no contrato legado. |
| Conversão de vazão | `Conv_bbmin_m3min(Q) = Q * 0.158987 / pi / 2` | Convenção interna por radiano; algumas saídas são reescaladas por `2*pi`. |
| Volume anular | `Vi = 0.5 * (R_outer^2 - R_inner^2) * thickness` | O volume de referência participa do balanço de pressão. |
| Compressibilidade | `setPFluid(11.5, 8E-4, 6.40E-10)` | O fluido carrega `k = 6.40e-10 1/Pa`. |
| Balanço de pressão | Termos proporcionais a `(Vq/Vi)/k` e `-(dV/Vi)/k` em `AssemblyFML` | A pressão `dP` é resolvida pelo balanço volumétrico anular. |
| Pressão de poço | `pw = pi + dP` | `pw` não é `p_net` PKN. |
| Fratura/leakoff | `if (pw > sigmaTheta)` e cálculo PKN de `dV_leakoff` | A abertura entra como acomodação volumétrica após o critério legado. |
| No-injection/shut-in | `t_no_injection` e `Vq = flowRate(tend)` após `t > tend` | O legado mantém volume injetado final durante a fase sem injeção. |

### Estado moderno auditado

| Conceito | Estado moderno | Lacuna |
|---|---|---|
| Taxa de injeção | `CaseParser` converte `lot.injection.rate` para `m3/s`. | Disponível. |
| Volume injetado | `PknModel` usa `V_inj = Q * t_ativo`. | Disponível. |
| Volume anular | Fase 10.16 exporta `initial_annular_volume_*` em `result.json`. | Exportado, mas ainda não usado no cálculo de pressão PKN. |
| Compressibilidade | `FluidData.compressibility_per_Pa` é parseado. | Disponível, mas ainda não usado pelo `PknModel`. |
| Pressão direta | `PknResult.net_pressure_series_Pa` armazena `p_net`. | Não representa `pw = pi + dP`. |
| Pressão de poço/anular | Não há série moderna explícita de `wellbore_pressure_Pa`. | Ausente no resultado atual. |
| Fratura/leakoff | Séries de volume de fratura e leakoff existem. | Podem alimentar diagnóstico opcional de balanço, sem validar física. |

### Gate da Fase 10.17A

O gate da auditoria é:

```text
IMPLEMENTATION_ALLOWED_OPTIONAL_BALANCE_MODE
```

Isto significa:

- pode ser criado um modo opcional `volumetric_balance`;
- o default moderno deve continuar `pkn_direct`;
- `net_pressure_Pa` não deve ser reclassificado como `pw`;
- campos de pressão de poço/balanço devem ser exportados separadamente;
- a rota continua diagnóstica até haver validação física independente.

### Modo opcional `volumetric_balance` — Fase 10.17B

**Status:** `OPTIONAL_BALANCE_MODE_IMPLEMENTED_NO_DEFAULT_CHANGE`.

A Fase 10.17B adiciona um modo explícito:

```yaml
lot:
  pressure_model:
    type: volumetric_balance
```

Quando o bloco está ausente, o parser mantém:

```text
pressure_model = pkn_direct
```

Portanto, os casos existentes continuam usando a formulação PKN direta. O modo
`volumetric_balance` é usado apenas no caso controlado:

```text
cases/validation/buz67d_pkn_legacy_aligned.yaml
```

O cálculo de balanço usa dados já disponíveis no `CaseData`:

```text
annular_volume_m3
FluidData.compressibility_per_Pa
injected_volume_series_m3
fracture_volume_series_m3
leakoff_volume_series_m3
```

Antes da abertura lógica do balanço:

```text
dV_effective = dV_injected
dP = dV_effective / (C_fluid * V_annular)
P_wellbore,new = max(0, P_wellbore,old + dP)
```

Após o limiar de breakdown ser atingido no balanço opcional:

```text
dV_effective = dV_injected - dV_fracture - dV_leakoff
dP = dV_effective / (C_fluid * V_annular)
```

Esse modelo não altera `PknResult.net_pressure_series_Pa`; ele exporta uma
série separada:

```text
wellbore_pressure_Pa
balance_delta_pressure_Pa
balance_effective_volume_increment_m3
balance_injected_volume_increment_m3
balance_fracture_volume_increment_m3
balance_leakoff_volume_increment_m3
```

Assim, `net_pressure_Pa` continua sendo a pressão líquida PKN, enquanto
`wellbore_pressure_Pa` representa a rota diagnóstica de balanço volumétrico. A
Fase 10.17B não valida fisicamente `wellbore_pressure_Pa` contra o legado; ela
apenas cria uma alternativa controlada para análise comparativa futura.

O planejamento de acomodação operacional, shut-in/no-injection e fluido Zamora
fica registrado em `docs/16_future_features.md` como Fase 10.17C. Esses itens
não foram conectados ao runtime nesta fase.

### Pressão inicial e schedule com shut-in — Fase 10.18B

**Status:** `PHASE10_18B_INITIAL_PRESSURE_AND_SHUTIN_DIAGNOSTIC_COMPLETE`.

A auditoria da Fase 10.18B confirmou que o legado usa uma pressão
preexistente/hidrostática por anular:

```text
line_up[lu].pi(idAnnular)
```

No caminho de fluido prescrito, essa pressão vem de:

```text
Fluids::getPFpressure(depth, seabed, rho)
  = p_ref + 9.81 * rho_ppg * 119.826427 * depth
```

e é somada no critério legado como:

```text
pw = line_up[lu].pi(idAnnular) + dP(idAnnular)
```

No caso BUZ67D auditado, a série exportada registra em `t = 0`:

```text
pw_Pa = 26732215.17314985
dP = 0
```

Logo, para o caso controlado, essa pressão foi registrada como:

```yaml
lot:
  initial_pressure:
    value: 26732215.17314985
    unit: Pa
```

O contrato moderno é:

```text
wellbore_pressure_Pa = initial_pressure_Pa + dP_balance_accumulated
```

somente para `pressure_model = volumetric_balance`. O default `pkn_direct`
permanece inalterado.

A mesma fase implementa `lot.injection.schedule.phases` como rota opcional:

```yaml
phases:
  - name: injection
    duration: {value: 12.5, unit: min}
    rate: {value: 0.5, unit: bbl_min}
  - name: shutin
    duration: {value: 9.5, unit: min}
    rate: {value: 0.0, unit: bbl_min}
```

Se `phases` estiver ausente, o comportamento antigo de uma única fase de
injeção é preservado. Com `shutin`, a vazão nova é zero e o volume injetado
permanece constante. No modo `volumetric_balance`:

- sem leakoff/fratura/fechamento ativo, a pressão não aumenta no shut-in;
- com leakoff ativo, o volume efetivo pode ficar negativo e a pressão pode
  declinar;
- o gatilho de abertura usa o incremento acima de `initial_pressure_Pa`, para
  evitar que a pressão inicial sozinha abra a fratura no tempo zero.

O diagnóstico BUZ67D completo passou a cobrir `0..1320 s`, mas a pressão
máxima moderna com `initial_pressure_Pa` ficou acima da pressão máxima legada.
Portanto, a correção é classificada como:

```text
PRE_EXISTING_PRESSURE_FIX_PARTIAL_OTHER_FACTORS_REMAIN
```

e não como validação física.

### Acoplamento fratura/leakoff ao balanço volumétrico — Fase 10.18C

**Status:** `PHASE10_18C_FRACTURE_VOLUME_BALANCE_DIAGNOSTIC_COMPLETE`.

A auditoria da Fase 10.18C confirmou que o `PknModel` moderno calcula
`fracture_volume_m3` e `leakoff_volume_m3` como séries acumuladas. O balanço
volumétrico usa incrementos derivados dessas séries:

```text
dV_fracture_i = fracture_volume_i - fracture_volume_{i-1}
dV_leakoff_i  = leakoff_volume_i  - leakoff_volume_{i-1}
```

No modo opt-in `pressure_model = volumetric_balance`, a rota de pressão passa a
usar:

```text
dV_eff = dV_inj - dV_fracture - dV_leakoff
dP     = dV_eff / (compressibility * annular_volume)
```

O acoplamento é sequencial e simplificado. O `PknModel` não recebe a pressão do
balanço como entrada para recalcular a geometria PKN no mesmo passo; portanto,
não há iteração pressão -> fratura -> pressão nesta fase.

O critério legado auditado é:

```text
P_simulacao = line_up[lu].pi(idAnnular) + line_up[lu].dP(idAnnular)
fratura inicia quando |P_simulacao| > |sigma_tangencial(altura_de_influencia)|
```

Esse critério foi classificado como:

```text
PARTIALLY_EXTRACTED_NOT_REPRODUCED_IN_PKN_MODEL
```

porque o `PknModel` não possui, nesta fase, a tensão tangencial no ponto nodal
da altura de influência. A implementação moderna usa apenas a aproximação
existente `fracture.breakdown.pressure` como limiar simplificado. Se esse campo
estiver ausente ou for zero, a abertura por pressão permanece desativada e os
volumes de fratura/leakoff não são descontados do balanço.

Esta fase não implementa Zamora, complacência de casing, APB/sal feedback,
novo critério geomecânico, dano, fechamento complexo de fratura ou nova
formulação PKN.

No BUZ67D controlado, o valor atual `fracture.breakdown.pressure = 1 Pa` é um
placeholder herdado das fases de alinhamento. Com o sink volumétrico ativo, esse
limiar abre a fratura cedo demais e faz com que praticamente todo o volume
injetado seja consumido por `fracture_volume_m3`, mantendo a pressão moderna
próxima de `initial_pressure_Pa`. Isso confirma o mecanismo, mas não constitui
calibração nem equivalência física com o legado.

### Gate sigma-theta para abertura de fratura — Fase 10.18D

**Status:** `SIGMA_THETA_AVAILABLE_DIAGNOSTIC_ONLY`.

A Fase 10.18D auditou se o critério legado:

```text
pw = pi + dP
sigmaTheta = -getSigmaTheta()
opened = pw > sigmaTheta
```

poderia substituir diretamente o placeholder
`fracture.breakdown.pressure = 1 Pa` no modo `volumetric_balance`.

O diagnóstico moderno já possui o campo:

```text
sigma_theta_compression_positive_Pa
```

e a função:

```text
evaluate_sigma_theta_breakdown_point(...)
```

que calcula:

```text
margin_Pa = pressure_Pa - sigma_theta_compression_positive_Pa
opened = margin_Pa > 0
```

Entretanto, essa rota está disponível apenas no diagnóstico experimental de
`coupling/`, alimentado por `SaltCreepTimeBridge::wall_stress_diagnostics()`.
O fluxo runtime `lot-sim run --mode lot-pkn` continua executando apenas:

```text
YAML -> CaseParser -> PknRunner -> PknModel -> ResultWriter
```

sem instanciar o bridge de sal, sem coletar `SaltWallStressDiagnostics` e sem
selecionar um ponto de influência sigma-theta por profundidade.

Por isso, a Fase 10.18D não conectou `sigma_theta_compression_positive_Pa` ao
`PknModel`. Fazer isso agora exigiria redesenhar o acoplamento LOT/sal ou
duplicar fora de `coupling/` a lógica já existente em
`LotSaltSigmaThetaBreakdown`, o que foi explicitamente bloqueado pela fase.

O modo `volumetric_balance` permanece usando somente o fallback explícito:

```text
fracture.breakdown.pressure
```

como limiar simplificado para habilitar sinks de fratura/leakoff. Casos com
`fracture.breakdown.pressure = 0` ou sem pressão definida continuam sem abertura
por esse critério. O default `pkn_direct` permanece inalterado.

### Calibração diagnóstica do threshold estático — Fase 10.18E

**Status:** `PHASE10_18E_STATIC_LEGACY_BREAKDOWN_DIAGNOSTIC_COMPLETE`.

A Fase 10.18E extraiu um threshold estático rastreável a partir do audit CSV do
`LOT_Tese` e do marcador nativo:

```text
results/comparison/level1_buz67d/legacy_audit/buz67d_audit_timeseries.csv
results/comparison/level1_buz67d/legacy_audit/legacy_native_output.dat
Momento da quebra: 8.5
```

O evento legado corresponde a `8.5 min = 510 s`. A linha selecionada no CSV é a
linha de maior `pw_Pa` nesse instante, com `layer = 16` e `annular_index = 1`:

```text
pw_Pa = 67342521.84592447 Pa
dP    = 8131435.236221395 Pa
```

O valor absoluto `pw_Pa = 67.342522 MPa` é mantido no relatório diagnóstico. No
entanto, o `PknModel` moderno consome `fracture.breakdown.pressure` como
threshold incremental acima de `initial_pressure_Pa`, portanto o caso
diagnóstico usa o delta legado:

```text
cases/validation/buz67d_pkn_legacy_static_breakdown.yaml
fracture.breakdown.pressure = 8131435.236221395 Pa
```

Esse caso não substitui `cases/validation/buz67d_pkn_legacy_aligned.yaml` e não
é um novo default. Ele existe apenas para testar o efeito de um threshold
estático calibrado por evidência legada.

Resultado observado:

| Modo | Pressão máxima | Erro relativo contra legado | Classificação |
|---|---:|---:|---|
| Legado auditado `pw_Pa` | `69.035836 MPa` | `0.000` | referência |
| 10.18B | `82.129237 MPa` | `+0.190` | referência diagnóstica |
| 10.18C | `26.732215 MPa` | `-0.613` | referência diagnóstica |
| 10.18E | `26.732215 MPa` | `-0.613` | `STATIC_BREAKDOWN_OPENED_TOO_EARLY` |

Conclusão: o threshold estático extraído é rastreável, mas não resolve a
abertura prematura no modelo moderno. O primeiro sink de fratura/leakoff no
caso 10.18E ocorreu em `30 s`, muito antes do marcador legado de `510 s`.
Portanto, a fase confirma que `fracture.breakdown.pressure` continua sendo uma
aproximação diagnóstica simplificada e não reproduz o critério legado
sigma-theta por altura de influência.

### Auditoria instrumentada do sink de fratura — Fase 10.18F

**Status:** `PHASE10_18F_FRACTURE_TRACE_AUDIT_COMPLETE_NO_SOLVER_CORRECTION`.

A Fase 10.18F instrumentou temporariamente o `LOT_Tese` para observar a ordem
local do critério legado de fratura e do sink volumétrico. A instrumentação foi
mantida apenas durante a auditoria, marcada com `// AUDIT: Phase 10.18F`, e foi
removida antes do commit. Nenhum arquivo em `legance/` é versionado nesta fase.

O traço legado gerado localmente fica em:

```text
results/comparison/phase10_18f/legacy_trace/buz67d_fracture_trace.csv
```

O primeiro ponto legado que satisfaz `pw > sigmaTheta` ocorreu em:

| Campo | Valor |
|---|---:|
| `time_s` | `510.0` |
| `pw_Pa` | `66769490.24425595` |
| `sigmaTheta_Pa` | `66666624.79984049` |
| `margin_Pa` | `102865.444415465` |
| `fracture_volume_increment_m3` | `0.0` |

O primeiro sink positivo observado no traço legado ocorreu no passo seguinte:

| Campo | Valor |
|---|---:|
| `time_s` | `540.0` |
| `fracture_volume_increment_m3` | `9.327456563839315e-05` |

A classificação local do legado é:

```text
LEGACY_SINK_NEXT_STEP
```

Entretanto, a comparação com o traço moderno 10.18E mostrou que o moderno abre
e aplica sink em `30 s`, muito antes do critério legado sigma-theta em `510 s`:

| Campo | Legado | Moderno 10.18E |
|---|---:|---:|
| Primeiro `opened` | `510.0 s` | `30.0 s` |
| Primeiro sink positivo | `540.0 s` | `30.0 s` |
| Incremento de fratura no primeiro sink | `9.327456563839315e-05 m3` | `0.039746823732 m3` |

Por isso, a causa raiz da divergência é classificada como:

```text
OTHER
modern static threshold opens before the legacy sigma-theta criterion;
this is a criterion mismatch, not a confirmed local C++ sink bug
```

Conclusão: não há evidência suficiente para corrigir a ordem do sink em
`PknModel`. A divergência principal vem do critério de abertura simplificado
`fracture.breakdown.pressure`, que ainda não reproduz o critério legado
sigma-theta por altura de influência. A próxima correção deve ser arquitetural:
fornecer uma rota opt-in testada para `SigmaThetaInfluenceLayer` alimentar o
balanço volumétrico, sem promover essa rota a default runtime.

### Critério `sigma_theta_static` opt-in — Fase 10.19A

**Status:** `SIGMA_THETA_STATIC_PROVIDER_IMPLEMENTATION_ALLOWED`.

A Fase 10.19A criou a primeira arquitetura runtime opt-in para que o modo
`volumetric_balance` receba uma fonte estática de:

```text
sigma_theta_compression_positive_Pa
```

sem fazer `PknModel` depender de `saltcreep`, `SaltCreepTimeBridge` ou
`coupling/`. O contrato é YAML -> `CaseParser` -> `CaseData` -> `PknRunner` ->
`PknInput` -> `PknModel`.

O formato aceito é:

```yaml
lot:
  fracture:
    initiation:
      type: sigma_theta_static
      source: diagnostic_static
      pressure_source: wellbore_pressure_Pa
      comparison: legacy_algebra
      sigma_theta:
        compression_positive:
          value: 67342521.84592447
          unit: Pa
        layer_id: legacy_layer_16
        influence_depth:
          value: 4374.0
          unit: m
        mapping_status: STATIC_FROM_LEGACY_AUDIT
```

Com esse critério, a pressão usada é a pressão trial de poço do balanço
volumétrico:

```text
wellbore_pressure_trial_Pa
```

A álgebra espelha o diagnóstico moderno de `LotSaltSigmaThetaBreakdown`:

```text
margin_Pa = wellbore_pressure_trial_Pa - sigma_theta_compression_positive_Pa
opened = margin_Pa > 0
```

Quando abre, o resultado passa a registrar:

```text
fracture_initiation_type = sigma_theta_static
fracture_initiation_time_s
fracture_initiation_pressure_Pa
fracture_initiation_sigma_theta_Pa
fracture_initiation_margin_Pa
fracture_initiation_layer_id
fracture_initiation_depth_m
```

O fallback antigo continua:

```text
constant_pressure -> fracture.breakdown.pressure
```

e `pkn_direct` permanece sem alteração de comportamento.

O caso diagnóstico criado é:

```text
cases/validation/buz67d_pkn_legacy_sigma_theta_static.yaml
```

Ele usa como proxy estático:

```text
sigma_theta_compression_positive_Pa = 67342521.84592447 Pa
```

Esse valor vem da auditoria legada e não é uma tensão runtime calculada por
saltcreep. O resultado do diagnóstico 10.19A foi:

| Métrica | Valor |
|---|---:|
| `fracture_initiation_time_s` | `30.0` |
| `fracture_initiation_pressure_Pa` | `82129237.46813472` |
| `fracture_initiation_sigma_theta_Pa` | `67342521.84592447` |
| `fracture_initiation_margin_Pa` | `14786715.62221025` |
| `max_pressure_10_19A` | `26.732215 MPa` |
| erro relativo contra legado | `-0.6128` |

Classificação:

```text
SIGMA_THETA_STATIC_OPENED_TOO_EARLY
```

Conclusão: a arquitetura opt-in foi estabelecida, mas o proxy estático ainda
abre cedo demais. A próxima etapa deve alimentar o critério com uma fonte
runtime por altura de influência (`SigmaThetaInfluenceLayer`), não apenas com
um valor escalar estático extraído do legado.
