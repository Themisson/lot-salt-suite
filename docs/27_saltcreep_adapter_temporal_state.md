# 27 — Estado temporal persistido do SaltCreepSaltcreepAdapter

**Status:** Implementado e isolado — Fase 7.7
**Ultima atualizacao:** 2026-06-03

## Objetivo

A Fase 7.7 reduz a reconstrucao interna do backend minimo do
`SaltCreepSaltcreepAdapter` sem trazer `TimeIntegrator` para o target principal.

A decisao segue a auditoria
`docs/audits/saltcreep_timeintegrator_include_boundary.md`: o integrador
temporal real do `external/saltcreep` ainda expõe headers de I/O com nomes que
colidem com `include/io/` do `lot-salt-suite`.

## Classificacao

```text
TEMPORAL_STATE_READY_WITHOUT_TIMEINTEGRATOR
```

O adapter preserva estado entre queries e reutiliza objetos do backend minimo,
mas nao executa uma integracao temporal de fluencia.

## O que passou a persistir

`SaltCreepSaltcreepAdapter` agora possui um cache privado e opaco para a rota
minima elastica/geostatica:

- elemento `AxisymL3`;
- material `ElasticIsotropic`;
- malha L3;
- matriz de rigidez;
- vetor geostatico, quando habilitado;
- graus de liberdade fixos.

O cache e criado preguiçosamente na primeira chamada valida de
`evaluate_wall_response()` e permanece entre queries subsequentes da mesma
instancia.

Cada query ainda monta o vetor de pressao de parede correspondente a
`time_s` e `wall_pressure_Pa`, resolve o sistema elastico e registra a resposta
em `SaltCreepAdapterState`.

## Diagnostico de teste

O metodo `backend_build_count()` existe para teste e diagnostico de integracao.
Ele confirma que:

- `is_available()` nao constroi o backend;
- duas queries com tempo crescente reutilizam o mesmo cache;
- uma configuracao fora da superficie minima nao constroi cache;
- uma query rejeitada por tempo decrescente nao reinicializa o backend.

## Limites

Esta fase nao muda:

- modelo constitutivo;
- formulação fisica;
- mapeamento de pressao LOT/APB para sal;
- `TimeIntegrator`;
- `external/saltcreep/`;
- LOT/PKN/APB.

`radial_strain` continua sendo o proxy `u_r / r_i` documentado na Fase 7.6.
Uma fase futura com fluencia real deve substituir esse campo por uma grandeza
derivada do campo adequado, se o contrato exigir deformacao radial verdadeira.
