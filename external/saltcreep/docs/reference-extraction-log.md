# Log de Extrações — Referências Bibliográficas

Template reutilizável para extrações de novos PDFs:

```
## [Autores] [Ano]

**PDF:** `docs/references/.../arquivo.pdf` | **Páginas:** 1–N  
**Tema:** uma linha sobre o paper  
**Étapa(s):** (Etapa 2, Etapa 8c, etc.)

### Equações Constitutivas (exatas do PDF)

(Copiar números de equação, variáveis, e unidades)

### Parâmetros (tabela com unidades)

(Extrair parâmetro | valor | unidade | nota)

### Caso(s) de Validação

(Descrição breve: que foi testado, em que condições, qual o resultado)

### Notas

(Convenções de sinal, considerações para implementação)
```

---

## ✓ Firme 2016

**PDF:** `docs/references/new_references/EquacoesConstitutivas/Firme2016_Article_AnAssessmentOfTheCreepBehaviou.pdf`  
**Autores:** Firme, Pedro A.L.P.; Roehl, Deane; Romanel, Celso  
**Ano:** 2016  
**Tema:** Avaliação do modelo multi-mecanismo (MD) para halita brasileira  
**Étapa(s):** Etapa 1 (DM base) + Etapa 8c (ISV_SH_DM, se implementar)

### Equações Constitutivas — Modelo Multi-Mecanismo (MD)

**Eq. (1) — Taxa de fluência por mecanismo DGL (Dislocation Glide):**
```
ε̇_DGL = |H(σ_eq − σ₀)| · B₁ exp(−Q₁/RT) 
         + B₂ exp(−Q₂/RT) · sinh(q(σ_eq − σ₀)/μ)
```
onde H é função Heaviside; σ₀ limiar do mecanismo; B₁, B₂, Q₁, Q₂, q são constantes.

**Eq. (2) — Taxa DCL (Dislocation Climb):**
```
ε̇_DCL = A₁ exp(−Q₁/RT) · (σ_eq/σ_ref)^n₁
```

**Eq. (3) — Taxa UMC (Undefined Mechanism):**
```
ε̇_UMC = A₂ exp(−Q₂/RT) · (σ_eq/σ_ref)^n₂
```

**Eq. (4) — Taxa total estado permanente:**
```
ε̇_ss = ε̇_DGL + ε̇_DCL + ε̇_UMC
```

**Eq. (5)–(6) — Transiente com endurecimento:**
```
F = exp[Δ(1 − ξ/ξ_t*)²]   ,  ξ < ξ_t*    [hardening]
  = 1                      ,  ξ = ξ_t*    [saturação]
  = exp[−δ(1 − ξ/ξ_t*)²]  ,  ξ > ξ_t*    [recovery]

ξ̇ = (F − 1) ε̇_ss            [evolução da variável de endurecimento]
```

**Eq. (7) — Parâmetro de endurecimento:**
```
Δ = α_a + β_a log(σ_eq/G)
```

**Eq. (8) — Taxa de fluência transiente:**
```
ε̇_t = K₀ exp(cT) (σ_eq/μ)^m
```

### Parâmetros — Halita Brasileira (Formação Muribeca, Sergipe)

**Tabela 2 — Parâmetros MD, Conjunto A:**

| Parâmetro | Valor | Unidade | Significado |
|---|---|---|---|
| A₁ | 1.638×10⁷ | s⁻¹ | pré-fator DCL |
| Q₁ | 104,500 | J/mol | energia de ativação DCL |
| n₁ | 7.2 | – | expoente de tensão DCL |
| A₂ | 1.924×10⁸ | s⁻¹ | pré-fator UMC |
| Q₂ | 41,800 | J/mol | energia de ativação UMC |
| n₂ | 3.2 | – | expoente de tensão UMC |
| σ₀ | 20.57 | MPa | limiar DGL (Heaviside) |
| q | 5335 | – | constante sinh |
| B₁ | 9.981×10⁴ | s⁻¹ | amplitude DGL 1 |
| B₂ | 4.976×10⁻⁵ | s⁻¹ | amplitude DGL 2 |
| m | 3.0 | – | expoente transiente |
| K₀ | 7.750×10⁴ | – | pré-fator transiente |
| c | 9.198×10⁻³ | K⁻¹ | coef. temperatura transiente |
| α_a | −17.37 | – | coef. endurecimento 1 |
| β_a | −7.738 | – | coef. endurecimento 2 |
| δ | 0.58 | – | parâmetro recovery |

