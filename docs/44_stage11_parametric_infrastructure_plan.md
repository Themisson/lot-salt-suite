# 44 — Stage 11 parametric infrastructure plan

## Resumo executivo

A Etapa 11 começa após o fechamento formal da Etapa 10. O objetivo é transformar o pacote BUZ-67D `modern-refined` em uma infraestrutura de estudos paramétricos mais reutilizável, rastreável e menos dependente de prompts longos.

Esta etapa não altera solver, não implementa sigmaTheta runtime real e não cria calibração física automática. A primeira implementação recomendada é um índice canônico multi-estudo para matrizes de sensibilidade.

## Motivação

A Etapa 10 provou que a matriz BUZ-67D `modern-refined` pode ser versionada, executada, sumarizada e empacotada. Ainda assim, o fluxo depende de conhecer caminhos específicos de matriz, runner e relatório.

A Etapa 11 deve tornar os estudos descobríveis e componíveis:

- matrizes YAML reutilizáveis;
- execução reproduzível;
- relatórios consolidados;
- comparação controlada de cenários;
- provenance de parâmetros;
- redução de dependência de prompts extensos.

## Entregas herdadas da Etapa 10

| Artefato | Papel |
|---|---|
| `cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml` | matriz versionada BUZ-67D |
| `tools/run_lot_pkn_sensitivity_matrix.py` | runner genérico LOT/PKN |
| `tools/report_lot_pkn_sensitivity_matrix.py` | reporter JSON/Markdown |
| `tools/run_buz67d_modern_refined_package.py` | pacote reproduzível BUZ-67D |
| `docs/43_phase10_closure_and_stage11_handoff.md` | handoff formal |

## Escopo da Etapa 11

A Etapa 11 prioriza:

- infraestrutura de estudos paramétricos;
- índices de estudos;
- matrizes reutilizáveis;
- execução e relatório multi-estudo;
- comparação controlada entre cenários;
- rastreamento de parâmetros e caveats.

## Fora de escopo

Ficam fora do escopo inicial:

- solver radial APBSalt1D;
- sigmaTheta runtime real;
- `SaltCreepTimeBridge`;
- novos modelos constitutivos;
- calibração física automática;
- promoção de `C_geom = 0.75x` a parâmetro calibrado;
- `pressure_tabulated_geometric`.

## Arquitetura proposta

```text
studies_index.yaml
  -> matrix YAML
    -> runner LOT/PKN
      -> summary.csv + metadata.json
        -> reporter JSON/Markdown
          -> pacote reproduzível ou relatório multi-estudo
```

O índice de estudos deve ser o primeiro ponto de descoberta. O runner existente continua aceitando matriz direta; ferramentas futuras podem resolver `study_id` para uma matriz versionada.

## Fases planejadas

| Fase | Objetivo | Entrada | Saída | Gate | Risco |
|---|---|---|---|---|---|
| 11.1B | matriz/runner canônico multi-estudo | matriz BUZ-67D existente | `studies_index.yaml` e ferramenta de listagem | matriz existente válida | índice virar lista hardcoded sem validação |
| 11.2A | schema de matriz paramétrica mais expressivo | matriz atual | proposta/validação de schema | sem mudar solver | schema crescer antes dos casos reais |
| 11.2B | geração automática de casos derivados | `base_case` + overrides | casos derivados controlados | Python não vira runtime obrigatório | gerar entradas de produção sem revisão |
| 11.3A | agregador multi-matriz | summaries de estudos | summary multi-estudo | rotas comparáveis declaradas | misturar rotas não equivalentes |
| 11.3B | relatório comparativo entre matrizes | agregados | JSON/Markdown comparativo | sem validação física indevida | ranking virar calibração |
| 11.4A | parâmetros rastreáveis e provenance | matriz/casos/docs | origem e caveats por parâmetro | sem dados inventados | provenance incompleta |
| 11.5A | pacote modern-refined para outros casos | dados auditados completos | pacote ou blocker documentado | caso compatível | forçar caso não-PKN |

## Critérios de aceite globais

