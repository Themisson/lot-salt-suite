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

**Conclusão:** No legado da tese, o valor passado para `e0` foi convertido para **[1/min]**.
O incremento `dt` usado por qualquer backend deve ser coerente com a unidade temporal da
taxa de fluência ativa; quando o backend usa `e0` em [1/min], o passo equivalente deve estar
em minutos ou deve haver conversão explícita na fronteira.

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
- O contrato LOT-sal moderno da Fase 7.1 usa `wall_pressure_Pa >= 0` como
  pressao compressiva positiva e separa isso do sinal geometrico do
  deslocamento radial.

**Contrato Fase 7.1 para LOT-saltcreep:**
- `radial_displacement_m > 0`: deslocamento radial para fora.
- `radial_displacement_m < 0`: deslocamento radial para dentro.
- `radial_closure_m >= 0`: magnitude positiva de fechamento,
  `max(0, -radial_displacement_m)`.
- `radial_strain` segue o deslocamento radial: positivo em expansao e negativo
  em fechamento.
- `effective_closure_pressure_Pa >= 0`: pressao efetiva compressiva positiva.
- O futuro adapter para `external/saltcreep` deve provar o mapeamento de sinal
  da condicao de contorno do backend antes de acoplar LOT/APB.

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

## R11 — LOT/PKN moderno não resolve balanço volumétrico anular legado

**Severidade:** Alta | **Status:** Confirmado na Fase 10.17A

A auditoria da Fase 10.17A confirmou que o caminho legado `LOT_Tese` calcula
pressão de poço/anular por balanço volumétrico envolvendo volume injetado
`Vq`, volume anular `Vi`, compressibilidade do fluido `k`, variação de volume
`dV` e, após abertura, termo de leakoff/fratura. O critério legado usa:

```text
pw = pi + dP
opened = pw > sigmaTheta
```

O caminho moderno `lot-pkn` atual calcula:

```text
p_net = E' * w / h
```

e não usa volume anular nem compressibilidade do fluido para resolver uma
série de pressão de poço. A Fase 10.16 passou a exportar volume anular
diagnóstico, mas essa informação ainda não participa da pressão PKN.

**Impacto:** Comparações diretas entre `pw_Pa` legado e
`net_pressure_Pa` moderno continuam semanticamente bloqueadas.

**Mitigação implementada:** a Fase 10.17B cria o modo moderno opcional
`volumetric_balance`, sem alterar o default `pkn_direct`, exportando campos
separados de `wellbore_pressure_Pa` e diagnóstico de balanço. Essa mitigação
é diagnóstica e não constitui validação física de fratura.

## R12 — Pressão inicial/hidrostática legada não fecha sozinha a comparação de `pw`

**Severidade:** Média | **Status:** Confirmado na Fase 10.18B

A Fase 10.18B confirmou que o legado da tese usa uma pressão inicial por anular:

```text
line_up[lu].pi(idAnnular)
```

No caminho de fluido prescrito, essa pressão é calculada por:

```text
p_ref + 9.81 * rho_ppg * 119.826427 * depth
```

e entra explicitamente em:

```text
pw = pi + dP
```

No BUZ67D auditado, o primeiro registro exportado indica:

```text
pw_Pa(t=0) = 26732215.17314985
dP(t=0) = 0
```

A Fase 10.18B adicionou `lot.initial_pressure` como campo opt-in moderno e
passou a calcular:

```text
wellbore_pressure_Pa = initial_pressure_Pa + dP_balance_accumulated
```

para `pressure_model = volumetric_balance`. Entretanto, a inclusão desse valor,
com o modelo de balanço simplificado atual, superestima a pressão máxima legada
no ciclo BUZ67D completo. Logo, a pressão inicial é parte necessária do contrato
de `pw`, mas não é suficiente para validar equivalência física.

**Mitigação:** manter o resultado como diagnóstico. Antes de declarar
equivalência, ainda são necessários contratos para semântica de `dP`, shut-in
com mecanismos dissipativos, casing/acomodação, Zamora e critério legado de
fratura/leakoff.

## R08 — Unidade de `dt`: coerente com a taxa de fluência; LOT_APB_v5 usa [h]

**Severidade:** Alta | **Status:** Confirmado em 2026-06-01

