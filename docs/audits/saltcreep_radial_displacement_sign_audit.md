# Auditoria — sinal do deslocamento radial no saltcreep

**Data:** 2026-06-03  
**Fase:** 7.2  
**Status:** `SIGN_CONFIRMED_FOR_WALL_DISPLACEMENT_OUTPUT`

## Objetivo

Confirmar, antes de qualquer adapter real, como o `external/saltcreep` armazena
e reporta deslocamento radial na parede interna.

Esta auditoria foi somente leitura. Nenhum arquivo em `external/saltcreep/` foi
alterado.

## Evidencias encontradas

| Arquivo | Evidencia |
|---------|-----------|
| `external/saltcreep/include/solver/TimeIntegrator.hpp` | `wall_displacement_m()` retorna `state_.u_total[0]`. |
| `external/saltcreep/include/solver/ImplicitAdaptiveIntegrator.hpp` | `wall_displacement_m()` retorna `state_.u_total[0]`. |
| `external/saltcreep/src/solver/TimeIntegrator.cpp` | `wall_closure_pct()` calcula `-state_.u_total[mesh_.dof_index(0, 0)] / mesh_.nodes.front().r * 100.0`. |
| `external/saltcreep/src/solver/ImplicitAdaptiveIntegrator.cpp` | `wall_closure_pct()` usa a mesma regra `-u_r/Ri * 100`. |
| `external/saltcreep/src/solver/TimeOutput.cpp` | `wall_disp_m` grava `u_r` assinado; `u_wall_m` e calculado como `-u_r`; diametro usa `2.0 * (Ri - u_wall)`. |
| `external/saltcreep/tests/cpp/test_thermal_force.cpp` | Caso de fechamento exige `integrator.wall_displacement_m() < 0.0` e `wall_closure_pct() > 0.0`. |
| `external/saltcreep/tests/cpp/test_sestsal_verification.cpp` | Extrai `u_elastic(0)` e calcula fechamento como `-u_radial_at_ri / ri * 100.0`. |
| `external/saltcreep/docs/sestsal-mapping-plan.md` | Documenta `wall_closure_pct() = -u_radial[Ri] / Ri * 100`. |

## Conclusao

Para os caminhos auditados de saida e testes do `saltcreep`:

- `u_r`/`state_.u_total[0]` e o deslocamento radial bruto assinado da parede;
- `u_r < 0` significa deslocamento para dentro, isto e, fechamento;
- fechamento positivo e calculado como `-u_r`;
- `wall_disp_m` preserva o deslocamento assinado;
- `u_wall_m` representa magnitude positiva de fechamento.

Essa conclusao e suficiente para o contrato moderno:

```text
radial_displacement_m = u_r
radial_closure_m = max(0, -radial_displacement_m)
```

## Limites da auditoria

A auditoria nao prova ainda uma API unica e estavel para executar o solver de
sal a partir de uma `SaltCreepQuery` isolada. O caminho real exige construir
malha, elemento, material constitutivo, campo termico, tensao geostatica,
condicoes de contorno e integrador. Por isso, a Fase 7.2 usa adapter neutro
experimental em vez de acoplamento real.

O mapeamento de pressao de parede deve ser provado na fase do adapter real:
`WallPressureField` existe, mas a conversao da pressao compressiva positiva do
LOT/APB para a condicao de contorno completa do backend ainda precisa de teste
dedicado.

## Complemento Fase 7.3

`docs/audits/saltcreep_backend_controlled_case.md` adiciona uma prova C++
controlada com Lame elastico. O resultado confirma a convencao de deslocamento
assinado e explicita o papel da condicao de contorno:

- pressao interna positiva aplicada por `WallPressureField` produz `u_r > 0`
  na parede interna, isto e, expansao para fora;
- pressao externa/confinante positiva produz `u_r < 0`, isto e, fechamento para
  dentro;
- fechamento positivo continua sendo `max(0, -u_r)`.

Assim, o contrato de sinais permanece valido, mas o futuro adapter real deve
mapear a pressao compressiva positiva do LOT/APB para o conjunto fisico correto
de pressoes e tensoes do backend.
