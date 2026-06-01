# 08 — Problemas Conhecidos e Riscos

**Status:** Ativo — Auditoria de formulação executada | **Última atualização:** 2026-06-01

> Este arquivo deve ser atualizado ANTES de qualquer mudança de formulação ou convenção.
> Toda refatoração deve ser comparada com esta lista antes de ser aprovada.

---

## RESULTADOS DA AUDITORIA DE FORMULAÇÃO (2026-06-01)

Arquivos auditados:
- `legance/LOT_Tese/include/sestsal/material.h`
- `legance/LOT_Tese/src/sestsal/material.cpp`
- `legance/LOT_APB_v5/src/apb_code/APB1da.cpp`
- `legance/LOT_Tese/LOTTeste.cpp` (linha 61–65)

---

## FA01 — Unidade de tempo do e0: [1/min], NÃO [1/h]

**Severidade:** Crítica | **Status:** Confirmado

**Evidência direta** (`LOTTeste.cpp`, linha 62–63):
```cpp
// a taxa de deformação está dividida por 60 para passar de horas para minuto
vrock.push_back(new Rock(..., 1.8792e-06 / 60, 9.92e+06, 86., 3.36, 7.55));
```

`material.h` declara `double e0; // [1/h]` — **INCORRETO**.
O valor passado é `e0_literatura [1/h] ÷ 60` = `e0 [1/min]`.

**Conclusão:** A unidade interna de tempo do modelo SESTSAL é **minutos [min]**, não horas.
O `dt` passado para `solveThermalViscoStep(dt)` deve estar em [min] ou há conversão interna.

**Impacto para o código novo:**
- Todo `e0` lido de YAML deve ser convertido: se o usuário informa `[1/h]`, o parser divide por 60 antes de passar ao modelo SESTSAL legado.
- Na nova arquitetura: armazenar `e0` em SI ([1/s]) internamente; converter na fronteira do SESTSAL adapter.
- Schema YAML deve declarar campo `e0_unit: "1/h"` para deixar explícito.

**Valores de referência confirmados:**
| Material | e0 literatura [1/h] | e0 passado ao modelo [1/min] |
|----------|--------------------|-----------------------------|
| Halita | 1.8792e-06 | 3.132e-08 |
| Carnalita | 1.581e-04 | 2.635e-06 |

---

## FA02 — Temperatura no modelo de fluência: [°C], NÃO [K]

**Severidade:** Alta | **Status:** Confirmado

**Evidência** (`LOTTeste.cpp`, linha 61):
```cpp
// Rocha viscoelástica (..., e0 [1/h], sig0 [Pa], T0 [degC], n1, n2)
vrock.push_back(new Rock(..., 86., 3.36, 7.55));  // T0 = 86 °C para halita
```

`material.h` declara `double T0; // reference temperature, [K]` — **INCORRETO**.
O valor passado é `T0 = 86` (°C), não `359.15` (K).

**Fórmula Arrhenius no legado:**
```
ε̇ = e0 · exp(Q_R/T0 − Q_R/T) · (σ_eff/σ₀)ⁿ
com Q_R = 12/0.0019858 = 6042.7  (unidade: °C, não K física)
```

**Consequência:** A fórmula é **auto-consistente em °C**: se T0 e T são ambos em °C, `exp(Q_R/T0 − Q_R/T)` = 1 exatamente quando T=T0. O valor `Q_R=6042.7` é um **parâmetro de ajuste empírico em °C**, não a razão Q/R física em Kelvin.

**Diferença em relação a usar Kelvin:**  
A sensibilidade à temperatura muda drasticamente:
- Na lei em °C, a variação entre 86°C e 96°C muda e0 por fator ≈ 4×
- Na lei em K, a mesma variação (359→369 K) muda e0 por fator ≈ 1.05×

**Impacto para o código novo:**
- O parser deve aceitar `T0` em °C (como está na prática), não em K.
- Internamente, armazenar T0 em K (adicionar +273.15) e usar T em K para o modelo novo.
- Para o `SaltCreepSESTSALAdapter`, manter a convenção original (°C) para reproduzir fielmente o legado.
- `saltcreep` (referência moderna) usa temperatura em K — confirmar antes de integrar.

**Valores confirmados:**
| Material | T0 (°C) | T0 (K) |
|----------|---------|--------|
| Halita | 86 | 359.15 |
| Carnalita | 130 | 403.15 |

---

## FA03 — Convenção de sinais: compressão POSITIVA

**Severidade:** Crítica | **Status:** Confirmado

**Evidência** (`material.cpp`, linhas 58–73 — tensor desviador):
```cpp
sigd << (+2*sig(0)-sig(1)-sig(2))/3.,
      (-sig(0)+2*sig(1)-sig(2))/3.,
      (-sig(0)-sig(1)+2*sig(2))/3.;
```
`sig = {σ_rr, σ_θθ, σ_zz}` — notação de Voigt, axissimétrico.
A pressão interna é passada como valor positivo (`pi + dP`, ambos positivos).

**Matriz constitutiva** (linhas 40–43):
```cpp
double fac = E/(1+nu)/(1-2*nu);  // positivo
cm << (1-nu)*fac, nu*fac, ...    // lei de Hooke com compressão > 0
```

**Conclusão:** Convenção de **mecânica dos solos**: tensão de compressão é positiva.
- σ > 0 → compressão (padrão geomecânico)
- p_lama > 0 → pressão compressiva na parede do poço
- dP_APB > 0 → aumento de pressão de compressão no anular