Arquivos auditados:
- `legance/LOT_APB_v5/include/apb/apb_salt_1d.h`
- `legance/LOT_APB_v5/src/apb/apb_salt_1d.cpp`
- `legance/LOT_APB_v5/include/sestsal/solver.h`
- `legance/LOT_APB_v5/src/sestsal/solver.cpp`
- `legance/LOT_APB_v5/src/sestsal/element.cpp`
- `legance/LOT_APB_v5/main/main.cpp`

**Evidência direta:**
- `APBSalt1D::solveThermalViscoStep(double dt_h)` recebe `dt_h` explicitamente nomeado em horas.
- `APBSalt1D` armazena `time_h` e `dt_h` como membros.
- `Solver::dt` é comentado como `last time increment, [h]`.
- `Element::incrementalViscousForces(double _dt)` multiplica diretamente a taxa de fluência por `_dt`.
- O APB principal usa `tac = 80 * 7 * 24` e escreve tempo como `t / 24 / 7`, consistente com `t` em horas.

**Conclusão específica do `LOT_APB_v5`:** O `dt` passado para `solveThermalViscoStep(dt)` está em **horas [h]**. O solver SESTSAL desse ramo espera taxa de fluência compatível com hora, e o passo interno adaptativo do wrapper (`dt = 1.e-6`, `dt_max = 0.001`) também está em horas.

**Regra geral:** `dt` é o incremento temporal numérico do modelo constitutivo e deve ser coerente com a unidade da taxa de deformação ativa. Se a taxa estiver em `[1/s]`, o `dt` correspondente deve estar em segundos; se estiver em `[1/h]`, em horas; se estiver em `[1/min]`, em minutos. Esse incremento pode ser definido pelo usuário, escolhido adaptativamente ou previamente inicializado pelo backend.

**Tempo de simulação e acomodação:** O tempo total de simulação é definido pelo usuário. O tempo de acomodação (`tac`/`stabilization_h`) representa o intervalo inicial decorrido sem incrementos térmicos ou injeção/variação operacional de fluidos, permitindo a acomodação mecânica/viscosa antes do carregamento principal.

**Impacto para o código novo:**
- `time.dt_h` permanece em horas no YAML e no `CaseData` como escala de entrada do APB/LOT.
- Um futuro `SaltCreepSESTSALAdapter` deve converter o passo de tempo para a unidade esperada pelo backend chamado.
- Para o wrapper `LOT_APB_v5`, passar `dt_h` em horas.
- Para uma implementação SESTSAL ou saltcreep que opere com taxa em segundos/minutos, converter explicitamente na fronteira para manter consistência dimensional.

**Risco lateral observado:** A versão ativa de `APBSalt1D::solveThermalViscoStep` não atribui `this->dt_h = dt_h`; `storeResults()` usa o membro `dt_h`, que fica inicializado em `0`. Isto sugere que o armazenamento temporal interno do wrapper pode estar incorreto nessa versão, embora o incremento mecânico passado ao solver ainda use o `dt` interno em horas. Não corrigir no legado; tratar no futuro adapter.

---

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
| R08 | Unidade de `dt` em modelos de fluência | Alto | **CONFIRMADO** — `dt` deve ser coerente com a taxa de deformação; no wrapper APB/SESTSAL do LOT_APB_v5 é [h] |
| R09 | Expressão suspeita `/ M_PI / 22` na conversão de vazão | Alto | **MITIGATED_FOR_AUDITED_PKN_CASES; BLOCKER_FOR_IDQ4_REGRESSION** — Fase 6.6 quantificou o fator 11 e confirmou que os dois PKN auditados usam `idQ == 6`, nao o ramo `/22` |
| R10 | Volume anular sem raio interno de drill pipe | Alto | **MITIGATED_FOR_BUZ67D_DIAGNOSTIC; NOT_PHYSICAL_VALIDATION** — Fase 10.16 documenta a convencao per-radian do legado e adiciona geometria opcional de drill pipe ao caso controlado moderno |

## R09 — Expressão suspeita `/ M_PI / 22` na conversão de vazão PKN

**Severidade:** Alta | **Status:** MITIGATED_FOR_AUDITED_PKN_CASES; BLOCKER_FOR_IDQ4_REGRESSION

