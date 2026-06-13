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