**Impacto para o código novo:**
- Todo módulo `lot/`, `apb/`, `geomechanics/`, `salt/` deve usar a MESMA convenção.
- Documentar em `include/core/types.hpp` com comentário explícito.
- O `saltcreep` usa mesma convenção (verificar antes da integração).

---

## FA04 — Acoplamento sal → APB: mecanismo confirmado

**Severidade:** Informativo | **Status:** Confirmado

**Fluxo de acoplamento** (`APB1da.cpp`, linhas 536–543):
```cpp
// 1. Impor pressão e temperatura do passo anterior no modelo de sal
mdl->setInnerPressure(pi + dP);
mdl->setInnerTemperature(Ti + dT);  // em °C

// 2. Resolver um passo temporal de fluência viscosa
mdl->solveThermalViscoStep(dt);

// 3. Obter deslocamento da parede do poço (m)
x(x.rows()-1) = mdl->getNodalDisplacement();  // linha 1197
```

**Fórmula de balanço de pressão APB** (linhas 839–842):
```
dP = (α·dT − (dV + dV_leakage + dV_vented − dMl/(ρ·FC)) / Vi) / k
```
onde `dV` = variação de volume calculada a partir de `u_wall`.

**Sentido físico:** Se o sal flui para dentro (fechamento), `u_wall > 0` →
volume anular reduz (`dV < 0`) → pressão de sal parcialmente alivia APB térmico.

**Nota de acoplamento fraco:** O deslocamento do sal é calculado fora do loop iterativo
de pressão (linhas 511–546), usando estado do passo anterior. O loop iterativo (linhas
560–868) recalcula pressão sem iterar no sal. Isto é acoplamento **sequencial fraco**
(staggered): sal e APB não são totalmente acoplados em cada passo de tempo.

---

## Problemas de nomenclatura

| ID | Problema | Impacto | Mitigação |
|----|---------|---------|-----------|
| N01 | Diretório físico é `legance/` mas docs dizem `legacy/` | Médio | Convivência deliberada — nunca renomear `legance/` |

## Parâmetros hard-coded identificados

| ID | Parâmetro | Valor | Arquivo | Ação necessária |
|----|-----------|-------|---------|-----------------|
| H01 | `dt` (passo temporal) | 1.0 h | `LOT_APB_v5/main/main.cpp` | YAML `time.dt_h` |
| H02 | `ctoldP` (tolerância pressão) | 1.0 bar | `LOT_APB_v5/main/main.cpp` | YAML `time.solver.tol_pressure_bar` |
| H03 | `tolEq` (tolerância equilíbrio) | 1E-8 | `LOT_APB_v5/main/main.cpp` | YAML `time.solver.tol_eq` |
| H04 | `tac` (estabilização) | 80 sem × 7d × 24h | `LOT_APB_v5/main/main.cpp` | YAML `time.solver.stabilization_h` |
| H05 | `e0` Halita | `1.8792e-06/60` [1/min] | `LOTTeste.cpp` | YAML `rocks[].creep.e0_per_h: 1.8792e-6` com conversão no parser |
| H06 | `e0` Carnalita | `1.581e-04/60` [1/min] | `LOTTeste.cpp` | Idem H05 |
| H07 | Viscosidade fluido LOT | 3.0 cP | `8-BUZ-67D-*.cpp` | Parser converte cP → Pa·s |
| H08 | Geometria LOT | `"elliptical"` | `8-BUZ-67D-*.cpp` | YAML `lot.fracture.geometry` |

## Riscos de formulação (atualizados após auditoria)

| ID | Risco | Impacto | Status após auditoria |
|----|-------|---------|----------------------|
| R01 | Convenção de sinais: compressão +/- | Crítico | **RESOLVIDO** — compressão POSITIVA (FA03) |
| R02 | Unidades mistas nos main.cpp | Alto | Confirmado — módulo `units/` obrigatório |
| R03 | SESTSAL divergente LOT_Tese × LOT_APB_v5 | Alto | Pendente comparação direta |
| R04 | `APB1da` monolítica | Alto | Confirmado — Fase 7 necessária |
| R05 | e0 em h⁻¹ × min⁻¹ | Crítico | **CONFIRMADO** — e0 está em [1/min] (FA01) |
| R06 | Temperatura: °C × K no SESTSAL | Crítico | **CONFIRMADO** — SESTSAL usa °C (FA02) |
| R07 | Acoplamento sal-APB sequencial fraco | Médio | **CONFIRMADO** — staggered, uma iteração de sal/passo (FA04) |
| R08 | `dt` passado a `solveThermalViscoStep` em horas ou minutos? | Alto | Pendente — verificar implementação do solver SESTSAL |

## Itens pendentes após auditoria

- [x] Convenção de sinais → FA03 (compressão positiva)
- [x] Temperatura no modelo: °C, não K → FA02
- [x] Unidade de e0: [1/min] internamente → FA01
- [x] Mecanismo de acoplamento sal→APB → FA04
- [ ] **R08 PENDENTE:** verificar se `dt` em `solveThermalViscoStep` é [h] ou [min]
      — arquivo a verificar: `legance/LOT_APB_v5/src/apb/apb_salt_1d.cpp`
- [ ] Confirmar convenção de sinal de `u_wall` (positivo = inward ou outward?)
      — arquivo: `legance/LOT_APB_v5/include/apb/apb_salt_1d.h`
- [ ] Comparar SESTSAL entre LOT_Tese e LOT_APB_v5 (risco R03)