**Propriedades Elásticas:**
- E = 25.37 GPa
- ν = 0.36

### Caso de Validação — Ensaios Triaxiais

| Teste | σ_conf | Δσ | Duração | Resultado |
|---|---|---|---|---|
| A | 10 MPa | 10 MPa | ~350 h | Concordância excelente primária + secundária + terciária |
| B | 14 MPa | 14 MPa | ~1000 h | Mesmo acima |
| C–D | 16–18 MPa | 16–18 MPa | ~2200 h | Idem |

Validação de campo: poço pré-sal Santos Basin, 4107–4250 m. Previsão de fechamento de poço concordou com medições de caliper ao longo de 10 h e 30 dias.

Validação de mina: galeria de 4×3 m na mina Taquari-Vassouras. Convergência vertical ao longo de 6 anos: erro < 10% vs. campo.

### Notas

- Compressão positiva (convenção padrão).
- O modelo completo envolve 3 mecanismos (DGL, DCL, UMC) acoplados com transiente via F(ξ).
- No SaltCreep, simplificamos para DM (dois mecanismos) — Firme2018 mostra isso.
- Parâmetros variam com litologia; tabela acima é para halita Muribeca.

---

## ✓ Firme 2018

**PDF:** `docs/references/new_references/EquacoesConstitutivas/Firme2018_Article_EnhancedDouble-mechanismCreepL.pdf`  
**Autores:** Firme, P.A.L.P.; Brandao, N.B.; Roehl, D.; Romanel, C.  
**Ano:** 2018  
**Tema:** Leis DM aprimoradas (EDMT, EDMP)  
**Étapa(s):** Etapa 2 (EDMT) — JÁ IMPLEMENTADO ✓

### Equações — EDMT (Enhanced DM with Transient Function)

**Eq. (1) — DM padrão:**
```
ε̇_ss = ε̇₀ exp(Q/R·(1/T₀ − 1/T)) · (σ_d/σ₀)^n
```

**Eq. (2) — EDMT com função transiente F:**
```
ε̇ = F · ε̇_ss
```

**Eq. (3) — Função transiente (Firme):**
```
F = exp[Δ(1 − ξ/ξ_t*)²]   ,  ξ ≤ ξ_t*
  = exp[−δ(1 − ξ/ξ_t*)²]  ,  ξ > ξ_t*
```

**Eq. (4) — Parâmetro Δ:**
```
Δ = α_a + β_a log(σ_d/G)
```

**Eq. (5) — Limiar transiente:**
```
ξ_t* = K₀ exp(cT) (σ_d/σ₀)^m
```

**Eq. (6) — Evolução de ξ:**
```
ξ̇ = (F − 1) ε̇_ss
```

### Parâmetros — Halita Brasileira

**Tabela 2 — DM padrão:**

| Parâmetro | Valor | Unidade |
|---|---|---|
| Q | 50,160 | J/mol |
| ε̇₀ | 1.888×10⁻⁹ | h⁻¹ |
| σ₀ | 9.91 | MPa |
| T₀ | 359.15 | K |
| n₁ (σ ≤ σ₀) | 3.36 | – |
| n₂ (σ > σ₀) | 7.55 | – |

**Tabela 3 — Parâmetros EDMT:**

| Parâmetro | Valor | Unidade |
|---|---|---|
| K₀ | 7.750×10⁻⁷ | – |
| c | 9.198×10⁻³ | K⁻¹ |
| l | 3.0 | – |
| α_a | −17.37 | – |
| β_a | −7.738 | – |
| δ | 0.58 | – |

