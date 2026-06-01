# Catálogo de modelos constitutivos

Lista das leis de fluência a implementar como `ConstitutiveModel`. Ordem de implementação,
equações e armadilhas. Cada lei é uma subclasse; o motor não muda.

## Ordem de implementação (não pule etapas)
1. **DM** (mecanismo duplo) — Etapa 1. Secundária. Base de todos os outros. ✓ IMPLEMENTADO
2. **EDMT** — Etapa 2. Primária empírica. Deve saturar para DM no regime permanente. ✓ IMPLEMENTADO
3. **ISV_SH_DM** — Etapa 8c. Primária com seno-hiperbólico (Munson-Dawson). Alternativa ao EDMT com endurecimento mais sofisticado.
4. **Motta v1/v2** ou **Wang 2004 CDM** — Etapa 8a. Terciária com dano Kachanov.
5. **Aubertin ISV_SH_D** — Etapa 8b. Formulação unificada com dano e temperatura. Mais sofisticada que ISV_SH_DM.
6. **Envoltórias de dilatância** (Spier, Hou/Lux, DeVries, Hunsche) — Etapa 9. Junto com (4) ou (5).

## DM — Mecanismo duplo de deformação (Costa & Poiate, 2008)

✓ **Status:** Implementado em `include/constitutive/double_mechanism.hpp` + `src/constitutive/double_mechanism.cpp`.

Lei de fluência secundária (regime permanente). Equação:
```
ε̇^v = ε̇₀ · (σ_ef / σ₀)^n · exp[(Q/R)(1/T₀ − 1/T)]
```
- ε̇^v: taxa de deformação efetiva (na direção do tensor desviador, material isotrópico).
- ε̇₀: taxa de referência (calibrada por litologia).
- σ_ef: tensão efetiva (von Mises ou desviadora — convenção do projeto).
- σ₀: tensão de referência.
- n: expoente; depende do nível de tensão:
  - n = 3 se σ_ef ≤ σ₀ (mecanismo de dislocation glide)
  - n = 5 se σ_ef > σ₀ (mecanismo de dislocation climb)
- Q: energia de ativação (J/mol; por litologia).
- R: 8.314 J/(mol·K).
- T: temperatura absoluta (K), vem do `ThermalField`.

Direção:
```
ε̇^v_ij = √(3/2) · ε̇^v · s_ij / σ_ef
```
onde s_ij é o tensor desviador. Componente volumétrica é zero (material isotrópico).

**Constantes** (halita, taquidrita, carnalita): valores em `data/litologias/`. Não inventar.
Os valores do TCC vêm de Poiate et al. (2006).

## EDMT — Primária empírica

✓ **Status:** Implementado em `include/constitutive/edmt.hpp` + `src/constitutive/edmt.cpp`. Testes verdes (6/6).

**Referência:** Firme et al. (2016, 2018). Costa & Poiate (2006).

**Equação:**
```
ε̇_total = ε̇_DM · (1 + K₁ · exp(−K₂ · εv))    [primary + secondary]
ε̇_DM    = ε̇₀ · (σ_ef/σ₀)^n · exp[Q/R·(1/T₀ − 1/T)]
```

**Estado interno:**
```
dεv/dt = |ε̇_total|    [accumulated effective viscous strain, dimensionless]
```

**Comportamento:**
- Inicial (εv=0): taxa = (1+K₁)·ε̇_DM (amplificação transiente).
- Regime permanente (εv→∞): taxa → ε̇_DM (satura no mecanismo duplo) ✓
- Flag `include_secondary`:
  - true: primary + secondary (físico, recomendado).
  - false: primary only (útil para testes, emite warning).

**Parâmetros:** K₁, K₂ carregados do YAML da litologia. Se ausentes, K₁=0, K₂=0 (DM puro).

## ISV_SH_DM — Primária com seno-hiperbólico

✓ **Status:** Implementado em `include/constitutive/isv_sh_dm.hpp` +
`src/constitutive/isv_sh_dm.cpp`.

**Referência:** Munson & Dawson (1990); Chan et al. (1992, 1994).

Implementação operacional como alternativa à EDMT para a fase primária. Com
`secondary:true`, a taxa total é a soma de DM secundária com um termo primário
Munson-Dawson de seno-hiperbólico que decai com a deformação primária acumulada:

```
ε̇^v = ε̇^v_DM + ε̇^v_primary

ε̇_primary = ε̇0 · sinh(σ_ef/σ_ref)^n · exp[(Q/R)(1/T0 - 1/T)] · h(ε_v^p)
h(ε_v^p) = 1 / sinh(asinh(1) + K_h · ε_v^p)
dε_v^p/dt = |ε̇_primary|
```

