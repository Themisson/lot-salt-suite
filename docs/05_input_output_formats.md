# 05 — Formatos de Entrada e Saída

**Status:** Planejado | **Última atualização:** 2026-06-01

## Formato principal: YAML

Schema completo definido em `schemas/lot_case.schema.yaml`.

Ver exemplo anotado no [index.html](index.html) seção #input.

### Seções do YAML de caso

`yaml
metadata:    # Nome, versão, modo, fonte legada
units:       # Sistema de unidades de entrada (convertido para SI)
wellbore:    # Geometria de poço
casings:     # Revestimentos metálicos
cements:     # Cimentações
annulars:    # Anulares selados
open_hole:   # Intervalo aberto
fluids:      # Propriedades PVT
temperature: # Perfil T(z)
geostatic:   # Tensão geostática inicial
layers:      # Camadas litológicas
rocks:       # Propriedades de rocha por material
lot:         # Parâmetros do LOT
apb:         # Parâmetros do APB
time:        # Configuração temporal e solver
output:      # Configuração de saída
postprocess: # Script de pós-processamento
`

## Formato legado: JSON (LOT_APB_v5)

Campos principais: `id_operation`, `duration`, `duration_unit`, `airgap`,
`temperature`, `solids`, `fluids`, `rocks`, `layers`, `top_packer`,
`depressurization`, `salt_creep_enabled`.

Mapeamento JSON → YAML em docs/09_migration_plan.md.

## Contrato YAML LOT/PKN (Fase 6.2)

Casos LOT/PKN usam `simulation.mode: lot-pkn` e mantem `metadata.mode: lot-pkn`
para compatibilidade com o parser atual.

```yaml
simulation:
  mode: lot-pkn

lot:
  enabled: true
  shoe_depth_m: 3000.0
  model: pkn
  injection:
    rate:
      value: 0.5
      unit: bbl_min
    schedule:
      total_time: {value: 12.5, unit: min}
      dt: {value: 0.5, unit: min}
      accommodation_time: {value: 9.5, unit: min}
  fracture:
    geometry: pkn
    fluid_viscosity_cP: 3.0
    height: {value: 20.0, unit: m}
    initial_width: {value: 0.0, unit: m}
    breakdown:
      method: pressure_threshold
      pressure: {value: 45.0e6, unit: Pa}
  leakoff:
    enabled: true
    model: synthetic_constant
    coefficient_m_sqrt_s: 1.0e-6
  detection:
    method: derivative_drop
```

Unidades aceitas no contrato:

| Quantidade | Unidades aceitas | Unidade interna |
|------------|------------------|-----------------|
| Taxa | `m3_s`, `m3_min`, `m3_h`, `bbl_min`, `bpm` | m3/s |
| Tempo | `s`, `min`, `h` | s |
| Comprimento | `m`, `in` | m |
| Pressao | `Pa`, `bar`, `psi` | Pa |

O caso migrado `cases/lot_tese_migrated/buz67d_pkn.yaml` e sintaticamente
validavel, mas campos marcados como `R09_PENDING_REVIEW` nao podem ser usados
como baseline numerico enquanto R09 estiver aberto.

## Saída moderna LOT/PKN (Fase 6.5)

O comando:

```bash
lot-sim run --case cases/validation/lot_pkn_minimal.yaml --mode lot-pkn --output results/lot_pkn_minimal
```

gera dois arquivos modernos e reproduzíveis no diretório informado. A pasta
`results/` permanece ignorada pelo git.

### `timeseries.csv`

```text
time_s,injected_volume_m3,fracture_length_m,fracture_width_m,fracture_volume_m3,leakoff_volume_m3,net_pressure_Pa
```

Todas as colunas estão em SI. O CSV contém a série temporal completa calculada
por `PknModel::simulate`.

### `result.json`

```json
{
  "metadata": {
    "case_id": "lot_pkn_minimal_validation",
    "mode": "lot-pkn",
    "validation_status": "synthetic_modern_no_legacy_regression"
  },
  "summary": {
    "final_time_s": 600.0,
    "final_injected_volume_m3": 0.3,
    "final_fracture_length_m": 0.0,
    "final_fracture_width_m": 0.0,
    "final_fracture_volume_m3": 0.0,
    "final_leakoff_volume_m3": 0.0,
    "final_net_pressure_Pa": 0.0
  },
  "warnings": [
    "No numerical regression against legacy was performed.",
    "R09 remains blocker for legacy comparison."
  ]
}
```

O JSON guarda apenas o resumo final; a série completa fica no CSV. O status
`synthetic_modern_no_legacy_regression` é deliberado: esta saída não é
validação contra legado.

## Saída CSV geral futura

Os modos APB, sal e acoplados ainda não têm writer moderno nesta fase. Quando
forem implementados, os CSVs devem seguir a mesma regra da saída LOT/PKN:
colunas nomeadas com unidade explícita, valores em SI e ausência de `NaN`/`Inf`.

Exemplo de campos esperados para fases futuras:

```text
time_h,annular_A_pressure_Pa,annular_B_pressure_Pa,lot_pressure_Pa,lot_volume_m3,salt_closure_mm
```
