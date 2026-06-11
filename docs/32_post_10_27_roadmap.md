# Post-10.27 roadmap

## Resumo executivo

A Fase 10.27C registra o roadmap técnico após a separação formal entre
`legacy-equivalence mode` e `modern-refined mode`. A recomendação imediata é
continuar pela rota `modern-refined`, consolidando validação documental e
sensibilidades antes de implementar novos solvers ou runtime de sal.

Status:

```text
POST_10_27_ROADMAP_RECORDED
NEXT_PHASE_MODERN_REFINED_VALIDATION_OR_SENSITIVITY
```

## Estado atual do projeto

O BUZ-67D já possui um pacote `modern-refined` documentado. A escala de pressão
foi considerada diagnosticamente boa com `constant_geometric`, o `sink_delay_s`
de `30 s` foi preservado com `sink_timing: next_step`, e a abertura moderna em
`660 s` foi classificada como diferença documentada, não erro automático.

A rota `legacy-equivalence` continua bloqueada para regressão estrita porque a
metadata APBSalt1D ainda não é consumida por um solver/sampler radial
equivalente. Portanto, `pressure_source/timing` permanece subordinado ao gate de
geometria.

## O que está concluído

- Comparação estrutural legado-moderno de Nível 0 com fixtures.
- Gates de prontidão temporal e parâmetros BUZ-67D controlados.
- Compliance diagnóstica `constant_geometric`.
- `sink_timing: next_step`.
- Trace legado unificado para abertura e sink.
- Provider diagnóstico `sigmaTheta(t)`.
- Metadata APBSalt1D opt-in validada.
- Decisão `legacy-equivalence` vs `modern-refined`.
- Pacote documental BUZ-67D `modern-refined`.

## O que está bloqueado

```text
APBSALT1D_SAMPLING_BRIDGE_BLOCKED
PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY
APBSALT1D_SOLVER_EQUIVALENCE_REQUIRED_FOR_STRICT_MATCH
SIGMATHETA_RUNTIME_STILL_FUTURE_WORK
```

Esses bloqueios impedem apresentar a abertura em `510 s` como requisito para o
modo moderno atual. Esse requisito só é válido para regressão estrita quando
domínio, malha, ordem de integração e ponto de amostragem forem equivalentes.

## Rotas futuras

| Fase | Rota | Objetivo | Pré-condição | Saída esperada | Status |
|---|---|---|---|---|---|
| 10.28A | modern-refined | modern-refined validation package for additional wells/cases | BUZ-67D modern-refined aceito | Pacotes diagnósticos adicionais | planned |
| 10.28B | modern-refined | modern-refined sensitivity study: mesh/domain/sampling | Ao menos um pacote modern-refined estável | Matriz de sensibilidade | planned |
| 10.28C | publication/reporting | prepare publication-grade comparison plots | Métricas e caveats congelados | Figuras e relatório revisáveis | planned |
| 10.29A | legacy-equivalence | APBSalt1D legacy-equivalence radial solver feasibility | Regressão estrita contra LOT_Tese continua necessária | Decisão de viabilidade do solver radial equivalente | planned_optional |
| 10.29B | legacy-equivalence | APBSalt1D sampling bridge design, if radial samples become available | Amostras espaciais ou solver equivalente existem | Design do sampling bridge ou blocker formal | blocked_by_spatial_samples |
| 10.30A | salt-runtime | SaltWallStressDiagnostics runtime integration plan | Decisão de priorizar fonte física moderna de sigmaTheta | Plano de integração runtime opt-in | planned |
| 10.30B | salt-runtime | SigmaThetaProvider real salt runtime prototype | Plano 10.30A aceito | Protótipo opt-in com wall stress real | planned |
| 10.31A | thermal/balance | thermal term explicit modeling audit | Rota de pressão modern-refined permanece útil | Gate de termo térmico | planned |
| 10.31B | thermal/balance | dMl/leakoff explicit balance audit | Auditoria thermal/balance continua em escopo | Gate de termos de balanço explícitos | planned |

## Próxima fase recomendada

A próxima fase recomendada é:

```text
10.28A — modern-refined validation package for additional wells/cases
```

