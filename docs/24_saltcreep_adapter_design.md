# 24 — Design do SaltCreepSaltcreepAdapter

**Status:** Experimental e isolado — Fase 7.2 | **Ultima atualizacao:** 2026-06-03

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
| Mapeamento de pressao de parede incompleto | Fase futura deve testar `WallPressureField` + integrador com caso controlado. |
| Tensao geostatica e sinal interno do backend | Preservar FA03 no contrato moderno e testar conversao no adapter real. |
| Tempo e passo do backend | `SaltCreepQuery` traz tempo absoluto; adapter real precisara de estado ou agenda temporal. |
| Temperatura | Contrato usa K; backend real deve receber campo termico coerente. |
| Acoplamento LOT/sal prematuro | `lot-sim run` e `PknModel` permanecem intocados nesta fase. |

## Proximos passos

1. Projetar configuracao explicita do adapter real: geometria, malha, material,
   integrador e campo termico.
2. Criar caso C++ controlado que rode `external/saltcreep` isoladamente e
   compare `u_r`, `radial_closure_m` e `wall_closure_pct`.
3. Somente depois conectar o adapter a `coupling/`, ainda sem modificar
   `PknModel`.