O deslocamento `asinh(1)` em `h` é uma regularização numérica: mantém `h(0)=1`
e evita a singularidade de `1/sinh(K_h ε_v^p)` em deformação inicial nula. Para
`ε_v^p` crescente, `h -> 0`; assim, com `secondary:true`, a lei satura para DM.

Parâmetros padrão:

| Parâmetro | Halita | Unidade |
|---|---:|---|
| `e0_s` | `5.0e-7` | `1/s` |
| `sig_ref` | `1.0e6` | `Pa` |
| `n` | `1.5` | – |
| `Q_J_mol` | `51.6e3` | `J/mol` |
| `K_h` | `1.2` | – |

YAML:
```yaml
creep:
  secondary: true
  primary: true
  primary_model: isv_sh_dm
  isv_sh_dm:
    e0_s: 5.0e-7
    sig_ref: 1.0e6
    n: 1.5
    Q_J_mol: 51.6e3
    T0: 359.15
    K_h: 1.2
```

**Diferenças vs. EDMT:**
- EDMT usa potência em tensão e transiente exponencial empírico `K1 exp(-K2 εv)`.
- ISV_SH_DM usa relação `sinh(σ_ef/σ_ref)^n` para a parte primária e hardening seno-hiperbólico.
- Ambas convergem para DM no regime permanente quando `secondary:true`.

## Motta v1 — Terciária com dano
Implementado na Etapa 4b como uma extensão da DM com dano escalar Kachanov. Na Etapa 9,
a envoltória de dilatância passou a ser uma interface plugável (`DilatancyEnvelope`) com
implementações `Spier`, `Ratigan`, `DeVries` e `Hunsche`.

Taxa viscosa:
```
ε̇^v_Motta = ε̇^v_DM / (1 - D)^n_d
```

Evolução do dano:
```
dD/dt = A_d · max(f_dil, 0)^m_d / (1 - D)^p_d
D ∈ [0, D_max], com D_max = 0.99 por padrão
```

Se `D = 0`, a taxa é exatamente a DM. Se `f_dil <= 0`, o dano não evolui, mas um dano
preexistente continua amplificando a taxa por `(1-D)^(-n_d)`.

Exemplo com envoltória Spier:
```
f_dil = sqrt(J2) - a · I1_comp - b
```

Convenção de sinal verificada no código em 2026-05-30: as tensões internas usam mecânica
clássica com compressão negativa. No Modelo A, o estado geostático inicial é
`[-119.7, -119.7, -119.7, 0] MPa`. Portanto a implementação calcula:
```
I1_comp = -I1
f_dil = sqrt(J2) + a · I1 - b
```
Assim, confinamento hidrostático compressivo fica seguro (`f_dil <= 0`) e somente
desvio/tensão suficiente ativa o dano.

Tangente para o integrador implícito:
```
∂ε̇^v_Motta/∂σ = (1 - D)^(-n_d) · ∂ε̇^v_DM/∂σ
```
Esta é a tangente simplificada aprovada para a Etapa 4b: `D` fica fixo durante a
linearização local, e é atualizado ao final da avaliação constitutiva.

### Diagnóstico de falha

A Etapa 8d adiciona diagnóstico operacional de falha por dano, sem alterar a lei constitutiva.
Quando `output.damage_tracking:true` e `creep.damage:true`, os integradores escrevem:

- `damage_wall.csv`: evolução de `D`, `eps_dot` e `sigma_ef` no ponto de Gauss mais próximo da
  parede interna.
- `damage_events.csv`: eventos por ponto de Gauss quando `D` cruza limiares configuráveis,
  quando `D >= failure_D_critical`, quando a taxa supera um múltiplo da DM pura no mesmo ponto,
  e quando a taxa muda de tendência de desaceleração para aceleração.

Interpretação:
- `D = 0`: rocha intacta no modelo terciário.
- `0 < D < D_max`: dano progressivo; a taxa é amplificada por `(1-D)^(-n_d)`.
- `D -> D_max`: aproximação numérica de falha/ruptura; a taxa cresce rapidamente e o problema
  exige `implicit_adaptive`.

O ponto de inflexão em `eps_dot(t)` é usado como marcador clássico da transição do regime
secundário/primário desacelerante para a terciária acelerante. O critério prático de falha
fica em `output.failure_D_critical` (padrão `0.5`) e deve ser calibrado experimentalmente.

## Motta v2
[Esqueleto — preencher quando implementar.] Variante posterior com calibração mais rica
da evolução de dano.

## Wang 2004 — CDM com dano não-linear

✓ **Status:** Implementado em `include/constitutive/wang_2004.hpp` +
`src/constitutive/wang_2004.cpp`.

