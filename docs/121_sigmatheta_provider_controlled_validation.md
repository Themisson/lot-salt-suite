# Fase E — validacao controlada do sigma-theta provider

## Resumo executivo

A Fase E valida, por fixtures pequenas e validador Python, que o
`PostDrillingSigmaThetaProvider` conectado ao diagnostic pre-runner cobre os
cenarios controlados esperados sem habilitar dispatch fisico.

Status:

```text
SIGMATHETA_PROVIDER_CONTROLLED_CASES_VALID
SIGMATHETA_PROVIDER_WIRED_TO_DIAGNOSTIC_PRE_RUNNER
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_NOT_CHANGED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

Esta fase valida contrato e regressao diagnostica. Ela nao valida fisicamente
fratura, nao executa BUZ29-PENNY, nao declara equivalencia com legado e nao
altera o comportamento fisico do PKN.

## Fixtures

As fixtures ficam em:

```text
tests/fixtures/comparison/phase_sigmatheta_provider/
```

| Fixture | Objetivo |
|---|---|
| `provider_disabled_default.yaml` | cobre diagnostico desabilitado por default |
| `provider_diagnostic_ready_not_reached.yaml` | cobre PKN com provider avaliado e gate nao atingido |
| `provider_diagnostic_pkn_reached.yaml` | cobre PKN com gate diagnostico atingido |
| `provider_diagnostic_penny_reached.yaml` | cobre PENNY_SHAPED elegivel apenas diagnosticamente |
| `provider_unknown_source_invalid.yaml` | cobre rejeicao de fonte desconhecida |
| `provider_physically_validated_true_invalid.yaml` | cobre rejeicao de alegacao de validacao fisica |
| `provider_legacy_equivalent_true_invalid.yaml` | cobre rejeicao de alegacao de equivalencia legado |

## Garantias

- `runtime_dispatch_enabled` permanece `false`.
- `PENNY_SHAPED` permanece `diagnostic_only`.
- `BUZ29-PENNY` permanece bloqueado.
- `PKN` permanece retrocompativel.
- As fixtures nao sao casos de validacao fisica.
- `diagnostic_fracture_gate.json` continua saida diagnostica isolada.

## Validador

O validador criado e:

```text
tools/validate_sigmatheta_provider_controlled_cases.py
```

Ele verifica presenca das fixtures, flags de seguranca, rejeicoes esperadas e
gera JSON/Markdown diagnostico quando solicitado.

## Proxima fase recomendada

```text
MASTER_PHASE_F_DECIDE_SIGMATHETA_PROVIDER_READINESS
```

