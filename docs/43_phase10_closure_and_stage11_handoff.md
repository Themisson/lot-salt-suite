# 43 — Phase 10 closure and Stage 11 handoff

## Resumo executivo

A Etapa 10 entrega um pacote BUZ-67D modern-refined reproduzível, uma matriz versionada de sensibilidade, runner genérico, reporter e documentação operacional. A Etapa 10 não entrega equivalência estrita com o LOT_Tese, não entrega sigmaTheta runtime real e não transforma fatores diagnósticos de compliance em calibração física.

O fechamento formal da Etapa 10 estabelece a transição para a Etapa 11. A próxima etapa deve reduzir dependência de prompts longos, consolidar estudos paramétricos modern-refined e tornar a descoberta de matrizes/casos mais canônica e rastreável.

## Escopo da Etapa 10

A Etapa 10 concentrou-se na comparação controlada entre o legado auditado e a rota moderna LOT/PKN, separando explicitamente dois modos:

- `legacy-equivalence mode`: reservado para regressão estrita contra o LOT_Tese.
- `modern-refined mode`: rota moderna documentada, com domínio, malha, sampling e simplificações próprios.

O escopo prático foi BUZ-67D, com auditorias de pressão, abertura, sink, compliance, sigmaTheta e pacote de sensibilidade diagnóstica.

## Entregas principais

| Entrega | Artefato | Status |
|---|---|---|
| Decisão legacy-equivalence vs modern-refined | `docs/30_legacy_equivalence_vs_modern_refined.md` | concluído |
| Validação documental BUZ-67D modern-refined | `docs/31_buz67d_modern_refined_validation.md` | concluído |
| Roadmap pós-10.27 | `docs/32_post_10_27_roadmap.md` | concluído |
| Gate BUZ-29D ou sensibilidade | `docs/34_phase10_28b_additional_or_sensitivity_gate.md` | concluído |
| Matriz BUZ-67D modern-refined | `cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml` | concluído |
| Runner genérico LOT/PKN | `tools/run_lot_pkn_sensitivity_matrix.py` | concluído |
| Reporter de sensibilidade | `tools/report_lot_pkn_sensitivity_matrix.py` | concluído |
| Pacote reproduzível BUZ-67D | `tools/run_buz67d_modern_refined_package.py` | concluído |

## Linha do tempo técnica resumida

| Bloco | Resultado |
|---|---|
| 10.19C–10.20C | `constant_geometric` funcionou como baseline diagnóstico; `elastic_annular_simple` ficou undercompliant. |
| 10.22C–10.23C | Legado confirmou `pw > sigmaTheta` e sink no passo seguinte; pressão e sink ficaram bons, abertura permaneceu deslocada. |
| 10.25A–10.26D | SigmaTheta refinado ajudou a rastrear a diferença, mas APBSalt1D ficou metadata-only por falta de amostras espaciais. |
| 10.27A–10.27C | Separação formal entre `legacy-equivalence` e `modern-refined`; roadmap posterior definido. |
| 10.28A–10.31A | Pacote modern-refined consolidado com matriz versionada, runner, reporter e execução reproduzível. |

## Status do BUZ-67D modern-refined

BUZ-67D está consolidado como caso diagnóstico modern-refined. O pacote reproduzível executa validações, matriz C_geom, resumo e relatório local em `results/`.

Resultados documentados:

- baseline `C_geom = 1.0x`: abertura em `660 s`;
- sensibilidade `C_geom = 0.75x`: abertura em `510 s`;
- `sink_timing = next_step`: atraso de sink de `30 s`;
- `C_geom = 0.75x`: melhor fator diagnóstico por abertura e score combinado.

## Status da matriz de sensibilidade

A matriz versionada `buz67d_modern_refined_cgeom_matrix.yaml` é o principal artefato paramétrico da Etapa 10. Ela é diagnóstica, reproduzível e pós-processável, mas não é calibração automática.

O fator C_geom = 0.75x permanece um resultado de sensibilidade diagnóstica. Ele não deve ser promovido automaticamente a parâmetro calibrado nem interpretado como validação física sem critérios independentes.

## Status do pacote reproduzível

O pacote 10.31A adicionou:

- `tools/run_buz67d_modern_refined_package.py`;
- `docs/42_buz67d_modern_refined_reproducible_package.md`;
- testes Python dedicados.

