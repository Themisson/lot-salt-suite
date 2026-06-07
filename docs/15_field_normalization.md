# 15 — Normalizacao documental de campos legacy-modern

Este documento registra normalizacoes documentais usadas para comparar saidas
legadas e modernas. Ele nao define validacao fisica, nao altera runtime e nao
autoriza comparacoes numericas alem das conversoes explicitamente listadas.

## Fase 10.14D — unidade temporal legada e evidence gate Level 1

**Status:** `LEVEL1_TIME_UNIT_RESOLVED_CASE_EQUIVALENCE_PENDING`.

Na Fase 10.14D, o contexto fornecido pelo autor da tese resolveu a unidade
temporal do legado LOT_Tese:

```text
APB1da dt, ttime e o campo Time exportado em .dat estao em minutos.
```

Tipo de evidencia:

```text
author_provided_context
```

Conversao documental permitida:

```text
time_s = Time_raw * 60.0
```

Essa conversao resolve a unidade, mas nao estabelece equivalencia de caso,
duracao, passo temporal, fisica de pressao, abertura de fratura, dano, ruptura
ou estado tensional.

## Duracao observada nos fixtures reduzidos

Nos fixtures reduzidos atuais:

| Fonte | Faixa temporal | Em segundos |
| --- | ---: | ---: |
| LOT_Tese `.dat` reduzido | `0..12.5 min` | `0..750 s` |
| Moderno `timeseries.csv` reduzido | `0..420 s` | `0..420 s` |

Portanto, a comparacao temporal numerica legado-moderno permanece bloqueada
exceto pela conversao de unidade documentada. A diferenca de duracao nos
fixtures reduzidos impede declarar equivalencia temporal Level 1.

## Gate Level 1

O gate Level 1 permanece fechado:

```text
level1_ready = false
physical_validation = false
numeric_equivalence = false
```

Campos ainda bloqueados:

- `sigmaTheta`
- `pw`
- `margin`
- `opened`
- `hoop_state` como validacao fisica
- `j2`
- von Mises
- dano
- fratura fisica
- significado semantico de `dP` legado
- equivalencia entre `Layer` legado e `wall_gp_*` moderno

## Equivalencia de caso

O par:

```text
legance/LOT_Tese/results/8-BUZ-67D-PKN.dat
cases/lot_tese_migrated/buz67d_pkn.yaml
```

deve ser classificado como:

```text
SIMILAR_CASE
```

e nao como `SAME_CASE`. O nome e a linhagem BUZ67D/PKN coincidem, mas os
fixtures sao reduzidos, a duracao moderna amostrada e diferente, e ainda ha
caveats de migracao/revisao que impedem equivalencia quantitativa.

## Proximo uso permitido

A informacao desta fase permite:

- testar que a conversao `min -> s` esta registrada;
- manter um gate automatizado que impede promocao indevida para Level 1;
- planejar uma ferramenta futura que so compare tempos quando houver evidencia
  adicional de equivalencia de caso e duracao.

Ela nao permite:

- comparar `dP` legado com `net_pressure_Pa`;
- comparar `sigmaTheta`, `pw`, `margin` ou `opened`;
- declarar validacao fisica de fratura;
- usar `hoop_state` como evidencia de equivalencia legado-moderno.

## Fase 10.14EF — caso moderno controlado legacy-aligned

**Status:** `LEVEL1_CONTROLLED_EQUIVALENT_CASE_CREATED_RUN_PENDING`.

A Fase 10.14EF adiciona um registro de parametros extraidos em modo read-only:

```text
tests/fixtures/comparison/buz67d_legacy_parameters.json
```

e cria um novo caso moderno controlado:

```text
cases/validation/buz67d_pkn_legacy_aligned.yaml
```

O caso migrado original permanece inalterado:

```text
cases/lot_tese_migrated/buz67d_pkn.yaml
```

Classificacao:

```text
CONTROLLED_EQUIVALENT
```

Essa classificacao e limitada a parametros de entrada essenciais. Foram
extraidos diretamente do main legado hard-coded campos temporais, injecao,
geometria, fluido, formacao/sal e identificacao PKN. O novo YAML codifica:

```text
total_time = 12.5 min = 750 s
dt = 0.5 min = 30 s
```

O gate Level 1 continua fechado porque a fase nao executa `lot-sim run` no caso
novo e nao compara saidas:

```text
level1_ready = false
physical_validation = false
numeric_equivalence = false
```

Assim, a normalizacao avanca de `SIMILAR_CASE` para um caso controlado de
entrada, mas ainda nao para equivalencia de resultado.

## Fase 10.15A — diagnostico Level 1 temporal/estrutural

**Status:** `LEVEL1_STRUCTURAL_DIAGNOSTIC_COMPLETE`.

A Fase 10.15A executa o caso controlado e aplica a conversao temporal ja
registrada:

```text
time_s = Time_raw * 60.0
```

O diagnostico gerado em `results/comparison/level1_buz67d/` confirma apenas
compatibilidade temporal/estrutural:

| Fonte | Registros | Time steps | Faixa temporal | dt medio |
|---|---:|---:|---:|---:|
| Legado | 5460 | 26 | `0..750 s` | `30 s` |
| Moderno | 26 | 26 | `0..750 s` | `30 s` |

Essa compatibilidade nao valida campos fisicos. O legado tem varios blocos por
camada/anular/campo, enquanto o moderno tem uma serie temporal LOT/PKN. A
diferenca de `n_records` e esperada para este diagnostico estrutural.

O gate permanece:

```text
level1_ready = false
physical_validation = false
numeric_equivalence = false
awaiting_human_review = true
```

As imagens em `results/comparison/level1_buz67d/` sao diagnosticas e nao devem
ser versionadas.

## Fase 10.15B — diagnostico visual com execucao legada auditada

**Status:** `LEVEL1B_LEGACY_AUDIT_VISUAL_DIAGNOSTIC_COMPLETE`.

A Fase 10.15B adiciona uma execucao auditada do `LOT_Tese` com instrumentacao
temporaria e nao comitavel. A instrumentacao exporta valores ja calculados pelo
legado para:

```text
results/comparison/level1_buz67d/legacy_audit/buz67d_audit_timeseries.csv
```

Campos exportados:

| Campo | Origem | Normalizacao |
|---|---|---|
| `time_min` | `ttime`/`timeResults` legado | mantido em minutos |
| `time_s` | `time_min` | `time_min * 60` |
| `pw_Pa` | `pi + dP` | Pa, sem equivalencia com `net_pressure_Pa` |
| `injected_volume_m3` | `Vq * 2*pi` | derivado de vazao auditada |
| `Q_raw` | `Q` legado | mantido como valor hard-coded |
| `Q_SI_m3_per_min` | `ConvflowRate() * 2*pi` | m3/min |
| `initial_annular_volume_m3` | `Vi * 2*pi` | derivado da geometria legada |
| `dP` | `results[lu].dP` | Pa, incremento legado |
| `sigmaTheta_Pa` | nao exportado nesta fase | vazio |

Os graficos gerados sao diagnosticos:

```text
injected_volume_vs_pressure.png
pressure_vs_time_diagnostic.png
```

Na Fase 10.15B, `annular_volume_comparison.png` permanecia bloqueado porque o
resultado moderno nao exportava `initial_annular_volume_m3`. A Fase 10.16
remove esse bloqueio tecnico para o caso controlado BUZ67D, mas apenas como
diagnostico geometrico.

## Fase 10.16 — volume anular com drill pipe

**Status:** `DRILLPIPE_ANNULAR_VOLUME_DIAGNOSTIC_EXPORTED`.

O legado LOT_Tese calcula `Vi` por radiano com:

```text
V_rad = 0.5 * (R_outer^2 - R_inner^2) * L
V_total = 2*pi*V_rad
```

Para o BUZ67D PKN, o drill pipe legado e:

```text
Solids(..., di = 4.67 in, de = 5.5 in, ...)
```

`di` e `de` sao diametros em polegadas, confirmados por `Solids.h` e por
`Solids::getRi_m()/getRe_m()`. No moderno, o caso controlado registra:

```text
wellbore.drill_pipe.inner_diameter = 4.67 in
wellbore.drill_pipe.outer_diameter = 5.5 in
wellbore.drill_pipe.depth = 4374 m
```

Campos modernos exportados em `result.json`:

| Campo | Unidade | Observacao |
|---|---|---|
| `initial_annular_volume_per_radian_m3` | m3/rad | mesma convencao interna do legado |
| `initial_annular_volume_m3` | m3 | `2*pi*V_rad` |
| `annular_outer_radius_m` | m | raio hidraulico externo selecionado |
| `annular_inner_radius_m` | m | raio externo do drill pipe quando atinge a sapata |
| `annular_length_m` | m | espessura vertical da layer que contem a sapata |
| `annular_volume_convention` | texto | contrato de exportacao |
| `annular_volume_source` | texto | origem dos dados usados |

Na geometria controlada BUZ67D atual, usando o raio interno do casing moderno
como raio hidraulico externo, o desconto do drill pipe altera o volume
diagnostico moderno de:

```text
0.22233639145536 m3/rad -> 0.17842518895536 m3/rad
1.39698074804365 m3     -> 1.12107852567506 m3
```

Essa normalizacao nao muda `PknModel` e nao transforma `net_pressure_Pa` em
`pw_Pa`. A comparacao Level 1B permanece diagnostica.

A comparacao visual usa os rotulos:

```text
Legacy pw_Pa — LOT_Tese audit run
Modern net_pressure_Pa — lot-sim, semantic equivalence not confirmed
```

Esses rotulos sao deliberadamente conservadores: `pw_Pa` legado e
`net_pressure_Pa` moderno podem ter semanticas diferentes. A fase nao valida
fisica de LOT, nao valida equivalencia numerica e nao abre o gate de Level 1.

## Fase 10.17A — normalização de campos para balanço volumétrico

