# Casos de Validação — SaltCreep

Conjunto padrão de casos físicos com soluções analyticamente ou numericamente conhecidas para verificar implementação de leis constitutivas, elementos, e acoplamentos.

---

## Caso 1: Lamé Elástico (Etapa 0) — ✓ VERIFICADO

**Tipo:** Solução analítica 1D axissimétrica elástica.

**Geometria:**
- Cilindro vazado: Ri = 0.155575 m (160 mm), Re = Ri × 320 ≈ 50 m.
- Carregamento: pressão interna pi, pressão externa pe = pi × 0.5.

**Solução Lamé:**
```
σ_rr(r) = [pi·Ri² − pe·Re²] / (Re²−Ri²)  +  [pi−pe]·Re²·Ri² / [(Re²−Ri²)·r²]
σ_θθ(r) = [pi·Ri² − pe·Re²] / (Re²−Ri²)  −  [pi−pe]·Re²·Ri² / [(Re²−Ri²)·r²]
σ_zz = 0  (deformação plana axissimétrica)

u_r(r) = {[pi·Ri² − pe·Re²]·r} / [E(Re²−Ri²)]  +  {[pi−pe]·Ri²·Re²} / [E(Re²−Ri²)·r]
```

**Verificação:** Deslocamento u_r na parede interna deve concordar com Lamé até tolerância numérica (~1e-10 relativa).

**Arquivo de caso:** `cases/validation/lame_elastic.yaml`

**Status:** ✓ VERDE (ctest `test_lame`)

---

## Caso 2: Patch Test (Etapa 1 FEM) — ✓ VERIFICADO

**Tipo:** Campo de deslocamento linear deve ser reproduzido exatamente por elementos lineares; campo quadrático por elementos quadráticos.

**Geometria:** Malha quadrada/retangular com um elemento (ou refinada uniformemente).

**Carregamento:** Deslocamento prescrito linear (ou quadrático) nas bordas.

**Verificação:** Strain (derivada do deslocamento) deve ser constante (ou linear para quadráticos); tensão σ = D·ε deve ser constante; reação nas bordas deve satisfazer equilíbrio.

**Elemento testandido:** axisym_1d_L3 (linear), depois Q4, T3, Q8, Q9, T6 (2D).

**Status:** ✓ VERDE para L3 (ctest `test_patch_axisym_1d_L3`)

---

## Caso 3: TCC Modelo A — Baseline DM (Etapa 1, Etapa 2) — ✓ IMPLEMENTADO

**Tipo:** Regressão numérica vs. SESTSAL C++ (oracle).

**Geometria:** 1 camada halita, 50 m espessura, Ri = 160 mm, Re = 50 m.

**Condições:**
- Pressão de fluido: ~9.6 ppg (≈ 65 MPa a 5400 m profundidade).
- k0 = 1.0 (lateral earth pressure ratio).
- Temperatura: constante 370.88 K (=97.73°C), consistente com SESTSAL.
- Tempo de simulação: 360 h (15 dias).
- Constitutivo: DM (secundária) + EDMT (primária, se habilitado).

**Oracle (SESTSAL):**
- Obtido executando SESTSAL no caso equivalente (`legacy/sestsal/examples/modelo_A.inp`).
- Pontos de comparação: fechamento % em t = [12h, 48h, 120h, 240h, 360h].

**Valores esperados (orientativo, verificar com SESTSAL):**
```
t [h]   | Closure [%]
12      | 0.5–1.0
48      | 2.0–3.0
120     | 5.0–7.0
240     | 8.0–10.0
360     | 10.0–12.0
```

**Arquivo de caso:** `cases/tcc/modelo_A.yaml`

**Status:**
- ✓ EDMT verde (testes unitários + regressão EDMT simplificada)
- ⏳ Regressão vs. SESTSAL: precisa oracle finalizado

---

## Caso 4: Convergência de Elemento (Etapa 4) — ⏳ PENDENTE

**Tipo:** Estudo de convergência h (refinamento de malha).

**Geometria:** 1 camada halita, 50 m.

**Física:** DM + EDMT (primária + secundária), 100 h.

**Metodologia:**
1. Malha grossa: n_elem = 5.
2. Refinamento sucessivo: n_elem = 10, 20, 40, 80.
3. Solução de referência: extrapolação de Richardson (n_elem → ∞).

**Métrica de erro:** Deslocamento na parede interna.

**Taxa esperada de convergência:**
- Elemento linear (L3): ~h² (log-log slope = -2).
- Elemento quadrático (Q4, Q8): ~h³ ou h⁴.

**Arquivo de caso:** `cases/validation/convergence_base.yaml` (parametrizado por n_elem).

**Script:** `post/convergence.py` — plota log(erro) vs. log(h), extrai taxa.

**Status:** ⏳ Pendente (Etapa 4)

---

## Caso 5: Acoplamento Térmico (Etapa 5c) — ⏳ PENDENTE

**Tipo:** Comparação entre modo `profile` (analítico) e `conduction_1d` (numérico).

**Geometria:** 1D axissimétrico com 50 m halita.

**Condições térmicas:**
- Modo 1 (`profile`): T(z) = T_seabed + grad·z (linear, analítico).
- Modo 2 (`conduction_1d`): Equação de calor FEM (Crank-Nicolson β=0.5).

**Verificação:** Deformação termomecânica acoplada (ε_th + ε_v + ε_e) deve concordar entre os dois modos no regime linear e tempo suficiente.

**Critério:** Erro de fechamento < 1% entre `profile` e `conduction_1d` em 360 h.

**Arquivo de caso:** `cases/validation/thermal_profile_vs_conduction.yaml` (dois sub-casos).

**Status:** ⏳ Pendente (Etapa 5c)

---

## Caso 6: Dilatância e Envoltória (Etapa 9) — ⏳ PENDENTE

**Tipo:** Validação numérica da envoltória de dilatância Hou/Lux ou Spier.

**Geometria:** 1D, 50 m halita.

**Carregamento:** Série de patamares de pressão crescente.

**Verificação:**
1. Abaixo da envoltória (f_dil < 0): deformação volumétrica negativa (compressão).
2. Acima da envoltória (f_dil > 0): dilatância emerge, taxa cresce com dano.
3. Transição: é suave (não descontinuidade) graças ao modelo CDM.

**Arquivo de caso:** `cases/validation/dilatancy_envelope_hou.yaml`

**Status:** ⏳ Pendente (Etapa 9)

---

## Protocolo de Validação (em ordem obrigatória)

1. **Lamé elástico** — verifica FEM base, sem creep. Tol = 1e-10 relativa. ✓ VERDE
2. **Patch test** — verifica elemento isolado. Tol = 1e-12 relativa (reprodução exata). ✓ VERDE (L3)
3. **Regressão TCC modelo A–F** — verifica DM vs. oracle (SESTSAL). Tol = 5% relativa. ⏳ PENDENTE (oracle)
4. **Convergência elemento** — verifica taxa h² (linear), h³ (quadrático). ⏳ PENDENTE
5. **Consistência térmica** — verifica profile vs. conduction_1d. Tol = 1%. ⏳ PENDENTE
6. **Estabilidade numérica** — grandes dt, taquidrita (creep rápido). ⏳ PENDENTE
7. **Comparação campo** — vs. SESTSAL + ABAQUS em casos reais. ⏳ PENDENTE

**Nunca relaxe tolerância.**

Se um teste regredir, rodar `ctest --output-on-failure` antes de investigar.

