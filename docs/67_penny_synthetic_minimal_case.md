# Fase 11.9A — caso sintético mínimo PennyShaped

## Resumo executivo

A Fase 11.9A adiciona um caso sintético mínimo para exercitar o contrato
diagnóstico `PennyShaped` sem promover o modelo a rota runtime oficial.

Status:

```text
PENNY_SYNTHETIC_CASE_CREATED
```

O caso é intencionalmente pequeno, em SI, e não passa pelo parser oficial do
`lot-sim`. Ele serve para verificação de contrato e documentação técnica.

## Arquivos

```text
cases/validation/non_pkn/penny_shaped_synthetic_minimal.yaml
tools/verify_phase11_9a_penny_synthetic_case.py
tests/python/test_verify_phase11_9a_penny_synthetic_case.py
```

## Entradas

O caso contém:

- `young_modulus_Pa`;
- `poisson_ratio`;
- `viscosity_Pa_min`;
- `flow_rate_m3_min`;
- `elapsed_since_opening_min`;
- `wellbore_pressure_Pa`;
- `sigma_theta_compression_positive_Pa`;
- `volume_multiplier`.

## Saídas verificadas

O verificador calcula:

```text
plane_strain_modulus_Pa
opening_m
radius_m
pressure_factor
fracture_volume_proxy_m3
```

## Caveat obrigatório

```text
Synthetic diagnostic case only. Not BUZ29 validation. Not legacy equivalence.
```

## Escopo preservado

Esta fase não altera schema oficial, parser, CLI, `PknModel`, `PknRunner`,
casos protegidos ou runtime `lot-pkn`.

## Próxima fase

```text
PHASE11_9B_BUZ29_PENNY_READINESS
```

A próxima fase deve avaliar se BUZ29 tem evidência suficiente para alimentar a
rota `PennyShaped`; a preferência continua sendo bloquear ou classificar como
parcial quando pressão, sigmaTheta, tempo e estado APB/sal não estiverem
completos.
