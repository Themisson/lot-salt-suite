# Fase 11.11E — implementação da integração runtime limitada do fracture gate

## Resumo executivo

A 11.11E implementa a integração runtime limitada do `fracture gate` no ponto
permitido entre parse/validação e `run_pkn_case`. A integração é opt-in,
diagnóstica e isolada: quando habilitada, avalia `FractureGateRuntimeWiring` e
escreve `diagnostic_fracture_gate.json`; quando desabilitada, não avalia o gate
e não gera saída diagnóstica.

A 11.11E implementa integração runtime limitada do fracture gate, mas não
habilita dispatch físico. O status de dispatch permanece diagnóstico e não
chama PknModel, PknRunner ou PennyShapedDiagnosticAdapter.

PKN permanece o default retrocompatível e BUZ29-PENNY permanece bloqueado.

## O que foi implementado

- `LimitedFractureGateRuntimeIntegration` como helper C++ isolado.
- Suporte ao modo `limited_gate`.
- Rejeição explícita de `dispatch_runtime_enabled=true`.
- Uso do helper pelo diagnóstico pre-runner existente.
- Comparação PKN disabled/enabled reexecutável com `--diagnostic-mode limited_gate`.
- Ferramenta de auditoria da 11.11E para JSON/Markdown.

## Modos suportados

| Modo | Status | Semântica |
|---|---|---|
| `pre_runner` | suportado | diagnóstico pre-runner existente |
| `diagnostic_only` | suportado | diagnóstico sem dispatch físico |
| `limited_gate` | suportado | integração runtime limitada sem dispatch físico |

## Garantias de não dispatch físico

`runtime_dispatch_enabled` permanece `false` em todos os resultados da
integração limitada. Os status `FRACTURE_DISPATCH_PKN_ELIGIBLE` e
`FRACTURE_DISPATCH_PENNY_DIAGNOSTIC_ELIGIBLE` são tratados apenas como
elegibilidade diagnóstica, sem chamada para solver físico.

O helper não inclui nem depende de:

- `PknModel`;
- `PknRunner`;
- `PennyShapedDiagnosticAdapter`.

## Saída diagnóstica isolada

Quando `lot.fracture.fracture_gate_diagnostics.enabled = true`, o runtime grava:

```text
diagnostic_fracture_gate.json
```

Os arquivos físicos permanecem:

```text
result.json
timeseries.csv
```

A comparação disabled/enabled da Fase 11.11E deve continuar provando que
`result.json` e `timeseries.csv` não mudam com o gate limitado.

## Regressão PKN

O caminho `lot-sim run --mode lot-pkn` segue usando `run_pkn_case(data)` depois
da avaliação diagnóstica. A avaliação do gate não muta `CaseData` nem altera
parâmetros físicos do PKN.

Status esperado:

```text
PKN_OUTPUTS_UNCHANGED_WITH_LIMITED_GATE
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

## Bloqueios preservados

- BUZ29-PENNY não é executado.
- `PENNY_SHAPED` segue diagnostic-only.
- Não há equivalência física com legado.
- Não há runtime físico Penny.
- Não há chamada ao `PennyShapedDiagnosticAdapter` como solver runtime.

## Próxima fase

```text
PHASE11_11F_ADD_LIMITED_GATE_CASE_FIXTURES
```

## Atualização 11.11F — fixtures do modo limited_gate

A Fase 11.11F adiciona fixtures pequenas e versionadas para o modo
`limited_gate`. Elas cobrem default disabled, PKN limitado, `PENNY_SHAPED`
diagnostic-only, `dispatch_runtime_enabled=true` invalido, sigma_theta ausente
e modelo nao suportado.

Essas fixtures validam contrato e regressao. Elas nao habilitam dispatch fisico,
nao executam BUZ29-PENNY e nao transformam `PENNY_SHAPED` em runtime fisico.

Status esperado:

```text
PHASE11_11F_LIMITED_GATE_FIXTURES_DEFINED
LIMITED_GATE_FIXTURES_VALID
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```
