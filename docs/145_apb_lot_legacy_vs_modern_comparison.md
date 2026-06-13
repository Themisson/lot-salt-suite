# Comparacao APB/LOT legado versus modos modernos

## Resumo executivo

A comparacao registra a diferenca metodologica entre:

```text
legacy_nodal_force + legacy_inside_newton + .dat
```

e:

```text
volume_balance + pre_iterative + *_out.json
```

Classificacao:

```text
APB_LOT_MODERN_MODE_COMPARISON_RECORDED
```

## Criterios

Nao se exige identidade numerica entre os modos, porque as metodologias sao
diferentes. Exige-se:

- sem NaN;
- sem travamento;
- pressao finita;
- JSON valido;
- legado preservado por flag;
- PKN inalterado.

## Interpretacao

A metodologia moderna e preferida como contrato novo por separar balanco
volumetrico e deslocamento do sal do vetor de forcas legado. Isso nao declara
equivalencia fisica com `APB1da`.

## Regressao estendida APB/LOT

A regressao estendida confirmou que os modos modernos e legados podem coexistir
no contrato:

```text
json + volume_balance + pre_iterative
legacy_dat + legacy_nodal_force + legacy_inside_newton
```

Essa comparacao ainda e contratual. Nao ha metricas runtime APB reais nesta
fase.

## Comparacao real ainda bloqueada

A fase `APB_LOT_VALIDATE_MODERN_MODES_WITH_REAL_APB_CASE` confirmou que ainda
nao existe runner APB/LOT moderno para comparar outputs reais. A trilha
legado-moderno permanece limitada a contratos e fixtures ate que:

```text
APB_LOT_IMPLEMENT_REAL_CASE_RUNNER_INTEGRATION
```

crie uma execucao controlada que gere dados efetivos.
