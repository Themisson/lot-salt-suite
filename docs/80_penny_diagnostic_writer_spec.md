# Fase 11.10F — especificação do writer diagnóstico PennyShaped

## Resumo executivo

A Fase 11.10F especifica como uma fase futura deve implementar um writer
diagnóstico PennyShaped opt-in, compatível com o contrato axissimétrico de 1 rad
e os fixtures materializados na Fase 11.10E.

Status:

```text
PHASE11_10F_PENNY_DIAGNOSTIC_WRITER_SPECIFIED
PENNY_DIAGNOSTIC_WRITER_SPECIFIED
IMPLEMENTATION_NOT_ALLOWED_IN_11_10F
RUNTIME_EXECUTION_NOT_ALLOWED_IN_11_10F
AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_READY_FOR_WRITER_IMPLEMENTATION
FIXTURES_READY_FOR_WRITER_IMPLEMENTATION
```

A 11.10F não implementa o writer diagnóstico PennyShaped. Ela apenas especifica
como uma fase futura deverá implementar o writer de forma opt-in, isolada e
compatível com as fixtures 11.10E.

## Contexto pós-11.10E

A Fase 11.10D definiu:

```text
AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_SPECIFIED
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED
```

A Fase 11.10E materializou esse contrato em fixtures versionadas:

```text
tests/fixtures/comparison/phase11_10e/penny_diagnostic_output_expected.json
tests/fixtures/comparison/phase11_10e/penny_diagnostic_output_expected.csv
tests/fixtures/comparison/phase11_10e/penny_diagnostic_output_metadata.json
```

Essas fixtures são válidas, mas ainda não há writer runtime:

```text
PENNY_DIAGNOSTIC_OUTPUT_FIXTURES_VALID
FIXTURE_ONLY_NO_RUNTIME_WRITER
IMPLEMENTATION_NOT_ALLOWED_IN_11_10E
```

## Objetivo do writer futuro

O writer futuro deve gerar saídas JSON/CSV diagnósticas para a trilha
PennyShaped, preservando:

- campos internos em `axisymmetric_1rad`;
- equivalentes `2π` quando a origem 1 rad for geometricamente integrável;
- `source` para qualquer equivalente `2π`;
- caveats obrigatórios;
- flags que impedem interpretação física indevida.

A saída do writer não implica validação física, equivalência com legado nem caso
de simulação ativo.

## O que o writer deve fazer

O writer futuro deve:

1. Receber uma entrada estruturada de diagnóstico, não um `CaseData` completo.
2. Emitir JSON com os campos contratuais da Fase 11.10E.
3. Emitir CSV com cabeçalho equivalente e uma linha por registro diagnóstico.
4. Preservar `fracture_volume_proxy_1rad_m3`.
5. Preservar `solid_volume_1rad_m3`, quando disponível.
6. Calcular equivalentes `2π` somente quando a fonte 1 rad for preservada.
7. Emitir `fracture_volume_equivalent_2pi_source`.
8. Emitir `solid_volume_equivalent_2pi_source`.
9. Manter `volume_multiplier` como campo empírico separado.
10. Manter `physically_validated=false`, `legacy_equivalent=false`,
    `active_simulation_case=false` e `diagnostic_only=true`.

## O que o writer não deve fazer

O writer futuro não deve:

- alterar `PknModel`, `PknRunner`, `volumetric_balance` ou `pkn_direct`;
- conectar BUZ29-PENNY ao runtime oficial;
- executar o modelo PennyShaped;
- recalcular pressão, abertura ou sigmaTheta;
- consumir `legacy/` ou `legance/` em runtime;
- tratar `volume_multiplier` como fator geométrico `2π`;
- declarar validação física;
- declarar equivalência com o LOT_Tese.

## Entradas esperadas

A API conceitual futura pode ser ajustada na implementação, mas deve preservar
este contrato semânticamente:

```cpp
struct PennyDiagnosticOutputInput {
    std::string case_id;
    std::string model;
    std::string route;

    bool diagnostic_only;
    bool physically_validated;
    bool legacy_equivalent;
    bool active_simulation_case;

    double axisymmetric_angle_rad;
    double volume_conversion_factor_1rad_to_2pi;

    double volume_multiplier;
    std::string volume_multiplier_semantics;
    bool volume_multiplier_is_2pi;

    double fracture_volume_proxy_1rad_m3;
    double solid_volume_1rad_m3;

    std::string fracture_volume_equivalent_2pi_source;
    std::string solid_volume_equivalent_2pi_source;

    std::vector<std::string> required_caveats;
};
```

