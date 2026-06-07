# 14 — Estratégia de comparação legado ↔ moderno

**Status:** Fase 10.13 concluída como auditoria documental  
**Escopo:** outputs legados disponíveis ↔ diagnóstico sigma-theta moderno  
**Restrição:** sem comparação numérica, sem instrumentar legado, sem alterar runtime

---

## Objetivo

Este documento define a estratégia de comparação entre os outputs legados já
extraíveis e os artefatos modernos do diagnóstico sigma-theta. A Fase 10.13 não
executa comparação numérica; ela estabelece o que pode ser comparado agora, o
que exige transformação e o que permanece bloqueado sem dados adicionais.

As fontes são:

```text
legance/LOT_Tese/*.dat existentes
legance/LOT_APB_v5/*.json existentes
tools/extract_legacy_lot_outputs.py
LotSaltSigmaThetaDiagnosticWriter
```

---

## Inventário legado

### LOT_Tese `.dat`

O extrator read-only da Fase 10.12B consegue produzir registros a partir dos
blocos exportados por `APB1da::saveFile(...)`:

| Campo | Significado operacional | Observações |
|---|---|---|
| `Time` | Série temporal bruta do legado | Unidade não inferida automaticamente; `time_unit_inferred = unknown`. |
| `Layer` | Índice de camada legado | 1-based; não equivale automaticamente a `layer_id` moderno. |
| `dT` | Incremento/variação térmica exportada | Campo por camada/anular/tempo. |
| `dP` | Incremento de pressão exportado | Não reconstrói `pw = pi + dP` sem `pi`. |
| `dV` | Variação de volume exportada | Não há campo sigma-theta moderno equivalente no writer atual. |
| `u` | Deslocamento/variável de fechamento exportada | Precisa de contrato antes de comparar com deslocamento moderno. |
| `Compressibilidade` | Compressibilidade usada no balanço | Campo APB/fluido, não campo sigma-theta. |
| `C_Exp` | Compressibilidade/expansibilidade auxiliar | Requer auditoria semântica antes de comparação. |
| `Vq` | Vazão/volume auxiliar exportado | O legado escreve com fator geométrico embutido. |
| `dV_leakoff` | Volume de leakoff/fratura no balanço | Métrica indireta; não equivale a `opened`. |
| `V_outflow` | Outflow agregado | Métrica indireta; não equivale a sigma-theta. |
| `Momento da quebra` | Primeiro instante bruto registrado pelo legado | Proxy escalar; não contém pontos/layers. |

### LOT_APB_v5 `.json`

O extrator também lê JSONs do `LOT_APB_v5`, incluindo o formato detalhado com
`results_by_time` e o formato top-level em lista com resultados diretos por
anular:

| Campo legado JSON | Campo normalizado | Observações |
|---|---|---|
| `pressure.start` | `pressure_start_psi`, `pressure_start_Pa` | Conversão `psi -> Pa`. |
| `pressure.final` | `pressure_final_psi`, `pressure_final_Pa` | Conversão `psi -> Pa`. |
| `pressure.diff` | `pressure_diff_psi`, `pressure_diff_Pa` | Conversão `psi -> Pa`. |
| `pressure.APB` | `pressure_apb_psi`, `pressure_apb_Pa` | Conversão `psi -> Pa`. |
| `volume.start` | `volume_start` | Unidade conforme legado. |
| `volume.final` | `volume_final` | Unidade conforme legado. |
| `volume.diff` | `volume_diff` | Unidade conforme legado. |
| `vented_bbl` | `vented_bbl` | Campo por resultado/anular. |
| `leakage_bbl` | `leakage_bbl` | Campo por resultado/anular. |
| `leakage_mass` | `leakage_mass` | Campo por resultado/anular. |
| `salt_displacement` | `salt_displacement` | JSON serializado; sem equivalência plena com wall stress moderno. |
| `temperature` | Ainda não exportado pelo extrator | Disponível em alguns JSONs, mas fora do CSV normalizado atual. |
| `density` | Ainda não exportado pelo extrator | Disponível em alguns JSONs, mas fora do CSV normalizado atual. |
| `md` | `md` | Profundidade medida exportada. |

### Campos ausentes no legado extraído

Os outputs existentes não exportam diretamente:

```text
pw
sigmaTheta
margin
opened
hoop_state
j2
von_mises
```

Esses campos só podem ser comparados ponto a ponto após instrumentação
controlada, nova exportação ou outro mecanismo validado de reconstrução.

---

## Inventário moderno

### `points.csv`

O `LotSaltSigmaThetaDiagnosticWriter` exporta, por cenário e ponto diagnóstico:

```text
case_id
scenario_id
scenario_label
step_index
time_s
sample_index
layer_id
gp_id
element_id
local_gp_id
r_m
z_m
depth_m
pressure_source
stress_source
pressure_map_method
pressure_map_label
wall_pressure_Pa
net_pressure_Pa
hydrostatic_pressure_Pa
surface_pressure_Pa
absolute_wellbore_pressure_Pa
sigma_theta_compression_positive_Pa
hoop_state
margin_Pa
opened
legacy_algebra_opened
tensile_hoop_state
mean_stress_Pa
j2_Pa2
von_mises_effective_stress_Pa
caveat
```

### `summary.csv`

O writer moderno exporta, por cenário:

```text
case_id
scenario_id
scenario_label
n_points
n_compressive
n_neutral
n_tensile
min_sigma_theta_compression_positive_Pa
max_sigma_theta_compression_positive_Pa
min_margin_Pa
max_margin_Pa
any_opened
any_legacy_algebra_opened
first_open_time_s
first_open_pressure_Pa
first_open_layer_id
```

### `metadata.json`

O writer moderno registra:

```text
case_id
generated_by
phase
format
input_case
files.points_csv
files.summary_csv
scenarios[].id
scenarios[].label
scenarios[].valid
scenarios[].n_points
scenarios[].n_steps
scenarios[].n_wall_samples
caveats
```

### Campos internos ainda não exportados

Alguns dados existem em módulos modernos, mas não necessariamente no writer
sigma-theta:

| Campo | Status |
|---|---|
| `radial_displacement_m` | Existe em respostas/diagnósticos de sal, mas não é coluna do writer sigma-theta. |
| `radial_closure_m` | Existe em contratos de sal, mas não é coluna do writer sigma-theta. |
| `creep_strain` | Não faz parte do writer sigma-theta atual. |
| `damage` / `tertiary creep` | Fora do writer sigma-theta atual. |
| Volume/fracture/leakoff moderno detalhado | Existe em outputs LOT/PKN, mas não no writer sigma-theta. |

---

## Matriz de comparabilidade

Classificação:

```text
direct      = mesmo conceito, mesma unidade ou conversão trivial
transform   = exige unidade, sinal, layer mapping ou normalização temporal
qualitative = tendência, ordem de grandeza ou comportamento sem ponto a ponto
blocked     = depende de instrumentação, dado adicional ou nova exportação
```

Prioridade:

```text
P0 = comparar primeiro, sanidade básica
P1 = comparação intermediária com transformação controlada
P2 = depende de instrumentação/export adicional
P3 = depende de acoplamento físico mais completo
```

| Campo legado | Fonte legada | Campo moderno | Fonte moderna | Comparabilidade | Transformação necessária | Pré-requisito | Risco | Prioridade |
|---|---|---|---|---|---|---|---|---|
| Existência de arquivo/caso | `.dat` / JSON | `case_id`, `input_case` | `metadata.json` | direct | Nenhuma | Definir pares de caso | Casos podem não ser fisicamente equivalentes | P0 |
| Número de registros | `legacy_points.csv` | `n_points` | `summary.csv` | direct | Agregação por cenário/fonte | Mesma granularidade definida | Contagens podem diferir por amostragem | P0 |
| `Time` | LOT_Tese `.dat` | `time_s` | `points.csv` | transform | Normalizar unidade temporal | Confirmar unidade FA01/legado | Curvas deslocadas por unidade errada | P0 |
| `Layer` | LOT_Tese `.dat` | `layer_id` / `gp_id` / `wall_stress_depth_m` | `points.csv` | transform | 1-based -> camada/profundidade/ponto | Mapa layer legado ↔ ponto moderno | Falso match por índice igual | P1 |
| `md` | LOT_APB_v5 JSON | `depth_m` / `wall_stress_depth_m` | `points.csv` | transform | Profundidade medida -> referência moderna | Definir referência vertical | MD não é necessariamente profundidade vertical | P1 |
| `pressure.start` | LOT_APB_v5 JSON | `pressure_start_Pa` | `legacy_points.csv` | direct | `psi -> Pa` | JSON válido e unidade psi | Pressão convertida pode vir de física diferente | P0 |
| `pressure.final` | LOT_APB_v5 JSON | `wall_pressure_Pa` | `points.csv` | transform | `psi -> Pa`; alinhar tempo/anular | Método de pressão moderno escolhido | Absoluta vs condição de parede pode divergir | P1 |
| `pressure.diff` | LOT_APB_v5 JSON | incremento de pressão moderno | `points.csv` / futuro | transform | `psi -> Pa`; definir incremento moderno | Coluna moderna de incremento ou cálculo | Incremento calculado de bases diferentes | P1 |
| `pressure.APB` | LOT_APB_v5 JSON | pressão APB/diff moderno | Futuro APB moderno | blocked | `psi -> Pa` e integração APB | APB moderno exportado | Comparar com sigma-theta seria mistura de escopo | P3 |
| `dP` | LOT_Tese `.dat` | `wall_pressure_Pa` | `points.csv` | qualitative | Avaliar incremento vs absoluto | `pi` legado ou referência equivalente | `dP` pode parecer bater com pressão absoluta | P2 |
| `dP` | LOT_Tese `.dat` | `net_pressure_Pa` | `points.csv` | qualitative | Definir se ambos são incrementos compatíveis | Contrato físico de referência | `p_net` PKN não é pressão anular | P2 |
| `dV` | LOT_Tese `.dat` | volume moderno | LOT/PKN outputs, não writer sigma-theta | blocked | Normalizar sinal/unidade/definição | Export moderno compatível | Conceitos de volume podem diferir | P3 |
| `dV_leakoff` | LOT_Tese `.dat` | métrica moderna de leakoff/fratura | LOT/PKN outputs, não writer sigma-theta | qualitative | Normalizar fator geométrico e unidade | Campo moderno escolhido | Leakoff não equivale a `opened` | P3 |
| `V_outflow` | LOT_Tese `.dat` | outflow/leakoff moderno | Futuro ou LOT/PKN output | blocked | Normalizar agregação e unidade | Campo moderno compatível | Métrica agregada pode esconder eventos | P3 |
| `Momento da quebra` | LOT_Tese `.dat` | `first_open_time_s` | `summary.csv` | qualitative | Normalizar tempo e critério | Instrumentação ou aceitação de proxy | Primeiro evento pode ter critério diferente | P2 |
| `salt_displacement` | LOT_APB_v5 JSON | `radial_displacement_m` | Diagnóstico interno, ainda não writer | qualitative | Definir sinal, ponto e tempo | Export moderno ou bridge diagnostic | Ponto de sal não é necessariamente parede | P3 |
| `pw` | Cálculo interno LOT_Tese | `wall_pressure_Pa` | `points.csv` | blocked | Exportar `pi + dP` ou reconstruir com `pi` | Instrumentação/novo dado | Reconstrução incompleta gera falso positivo | P2 |
| `sigmaTheta` | Cálculo interno LOT_Tese | `sigma_theta_compression_positive_Pa` | `points.csv` | blocked | Exportar `-getSigmaTheta()` | Instrumentação controlada | Sinal e ponto de amostra podem divergir | P2 |
| `pw - sigmaTheta` | Cálculo interno LOT_Tese | `margin_Pa` | `points.csv` | blocked | Exportar/reconstruir ambos | `pw` e `sigmaTheta` disponíveis | Margem moderna pode usar pressão diferente | P2 |
| `pw > sigmaTheta` | Cálculo interno LOT_Tese | `opened` / `legacy_algebra_opened` | `points.csv` | blocked | Exportar booleano ou reproduzir critério | `pw`, `sigmaTheta`, tempo e layer | Igualdade/threshold podem mudar resultado | P2 |
| `getDeviatoricStress()` | Interno LOT_Tese | `j2_Pa2` / `von_mises_effective_stress_Pa` | `points.csv` | blocked | Exportar tensão ou invariantes legados | Instrumentação do legado | Convenção de sinal/invariante pode divergir | P2 |
| `temperature` | LOT_APB_v5 JSON | temperatura moderna | Ainda não writer sigma-theta | blocked | Exportar/normalizar unidade | Campo moderno disponível | Temperatura não é comparável via sigma writer atual | P3 |
| `density` | LOT_APB_v5 JSON | densidade moderna | Ainda não writer sigma-theta | blocked | Normalizar unidade/conceito | Campo moderno disponível | Densidade de fluido vs rocha pode ser confundida | P3 |

