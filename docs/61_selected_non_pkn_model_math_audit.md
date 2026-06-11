# Selected Non-PKN Model Math Audit (Fase 11.7B)

## Resumo executivo

A Fase 11.7B audita matematicamente a trilha selecionada na 11.7A:

```text
selected_track = PENNY_SHAPED
status = SELECTED_MODEL_MATH_AUDITED
implementation_readiness = MINIMAL_IMPLEMENTATION_READY_DIAGNOSTIC_ONLY
recommended_next_phase = PHASE11_7C_SELECTED_MODEL_YAML_IO_SPEC
```

A auditoria matemática da 11.7B não implementa o modelo moderno. Ela define a
base técnica mínima para especificação de YAML/IO e implementação posterior.

## Fontes legadas

| Fonte | Papel |
|---|---|
| `legance/LOT_Tese/src/apb_code/APB1da.cpp` | Contém `calculateLOTFracturedSaltRock(...)` e o bloco `idTypeFracture == 3`. |
| `legance/LOT_Tese/include/apb_code/APB1da.h` | Declara `calculateLOTFracturedSaltRock(...)`, `ConvflowRate()` e estado de tempo. |
| `legance/LOT_Tese/src/apb_code/Fluids.cpp` | Converte viscosidade e mapeia `penny-shaped`. |
| `legance/LOT_Tese/include/apb_code/Fluids.h` | Define `idTypeFracture`: `penny-shaped -> 3`. |
| `legance/LOT_Tese/BUZ29-VISCO-first-well.cpp` | Caso driver com `setLeakoffProps("pa_min", 3., "penny-shaped")`. |

## Equações extraídas

| Item | Símbolo | Código legado | Unidade | Interpretação | Status |
|---|---|---|---|---|---|
| Módulo plano | `E' = E / (1 - nu^2)` | `EPd = E / (1 - pow(nu, 2))` | Pa | Módulo elástico efetivo usado nas relações de fratura. | `EXTRACTED` |
| Módulo cisalhante | `G = E / (2(1+nu))` | `G = E / (2 * (1 + nu))` | Pa | Calculado no bloco LOT, embora o penny-shaped use `EPd` nas fórmulas ativas. | `EXTRACTED` |
| Abertura máxima | `w0 = 3.65 * ((mu^2 Qinj^3) / E'^2)^(1/9) * time^(1/9)` | `APB1da.cpp`, bloco penny-shaped | m | Proxy de abertura máxima da fratura penny-shaped. | `EXTRACTED` |
| Raio de fratura | `R = 0.572 * ((E' Qinj^3) / mu)^(1/9) * time^(4/9)` | `APB1da.cpp`, bloco penny-shaped | m | Raio diagnóstico da fratura penny-shaped. | `EXTRACTED` |
| Fator de pressão | `pressureFactor = pw / sigmaTheta` | `pressureFactor = pw / sigmaTheta` | - | Amplificador legado relacionado à razão entre pressão de poço e `sigmaTheta`. | `EXTRACTED` |
| Volume proxy | `dV_leakoff = 10 * (w0/2)^2 * R * pi * pressureFactor` | `line_up[lu].dV_leakoff(idAnnular) = ...` | m3/rad legado | Volume/sink de fratura usado no balanço legado. | `EXTRACTED` |

## Variáveis e unidades

| Variável | Unidade | Origem | Observação |
|---|---|---|---|
| `E` | Pa | Rocha ativa no layer | Módulo de Young. |
| `nu` | - | Rocha ativa no layer | Poisson. |
| `mu` | Pa·min | `converterViscosidade(...)[strViscosity]` | BUZ29 usa `pa_min`, viscosidade de entrada em cP. |
| `Qinj` | m3/min | `ConvflowRate()` | Compatível com tempo legado em minutos. |
| `time` | min | `t - firstTimePwExceedsSigmaMin` | Só positivo após `pw > sigmaTheta`. |
| `pw` | Pa | pressão anular/poço | Usado no critério de abertura. |
| `sigmaTheta` | Pa | `-mdl->getSigmaTheta()` | Compressão positiva no critério legado. |
| `w0` | m | fórmula penny-shaped | Abertura máxima proxy. |
| `R` | m | fórmula penny-shaped | Raio proxy. |

## Entradas necessárias

- `young_modulus_Pa`
- `poisson_ratio`
- `viscosity_Pa_min`
- `flow_rate_m3_min`
- `elapsed_since_opening_min`
- `wellbore_pressure_Pa`
- `sigma_theta_compression_positive_Pa`

## Saídas esperadas

- `opening_m`
- `radius_m`
- `pressure_factor`
- `fracture_volume_proxy_m3`

## Acoplamentos com LOT

O bloco legado só calcula `dV_leakoff` quando `pw > sigmaTheta` e
`time > 0`. O volume calculado entra em `line_up[lu].dV_leakoff(idAnnular)` e
depois participa do balanço volumétrico pelo caminho de `getdV(...)`.

## Diferenças em relação ao PKN

- O PKN moderno atual usa altura/comprimento de fratura; o penny-shaped usa raio.
- A relação temporal do penny-shaped auditado usa expoentes `1/9` para abertura
  e `4/9` para raio.
- O volume legado inclui fator empírico `10` e `pressureFactor = pw/sigmaTheta`.
- A fonte `sigmaTheta` vem do estado de sal legado, não do PKN moderno.

## Prontidão para implementação

```text
MINIMAL_IMPLEMENTATION_READY_DIAGNOSTIC_ONLY
```

Há equações suficientes para implementar um núcleo C++ isolado que calcula
`w0`, `R`, `pressureFactor` e `fracture_volume_proxy_m3` com validação de
parâmetros. Isso não significa que BUZ29 esteja pronto para validação moderna.

## Bloqueios

- Equivalência com BUZ29 depende de APB/sal, `sigmaTheta`, histórico de pressão
  e convenções volumétricas legadas.
- O fator `10` do volume proxy é legado/empírico e deve permanecer explícito.
- A 11.8A, se executada, deve ser núcleo mínimo isolado e opt-in.

## Próxima fase recomendada

```text
PHASE11_7C_SELECTED_MODEL_YAML_IO_SPEC
```

## Resultado da Fase 11.7C

A Fase 11.7C criou uma especificação YAML/IO para essas entradas e saídas em
modo fixture-only:

```text
SELECTED_MODEL_YAML_IO_SPECIFIED
SPEC_FIXTURE_ONLY_NOT_RUNTIME_SCHEMA
```

O contrato exige unidades explícitas para `young_modulus`,
`poisson_ratio`, `viscosity`, `flow_rate`, `elapsed_since_opening`,
`wellbore_pressure` e `sigma_theta_compression_positive`, além do fator legado
`volume_multiplier = 10.0`. O parser principal e os schemas oficiais continuam
inalterados.

## Resultado da Fase 11.8A

A Fase 11.8A implementa essas relações em um núcleo C++ isolado:

```text
include/lot/PennyShapedModel.hpp
src/lot/PennyShapedModel.cpp
tests/cpp/test_penny_shaped_model.cpp
```

O escopo permanece restrito a formulas auditadas e testes unitários. Nenhum
runtime LOT/PKN, parser ou caso BUZ29 foi conectado.
