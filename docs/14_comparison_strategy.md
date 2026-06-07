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
legacy time unit is unknown
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

A Fase 10.14B complementa os fixtures temporarios da Fase 10.14A com um par
pequeno e versionado em:

```text
tests/fixtures/legacy_modern_level0/buz67d_reduced/
```

O fixture legado e um recorte de linhas ja extraidas de
`legance/LOT_Tese/results/8-BUZ-67D-PKN.dat`. O fixture moderno e um recorte
reduzido de uma saida moderna `lot-sim run --mode lot-pkn` para o caso BUZ67D
migrado. Ambos sao pequenos e servem apenas para validar o contrato estrutural.

Arquivos versionados:

```text
legacy_points.csv
legacy_summary.csv
modern_points.csv
modern_summary.csv
```

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
von Mises, dano ou fratura como equivalencia fisica. A unidade temporal legada
continua desconhecida e `Layer` legado continua nao equivalente a `wall_gp_*`.
