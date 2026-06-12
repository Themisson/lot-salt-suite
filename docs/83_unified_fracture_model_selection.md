# Fase 11.10I — seleção unificada de `fracture_model`

## Resumo executivo

A Fase 11.10I reconcilia o gate da Fase 11.10H com a decisão arquitetural
preferida para o `lot-salt-suite`: a evolução não-PKN não deve criar uma rota
runtime paralela permanente. A arquitetura recomendada é manter uma rota
LOT/fracture unificada e diferenciar o modelo de fraturamento pelo campo
`fracture_model` no input. Quando `fracture_model` estiver ausente, o
comportamento default deve permanecer PKN.

Classificações registradas:

```text
PKN_DEFAULT_FRACTURE_MODEL
PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY
UNIFIED_LOT_FRACTURE_RUNTIME_SELECTED
UNSUPPORTED_FRACTURE_MODELS_BLOCKED
FRACTURE_INITIATION_GATE_REQUIRED
SIGMATHETA_SIGN_CONVENTION_REQUIRED
```

Esta fase é somente especificação. Ela não implementa runner, não altera C++,
não altera parser/schema, não executa BUZ29-PENNY, não valida BUZ29 e não muda
o comportamento de `lot-sim run --mode lot-pkn`.

## Contexto pós-11.10H

A Fase 11.10H registrou:

```text
decision = NON_PKN_DIAGNOSTIC_RUNNER_SPEC_PARTIAL
runner_implementation_allowed_now = false
buz29_runtime_execution_allowed = false
lot_pkn_impact_allowed = false
recommended_next_phase = PHASE11_10I_SPECIFY_NON_PKN_DIAGNOSTIC_RUNNER
```

Essa recomendação apontava para especificar um runner diagnóstico não-PKN
futuro. A 11.10I estreita essa direção: o projeto deve evitar bifurcar o
runtime oficial em rotas independentes quando a distinção correta é a seleção
do modelo de fratura dentro de uma rota LOT/fracture comum.

## Problema com rotas paralelas

Um runner paralelo não-PKN poderia duplicar responsabilidades já existentes no
fluxo LOT:

- leitura e validação de caso;
- critério de início de fratura;
- montagem de séries temporais;
- escrita de diagnóstico;
- preservação dos casos PKN existentes.

Duplicar esses pontos aumentaria o risco de divergência entre PKN e modelos
diagnósticos futuros. O caminho recomendado é introduzir, em fase futura, um
selector guardado por input, sem alterar o default atual.

## Decisão: runtime LOT/fracture unificado

A decisão arquitetural é:

```text
UNIFIED_LOT_FRACTURE_RUNTIME_SELECTED
```

Interpretação:

1. Casos antigos sem `fracture_model` continuam usando PKN.
2. Casos PKN existentes continuam usando PKN.
3. `PENNY_SHAPED` só é selecionado quando declarado explicitamente no input.
4. `KGD`, `KGD_CIRCULAR`, `KGD_ELLIPTICAL`, `RADIAL`, `ELLIPTICAL`, `UNKNOWN`
   e valor vazio explícito permanecem bloqueados.
5. A seleção do modelo não deve criar rotas runtime paralelas desnecessárias.

## Campo `fracture_model` proposto

Forma preferencial futura:

```yaml
lot:
  fracture:
    enabled: true
    fracture_model: PKN
```

ou:

```yaml
lot:
  fracture:
    enabled: true
    fracture_model: PENNY_SHAPED
```

O campo recomendado é:

```text
lot.fracture.fracture_model
```

Nesta fase, o campo é apenas especificado. Parser e schema permanecem
inalterados.

## PKN como default

Classificação:

```text
PKN_DEFAULT_FRACTURE_MODEL
```

Regra futura:

```text
Se fracture_model estiver ausente:
  usar PKN.
```

Essa regra preserva compatibilidade com os casos existentes, que hoje são
selecionados por `simulation.mode: lot-pkn`, `lot.model: pkn` e
`lot.fracture.geometry: pkn`.