### Distribuição da matriz

| Comparabilidade | Quantidade |
|---|---:|
| `direct` | 3 |
| `transform` | 6 |
| `qualitative` | 5 |
| `blocked` | 9 |

| Prioridade | Quantidade |
|---|---:|
| `P0` | 4 |
| `P1` | 5 |
| `P2` | 7 |
| `P3` | 7 |

---

## Sequência recomendada de comparação

### Nível 0 — Sanidade básica

Comparar primeiro:

```text
existência de caso equivalente
número de registros
faixa de tempo
ordem dos passos
número de camadas/registros por tempo
```

Caso mínimo recomendado:

```text
legado : legance/LOT_Tese/results/8-BUZ-67D-PKN.dat
moderno: cases/lot_tese_migrated/buz67d_pkn.yaml
objetivo: comparar estrutura temporal/camadas com cautela
```

### Nível 1 — Campos diretos ou quase diretos

Comparar:

```text
Time -> time_s, após normalização
Layer -> índice/camada, com ressalva
pressure JSON v5 psi -> Pa
```

Caso mínimo recomendado:

```text
legado : legance/LOT_APB_v5/SCORE-MRO-28_output.json
moderno: diagnóstico moderno com pressure_Pa/wall_pressure_Pa em cenário controlado
objetivo: validar conversão psi->Pa e ordem de grandeza
```

### Nível 2 — Campos com transformação

Comparar com cuidado:

```text
dP legado -> incremento/pressão moderna, separando absoluto vs incremental
dV/dV_leakoff -> campos modernos indiretos, se disponíveis
V_outflow -> métrica moderna compatível, se existir
Layer 1-based -> layer_id/gp_id/depth
```

Caso mínimo recomendado:

```text
legado : .dat com dV_leakoff/V_outflow não nulos
moderno: output LOT/PKN ou futuro artefato com leakoff/volume compatível
objetivo: comparação indireta de comportamento, não validação sigma-theta
```

### Nível 3 — Campos bloqueados

Não executar comparação automática sem instrumentação ou nova exportação:

```text
pw
sigmaTheta
margin
opened
hoop_state
```

Caso mínimo recomendado:

```text
não executar ainda
pré-requisito: export legado controlado de pw/sigmaTheta/margin/opened
```

### Nível 4 — Campos de acoplamento físico

Adiar até maturação do acoplamento:

```text
salt_displacement
creep_strain
radial_displacement
j2
von_mises
damage
tertiary creep
fracture size
```

Caso mínimo recomendado:

```text
adiar até haver acoplamento físico consolidado e contrato de amostragem de parede
```

---

## Pré-requisitos técnicos

| Comparação | Moderno exporta? | Legado exporta? | Caso equivalente existe? | Unidade compatível? | Sinal compatível? | Pré-requisito |
|---|---|---|---|---|---|---|
| `Time` | Sim | Sim | Parcial | Não confirmada | N/A | Normalizar unidade temporal. |
| `Layer` | Sim | Sim | Parcial | N/A | N/A | Mapear índice 1-based para camada/profundidade moderna. |
| `dP` | Parcial | Sim | Parcial | Pa aparente | Pressão positiva | Separar incremento de pressão absoluta. |
| `pressure JSON` | Sim, em Pa no extrator | Sim, em psi | Parcial | Sim após conversão | Pressão positiva | Usar `psi -> Pa`. |
| `dV_leakoff` | Não no writer sigma-theta | Sim | Parcial | Não confirmada | Não confirmada | Escolher output moderno compatível. |
| `V_outflow` | Não no writer sigma-theta | Sim | Parcial | Não confirmada | Não confirmada | Definir métrica moderna equivalente. |
| `pw` | Sim como `wall_pressure_Pa` | Não diretamente | Parcial | Pa | Pressão positiva | Instrumentar ou exportar `pi + dP`. |
| `sigmaTheta` | Sim | Não diretamente | Parcial | Pa | Requer sinal compressivo positivo | Instrumentar `-getSigmaTheta()`. |
| `margin` | Sim | Não diretamente | Parcial | Pa | Depende de `pw` e `sigmaTheta` | Instrumentar ou reconstruir ambos. |
| `opened` | Sim | Não diretamente | Parcial | N/A | Booleano | Exportar booleano legado ou critério completo. |
| `salt_displacement` | Não no writer sigma-theta | Sim no JSON v5 | Parcial | Não confirmada | Requer sinal | Definir ponto de amostragem e unidade. |
| `deviatoric/von Mises` | Sim | Não nos outputs | Parcial | Pa / Pa² | Requer convenção | Instrumentar tensão/invariantes no legado. |

---

## Riscos de comparação

### Falso-positivo

- `dP` legado pode parecer coerente com `wall_pressure_Pa`, mas um campo pode ser
  incremental enquanto o outro pode ser absoluto.
- `Layer` legado pode coincidir numericamente com `layer_id` moderno, mas pode
  representar outra abstração vertical.
- Pressões JSON v5 convertidas de psi para Pa podem parecer plausíveis, mas vêm
  de uma versão física diferente da cadeia sigma-theta moderna.
