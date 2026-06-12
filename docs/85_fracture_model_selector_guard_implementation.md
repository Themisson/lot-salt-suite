# Fase 11.10K — implementação do guard `fracture_model`

## Resumo executivo

A 11.10K implementa apenas o helper/guard C++ isolado para seleção de fracture_model. Ela não integra o guard ao parser, schema, CLI ou runtime oficial.

O helper criado é:

```text
include/lot/FractureModelSelector.hpp
src/lot/FractureModelSelector.cpp
tests/cpp/test_fracture_model_selector.cpp
```

Status registrado:

```text
PHASE11_10K_FRACTURE_MODEL_SELECTOR_GUARD_IMPLEMENTED
FRACTURE_MODEL_SELECTOR_GUARD_IMPLEMENTED
PKN_DEFAULT_WHEN_FRACTURE_MODEL_MISSING
PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY
EXPLICIT_EMPTY_FRACTURE_MODEL_BLOCKED
UNSUPPORTED_FRACTURE_MODELS_BLOCKED
PARSER_SCHEMA_RUNTIME_NOT_INTEGRATED
```

## Contexto pós-11.10J

A Fase 11.10J especificou o guard futuro para:

```text
lot.fracture.fracture_model
```

A 11.10K materializa essa regra como biblioteca/helper isolado para testes e
integração futura. Ela não altera o contrato YAML atual, não altera o schema e
não muda o fluxo `lot-sim run --mode lot-pkn`.

## API C++

```cpp
namespace lss::lot {

enum class FractureModelKind {
  Pkn,
  PennyShaped,
};

enum class FractureModelSelectionSource {
  Defaulted,
  Explicit,
};

struct FractureModelSelectionInput {
  bool has_fracture_model_field = false;
  std::string fracture_model_value;
};

struct FractureModelSelectionResult {
  FractureModelKind kind;
  FractureModelSelectionSource source;
  std::string canonical_name;
  std::string route;
  bool diagnostic_only;
  bool physically_validated;
  bool legacy_equivalent;
  bool runtime_supported_now;
  bool requires_fracture_initiation_gate;
};

FractureModelSelectionResult select_fracture_model(
    const FractureModelSelectionInput& input);

std::string to_string(FractureModelKind kind);

}  // namespace lss::lot
```

## Regras de default

A ausência de fracture_model preserva o comportamento histórico e seleciona PKN. Valor vazio explícito é erro. PENNY_SHAPED é opt-in explícito e permanece diagnóstico, não validado e não equivalente ao legado.

Quando `has_fracture_model_field == false`, o resultado é:

```text
kind = Pkn
source = Defaulted
canonical_name = PKN
route = lot-pkn
diagnostic_only = false
runtime_supported_now = true
requires_fracture_initiation_gate = true
```

## Regras de normalização

| Entrada | Canônico |
|---|---|
| `PKN` | `PKN` |
| `pkn` | `PKN` |
| `lot-pkn` | `PKN` |
| `lot_pkn` | `PKN` |
| `PENNY_SHAPED` | `PENNY_SHAPED` |
| `penny_shaped` | `PENNY_SHAPED` |
| `penny-shaped` | `PENNY_SHAPED` |
| `penny` | `PENNY_SHAPED` |

## Regras de rejeição

Valor vazio explícito lança `std::invalid_argument` com:

```text
EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED
```

Modelos não suportados lançam `std::invalid_argument` com:

```text
UNSUPPORTED_FRACTURE_MODEL
```

Modelos bloqueados:

```text
KGD
KGD_CIRCULAR
KGD_ELLIPTICAL
RADIAL
ELLIPTICAL
UNKNOWN
```

## Estado PKN

`PKN` permanece o default e a única rota oficial suportada pelo runtime atual.
O helper não é chamado pelo parser, pelo CLI, pelo `PknModel` ou pelo
`PknRunner` nesta fase.

## Estado PENNY_SHAPED

`PENNY_SHAPED` é aceito somente como seleção explícita no helper isolado. O
resultado marca:

```text
diagnostic_only = true
physically_validated = false
legacy_equivalent = false
runtime_supported_now = false
```

Isso preserva a trilha diagnóstica e impede que a seleção seja confundida com
execução física validada.

## Interação futura com `fracture_initiation_gate`

Ambos os modelos retornam:

```text
requires_fracture_initiation_gate = true
```

A seleção do modelo não executa fratura. A fase futura de integração deverá
garantir que o dispatch só aconteça após o gate de iniciação e com convenção
explícita para `sigma_theta_compression_positive_Pa`.

## O que não foi integrado

Permanece falso nesta fase:

```text
parser_integrated = false
schema_integrated = false
runtime_integrated = false
buz29_executed = false
lot_pkn_behavior_changed = false
```

## Próxima fase recomendada

```text
PHASE11_10L_SPECIFY_PARSER_SCHEMA_INTEGRATION_FOR_FRACTURE_MODEL
```

A próxima fase deve decidir como integrar o guard ao parser/schema sem alterar
o comportamento dos casos PKN existentes.

## Especificação 11.10L

A Fase 11.10L especifica essa integração futura sem implementá-la. A política
recomendada é `SCHEMA_STRICT_CANONICAL_ONLY`, com `PKN` e `PENNY_SHAPED` como
valores canônicos, ausência do campo defaultando para PKN no parser, valor
vazio explícito como erro e runtime BUZ29-PENNY ainda bloqueado.