Modelo de dano contínuo (CDM) usado como alternativa ao Motta v1 para a fase terciária.
A implementação segue o contrato operacional extraído de Wang 2019 / FeiWu 2018 / Wu 2020,
com DM como taxa base e dano escalar acoplado à tensão equivalente.

Taxa viscosa:
```
ε̇^v_Wang = ε̇^v_DM / (1 - D)^n_d
```

Evolução do dano:
```
dD/dt = A_d · σ_ef^m_d / (1 - D)^p_d
σ_ef = sqrt(3/2 · s:s)
D ∈ [0, D_max], D_max = 0.99
```

O integrador local resolve implicitamente a atualização escalar de D para o passo constitutivo;
se a equação ultrapassa o limite físico/numerico no passo, D é saturado em `D_max`.
Com `A_d = 0` ou `dt = 0`, `D` fica fixo e a lei reduz exatamente ao DM quando `D=0`.

Parâmetros padrão carregados pelo parser:

| Parâmetro | Halita | Taquidrita | Unidade |
|---|---:|---:|---|
| `A_d` | `1.2e-8` | `3.5e-8` | `1/s/Pa^m` |
| `m_d` | `2.5` | `2.8` | – |
| `p_d` | `1.0` | `1.2` | – |
| `n_d` | `2.0` | `2.0` | – |
| `D_max` | `0.99` | `0.99` | – |

YAML:
```yaml
creep:
  secondary: true
  tertiary: true
  damage: true
  tertiary_model: wang_2004
  wang_2004:
    A_d: 1.2e-8
    m_d: 2.5
    p_d: 1.0
    n_d: 2.0
    D_max: 0.99
```

Tangente para o integrador implícito:
```
∂ε̇^v_Wang/∂σ = (1 - D)^(-n_d) · ∂ε̇^v_DM/∂σ
```
Assim como no Motta v1, a linearização mantém D fixo durante a montagem local do Newton.
Como os parâmetros publicados são muito agressivos em unidades SI, use `implicit_adaptive` e
calibração específica antes de interpretar previsões de falha quantitativamente.

## Aubertin ISV_SH_D — unificado

✓ **Status:** Implementado em `include/constitutive/aubertin_isv_sh_d.hpp` +
`src/constitutive/aubertin_isv_sh_d.cpp`.

Modelo unificado com variáveis de estado interno, baseado na trilha Aubertin/Firme
(Firme 2016, Firme 2018 e `firme2019` conforme `docs/reference-index.md`). Combina
primária, secundária, terciária e dano em uma única lei, sem compor EDMT + Motta por fora.

Variáveis internas:
```
eps_v_primary    deformação viscosa primária acumulada
eps_v_secondary  deformação viscosa secundária acumulada
D                dano escalar, D ∈ [0, D_max]
```

Taxa viscosa:
```
ε̇^v = ε̇0 · (σ_ef/σ0)^n · exp[(Q/R)(1/T0 - 1/T)]
      · f_primary(eps_v_primary) · f_creep(D)

f_primary = 1 + K1 · exp(-K2 · eps_v_primary)
f_creep   = 1/(1-D)^n_d
```

Evolução do dano:
```
dD/dt = A_d · σ_ef^m_d · (1-D)^p_d · g(eps_v)
g(eps_v) = max(eps_v_primary + eps_v_secondary, 0)
```

A atualização local usa iteração de ponto fixo em forma backward-Euler para `eps_v_primary`,
`eps_v_secondary` e `D`. A tangente mantém as variáveis internas fixas durante a linearização,
isto é, deriva a taxa instantânea em relação à tensão com os multiplicadores ISV congelados.

Parâmetros operacionais de partida para halita Muribeca:

| Parâmetro | Valor | Unidade |
|---|---:|---|
| `e0_s` | `5.0e-7` | `1/s` |
| `sig0` | `1.0e6` | `Pa` |
| `n` | `3.0` | – |
| `Q_J_mol` | `51.6e3` | `J/mol` |
| `K1` | `0.8` | – |
| `K2` | `2.5` | `1/strain` |
| `A_d` | `1.5e-8` | `1/s/Pa^m` |
| `m_d`, `n_d`, `p_d` | `2.5`, `2.0`, `1.0` | – |
| `D_max` | `0.99` | – |

YAML:
```yaml
creep:
  tertiary: true
  damage: false          # opcional; Aubertin tem dano intrínseco
  tertiary_model: aubertin_isv_sh_d
  aubertin_isv_sh_d:
    e0_s: 5.0e-7
    sig0: 1.0e6
    n: 3.0
    Q_J_mol: 51.6e3
    T0: 359.15
    K1: 0.8
    K2: 2.5
    A_d: 1.5e-8
    m_d: 2.5
    n_d: 2.0
    p_d: 1.0
    D_max: 0.99
```