**Propriedades Elásticas:**
- E = 25.37 GPa
- ν = 0.36

### Casos de Validação

**Ensaios triaxiais (A, B, C/D):** mesmo como Firme2016. EDMT mostra concordância excelente com os dados experimentais, especialmente na fase transiente inicial.

**Galeria de mina (Taquari-Vassouras):** 4.0 m × 3.0 m, 8 anos de dados. EDMT e EDMP (power law) convergência vertical, erro < 5%.

**Poço pré-sal:** 4107–4250 m, predição de fechamento. EDMT e EDMP similares; ambas superiores ao DM padrão (32% subestimativa).

### Notas

- **Atenção:** A função F de Firme (Eq. 3) é diferente da implementação simplificada no SaltCreep (K₁·exp(−K₂·εv)).
- No SaltCreep usamos uma versão empiricamente calibrada: ε̇ = ε̇_DM · (1 + K₁ exp(−K₂ εv)).
- Ambas as funções descrevem transiente + endurecimento; a de Firme é mais sofisticada (inclui recovery para ξ > ξ_t*).
- Parâmetros Q/R, ε̇₀, σ₀, n₁, n₂ são os mesmos para DM em ambas as referências (Firme2016 e 2018).

---

## ✓ Chan 1992

**PDF:** `docs/references/new_references/EquacoesConstitutivas/artigos/chan1992.pdf`  
**Autores:** Chan, K.S.; Bodner, S.R.; Fossum, A.F.; Munson, D.E.  
**Ano:** 1992  
**Tema:** Modelo M-D com dano para fluência e dilatância  
**Étapa(s):** Etapa 8c (ISV_SH_DM com dano)

### Equações — Munson-Dawson + Dano

**Eq. (21) — Taxa total com transiente F:**
```
ε̇_eq = F · ε̇_s
```

**Eq. (23)–(25) — Mecanismos de estado permanente (M-D):**
```
Mecanismo 1:  ε̇_s1 = A₁ exp(−Q₁/RT) · (σ/μ)^n₁

Mecanismo 2:  ε̇_s2 = A₂ exp(−Q₂/RT) · (σ/μ)^n₂

Mecanismo 3:  ε̇_s3 = |H| · [B₁ exp(−Q₁/RT) + B₂ exp(−Q₂/RT)] · sinh(q(σ−σ₀)/μ)
```

**Eq. (26) — Função transiente F(ξ) (M-D clássico):**
```
F = exp[Δ(1 − ξ/ξ_t*)²]   ,  ξ < ξ_t*
  = 1                      ,  ξ = ξ_t*
  = exp[−δ(1 − ξ/ξ_t*)²]  ,  ξ > ξ_t*
```

**Eq. (27) — Limiar transiente:**
```
ξ_t* = K₀ c^(cT) (σ/μ)^m
```

**Eq. (28) — Evolução de ξ:**
```
ξ̇ = (F − 1) ε̇_s
```

**Eq. (16) — Evolução de dano (Kachanov-style):**
```
ω̇ = (x₃/x₄) ln(1/ω) · [σ_eq^w H(σ_eq^w)]^x₅ − h(ω, T, I_t)
```

onde ω ∈ [0,1] é dano; h é healing function.

**Eq. (17) — Dano acumulado (regime constante):**
```
ω = exp{−[(x₃/(σ_eq^w H(σ_eq^w)))^x₁] · (t/t_f)}
```

### Parâmetros — Sal Limpo (Clean Rock Salt)

**Tabela 1 — Constantes M-D para sal:**

| Parâmetro | Valor | Unidade | Mecanismo |
|---|---|---|---|
| A₁ | 8.360×10²² | s⁻¹ | Mec. 1 |
| Q₁ | 1.045×10⁵ | J/mol | Mec. 1 |
| n₁ | 5.5 | – | Mec. 1 |
| A₂ | 6.886×10⁶ | s⁻¹ | Mec. 2 |
| Q₂ | (idem) | J/mol | Mec. 2 |
| n₂ | (idem) | – | Mec. 2 |
| A₃ | 9.672×10¹² | s⁻¹ | Mec. 3 (DGL) |
| Q₃ | 4.18×10⁵ | J/mol | Mec. 3 |
| n₃ | 5.0 | – | Mec. 3 |
| B₁ | 3.034×10⁻² | s⁻¹ | DGL amplitude 1 |
| σ₀ | 20.57 | MPa | DGL limiar |
| q | 5335 | (no units) | sinh coeff. |

