# 24 — Design do SaltCreepSaltcreepAdapter

**Status:** Experimental e isolado — Fases 7.2-7.4 | **Ultima atualizacao:** 2026-06-03

## Objetivo

`SaltCreepSaltcreepAdapter` e o primeiro adapter C++ concreto que implementa
`SaltCreepInterface` em preparacao para o backend `external/saltcreep/`.

Nesta fase ele e deliberadamente isolado:

- nao e conectado ao LOT/PKN;
- nao e conectado ao APB;
- nao e chamado por `lot-sim run`;
- nao linka o target principal contra objetos do `external/saltcreep`;
- nao executa o solver FEM de sal.

## Status do backend

O adapter existe, compila e valida queries, mas o backend real ainda nao esta
conectado.

```text
SaltCreepSaltcreepAdapter::is_available() = false
```

Esse valor significa que a superficie C++ do adapter existe, mas nao ha
execucao fisica do `saltcreep` por tras dela. A resposta para query valida e
neutra e documentada.

## Entrada

O adapter recebe `SaltCreepQuery` em SI:

| Campo | Unidade | Regra |
|-------|---------|-------|
| `time_s` | s | finito e `>= 0` |
| `wall_pressure_Pa` | Pa | finito e `>= 0`, compressao positiva |
| `temperature_K` | K | finito e `> 0` |
| `radial_position_m` | m | finito e `>= 0` |

Valores invalidos lancam `std::invalid_argument`.

## Saida nesta fase

Para query valida, o adapter retorna:

```text
radial_displacement_m = 0
radial_closure_m = 0
radial_strain = 0
effective_closure_pressure_Pa = 0
valid = true
```

## Convencao de sinais

A Fase 7.2 preserva `docs/23_lot_salt_sign_convention.md`:

- pressao de parede compressiva e positiva;
- deslocamento radial positivo aponta para fora;
- deslocamento radial negativo aponta para dentro;
- fechamento radial e magnitude positiva:

```text
radial_closure_m = max(0, -radial_displacement_m)
```

O adapter expõe `radial_closure_from_displacement()` para manter essa regra
testada antes do backend real.

## Auditoria de suporte no saltcreep

`docs/audits/saltcreep_radial_displacement_sign_audit.md` confirma que os
caminhos auditados do `external/saltcreep` armazenam o deslocamento radial da
parede como `u_r` assinado, com fechamento para dentro representado por
`u_r < 0`, e calculam fechamento positivo como `-u_r`.

## Caso controlado do backend

A Fase 7.3 adiciona `tests/cpp/test_saltcreep_backend_controlled_case.cpp` e
`docs/audits/saltcreep_backend_controlled_case.md`. O teste compila um target
Catch2 separado, `saltcreep_backend_controlled_tests`, com um subconjunto minimo
das fontes do `external/saltcreep`, sem alterar o backend vendorizado e sem
linkar `lot-sim` ou `lot_sim_tests` ao solver de sal.

O caso usa Lame elastico axisimetrico para provar a rota C++ direta:

- pressao interna positiva aplicada como `WallPressureField` produz
  `u_r > 0`, isto e, deslocamento para fora e fechamento nulo;
- pressao externa/confinante positiva produz `u_r < 0`, isto e, fechamento
  para dentro com `radial_closure_m = max(0, -u_r)`;
- ambos os casos batem a solucao analitica com erro relativo menor que `1e-6`.

Esse resultado mostra que existe uma API C++ direta para um caso elastico
controlado. Ele nao muda o status do adapter: o backend real ainda nao esta
conectado a `SaltCreepSaltcreepAdapter`.

## Caso controlado com tempo, geostatica e termico neutro

A Fase 7.4 adiciona `tests/cpp/test_saltcreep_backend_time_geostatic_case.cpp`
e `docs/audits/saltcreep_backend_time_geostatic_case.md`. O target Catch2
separado `saltcreep_backend_time_geostatic_tests` instancia `TimeIntegrator`
com:

- material elastico `ElasticIsotropic`;
- `ProfileField::make_constant()` com `alpha_thermal = 0`;
- `ConstantWallPressureField`;
- vetor geostatico explicito por ponto de Gauss;
- um ou poucos passos `advance(dt_s)`.

O teste confirma que campos neutros preservam a resposta elastica estatica e
que uma geostatica compressiva simplificada, com parede externa fixa, produz
fechamento assinado (`u_r < 0`) e fechamento positivo (`max(0, -u_r)`).

Classificacao da API: `TIME_THERMAL_GEOSTATIC_CONTROLLED_TEST_READY`.

Esse resultado prova uma superficie C++ controlada mais rica, mas ainda nao
transforma `SaltCreepSaltcreepAdapter` em backend real.

## Por que o backend real nao foi ligado

Nao ha, ainda, uma API simples do tipo "avaliar resposta de parede" que aceite
apenas `SaltCreepQuery`. O uso real do `saltcreep` exige selecionar e construir:

- malha;
- elemento;
- material constitutivo;
- campo termico;
- tensao geostatica;
- campo de pressao de parede;
- condicoes de contorno;
- integrador explicito ou implicito.

Conectar parcialmente esses objetos nesta fase criaria acoplamento falso e
risco de reinterpretar a fisica. A decisao tecnica da Fase 7.2 e preparar a
classe e seus testes isolados, mantendo `is_available() = false`.

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| Mapeamento de pressao de parede incompleto | Fase 7.4 testou `WallPressureField` + `TimeIntegrator`; adapter real ainda precisa mapear condicoes fisicas LOT/APB. |
| Tensao geostatica e sinal interno do backend | Preservar FA03 no contrato moderno e testar conversao no adapter real. |
| Tempo e passo do backend | `SaltCreepQuery` traz tempo absoluto; adapter real precisara de estado ou agenda temporal. |
| Temperatura | Contrato usa K; backend real deve receber campo termico coerente. |
| Acoplamento LOT/sal prematuro | `lot-sim run` e `PknModel` permanecem intocados nesta fase. |
| Sinal da pressao aplicada | Fase 7.3 provou que pressao interna positiva expande a parede; o adapter real deve mapear pressoes internas, externas e geostaticas deliberadamente. |

## Proximos passos

1. Projetar configuracao explicita do adapter real: geometria, malha, material,
   integrador e campo termico.
2. Definir configuracao/state machine do adapter real para preservar estado
   temporal entre chamadas.
3. Somente depois conectar o adapter a `coupling/`, ainda sem modificar
   `PknModel`.
