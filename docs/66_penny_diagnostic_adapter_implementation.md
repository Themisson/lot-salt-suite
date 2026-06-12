# Fase 11.8D — adapter diagnóstico PennyShaped

## Resumo executivo

A Fase 11.8D implementa um adapter C++ opt-in em torno do núcleo isolado
`PennyShapedModel`. O adapter existe apenas para diagnóstico e testes
controlados; ele não altera o parser, schema, CLI, `PknModel`, `PknRunner` ou o
fluxo `lot-sim run --mode lot-pkn`.

Status:

```text
PENNY_SHAPED_DIAGNOSTIC_ADAPTER_IMPLEMENTED
```

## API criada

Arquivos:

```text
include/lot/PennyShapedDiagnosticAdapter.hpp
src/lot/PennyShapedDiagnosticAdapter.cpp
tests/cpp/test_penny_shaped_diagnostic_adapter.cpp
```

Contrato:

```cpp
struct PennyShapedDiagnosticInput;
struct PennyShapedDiagnosticResult;

PennyShapedInput make_penny_shaped_input(
    const PennyShapedDiagnosticInput& input);

PennyShapedDiagnosticResult run_penny_shaped_diagnostic(
    const PennyShapedDiagnosticInput& input);
```

O adapter copia os campos SI do input diagnóstico para `PennyShapedInput`,
chama `evaluate_penny_shaped_model(...)` e retorna o resultado com metadados
`source`, `caveat` e `status`.

## Escopo preservado

Esta fase não:

- cria modo `lot-sim`;
- altera parser;
- altera schema;
- cria YAML BUZ29;
- altera `PknModel`;
- altera `PknRunner`;
- declara equivalência com LOT_Tese;
- valida BUZ29.

## Testes

Os testes Catch2 cobrem:

- mapeamento do input diagnóstico para `PennyShapedInput`;
- resultado finito;
- equivalência com chamada direta do núcleo;
- propagação das validações do modelo;
- independência explícita em relação ao LOT/PKN.

## Próxima fase

```text
PHASE11_9A_PENNY_SYNTHETIC_MINIMAL_CASE
```

A próxima fase pode criar um caso sintético mínimo e verificador diagnóstico,
sem promover a rota para parser/schema oficial.

## Resultado da Fase 11.9A

A fase seguinte criou o caso sintético mínimo:

```text
cases/validation/non_pkn/penny_shaped_synthetic_minimal.yaml
```

O caso é verificado por `tools/verify_phase11_9a_penny_synthetic_case.py` e
permanece fora do parser/schema oficial.
