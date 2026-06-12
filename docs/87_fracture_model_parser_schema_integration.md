# Fase 11.10M — integração parser/schema de `fracture_model`

## Resumo executivo

A Fase 11.10M integra o campo:

```text
lot.fracture.fracture_model
```

ao schema YAML e ao parser C++ com default retrocompatível `PKN`. A integração
usa o helper isolado `FractureModelSelector`, criado na Fase 11.10K, e grava a
seleção em `CaseData` como metadados de seleção. A fase não altera
`PknRunner`, `PknModel`, CLI, writer ou qualquer dispatch runtime.

A integração parser/schema de lot.fracture.fracture_model não autoriza execução runtime do modelo selecionado nesta fase.

## Contexto pós-11.10L

A Fase 11.10L especificou que o campo deveria ser integrado com:

```text
SCHEMA_STRICT_CANONICAL_ONLY
PKN_DEFAULT_PARSER_BEHAVIOR_REQUIRED
EXPLICIT_EMPTY_FRACTURE_MODEL_BLOCKED
UNSUPPORTED_FRACTURE_MODELS_BLOCKED
RUNTIME_EXECUTION_NOT_ALLOWED_NEXT
BUZ29_EXECUTION_NOT_ALLOWED_NEXT
```

A 11.10M implementa apenas a parte parser/schema desse contrato.

## Campo integrado

Campo oficial:

```yaml
lot:
  fracture:
    fracture_model: PKN
```

A ausência de lot.fracture.fracture_model preserva compatibilidade retroativa e seleciona PKN como default.

## Política de schema

O schema `schemas/lot_case.schema.yaml` segue a política:

```text
SCHEMA_STRICT_CANONICAL_ONLY
```

Valores canônicos aceitos:

```text
PKN
PENNY_SHAPED
```

Aliases continuam responsabilidade do helper C++ em testes/unitários, mas o
YAML oficial deve usar valores canônicos.

## Default PKN

Quando `fracture_model` está ausente, o parser chama `FractureModelSelector`
com campo ausente e registra:

```text
fracture_model = PKN
fracture_model_selection_source = DEFAULTED
fracture_model_route = lot-pkn
fracture_model_runtime_dispatch_enabled = false
```

Esse comportamento preserva os casos PKN existentes.

## PKN explícito

Quando o YAML declara:

```yaml
fracture_model: PKN
```

o parser registra:

```text
fracture_model = PKN
fracture_model_selection_source = EXPLICIT
fracture_model_runtime_supported_now = true
fracture_model_runtime_dispatch_enabled = false
```

Mesmo com PKN explícito, a fase não introduz novo dispatch: `lot-pkn` continua
o caminho runtime existente.

## PENNY_SHAPED explícito

Quando o YAML declara:

```yaml
fracture_model: PENNY_SHAPED
```

o parser aceita a seleção como metadado diagnóstico:

```text
fracture_model = PENNY_SHAPED
fracture_model_selection_source = EXPLICIT
fracture_model_diagnostic_only = true
fracture_model_physically_validated = false
fracture_model_legacy_equivalent = false
fracture_model_runtime_supported_now = false
fracture_model_runtime_dispatch_enabled = false
```

Isso não executa BUZ29-PENNY, não cria equivalência com o legado e não altera
o comportamento físico de `lot-sim run --mode lot-pkn`.

## Valor vazio explícito

Valor vazio explícito:

```yaml
fracture_model: ""
```

é rejeitado pelo helper com mensagem contendo:

```text
EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED
```

Valor vazio não é equivalente a campo ausente.

## Modelos não suportados

Modelos não suportados, por exemplo:

```text
KGD
RADIAL
UNKNOWN
```

são rejeitados com mensagem contendo:

```text
UNSUPPORTED_FRACTURE_MODEL
```

## Garantia de não execução runtime

A seleção fica armazenada em `CaseData`, mas não é consumida por `PknRunner`,
`PknModel`, CLI ou writer. O campo:

```text
fracture_model_runtime_dispatch_enabled = false
```

registra explicitamente esse estado. BUZ29-PENNY não foi executado nesta fase.

## Gate físico futuro: sigma_theta inicial

Antes de qualquer dispatch real de fratura, deve ser auditado se sigma_theta_compression_positive_Pa está inicializado com o estado geomecânico pós-perfuração e se o fracture_initiation_gate não está sendo avaliado com tensão tangencial nula ou não inicializada.

Classificação futura registrada:

```text
cause = FRACTURE_GATE_MAY_BE_EVALUATED_BEFORE_INITIAL_STRESS_STATE
gate = SIGMATHETA_INITIAL_STATE_REQUIRED_BEFORE_MODEL_DISPATCH
secondary_cause = POSSIBLE_PRESSURE_SIGMATHETA_REFERENCE_MISMATCH
secondary_gate = ALIGN_PRESSURE_AND_SIGMATHETA_SEMANTICS_BEFORE_FRACTURE_MODEL_SELECTION
```

Motivo: o `t = 0` do LOT não é necessariamente o `t = 0` da perfuração. Em
rochas salinas ou viscoelásticas, a resposta elástica inicial da perfuração
pode já ter alterado o estado tangencial antes do início do LOT.

## Testes

A fase adiciona cobertura para:

- campo ausente defaultando para `PKN`;
- `fracture_model: PKN`;
- `fracture_model: PENNY_SHAPED`;
- valor vazio explícito;
- `KGD`;
- `RADIAL`;
- auditoria Python da integração;
- preservação de `runtime_dispatch_enabled = false`.

## Próxima fase recomendada

```text
PHASE11_10N_AUDIT_FRACTURE_INITIATION_GATE_INITIAL_SIGMATHETA_STATE
```

Essa fase deve ocorrer antes de qualquer dispatch físico por
`fracture_model`.

## Resultado da auditoria 11.10N

A Fase 11.10N executa a auditoria do gate acima e mantém o dispatch bloqueado:

```text
sigmatheta_initial_state = SIGMATHETA_INITIAL_STATE_MISSING
fracture_gate_status = FRACTURE_GATE_REQUIRES_INITIAL_STATE_WIRING
pressure_semantics = PRESSURE_SIGMATHETA_SEMANTICS_PARTIAL_REQUIRES_ALIGNMENT
sign_convention = SIGN_CONVENTION_REQUIRES_REVIEW
dispatch_allowed_next = false
runtime_execution_allowed_next = false
buz29_execution_allowed_next = false
```

O motivo é que o runtime `lot-pkn` já consegue consumir sigma-theta por rota
diagnóstica, mas ainda não comprova um estado inicial tangencial
pós-perfuração antes do gate. A próxima fase segura é
`PHASE11_10O_SPECIFY_SIGMATHETA_INITIAL_STATE_WIRING`.

## Resultado da especificação 11.10O

A Fase 11.10O não altera parser/schema, mas define o contrato que uma fase
futura deverá implementar antes de qualquer dispatch:

```text
wiring_spec_status = SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED
preferred_source = ELASTIC_INITIAL_WELLBORE_STATE
dispatch_allowed_next = false
runtime_execution_allowed_next = false
implementation_allowed_next = true
recommended_next_phase = PHASE11_10P_IMPLEMENT_SIGMATHETA_INITIAL_STATE_WIRING_GUARD
```

O parser/schema pode continuar armazenando `fracture_model`, mas a execução
continua bloqueada até que o guard valide o estado inicial
`AFTER_DRILLING_BEFORE_LOT`, a convenção `COMPRESSION_POSITIVE` e a
compatibilidade entre pressão e referencial de `sigma_theta`.

## Resultado da implementacao 11.10P

A Fase 11.10P implementa `SigmaThetaInitialStateGuard` como helper C++ isolado
para validar `sigma_theta_initial_compression_positive_Pa`, fonte, tempo de
estado, referencial, convencao de sinal e semantica de pressao antes de uma
futura avaliacao do `fracture_initiation_gate`.

Esta fase nao altera parser ou schema. O campo
`lot.fracture.fracture_model` continua integrado conforme a 11.10M, mas nenhum
dispatch fisico novo e habilitado:

```text
PARSER_SCHEMA_NOT_CHANGED
RUNTIME_DISPATCH_NOT_CHANGED
LOT_PKN_BEHAVIOR_NOT_CHANGED
SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED
```

## Resultado da especificacao 11.10Q

A Fase 11.10Q nao altera parser/schema. Ela apenas especifica como o futuro
`fracture_initiation_gate` deve consultar `SigmaThetaInitialStateGuard` depois
da selecao por `FractureModelSelector`.

Status:

```text
FRACTURE_GATE_DISPATCH_WITH_SIGMATHETA_GUARD_SPECIFIED
PARSER_SCHEMA_NOT_CHANGED
RUNTIME_DISPATCH_NOT_CHANGED
DISPATCH_REMAINS_BLOCKED
```

O criterio pressao x sigma-theta permanece como requisito da 11.10R.
