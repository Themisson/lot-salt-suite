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

## Regressao estendida APB/LOT

A suite `APB_LOT_RUN_EXTENDED_REGRESSION_SUITE` validou:

```text
pre_iterative
legacy_inside_newton
```

e rejeitou `inside_magic_loop`. A validacao e contratual e nao declara
equivalencia fisica com o legado.

## Gate de caso real

A fase `APB_LOT_VALIDATE_MODERN_MODES_WITH_REAL_APB_CASE` confirmou que
`pre_iterative` ainda nao e exercitado por um runner APB/LOT real. O modo
continua registrado como contrato moderno; a chamada efetiva ao sal no runtime
depende de uma fase futura de integracao de runner APB/LOT.

Status: `REAL_CASE_RUNNER_INTEGRATION_REQUIRED`.
