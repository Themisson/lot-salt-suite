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
