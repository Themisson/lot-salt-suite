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

## Formato de saída CSV

`
time_h, annular_A_pressure_Pa, annular_B_pressure_Pa,
lot_pressure_Pa, lot_volume_m3, salt_closure_mm, ...
`
"@

System.Collections.Hashtable["06_validation_plan.md"] = @"
# 06 — Plano de Validação

**Status:** Planejado | **Última atualização:** 2026-06-01

## Sequência V0-V9

| Nível | Teste | Critério |
|-------|-------|----------|
| V0 | Parser YAML: carregar e imprimir caso | Zero erros de parsing |
| V1 | Fluido isolado: PVT analítico | Erro < 0.01% |
| V2 | Elástico isolado: solução de Lamé | Erro L2 < 1e-6 |
| V3 | LOT simples sem sal (LOTTeste) | Curva P×V dentro de 1% do legado |
| V4 | APB simples sem sal (BUZ29-VISCO-DELL) | ΔP máx dentro de 1% |
| V5 | Sal isolado (halita, mecanismo duplo) | Erro < 0.1% vs saltcreep |
| V6 | LOT + sal (8-BUZ-67D elliptical) | Erro < 1% vs LOT_Tese |
| V7 | APB + sal (BUZ29 cenário 1) | Erro < 1% vs LOT_APB_v5 |
| V8 | Caso acoplado completo | Comparação com melhor referência |
| V9 | Regressão automática (suíte completa) | 100% dentro de tolerância |

## Status atual

| Nível | Status |
|-------|--------|
| V0-V9 | Não executado |

> **REGRA:** Nunca atualizar status para 'executado' sem resultados reais documentados
> em docs/12_validation_results.md.

## Captura de baselines (pré-requisito)

Antes de V3-V7, executar os legados e salvar em `tests/baselines/`:

`ash
# Compilar e executar LOT_APB_v5
cd legance/LOT_APB_v5 && make main
./main SCORE-MRO-28_input.json
# Salvar output como tests/baselines/apbv5_score_mro_28.json
`
"@

System.Collections.Hashtable["07_target_architecture.md"] = @"
# 07 — Arquitetura-Alvo

**Status:** Planejado | **Última atualização:** 2026-06-01

## Diagrama de módulos

`
apps/lot-sim.cpp
    └── include/cli/         (subcomandos: run, validate, inspect, migrate)
         └── include/io/     (parser YAML+JSON → CaseData)
              └── include/units/ (conversão de unidades → SI)
                   └── Módulos físicos:
                        ├── include/wellbore/   (geometria)
                        ├── include/fluids/     (PVT)
                        ├── include/thermal/    (T(z))
                        ├── include/rocks/      (elástico)
                        ├── include/salt/       (SaltCreepInterface + adapters)
                        ├── include/lot/        (fratura, leakoff)
                        ├── include/apb/        (balanço anular)
                        ├── include/geomechanics/ (tensão geostática)
                        └── include/coupling/   (orquestrador)
`

## Interfaces plugáveis (padrão do saltcreep)

1. `SaltCreepInterface` — modelo constitutivo de sal
2. `ThermalFieldInterface` — campo de temperatura (futuro)
3. `FractureGeometryInterface` — geometrias de LOT

## Regra de dependência

- `core/` ← todos os módulos dependem
- `units/` ← `io/` depende
- `io/` ← `cli/` depende
- Módulos físicos NÃO dependem entre si diretamente — somente via `coupling/`
- `coupling/` orquestra todos os módulos físicos

## Adapter para saltcreep

`
include/salt/
├── SaltCreepInterface.hpp         (interface abstrata)
├── SaltCreepSaltcreepAdapter.hpp  (usa external/saltcreep)
└── SaltCreepSESTSALAdapter.hpp    (usa SESTSAL legado)
`
"@

System.Collections.Hashtable["08_known_issues.md"] = @"
# 08 — Problemas Conhecidos e Riscos

**Status:** Ativo | **Última atualização:** 2026-06-01

> Este arquivo deve ser atualizado ANTES de qualquer mudança de formulação ou convenção.

## Problemas de nomenclatura

| ID | Problema | Impacto | Mitigação |
|----|---------|---------|-----------|
| N01 | Diretório físico é `legance/` mas docs dizem `legacy/` | Médio | Criar `legacy/` organizacional; não renomear `legance/` |

## Parâmetros hard-coded identificados

| ID | Parâmetro | Valor | Arquivo legado | Impacto na migração |
|----|-----------|-------|---------------|-------------------|
| H01 | dt | 1.0 h | `LOT_APB_v5/main/main.cpp` | Mover para YAML |
| H02 | ctoldP | 1.0 bar | `LOT_APB_v5/main/main.cpp` | Mover para YAML |
| H03 | tac | 80 sem × 7d × 24h | `LOT_APB_v5/main/main.cpp` | Mover para YAML |
| H04 | e0 Halita | 1.8792e-6/h | `LOTTeste.cpp` | Verificar unidades (h vs min) |
| H05 | LOT fluid visc | 3.0 cP | `8-BUZ-67D-*.cpp` | Converter para Pa·s |

## Riscos de formulação

| ID | Risco | Probabilidade | Mitigação |
|----|-------|--------------|-----------|
| R01 | Convenção de sinais não documentada (compressão +/-) | Alta | Auditar via `/formulation-audit` |
| R02 | Unidades mistas nos main.cpp (PPG, pol, Pa, cP) | Alta | Módulo `units/` centralizado |
| R03 | SESTSAL duplicado entre LOT_Tese e LOT_APB_v5 | Alta | Usar interface/adapter |
| R04 | APB1da monolítica: sem separação de responsabilidades | Alta | Fase 7 dedicada |
| R05 | Coeficientes de fluência em h⁻¹ convertidos para min⁻¹ inline | Média | Verificar em cada main |

## Divergências identificadas entre legados

| ID | Divergência | LOT_Tese | LOT_APB_v5 |
|----|------------|----------|------------|
| D01 | SESTSAL (possível versão diferente) | src/sestsal/ | src/sestsal/ |
| D02 | Parâmetros solver | Hard-coded no main | Maioria no JSON |
