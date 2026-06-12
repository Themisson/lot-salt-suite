# Fase 11.11B — comparacao PKN com diagnostico disabled/enabled

## Resumo

A Fase 11.11B compara os outputs fisicos LOT-PKN com o diagnostico
pre-runner desabilitado e habilitado de forma opt-in. O objetivo e confirmar
que `result.json` e `timeseries.csv` permanecem identicos, enquanto
`diagnostic_fracture_gate.json` e produzido apenas quando o diagnostico esta
explicitamente habilitado.

Esta fase nao valida fisicamente BUZ29, nao habilita dispatch fisico, nao chama
o adapter PennyShaped como runtime fisico e nao declara equivalencia com legado.

## Casos comparados

Os casos protegidos sao executados por copia temporaria:

```text
cases/validation/lot_pkn_minimal.yaml
cases/validation/lot_pkn_with_leakoff.yaml
```

Para cada caso, a ferramenta cria:

```text
disabled: YAML original copiado sem bloco diagnostico
enabled : YAML copiado com lot.fracture.fracture_gate_diagnostics opt-in
```

O bloco injetado na copia habilitada e:

```yaml
fracture_gate_diagnostics:
  enabled: true
  mode: pre_runner
  dispatch_runtime_enabled: false
```

## Contrato de comparacao

Arquivos fisicos comparados byte a byte:

```text
result.json
timeseries.csv
```

Arquivo diagnostico esperado apenas no run habilitado:

```text
diagnostic_fracture_gate.json
```

Classificacao esperada:

```text
PKN_OUTPUTS_UNCHANGED_WITH_DIAGNOSTICS
```

Marcadores obrigatorios:

```text
physical_outputs_identical = true
diagnostic_output_isolated = true
pkn_behavior_changed = false
runtime_physical_dispatch_enabled = false
buz29_execution_allowed = false
```

## Ferramenta

```text
tools/compare_phase11_11b_pkn_outputs_with_diagnostics.py
```

Uso real:

```powershell
python tools/compare_phase11_11b_pkn_outputs_with_diagnostics.py `
  --lot-sim build/Debug/lot-sim.exe `
  --output-json results/comparison/phase11_11b/pkn_diagnostic_regression.json `
  --output-md results/comparison/phase11_11b/pkn_diagnostic_regression.md
```

Os testes unitarios usam `--fixture-root` com pares sinteticos pequenos para
evitar execucao de simulacoes dentro do pytest.

## Caveats

- A comparacao cobre apenas `result.json` e `timeseries.csv`.
- A saida diagnostica permanece isolada do resultado fisico.
- `dispatch_runtime_enabled` continua proibido.
- BUZ29-PENNY nao e executado.
- Esta fase e regressao de nao alteracao PKN, nao validacao fisica.

## Proxima fase

```text
PHASE11_11C_DECIDE_RUNTIME_WIRING_INTEGRATION_READINESS
```

## Atualizacao 11.11C

A Fase 11.11C usa esta comparacao como evidencia para classificar:

```text
RUNTIME_WIRING_READY_FOR_LIMITED_GATE_SPEC
```

Essa classificacao autoriza apenas a especificacao da integracao limitada na
11.11D. Ela nao habilita dispatch fisico e nao executa BUZ29-PENNY.
A comparacao da Fase 11.11B permanece a regressao fisica de referencia para a
11.11E. A ferramenta aceita `--diagnostic-mode limited_gate` para provar que a
integracao limitada tambem preserva `result.json` e `timeseries.csv` enquanto
mantem `diagnostic_fracture_gate.json` isolado.

```text
PKN_OUTPUTS_UNCHANGED_WITH_LIMITED_GATE
```