**Localização:** `legance/LOT_Tese/src/apb_code/APB1da.cpp`, linha aproximada 8,
função `Conv_bbmin_m3h(double Q)`.

**Evidência:** A função `Conv_bbmin_m3h` contém:

```cpp
constexpr double Conv_bbmin_m3h(double Q) { return Q * 9.53924 / M_PI / 22; }
```

A auditoria Fase 6.3 (`docs/audits/R09_pkn_mpi22_audit.md`) e o ensaio
controlado Fase 6.6 (`docs/audits/R09_pkn_conversion_experiment.md`) mostraram que:
- `9.53924` é compatível com `bbl/min -> m³/h`;
- `/ M_PI / 22` é equivalente a `/ (M_PI * 22)` e preserva unidade, mas aplica
  fator adimensional não documentado;
- as demais conversões equivalentes usam `/ M_PI / 2`;
- os casos PKN auditados (`8-BUZ-67D-RJS-VISCO-pkn.cpp` e
  `9-BUZ-39DA-RJS-VISCO-2.cpp`) usam `idQ == 6`, portanto chamam
  `Conv_bbmin_m3min(Q) = Q * 0.158987 / M_PI / 2`, não `Conv_bbmin_m3h`.
- para a mesma base `Q * 9.53924`, o ramo `/22` gera exatamente `1/11` do valor
  do ramo `/2`.

**Impacto:**
- Se um caso usar `idQ == 4`, `/ M_PI / 22` reduz `Qinj` por fator 11 em relação
  ao padrão `/ M_PI / 2`.
- Para os PKN auditados com `idQ == 6`, o impacto direto dessa linha específica
  é nulo. R09 fica mitigado para esses dois casos enquanto permanecer comprovado
  que o caminho ativo é `idQ == 6`.
- A regressão PKN legado × moderno continua bloqueada para `idQ == 4`, para
  arquivos `.dat` cujo `idQ` de geração não esteja provado e para qualquer uso
  geral da família de conversões do legado como referência física.
- O caminho PKN ainda tem outros pontos pendentes (`t` absoluto, `time` desde
  breakdown e volume `w0 * L1 * M_PI`), portanto a Fase 6.6 não libera validação
  quantitativa legado × moderno.

**Condição para desbloquear:**
1. Confirmar, por metadado de geração ou reexecução controlada, quais `idQ`
   foram usados nos `.dat` PKN existentes.
2. Para `idQ == 4`, obter justificativa física/documental para `22` ou tratar o
   ramo como não confiável para regressão.
3. Documentar a formulação física moderna de PKN em SI antes de usar qualquer
   baseline legado.

**Não bloqueia:** implementação de tipos de entrada, estrutura do `PknModel` e testes
unitários com entradas sintéticas. **Bloqueia:** comparação com baseline legado PKN.

---

## R10 — Volume anular deve descontar drill pipe

**Severidade:** Alta | **Status:** MITIGATED_FOR_BUZ67D_DIAGNOSTIC; NOT_PHYSICAL_VALIDATION

**Localizacao:** `legance/LOT_Tese/src/apb_code/Layers.cpp`, funcao de montagem de
`line_up[idLineUp].Vi(e)`, e `legance/LOT_Tese/src/apb_code/Solids.cpp`.

**Evidencia direta:**

```cpp
// Layers.cpp
a = this->v_solids[this->tier[idTier]->order(1, e_1)]->getRe_m();
b = this->v_solids[this->tier[idTier]->order(1, e1)]->getRi_m();
this->line_up[idLineUp].Vi(e) = (pow(b, 2) - pow(a, 2)) * this->getThickness(idLineUp) / 2;

// Solids.cpp
double Solids::getRi_m() { return Conv_pol_m(this->di) / 2; }
double Solids::getRe_m() { return Conv_pol_m(this->de) / 2; }
```

O caso BUZ67D PKN legado declara o drill pipe como:

```cpp
vsolids.push_back(new Solids(true, 1922., profTeste, 210E9, 0.3, 4.67, 5.5, 20, 0));
```

`Solids.h` define `di` e `de` como diametros em polegadas. Portanto, para esta
rota, `di = 4.67 in` e `de = 5.5 in` sao diametros, e os raios usados na
geometria sao obtidos por conversao polegada -> metro e divisao por 2.

**Convencao de volume:** o legado armazena `Vi` por radiano:

