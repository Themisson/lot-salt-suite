# Fase 11.10J — guard do seletor `fracture_model`

## Resumo executivo

A Fase 11.10J especifica o guard de seleção para o futuro campo:

```text
lot.fracture.fracture_model
```

Esta fase é somente especificação. Ela não implementa parser, schema, C++,
runner, CLI, execução BUZ29-PENNY ou alteração do fluxo `lot-pkn`.

Status registrado:

```text
FRACTURE_MODEL_SELECTOR_GUARD_SPECIFIED
PKN_DEFAULT_WHEN_ABSENT
EXPLICIT_EMPTY_FRACTURE_MODEL_REJECTED
PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY
UNSUPPORTED_FRACTURE_MODELS_BLOCKED
FRACTURE_INITIATION_GATE_REQUIRED
SIGMATHETA_SIGN_CONVENTION_REQUIRED
NO_RUNTIME_CHANGE_IN_11_10J
```

## Texto normativo

A ausência de lot.fracture.fracture_model deve preservar o comportamento histórico e selecionar PKN como default. Um valor vazio explícito não é equivalente à ausência do campo e deve ser tratado como erro.

PENNY_SHAPED só pode ser selecionado por opt-in explícito. Mesmo quando selecionado, permanece diagnóstico, não fisicamente validado e não equivalente ao legado.

A seleção do fracture_model não implica execução imediata. A execução depende do fracture_initiation_gate e da convenção de sinal explícita para sigma_theta.

## Regra de seleção

| Entrada | Modelo canônico | Status | Ação |
|---|---|---|---|
| campo ausente | `PKN` | `DEFAULT_TO_PKN` | aceitar |
| `PKN`, `pkn`, `lot-pkn`, `lot_pkn` | `PKN` | `EXPLICIT_PKN_ACCEPTED` | aceitar |
| `PENNY_SHAPED`, `penny_shaped`, `penny-shaped`, `penny` | `PENNY_SHAPED` | `PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY` | aceitar como diagnóstico |
| string vazia | nenhum | `EXPLICIT_EMPTY_FRACTURE_MODEL_REJECTED` | erro |
| `KGD`, `KGD_CIRCULAR`, `KGD_ELLIPTICAL`, `RADIAL`, `ELLIPTICAL`, `UNKNOWN` | nenhum | `UNSUPPORTED_FRACTURE_MODEL_REJECTED` | erro |

## Estados de seleção e execução

| Estado de seleção | Estado de execução | Observação |
|---|---|---|
| `PKN_SELECTED_BY_ABSENCE` | `OFFICIAL_LOT_PKN_RUNTIME` | preserva casos existentes |
| `PKN_SELECTED_EXPLICITLY` | `OFFICIAL_LOT_PKN_RUNTIME` | deve ser compatível com ausência do campo |
| `PENNY_SHAPED_SELECTED_EXPLICITLY` | `DIAGNOSTIC_OPT_IN_ONLY` | depende de gates adicionais |
| `UNSUPPORTED_SELECTED` | `BLOCKED` | deve falhar antes de dispatch para solver |

## Gates obrigatórios

O guard futuro deve separar três decisões:

1. seleção do modelo de fratura;
2. autorização de início de fratura;
3. execução do modelo selecionado.

Para `PENNY_SHAPED`, a seleção explícita ainda não basta. A rota deve exigir:

```text
FRACTURE_INITIATION_GATE_REQUIRED
SIGMATHETA_SIGN_CONVENTION_REQUIRED
```

Assim, `sigma_theta_compression_positive_Pa` deve permanecer explícito na
álgebra de decisão, e a convenção de compressão positiva não deve ser inferida
implicitamente.

## Escopo preservado

A 11.10J não altera:

- `src/`;
- `include/`;
- `apps/`;
- `CMakeLists.txt`;
- `schemas/`;
- `legacy/`;
- `legance/`;
- `external/saltcreep/`;
- casos protegidos;
- comportamento de `lot-sim run --mode lot-pkn`.

## Próxima fase recomendada

```text
PHASE11_10K_IMPLEMENT_FRACTURE_MODEL_SELECTOR_GUARD
```

A próxima fase pode implementar o guard de forma mínima e testável, desde que
preserve o default PKN, rejeite valores vazios explícitos, bloqueie modelos não
suportados e mantenha `PENNY_SHAPED` como opt-in diagnóstico.

## Implementação 11.10K

A Fase 11.10K implementa essa especificação como helper C++ isolado:

```text
include/lot/FractureModelSelector.hpp
src/lot/FractureModelSelector.cpp
```

O helper ainda não é integrado ao parser, schema, CLI ou runtime oficial.
Sua função é congelar a semântica de seleção antes da fase de integração.

## Especificação parser/schema 11.10L

A Fase 11.10L define como essa integração deve ocorrer futuramente:

```text
lot.fracture.fracture_model
SCHEMA_STRICT_CANONICAL_ONLY
PKN_DEFAULT_PARSER_BEHAVIOR_REQUIRED
PARSER_SCHEMA_INTEGRATION_ALLOWED_NEXT
RUNTIME_EXECUTION_NOT_ALLOWED_NEXT
```

A fase não altera parser, schema ou runtime.
