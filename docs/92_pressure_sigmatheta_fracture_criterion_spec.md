# Critério pressão x sigma_theta para fracture_initiation_gate (Fase 11.10R)

## Resumo executivo

A 11.10R não implementa o critério de fratura. Ela apenas especifica a álgebra e a convenção de sinal necessárias para impedir comparações inválidas entre pressão e sigma_theta.

A decisão da fase é que o futuro `fracture_initiation_gate` deve consultar `SigmaThetaInitialStateGuard`, exigir semântica de pressão conhecida, exigir referencial de `sigma_theta` conhecido e só então avaliar um critério escrito em termos de tração tangencial efetiva ou de uma pressão crítica derivada. O dispatch físico permanece bloqueado.

## Contexto pós-11.10Q

A 11.10Q especificou a sequência futura:

```text
FractureModelSelector
-> SigmaThetaInitialStateGuard
-> criterio pressao x sigma_theta
-> dispatch PKN/PENNY_SHAPED futuro
```

O estado registrado foi:

```text
FRACTURE_GATE_DISPATCH_WITH_SIGMATHETA_GUARD_SPECIFIED
PRESSURE_SIGMATHETA_CRITERION_SPEC_REQUIRED
SIGN_CONVENTION_RESOLUTION_REQUIRED
DISPATCH_REMAINS_BLOCKED
```

Esta fase resolve a especificação algébrica, mas não altera C++, parser, schema, `PknModel`, `PknRunner`, CLI ou `lot-pkn`.

## Convenção de sinal

O projeto preserva a convenção de compressão positiva:

```text
sigma_theta_compression_positive_Pa > 0  -> compressão tangencial
sigma_theta_compression_positive_Pa = 0  -> tensão tangencial nula
sigma_theta_compression_positive_Pa < 0  -> tração tangencial
```

A pressão de poço é positiva quando representa pressão interna compressiva aplicada pelo fluido na parede:

```text
wellbore_pressure_Pa > 0 -> pressão compressiva contra a parede
```

Com sigma_theta em convenção compression-positive, a condição de tração deve ser escrita com transformação explícita de sinal. Não é permitido usar pressure > sigma_theta_compression_positive_Pa como critério final sem definir referencial, pressão crítica e convenção de sinal.

## Campos de pressão auditados

| Campo | Estado atual | Semântica | Uso recomendado no gate futuro |
|---|---|---|---|
| `wellbore_pressure_Pa` | Exportado por `PknResult` e usado no modo `volumetric_balance`. | Candidato a pressão de poço/anular absoluta ou total quando a semântica está documentada. | Preferido como pressão interna se `pressure_semantics` for explícito. |
| `wall_pressure_Pa` | Usado em acoplamento sal/bridge. | Pressão compressiva de parede para sal, ou condição radial equivalente documentada. | Não usar diretamente como gate LOT sem mapeamento. |
| `net_pressure_Pa` | Saída PKN direta. | Pressão líquida/incremental PKN. | Bloqueado como substituto de pressão absoluta sem transformação de referência. |
| `trial_pressure_Pa` | Variável local em `PknModel`. | Candidato de passo antes da aplicação de sink. | Pode virar campo explícito futuro, mas não é contrato público hoje. |
| `fracture_threshold_pressure_Pa` | Não existe como campo de runtime. | Pressão crítica derivada de tensão, resistência e referencial. | Campo futuro para forma alternativa por threshold. |

## Campos de sigma_theta auditados

| Campo | Estado atual | Semântica | Uso recomendado no gate futuro |
|---|---|---|---|
| `sigma_theta_compression_positive_Pa` | Existe em provider, diagnósticos, YAMLs e resultados. | Amostra sigma-theta em compressão positiva. | Usar somente com tempo, fonte e referencial conhecidos. |
| `sigma_theta_initial_compression_positive_Pa` | Entrada do `SigmaThetaInitialStateGuard`. | Estado inicial após perfuração e antes do LOT. | Pré-condição, não critério corrente completo por si só. |
| `sigma_theta_current_compression_positive_Pa` | Campo conceitual futuro. | Estado atual total/efetivo no instante do gate. | Preferido para o critério físico futuro. |
| `sigma_theta_increment_due_to_lot_Pa` | Não existe. | Incremento induzido pelo LOT sobre o estado inicial. | Necessário se o estado corrente não estiver disponível diretamente. |