```text
V_rad = 0.5 * (R_outer^2 - R_inner^2) * L
V_total = 2*pi*V_rad
```

**Impacto:** uma comparacao moderna que usa `R_inner = 0` superestima o volume
hidraulico do anular quando ha drill pipe presente. Isso afeta diagnosticos de
volume e qualquer futura rota APB/pressao que dependa de volume anular.

**Mitigacao da Fase 10.16:** o caso controlado
`cases/validation/buz67d_pkn_legacy_aligned.yaml` passa a declarar
`wellbore.drill_pipe`, e o resultado moderno LOT/PKN passa a exportar:

```text
initial_annular_volume_per_radian_m3
initial_annular_volume_m3
annular_outer_radius_m
annular_inner_radius_m
annular_length_m
annular_volume_convention
annular_volume_source
```

Essa mitigacao e diagnostica. O `PknModel` continua sem consumir volume anular
para calcular pressao, e nenhuma equivalencia fisica com o LOT_Tese e declarada.

---

## R13 — Critério legado de fratura por sigma tangencial não está no PknModel

**Severidade:** Alta | **Status:** PARTIALLY_EXTRACTED; MODERN_APPROXIMATION_ONLY

**Evidência:** a auditoria da Fase 10.18C identificou que o legado usa a pressão
da simulação:

```text
P_simulacao = line_up[lu].pi(idAnnular) + line_up[lu].dP(idAnnular)
```

e inicia fratura quando:

```text
|P_simulacao| > |sigma_tangencial(altura_de_influencia)|
```

O `PknModel` moderno não possui, nesta fase, a tensão tangencial nodal na
altura de influência. Portanto, o critério não foi reproduzido no solver PKN.
A rota moderna usa apenas `fracture.breakdown.pressure` como aproximação
simplificada opt-in para habilitar o desconto de `fracture_volume_m3` e
`leakoff_volume_m3` no balanço volumétrico.

**Impacto:** a curva moderna com balanço de fratura/leakoff continua sendo
diagnóstica. Não validar `sigmaTheta`, `margin`, `opened`, dano, ruptura ou
pressão de fratura física a partir dessa rota.

---

## Itens pendentes após auditoria

- [x] Convenção de sinais → FA03 (compressão positiva)
- [x] Temperatura no modelo: °C, não K → FA02
- [x] Unidade de e0: [1/min] internamente → FA01
- [x] Mecanismo de acoplamento sal→APB → FA04
- [x] **R08:** `dt` deve seguir a unidade temporal da taxa de fluência; no wrapper APB/SESTSAL do LOT_APB_v5 é [h]
- [x] **R09:** Fase 6.6 executou ensaio analitico controlado; mitigado para os dois PKN auditados (`idQ == 6`), ainda blocker para `idQ == 4` e regressao quantitativa ampla
- [x] **R10:** Fase 10.16 adicionou suporte diagnostico a volume anular com drill pipe no caso controlado BUZ67D, preservando a convencao per-radian do legado
- [x] **R13:** Fase 10.18C auditou o criterio legado de fratura por sigma tangencial e manteve a rota moderna como aproximacao opt-in por `fracture.breakdown.pressure`
- [x] **R14:** Fase 10.18D confirmou que `sigma_theta_compression_positive_Pa`
  existe no diagnostico moderno, mas ainda nao e fonte runtime para
  `lot-sim run --mode lot-pkn`
- [x] **R15:** Fase 10.18E confirmou que um threshold estatico extraido do
  legado abre cedo demais no moderno e nao substitui o criterio sigma-theta
- [x] **R16:** Fase 10.18F confirmou que a divergencia nao e bug local
  comprovado de ordem do sink; o moderno abre cedo por mismatch de criterio
- [x] **R17:** Fase 10.19A criou `sigma_theta_static` opt-in, mas o proxy
  estatico ainda abre cedo demais e nao e validacao fisica

### R14 — Sigma-theta disponivel apenas como diagnostico

**Severidade:** Alta | **Status:** Confirmado na Fase 10.18D

A Fase 10.18D auditou o criterio legado:

```text
pw = pi + dP
sigmaTheta = -getSigmaTheta()
opened = pw > sigmaTheta
```