**Status:** `BALANCE_AUDIT_COMPLETE_OPTIONAL_MODE_ALLOWED`.

A auditoria 10.17A preserva a distinção entre:

| Campo | Origem | Status de comparação |
|---|---|---|
| `pw_Pa` | Legado `pi + dP` | Pressão de poço/anular do balanço legado. |
| `dP` | Legado `APB1da` | Incremento do balanço volumétrico legado. |
| `Vq` | Legado `flowRate(...)` | Volume injetado, com convenção geométrica legada. |
| `Vi` | Legado `0.5*(R_outer^2-R_inner^2)*L` | Volume anular de referência. |
| `k` | Legado `Fluid::kt` | Compressibilidade do fluido. |
| `net_pressure_Pa` | Moderno `PknResult` | Pressão líquida PKN, não equivalente a `pw_Pa`. |
| `initial_annular_volume_m3` | Moderno `result.json` | Disponível como diagnóstico desde a Fase 10.16. |
| `FluidData.compressibility_per_Pa` | Moderno `CaseData` | Disponível no parser, ainda não usado no `PknModel` direto. |

O próximo campo moderno permitido por esta normalização é uma série separada
`wellbore_pressure_Pa` em modo opt-in. Ela deve ser tratada como diagnóstico de
balanço, não como substituição automática de `net_pressure_Pa`.

## Fase 10.17B — campos exportados pelo modo `volumetric_balance`

**Status:** `BALANCE_FIELDS_EXPORTED_OPT_IN`.

O writer moderno passa a exportar campos de balanço no `timeseries.csv` e no
`result.json`. Eles são sempre presentes para estabilidade de formato, mas só
têm significado físico operacional quando:

```text
pressure_model = volumetric_balance
```

Campos:

| Campo | Unidade | Interpretação |
|---|---|---|
| `pressure_model` | texto | `pkn_direct` ou `volumetric_balance`. |
| `wellbore_pressure_Pa` | Pa | Pressão acumulada pelo balanço opt-in. |
| `balance_delta_pressure_Pa` | Pa | Incremento do passo por `dV_effective/(C*V)`. |
| `balance_effective_volume_increment_m3` | m3 | Volume líquido usado no balanço do passo. |
| `balance_injected_volume_increment_m3` | m3 | Incremento de volume injetado. |
| `balance_fracture_volume_increment_m3` | m3 | Incremento de volume de fratura descontado após abertura lógica. |
| `balance_leakoff_volume_increment_m3` | m3 | Incremento de leakoff descontado após abertura lógica. |

O campo `net_pressure_Pa` não foi renomeado nem reclassificado. Comparações
legado-moderno que usem `wellbore_pressure_Pa` devem registrar explicitamente
que estão usando a rota `volumetric_balance`, não a pressão PKN direta.

## Fase 10.18A — uso diagnóstico de `wellbore_pressure_Pa`

**Status:** `PHASE10_18A_VOLUMETRIC_BALANCE_DIAGNOSTIC_COMPLETE`.

A comparação visual da Fase 10.18A usa os campos de pressão com os seguintes
rótulos semânticos:

| Fonte | Campo | Uso nesta fase |
|---|---|---|
| Legado auditado | `pw_Pa` | Pressão `pi + dP` exportada por instrumentação auditada. |
| Moderno `pkn_direct` | `net_pressure_Pa` | Referência PKN direta; não equivalente a `pw_Pa`. |
| Moderno `volumetric_balance` | `wellbore_pressure_Pa` | Diagnóstico opt-in de balanço volumétrico. |

Campos de balanço usados no gráfico de componentes:

| Campo | Interpretação |
|---|---|
| `balance_injected_volume_increment_m3` | Incremento de volume injetado no passo. |
| `balance_effective_volume_increment_m3` | Incremento efetivo usado no balanço. |
| `balance_fracture_volume_increment_m3` | Volume de fratura descontado quando aplicável. |
| `balance_leakoff_volume_increment_m3` | Volume de leakoff descontado quando aplicável. |
| `balance_delta_pressure_Pa` | Incremento de pressão por balanço. |

O diagnóstico classificou a curva `volumetric_balance` como mais próxima do
legado em pressão máxima do que `pkn_direct`, mas isso não altera o contrato de
normalização: `pw_Pa`, `net_pressure_Pa` e `wellbore_pressure_Pa` continuam
campos distintos. Nenhum campo tensorial, `sigmaTheta`, `margin`, `opened`,
dano ou ruptura foi comparado.

## Fase 10.17C — campos ainda planejados

Campos futuros de acomodação, shut-in e Zamora permanecem fora do contrato
normalizado atual. Antes de comparar ou exportar esses dados, uma fase futura
deve definir:

- `operation_phase`;
- `phase_elapsed_time_s`;
- `injection_active`;
- `shutin_active`;
- `fluid_model`;
- `fluid_density_kg_m3`;
- `fluid_compressibility_per_Pa`;
- `fluid_thermal_expansion_per_K`;
- `fluid_state_source`.

Até lá, a comparação Level 1 continua restrita aos campos já exportados e
documentados.