Saídas esperadas permanecem locais em `results/` e não devem ser versionadas.

## Status do BUZ-29D

BUZ-29D foi auditado, mas ainda não está pronto como YAML PKN moderno. Os materiais legados existem, porém a trilha PKN moderna ainda precisa de melhor proveniência de caso, modelo e parâmetros antes de virar validação additional well.

## Status legacy-equivalence vs modern-refined

`legacy-equivalence mode` continua separado. Exigir abertura em `510 s` só é tecnicamente correto quando geometria, malha, ordem de integração, sampling APBSalt1D e fonte de sigmaTheta forem equivalentes.

`modern-refined mode` pode divergir do LOT_Tese quando usa domínio, malha e sampling diferentes, desde que a divergência seja documentada e não apresentada como regressão estrita.

## Gates resolvidos

| Gate | Status |
|---|---|
| BUZ-67D modern-refined package | fechado |
| Matriz C_geom versionada | fechado |
| Runner genérico LOT/PKN | fechado |
| Reporter de sensibilidade | fechado |
| Separação legacy-equivalence vs modern-refined | fechado |

## Gates bloqueados

| Gate | Motivo |
|---|---|
| APBSalt1D sampling bridge | sem amostras espaciais para mapear `legacy_elem0_sig_2_0` |
| sigmaTheta runtime real | sem integração `SaltWallStressDiagnostics` runtime |
| pressure_tabulated_geometric | bloqueado por termos térmicos, sinais e balanço parcial |
| regressão estrita LOT_Tese | requer consumo real da geometria/sampling APBSalt1D |
| BUZ-29D modern YAML | caso ainda não está pronto como PKN moderno |

## Comandos canônicos de reprodução

```powershell
cmake -S . -B build
cmake --build build --config Debug -j
python tools/run_buz67d_modern_refined_package.py --lot-sim build/Debug/lot-sim.exe --output-dir results/comparison/buz67d_modern_refined_package
```

Execução manual da matriz:

```powershell
python tools/run_lot_pkn_sensitivity_matrix.py --matrix cases/validation/sensitivity/buz67d_modern_refined_cgeom_matrix.yaml --output-dir results/comparison/buz67d_cgeom_matrix
```

Relatório manual:

```powershell
python tools/report_lot_pkn_sensitivity_matrix.py --summary results/comparison/buz67d_cgeom_matrix/summary.csv --metadata results/comparison/buz67d_cgeom_matrix/metadata.json --output-json results/comparison/buz67d_cgeom_report.json --output-md results/comparison/buz67d_cgeom_report.md --legacy-opening-time-s 510 --legacy-max-pressure-Pa 69035836.1743195
```

## O que não deve ser interpretado como validação física

- `C_geom = 0.75x` não é calibração física.
- A abertura em `510 s` no cenário `0.75x` não prova equivalência com LOT_Tese.
- O pacote BUZ-67D modern-refined não prova sigmaTheta runtime real.
- A matriz de sensibilidade não substitui validação independente.
- O modo modern-refined não é regressão estrita contra o LOT_Tese.

## Riscos remanescentes

- Interpretação indevida de sensibilidade como calibração.
- Mistura acidental entre modern-refined e legacy-equivalence.
- Uso de artefatos locais em `results/` como se fossem baseline versionado.
- Tentativas de corrigir pressure_source/timing antes de resolver ou descartar a equivalência geométrica APBSalt1D.

## Definition of Done da Etapa 10

| Critério | Status |
|---|---|
| Pacote BUZ-67D modern-refined reproduzível | atendido |
| Matriz C_geom versionada | atendido |
| Runner e reporter documentados | atendido |
| BUZ-29D auditado | atendido |
| Bloqueios principais documentados | atendido |
| Nenhuma validação física indevida declarada | atendido |

## Recomendação de abertura da Etapa 11

A Etapa 11 deve começar por infraestrutura paramétrica modern-refined:

- índice de estudos;
- matrizes reutilizáveis;
- execução e relatório multi-estudo;
- provenance de parâmetros;
- redução de dependência de prompts longos.

Status de handoff:

```text
PHASE10_CLOSED_READY_FOR_STAGE11
STAGE11_PARAMETRIC_INFRASTRUCTURE_RECOMMENDED
```