Saída conceitual mínima:

```cpp
struct PennyDiagnosticOutputRecord {
    double fracture_volume_equivalent_2pi_m3;
    double solid_volume_equivalent_2pi_m3;
    std::string volume_interpretation;
};
```

## Saídas JSON

O JSON futuro deve conter, no mínimo:

```text
case_id
phase
track
model
axisymmetric_angle_rad
axisymmetric_basis
volume_conversion_factor_1rad_to_2pi
volume_multiplier
volume_multiplier_semantics
volume_multiplier_interpretation
volume_multiplier_is_2pi
fracture_volume_proxy_1rad_m3
fracture_volume_equivalent_2pi_m3
fracture_volume_equivalent_2pi_source
solid_volume_1rad_m3
solid_volume_equivalent_2pi_m3
solid_volume_equivalent_2pi_source
volume_interpretation
physically_validated
legacy_equivalent
active_simulation_case
diagnostic_only
runtime_writer_implemented
implementation_allowed
source_contract
source_phase
recommended_next_phase
required_caveats
```

## Saídas CSV

O CSV futuro deve conter os mesmos campos escalares do JSON. Para a rota mínima
de diagnóstico, uma linha por registro é suficiente. Campos vetoriais como
`required_caveats` devem permanecer em metadata JSON, ou serem serializados
apenas se uma fase futura definir uma codificação explícita.

## Metadata e caveats

Metadata obrigatória:

```text
phase
status
fixture_status
implementation_status
contract_materialized
axisymmetric_angle_rad
axisymmetric_basis
volume_conversion_factor_1rad_to_2pi
volume_multiplier_semantics
volume_multiplier_interpretation
volume_multiplier_is_2pi
json_fixture
csv_fixture
source_contract
physically_validated
legacy_equivalent
active_simulation_case
diagnostic_only
implementation_allowed
runtime_writer_implemented
recommended_next_phase
required_caveats
forbidden_interpretations
```

Caveats obrigatórios para o writer futuro:

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
NOT_ACTIVE_SIMULATION_CASE
DIAGNOSTIC_ONLY
```

Durante a 11.10F, os caveats adicionais são:

```text
IMPLEMENTATION_NOT_ALLOWED_IN_11_10F
RUNTIME_EXECUTION_NOT_ALLOWED_IN_11_10F
```

## Regras de conversão 1 rad → 2π

O writer futuro deve preservar simultaneamente as grandezas internas em 1 rad e
os equivalentes totais em 2π, quando aplicáveis. O campo volume_multiplier
permanece empírico e não pode ser reutilizado como fator geométrico 2π.

Regras:

```text
fracture_volume_equivalent_2pi_m3 =
  fracture_volume_proxy_1rad_m3 * 2π

solid_volume_equivalent_2pi_m3 =
  solid_volume_1rad_m3 * 2π
