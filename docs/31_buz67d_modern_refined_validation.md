# BUZ67D modern-refined validation package

## Resumo executivo

A Fase 10.27B consolida o BUZ-67D como diagnóstico do `modern-refined mode`.
Esse modo não é regressão estrita contra o `LOT_Tese`; ele documenta uma rota
moderna com parâmetros físicos rastreados, compliance diagnóstica,
`sink_timing: next_step` e fonte `sigmaTheta` refinada em série temporal.

O modern-refined mode não é regressão estrita contra o LOT_Tese. Ele deve ser
avaliado como rota moderna documentada, com malha/domínio/amostragem próprios. A
divergência temporal da abertura em relação ao LOT_Tese só deve ser tratada como
erro se a geometria, a malha, a ordem de integração, o sampling de sigmaTheta e
a fonte de tensão forem equivalentes.

Status:

```text
BUZ67D_MODERN_REFINED_VALIDATION_DOCUMENTED
MODERN_REFINED_NOT_LEGACY_EQUIVALENT
PRESSURE_SOURCE_TIMING_REVIEW_BLOCKED_BY_GEOMETRY
APBSALT1D_SAMPLING_BRIDGE_BLOCKED
```

## Objetivo do modern-refined mode

O objetivo é manter uma rota moderna auditável para BUZ-67D sem forçar o solver
a reproduzir uma malha e um ponto de amostragem legados ainda não consumidos.
Ela serve para:

- preservar parâmetros físicos extraídos/auditados;
- manter escala de pressão diagnóstica adequada;
- preservar `sink_delay_s = 30 s`;
- separar divergência de abertura de regressão estrita;
- preparar validação moderna futura.

## Diferença para legacy-equivalence

`legacy-equivalence mode` exige que a configuração APBSalt1D seja consumida de
fato: domínio radial, malha, `ratio`, ordem de integração e sampling
`legacy_elem0_sig_2_0`.

`modern-refined mode` aceita que o domínio, a malha e a fonte `sigmaTheta`
modernos sejam diferentes, desde que isso seja explicitamente documentado. Por
isso, abertura em `660 s` não é automaticamente erro nesse modo.

## Parâmetros físicos preservados

| Item | Valor moderno | Valor legado auditado | Status |
|---|---:|---:|---|
| pressão inicial | `26732215.17314985 Pa` | `pi` inicial auditado | preservado |
| vazão | `0.5 bbl/min` | `Q = 0.5 bpm` | preservado |
| tempo de injeção | `12.5 min` | `tend = 12.5 min` | preservado |
| tempo de shut-in | `9.5 min` | `t_no_injection = 9.5 min` | preservado |
| fluido | `11.5 ppg` | `11.5 ppg` | preservado |
| compressibilidade | `6.4e-10 1/Pa` | `6.4e-10 1/Pa` | preservado |
| `alpha` | `8e-4 1/degC` | `8e-4 1/degC` | preservado |
| drill pipe OD | `5.5 in` | `5.5 in` | preservado |
| `profTeste` | `4374 m` | `4374 m` | preservado |
| compliance | `constant_geometric = 1.8571966938610005e-8 1/Pa` | equivalente diagnóstica | diagnóstica |
| `sink_timing` | `next_step` | sink positivo no passo seguinte | preservado para diagnóstico |

## Diferenças geométricas, malha e sampling

| Item | LOT_Tese/APBSalt1D | Modern-refined | Consequência |
|---|---:|---:|---|
| `outer_radius_m` | `8 m` | `1.556 m` default/bridge | domínio não equivalente |
| `radial_elements` | `15` | `40` default/bridge | malha não equivalente |
| `ratio` | `10` | metadata não consumida | não há equivalência APBSalt1D |
| `integration_order` | `3` | `3` em `AxisymL3` | alinhamento parcial, insuficiente |
| sampling `sigmaTheta` | `getElem(0)->getSigmaTheta(); sig(2,0)` | série temporal sem amostras espaciais | `legacy_elem0_sig_2_0` bloqueado |
| fonte `sigmaTheta` | APBSalt1D legado | refined `sigma_theta_time_series` | diagnóstica, não runtime wall stress |
| status APBSalt1D metadata | consumida no legado | `APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED` | metadata-only |
| status sampling bridge | n/a | `APBSALT1D_SAMPLING_BRIDGE_METADATA_ONLY` | sem consumo real |

