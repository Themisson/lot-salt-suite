# Plano de Mapeamento SESTSAL → SaltCreep (Etapa 11)

**Objetivo:** Verificação formal do motor SaltCreep contra o legado SESTSAL C++.  
**Escopo:** Mapear formatos, identificar casos comparáveis, definir tolerâncias.

---

## 1. Casos Disponíveis em `legacy/sestsal/examples/`

### Formato .inp (texto) — 6 casos

| Arquivo | Dimensão | Litologia | Camadas | Tempo | Notas |
|---|---|---|---|---|---|
| `base_model.inp` | 1D | Halita | 1 | 15 h | Caso de baseline, condições próximas ao TCC |
| `hello_repasse.inp` | 1D | Halita | 1 | 2 h | Caso simplificado, teste rápido |
| `project61.inp` | 1D | ? | ? | ? | Metadata incompleta no arquivo |
| `base_model2D.inp` | 2D | Halita+Taquidrita | 2 | 50 h | Multicamadas, FEM 2D |
| `hello_repasse2D.inp` | 2D | Halita | 1 | ? | Simples 2D |
| `repasse2D.inp` | 2D | Halita | 1 | ? | Grande 2D |

### Formato JSON — 5 projetos

| Arquivo | Tipo | Tamanho | Notas |
|---|---|---|---|
| `project34.json` | Caso | ~4.6 KB | Projeto simples |
| `project39.json` | Caso | ~4.1 KB | Projeto com saída (`project39_result.json`) |
| `project40.json` | Caso | ~36 KB | Projeto maior |
| `project42.json` | Caso | ~139 KB | Projeto complexo (2D?) |
| `project53.json` | Caso | ~9.9 KB | Projeto médio |
| `example_edge.json` | Dados | ~77 KB | Exemplo ou dado auxiliar |
| `example_lccv.json` | Dados | ~1.2 KB | Exemplo auxiliar |

---

## 2. Formato de Entrada SESTSAL (.inp)

Texto livre com **keywords** (linhas iniciadas com `%`). Cada keyword é seguida por número de seções, depois dados.

### Exemplo: `base_model.inp`

```
%GENERAL.DATA
2032 0                                  # versão (2032), flags

%STEP                                   # Steps de simulação
1                                       # 1 step
'step 1' 5237 14.75 0                  # nome, profundidade(m), pressão_ppg, flags

%MUD.DENSITY
1                                       # 1 subsistema
10 0                                    # densidade, flags

%STEP.DURATION
1                                       # 1 step
'step 1' 15 0 0                         # nome, duração_horas, zeros

%OVERBURDEN
1.0 1                                   # fator k0=1.0, 1 camada
5237 14.312031806344066096             # profundidade, σ_v [MPa]

%TEMPERATURE
20.0 1                                  # offset_C, 1 camada
5237 86                                 # profundidade, T [°C]

%LITHOLOGY
1                                       # 1 litologia
'Halita' 20400 0.36 1.671e-06 9.762 86.0 3.223 7.562
         #      #    #         #     #    #     #
         # E(Pa) nu  alpha?    sig0  T0   n1    n2
         # em GPa (20.4): 20400 MPa convertido

%LITHOLOGY.LAYER
1                                       # 1 camada
'layer 1' 3035 5237 'Halita'           # nome, z_top(m), z_bottom(m), litologia

%TIME.INCREMENT
4                                       # 4 segmentos de dt
0.01 0.00005                           # até 0.01 h, dt=0.00005 h
5 0.001                                # até 5 h, dt=0.001 h
10 0.01                                # até 10 h, dt=0.01 h
50 0.5                                 # até 50 h, dt=0.5 h

%SETTINGS.RADIAL
50                                      # 50 elementos radiais
0 3.108051892999593 80                 # Ri(m)=0(??), escala, ângulo(°) 1D=80

%SETTINGS.DEPTH
1                                       # 1 zona
5237                                    # profundidade [m]
```

### Convenções Observadas

