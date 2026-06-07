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