## PENNY_SHAPED como opt-in explícito

Classificação:

```text
PENNY_SHAPED_EXPLICIT_OPT_IN_ONLY
```

Regra futura:

```text
PENNY_SHAPED só pode ser usado quando fracture_model = PENNY_SHAPED estiver
explicitamente declarado.
```

PENNY_SHAPED é opt-in explícito, diagnóstico, não fisicamente validado e não
equivalente ao legado. Ele não deve alterar o comportamento dos casos PKN
existentes.

## Modelos bloqueados

Classificação:

```text
UNSUPPORTED_FRACTURE_MODELS_BLOCKED
```

Modelos bloqueados nesta etapa:

```text
KGD
KGD_CIRCULAR
KGD_ELLIPTICAL
RADIAL
ELLIPTICAL
UNKNOWN
vazio inválido explícito
```

A existência documental de modelos não-PKN no legado não autoriza seleção
runtime moderna sem contrato, parser/schema, testes e documentação dedicados.

## Gate de início de fratura

A seleção do `fracture_model` só deve produzir execução do modelo de fratura
após o gate de início de fratura, baseado em pressão interna e `sigma_theta`,
com convenção de sinal explicitamente documentada.

Campos conceituais:

```text
wellbore_pressure_Pa
sigma_theta_compression_positive_Pa
fracture_initiation_gate
fracture_model
```

Estados conceituais:

```text
fracture_initiation_gate = NOT_REACHED
selected_fracture_model = PKN
fracture_model_selected_but_not_executed
```

ou:

```text
fracture_initiation_gate = REACHED
selected_fracture_model = PENNY_SHAPED
runtime_status = DIAGNOSTIC_ONLY
```

## Convenção de sinal de `sigma_theta`

O projeto usa a convenção documentada de compressão positiva. Assim, qualquer
critério que use `sigma_theta_compression_positive_Pa` deve escrever a álgebra
explicitamente para evitar inversão de sinal.

Regra conceitual:

```text
wellbore_pressure_Pa > sigma_theta_compression_positive_Pa
```

Essa expressão é somente uma forma diagnóstica já usada nas fases sigma-theta.
Ela não valida fisicamente BUZ29-PENNY nem estabelece equivalência com o legado.

## Status atual de PKN

O PKN é o único runtime oficial disponível no `lot-sim` atual. O comando:

```text
lot-sim run --mode lot-pkn
```

permanece desacoplado da rota PennyShaped e não é alterado por esta fase.

## Status atual de PENNY_SHAPED

PENNY_SHAPED possui:

- núcleo mínimo isolado;
- adapter diagnóstico opt-in;
- writer diagnóstico opt-in;
- fixtures de contrato;
- candidato BUZ29-PENNY inativo.

Ainda não possui:

- execução runtime BUZ29-PENNY;
- validação física;
- equivalência com o legado;
- parser/schema oficial para `fracture_model`;
- selector guard integrado ao runtime.

## Impacto no parser/schema

Impacto nesta fase:

```text
parser_schema_change_allowed_now = false
runtime_implementation_allowed_now = false
```

Uma fase futura deve especificar ou implementar um guard de seleção que:

1. preserve `DEFAULT_TO_PKN` quando `fracture_model` estiver ausente;
2. aceite `PKN`;
3. aceite `PENNY_SHAPED` somente como opt-in explícito;
4. rejeite modelos não suportados com erro claro;
5. mantenha `lot-pkn` inalterado.

## Próxima fase recomendada

Próxima fase recomendada:

```text
PHASE11_10J_SPECIFY_FRACTURE_MODEL_SELECTOR_GUARD
```

Se a revisão arquitetural da próxima fase confirmar que já há estrutura segura
para isso sem alterar comportamento PKN, a fase seguinte poderá evoluir para:

```text
PHASE11_10J_IMPLEMENT_FRACTURE_MODEL_SELECTOR_GUARD
```
