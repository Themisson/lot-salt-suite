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
serie. Tambem nao existem em `PknResult` campos como `p_net_at_breakdown`,
`net_pressure_at_breakdown`, `breakdown_step`, `breakdown_time_s` ou
`fracture_initiation_step`. Inferir esses valores diretamente da serie atual
nao e robusto, porque a formulacao PKN moderna ja propaga a partir do tempo
ativo e pode carregar largura minima/valores numericos que nao representam um
evento fisico claro de breakdown.

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
