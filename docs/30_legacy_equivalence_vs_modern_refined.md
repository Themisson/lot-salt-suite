# Legacy-equivalence vs modern-refined

## Resumo executivo

A Fase 10.27A consolida a decisão estratégica entre dois modos distintos de
trabalho para o diagnóstico `sigmaTheta` no LOT/PKN:

- **legacy-equivalence mode**: busca reproduzir o `LOT_Tese` como regressão
  histórica, incluindo domínio radial, malha, razão geométrica e ponto de
  amostragem do `APBSalt1D`;
- **modern-refined mode**: usa a arquitetura moderna como rota analítica
  controlada, com parâmetros documentados e sem exigir que a abertura ocorra no
  mesmo instante do legado quando domínio, malha e amostragem são diferentes.

Equivalência com o legado não é sinônimo de validação física.
Divergência em relação ao LOT_Tese pode ser aceitável quando o modo moderno usa
domínio, malha, amostragem e refinamento diferentes, desde que os parâmetros
físicos estejam documentados e a comparação não seja apresentada como regressão
legado-equivalente.

## Histórico 10.19C-10.26D

### 10.19C — compliance geométrica diagnóstica

A rota `constant_geometric` aproximou bem a escala de pressão do BUZ-67D:

```text
C_fluid = 6.4e-10 1/Pa
C_geom = 1.8571966938610005e-8 1/Pa
C_eff = 1.9211966938610006e-8 1/Pa
relative_error_max_pressure = -0.02468924338685035
classification = COMPLIANCE_EFFECTIVE
```

Essa é uma baseline diagnóstica, não uma formulação física validada.

### 10.20C — elastic annular simple

O modelo `elastic_annular_simple` ficou undercompliant:

```text
classification = ELASTIC_COMPLIANCE_UNDERCOMPLIANT
modern_first_dP_elastic_compliance_Pa = 43639672.35675542
legacy_first_dP_Pa = 1845413.7784679066
```

Logo, ele não substitui a compliance equivalente diagnóstica no BUZ-67D.

### 10.22C — trace legado unificado

O `LOT_Tese` confirmou abertura por:

```text
pw > sigmaTheta
```

com:

```text
first_opened_time_s = 510.0
first_sink_positive_time_s = 540.0
sink_delay_s = 30.0
first_pw_Pa = 66769500.0
first_sigmaTheta_Pa = 66666600.0
first_margin_Pa = 102865.0
```

### 10.23A-10.23C — sink next-step e decisão de modelo

`sink_timing: next_step` reproduziu o atraso de sink de `30 s`; a escala de
pressão ficou boa, mas a abertura moderna permaneceu deslocada. A decisão da
10.23C foi priorizar `sigmaTheta` runtime, mantendo
`pressure_tabulated_geometric` bloqueado.

### 10.25A-10.25C — sigmaTheta refinado

A série refinada de `sigmaTheta` possui `44` pontos e confirma:

```text
legacy_first_opened_time_s = 510.0
modern_fracture_initiation_time_s = 660.0
opening_time_error_s = 150.0
modern_sink_delay_s = 30.0
```

O refinamento melhorou a origem da série, mas não eliminou o deslocamento de
abertura.

### 10.26A-10.26D — gate APBSalt1D

A auditoria geométrica mostrou diferença estrutural entre legado e moderno:

| Aspecto | LOT_Tese / APBSalt1D | Moderno atual |
|---|---:|---:|
| `outer_radius_m` | `8 m` | `1.556 m` default/bridge |
| elementos radiais | `15` | `40` default/bridge |
| `ratio` | `10` | não consumido |
| `integration_order` | `3` | `3` em `AxisymL3` |
| amostragem | `getElem(0)->getSigmaTheta(); sig(2,0)` | time-series sem amostras espaciais |

As classificações atuais são:

```text
APBSALT1D_METADATA_ONLY_CONFIRMED
APBSALT1D_SAMPLING_BRIDGE_BLOCKED
PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY
```

