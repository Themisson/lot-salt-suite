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

`annular_volume_comparison.png` permanece bloqueado porque o resultado moderno
nao exporta `initial_annular_volume_m3`. O CSV correspondente registra o
status `BLOCKED_MISSING_VOLUME`.

A comparacao visual usa os rotulos:

```text
Legacy pw_Pa — LOT_Tese audit run
Modern net_pressure_Pa — lot-sim, semantic equivalence not confirmed
```

Esses rotulos sao deliberadamente conservadores: `pw_Pa` legado e
`net_pressure_Pa` moderno podem ter semanticas diferentes. A fase nao valida
fisica de LOT, nao valida equivalencia numerica e nao abre o gate de Level 1.
