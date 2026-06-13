# Diagnostico APB/LOT: output, leakoff e deslocamento do sal

## Resumo executivo

Esta fase consolidou os pontos de modernizacao do fluxo APB/LOT:

- saida estruturada `*_out.json`;
- leakoff como contribuicao volumetrica em `dV`;
- deslocamento do sal calculado antes do loop iterativo de pressao.

Classificacao:

```text
APB_LOT_DIAGNOSIS_COMPLETE
implementation_allowed_next = true
```

## Achados

| Item | Status | Observacao |
|---|---|---|
| `.dat` legado | Encontrado | permanece como compatibilidade/comparacao |
| JSON moderno | Encontrado/necessita consolidacao | PKN ja escreve `result.json`; APB/LOT recebe writer especifico |
| `legacy_nodal_force` | Preservado como modo | representa a rota conceitual do legado |
| `volume_balance` | Implementavel | formaliza `dV = dV + dV_leakoff` |
| `legacy_inside_newton` | Preservado como modo | compara chamadas por iteracao |
| `pre_iterative` | Implementavel | chama sal uma vez por layer/step |

## Caveats

Esta fase nao altera `legacy/`, `legance/` ou `external/saltcreep/`.
Tambem nao habilita solver APB completo moderno. Os novos contratos sao
diagnosticos e testaveis, preservando o comportamento PKN.