- Nenhum caso protegido é alterado.
- Nenhum comportamento padrão do solver muda.
- `results/` permanece não versionado.
- Todo estudo declara rota, status e caveats.
- Nenhuma sensibilidade diagnóstica é promovida a validação física.
- Toda ferramenta responde a `--help` e possui teste Python.

## Riscos

- Confundir modern-refined com legacy-equivalence.
- Criar automação que esconda parâmetros físicos.
- Usar Python como pré-processador obrigatório do runtime.
- Comparar estudos com rotas ou hipóteses incompatíveis.

## Primeira implementação recomendada

```text
STAGE11_1B_MULTI_STUDY_MATRIX_INDEX
```

A próxima fase deve criar `cases/validation/sensitivity/studies_index.yaml`,
registrar a matriz BUZ-67D existente e adicionar uma ferramenta de listagem e
validação do índice.

## Fase 11.1B implementada

A Fase 11.1B adiciona o índice canônico:

```text
cases/validation/sensitivity/studies_index.yaml
```

e a ferramenta:

```text
tools/list_lot_pkn_sensitivity_studies.py
```

Status:

```text
STAGE11_1B_MULTI_STUDY_INDEX_ADDED
BUZ67D_CGEOM_SENSITIVITY_REGISTERED_AS_STUDY
```

O runner `tools/run_lot_pkn_sensitivity_matrix.py` permanece inalterado nesta
fase. A execução por `study_id` fica reservada para uma fase futura, depois que
o contrato do índice estiver estável.

## Fase 11.2A especificada

A Fase 11.2A define o contrato `schema_version: 2` para matrizes paramétricas
LOT/PKN com `base_case + overrides`, sem alterar solver nem runtime. O formato
v1 baseado em `scenario.case` permanece válido.

Artefatos:

```text
docs/46_parametric_matrix_schema.md
tools/validate_lot_pkn_parametric_matrix.py
tests/fixtures/comparison/phase11_2a_parametric_matrix_v2_fixture.yaml
```

Status:

```text
PARAMETRIC_MATRIX_SCHEMA_V2_SPECIFIED
PARAMETRIC_MATRIX_VALIDATOR_ADDED
```

## Fase 11.2B materializador

A Fase 11.2B adiciona materialização explícita de casos derivados a partir de
matrizes v2. O utilitário aplica overrides em cópias do `base_case` e grava os
YAMLs derivados em `results/` ou diretório temporário, nunca em
`cases/validation/` por padrão.

Artefatos:

```text
tools/materialize_lot_pkn_parametric_matrix.py
docs/47_parametric_case_materialization.md
```

Status:

```text
PARAMETRIC_CASE_MATERIALIZER_ADDED
```

## Fase 11.2C runner v2

A Fase 11.2C conecta o runner genérico ao materializador v2. O runner passa a
aceitar tanto matrizes v1 quanto v2, materializando cenários v2 em
`<output-dir>/materialized_cases/` antes de validar/rodar.

Status:

```text
SENSITIVITY_RUNNER_SUPPORTS_PARAMETRIC_MATRIX_V2
BUZ67D_CGEOM_SENSITIVITY_V2_REGISTERED
```

## Fase 11.3A verificação v2

A Fase 11.3A executa a matriz v2 BUZ-67D com o runner genérico e confirma que
os cenários materializados em `results/` reproduzem os diagnósticos v1
documentados para `0.75x`, baseline, `1.25x` e `same_step`.

## Fase 11.3B execução por study_id

A Fase 11.3B adiciona uma camada operacional para executar estudos registrados
no índice:

```text
tools/run_lot_pkn_sensitivity_study.py
```

Status:

```text
SENSITIVITY_STUDY_ID_EXECUTION_ADDED
BUZ67D_CGEOM_SENSITIVITY_V2_RUNNABLE_BY_STUDY_ID
```

Essa etapa melhora usabilidade sem alterar solver, schema ou casos protegidos.

## Fase 11.3C comando canônico

A Fase 11.3C cria:

```text
tools/run_lot_pkn_study.py
```

O comando único resolve `study_id`, executa a matriz por meio dos wrappers
existentes, gera relatório quando aplicável e escreve manifesto local. Ele é a
entrada preferencial para execução reproduzível de estudos LOT/PKN registrados.