- `Momento da quebra` pode parecer equivalente a `first_open_time_s`, mas o
  critério legado não foi exportado ponto a ponto.

### Falso-negativo

- Time stepping diferente pode gerar divergência sem erro físico.
- Unidade temporal não normalizada pode deslocar curvas inteiras.
- Ordem de camadas diferente pode parecer erro de pressão.
- Amostra de parede moderna por ponto de Gauss pode não equivaler a
  `getElem(0)` do legado.

---

## Decisão sobre instrumentação

### Opção A — Comparação limitada com campos já exportados

Não instrumenta legado. Usa apenas `.dat` e JSON existentes extraídos pela
Fase 10.12B. É a opção recomendada para o primeiro ciclo porque preserva a base
histórica intacta e permite checar sanidade estrutural.

### Opção B — Extractor/adaptador para outputs existentes

Aprimora `tools/extract_legacy_lot_outputs.py` para campos já presentes, como
`temperature`, `density` e agregações por tempo/layer. É útil, mas não remove a
lacuna central de `pw/sigmaTheta/margin/opened`.

### Opção C — Instrumentação controlada do legado

Exportaria explicitamente:

```text
pw
sigmaTheta
margin
opened
depth_influence
thickness
```

Essa opção é necessária antes de qualquer comparação sigma-theta ponto a ponto,
mas deve ser fase separada, com autorização explícita para tocar `legance/`.

### Opção D — Comparação manual com dados da tese

Usa tabelas, figuras e resultados consolidados quando disponíveis. Pode ajudar
na interpretação, mas não substitui rastreabilidade numérica.

### Recomendação

Sequência recomendada:

```text
1. Começar com comparação limitada e indireta usando outputs existentes.
2. Aprimorar o extrator apenas para campos já presentes, se necessário.
3. Definir o menor escopo possível de instrumentação futura para
   pw/sigmaTheta/margin/opened.
4. Só depois executar comparação sigma-theta ponto a ponto.
```

O próximo passo de implementação deve ser uma fase limitada a comparação Nível
0/Nível 1, sem instrumentar legado e sem declarar validação física.

---

## Comparação Nível 0 com fixtures (Fase 10.14A)

**Status:** implementada como teste Python com fixtures temporarios.

A Fase 10.14A materializa o primeiro contrato executavel da estrategia, mas
continua restrita a sanidade estrutural. Ela nao processa os arquivos reais
grandes em `legance/LOT_Tese/results/`, nao escreve em `results/` e nao tenta
validar comportamento fisico.

A comparacao Nível 0 verifica apenas compatibilidade estrutural minima entre
saidas legadas e modernas. Esta etapa nao valida equivalencia fisica, nao
compara campos tensoriais e nao estabelece correlacao quantitativa entre
pressao, abertura de fratura, dano, ruptura ou estado tensional.

O teste `tests/python/test_compare_legacy_modern_level0.py` cria, em diretorio
temporario, quatro artefatos minimos:

```text
legacy_points.csv
legacy_summary.csv
modern_points.csv
modern_summary.csv
```

Esses fixtures representam apenas o formato intermediario ja planejado pela
Fase 10.12B e pelo writer sigma-theta moderno. O objetivo e testar a logica de
comparacao antes de criar uma ferramenta real.

### Metricas estruturais cobertas

```text
legacy_n_records
legacy_n_times
legacy_time_min_raw
legacy_time_max_raw
legacy_n_layers
modern_n_points
modern_n_steps
modern_time_min_s
modern_time_max_s
modern_n_samples_per_step
```

As metricas de tempo legado sao classificadas como seguras apenas enquanto
valores brutos. Qualquer alinhamento temporal legado-moderno permanece marcado
como `requires_time_unit_normalization`. Qualquer alinhamento entre `Layer`
legado e `wall_gp_*` moderno permanece marcado como
`requires_layer_mapping`.

### Caveats obrigatorios

O resultado da comparacao Nível 0 deve carregar explicitamente:

```text
legacy time unit is minutes by author_provided_context
legacy converted duration still requires case/duration equivalence evidence
legacy Layer is 1-based and not equivalent to wall_gp_*
sigmaTheta is not exported by legacy output
pw is not exported by legacy output
margin is not exported by legacy output
opened is not exported by legacy output
comparison is structural only, not physical validation
```

### Campos bloqueados

A comparacao Nível 0 nao compara:

```text
sigmaTheta
pw
margin
opened
hoop_state como validacao fisica
j2
von Mises
dano
fratura
```

Esses campos continuam fora do escopo ate que exista instrumentacao ou contrato
de equivalencia mais forte. A proxima fase pode criar
`tools/compare_legacy_modern_level0_level1.py`, mas apenas depois de congelar
as metricas e caveats em teste.

---

## Comparação Nível 0 com recortes reais reduzidos (Fase 10.14B)

**Status:** implementada como teste Python com fixtures reais reduzidos.

**Classificacao:** `LEVEL0_REAL_REDUCED_FIXTURES_ESTABLISHED_NO_PHYSICAL_VALIDATION`.

A Fase 10.14B complementa os fixtures temporarios da Fase 10.14A com pequenos
recortes versionados de artefatos reais em:

```text
tests/fixtures/comparison/
```

Esses recortes nao executam legado, nao instrumentam `legance/`, nao versionam
diretorios completos de resultado e nao criam baseline numerico. Eles apenas
provam que a comparacao Nível 0 consegue ler amostras reais pequenas e extrair
metadados estruturais minimos.

Arquivos versionados:

```text
legacy_buz67d_sample.dat
legacy_score_mro28_sample.json
modern_buz67d_sample.csv
README.md
```

Origens:

- `legacy_buz67d_sample.dat`: recorte textual de
  `legance/LOT_Tese/results/8-BUZ-67D-PKN.dat`;
- `legacy_score_mro28_sample.json`: bloco temporal reduzido de
  `legance/LOT_APB_v5/SCORE-MRO-28_output.json`;
