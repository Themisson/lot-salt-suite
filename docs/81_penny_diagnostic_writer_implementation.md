# Fase 11.10G — implementação do writer diagnóstico PennyShaped

## Resumo executivo

A Fase 11.10G implementa o writer diagnóstico PennyShaped opt-in em C++,
compatível com o contrato axissimétrico de 1 rad e os fixtures materializados
na Fase 11.10E.

Status:

```text
PHASE11_10G_PENNY_DIAGNOSTIC_WRITER_IMPLEMENTED_OPT_IN
PENNY_DIAGNOSTIC_WRITER_IMPLEMENTED_OPT_IN
NO_BUZ29_RUNTIME_EXECUTION
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
```

A 11.10G implementa apenas o writer diagnóstico PennyShaped opt-in. Ela não
implementa runner, não executa BUZ29-PENNY, não valida fisicamente BUZ29 e não
declara equivalência com legado.

## Contexto pós-11.10F

A 11.10F especificou o writer futuro e autorizou a implementação isolada na
fase seguinte, preservando:

- saída JSON/CSV diagnóstica;
- grandezas internas em 1 rad;
- equivalentes 2π com `source`;
- `volume_multiplier` como campo empírico separado;
- flags explícitas de não validação física e não equivalência legada.

## Writer implementado

Arquivos C++:

```text
include/lot/PennyShapedDiagnosticWriter.hpp
src/lot/PennyShapedDiagnosticWriter.cpp
tests/cpp/test_penny_shaped_diagnostic_writer.cpp
```

O writer fica no módulo `lot` porque é uma saída diagnóstica da trilha
PennyShaped e não participa do writer oficial de resultados do `lot-sim`.
Ele não depende de `CaseData`, parser, schema, CLI, `PknModel` ou `PknRunner`.

## API C++

A API expõe:

```cpp
struct PennyShapedDiagnosticOutputInput;
struct PennyShapedDiagnosticOutputRecord;

std::vector<std::string> required_penny_shaped_diagnostic_writer_caveats();

PennyShapedDiagnosticOutputRecord
compute_penny_shaped_diagnostic_output_record(
    const PennyShapedDiagnosticOutputInput& input);

std::string write_penny_shaped_diagnostic_json_string(
    const PennyShapedDiagnosticOutputInput& input);

std::string write_penny_shaped_diagnostic_csv_header();

std::string write_penny_shaped_diagnostic_csv_row(
    const PennyShapedDiagnosticOutputInput& input);

void validate_penny_shaped_diagnostic_output_input(
    const PennyShapedDiagnosticOutputInput& input);
```

## Campos JSON

O JSON emitido inclui:

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

## Campos CSV

O CSV usa os mesmos campos escalares do JSON, sem serializar
`required_caveats`. A ordem do cabeçalho permanece estável para comparação com
fixtures.

## Conversão 1 rad → 2π

O writer preserva o valor interno em 1 rad e calcula o equivalente total em 2π
apenas para campos volumétricos geometricamente integráveis e com source/caveat
explícitos.

Regras implementadas:

```text
fracture_volume_equivalent_2pi_m3 =
  fracture_volume_proxy_1rad_m3 * volume_conversion_factor_1rad_to_2pi

solid_volume_equivalent_2pi_m3 =
  solid_volume_1rad_m3 * volume_conversion_factor_1rad_to_2pi
```

## Semântica de volume_multiplier

`volume_multiplier` permanece empírico e não é usado como fator geométrico
2π.

O writer rejeita:

- `volume_multiplier_is_2pi = true`;
- `volume_multiplier_semantics != VOLUME_MULTIPLIER_EMPIRICAL`;
- `volume_multiplier_interpretation != VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI`;
- `volume_multiplier` numericamente igual ao fator de conversão 2π.

## Caveats obrigatórios

O writer exige:

```text
PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED
AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED
VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI
NOT_PHYSICALLY_VALIDATED
NOT_LEGACY_EQUIVALENT
NOT_ACTIVE_SIMULATION_CASE
DIAGNOSTIC_ONLY
```

## Validações defensivas

O writer rejeita:

- `axisymmetric_angle_rad <= 0`;
- `volume_conversion_factor_1rad_to_2pi <= 0`;
- volumes 1 rad negativos ou não finitos;
- `physically_validated = true`;
- `legacy_equivalent = true`;
- `active_simulation_case = true`;
- `diagnostic_only = false`;
- sources 2π vazios;
- caveats obrigatórios ausentes.

## Testes C++

Os testes Catch2 cobrem:

- conversão do volume proxy de fratura 1 rad para 2π;
- conversão do volume sólido 1 rad para 2π;
- campos obrigatórios no JSON;
- cabeçalho CSV;
- linha CSV compatível com a fixture 11.10E;
- rejeição de flags proibidas;
- rejeição de caveats e sources ausentes;
- rejeição de dados angulares/volumétricos inválidos.

## Testes Python

A fase adiciona:

```text
tools/check_phase11_10g_penny_writer_against_fixtures.py
tests/python/test_check_phase11_10g_penny_writer_against_fixtures.py
```

A ferramenta valida que as fixtures 11.10E continuam compatíveis com o contrato
do writer e registra que a verificação runtime do writer é feita pelos testes
Catch2.

## O que não foi implementado

A Fase 11.10G não:

- implementa runner não-PKN;
- conecta PennyShaped ao CLI;
- executa BUZ29-PENNY;
- valida BUZ29 fisicamente;
- declara equivalência com LOT_Tese;
- altera `lot-pkn`;
- altera `PknModel`;
- altera `PknRunner`;
- altera parser, schema ou `CaseData`.

## Limitações

O writer emite strings JSON/CSV diagnósticas em memória. Não há ainda uma rota
oficial para gravar esses artefatos a partir de um caso moderno, porque isso
exigiria um gate separado para runner não-PKN.

## Próxima fase recomendada

```text
PHASE11_10H_SPECIFY_NON_PKN_DIAGNOSTIC_RUNNER_GATE
```

Uma alternativa aceitável, se a revisão preferir aumentar cobertura antes do
runner, é:

```text
PHASE11_10H_ADD_WRITER_OUTPUT_GOLDEN_TESTS
```

## Resultado da Fase 11.10H

A 11.10H escolheu a trilha de gate do runner não-PKN e registrou:

```text
NON_PKN_DIAGNOSTIC_RUNNER_SPEC_PARTIAL
runner_implementation_allowed_now = false
buz29_runtime_execution_allowed = false
lot_pkn_impact_allowed = false
recommended_next_phase = PHASE11_10I_SPECIFY_NON_PKN_DIAGNOSTIC_RUNNER
```

O writer continua implementado e disponível como componente opt-in, mas não há
runner não-PKN nem execução BUZ29-PENNY nesta fase.

## Resultado da Fase 11.10I

A 11.10I preserva o writer como componente opt-in, mas altera a recomendação
arquitetural: em vez de criar uma rota oficial não-PKN paralela, a evolução
futura deve usar uma seleção unificada de modelo por
`lot.fracture.fracture_model`. `PKN` permanece o default; `PENNY_SHAPED` só
pode ser selecionado por opt-in explícito e continua diagnóstico.