Com `A_d=0`, `D=0` e parâmetros base equivalentes, a lei reduz à forma EDMT exponencial
`ε̇ = ε̇_DM · (1 + K1 exp(-K2 eps_v_primary))`. Para previsões quantitativas, calibrar os
parâmetros com ensaios de Firme/Aubertin antes de usar os defaults em cenários de falha.

## Envoltórias de dilatância (critérios de dano)

✓ **Status:** Implementado em `include/constitutive/dilatancy_envelope.hpp` +
`src/constitutive/dilatancy_envelope.cpp`.

A envoltória é uma função `f(σ) = 0` no espaço de tensões. Acima dela (`f > 0`), o
material está em regime dilatante e a terciária/dano pode iniciar. Abaixo, regime seguro.
Não é critério de ruptura — é critério de início de dano. O `MottaV1` usa a interface
virtual:

```cpp
class DilatancyEnvelope {
public:
    virtual double dilatancy_function(double I1, double J2) const = 0;
};
```

Convenção de sinal: o código usa tensões internas com compressão negativa; portanto os
critérios calibrados em geomecânica são avaliados com `I1_comp = -I1` quando o termo
representa confinamento. Para Spier, isso é equivalente a `sqrt(J2) + a·I1 - b`.

| Envoltória | Fórmula implementada | YAML |
|---|---|---|
| Spier | `f = sqrt(J2) - a·I1_comp - b` | `dilatancy_envelope: Spier` |
| Ratigan / Van Sambeek | `f = sqrt(J2) - c·(I1_comp + d)^m` | `dilatancy_envelope: Ratigan` |
| DeVries | `f = sqrt(J2) - e·sinh(f_coeff·I1_comp/σ0)` | `dilatancy_envelope: DeVries` |
| Hunsche | `f = sqrt(J2) - g·(I1_comp/I1_ref)^h` | `dilatancy_envelope: Hunsche` |

Defaults operacionais:

| Parâmetro | Valor |
|---|---:|
| `spier.a`, `spier.b_Pa` | `0.25`, `0.0` |
| `ratigan.c`, `ratigan.d_Pa`, `ratigan.m` | `0.81`, `0.0`, `1.0` |
| `devries.e_Pa`, `devries.f`, `devries.sigma0_Pa` | `10.0e6`, `1.0`, `30.0e6` |
| `hunsche.g_Pa`, `hunsche.I1_ref_Pa`, `hunsche.h` | `10.0e6`, `30.0e6`, `1.0` |

As referências Hou/Lux/Fossum/Ratigan/DeVries/Hunsche trazem famílias de critérios e
calibrações dependentes do sal e do ensaio; por isso os defaults acima são pontos de partida
e todos os coeficientes são parametrizáveis no YAML. Para previsões quantitativas de falha,
calibrar a envoltória com ensaios triaxiais da litologia alvo.

## Padrão de implementação (todas as leis)
1. Subclasse de `ConstitutiveModel` em `main/constitutive/` + `src/constitutive/`.
2. Construtor recebe parâmetros via struct (lidos do YAML); NUNCA hard-code.
3. Método `evaluate()` puro: dado σ, estado, T, dt → retorna ε̇^v, novo estado, D.
4. Registro no factory por nome (string que aparece no YAML: `creep.primary_model: "EDMT"`).
5. Teste unitário: ponto material isolado sob tensão+T constantes, comparar com solução
   analítica (quando existir) ou com curva publicada.
6. Para leis com primária: teste de saturação para DM no regime permanente.
7. Para leis com dano: teste de monotonia (D não decresce) e limite numérico.

## Armadilhas conhecidas
- **Voigt vs Mandel**: convenção do tensor de tensões/deformações. Voigt é o padrão; cuidado
  com fatores de √2 nas componentes de cisalhamento se misturar convenções.
- **Sinal de compressão**: em geomecânica, compressão é positiva (oposto da convenção da
  mecânica dos sólidos clássica). O projeto adota compressão positiva — consistente com TCC,
  dissertação e SESTSAL.
- **Unidades**: σ em Pa, ε adimensional, ε̇ em 1/s, T em K, Q em J/mol. R = 8.314. Erro de
  unidade em Q (J/mol vs kJ/mol) é o erro de calibração mais comum no creep.
- **Voigt indices**: para axissimétrico (r, θ, z), a ordem padrão do projeto é
  [σ_rr, σ_θθ, σ_zz, σ_rz]. Documentar e respeitar.
- **σ_ef = 0** (caso degenerado, antes do furo): a direção do tensor desviador é indefinida.
  Retornar ε̇^v = 0 e direção zero; não dividir por zero.
