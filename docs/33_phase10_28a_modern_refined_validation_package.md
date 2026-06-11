# Phase 10.28A modern-refined validation package

## Resumo executivo

A Fase 10.28A planeja o pacote de validação `modern-refined` para casos ou
poços adicionais. Se dados completos adicionais não estiverem disponíveis, a
fase define uma matriz formal de sensibilidade baseada no BUZ-67D, sem
reclassificar divergências como erro e sem misturar a trilha
`legacy-equivalence`.

Status:

```text
PHASE=10.28A
MODE=MODERN_REFINED_VALIDATION_PACKAGE
LEGACY_EQUIVALENCE=SEPARATE_TRACK
BASE_CASE=BUZ67D_MODERN_REFINED
NEXT_GATE=ADDITIONAL_WELLS_OR_SENSITIVITY_MATRIX
PROTECTED_SCOPE_UNCHANGED=true
```

## Estado herdado das Fases 10.27B e 10.27C

A Fase 10.27B consolidou o BUZ-67D como pacote `modern-refined`: a escala de
pressão e o `sink_delay_s = 30 s` ficaram documentados como bons indicadores
diagnósticos, enquanto a abertura moderna em `660 s` permanece uma diferença
documentada, não erro automático.

A Fase 10.27C registrou o roadmap pós-10.27 e recomendou continuar pela rota
`modern-refined` antes de implementar solver APBSalt1D equivalente ou runtime
real de `SaltWallStressDiagnostics`.

## Separação entre modern-refined e legacy-equivalence

`modern-refined validation` avalia a rota moderna documentada, com domínio,
malha, amostragem e fonte `sigmaTheta` próprios. Ela não exige que a abertura
ocorra em `510 s` apenas porque esse é o instante do `LOT_Tese`.

`legacy-equivalence` é uma trilha separada. Ela só pode exigir regressão estrita
contra o `LOT_Tese` quando geometria APBSalt1D, malha radial, razão de malha,
ordem de integração e ponto de amostragem `legacy_elem0_sig_2_0` forem
consumidos de forma real.

## Critérios para aceitar novos casos ou poços

Um caso adicional só deve entrar no pacote `modern-refined` se houver:

- YAML moderno validável sem alterar casos protegidos;
- parâmetros de fluido, geometria e schedule rastreáveis;
- pressão inicial e unidades temporais documentadas;
- definição explícita do modo de pressão e compliance;
- fonte `sigmaTheta` diagnóstica ou caveat indicando ausência;
- saída moderna `timeseries.csv` e `result.json` geradas por `lot-sim`;
- caveat explícito de que a comparação não é regressão legacy-equivalence.

## Dados mínimos necessários

| Categoria | Dados mínimos | Obrigatório? | Observação |
|---|---|---:|---|
| temporal | tempo inicial, passo, duração de injeção e shut-in | sim | necessário para comparar cobertura |
| pressão | pressão inicial, pressão máxima e trajetória moderna | sim | sem equivalência automática com `pw` legado |
| fluido | densidade ou ppg, compressibilidade e unidade | sim | converter/registrar em SI |
| geometria | profundidade, anular, drill pipe e volumes | sim | requisito para rastreabilidade |
| compliance | modelo usado e parâmetros | sim | `constant_geometric` permanece diagnóstico |
| sink | política de sink e atraso observado | sim | `next_step` deve ser rastreável |
| sigmaTheta | fonte e amostragem | desejável | se ausente, registrar blocker |
| legado | dados de referência auditados | opcional | não usar para regressão estrita sem equivalência |

## Matriz de sensibilidade recomendada

Se não houver novos dados completos, a próxima rota deve ser uma matriz de
sensibilidade BUZ-67D `modern-refined`:

| Eixo | Variação recomendada | Objetivo | Caveat |
|---|---|---|---|
| domínio radial | atual, maior, menor | medir impacto em `sigmaTheta` moderno | não equivale automaticamente ao APBSalt1D |
| malha radial | atual, refinada, coarser | avaliar estabilidade numérica | não usar para forçar `510 s` |
| sampling | menor raio, amostra interna alternativa, média local | testar robustez de `sigmaTheta` | requer fonte espacial real |
| compliance | baseline `constant_geometric`, variações controladas | medir escala de pressão | diagnóstico, não calibração automática |
| sink | `next_step` preservado | confirmar atraso de sink | não valida fratura física |
| pressão | before/trial/after somente após gate geométrico | evitar correção prematura | bloqueado para legacy-equivalence |

## Métricas de comparação

As métricas recomendadas são:

- pressão máxima moderna;
- erro relativo de pressão máxima contra referência auditada, quando houver;
- pressão no instante de abertura moderna;
- tempo de abertura moderno;
- `opening_time_error_s` apenas como diferença diagnóstica;
- `sink_delay_s`;
- cobertura temporal;
- disponibilidade de `sigmaTheta`;
- status de geometria/sampling;
- caveats ativos.

## Critérios de não classificação automática como erro

Uma diferença temporal ou numérica não deve ser classificada automaticamente
como erro quando:

- o caso usa `modern-refined mode`, não `legacy-equivalence`;
- a geometria APBSalt1D não é consumida;
- `legacy_elem0_sig_2_0` não está disponível;
- a fonte `sigmaTheta` é série temporal diagnóstica;
- `pressure_source/timing` permanece bloqueado por geometria;
- o objetivo declarado é análise moderna documentada, não regressão estrita.

## Próximos gates

```text
ADDITIONAL_WELLS_OR_SENSITIVITY_MATRIX
MODERN_REFINED_ADDITIONAL_CASE_DATA_REQUIRED
MODERN_REFINED_SENSITIVITY_MATRIX_READY
LEGACY_EQUIVALENCE_REMAINS_SEPARATE_TRACK
PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY
```

## Próximo passo recomendado

Se houver dados completos de outro poço/caso, a próxima fase deve criar um
pacote `modern-refined` adicional com o mesmo contrato do BUZ-67D. Se não
houver, a próxima fase deve executar a matriz de sensibilidade BUZ-67D definida
neste documento.
