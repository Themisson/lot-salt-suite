# 22 — Contrato SaltCreepInterface

**Status:** Implementado — Fase 7.0 | **Última atualização:** 2026-06-03

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
- `tests/cpp/test_salt_creep_interface.cpp` — testes Catch2 do contrato.

## O que não existe nesta fase

- Não há `SaltCreepSaltcreepAdapter`.
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
| `SaltCreepResponse` | `radial_strain` | adimensional |
| `SaltCreepResponse` | `effective_closure_pressure_Pa` | Pa |

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
radial_strain = 0
effective_closure_pressure_Pa = 0
valid = true para query válida
```

`is_available() = false` significa que o solver real de sal ainda não está
conectado. `valid = true` significa que a query foi validada e que a resposta
neutra foi calculada corretamente. Essa separação permite que testes e futuros
orquestradores diferenciem “solver indisponível” de “entrada inválida”.

## Por que LOT/PKN ainda não foi acoplado

A Fase 7.0 é uma etapa de contrato. Acoplar LOT/PKN ao sal exigirá decisões
adicionais sobre pressão de parede, sinal de deslocamento radial, tempo de
integração e conversão de fechamento em volume anular. Essas decisões pertencem
a uma fase futura com testes próprios e comparação controlada.

O `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter` e `CaseParser`
permanecem sem alteração nesta fase.

## Próximos passos

1. Criar `SaltCreepLotAdapter` ou `SaltCreepSaltcreepAdapter` em C++.
2. Mapear pressão LOT/APB para campo de pressão de parede.
3. Definir convenção de sinal para deslocamento radial e fechamento.
4. Executar o `external/saltcreep` por adapter, sem copiar código constitutivo.
5. Adicionar testes de integração que provem que LOT/PKN permanece inalterado
   quando a interface nula é usada.

## Riscos futuros

| Risco | Motivo |
|-------|--------|
| Sinais | O projeto usa compressão positiva; deslocamento radial precisa de convenção explícita. |
| Tempo | O contrato usa segundos; backends podem usar horas, minutos ou passos adaptativos. |
| Temperatura | O contrato usa K; SESTSAL legado usa °C empírico. |
| Pressão de parede | LOT/APB devem mapear pressão para condição de contorno sem duplicar física. |
| Deslocamento radial | `u_wall` precisa indicar claramente inward/outward antes de virar volume. |
| Fechamento | Fechamento deve ser convertido para volume anular com geometria validada. |
| Compressão | FA03 deve ser preservado em todos os adapters. |
| Integração saltcreep | Usar `WallPressureField` e superfícies existentes antes de criar rotas paralelas. |