## Fase 11.4A provenance de estudos

A Fase 11.4A adiciona provenance completa ao `study_manifest.json` v1,
registrando Git, ambiente Python, plataforma, executável `lot-sim`, matriz,
`base_case`, outputs, cenários e comandos de reprodução. A etapa não altera
solver, schema, C++ ou casos protegidos.

## Fase 11.4B verificador de resultados

A Fase 11.4B adiciona `tools/verify_lot_pkn_study_results.py`. O verificador
confirma integridade operacional de diretórios de estudo produzidos pelo comando
canônico: manifesto v1, outputs, resumo, metadados, relatório opcional e status
dos cenários.

## Fase 11.5A matriz C_geom ampliada

A Fase 11.5A registra e executa
`buz67d_cgeom_extended_sensitivity_v2`, uma matriz v2 ampliada de `C_geom` para
BUZ-67D `modern-refined`. O resultado é diagnóstico: `cgeom_075_next_step` foi o
melhor por abertura e score combinado, mas isso não é calibração física.

## Fase 11.5B matriz C_geom x sink_timing

A Fase 11.5B registra e executa
`buz67d_cgeom_sink_timing_sensitivity_v2`, uma matriz v2 2D que cruza quatro
fatores de `C_geom` com `same_step` e `next_step`. O estudo confirma a separação
operacional entre abertura controlada por compliance e atraso de sink controlado
por `sink_timing`, ainda como diagnóstico `modern-refined`.

## Fase 11.5C consolidação BUZ-67D

A Fase 11.5C consolida os estudos 11.5A e 11.5B em
`docs/56_buz67d_modern_refined_sensitivity_consolidation.md`. A conclusão
mantém `C_geom=0.75x` como melhor ranking diagnóstico combinado e registra que
`C_geom=0.55x` aproxima melhor a pressão máxima, reforçando que não há
calibração física automática.

## Fase 11.6A auditoria BUZ29-VISCO-first-well

A Fase 11.6A adiciona uma auditoria somente leitura para o candidato
`BUZ29-VISCO-first-well.cpp`:

```text
docs/57_buz29_visco_first_well_audit.md
tools/audit_phase11_6a_buz29_visco_first_well.py
```

Resultado:

```text
BUZ29_VISCO_FIRST_WELL_SOURCE_FOUND
BUZ29_VISCO_FIRST_WELL_NOT_PKN
BUZ29_VISCO_FIRST_WELL_MODERN_YAML_NOT_READY
```

O caso não deve ser forçado para a infraestrutura LOT/PKN porque o modelo ativo
é `penny-shaped`. A próxima fase recomendada é um roadmap não-PKN.

## Fase 11.6B roadmap não-PKN

A Fase 11.6B registra o roadmap não-PKN em:

```text
docs/58_non_pkn_model_roadmap.md
tools/plan_phase11_6b_non_pkn_models.py
```

O gate novo é:

```text
NON_PKN_MODEL_ROADMAP_RECORDED
```

O caminho prioritário recomendado é auditar a formulação `penny-shaped` antes
de qualquer tentativa de YAML moderno BUZ29. KGD/circular/elliptical e Zamora
ficam em trilhas separadas.

## Fase 11.5D maxima em summaries

A Fase 11.5D adiciona máximos opcionais ao `summary.csv` do runner genérico:

```text
max_fracture_volume_m3
max_leakoff_volume_m3
max_fracture_length_m
max_fracture_width_m
max_net_pressure_Pa
```

O gate é `SUMMARY_MAXIMA_PYTHON_ONLY_SAFE`: esses campos já existem em
`timeseries.csv`, então a mudança fica restrita a pós-processamento Python.

## Fase 11.7A decisão pós-BUZ29

A Fase 11.7A seleciona a trilha prioritária para o primeiro modelo não-PKN:

```text
PHASE11_7A_NEXT_MODEL_TRACK_DECIDED
selected_track = PENNY_SHAPED
```

A escolha segue a auditoria BUZ29-VISCO-first-well: o modelo ativo é
`penny-shaped`, enquanto a evidência PKN é apenas linha comentada ou artefato
output-only. A fase é decisória e não implementa modelo físico novo.
