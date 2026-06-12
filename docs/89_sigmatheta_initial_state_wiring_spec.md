# Fase 11.10O — especificação do wiring do estado inicial sigma-theta

## Resumo executivo

A Fase 11.10O especifica o contrato futuro para conectar o estado inicial
`sigma_theta_compression_positive_Pa` ao `fracture_initiation_gate`. Ela
responde ao bloqueio da Fase 11.10N, que classificou a rota atual como:

```text
SIGMATHETA_INITIAL_STATE_MISSING
FRACTURE_GATE_REQUIRES_INITIAL_STATE_WIRING
PRESSURE_SIGMATHETA_SEMANTICS_PARTIAL_REQUIRES_ALIGNMENT
SIGN_CONVENTION_REQUIRES_REVIEW
```

A 11.10O não implementa wiring nem altera o critério físico. Ela apenas especifica como o estado inicial sigma_theta_compression_positive_Pa deve ser conectado antes de qualquer dispatch real de fratura.

Classificação da especificação:

```text
wiring_spec_status = SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED
preferred_source = ELASTIC_INITIAL_WELLBORE_STATE
dispatch_allowed_next = false
runtime_execution_allowed_next = false
implementation_allowed_next = true
recommended_next_phase = PHASE11_10P_IMPLEMENT_SIGMATHETA_INITIAL_STATE_WIRING_GUARD
```

## Contexto pós-11.10N

A 11.10N mostrou que o runtime já consegue consumir `sigma_theta_static`,
`sigma_theta_time_series` e provider diagnóstico, mas não prova que existe um
estado tangencial inicial pós-perfuração antes do gate. O problema deixou de ser
apenas sintático: `fracture_model` já está no parser/schema, mas o dispatch
físico continua bloqueado por falta de contrato de estado inicial.

## Problema físico

O t=0 do LOT representa o início do teste de pressurização, não o instante da perfuração. A resposta elástica inicial da perfuração deve estar refletida no estado inicial geomecânico antes da avaliação do fracture_initiation_gate.

Para rochas salinas ou viscoelásticas, a parede do poço já passou por
redistribuição elástica/geomecânica antes do LOT. Portanto, o gate não deve
assumir `sigma_theta_compression_positive_Pa = 0`, nem aceitar valor ausente,
default silencioso ou referência semântica desconhecida.

## Fontes candidatas de sigma_theta inicial

| Fonte | Classificação | Uso recomendado |
|---|---|---|
| `ELASTIC_INITIAL_WELLBORE_STATE` | `PREFERRED_SOURCE` | Estado geomecânico calculado internamente após perfuração e antes do LOT. |
| `APB_SALT_COUPLED_STATE` | `FUTURE_SOURCE` | Fonte física mais rica, dependente de runtime sal/APB acoplado futuro. |
| `LEGACY_DIAGNOSTIC_TRACE` | `VALID_DIAGNOSTIC_SOURCE` | Comparação/auditoria controlada, sem virar produção. |
| `EXPLICIT_DIAGNOSTIC_INPUT` | `FALLBACK_WITH_CAVEAT` | Entrada manual apenas para teste controlado e documentação clara. |
| `SYNTHETIC_FIXTURE` | `FALLBACK_WITH_CAVEAT` | Teste unitário/fixture; não representa caso físico. |
| `UNKNOWN` | `BLOCKED_SOURCE` | Não pode alimentar o gate. |

A fonte preferencial deve ser o estado geomecânico calculado internamente antes do LOT, não um valor arbitrário de YAML.

## Contrato de estado inicial

O contrato conceitual futuro deve conter, no mínimo:

| Campo | Obrigatório | Semântica |
|---|---|---|
| `sigma_theta_initial_compression_positive_Pa` | Sim | Tensão tangencial compressiva positiva após perfuração e antes do LOT. |
| `sigma_theta_current_compression_positive_Pa` | Sim | Valor corrente usado pelo gate durante o passo LOT. |
| `sigma_theta_increment_due_to_lot_Pa` | Opcional | Incremento atribuído ao carregamento LOT. |
| `sigma_theta_source` | Sim | Origem rastreável do estado. |
| `sigma_theta_state_time` | Sim | Tempo conceitual do estado. |
| `sigma_theta_initialized` | Sim | Deve ser `true` antes do gate. |
| `sigma_theta_initial_state_valid` | Sim | Deve ser `true` antes do gate. |
| `sigma_theta_sign_convention` | Sim | Convenção de sinal explícita. |
| `sigma_theta_reference_frame` | Sim | Referencial total, efetivo ou incremental. |

Valores recomendados:

```text
sigma_theta_state_time:
  AFTER_DRILLING_BEFORE_LOT
  DURING_LOT_STEP
  UNKNOWN

sigma_theta_source:
  ELASTIC_INITIAL_WELLBORE_STATE
  APB_SALT_COUPLED_STATE
  LEGACY_DIAGNOSTIC_TRACE
  EXPLICIT_DIAGNOSTIC_INPUT
  SYNTHETIC_FIXTURE
  UNKNOWN

sigma_theta_reference_frame:
  TOTAL_STRESS
  EFFECTIVE_STRESS
  INCREMENTAL_STRESS
  UNKNOWN

sigma_theta_sign_convention:
  COMPRESSION_POSITIVE
  TENSION_POSITIVE
  UNKNOWN
```

## Regras do fracture_initiation_gate

O gate futuro deve bloquear avaliação quando:

```text
FRACTURE_GATE_BLOCKED_MISSING_INITIAL_SIGMATHETA:
  sigma_theta_initialized = false
  sigma_theta_initial_state_valid = false

FRACTURE_GATE_BLOCKED_PRESSURE_SIGMATHETA_MISMATCH:
  pressão absoluta comparada com tensão incremental
  pressão incremental comparada com tensão total
  pressure_semantics = UNKNOWN
  sigma_theta_reference_frame = UNKNOWN

FRACTURE_GATE_BLOCKED_SIGN_CONVENTION_UNKNOWN:
  sigma_theta_sign_convention = UNKNOWN
```

O estado positivo para a próxima implementação é apenas:

```text
FRACTURE_GATE_READY_FOR_DISPATCH_SPEC
```

Esse estado significa que a implementação do guard pode começar. Ele não
significa dispatch físico liberado.

## Alinhamento pressão × sigma_theta

| pressure_semantics | sigma_theta_reference_frame | Compatibilidade |
|---|---|---|
| `WELLBORE_PRESSURE_ABSOLUTE` | `TOTAL_STRESS` | Compatível se ambos representam o mesmo estado de parede e compressão positiva. |
| `WELLBORE_PRESSURE_ABSOLUTE` | `EFFECTIVE_STRESS` | Requer pressão de poros ou definição efetiva explícita. |
| `WELLBORE_PRESSURE_ABSOLUTE` | `INCREMENTAL_STRESS` | Bloqueado. |
| `PRESSURE_INCREMENT` | `INCREMENTAL_STRESS` | Compatível apenas com baseline incremental explícito. |
| `PRESSURE_INCREMENT` | `TOTAL_STRESS` | Bloqueado. |
| `NET_PRESSURE` | `TOTAL_STRESS` | Requer hidrostática, pressão de poros e referência de closure definidas. |
| `UNKNOWN` | `UNKNOWN` | Bloqueado. |

Não há fórmula final nesta fase. O objetivo é impedir que grandezas de
referenciais diferentes sejam comparadas por acidente.

## Convenção de sinal

A convenção preferencial do contrato é:

```text
sigma_theta_sign_convention = COMPRESSION_POSITIVE
```

O campo moderno `sigma_theta_compression_positive_Pa` deve permanecer
semanticamente fiel ao nome. Se uma fonte futura fornecer tensão com tração
positiva, a conversão de sinal deve ocorrer antes do gate, com `source` e
`reference_frame` preservados.

## O que pode ser implementado na próxima fase

A próxima fase pode implementar um guard sem ativar dispatch físico:

```text
PHASE11_10P_IMPLEMENT_SIGMATHETA_INITIAL_STATE_WIRING_GUARD
```

Esse guard deve validar campos, bloquear estados desconhecidos e registrar
status explícitos, mantendo `dispatch_allowed_next = false` até que uma fonte
real ou diagnóstica controlada seja conectada com testes.

## O que continua bloqueado

Dispatch físico de PKN ou PENNY_SHAPED permanece bloqueado até que sigma_theta inicial, semântica de pressão e convenção de sinal estejam definidos e implementados.

Continuam bloqueados:

- execução BUZ29-PENNY;
- validação física de fratura;
- equivalência com legado;
- runtime `SaltWallStressDiagnostics` como fonte default;
- uso de `sigma_theta = 0` ou `UNKNOWN` como fallback silencioso;
- comparação entre pressão absoluta e tensão incremental;
- comparação entre pressão incremental e tensão total.

## Status registrado

```text
PHASE11_10O_SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED
SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED
ELASTIC_INITIAL_WELLBORE_STATE_SELECTED_AS_PREFERRED_SOURCE
FRACTURE_GATE_BLOCKED_UNTIL_SIGMATHETA_INITIALIZED
PRESSURE_SIGMATHETA_COMPATIBILITY_REQUIRED
DISPATCH_REMAINS_BLOCKED
```