O moderno ja possui `sigma_theta_compression_positive_Pa`,
`margin_Pa`, `opened` e `legacy_algebra_opened` no diagnostico sigma-theta.
Entretanto, esses campos sao gerados pelo caminho experimental:

```text
SaltCreepTimeBridge -> SaltWallStressDiagnostics -> LotSaltSigmaThetaDiagnostic
```

e nao pelo runtime:

```text
CaseParser -> PknRunner -> PknModel -> ResultWriter
```

Portanto, `sigma_theta_compression_positive_Pa` nao deve ser usado como gatilho
runtime de fratura no `volumetric_balance` enquanto nao houver uma fronteira
opt-in que forneca, de forma testada, `SigmaThetaInfluenceLayer` ao calculo de
pressao. O gate da fase e:

```text
SIGMA_THETA_AVAILABLE_DIAGNOSTIC_ONLY
```

Usar `first_wall_sample` ou ponto de Gauss mais proximo da parede como criterio
fisico sem mapear a altura de influencia legada e risco de falso positivo.

---

## R15 — Threshold estático legado não reproduz o critério sigma-theta

**Severidade:** Alta | **Status:** Confirmado na Fase 10.18E

A Fase 10.18E extraiu do audit legado um marcador rastreável de início de
fratura:

```text
Momento da quebra = 8.5 min = 510 s
pw_Pa             = 67342521.84592447 Pa
dP                = 8131435.236221395 Pa
```

Como o `PknModel` moderno interpreta `fracture.breakdown.pressure` como limiar
incremental acima de `initial_pressure_Pa`, o caso diagnóstico
`buz67d_pkn_legacy_static_breakdown.yaml` usa o delta `dP`, não a pressão
absoluta `pw_Pa`.

Mesmo com essa calibração, o modo moderno `volumetric_balance` abre a rota de
sink cedo demais:

```text
classificacao = STATIC_BREAKDOWN_OPENED_TOO_EARLY
primeiro sink moderno = 30 s
marcador legado = 510 s
max moderno 10.18E = 26.732215 MPa
max legado = 69.035836 MPa
```

**Impacto:** `fracture.breakdown.pressure` não deve ser tratado como substituto
físico do critério legado `pw > sigmaTheta`. Ele permanece apenas ferramenta
diagnóstica opt-in até que uma rota runtime forneça a tensão tangencial da
altura de influência ao balanço volumétrico.

---

## R16 — Auditoria instrumentada não autoriza correção local do sink

**Severidade:** Alta | **Status:** Confirmado na Fase 10.18F

A Fase 10.18F instrumentou temporariamente o `LOT_Tese` para observar a ordem
entre abertura por:

```text
pw > sigmaTheta
```

e entrada do sink volumétrico. No traço auditado, o primeiro `opened` ocorreu em
`510 s` e o primeiro incremento positivo de fratura/leakoff ocorreu em `540 s`,
classificando o legado como:

```text
LEGACY_SINK_NEXT_STEP
```

Apesar disso, o traço moderno do caso
`cases/validation/buz67d_pkn_legacy_static_breakdown.yaml` abriu em `30 s`.
A comparação foi classificada como:

```text
OTHER
```

porque o threshold estático moderno abre antes do critério legado sigma-theta.
Isso indica mismatch de critério, não bug local comprovado na ordem do sink em
`PknModel`.

**Impacto:** não alterar a ordem do balanço volumétrico para perseguir o
marcador de `510 s`. A próxima evolução deve implementar uma rota explícita e
opt-in para fornecer a tensão tangencial na altura de influência ao critério de
abertura, ou manter `fracture.breakdown.pressure` como proxy diagnóstico.

---

## R17 — `sigma_theta_static` é arquitetura opt-in, não validação física

**Severidade:** Alta | **Status:** Confirmado na Fase 10.19A

A Fase 10.19A adicionou o critério opt-in:

```text
lot.fracture.initiation.type = sigma_theta_static
```

O critério usa:

```text
margin_Pa = wellbore_pressure_trial_Pa - sigma_theta_compression_positive_Pa
opened = margin_Pa > 0
```

e mantém `constant_pressure` e `pkn_direct` preservados. Essa arquitetura evita
que `PknModel` dependa de `saltcreep`; o valor de sigma-theta é fornecido de
forma estática/diagnóstica pelo YAML.