## Critério algébrico recomendado

O critério preferencial deve usar o estado corrente de `sigma_theta` no referencial correto:

```text
tensile_condition_Pa = -sigma_theta_current_compression_positive_Pa
fracture_initiated = tensile_condition_Pa >= tensile_strength_Pa
```

Forma equivalente:

```text
sigma_theta_current_compression_positive_Pa <= -tensile_strength_Pa
```

Esse critério só pode ser avaliado quando:

```text
SigmaThetaInitialStateGuard = READY
pressure_semantics conhecido
sigma_theta_reference_frame conhecido
sigma_theta_sign_convention = COMPRESSION_POSITIVE
tensile_strength_Pa definido
```

Se apenas `sigma_theta_initial_compression_positive_Pa` estiver disponível, uma fase futura deve especificar o wiring de incremento LOT:

```text
sigma_theta_current_compression_positive_Pa =
    sigma_theta_initial_compression_positive_Pa
  + sigma_theta_increment_due_to_lot_Pa
```

Essa soma só é válida se ambos estiverem no mesmo referencial.

## Forma alternativa por threshold pressure

Uma implementação futura também pode trabalhar por pressão crítica:

```text
fracture_margin_Pa = wellbore_pressure_Pa - fracture_threshold_pressure_Pa
fracture_initiated = fracture_margin_Pa >= 0
```

Mas `fracture_threshold_pressure_Pa` deve ser derivada explicitamente de:

```text
sigma_theta_current_compression_positive_Pa
tensile_strength_Pa
estado inicial
referencial total/efetivo
semântica da pressão
```

A forma por threshold não autoriza comparar diretamente `wellbore_pressure_Pa` com `sigma_theta_compression_positive_Pa`.

## Atalhos proibidos

Atalhos bloqueados:

```text
pressure > sigma_theta_compression_positive_Pa
wellbore_pressure_Pa > sigma_theta_compression_positive_Pa
net_pressure_Pa > sigma_theta_compression_positive_Pa
```

Essas expressões são proibidas como critério físico final quando não houver transformação de sinal, pressão crítica e referencial explícito. A álgebra histórica `legacy_algebra` permanece apenas diagnóstica.

## Estados do critério

Estados definidos para o futuro guard:

```text
FRACTURE_CRITERION_BLOCKED_SIGMATHETA_GUARD_NOT_READY
FRACTURE_CRITERION_BLOCKED_PRESSURE_SEMANTICS_UNKNOWN
FRACTURE_CRITERION_BLOCKED_SIGN_CONVENTION_UNKNOWN
FRACTURE_CRITERION_BLOCKED_REFERENCE_FRAME_MISMATCH
FRACTURE_CRITERION_READY
FRACTURE_NOT_INITIATED
FRACTURE_INITIATED
```

## Campos ainda necessários

Campos mínimos para a fase de implementação do guard:

```text
wellbore_pressure_Pa
sigma_theta_current_compression_positive_Pa
tensile_strength_Pa
pressure_semantics
sigma_theta_reference_frame
sigma_theta_sign_convention
fracture_margin_Pa
```

Campos opcionais, mas úteis:

```text
fracture_threshold_pressure_Pa
sigma_theta_increment_due_to_lot_Pa
criterion_status
blocking_reasons
```

## Próxima fase recomendada

```text
PHASE11_10S_IMPLEMENT_PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD
```

O dispatch físico continua bloqueado até implementação e teste de um guard específico para o critério pressão × sigma_theta.

## Status registrado

```text
PHASE11_10R_PRESSURE_SIGMATHETA_FRACTURE_CRITERION_SPECIFIED
PRESSURE_SIGMATHETA_FRACTURE_CRITERION_SPECIFIED
SIGMATHETA_COMPRESSION_POSITIVE_SIGN_CONVENTION_RESOLVED
PRESSURE_GREATER_THAN_SIGMATHETA_SHORTCUT_FORBIDDEN
DISPATCH_REMAINS_BLOCKED_UNTIL_CRITERION_GUARD_IMPLEMENTED
```
