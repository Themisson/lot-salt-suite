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

## Resultado da Fase 11.10C

A auditoria matemática posterior classificou o núcleo usado pelo adapter como:

```text
primary_classification = PENNY_MATH_HYDRAULIC_DIAGNOSTIC_SCALING
secondary_classification = PENNY_MATH_AXISYMMETRIC_1RAD_PROXY
math_audit_passed = true
requires_code_correction = false
requires_output_contract = true
```

Essa classificação preserva o adapter atual: não há correção C++ obrigatória.
O próximo passo técnico é definir contrato de saída para separar grandezas
internas em 1 rad e volumes equivalentes 2π antes de qualquer uso físico forte
do `fracture_volume_proxy_m3`.

## Resultado da Fase 11.10D

A 11.10D definiu esse contrato como especificação documental:

```text
AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_SPECIFIED
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
IMPLEMENTATION_NOT_ALLOWED_IN_11_10D
```

O adapter C++ permanece inalterado. Uma futura fase poderá criar fixtures de
saída diagnóstica com `fracture_volume_proxy_1rad_m3`,
`fracture_volume_equivalent_2pi_m3` e `fracture_volume_equivalent_2pi_source`
antes de qualquer writer/runtime.

## Resultado da Fase 11.10E

A 11.10E criou fixtures de saída diagnóstica para esse contrato, ainda sem
alterar o adapter:

```text
PENNY_DIAGNOSTIC_OUTPUT_FIXTURES_VALID
FIXTURE_ONLY_NO_RUNTIME_WRITER
IMPLEMENTATION_NOT_ALLOWED_IN_11_10E
```

Os fixtures vivem em `tests/fixtures/comparison/phase11_10e/` e são validados
por `tools/validate_phase11_10e_penny_output_fixtures.py`. Eles não representam
execução BUZ29-PENNY nem writer C++ real; apenas fixam o contrato esperado para
uma futura implementação opt-in.

## Resultado da Fase 11.10F

A 11.10F especificou o writer diagnóstico PennyShaped futuro, ainda sem alterar
o adapter:

```text
PENNY_DIAGNOSTIC_WRITER_SPECIFIED
IMPLEMENTATION_NOT_ALLOWED_IN_11_10F
RUNTIME_EXECUTION_NOT_ALLOWED_IN_11_10F
```

O writer futuro deve ser opt-in, emitir JSON/CSV compatíveis com as fixtures
11.10E e preservar `volume_multiplier` como empírico, separado da conversão
geométrica `1rad -> 2pi`.

## Resultado da Fase 11.10G

A 11.10G implementou `PennyShapedDiagnosticWriter` como componente C++ isolado
em `include/lot/` e `src/lot/`. O adapter existente permanece inalterado: a
nova classe apenas escreve saídas diagnósticas a partir de uma entrada
estruturada, sem executar BUZ29-PENNY, sem conectar CLI e sem alterar o fluxo
`lot-pkn`.

O writer exige os caveats diagnósticos, preserva `*_1rad_m3`, calcula os
equivalentes `*_equivalent_2pi_m3` com `source` explícito e rejeita
`physically_validated=true`, `legacy_equivalent=true`,
`active_simulation_case=true` e `volume_multiplier_is_2pi=true`.

## Resultado da Fase 11.10H

A 11.10H auditou o caminho adapter → writer e registrou:

```text
NON_PKN_DIAGNOSTIC_RUNNER_SPEC_PARTIAL
runner_implementation_allowed_now = false
buz29_runtime_execution_allowed = false
lot_pkn_impact_allowed = false
```

O adapter e o writer podem ser conectados por especificação futura, mas a
execução BUZ29-PENNY segue bloqueada por entradas parciais e semânticas ainda
deferidas. Nenhum C++ foi alterado na 11.10H.