No caso `buz67d_pkn_legacy_sigma_theta_static.yaml`, usando o proxy estático:

```text
sigma_theta_compression_positive_Pa = 67342521.84592447 Pa
```

o moderno ainda abriu em `30 s`, com:

```text
fracture_initiation_pressure_Pa = 82129237.46813472
fracture_initiation_margin_Pa   = 14786715.62221025
classificacao                   = SIGMA_THETA_STATIC_OPENED_TOO_EARLY
```

**Impacto:** `sigma_theta_static` prova a arquitetura de provider, mas não deve
ser tratado como critério físico validado. A próxima evolução precisa de uma
fonte runtime de `SigmaThetaInfluenceLayer`/altura de influência, provavelmente
via rota opt-in de `SaltCreepTimeBridge`/`SaltWallStressDiagnostics`.

---

## R18 — `volumetric_balance` moderno não inclui complacência geométrica pré-fratura

**Severidade:** Alta | **Status:** Confirmado na Fase 10.19B

A Fase 10.19B auditou a hipótese de erro de vazão no caso BUZ67D. O legado usa
`idQ = 6`, `Q = 0.5 bbl/min` e converte:

```text
Q_total = 0.0794935 m3/min
Q_rad = Q_total / (2*pi)
```

No primeiro passo de `30 s`, isso gera:

```text
dV_rad = 0.00632589173433779 m3/rad
```

Usando `V_annular_rad = 0.17842518895535997 m3/rad` e
`C = 6.4e-10 1/Pa`, a compressão pura do fluido produz:

```text
dP_theoretical = 55396919.53121999 Pa
```

Esse valor bate com a escala do salto trial moderno. O legado auditado, porém,
apresenta no primeiro passo:

```text
legacy_first_dP = 1845413.7784679066 Pa
legacy_first_dP / dP_theoretical = 0.03331256651017148
```

A causa raiz foi classificada como:

```text
ROOT_CAUSE_MISSING_GEOMETRIC_COMPLIANCE
```

porque `APB1da` usa a fórmula ativa:

```text
dP = (alpha*dT - (-Vq + dV - dMl/(rho*FC))) / Vi / k
```

e `dV` vem de deslocamentos geométricos do anular (`u(e)`, `u(e1)`). O moderno
10.19B ainda usa apenas compressão de fluido menos sinks de fratura/leakoff.

**Impacto:** não corrigir isso com fator empírico de pressão. A próxima fase
deve planejar/implementar um modelo opt-in explícito de `annular_compliance` ou
`wellbore_compliance`, preservando `pkn_direct` e casos padrão.

**Atualizacao Fase 10.19C:** foi criado um modelo opt-in
`constant_geometric` que usa `C_eff = C_fluid + C_geom`. O valor diagnostico
`C_geom = 1.8571966938610005e-8 1/Pa` foi inferido do primeiro passo legado e
aproxima o primeiro `dP` e o pico de pressao, mas permanece um proxy constante.
Ele nao substitui um modelo mecanico validado de casing/rocha e nao altera o
default `pkn_direct`.

**Atualizacao Fase 10.20A:** a auditoria confirmou que o `dV` legado e
calculado por area anular deformada com deslocamentos `u(e)`/`u(e1)`:

```text
dV = 0.5 * h * ((b + u_outer)^2 - (a + u_inner)^2) - Vi
```

Foi formulado o candidato `elastic_annular_simple`, mas o gate ficou
`MECHANICAL_COMPLIANCE_FORMULATION_PARTIAL`: a estimativa elastica simples para
BUZ67D (`C_geom ~= 1.7242805809704984e-10 1/Pa`) e muito menor que o proxy
diagnostico da 10.19C. Assim, qualquer implementação deve continuar opt-in,
experimental e sem declarar validacao fisica.
- [x] Definir contrato moderno de pressao/deslocamento/fechamento LOT-saltcreep
      — Fase 7.1, ver `docs/23_lot_salt_sign_convention.md`
- [ ] Confirmar convenção de sinal de `u_wall` no wrapper legado antes de usar
      `LOT_APB_v5` como referencia numerica direta
      — arquivo: `legance/LOT_APB_v5/include/apb/apb_salt_1d.h`
- [ ] Comparar SESTSAL entre LOT_Tese e LOT_APB_v5 (risco R03)
