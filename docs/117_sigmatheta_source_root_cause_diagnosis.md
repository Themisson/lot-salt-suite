# Fase A — diagnostico da causa raiz da fonte sigma_theta

## Resumo executivo

O limited_gate e o bloco `sigma_theta_diagnostic_input` funcionam em modo
diagnostico, mas o runtime moderno ainda nao expoe uma fonte fisica de
`sigma_theta_initial_compression_positive_Pa` ou
`sigma_theta_current_compression_positive_Pa`.

Classificacao:

```text
SEMI_PHYSICAL_ELASTIC_SIGMATHETA_SOURCE_IMPLEMENTABLE
implementation_allowed_next = true
```

Isso significa que o proximo passo pode implementar um provider pequeno e
controlado para normalizar a fonte de sigma_theta do gate. A fase nao habilita
dispatch fisico, nao executa BUZ29-PENNY e nao altera o comportamento fisico do
PKN.

## Evidencia auditada

| Pergunta | Resposta | Evidencia |
|---|---|---|
| Existe `sigma_theta_initial` fisico no runtime moderno? | Nao | `FractureGateDiagnosticPreRunner` popula o gate a partir de `sigma_theta_diagnostic_input`. |
| Existe `sigma_theta_current` fisico no runtime moderno? | Nao | Nao ha estado tangencial corrente real exposto ao `limited_gate`. |
| Existe pressao de poco runtime? | Sim | `PknResult.wellbore_pressure_series_Pa` e `ResultWriter` exportam `wellbore_pressure_Pa`. |
| Existe geometria/material suficiente para um provider inicial? | Parcial | `CaseData` contem contexto do caso, mas o calculo elastico validado ainda nao existe. |
| O calculo deve ser provider novo? | Sim | Um `PostDrillingSigmaThetaProvider` isola semantica, sinal e caveats antes do pre-runner. |

## Diagnostico

O problema real nao esta no selector, nos guards ou no limited_gate. Esses
componentes ja validam contratos diagnosticos. A lacuna esta antes deles: falta
uma fonte normalizada de sigma_theta pos-perfuracao, antes do LOT, com sinal,
referencial e tempo de estado explicitos.

O caminho minimo seguro e implementar um provider que aceite fontes
diagnosticas existentes e uma rota semi-fisica inicial, sem promover o resultado
a validacao fisica.

## Gate para a proxima fase

```text
recommended_solution_path = SEMI_PHYSICAL_ELASTIC_SIGMATHETA_SOURCE_IMPLEMENTABLE
implementation_allowed_next = true
proposed_component = PostDrillingSigmaThetaProvider
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_change_allowed = false
```

## Arquivos provaveis da solucao

```text
include/lot/PostDrillingSigmaThetaProvider.hpp
src/lot/PostDrillingSigmaThetaProvider.cpp
tests/cpp/test_post_drilling_sigma_theta_provider.cpp
src/lot/FractureGateDiagnosticPreRunner.cpp
```

## Caveats

- O diagnostico nao valida fisicamente abertura de fratura.
- O legado continua referencia auditada, nao fonte runtime fisica.
- `PENNY_SHAPED` permanece diagnostic-only.
- O dispatch fisico permanece desabilitado.