## O que foi comprovado

- A escala de pressão do BUZ-67D pode ser aproximada com
  `constant_geometric` em rota diagnóstica.
- O legado abre em `510 s` por `pw > sigmaTheta`.
- O sink legado positivo começa no passo seguinte, com `sink_delay_s = 30 s`.
- A série refinada `sigmaTheta(t)` é mais completa do que a fixture inicial.
- A abertura moderna em `660 s` persiste mesmo com `sigmaTheta(t)` refinado.
- A geometria/malha/ponto de amostragem APBSalt1D ainda não é consumida no
  cálculo moderno.

## O que não foi comprovado

- Não foi comprovado que a abertura moderna em `660 s` é erro físico.
- Não foi comprovado que corrigir `pressure_source` ou timing reproduzirá o
  legado.
- Não foi comprovada equivalência entre `legacy_elem0_sig_2_0` e qualquer
  amostra moderna.
- Não foi validado acoplamento físico runtime com `SaltWallStressDiagnostics`.
- Não foi liberado `pressure_tabulated_geometric`.

## Definição de legacy-equivalence mode

`legacy-equivalence mode` é uma rota de regressão histórica. Ela só deve ser
usada quando o objetivo explícito for reproduzir o `LOT_Tese`. Para isso, deve
consumir de forma real:

- `outer_radius_m = 8 m`;
- `radial_elements = 15`;
- `ratio = 10`;
- `integration_order = 3`;
- ponto de amostragem compatível com `mdl->getElem(0)->getSigmaTheta(); sig(2,0)`;
- critério `pw > sigmaTheta` com rastreabilidade temporal.

Enquanto esses itens forem apenas metadata, o modo não pode ser usado para
alegar equivalência numérica.

## Definição de modern-refined mode

`modern-refined mode` é uma rota moderna de análise. Ela pode usar malha,
domínio, amostragem e fontes de tensão mais adequadas ao desenho moderno, desde
que:

- a comparação não seja chamada de regressão legado-equivalente;
- os parâmetros físicos e geométricos estejam documentados;
- divergências como abertura em `660 s` sejam relatadas como consequência
  possível de diferenças de modelo, não automaticamente como erro;
- a validação física seja feita por critérios próprios, não apenas por casar com
  o legado.

## Quando usar cada modo

Use `legacy-equivalence mode` quando:

- a meta for regressão estrita contra o `LOT_Tese`;
- for necessário explicar linha a linha por que o moderno abre em `510 s`;
- a comparação depender do ponto legado `elem0/sig(2,0)`;
- o relatório for apresentado como equivalência histórica.

Use `modern-refined mode` quando:

- a meta for análise física moderna;
- a malha moderna refinada for intencional;
- o domínio ou ponto de amostragem moderno diferir do legado;
- o objetivo for evoluir para `SaltWallStressDiagnostics` runtime opt-in.

## Por que 660 s não é automaticamente erro

A abertura moderna em `660 s` difere dos `510 s` do legado. Porém, o caminho
moderno atual não usa o mesmo domínio radial, a mesma malha, a mesma razão
geométrica nem o mesmo ponto `sigmaTheta` do `APBSalt1D`. Portanto, o erro de
tempo não pode ser tratado automaticamente como erro de `pressure_source`,
timing ou solver.

O valor `660 s` é incorreto apenas se a execução for apresentada como
`legacy-equivalence mode`. Em `modern-refined mode`, ele é uma observação
diagnóstica a ser validada por contratos modernos.

## Quando exigir abertura em 510 s

Exija abertura em `510 s` somente quando:

- o objetivo declarado for regressão estrita do `LOT_Tese`;
- a geometria APBSalt1D for consumida, não apenas declarada;
- o sampling `legacy_elem0_sig_2_0` tiver equivalente implementado;
- a fonte de `sigmaTheta` e o tempo de consulta estiverem rastreados.

## Gates contra comparações indevidas