- `modern_buz67d_sample.csv`: cabecalho e primeiras linhas de
  `results/phase10_14b_buz67d/timeseries.csv`, gerado por
  `lot-sim run --mode lot-pkn` para o caso BUZ67D migrado.

A comparacao continua limitada a Nível 0:

- existencia de registros;
- quantidade de tempos;
- faixa de tempo bruta;
- ordem/contagem de passos;
- quantidade de camadas/amostras;
- presenca de campos esperados;
- emissao de caveats obrigatorios.

Nao ha validacao fisica nesta fase. Mesmo com dados reais reduzidos, a
comparacao nao usa `sigmaTheta`, `pw`, `margin`, `opened`, `hoop_state`, `j2`,
von Mises, dano ou fratura como equivalencia fisica. Na Fase 10.14D, a unidade
temporal legada foi resolvida documentalmente como minutos por contexto do
autor, mas `Layer` legado continua nao equivalente a `wall_gp_*`.

---

## Level 0 field mapping (Fase 10.14C)

**Status:** `LEVEL0_FIELD_MAPPING_DOCUMENTED_NO_PHYSICAL_VALIDATION`.

A Fase 10.14C cria um artefato documental versionado em:

```text
tests/fixtures/comparison/field_mapping_level0.json
```

Esse arquivo nao e uma ferramenta de comparacao fisica. Ele registra, em
formato testavel, quais campos podem ser vistos apenas como presenca estrutural
e quais permanecem bloqueados para qualquer equivalencia numerica.

### Unidade temporal legada

A investigacao em modo leitura encontrou que `APB1da::saveFile()` escreve o
bloco `Time` do `.dat` a partir de `APB1da::ttime`, enquanto `APB1da::Solve()`
incrementa `t` por `t += dt` e armazena esse valor em `ttime`. O arquivo `.dat`
nao declara a unidade fisica de `ttime`.

O fixture legado reduzido tem:

```text
Time raw: 0.0 .. 12.5
```

O fixture moderno reduzido tem:

```text
time_s: 0.0 .. 420.0
```

Embora o YAML migrado registre `total_time = 12.5 min` e `dt = 0.5 min`, o
recorte moderno cobre apenas as primeiras linhas da saida moderna, e a unidade
do `Time` legado nao foi determinada de forma auditavel nesta fase. Portanto:

```text
temporal_comparison_status: RESOLVED_MINUTES_AUTHOR_CONTEXT
legacy Time is documented as minutes by author_provided_context
time_s = Time_raw * 60.0
legacy Time must not be compared numerically against modern time_s until case
and duration equivalence are established
```

### Mapeamentos bloqueados ou presenciais

- `Time` legado -> `time_s` moderno: `BLOCKED_UNKNOWN_UNIT`,
  `structural_only`.
- `Layer` legado -> indice moderno: `BLOCKED_NON_EQUIVALENT_INDEX`,
  `presence_only`; `Layer` 1-based nao equivale a `wall_gp_*`.
- `dP` legado -> `net_pressure_Pa` moderno:
  `BLOCKED_SEMANTIC_AMBIGUITY`, `presence_only`; `dP` nao deve ser assumido
  como pressao liquida PKN moderna.
- `fracture_width_m` moderno: `NOT_EXPORTED_BY_LEGACY`,
  `modern_presence_only`.
- `sigmaTheta`, `pw`, `margin` e `opened`:
  `NOT_AVAILABLE_FOR_COMPARISON`, `comparison_allowed = none`.

Esta fase continua documental/estrutural. Ela nao valida acoplamento fisico,
nao compara tensoes, nao compara abertura/fratura, nao compara dano e nao
estabelece correlacao quantitativa entre pressao legada e campos modernos.

---

## Evidence gate Level 1 para tempo legado (Fase 10.14D)

**Status:** `LEVEL1_TIME_UNIT_RESOLVED_CASE_EQUIVALENCE_PENDING`.

A Fase 10.14D registra a unidade temporal do legado LOT_Tese a partir de
contexto fornecido pelo autor da tese:

```text
APB1da dt, ttime e o campo Time exportado em .dat estao em minutos.
```

Com isso, a conversao documental permitida passa a ser:

```text
time_s = Time_raw * 60.0
```

Essa resolucao remove apenas o bloqueio de unidade. Ela nao estabelece
equivalencia quantitativa entre o legado e o moderno. Nos fixtures reduzidos
atuais, a faixa legada `0..12.5 min` corresponde a `0..750 s`, enquanto a faixa
moderna reduzida cobre `0..420 s`. Portanto, o gate Level 1 permanece fechado:

```text
level1_ready = false
physical_validation = false
numeric_equivalence = false
```

O par `8-BUZ-67D-PKN.dat` e `buz67d_pkn.yaml` deve ser tratado como
`SIMILAR_CASE`, nao como `SAME_CASE`, ate que haja evidencia adicional de
equivalencia de caso, duracao e amostragem.

A Fase 10.14D cria `docs/15_field_normalization.md` e
`tests/fixtures/comparison/level1_readiness_gate.json` para manter essa decisao
testavel. Permanecem bloqueados para comparacao Level 1:

```text
sigmaTheta
pw
margin
opened
hoop_state como validacao fisica
j2
von Mises
dano
fratura fisica
dP legado -> net_pressure_Pa moderno
Layer legado -> wall_gp_* moderno
```

Assim, o proximo passo permitido e testar ou automatizar a conversao de unidade
temporal, mantendo suspensa qualquer comparacao numerica fisica.

---

## Caso moderno controlado legacy-aligned (Fase 10.14EF)

**Status:** `LEVEL1_CONTROLLED_EQUIVALENT_CASE_CREATED_RUN_PENDING`.

A Fase 10.14EF executa duas etapas sem modificar o legado:

```text
Etapa E: extracao read-only de parametros do main legado BUZ67D/PKN.
Etapa F: criacao de um YAML moderno controlado em cases/validation/.
```

Fontes principais inspecionadas:

```text
legance/LOT_Tese/results/8-BUZ-67D-PKN.dat
legance/LOT_Tese/results/8-BUZ-67D-PKN-INC_DT_FULL.dat
tests/fixtures/comparison/legacy_buz67d_sample.dat
legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp
legance/LOT_Tese/include/apb_code/APB1da.h
legance/LOT_Tese/src/apb_code/APB1da.cpp
legance/LOT_Tese/include/apb_code/Fluids.h
legance/LOT_Tese/src/apb_code/Fluids.cpp
legance/LOT_Tese/include/apb_code/Rock.h
```

Artefatos criados:

```text
tests/fixtures/comparison/buz67d_legacy_parameters.json
cases/validation/buz67d_pkn_legacy_aligned.yaml
tests/python/test_legacy_aligned_case.py
```

Classificacao final:

```text
CONTROLLED_EQUIVALENT
```

Essa classificacao significa que parametros essenciais de entrada foram
extraidos diretamente do main legado hard-coded:

| Grupo | Exemplos extraidos |
|---|---|
| Temporal | `dt = 0.5 min`, `tend = 12.5 min`, `t_no_injection = 9.5 min` |
| Injecao | `Q = 0.5`, `idQ = 6`, comentario legado `0.5 bpm` |
| Geometria | `profTeste = 4374 m`, casing `12.376/14 in`, open hole `13.5 in` |
| Fluido | `density = 11.5 ppg`, `alpha = 8E-4`, `kt = 6.40E-10 Pa^-1`, `viscosity = 3 cP` |
| Rocha/sal | halita ativa, `E = 20.4E9 Pa`, `nu = 0.36`, `sg = 2200`, `sig0 = 9.92E6 Pa` |
| PKN | `setLeakoffProps("pa_min", 3., "pkn")` |

Contagens registradas no JSON:

```text
n_extracted = 29
n_inferred = 1
n_not_found = 4
n_not_applicable = 1
```

O novo YAML usa a duracao controlada:

```text
lot.injection.schedule.total_time = 12.5 min
time.total_h = 0.2083333333
equivalente a 750 s
```

O YAML validou com `lot-sim validate`, mas a fase nao executa `lot-sim run`
nesse caso. Portanto, o Level 1 segue fechado:

```text
level1_ready = false
physical_validation = false
numeric_equivalence = false
```

Continuam bloqueadas comparacoes de `sigmaTheta`, `pw`, `margin`, `opened`,
`hoop_state`, `j2`, von Mises, dano, fratura e equivalencia `dP` legado ->
`net_pressure_Pa` moderno.

---

## Diagnostico temporal/estrutural Level 1 (Fase 10.15A)

**Status:** `LEVEL1_STRUCTURAL_DIAGNOSTIC_COMPLETE`.

A Fase 10.15A executa o caso controlado legacy-aligned e gera um diagnostico
visual em `results/`, sem versionar os artefatos gerados:

```text
results/comparison/level1_buz67d/
```

Comandos principais:

```powershell
.\build\Debug\lot-sim.exe run --case cases\validation\buz67d_pkn_legacy_aligned.yaml --mode lot-pkn --output results\comparison\level1_buz67d\modern
python tools\extract_legacy_lot_outputs.py --input legance\LOT_Tese\results\8-BUZ-67D-PKN.dat --output-dir results\comparison\level1_buz67d\legacy
python tools\compare_level1.py --legacy-csv results\comparison\level1_buz67d\legacy\legacy_points.csv --modern-csv results\comparison\level1_buz67d\modern\timeseries.csv --output-dir results\comparison\level1_buz67d --legacy-time-unit min
```

Resumo estrutural observado:

| Metrica | Legado | Moderno | Status |
|---|---:|---:|---|
| `n_records` | 5460 | 26 | diagnostico apenas |
| `time_min_s` | 0 | 0 | unidade convertida |
| `time_max_s` | 750 | 750 | unidade convertida |
| `n_time_steps` | 26 | 26 | estrutural |
| `dt_s_mean` | 30 | 30 | estrutural |

Graficos gerados:

```text
time_coverage.png
record_count.png
pressure_range_diagnostic.png
fields_availability.png
```

O grafico de pressao usa rotulos diagnosticos:

```text
legacy dP — semantic unconfirmed
modern net_pressure_Pa
```

e o titulo:

```text
Level 1 Diagnostic — Pressure Range — DIAGNOSTIC ONLY — NOT PHYSICAL VALIDATION
```

O Level 1 permanece fechado para validacao fisica:

```text
level1_ready = false
physical_validation = false
numeric_equivalence = false
awaiting_human_review = true
```

A proxima decisao deve ser uma revisao humana dos graficos antes de planejar
Level 2 ou investigar divergencias.

---

## Diagnostico visual com execucao legada auditada (Fase 10.15B)

**Status:** `LEVEL1B_LEGACY_AUDIT_VISUAL_DIAGNOSTIC_COMPLETE`.

A Fase 10.15B executa uma instrumentacao temporaria e nao comitavel em
`legance/LOT_Tese/` para exportar valores ja calculados pelo legado. Toda
linha adicionada na instrumentacao contem o marcador:

```cpp
// AUDIT: Phase 10.15B
```

A instrumentacao nao altera equacoes, parametros fisicos, conversoes de
unidade, convencoes de sinal, `dt`, tempo total, vazao, geometria ou criterios
de parada. O patch usado na execucao fica registrado em:

```text
results/comparison/level1_buz67d/legacy_audit/legacy_audit.patch
```

Saidas geradas:

```text
results/comparison/level1_buz67d/legacy_audit/buz67d_audit_timeseries.csv
results/comparison/level1_buz67d/legacy_audit/buz67d_audit_metadata.json
results/comparison/level1_buz67d/legacy_audit/legacy_audit_stdout.txt
results/comparison/level1_buz67d/injected_volume_vs_pressure.csv
results/comparison/level1_buz67d/injected_volume_vs_pressure.png
results/comparison/level1_buz67d/pressure_vs_time_diagnostic.png
results/comparison/level1_buz67d/annular_volume_comparison.csv
results/comparison/level1_buz67d/level1b_metadata.json
```

O grafico volume injetado x pressao usa:

```text
X legado: injected_volume_m3
Y legado: pw_Pa
X moderno: injected_volume_m3
Y moderno: net_pressure_Pa
```

Rotulos:

```text
Legacy pw_Pa — LOT_Tese audit run
Modern net_pressure_Pa — lot-sim, semantic equivalence not confirmed
```

Titulo:

```text
LOT Diagnostic — Injected Volume vs Pressure — BUZ-67D-PKN
```

Nota:

```text
DIAGNOSTIC ONLY — pw_Pa and net_pressure_Pa may differ semantically
```

O grafico pressao x tempo usa os mesmos rotulos de pressao e a nota:

```text
DIAGNOSTIC ONLY — not physical validation
```

Resumo observado:

| Metrica | Legado auditado | Moderno controlado | Status |
|---|---:|---:|---|
| Linhas brutas | 900 | 26 | diagnostico apenas |
| Tempos agregados | 45 | 26 | diagnostico apenas |
| Faixa temporal | `0..1320 s` | `0..750 s` | nao equivalente |
| Pressao | `pw_Pa` | `net_pressure_Pa` | sem equivalencia semantica |
| Volume inicial anular | derivado da geometria legada | exportado a partir da Fase 10.16 | diagnostico apenas |

O legado auditado vai ate `1320 s` porque o caso hard-coded inclui a fase sem
injecao (`t_no_injection = 9.5 min`). O caso moderno controlado permanece no
horizonte de injecao `0..750 s`.

Na Fase 10.15B, antes da correcao de geometria da Fase 10.16, o arquivo
`annular_volume_comparison.csv` registrava:

```text
annular_volume_comparison_status = BLOCKED_MISSING_VOLUME
```

porque o moderno `result.json` nao exporta `initial_annular_volume_m3`. O
grafico `annular_volume_comparison.png` e omitido ate que esse campo exista ou
ate que uma regra de derivacao moderna seja formalizada.

Esta fase nao declara validacao fisica, equivalencia numerica ou equivalencia
semantica entre `pw_Pa` e `net_pressure_Pa`. Tambem nao compara `sigmaTheta`,
`margin`, `opened`, `hoop_state`, dano, ruptura ou tensores. O gate permanece:

```text
level1_ready = false
physical_validation = false
numeric_equivalence = false
pressure_semantic_equivalence = false
awaiting_human_review = true
```

---

## Volume anular com drill pipe no caso controlado BUZ67D (Fase 10.16)

**Status:** `DRILLPIPE_ANNULAR_VOLUME_DIAGNOSTIC_EXPORTED`.

A Fase 10.16 resolve uma lacuna geometrica diagnostica: o legado calcula o
volume anular por radiano descontando o raio externo do solido imediatamente
interno ao anular. Para o BUZ67D PKN esse solido e o drill pipe:

```text
di = 4.67 in
de = 5.5 in
```

No legado, `Solids::getRi_m()` e `Solids::getRe_m()` confirmam que esses
valores sao diametros em polegadas convertidos para raios em metros. A
convencao encontrada em `Layers.cpp` e:

```text
V_rad = 0.5 * (R_outer^2 - R_inner^2) * L
V_total = 2*pi*V_rad
```

O caso controlado `cases/validation/buz67d_pkn_legacy_aligned.yaml` agora
declara `wellbore.drill_pipe`. O resultado moderno `result.json` exporta:

```text
initial_annular_volume_per_radian_m3
initial_annular_volume_m3
annular_outer_radius_m
annular_inner_radius_m
annular_length_m
annular_volume_convention
annular_volume_source
```

Para a geometria moderna controlada atual (`R_outer = 0.1571752 m`,
`R_inner = 0.06985 m`, `L = 18 m`), o diagnostico moderno muda de:

```text
sem drill pipe: 0.22233639145536 m3/rad; 1.39698074804365 m3 total
com drill pipe: 0.17842518895536 m3/rad; 1.12107852567506 m3 total
```

O comparador Level 1B passa a registrar `volume_per_radian_m3` e
`volume_total_m3` em `annular_volume_comparison.csv`, e pode gerar:

```text
injected_volume_vs_pressure_with_drillpipe.png
pressure_vs_time_with_drillpipe.png
annular_volume_comparison.png
```

Essa etapa continua diagnostica. O `PknModel` nao usa volume anular para
alterar `net_pressure_Pa`, e `pw_Pa` legado continua sem equivalencia semantica
declarada com `net_pressure_Pa` moderno. Portanto, a comparacao segue sem
validar pressao, abertura de fratura, dano, ruptura ou estado tensional.

---

## Fase 10.17B — pressão de balanço volumétrico moderna opt-in

**Status:** `OPTIONAL_BALANCE_MODE_AVAILABLE`.

A Fase 10.17B implementa o modo:

```text
lot.pressure_model.type = volumetric_balance
```

apenas como rota opt-in. O default permanece:

```text
lot.pressure_model.type = pkn_direct
```

A comparação futura deve tratar os campos assim:

| Campo moderno | Uso permitido |
|---|---|
| `net_pressure_Pa` | Pressão líquida PKN direta; não equivale a `pw_Pa`. |
| `wellbore_pressure_Pa` | Diagnóstico de balanço volumétrico opt-in. |
| `balance_delta_pressure_Pa` | Incremento calculado por `dV_effective/(C*V)`. |
| `balance_effective_volume_increment_m3` | Incremento volumétrico após descontos de fratura/leakoff quando aplicáveis. |
| `pressure_model` | Rótulo obrigatório para impedir mistura semântica. |

Esse modo permite gerar curvas modernas alternativas para o caso controlado
BUZ67D, mas ainda não transforma Level 1 em validação física. A equivalência
com `pw = pi + dP` segue pendente de revisão humana, normalização de pressão
inicial e entendimento do termo pós-fratura legado.

## Fase 10.18A — diagnóstico visual do modo `volumetric_balance`

**Status:** `PHASE10_18A_VOLUMETRIC_BALANCE_DIAGNOSTIC_COMPLETE`.

A Fase 10.18A executa uma comparação visual diagnóstica entre:

- legado auditado: `pw_Pa` e `injected_volume_m3` de
  `results/comparison/level1_buz67d/legacy_audit/buz67d_audit_timeseries.csv`;
- moderno `pkn_direct`: `net_pressure_Pa` em saída temporária sob `results/`;
- moderno `volumetric_balance`: `wellbore_pressure_Pa` em saída temporária sob
  `results/`.

A ferramenta:

```text
tools/compare_phase10_18a.py
```

gera, sem versionar artefatos de `results/`:

```text
phase10_18a_summary.csv
phase10_18a_metadata.json
injected_volume_vs_pressure_volumetric.png
pressure_vs_time_volumetric.png
volume_balance_components.png
```

Resultado observado no caso controlado BUZ67D:

| Métrica | Legado auditado | Moderno `pkn_direct` | Moderno `volumetric_balance` |
|---|---:|---:|---:|
| Campo de pressão | `pw_Pa` | `net_pressure_Pa` | `wellbore_pressure_Pa` |
| Máxima pressão | `6.9035836e7 Pa` | `3.0847520e7 Pa` | `5.5397022e7 Pa` |
| Diferença relativa no máximo contra legado | — | `0.553` | `0.198` |
| Registros | `900` | `26` | `26` |
| Faixa temporal | `0..1320 s` | `0..750 s` | `0..750 s` |

Classificação diagnóstica:

```text
VOLUMETRIC_BALANCE_CLOSER_TO_LEGACY
```

Essa classificação significa apenas que, neste recorte controlado, a ordem de
grandeza da curva de pressão por balanço volumétrico ficou mais próxima de
`pw_Pa` legado do que `net_pressure_Pa`. Ela não valida fratura, dano, ruptura,
`sigmaTheta`, `margin`, `opened` ou equivalência física. A diferença remanescente
continua compatível com a ausência de shut-in moderno, semântica distinta entre
`pw` e pressões modernas, compressibilidade constante, ausência de Zamora e
ausência de acomodação mecânica/casing.

O gate permanece fechado:

```text
level1_ready = false
physical_validation = false
numeric_equivalence = false
pressure_semantic_equivalence = false
awaiting_human_review = true
```

## Fase 10.18B — pressão inicial e ciclo completo com shut-in

**Status:** `PHASE10_18B_INITIAL_PRESSURE_AND_SHUTIN_DIAGNOSTIC_COMPLETE`.

A Fase 10.18B auditou dois pontos independentes:

| Gate | Resultado |
|---|---|
| Pressão inicial/preexistente | `PRE_EXISTING_PRESSURE_CONFIRMED_IMPLEMENTATION_ALLOWED` |
| Schedule com shut-in | `SHUTIN_CONFIRMED_IMPLEMENTATION_ALLOWED` |

E implementou, de forma opt-in:

- `lot.initial_pressure`;
- `lot.injection.schedule.phases`;
- fase `injection` com `Q > 0`;
- fase `shutin` com `Q = 0`;
- extensão do caso controlado BUZ67D para `0..1320 s`.

O diagnóstico gera em `results/comparison/phase10_18b/`, sem versionar:

```text
phase10_18b_summary.csv
phase10_18b_metadata.json
pressure_vs_time_full_cycle.png
injected_volume_vs_pressure_full_cycle.png
injection_rate_vs_time.png
pressure_comparison_all_modes.png
```

Resultado observado:

| Métrica | Legado auditado | Moderno 10.18A | Moderno 10.18B |
|---|---:|---:|---:|
| Campo | `pw_Pa` | `wellbore_pressure_Pa` | `wellbore_pressure_Pa` |
| Tempo | `0..1320 s` | `0..750 s` | `0..1320 s` |
| Pressão inicial | `26.732215 MPa` | `0 MPa` | `26.732215 MPa` |
| Máxima pressão | `69.035836 MPa` | `55.397022 MPa` | `82.129237 MPa` |
| Diferença relativa no máximo | — | `0.198` | `0.190` |

Classificação:

```text
PRE_EXISTING_PRESSURE_FIX_PARTIAL_OTHER_FACTORS_REMAIN
```

A comparação melhorou ligeiramente a diferença absoluta de máxima pressão, mas
passou a superestimar a curva legada. A pressão inicial é, portanto, parte do
contrato legado `pw = pi + dP`, mas não explica sozinha a diferença. O resultado
continua diagnóstico e não valida equivalência física, fratura, dano, ruptura,
`sigmaTheta`, `margin` ou `opened`.

## Fase 10.17C — planejamento antes de novos mecanismos

A próxima evolução não deve avançar diretamente para validação física. A Fase
10.17C registra em `docs/16_future_features.md` os contratos futuros de:

- agenda operacional com acomodação;
- shut-in/no-injection com volume injetado constante;
- modelo de fluido Zamora moderno em `fluids/`.

Esses itens permanecem planejados. Nenhum deles altera o comparador Level 1,
o `PknModel`, o parser runtime ou os casos padrão nesta fase.

---

## Fase 10.17A — gate para balanço volumétrico opcional

**Status:** `IMPLEMENTATION_ALLOWED_OPTIONAL_BALANCE_MODE`.

A auditoria 10.17A registra que a divergência mais importante para comparação
de pressão LOT_Tese versus moderno é estrutural:

```text
LOT_Tese:
  pw = pi + dP
  dP vem de balanço Vq, Vi, k, dV e dV_leakoff

Moderno atual:
  net_pressure_Pa = E' * w / h
  sem uso de Vi ou k no cálculo da pressão PKN
```

O artefato:

```text
tests/fixtures/comparison/phase10_17_balance_audit.json
```

classifica `annular_volume`, `compressibility` e `wellbore_pressure` como
lacunas do modelo moderno direto para fins de comparação de pressão. O gate
permite implementar uma rota opcional `volumetric_balance`, mas não permite:

- mudar o default `pkn_direct`;
- comparar `pw_Pa` com `net_pressure_Pa` como equivalentes;
- declarar validação física de fratura;
- promover Level 1 para equivalência quantitativa.
