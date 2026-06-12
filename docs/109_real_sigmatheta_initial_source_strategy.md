# Fase 11.11I — estrategia de fonte real para sigma-theta inicial

## Resumo executivo

A Fase 11.11I especifica a estrategia para obter
`sigma_theta_initial_compression_positive_Pa` fisicamente consistente para o
`SigmaThetaInitialStateGuard`.

Status:

```text
REAL_SIGMATHETA_INITIAL_SOURCE_STRATEGY_SPECIFIED
```

Esta fase nao implementa C++, nao habilita dispatch fisico, nao executa
BUZ29-PENNY e nao transforma `PENNY_SHAPED` em runtime fisico.

## Premissa t=0 LOT vs t=0 perfuracao

```text
t = 0 do LOT nao e t = 0 da perfuracao.
```

A estrategia primaria para sigma_theta_initial_compression_positive_Pa deve
representar o estado inicial pos-perfuracao, nao um estado nulo no inicio do
LOT.

O estado inicial do LOT deve representar a condicao da parede do poco depois da
perfuracao e antes do ensaio, ja incluindo a redistribuicao elastica inicial e,
em fases futuras, eventuais efeitos acoplados de sal, APB e fluencia.

## Fontes candidatas

| Fonte | Papel | Status |
|---|---|---|
| `ELASTIC_INITIAL_WELLBORE_STATE` | Fonte primaria recomendada | Primaria |
| `APB_SALT_COUPLED_STATE` | Fonte futura mais completa | Futuro |
| `LEGACY_DIAGNOSTIC_TRACE` | Evidencia historica e diagnostica | Nao validar fisicamente |
| `EXPLICIT_DIAGNOSTIC_INPUT` | Fallback controlado para testes | Fallback |
| `SYNTHETIC_FIXTURE` | Fallback de fixture para contrato | Fallback |
| `UNKNOWN` | Estado nao aceitavel para gate fisico | Bloqueado |

## Fonte primaria recomendada

```text
primary_source = ELASTIC_INITIAL_WELLBORE_STATE
```

Essa fonte deve fornecer tensao tangencial total na parede do poco, em
compressao positiva:

```text
sigma_theta_initial_compression_positive_Pa
state_time = POST_DRILLING_BEFORE_LOT
sign_convention = COMPRESSION_POSITIVE
reference_frame = WELLBORE_WALL_TOTAL_STRESS
```

## Fontes fallback

```text
fallback_sources = EXPLICIT_DIAGNOSTIC_INPUT, SYNTHETIC_FIXTURE
```

Essas fontes sao permitidas para fixtures e diagnosticos controlados. Elas nao
devem ser promovidas automaticamente a validacao fisica.

## Fontes apenas diagnosticas

```text
not_validation_sources = LEGACY_DIAGNOSTIC_TRACE
legacy_trace_validation_allowed = false
```

O trace legado pode explicar ou reproduzir uma decisao historica, mas nao deve
ser usado como fonte automatica de validacao fisica moderna.

## Convencao de sinal

A convencao preservada e compressao positiva:

```text
sign_convention = COMPRESSION_POSITIVE
```

## Referencial esperado

O referencial esperado e tensao total na parede do poco:

```text
reference_frame = WELLBORE_WALL_TOTAL_STRESS
pressure_reference = WELLBORE_PRESSURE
```

## Proxima fase recomendada

```text
PHASE11_11J_AUDIT_RUNTIME_SIGMATHETA_AND_PRESSURE_AVAILABILITY
```

A 11.11J deve auditar se o runtime real ja possui `sigma_theta_initial`,
`sigma_theta_current` e `wellbore_pressure` com semantica suficiente para
alimentar o gate.

## Resultado da auditoria 11.11J

A Fase 11.11J confirmou:

```text
sigma_theta_initial_runtime_available = false
sigma_theta_current_runtime_available = false
wellbore_pressure_runtime_available = true
runtime_real_wiring_allowed_next = false
```

Assim, a estrategia permanece especificada, mas ainda nao implementavel como
wiring fisico real.
## Fonte diagnóstica explícita adicionada na 11.11N

A 11.11N nao substitui a fonte fisica futura `ELASTIC_INITIAL_WELLBORE_STATE`.
Ela adiciona uma fonte diagnostica explicita para testes controlados:

```text
EXPLICIT_DIAGNOSTIC_INPUT
SYNTHETIC_FIXTURE
```

Ambas exigem:

```text
physically_validated = false
legacy_equivalent = false
runtime_dispatch_enabled = false
```