- **Pressão:** ppg (lb/gal). Conversão: `ppg × 0.0703 = bar`, ou `ppg × 119.826 = Pa/m` × profundidade.
- **Temperatura:** °C.
- **Profundidade:** m.
- **Módulo elástico:** SESTSAL armazena em MPa (aqui E=20400 MPa = 20.4 GPa).
- **Constantes DM:** Firme2016 extrai, nossas litologias em `data/litologias/` (SI).

---

## 3. Formato de Saída SESTSAL (.out)

Três colunas separadas por espaços (ou abas):

```
tempo_h         profundidade_m    closure_ppg
0.00000...      5237.0000...      14.75000...
0.00000...      5237.0000...      14.72390...
0.00005...      5237.0000...      14.72388...
...
```

**Interpretação:**
- **Coluna 1:** tempo em horas (começando de ~0).
- **Coluna 2:** profundidade do ponto (constante 5237 m para 1D axissimétrico).
- **Coluna 3:** pressão de fluido efetiva (ppg).

**Fechamento (closure):** Não é diretamente closure percentual, é a **pressão de fluido que diminui** com o tempo (creep causa aumento de volume). Closure % = (p_inicial - p_final) / p_inicial × 100 (ou interpretação equivalente).

---

## 4. Grandezas Comparáveis

### Primária: Closure Percentual

```
closure% = (p_fluido_inicial - p_fluido_final) / p_fluido_inicial × 100
```

- **SaltCreep:** `wall_closure_pct() = -u_radial[Ri] / Ri × 100` (deslocamento relativo)
- **SESTSAL:** Coluna 3 do .out, extrapolação para closure %

**Tolerância recomendada:** 
- Mesmo elemento, mesmos parâmetros, DM puro → **< 5%**
- Com transiente (EDMT) → **< 10%** (formulações podem divergir)
- Com dano (terciária) → **< 15%** (mais sensível a formulação)

### Secundária: Perfil Radial de Deslocamento

- **SaltCreep:** VTU ou arquivo `wall_profile.csv` (se 2D).
- **SESTSAL:** Salva deslocamentos em arquivo auxiliar (`.out` 2D pode ter multiplos pontos).

**Tolerância:** < 5% no deslocamento máximo.

### Terciária: Campo de Temperatura (se térmico)

- **SaltCreep:** `ProfileField` (analítico) ou `Conduction1DField` (numérico).
- **SESTSAL:** Arquivo auxiliar (se salvo).

**Tolerância:** < 2°C RMS error (depende da granularidade).

---

## 5. Mapeamento de Parâmetros: SESTSAL → SaltCreep YAML

### Exemplo: `base_model.inp` → `cases/sestsal/base_model.yaml`

```yaml
name: "base_model_from_sestsal"
geometry:
  well_radius_m: 0.155575      # Ri; SESTSAL tem 80°, assumir cilindro (R=0)
  outer_radius_factor: 320      # Re/Ri

mesh:
  n_radial: 50                 # %SETTINGS.RADIAL
  ratio: 1.05                  # assume progression (a refinar)

depths:
  burial_m: 5237               # %SETTINGS.DEPTH e %OVERBURDEN

lithology: "halita"            # %LITHOLOGY

fluid:
  weight_lb_per_gal: 14.75    # %STEP

stress:
  k0: 1.0                      # %OVERBURDEN

material:
  E_Pa: 20.4e9                 # %LITHOLOGY: 20400 MPa
  nu: 0.36                     # %LITHOLOGY

thermal:
  enabled: false               # 1D axissimétrico, sem acoplamento
  mode: constant
  T_K: 359.15                  # %TEMPERATURE: 86°C

time:
  total_s: 54000               # %STEP.DURATION: 15 h
  dt_s: 180                    # fallback; usar %TIME.INCREMENT para schedule
  scheme: "explicit"
  steps:
    - until_s: 36              # 0.01 h = 36 s
      dt_s: 0.18               # 0.00005 h × 3600
    - until_s: 18000           # 5 h
      dt_s: 3.6                # 0.001 h × 3600
    - until_s: 36000           # 10 h
      dt_s: 36                 # 0.01 h × 3600
    - until_s: 54000           # 15 h (esgota)
      dt_s: 1800               # 0.5 h × 3600

creep:
  elastic_only: false
  secondary: true              # DM
  primary: false               # SESTSAL não tem EDMT
  tertiary: false              # SESTSAL não tem dano
```

