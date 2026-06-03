# 22 — Contrato SaltCreepInterface

**Status:** Implementado — Fases 7.0-7.2 | **Última atualização:** 2026-06-03

## Objetivo

`SaltCreepInterface` define o contrato C++ mínimo entre o núcleo moderno do
`lot-salt-suite` e uma futura integração com fluência de sal. A interface cria
uma fronteira estável para que `coupling/` e futuros adapters consumam respostas
de sal sem conhecer detalhes internos do `external/saltcreep`.

Nesta fase, a interface é deliberadamente não acoplada: ela não executa o solver
FEM, não altera LOT/PKN, não altera APB e não muda nenhum modelo físico.

## O que existe nesta fase

- `include/salt/SaltCreepTypes.hpp` — tipos simples em SI.
- `include/salt/SaltCreepInterface.hpp` — interface abstrata e implementação nula.
- `src/salt/SaltCreepInterface.cpp` — validação de entrada e resposta neutra.
- `include/salt/SaltCreepSaltcreepAdapter.hpp` — adapter experimental isolado.
- `src/salt/SaltCreepSaltcreepAdapter.cpp` — validação e resposta neutra
  enquanto o backend real nao esta conectado.
- `tests/cpp/test_salt_creep_interface.cpp` — testes Catch2 do contrato.
- `tests/cpp/test_salt_creep_saltcreep_adapter.cpp` — testes Catch2 do adapter
  experimental.

## O que não existe nesta fase

- Não há chamada para `external/saltcreep`.
- Não há acoplamento LOT/sal.
- Não há atualização de volume anular, APB ou dano.
- Não há leitura de arquivos legados ou baselines.
- Não há script Python ou pré-processamento.

## Tipos e unidades

Todos os campos são SI e devem chegar convertidos pelo parser ou pelo futuro
orquestrador:

| Tipo | Campo | Unidade |
|------|-------|---------|
| `WallPressureSample` | `time_s` | s |
| `WallPressureSample` | `pressure_Pa` | Pa |
| `SaltCreepQuery` | `time_s` | s |
| `SaltCreepQuery` | `wall_pressure_Pa` | Pa |
| `SaltCreepQuery` | `temperature_K` | K |
| `SaltCreepQuery` | `radial_position_m` | m |
| `SaltCreepResponse` | `radial_displacement_m` | m |
| `SaltCreepResponse` | `radial_closure_m` | m |
| `SaltCreepResponse` | `radial_strain` | adimensional |
| `SaltCreepResponse` | `effective_closure_pressure_Pa` | Pa |

## Convencao de sinais

A convencao detalhada LOT-sal esta fixada em
`docs/23_lot_salt_sign_convention.md`. Resumo do contrato:

- `wall_pressure_Pa >= 0` e pressao compressiva positiva.
- `effective_closure_pressure_Pa >= 0` e pressao compressiva efetiva positiva.
- `radial_displacement_m > 0` indica deslocamento radial para fora.
- `radial_displacement_m < 0` indica deslocamento radial para dentro.
- `radial_strain` segue o deslocamento radial: positiva em expansao e negativa
  em fechamento.
- `radial_closure_m >= 0` e a magnitude positiva de fechamento:
  `max(0, -radial_displacement_m)`.

## Validação de entrada

`NullSaltCreepInterface::evaluate_wall_response` rejeita:

- `NaN`;
- `Inf`;
- `time_s < 0`;
- `wall_pressure_Pa < 0`;
- `temperature_K <= 0`;
- `radial_position_m < 0`.

Entradas inválidas lançam `std::invalid_argument` com mensagem explícita.

## Comportamento nulo

`NullSaltCreepInterface` representa a ausência controlada de solver real:

```text
is_available() = false
radial_displacement_m = 0
radial_closure_m = 0
radial_strain = 0
effective_closure_pressure_Pa = 0
valid = true para query válida
```

`is_available() = false` significa que o solver real de sal ainda não está
conectado. `valid = true` significa que a query foi validada e que a resposta
neutra foi calculada corretamente. Essa separação permite que testes e futuros
orquestradores diferenciem “solver indisponível” de “entrada inválida”.

## Adapter saltcreep experimental

A Fase 7.2 adicionou `SaltCreepSaltcreepAdapter`. Nesta fase ele e
intencionalmente equivalente a um adapter neutro documentado:

```text
SaltCreepSaltcreepAdapter::is_available() = false
```

Ele valida a query com as mesmas regras do contrato, retorna resposta neutra
valida e testa explicitamente a regra:

```text
radial_closure_m = max(0, -radial_displacement_m)
```

O adapter ainda nao instancia malha, elemento, material, campo termico,
geostatica, `WallPressureField` ou integrador do `external/saltcreep`.
Detalhes em `docs/24_saltcreep_adapter_design.md`.

## Por que LOT/PKN ainda não foi acoplado

A Fase 7.0 criou a interface minima. A Fase 7.1 fixou a convencao de pressao,
deslocamento radial e fechamento, ainda sem acoplar LOT/PKN ao sal. Acoplar
LOT/PKN ao backend de sal exigira decisoes adicionais sobre tempo de integracao
e conversao de fechamento em volume anular, com testes proprios e comparacao
controlada.

O `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter` e `CaseParser`
permanecem sem alteração nesta fase.

## Próximos passos

1. Criar `SaltCreepLotAdapter` ou `SaltCreepSaltcreepAdapter` em C++.
2. Mapear pressão LOT/APB para campo de pressão de parede preservando
   `wall_pressure_Pa >= 0` como compressao positiva.
3. Converter o deslocamento bruto do backend em `radial_displacement_m` e
   `radial_closure_m`.
4. Executar o `external/saltcreep` por adapter, sem copiar código constitutivo.
5. Adicionar testes de integração que provem que LOT/PKN permanece inalterado
   quando a interface nula é usada.

## Riscos futuros

| Risco | Motivo |
|-------|--------|
| Sinais | Contrato moderno definido na Fase 7.1; adapter ainda precisa provar o mapeamento para o backend. |
| Tempo | O contrato usa segundos; backends podem usar horas, minutos ou passos adaptativos. |
| Temperatura | O contrato usa K; SESTSAL legado usa °C empírico. |
| Pressão de parede | LOT/APB devem mapear pressão para condição de contorno sem duplicar física. |
| Deslocamento radial | `u_wall` precisa indicar claramente inward/outward antes de virar volume. |
| Fechamento | Fechamento deve ser convertido para volume anular com geometria validada. |
| Compressão | FA03 deve ser preservado em todos os adapters. |
| Integração saltcreep | Usar `WallPressureField` e superfícies existentes antes de criar rotas paralelas. |
