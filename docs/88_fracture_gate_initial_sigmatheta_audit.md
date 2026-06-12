# Fase 11.10N — auditoria do estado inicial de sigma-theta no gate de fratura

## Resumo executivo

A Fase 11.10N audita se o futuro `fracture_initiation_gate` pode ser avaliado
com `sigma_theta_compression_positive_Pa` nulo, não inicializado ou
semanticamente desalinhado com a pressão usada no critério.

Classificação:

```text
sigmatheta_initial_state = SIGMATHETA_INITIAL_STATE_MISSING
fracture_gate_status = FRACTURE_GATE_REQUIRES_INITIAL_STATE_WIRING
pressure_semantics = PRESSURE_SIGMATHETA_SEMANTICS_PARTIAL_REQUIRES_ALIGNMENT
sign_convention = SIGN_CONVENTION_REQUIRES_REVIEW
dispatch_allowed_next = false
runtime_execution_allowed_next = false
buz29_execution_allowed_next = false
recommended_next_phase = PHASE11_10O_SPECIFY_SIGMATHETA_INITIAL_STATE_WIRING
```

A seleção de fracture_model no parser/schema não autoriza dispatch físico de PKN ou PENNY_SHAPED enquanto sigma_theta_compression_positive_Pa não estiver comprovadamente inicializado e semanticamente alinhado com a pressão usada no critério.

## Motivação

A Fase 11.10M integrou `lot.fracture.fracture_model` ao parser/schema com
default retrocompatível `PKN`, mas manteve:

```text
runtime_dispatch_enabled = false
buz29_execution_allowed = false
sigma_theta_initial_state_audit_required = true
```

O gate registrado foi:

```text
SIGMATHETA_INITIAL_STATE_REQUIRED_BEFORE_MODEL_DISPATCH
```

A 11.10N confirma que esse gate ainda deve permanecer fechado.

## t=0 da perfuração versus t=0 do LOT

O t=0 da simulação LOT não deve ser interpretado como t=0 da perfuração. Para rochas salinas/viscoelásticas, o estado inicial do LOT deve considerar a redistribuição elástica/geomecânica já ocorrida após a perfuração.

Isso significa que um futuro critério de fratura não deve assumir:

```text
sigma_theta_compression_positive_Pa = 0
```

no início do LOT. A tensão tangencial relevante deve representar o estado de
parede após a perfuração e antes do carregamento LOT, ou declarar
explicitamente que usa um proxy diagnóstico.

## Fontes auditadas

Foram auditadas as seguintes rotas modernas:

| Rota | Arquivos principais | Status |
|---|---|---|
| Parser YAML sigma-theta | `src/io/CaseParser.cpp`, `include/core/types.hpp` | Lê `sigma_theta_static` e `sigma_theta_time_series`, mas como entrada diagnóstica. |
| Provider runtime diagnóstico | `include/lot/SigmaThetaProvider.hpp`, `src/lot/SigmaThetaProvider.cpp` | Interpola série temporal fornecida; não calcula estado pós-perfuração. |
| Gate em PKN | `src/lot/PknModel.cpp` | Compara `trial_pressure_Pa` contra sigma-theta fornecido. |
| Runner | `src/lot/PknRunner.cpp` | Constrói provider a partir de `CaseData`; não calcula tensão inicial. |
| Writer | `src/io/ResultWriter.cpp` | Exporta campos de iniciação e lookup; não define o estado. |
| Diagnóstico sal/coupling | `src/salt/SaltCreepTimeBridge.cpp`, `include/salt/SaltWallStressDiagnostics.hpp`, `src/coupling/LotSaltSigmaThetaDiagnostic.cpp` | Disponível como rota opt-in de diagnóstico; não é o runtime default de fratura. |
| Breakdown sigma-theta | `src/coupling/LotSaltSigmaThetaBreakdown.cpp` | Implementa álgebra diagnóstica `pressure - sigmaTheta`; não inicializa estado geomecânico. |

## Estado inicial geomecânico

Não foi encontrada, no runtime `lot-pkn`, uma etapa que construa
explicitamente:

```text
sigma_theta_initial_after_drilling
```

antes do gate de fratura. As fontes atuais de sigma-theta entram por:

1. `sigma_theta_static` no YAML;
2. `sigma_theta_time_series` no YAML;
3. provider runtime criado a partir da série;
4. rota diagnóstica opt-in via `SaltWallStressDiagnostics`.

Essas rotas são úteis para diagnóstico, mas não comprovam que o estado inicial
pós-perfuração foi calculado, preservado e entregue ao gate de fratura.

## Inicialização de sigma_theta

O `PknModel` valida que `sigma_theta_compression_positive_Pa` seja finito e
positivo quando a rota sigma-theta está ativa. Isso evita um valor zero
silencioso em `sigma_theta_static` e no provider.

