# Diagnostic pre-runner fixtures (Fase 11.10Z)

## Resumo executivo

A Fase 11.10Z adiciona fixtures versionadas para validar o contrato do
diagnostico pre-runner criado na 11.10Y. As fixtures sao pequenas, sinteticas e
nao executam BUZ29-PENNY.

## Contexto pos-11.10Y

A 11.10Y implementou o gate diagnostico opt-in antes de `run_pkn_case`. A 11.10Z
nao altera runtime, nao habilita dispatch fisico e nao muda o comportamento
padrao do PKN. Ela apenas registra cenarios de contrato para testes e auditoria.

## Fixtures criadas

As fixtures ficam em:

```text
tests/fixtures/comparison/phase11_10z/
```

Arquivos:

```text
diagnostic_disabled_default.yaml
diagnostic_enabled_pkn_pre_runner.yaml
diagnostic_enabled_penny_pre_runner.yaml
diagnostic_dispatch_true_invalid.yaml
diagnostic_invalid_mode.yaml
diagnostic_missing_sigmatheta_blocks.yaml
```

## Cenarios cobertos

| Cenario | Expectativa |
|---|---|
| default disabled | diagnostico ausente, sem arquivo diagnostico |
| PKN pre-runner | diagnostico gerado, PKN selecionado, sigma_theta ausente bloqueia |
| PENNY_SHAPED diagnostico | modelo diagnostic_only, sem execucao fisica |
| dispatch true invalido | rejeitado nesta fase |
| mode invalido | rejeitado |
| missing sigmaTheta blocks | `FRACTURE_GATE_BLOCKED_SIGMATHETA_INITIAL_STATE` |

## Regras de validacao

O validador da fase e:

```text
tools/validate_phase11_10z_diagnostic_pre_runner_fixtures.py
```

Ele exige seis fixtures, confere os campos minimos e emite:

```text
DIAGNOSTIC_PRE_RUNNER_FIXTURES_VALID
```

quando a cobertura esta completa.

## O que permanece bloqueado

```text
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_NOT_CHANGED
```

As fixtures nao sao validacao fisica, nao declaram equivalencia com legado e
nao transformam `PENNY_SHAPED` em rota runtime.

## Proxima fase recomendada

```text
PHASE11_11A_VALIDATE_DIAGNOSTIC_PRE_RUNNER_ON_CONTROLLED_CASES
```

Essa proxima fase pode executar casos controlados com diagnostico habilitado,
mantendo a separacao entre diagnostico e resultado fisico.

## Atualizacao 11.11A — validacao controlada

A Fase 11.11A consome estas fixtures e registra:

```text
PHASE11_11A_DIAGNOSTIC_PRE_RUNNER_CONTROLLED_CASES_VALIDATED
DIAGNOSTIC_PRE_RUNNER_CONTROLLED_CASES_VALID
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
```

Essa validacao ainda nao compara os outputs fisicos PKN em profundidade; isso
fica reservado para a 11.11B.
