# 13 — Acoplamento LOT–APB–Sal

**Status:** Planejado | **Última atualização:** 2026-06-01

> A formulação detalhada deve ser verificada via `/formulation-audit`
> comparando os legados antes de implementar o módulo `coupling/`.

## Conceito de acoplamento

O LOT, APB e fluência de sal são fenômenos que se influenciam mutuamente:

1. **LOT → Sal:** pressão de fratura provoca campo de tensão na parede do poço →
   inicia ou acelera fluência do sal
2. **Sal → APB:** fluência do sal deforma a parede → reduz volume anular →
   aumenta pressão no anular (APB)
3. **APB → Sal:** pressão anular muda a tensão efetiva na rocha salina

Na arquitetura atual, o caminho LOT inicial deve ser PKN. O acoplamento com sal
deve passar pelo adapter para `external/saltcreep/`, que e uma dependencia
vendorizada ativa com governanca descrita em `docs/16_saltcreep_governance.md`.
O adapter nao deve depender de scripts Python em runtime. A Fase 6.10B criou a
opcao CMake `LSS_SALTCREEP_FORCE_LSS_EIGEN` e provou que o saltcreep compila e
executa corretamente com `include/Eigen` (via diretorio proxy). As duas copias
de Eigen permanecem preservadas; a migracao definitiva sera decidida apos o
ctest completo do build forcado.

## Política de implementação

O acoplamento LOT/APB/sal deve ser implementado em C++.

Python não deve atuar como intermediário runtime entre LOT e sal, nem montar
condições de contorno para `external/saltcreep` no fluxo principal. A integração
deve ocorrer por interfaces C++, como `SaltCreepInterface`,
`SaltCreepSaltcreepAdapter` e futuros adapters específicos para LOT/sal.
A Fase 7.0 criou apenas o contrato minimo `SaltCreepQuery` /
`SaltCreepResponse` e `NullSaltCreepInterface`; ainda nao ha chamada para
`external/saltcreep` nem acoplamento LOT/sal.
A Fase 7.1 fixou a convencao de sinais LOT-sal em
`docs/23_lot_salt_sign_convention.md`: pressoes compressivas sao positivas,
deslocamento radial positivo aponta para fora e fechamento radial e uma
magnitude positiva separada.
A Fase 7.2 criou `SaltCreepSaltcreepAdapter` como adapter C++ experimental e
isolado. Ele valida queries e preserva a convencao de fechamento, mas ainda
retorna resposta neutra com `is_available() = false`; portanto nao ha
acoplamento LOT/sal nem chamada fisica ao `external/saltcreep`.
A Fase 7.3 provou um caso C++ controlado e isolado do backend `saltcreep` com
Lame elastico, mas manteve o adapter neutro. O teste mostrou que pressao
interna positiva no `WallPressureField` expande a parede (`u_r > 0`), enquanto
pressao externa/confinante fecha (`u_r < 0`). Portanto, o futuro acoplamento
deve mapear cuidadosamente pressoes internas, externas e geostaticas antes de
converter resposta do backend em `radial_closure_m`.

Fluxo esperado:

```text
YAML/JSON → C++ parser → C++ LOT/APB/salt coupling → C++ writer → CSV/JSON
```

Python pode aparecer somente depois, para:

```text
CSV/JSON → Python plot/report/auditoria externa → PNG/HTML
```

## Algoritmo proposto (a verificar com formulação do legado)

```
Para cada passo de tempo dt:
  1. Atualizar campo térmico T(z, t)
  2. Calcular tensão geostática atualizada σ₀(t)
  3. Resolver LOT:
     - Calcular pressão de fratura P_frac
     - Calcular leakoff: volume perdido Q_LOT(t)
  4. Calcular tensão na parede do poço:
     σ_wall = f(P_anular, P_poros, σ₀, geometria)
  5. Chamar SaltCreepInterface::evaluate_wall_response(query):
     - Entradas: tempo [s], pressao de parede compressiva [Pa], temperatura [K] e posicao radial [m]
     - Retorna: deslocamento radial assinado [m], fechamento radial positivo [m], deformacao radial e pressao efetiva de fechamento [Pa]
  6. Calcular variação de volume anular:
     δV_anular = f(ε, geometria do poço)
  7. Atualizar pressão APB:
     δP_APB = δV_anular / (compressibilidade_fluido × V_anular)
  8. Verificar convergência (|δP_APB| < tolP)
  9. Atualizar estado e avançar tempo
```

## Questões em aberto (PENDENTE de auditoria)