**Propriedades Elásticas:**
- μ (shear) = 12.4 GPa
- E = 31.0 GPa
- ν = 0.25

**Parâmetros Dano:**
- x₁, x₃, x₄, x₅: constantes do modelo de dano Kachanov.

### Casos de Validação

**Wallner (1984) Salt Data:** Ensaios triaxiais em sal sob diferentes confinamentos (1, 5, 10, 20 MPa). Modelo captura:
- Redução de taxa com confinamento crescente.
- Transição de compressão para dilatância (plastic dilatancy).
- Taxa volumétrica zero em regime desviador.

**WIPP Room D (in-situ):** Previsão de fechamento de câmara subterrânea. Taxa de convergência vertical vs. horizontal capturada corretamente.

### Notas

- Compressão positiva.
- Modelo acoplado: dano eleva a taxa viscosa via (1−ω)^(−n_d) termo.
- Healing function h (recuperação de dano) relevante para sal que veda fraturas.
- Chan1992 é base para ISV_SH_DM (Internal State Variable, sinh-hyperbolic, Double Mechanism).

---

## ✓ PoiateFalcao 2006

**PDF:** `docs/references/new_references/PETRO_COSTA, Well Design for Drilling Through Thick Evaporite Layers in Santos Basin - Brazil_2006.pdf`  
**Autores:** Poiate Jr., E.; Costa, A.; Maia, C.; Falcao, J.L.  
**Ano:** 2006  
**Publicação:** IADC/SPE 99161, Drilling Conference  
**Tema:** Lei DM aplicada a perfuração em camadas espessas de sal (Santos)  
**Étapa(s):** Etapa 1 (DM) + calibração de litologias

### Equações

**Lei DM (apresentado sem derivação; usa formato de duas taxas):**
```
ε̇ = ε̇₀ · (σ_eq/σ₀)^n · exp[Q/R · (1/T₀ − 1/T)]
```

Seleção de expoente n em função de σ_eq vs. σ₀ (tipo Costa/Poiate, idem Firme).

### Parâmetros por Litologia Brasileira

**Tabela de Propriedades Elásticas (Table 1 do paper):**

| Material | E [kPa × 10⁻⁴] | E [GPa] | ν |
|---|---|---|---|
| Halita | 2.040 | 20.4 | 0.36 |
| Carnalita | 0.402 | 4.02 | 0.36 |
| Taquidrita | 0.492 | 4.92 | 0.33 |
| Fine Limestone | 3.100 | 31.0 | 0.30 |
| Cimento | 6.100 | 61.0 | 0.23 |
| Casing | 21.000 | 210 | 0.28 |

**Parâmetros DM (extraídos do texto; valores aproximados):**
- Halita, Carnalita, Taquidrita têm constantes DM distintas.
- Q ≈ 12 kcal/mol = 50,208 J/mol (global para todos).
- ε̇₀, σ₀, n1, n2 variam por litologia.

### Casos de Validação

**Well Design, Santos Basin:**
- Dois planos de perfuração (A, B) em profundidades 2984–4960 m.
- Camadas: halita, carnalita, taquidrita.
- Modelagem FEM acoplada com constitutivo DM.
- Previsão de fechamento de poço, fechamento de revestimento, profundidade máxima alcançável.

**Resultados:** Simulações concordam com observações de campo (atividade de perfuração, tubing stuck, timing de cimentação).

### Notas

- Referência **fundamental** para calibração de constantes DM por litologia brasileira.
- As propriedades elásticas nesta tabela são as usadas em SaltCreep (`data/litologias/`).
- Valores de ε̇₀, σ₀, n podem ser extraídos de análise de sensibilidade do paper ou de fits posteriores (Firme2016/2018).