## Configuração de compliance diagnóstica

A baseline diagnóstica usa:

```text
C_eff = C_fluid + C_geom
C_fluid = 6.4e-10 1/Pa
C_geom = 1.8571966938610005e-8 1/Pa
C_eff = 1.9211966938610006e-8 1/Pa
```

Isso sustentou a escala de pressão, mas não deve ser promovido a modelo físico
validado.

## Configuração de sink_timing

O legado aplica sink positivo no passo seguinte à abertura:

```text
first_opened_time_s = 510.0
first_sink_positive_time_s = 540.0
sink_delay_s = 30.0
```

O moderno preserva esse comportamento diagnóstico com `sink_timing: next_step`.

## Configuração sigmaTheta

A fonte moderna usada é `sigma_theta_time_series` refinada:

```text
number_of_sigmaTheta_points = 44
sigmaTheta_at_510s = 66666600.0 Pa
sigmaTheta_at_660s = 65445500.0 Pa
```

Essa fonte é diagnóstica; ela não substitui `SaltWallStressDiagnostics` runtime.

## Resultados

| Métrica | Legado | Modern-refined | Diferença | Interpretação |
|---|---:|---:|---:|---|
| pressão máxima | `69035836.1743195 Pa` | `67331393.612597 Pa` | `-2.468924338685035%` | escala de pressão diagnóstica boa |
| erro relativo de pressão máxima | `0` | `-0.02468924338685035` | `-0.02468924338685035` | aceitável para diagnóstico, não validação física |
| tempo de abertura | `510 s` | `660 s` | `+150 s` | diferente, mas não erro automático |
| erro de tempo de abertura | `0 s` | `+150 s` | `+150 s` | bloqueado por geometria/sampling |
| sink delay | `30 s` | `30 s` | `0 s` | preservado |
| pressão na abertura | auditada no legado | próxima em escala | erro relativo `0.008415423398363079` | bom para diagnóstico |
| erro relativo da pressão na abertura | `0` | `0.008415423398363079` | `0.8415%` | escala local preservada |

## Interpretação da abertura em 660 s

A abertura moderna em `660 s` não deve ser automaticamente classificada como
erro. O modo atual não consome a geometria APBSalt1D, não possui amostras
espaciais para `legacy_elem0_sig_2_0` e não usa uma fonte real de tensão de
parede runtime.

## O que seria necessário para exigir 510 s

Para exigir abertura em `510 s`, seria necessário operar em
`legacy-equivalence mode` real:

- consumir `outer_radius_m = 8 m`;
- consumir `radial_elements = 15`;
- consumir `ratio = 10`;
- preservar `integration_order = 3`;
- mapear `legacy_elem0_sig_2_0`;
- rastrear `pressure_source` e timing depois do gate geométrico.

## Limitações

- Não há validação física de fratura.
- `constant_geometric` continua diagnóstico.
- `pressure_tabulated_geometric` permanece bloqueado.
- `pressure_source/timing` permanece bloqueado por geometria.
- `SaltWallStressDiagnostics` ainda não alimenta o LOT runtime.
- A comparação com o legado é informativa, não regressão estrita.

## Próximas etapas recomendadas

1. Consolidar `modern-refined mode` em mais casos ou sensitividade de
   malha/domínio/sampling.
2. Preparar gráficos e relatórios de comparação para tese/artigo.
3. Planejar `SaltWallStressDiagnostics` runtime opt-in.
4. Só estudar solver-equivalence APBSalt1D se regressão estrita contra
   `LOT_Tese` for necessária.

## Roadmap associado

A Fase 10.27C consolidou o roadmap pós-10.27 em:

```text
docs/32_post_10_27_roadmap.md
```

A próxima fase recomendada é `10.28A`, focada em aplicar o pacote
`modern-refined` a casos adicionais. A sensibilidade de malha/domínio/sampling
fica planejada para `10.28B`, e os gráficos de comparação para tese/artigo para
`10.28C`.
