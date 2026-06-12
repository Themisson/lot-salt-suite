# Fase 11.11J — auditoria de disponibilidade runtime de sigma-theta e pressao

## Resumo executivo

A Fase 11.11J audita se o runtime real ja possui fontes suficientes para
alimentar o `limited_gate` com `sigma_theta_initial`, `sigma_theta_current` e
pressao de poco com semantica resolvida.

Classificacao:

```text
RUNTIME_SIGMATHETA_PRESSURE_AVAILABILITY_AUDITED
```

Decisao:

```text
runtime_real_wiring_allowed_next = false
```

## Escopo auditado

Foram auditados, em modo leitura:

```text
apps/lot-sim.cpp
include/core/
src/core/
include/io/
src/io/
include/lot/
src/lot/
include/salt/
src/salt/
external/saltcreep/
legacy/
legance/
```

## sigma_theta inicial

Status:

```text
sigma_theta_initial_runtime_available = false
```

O runtime diagnostico atual ainda inicializa o estado sigma-theta como ausente
quando o gate limitado roda sem fonte explicita. Existem campos de
`sigma_theta` em casos diagnosticos e rotas de salt/coupling, mas isso ainda
nao constitui uma fonte runtime real pos-perfuracao para o gate.

## sigma_theta current

Status:

```text
sigma_theta_current_runtime_available = false
```

Nao ha stream runtime LOT/PKN de sigma-theta total atual na parede do poco,
com sinal e referencial alinhados ao criterio pressao x sigma-theta.

## Pressao

Status:

```text
wellbore_pressure_runtime_available = true
```

O runtime LOT/PKN possui pressoes de poco suficientes para outputs e
diagnosticos. Para wiring fisico do gate, porem, a semantica da pressao ainda
precisa ser alinhada ao referencial de sigma-theta.

## Convencao de sinal

Status:

```text
sign_convention_resolved = false
```

A convencao geral de compressao positiva esta documentada, mas a fonte runtime
real de sigma-theta ainda nao existe. Portanto a convencao nao pode ser
declarada resolvida para wiring real do gate.

## Referencial

Status:

```text
reference_frame_resolved = false
```

O contrato esperado e:

```text
WELLBORE_WALL_TOTAL_STRESS
```

Como a fonte runtime real ainda nao existe, o referencial permanece bloqueado.

## Lacunas

```text
MISSING_RUNTIME_SIGMATHETA_INITIAL_SOURCE
MISSING_RUNTIME_SIGMATHETA_CURRENT_SOURCE
PRESSURE_SEMANTICS_NOT_RESOLVED_FOR_REAL_GATE
SIGMATHETA_SIGN_CONVENTION_NOT_RUNTIME_RESOLVED
SIGMATHETA_REFERENCE_FRAME_NOT_RUNTIME_RESOLVED
```

## Proxima fase recomendada

```text
PHASE11_11K_SPECIFY_POST_DRILLING_INITIAL_STATE_INTEGRATION
```

A proxima fase deve especificar o contrato de estado inicial pos-perfuracao,
mantendo `implementation_allowed_next=false` enquanto a fonte runtime real nao
existir.