```

Essas regras só podem ser aplicadas quando:

1. o campo de origem for geometricamente integrável;
2. o campo de origem 1 rad for preservado na saída;
3. `source`/caveat estiver presente para o equivalente `2π`;
4. a saída não interpretar `volume_multiplier` como conversão angular.

## Tratamento de volume_multiplier

`volume_multiplier` permanece:

```text
VOLUME_MULTIPLIER_EMPIRICAL
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
volume_multiplier_is_2pi = false
```

Ele pode ser reportado e preservado, mas não deve participar da conversão
geométrica 1 rad → 2π.

## Flags de validação

Até validação futura dedicada, o writer deve emitir:

```text
physically_validated = false
legacy_equivalent = false
active_simulation_case = false
diagnostic_only = true
```

Essas flags não são decorativas: elas fazem parte do contrato para impedir que
fixtures ou saídas diagnósticas sejam confundidas com simulação física ativa.

## Arquivos C++ prováveis para implementação futura

Uma implementação futura deve permanecer opt-in e isolada. Arquivos prováveis:

```text
include/io/PennyShapedDiagnosticWriter.hpp
src/io/PennyShapedDiagnosticWriter.cpp
tests/cpp/test_penny_shaped_diagnostic_writer.cpp
```

Alternativa aceitável, se a arquitetura preferir manter saídas não-runtime fora
de `io/`:

```text
include/lot/PennyShapedDiagnosticWriter.hpp
src/lot/PennyShapedDiagnosticWriter.cpp
```

Nesse caso, a fase futura deve justificar por que o writer pertence ao módulo
`lot` e confirmar que não contamina `PknModel` ou `PknRunner`.

## Testes C++ futuros

Testes mínimos recomendados:

- writer emite JSON com campos obrigatórios;
- writer emite CSV com cabeçalho compatível;
- `fracture_volume_equivalent_2pi_m3 == fracture_volume_proxy_1rad_m3 * 2π`;
- `solid_volume_equivalent_2pi_m3 == solid_volume_1rad_m3 * 2π`;
- `volume_multiplier_is_2pi == false`;
- `volume_multiplier_semantics == VOLUME_MULTIPLIER_EMPIRICAL`;
- flags de validação permanecem falsas;
- erro ou rejeição para equivalente `2π` sem `source`;
- casos sem writer não alteram `lot-pkn`.

## Testes Python futuros

Testes Python devem comparar a saída real do writer contra as fixtures 11.10E,
usando o validador:

```text
tools/validate_phase11_10e_penny_output_fixtures.py
```

A fase futura também deve verificar que artefatos em `results/` não são
versionados.

## Riscos

- Confundir fixture diagnóstica com saída de simulação ativa.
- Usar `volume_multiplier` como se fosse `2π`.
- Reportar volume equivalente sem preservar origem 1 rad.
- Declarar validação física antes de BUZ29-PENNY estar executável e auditado.
- Acoplar o writer ao fluxo LOT/PKN padrão.

## Próxima fase recomendada

```text
PHASE11_10G_IMPLEMENT_PENNY_DIAGNOSTIC_WRITER_OPT_IN
```

A 11.10G poderá implementar C++ somente se preservar o escopo opt-in,
independência do `lot-pkn` e as flags de não validação física estabelecidas
nesta especificação.

## Resultado da Fase 11.10G

A Fase 11.10G implementou o writer especificado em:

```text
include/lot/PennyShapedDiagnosticWriter.hpp
src/lot/PennyShapedDiagnosticWriter.cpp
tests/cpp/test_penny_shaped_diagnostic_writer.cpp
```

Status:

```text
PENNY_DIAGNOSTIC_WRITER_IMPLEMENTED_OPT_IN
NO_BUZ29_RUNTIME_EXECUTION
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
```

O writer permanece isolado, sem runner não-PKN, sem CLI, sem parser/schema e
sem alteração do fluxo `lot-pkn`.

## Resultado da Fase 11.10H

A Fase 11.10H registrou o gate do runner diagnóstico não-PKN:

```text
NON_PKN_DIAGNOSTIC_RUNNER_SPEC_PARTIAL
RUNNER_IMPLEMENTATION_NOT_ALLOWED_IN_11_10H
BUZ29_RUNTIME_EXECUTION_NOT_ALLOWED
LOT_PKN_IMPACT_NOT_ALLOWED
```

O writer implementado na 11.10G pode participar de uma especificação futura de
runner, mas a 11.10H não implementa esse runner e não executa BUZ29-PENNY.

## Resultado da Fase 11.10I

A 11.10I especificou que o writer diagnóstico PennyShaped deve ser consumido,
se vier a ser consumido por runtime, dentro de uma rota LOT/fracture unificada
selecionada por `lot.fracture.fracture_model`. O default futuro deve ser `PKN`
quando o campo estiver ausente, e `PENNY_SHAPED` deve permanecer opt-in
explícito, diagnóstico e não fisicamente validado.
## Atualização 11.10J — writer não implica seleção runtime

O writer diagnóstico PennyShaped permanece opt-in e isolado. A Fase 11.10J
especifica que a seleção futura por `lot.fracture.fracture_model` não deve
executar o writer automaticamente; `PENNY_SHAPED` continua diagnóstico e
depende de seleção explícita, gate de início de fratura e convenção de sinal.