| Questão | Impacto | Arquivo de referência |
|---------|---------|----------------------|
| Convenção de sinais de tensão | Crítico | `legance/LOT_Tese/include/apb_code/Rock.h` |
| Definição de tensão efetiva no sal | Crítico | `legance/LOT_Tese/include/sestsal/material.h` |
| Coordenadas: tensão radial × tangencial × axial | Alto | `legance/LOT_Tese/src/apb_code/APB1da.cpp` |
| Critério de convergência do loop | Médio | `legance/LOT_APB_v5/main/main.cpp` |
| Semantica de tempo PKN (`t` absoluto vs. tempo desde breakdown) | Alto | `legance/LOT_Tese/src/apb_code/APB1da.cpp` |
| Conversoes de vazao com fator geometrico embutido | Alto | `legance/LOT_Tese/src/apb_code/APB1da.cpp` |

## Interface proposta para coupling/

```cpp
// include/coupling/LotApbSaltCoupling.hpp
class LotApbSaltCoupling {
public:
    struct Config {
        double tol_pressure_Pa;
        int max_iterations;
        bool salt_enabled;
        bool lot_enabled;
        bool apb_enabled;
    };

    // Executa um passo de tempo acoplado
    void step(double dt_s, const Config& cfg);

private:
    // Referências para módulos físicos
    WellboreGeometry& wellbore_;
    FluidProperties& fluids_;
    ThermalField& thermal_;
    SaltCreepInterface& salt_;
    LotSolver& lot_;
    ApbSolver& apb_;
};
```

## Contrato PKN/saltcreep

O `coupling/` nao deve conhecer detalhes internos do PKN legado nem do FEM de
sal. O fluxo esperado e:

1. `lot/` calcula pressao, breakdown, abertura/comprimento PKN e volume de
   leakoff/fratura.
2. `coupling/` transforma a pressao anular/LOT em condicoes de contorno para sal.
3. `SaltCreepSaltcreepAdapter` delega para o `external/saltcreep/`, usando
   mecanismos existentes de pressao de parede quando aplicaveis.
4. O retorno do sal atualiza deslocamento radial assinado, fechamento radial
   positivo, volume anular e diagnosticos de dano.
5. `apb/` atualiza pressao anular a partir do volume e compressibilidade.

Na Fase 7.0, somente o `NullSaltCreepInterface` existe. Ele valida entradas SI
e retorna resposta neutra valida (`u_r = 0`, `strain = 0`,
`effective_closure_pressure_Pa = 0`) com `is_available() = false`, para deixar
claro que o solver real ainda nao esta conectado.
Na Fase 7.1, o contrato passou a expor tambem `radial_closure_m = 0` na
resposta neutra. Para respostas reais futuras, `radial_displacement_m < 0`
significa fechamento para dentro e `radial_closure_m = max(0,
-radial_displacement_m)` deve ser usado por calculos que esperam magnitude
positiva de fechamento.
Na Fase 7.2, `SaltCreepSaltcreepAdapter` implementa a mesma interface, mas
permanece neutro e indisponivel enquanto a configuracao completa do backend
(malha, material, temperatura, geostatica, pressao de parede e integrador) nao
for formalizada.
Na Fase 7.3, a rota C++ direta do backend foi validada apenas para um caso
elastico controlado em target Catch2 separado. Isso reduz risco de integracao,
mas nao autoriza acoplamento LOT/sal nem mudanca em `PknModel`.
Na Fase 7.4, `TimeIntegrator` tambem foi exercitado em target Catch2 separado
com campo termico constante neutro, vetor geostatico simplificado e pressao de
parede constante. Isso confirma uma rota controlada para tempo/geostatica, mas
continua fora do `coupling/` e nao muda o status neutro do adapter.
Na Fase 7.5, `SaltCreepAdapterConfig` e `SaltCreepAdapterState` foram
adicionados como fronteira C++ testada para geometria, malha, material,
termico, geostatica, tempo e pressao inicial de parede. O adapter continua sem
chamar o backend real: `evaluate_wall_response()` permanece neutro e
`is_available()` permanece `false`.
Na Fase 7.6, o adapter passou a chamar uma rota elastica/geostatica minima do
backend `external/saltcreep`, ainda isolada. `is_available()` agora indica que
a configuracao e suportada por essa superficie minima. Isso nao conecta
LOT/PKN/APB ao sal e nao altera `PknModel` ou `lot-sim run --mode lot-pkn`.

## Dependencia Eigen no acoplamento

Targets novos do `lot-salt-suite` devem receber Eigen por `lss::eigen`, que
aponta para `include/Eigen/`. O acoplamento com `external/saltcreep/` deve ser
feito por adapter e contrato de dados, sem misturar include paths apenas para
resolver headers Eigen.

A Fase 6.11 completou a migracao Eigen do saltcreep (`MIGRATION_COMPLETED`):
`external/saltcreep/CMakeLists.txt` agora auto-detecta o contexto `lot-salt-suite`
e usa `include/Eigen` por padrao. A duplicacao de Eigen (via proxy no build dir)
e aceitavel ate o adapter `SaltCreepSaltcreepAdapter` estabilizar.
