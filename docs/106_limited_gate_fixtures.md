# Fase 11.11F — fixtures do limited fracture gate

## Resumo executivo

A Fase 11.11F adiciona fixtures pequenas para o modo `limited_gate` do
`fracture_gate_diagnostics`. O objetivo e fixar o contrato de validacao da
integracao runtime limitada implementada na 11.11E, sem habilitar dispatch
fisico e sem transformar modelos nao-PKN em rotas operacionais.

A 11.11F cria fixtures do modo limited_gate. Ela não habilita dispatch físico,
não executa BUZ29-PENNY e não transforma PENNY_SHAPED em runtime físico.

As fixtures existem para validar contrato e regressão, não para validação
física.

## Contexto pós-11.11E

A 11.11E registrou:

```text
LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_IMPLEMENTED
runtime_dispatch_enabled = false
PKN_OUTPUTS_UNCHANGED_WITH_LIMITED_GATE
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

As fixtures da 11.11F exercitam esse contrato como dados pequenos versionados
em:

```text
tests/fixtures/comparison/phase11_11f/
```

## Fixtures criadas

| Fixture | Cenário | Expectativa |
|---|---|---|
| `limited_gate_disabled_default.yaml` | default disabled | sem diagnostico e PKN preservado |
| `limited_gate_enabled_pkn.yaml` | PKN com `limited_gate` | diagnostico gerado, dispatch fisico falso |
| `limited_gate_enabled_penny.yaml` | `PENNY_SHAPED` com `limited_gate` | diagnostic-only, sem runtime fisico |
| `limited_gate_dispatch_true_invalid.yaml` | dispatch true | rejeicao obrigatoria |
| `limited_gate_missing_sigmatheta_blocks.yaml` | sigma_theta ausente | bloqueio diagnostico do gate |
| `limited_gate_invalid_model_blocked.yaml` | modelo nao suportado | bloqueio antes de qualquer dispatch |

## Metadata e caveats

O arquivo `limited_gate_fixtures_metadata.json` registra:

```text
runtime_dispatch_enabled = false
runtime_physical_dispatch_allowed = false
buz29_execution_allowed = false
pkn_behavior_change_allowed = false
penny_shaped_runtime_enabled = false
```

Caveats obrigatorios:

```text
PKN_DEFAULT_RETROCOMPATIBLE
LIMITED_GATE_DIAGNOSTIC_ONLY
DISPATCH_RUNTIME_ENABLED_TRUE_REJECTED
PENNY_SHAPED_DIAGNOSTIC_ONLY
BUZ29_EXECUTION_BLOCKED
DIAGNOSTIC_OUTPUT_ISOLATED
```

## Validação

A ferramenta:

```text
tools/validate_phase11_11f_limited_gate_fixtures.py
```

valida a presenca dos seis cenarios, a metadata, os bloqueios de dispatch e os
flags que preservam PKN como default retrocompativel.

Classificacao esperada:

```text
LIMITED_GATE_FIXTURES_VALID
```

## O que permanece bloqueado

- Dispatch fisico runtime.
- BUZ29-PENNY.
- `PENNY_SHAPED` como modelo fisico operacional.
- Qualquer declaracao de equivalencia com legado.
- Qualquer mudanca no comportamento fisico PKN.

## Próxima fase recomendada

```text
PHASE11_11G_VALIDATE_LIMITED_GATE_ON_CONTROLLED_CASES
```

## Atualização 11.11G — validação controlada

A Fase 11.11G valida os fixtures da 11.11F como casos controlados do contrato
`limited_gate`. O resultado esperado e:

```text
LIMITED_GATE_CONTROLLED_CASES_VALID
PKN_OUTPUTS_UNCHANGED_WITH_LIMITED_GATE
DIAGNOSTIC_OUTPUT_ISOLATED
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

A validacao permanece diagnostica e nao habilita dispatch fisico.
