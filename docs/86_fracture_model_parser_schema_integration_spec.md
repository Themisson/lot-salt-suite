# Fase 11.10L — especificação da integração parser/schema de `fracture_model`

## Resumo executivo

A 11.10L não integra o guard ao parser, schema, CLI ou runtime. Ela apenas especifica como a integração deverá ocorrer em fase futura.

A fase define o contrato futuro para:

```text
lot.fracture.fracture_model
```

Status registrado:

```text
PHASE11_10L_FRACTURE_MODEL_PARSER_SCHEMA_INTEGRATION_SPECIFIED
FRACTURE_MODEL_FIELD_LOT_FRACTURE_FRACTURE_MODEL
PKN_DEFAULT_PARSER_BEHAVIOR_REQUIRED
EXPLICIT_EMPTY_FRACTURE_MODEL_BLOCKED
UNSUPPORTED_FRACTURE_MODELS_BLOCKED
PARSER_SCHEMA_INTEGRATION_ALLOWED_NEXT
RUNTIME_EXECUTION_NOT_ALLOWED_NEXT
BUZ29_EXECUTION_NOT_ALLOWED_NEXT
```

## Contexto pós-11.10K

A Fase 11.10K implementou `FractureModelSelector` como helper C++ isolado. Ele
normaliza `PKN` e `PENNY_SHAPED`, rejeita valor vazio explícito e bloqueia
modelos não suportados. Esse helper ainda não é usado pelo parser, schema, CLI
ou runtime.

## Parser/schema atuais

Auditoria sem alteração:

| Item | Local atual | Observação |
|---|---|---|
| Leitura YAML | `src/io/CaseParser.cpp::parse_yaml` | Lê `lot.fracture.geometry` |
| Header parser | `include/io/CaseParser.hpp` | Expõe `parse_yaml` |
| Estrutura de caso | `include/core/types.hpp::LotConfig` | Possui `model` e `fracture_geometry`; não possui `fracture_model` |
| Schema | `schemas/lot_case.schema.yaml` | `lot.fracture` exige `geometry` e usa `additionalProperties: false` |
| Validação `lot-pkn` | `src/io/CaseParser.cpp` | Exige `lot.model/fracture.geometry pkn` |

O menor ponto seguro de integração futura é no parser, imediatamente após ler
`lot.fracture`, antes das validações específicas de `lot-pkn`, armazenando a
seleção em `CaseData` apenas se uma fase futura adicionar campo estruturado para
isso.

## Campo `lot.fracture.fracture_model`

Campo futuro:

```yaml
lot:
  fracture:
    fracture_model: PKN
```

A ausência de lot.fracture.fracture_model deve preservar compatibilidade retroativa e defaultar para PKN. Valor vazio explícito deve ser erro.

## Campo ausente

Comportamento futuro:

```text
selected_fracture_model = PKN
selection_source = DEFAULTED
validation_error = false
backward_compatible = true
```

## PKN explícito

Comportamento futuro:

```text
selected_fracture_model = PKN
selection_source = EXPLICIT
validation_error = false
```

## PENNY_SHAPED explícito

Comportamento futuro:

```text
selected_fracture_model = PENNY_SHAPED
selection_source = EXPLICIT
diagnostic_only = true
runtime_supported_now = false
```

A integração parser/schema não autoriza execução BUZ29-PENNY, não valida PENNY_SHAPED fisicamente e não deve alterar o comportamento dos casos PKN existentes.

## Valor vazio explícito

Comportamento futuro:

```text
lot.fracture.fracture_model: ""
```

deve falhar com:

```text
EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED
```

## Modelos não suportados

Entradas como:

```text
KGD
KGD_CIRCULAR
KGD_ELLIPTICAL
RADIAL
ELLIPTICAL
UNKNOWN
```

devem falhar com:

```text
UNSUPPORTED_FRACTURE_MODEL
```

## Política de schema

Recomendação:

```text
SCHEMA_STRICT_CANONICAL_ONLY
```

Schema futuro recomendado:

```yaml
lot:
  fracture:
    fracture_model:
      type: string
      enum:
        - PKN
        - PENNY_SHAPED
```

Regras:

1. ausência do campo é permitida;
2. ausência defaulta para PKN no parser/selector;
3. string vazia explícita é inválida;
4. aliases como `pkn` e `penny` seguem aceitos pelo helper, mas não devem virar
   YAML oficial sem decisão explícita;
5. se o schema permanecer estrito, o YAML oficial deve usar valores canônicos.

## Testes futuros

A próxima fase deve cobrir:

- casos PKN existentes sem `fracture_model` continuam válidos;
- `fracture_model: PKN` é válido;
- `fracture_model: PENNY_SHAPED` é aceito apenas como seleção diagnóstica;
- `fracture_model: ""` é rejeitado;
- `fracture_model: KGD`, `RADIAL` e `UNKNOWN` são rejeitados;
- `lot-pkn` não muda comportamento nem saída.

## O que a próxima fase pode implementar

Se autorizada, a próxima fase pode:

```text
parser_integration_allowed_next = true
schema_integration_allowed_next = true
```

## O que a próxima fase ainda não pode executar

Permanece bloqueado:

```text
runtime_execution_allowed_next = false
buz29_execution_allowed_next = false
lot_pkn_behavior_change_allowed = false
```

## Próxima fase recomendada

```text
PHASE11_10M_INTEGRATE_FRACTURE_MODEL_IN_PARSER_SCHEMA
```
