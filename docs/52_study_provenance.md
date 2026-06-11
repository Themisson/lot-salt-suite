# 52 - LOT/PKN study provenance

## Objetivo

A Fase 11.4A adiciona proveniencia operacional completa aos estudos LOT/PKN
executados por `tools/run_lot_pkn_study.py`.

O manifesto registra a proveniencia operacional do estudo. Ele nao substitui os
arquivos de entrada versionados nem transforma resultados diagnosticos em
validacao fisica.

## O que e provenance

Neste contexto, provenance e o conjunto de informacoes que permite reconstruir
como um estudo foi executado:

- estudo selecionado;
- indice de estudos;
- matriz de sensibilidade;
- `base_case`;
- comandos executados;
- ambiente Python e sistema operacional;
- commit, branch e estado dirty do Git;
- executavel `lot-sim`;
- artefatos produzidos;
- status dos cenarios.

## Dry-run

Em `--dry-run`, o manifesto e gerado com `study_status=dry_run`. Os caminhos de
saida sao registrados como artefatos planejados, mas `summary.csv` e relatorios
reais nao sao exigidos.

## Run completo

Em execucao completa, o manifesto registra `study_status=completed` quando o
`summary.csv` e produzido. O relatorio `sensitivity_report.json` e
`sensitivity_report.md` e registrado quando a etapa de report nao e omitida.

## Arquivo de comandos

`run_commands.txt` registra:

1. comando canonico do estudo;
2. comando do wrapper por `study_id`;
3. comando do runner de matriz;
4. comando do reporter;
5. comando de verificacao futura da Fase 11.4B.

## Limites

Provenance melhora reproducibilidade operacional, mas nao muda a natureza dos
resultados. Estudos `modern-refined` continuam diagnosticos ate que gates
fisicos independentes sejam definidos.

## Verificador

A Fase 11.4B conecta a proveniência ao verificador
`tools/verify_lot_pkn_study_results.py`. Ele confirma integridade operacional do
diretório de resultados e pode gerar relatório JSON/Markdown local.

## Uso em estudos ampliados

A Fase 11.5A usa o mesmo manifesto v1 para registrar o estudo
`buz67d_cgeom_extended_sensitivity_v2`. Os artefatos permanecem locais em
`results/` e não são versionados.

A Fase 11.5B usa o mesmo contrato para registrar
`buz67d_cgeom_sink_timing_sensitivity_v2`, incluindo matriz, base case, cenários
materializados localmente, comandos de reprodução e verificação.
