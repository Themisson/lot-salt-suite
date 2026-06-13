# APB/LOT pre-iterative salt displacement mode

## Resumo executivo

Foram formalizados dois modos de deslocamento do sal:

```text
legacy_inside_newton
pre_iterative
```

No modo `pre_iterative`, o contrato chama conceitualmente
`solveThermalViscoStep(dt)` uma vez por layer/step antes do loop iterativo de
pressao e reutiliza o deslocamento durante as iteracoes.

## Comparacao de chamadas

| Modo | Chamadas por passo |
|---|---|
| `legacy_inside_newton` | `layers * newton_iterations` |
| `pre_iterative` | `layers` |

## Limite

Esta fase nao implementa um solver APB/sal completo nem altera `saltcreep`.
Ela cria o contrato moderno e os testes de contagem/planejamento.