Ela deve manter a rota moderna documentada e verificar se as conclusões do
BUZ-67D são específicas do caso ou se aparecem em outros poços/cenários. A
10.28B pode vir logo depois para estudar sensibilidade de malha, domínio e
sampling dentro do próprio modo moderno.

## Critérios para escolher entre rotas

| Critério | Rota recomendada |
|---|---|
| Validar análise moderna com parâmetros documentados | modern-refined |
| Preparar tese/artigo com caveats claros | publication/reporting |
| Obter fonte física moderna de sigmaTheta | salt-runtime |
| Reproduzir exatamente abertura `510 s` do LOT_Tese | legacy-equivalence |
| Revisar pressure_source/timing | somente após resolver ou rejeitar formalmente o gate geométrico |

## Matriz de priorização

| Prioridade | Fase | Justificativa | Risco | Benefício |
|---:|---|---|---|---|
| 1 | 10.28A / 10.28B | Consolida evidência modern-refined sem forçar equivalência legada. | Conclusões podem continuar específicas do BUZ-67D. | Fortalece validação moderna antes de novo runtime. |
| 2 | 10.28C | Transforma o pacote em figuras revisáveis. | Figuras podem ser superinterpretadas sem caveats. | Melhora comunicação técnica para tese/artigo. |
| 3 | 10.30A / 10.30B | Avança para fonte física moderna de sigmaTheta. | Runtime de sal amplia escopo arquitetural. | Reduz dependência de provider diagnóstico. |
| 4 | 10.29A / 10.29B | Necessário apenas para regressão estrita LOT_Tese. | Pode reproduzir legado sem aumentar validação física. | Isola se `510 s` é efeito de malha/domínio. |

## Riscos remanescentes

- `modern-refined mode` não é regressão estrita contra o `LOT_Tese`.
- `constant_geometric` permanece baseline diagnóstica.
- Metadata APBSalt1D continua sem consumo real sem amostras espaciais.
- `pressure_source/timing` permanece bloqueado para alegações de
  legacy-equivalence.
- `SaltWallStressDiagnostics` runtime segue como trabalho futuro.

## Checklist para continuidade em outro computador

1. Rodar `git status` e confirmar `main...origin/main` limpo.
2. Rodar `cmake -S . -B build`.
3. Rodar `cmake --build build --config Debug -j`.
4. Rodar `ctest --test-dir build -C Debug --output-on-failure`.
5. Rodar `python -m pytest tests/python/ -v`.
6. Rodar `python tools/generate_docs_index.py`.
7. Validar os três casos principais LOT-PKN.
8. Confirmar que `results/` permanece ignorado.

## Fase 10.28A registrada

A Fase 10.28A cria o pacote documental em:

```text
docs/33_phase10_28a_modern_refined_validation_package.md
```

Ela mantém a recomendação do roadmap: primeiro tentar casos/poços adicionais
com dados completos; se isso não estiver disponível, executar uma matriz de
sensibilidade `modern-refined` baseada no BUZ-67D. A trilha
`legacy-equivalence` permanece separada e condicionada ao consumo real de
geometria/sampling APBSalt1D.

## Fase 10.28B registrada

A Fase 10.28B executa o gate duplo em:

```text
docs/34_phase10_28b_additional_or_sensitivity_gate.md
```

Resultado:

```text
ADDITIONAL_WELL_BLOCKED_SENSITIVITY_SELECTED
SENSITIVITY_MATRIX_READY_FOR_10_28C
```

BUZ-29D foi localizado como material legado, mas não como caso PKN moderno
pronto. A próxima fase deve executar a matriz BUZ-67D `modern-refined` S0-S3
sem promover equivalência com o `LOT_Tese`.

## Fase 10.28C registrada

A Fase 10.28C executa a matriz de sensibilidade em:

```text
docs/35_phase10_28c_modern_refined_diagnostic.md
```

Resultado:

```text
PHASE10_28C_SENSITIVITY_MATRIX_EXECUTED
PHASE10_28C_SENSITIVITY_MATRIX_RUN_OK
```

O cenário `0.75x C_geom` aproximou a abertura de `510 s`, mas isso foi
registrado apenas como sensibilidade diagnóstica. `constant_geometric` continua
baseline diagnóstico, não calibração automática nem validação física.
