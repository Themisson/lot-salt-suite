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
  5. Chamar SaltCreepInterface::evaluate(σ_wall, T, dt):
     - Retorna: taxa de deformação dε/dt e deformação acumulada ε
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
