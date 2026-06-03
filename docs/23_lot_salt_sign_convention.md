# 23 — Convencao de sinais LOT-saltcreep

**Status:** Implementado — Fases 7.1-7.2 | **Ultima atualizacao:** 2026-06-03

## Objetivo

Este documento fixa o contrato de sinais, unidades e fronteira de dados entre o
LOT/PKN moderno e um futuro adapter para `external/saltcreep/`. A Fase 7.1 nao
implementa o adapter real, nao chama o solver FEM de sal e nao altera qualquer
modelo fisico LOT, APB ou saltcreep.

## Decisoes de contrato

Todos os campos da fronteira `salt::SaltCreepInterface` usam SI.

| Campo | Unidade | Convencao |
|-------|---------|-----------|
| `wall_pressure_Pa` | Pa | Pressao de parede compressiva, positiva ou zero. |
| `temperature_K` | K | Temperatura absoluta. |
| `radial_position_m` | m | Posicao radial geometrica, positiva ou zero. |
| `radial_displacement_m` | m | Deslocamento radial bruto: positivo para fora, negativo para dentro. |
| `radial_closure_m` | m | Magnitude positiva de fechamento: `max(0, -radial_displacement_m)`. |
| `radial_strain` | adimensional | Segue o sinal do deslocamento radial: positivo em expansao, negativo em fechamento. |
| `effective_closure_pressure_Pa` | Pa | Pressao efetiva compressiva associada ao fechamento, positiva ou zero. |

## Pressao, deslocamento e fechamento

O projeto moderno preserva FA03: pressao e tensoes compressivas externas ao
backend sao positivas. Assim, `wall_pressure_Pa >= 0` representa carga
compressiva aplicada na parede do poco.

O deslocamento radial segue a coordenada geometrica:

- `radial_displacement_m > 0`: parede se desloca para fora, aumentando raio.
- `radial_displacement_m < 0`: parede se desloca para dentro, reduzindo raio.
- `radial_displacement_m = 0`: resposta radial neutra.

Fechamento nao e um segundo sinal de deslocamento. Ele e a magnitude positiva da
reducao radial:

```text
radial_closure_m = max(0, -radial_displacement_m)
```

Um futuro calculo de volume anular deve consumir `radial_closure_m` quando
precisar da reducao positiva de raio/volume, e deve consumir
`radial_displacement_m` quando precisar do deslocamento assinado.

## Observacao sobre `external/saltcreep`

A inspecao de Fase 7.1 encontrou saidas existentes em `external/saltcreep/` nas
quais o deslocamento de parede bruto `u_r` e negativo para fechamento interno, e
metricas de fechamento sao calculadas como magnitude positiva `-u_r`.
A auditoria formal de Fase 7.2 esta em
`docs/audits/saltcreep_radial_displacement_sign_audit.md` e confirmou esse
sinal para os caminhos auditados de integradores, saida temporal e testes.

Por isso, o futuro `SaltCreepSaltcreepAdapter` deve:

1. mapear a pressao LOT/APB positiva compressiva para a condicao de contorno
   esperada pelo backend, sem inverter sinal por suposicao;
2. retornar o deslocamento bruto do backend em `radial_displacement_m`;
3. preencher `radial_closure_m` como `max(0, -radial_displacement_m)`;
4. manter `effective_closure_pressure_Pa` como grandeza compressiva positiva ou
   zero no contrato moderno.

Essa regra evita misturar a convencao externa de pressoes compressivas positivas
com detalhes internos de tensao, tracao ou vetor normal do backend FEM.

Na Fase 7.2, `SaltCreepSaltcreepAdapter` aplica apenas a parte cinemática dessa
regra (`radial_closure_m = max(0, -radial_displacement_m)`) e retorna resposta
neutra porque o backend real ainda nao esta conectado.

## Escopo preservado

Esta fase altera apenas o contrato de dados e a documentacao. Permanecem sem
alteracao:

- `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter` e `CaseParser`;
- `src/lot/` e `include/lot/`;
- `external/saltcreep/`;
- `legance/`, `legacy/`, baselines e modelos fisicos.