Essa validação é necessária, mas não suficiente. Ela confirma que há um número
positivo; não confirma que o número corresponde ao estado geomecânico
pós-perfuração.

## Semântica de pressão

As rotas atuais usam pressões distintas:

| Campo | Uso atual | Risco |
|---|---|---|
| `wellbore_pressure_trial_Pa` | Usado em `sigma_theta_time_series` e provider runtime. | Pode ser pressão total trial; precisa alinhar com a referência de sigma-theta. |
| `wellbore_pressure_Pa` | Exigido por `sigma_theta_static`. | Pode representar resultado de balanço volumétrico diagnóstico. |
| `fracture.breakdown.pressure` | Threshold simplificado contra incremento acima de `initial_pressure_Pa`. | Não é sigma-theta e não representa o critério legado completo. |
| `net_pressure_Pa` | Pressão PKN direta/incremental. | Não deve ser confundida com pressão absoluta de parede. |

O risco principal é comparar pressão absoluta com tensão incremental, ou
pressão incremental com tensão total. A próxima fase precisa especificar a
referência exata de ambos os lados do critério.

## Convenção de sinal

O projeto documenta compressão positiva em `docs/08_known_issues.md`, e os
campos modernos usam explicitamente:

```text
sigma_theta_compression_positive_Pa
```

A álgebra diagnóstica atual é:

```text
margin_Pa = pressure_Pa - sigma_theta_compression_positive_Pa
opened = margin_Pa > 0
```

Essa álgebra é coerente com o critério legado-migrado quando `sigmaTheta`
representa uma pressão/tensão crítica equivalente em compressão positiva.
Ainda assim, antes de dispatch físico, a rota precisa declarar se
`sigma_theta` é tensão total, tensão efetiva, tensão tangencial compressiva ou
um limiar de pressão equivalente.

## Risco de fratura em t≈0

Fratura em t≈0 é suspeita se decorrer de sigma_theta nulo, não inicializado, ou de comparação entre pressão e tensão com referenciais incompatíveis.

Casos especialmente perigosos:

- `sigma_theta_compression_positive_Pa = 0`;
- provider retornando valor default não inicializado;
- ausência silenciosa de estado inicial pós-perfuração;
- comparação de `wellbore_pressure_trial_Pa` total contra tensão incremental;
- comparação de pressão incremental contra tensão total;
- inversão de sinal entre compressão positiva e tensão positiva.

## Classificação do estado inicial

```text
SIGMATHETA_INITIAL_STATE_MISSING
```

Justificativa: existem rotas de consumo de sigma-theta, mas não existe prova
no runtime `lot-pkn` de que `sigma_theta_initial_after_drilling` seja calculado
antes do gate.

## Classificação do fracture gate

```text
FRACTURE_GATE_REQUIRES_INITIAL_STATE_WIRING
```

O gate de fratura não deve ser liberado para dispatch por `fracture_model`
enquanto a origem do sigma-theta inicial não for especificada e testada.

## Próxima fase recomendada

```text
PHASE11_10O_SPECIFY_SIGMATHETA_INITIAL_STATE_WIRING
```

A próxima fase deve especificar a fronteira mínima para fornecer
`sigma_theta_initial_after_drilling` ao critério de fratura, sem ainda executar
BUZ29-PENNY e sem alterar o comportamento default de `lot-pkn`.

## Encaminhamento 11.10O

A Fase 11.10O atende a recomendação acima como especificação, não como
implementação:

```text
PHASE11_10O_SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED
SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED
ELASTIC_INITIAL_WELLBORE_STATE_SELECTED_AS_PREFERRED_SOURCE
FRACTURE_GATE_BLOCKED_UNTIL_SIGMATHETA_INITIALIZED
PRESSURE_SIGMATHETA_COMPATIBILITY_REQUIRED
DISPATCH_REMAINS_BLOCKED
```

O contrato futuro exige que `sigma_theta_initial_compression_positive_Pa`
represente o estado pós-perfuração e pré-LOT. A próxima fase permitida é
implementar um guard de wiring; dispatch físico, runtime BUZ29-PENNY e
equivalência legada continuam bloqueados.

## Encaminhamento 11.10P

A Fase 11.10P implementa o guard isolado
`lot::SigmaThetaInitialStateGuard`, cobrindo as lacunas auditadas aqui:
estado inicial ausente, valor nao finito ou nao positivo, fonte desconhecida,
tempo de estado incorreto, referencial desconhecido, convencao de sinal
desconhecida e incompatibilidade pressao x sigma-theta.

O guard ainda nao e integrado ao runtime. Portanto, a conclusao da auditoria
permanece operacionalmente bloqueante para dispatch fisico:

```text
SIGMATHETA_INITIAL_STATE_GUARD_IMPLEMENTED
DISPATCH_REMAINS_BLOCKED
BUZ29_RUNTIME_EXECUTION_NOT_ALLOWED
```