---

## ✓ Munson 1990

**PDF:** `docs/references/new_references/EquacoesConstitutivas/artigos/munson1990.pdf`  
**Autores:** Munson, D.E.; Fossum, A.F.; Senseny, P.E.  
**Ano:** 1990  
**Publicação:** Tunnelling and Underground Space Technology, Vol. 5(1), pp. 135–139  
**Tema:** Modelo Munson-Dawson (M-D) revisado, predição de fechamento WIPP  
**Étapa(s):** Etapa 8c (ISV_SH_DM)

### Equações — M-D (versão 1990)

**Strain rate total com transiente e recovery:**
```
ε̇ = F · ε̇_s + D · σ_eq^m
```
onde F é função transiente (hardening + recovery), ε̇_s é taxa permanente, D termo dano.

**Taxa permanente (superposição de 2–3 mecanismos):**
```
ε̇_s = Σ [A_i exp(−Q_i/RT) · (σ_eq)^n_i]
```

**Função transiente F(ξ, ξ*):**
```
F = exp[Δ(1 − ξ/ξ*)²]     [hardening, ξ < ξ*]
  = 1                      [saturação]
  = exp[−δ(1 − ξ/ξ*)²]    [recovery, ξ > ξ*]
```

**Evolução de ξ:**
```
ξ̇ = (F − 1) ε̇_s
```

### Parâmetros — Sal limpo + sal argiloso (WIPP)

**Tabela 1 — Material Constants for Clean Salt:**

| Parâmetro | Clean Salt | Argillaceous Salt | Unidade |
|---|---|---|---|
| A₁ | 8.386×10²² | 1.407×10²³ | s⁻¹ |
| Q₁ | 1.045×10⁵ | (idem) | J/mol |
| n₁ | 5.5 | 5.5 | – |
| A₂ | 2.5000 | 2.5000 | s⁻¹ |
| Q₂ | – | – | J/mol |
| n₂ | 5.086 | 8.998 | – |
| A₃ | 9.672×10¹² | 1.314×10¹³ | s⁻¹ |
| Q₃ | 4.18×10⁵ | (idem) | J/mol |
| n₃ | 5.0 | 5.0 | – |
| m | 3.0 | 3.0 | – |
| K₀ | 6.275×10⁵ | – | – |
| c | 0.009198 | – | K⁻¹ |
| α | −17.37 | – | – |
| β | −7.738 | – | – |
| δ | 0.58 | – | – |

### Casos de Validação

**WIPP Room D Closure (1984–1988):** In-situ closure of underground salt repository. Measured vs. predicted convergence (vertical + horizontal). Model captures:
- Primary (transient) phase: primeiros meses.
- Secondary (steady): meses a anos.
- Tertiary: regime permanente com recuperação (recovery) visível.

**Comparação Tresça vs. von Mises:** Paper valida via Tresça flow criterion (mais conservador para sal) vs. von Mises; ambos funcionam com o M-D.

### Notas

- **Histórica:** Munson1990 é a primeira publicação do modelo M-D completo com transiente/recovery.
- Referenciar Chan1992 e Firme2016 para versões estendidas (com dano).
- R = 8.314 J/(mol·K) universalmente.

---

## ✓ FeiWu 2018 (Wu et al. 2019)

**PDF:** `docs/references/new_references/EquacoesConstitutivas/artigos/FeiWu2018.pdf`  
**Autores:** Wu, Fei; Chen, Jie; Zou, Quanle  
**Ano:** 2019 (online 2018)  
**Publicação:** International Journal of Damage Mechanics, Vol. 28(5)  
**Tema:** Modelo não-linear de dano em fluência para sal  
**Étapa(s):** Etapa 8a (CDM alternativo ao Wang 2004) + Etapa 3 (terciária)

### Equações — Modelo de Dano Não-Linear

**Eq. (1) — Dano (Kachanov-style):**
```
D = 1 − exp(−a(t−t₀))   ,  t ≥ t₀
  = 0                    ,  t < t₀
```
onde t₀ é o tempo de início da fase acelerada, a é taxa de dano.