```text
LEGACY_EQUIVALENCE_REQUIRES_MESH_MATCHING
APBSALT1D_METADATA_ONLY_CONFIRMED
APBSALT1D_SAMPLING_BRIDGE_BLOCKED
PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY
LEGACY_EQUIVALENCE_VS_MODERN_REFINED_DECISION_RECORDED
```

Esses gates impedem que o moderno seja ajustado para casar com o legado sem
declarar qual modo está sendo usado.

## Matriz de decisão

| Aspecto | Legacy-equivalence mode | Modern-refined mode | Gate |
|---|---|---|---|
| domínio radial | `outer_radius_m = 8 m` | default/bridge `1.556 m` | `LEGACY_EQUIVALENCE_REQUIRES_MESH_MATCHING` |
| malha radial | `15` elementos | `40` elementos default | `LEGACY_EQUIVALENCE_REQUIRES_MESH_MATCHING` |
| razão de malha | `ratio = 10` | não consumido | `APBSALT1D_METADATA_ONLY_CONFIRMED` |
| integração | `3` | `3` em `AxisymL3` | parcial, não suficiente |
| sampling `sigmaTheta` | `elem0/sig(2,0)` | time-series sem amostras espaciais | `APBSALT1D_SAMPLING_BRIDGE_BLOCKED` |
| fonte `sigmaTheta` | APBSalt1D legado | refined time-series / futuro wall stress | `SIGMATHETA_RUNTIME_STILL_FUTURE_WORK` |
| pressure/timing | após equivalência geométrica | bloqueado por enquanto | `PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY` |
| compliance | regressão diagnóstica | `constant_geometric` opt-in | `CONSTANT_GEOMETRIC_REMAINS_DIAGNOSTIC_BASELINE` |
| sink | next-step confirmado | next-step diagnóstico | não valida fratura física |

## Próxima fase recomendada

A decisão padrão da Fase 10.27A é:

```text
NEXT_PHASE_MODERN_REFINED_DOCUMENTATION_AND_VALIDATION
```

Se o objetivo do usuário passar a ser regressão estrita do `LOT_Tese`, a próxima
fase deve mudar para:

```text
NEXT_PHASE_LEGACY_EQUIVALENCE_RADIAL_SOLVER
```

Se o objetivo for análise física moderna, uma alternativa técnica é:

```text
NEXT_PHASE_IMPLEMENT_SALT_WALL_STRESS_RUNTIME
```

Em todos os casos, `NEXT_PHASE_RETURN_TO_PRESSURE_SOURCE_TIMING` só deve ser
usado depois de equivalência geométrica real ou de uma decisão explícita de
abandonar a equivalência APBSalt1D.

## Pacote BUZ-67D modern-refined (Fase 10.27B)

A Fase 10.27B aplica esta matriz ao BUZ-67D e registra o pacote documental:

```text
docs/31_buz67d_modern_refined_validation.md
```

O pacote confirma:

- `modern-refined mode` não é regressão estrita;
- a pressão máxima moderna fica cerca de `-2.47%` do legado;
- o erro relativo da pressão na abertura é cerca de `0.8415%`;
- `sink_delay_s = 30 s` é preservado;
- abertura moderna em `660 s` é diferença documentada, não erro automático;
- exigir `510 s` permanece condicionado ao `legacy-equivalence mode`.

## Roadmap pós-10.27 (Fase 10.27C)

A Fase 10.27C registra o roadmap técnico em:

```text
docs/32_post_10_27_roadmap.md
```

Status:

```text
POST_10_27_ROADMAP_RECORDED
NEXT_PHASE_MODERN_REFINED_VALIDATION_OR_SENSITIVITY
```

A prioridade imediata é consolidar o `modern-refined mode` em casos adicionais
ou em estudo de sensibilidade de malha/domínio/sampling. A rota
`legacy-equivalence` permanece disponível para regressão estrita, mas deve ser
tratada como rota separada e opcional, condicionada a solver/sampler APBSalt1D
equivalente.
