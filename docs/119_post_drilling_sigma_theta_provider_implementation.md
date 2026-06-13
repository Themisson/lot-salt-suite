# Fase C — PostDrillingSigmaThetaProvider

## Resumo executivo

A Fase C implementa `PostDrillingSigmaThetaProvider`, um componente C++
isolado para normalizar valores de sigma_theta pos-perfuracao antes de wiring
com o diagnostic pre-runner.

Status:

```text
POST_DRILLING_SIGMATHETA_PROVIDER_IMPLEMENTED
```

O provider nao habilita dispatch fisico, nao altera PKN, nao executa
BUZ29-PENNY e nao chama `PknModel`, `PknRunner` ou
`PennyShapedDiagnosticAdapter`.

## Fontes suportadas

| Fonte | Uso |
|---|---|
| `EXPLICIT_DIAGNOSTIC_INPUT` | entrada diagnostica controlada |
| `SYNTHETIC_FIXTURE` | fixture sintetico controlado |
| `ELASTIC_INITIAL_WELLBORE_STATE` | rota semi-fisica com caveat |
| `UNKNOWN` | rejeitada |

## Semantica fixa

```text
state_time = POST_DRILLING_BEFORE_LOT
sign_convention = COMPRESSION_POSITIVE
reference_frame = WELLBORE_WALL_TOTAL_STRESS
physically_validated = false
legacy_equivalent = false
```

## Regras implementadas

- Valores de sigma_theta devem ser finitos e positivos.
- `wellbore_pressure_Pa` e `tensile_strength_Pa` devem ser finitos e nao negativos.
- `physically_validated=true` e rejeitado.
- `legacy_equivalent=true` e rejeitado.
- A fonte `UNKNOWN` e rejeitada.
- `ELASTIC_INITIAL_WELLBORE_STATE` recebe caveat
  `SEMI_PHYSICAL_ELASTIC_APPROXIMATION`.

## Caveats

O provider ainda nao esta conectado ao `FractureGateDiagnosticPreRunner`; isso
fica para a Fase D. A rota elastica inicial e apenas semi-fisica nesta etapa e
nao constitui validacao fisica.

## Proxima fase

```text
MASTER_PHASE_D_WIRE_SIGMATHETA_PROVIDER_TO_PRE_RUNNER
```