**Eq. (2) — Tensão efetiva (acoplamento damage):**
```
σ_efetiva = σ₀ / (1 − D)
```

**Eq. (3)–(6) — Taxa de fluência com dano:**
```
ε = ε₀ + ε₁ + ε₂
onde:
ε₁ = (σ₀/E₀) · [(1/(1−D)) − 1]        [elastic damage-induced]
ε₂ = ∫ ε̇(t) dt = ∫ [Aσ₀^n / (1−D)^n] exp(a(t−t₀)) dt    [creep damage-coupled]
```

**Strain rate no regime permanente (Maxwellian):**
```
ε̇ = σ₀/E + σ₀^n / [η(1+β)]  · t^β    [β = fractional order]
```

onde η é coeficiente de viscosidade, β ≈ 0.7–0.924 (subunitário → fluência acelerada).

### Parâmetros — Sal da China (Wangchu Mine)

**Tabela 1 — Parâmetros do modelo não-linear:**

| Parâmetro | Valor | Unidade |
|---|---|---|
| E/GPa | 0.54 | GPa |
| E₀/GPa | 22 | GPa |
| η / (GPa·h) | 177.65 | GPa·h |
| β | 0.924 | – |
| a | 0.0064 | – |
| A | 2.88×10⁻⁸ | – |
| n | 2.56 | – |

**Propriedades:**
- Sal chinês muito mais deformável (E = 0.54 GPa) que halita brasileira (20.4 GPa).
- Coeficiente de viscosidade alto (177.65 GPa·h).
- Expoente fracionário β = 0.924 ≈ 1 (próximo do caso linear, mas subunitário).

### Caso de Validação — Ensaio de Carga em Degraus

**Setup:** Triaxial creep test sob carregamento em degraus progressivos (10 etapas, cada uma escalando tensão).
- Duração total: 6 meses.
- Monitoramento: deformação axial, dano (via emissão acústica 3D).

**Resultados:**
- Fase acelerada (terciária) emerge no estágio 10.
- Dano na falha D ≈ 0.4.
- Modelo não-linear fit com χ² < 0.05 (excelente).

### Notas

- **atenção:** Este é um modelo CDM **alternativo**, não o Wang 2004 citado no roadmap.
- Aplicável a sal chinês (composição, granulatoria distinta).
- Requer calibração de a, A, n, β para cada litologia.
- Taxa de dano exponencial (Kachanov) simples, porém bem-validada.

---

## Validação Cruzada de Constantes

### DM (Firme2016/2018, Munson1990, PoiateFalcao2006)

Todas as referências concordam:
- **Halita brasileira:** E ≈ 20.4 GPa, ν ≈ 0.36, Q ≈ 50,208 J/mol.
- **Taquidrita:** E ≈ 4.92 GPa, ν ≈ 0.33.
- **Carnalita:** E ≈ 4.02 GPa, ν ≈ 0.36.

Implementado em `data/litologias/` com estes valores.

### M-D vs. DM

- **DM (Firme):** Dois mecanismos (dislocation-climb + undefined mechanism) → mais compato, 2 expoentes n₁, n₂.
- **M-D (Munson, Chan):** Três mecanismos (DCL + UMC + DGL) → mais completo, mais parâmetros.
- Firme2018 mostra que DM (simplificado) é indistinguível de M-D completo para halita em pequenos strain.

---

## Próximos PDFs a Processar

(Prioridade decrescente)

1. **Firme Dissertação 2019** (9.41 MB) — ISV_SH_D unificado. Prioridade 1 (Etapa 8b).
2. **Chan 1994** — M-D com healing. Prioridade 2 (Etapa 8c).
3. **Fossum 1993** — Envoltória de dilatância Hou/Lux. Prioridade 2 (Etapa 9).
4. **TCC_OTAVIO** — Casos de validação numéricos. Prioridade 3 (teste regressão).
5. **ARMA papers 2014–2022** — Múltiplos autores, validação calibração. Prioridade 3.