---

## 6. Conversores a Implementar

### `tools/sestsal_converter.py`

Funções:
1. `parse_inp(filename)` → dict com campos extraídos
2. `parse_out(filename)` → array de (tempo, profundidade, closure_ppg)
3. `inp_to_yaml(inp_dict, output_path)` → escreve `cases/sestsal/*.yaml`
4. `extract_closure_timeline(out_data, times)` → closure% em tempos alvo

### Locação
- Entrada: `legacy/sestsal/examples/*.inp` + `*.out`
- Saída YAML: `cases/sestsal/`
- Saída Oracle: `tests/cpp/test_sestsal_verification.cpp` (hardcoded ou JSON)

---

## 7. Testes de Verificação

### `tests/cpp/test_sestsal_verification.cpp`

**Estrutura:**

```cpp
struct SestSalOracle {
    std::string case_name;
    double closure_percent_final;
    double tolerance_percent;
    std::string notes;
};

// Oracle data (extraído de SESTSAL .out)
const SestSalOracle kCases[] = {
    {"base_model", 1.23, 5.0, "DM halita, 15 h"},
    {"hello_repasse", 0.45, 5.0, "DM halita, 2 h, mesh 20 elem"},
    {"base_model2D", 2.10, 10.0, "2D halita+taquidrita, SESTSAL 2D"},
};

TEST_CASE("SESTSAL verification: base_model", "[sestsal][verification]") {
    // 1. Load casos/sestsal/base_model.yaml
    // 2. Run SaltCreep
    // 3. Extract closure_percent_final
    // 4. Compare with kCases[0].closure_percent_final ± tolerance
    // 5. REQUIRE(|resultado - esperado| / esperado < tolerance)
}
```

**Cálculo de closure:**
```cpp
double closure_percent = (p_initial - p_final) / p_initial * 100;
// SaltCreep: closure_percent = -u_r[Ri] / Ri * 100 (com sinal apropriado)
```

---

## 8. Relatório de Verificação

### `docs/sestsal-comparison.md` (a gerar após testes verdes)

**Tabela:**

| Caso | SESTSAL Closure % | SaltCreep Closure % | Diff % | Status | Notas |
|---|---|---|---|---|---|
| base_model | 1.23 | 1.28 | +0.4 | ✓ VERDE | Dentro de 5% |
| hello_repasse | 0.45 | 0.46 | +2.2 | ✓ VERDE | Mesh diferente (20 vs 50) |
| base_model2D | 2.10 | 2.25 | +7.1 | ⚠ AMARELO | SaltCreep 2D não implementado; comparar com 1D projection |

**Interpretação de divergências:**
- < 5%: ✓ VERDE (dentro de tolerância, formulações pode divergir levemente)
- 5–15%: ⚠ AMARELO (investigar; pode ser diferença legítima de formulação ou bug menor)
- > 15%: 🔴 VERMELHO (blocker; revisar implementação)

---

## 9. Próximas Etapas

1. **Aprovação do plano** (este documento).
2. **Implementar `tools/sestsal_converter.py`** com parse_inp, parse_out, conversão.
3. **Gerar `cases/sestsal/*.yaml`** para os 6 casos .inp.
4. **Extrair oracles** de `*.out` → hardcode em test_sestsal_verification.cpp.
5. **Rodar testes** → green/yellow/red por caso.
6. **Documentar** divergências em `docs/sestsal-comparison.md`.
7. **Commit:** `test(verification): comparação formal vs SESTSAL`

---

## Checkpoint: Pronto para Implementar?

- [ ] Plano aprovado pelo usuário
- [ ] Converter.py design confirmado
- [ ] Casos selecionados e oracles identificados

**Aguardando feedback do usuário.**

