# 08 — Problemas Conhecidos e Riscos

**Status:** Ativo | **Última atualização:** 2026-06-01

> Este arquivo deve ser atualizado ANTES de qualquer mudança de formulação ou convenção.
> Toda refatoração deve ser comparada com esta lista antes de ser aprovada.

## Problemas de nomenclatura

| ID | Problema | Impacto | Mitigação |
|----|---------|---------|-----------|
| N01 | Diretório físico é `legance/` mas docs dizem `legacy/` | Médio | Criar `legacy/` organizacional; nunca renomear `legance/` |

## Parâmetros hard-coded identificados

| ID | Parâmetro | Valor | Arquivo legado | Ação necessária |
|----|-----------|-------|---------------|-----------------|
| H01 | `dt` (passo temporal) | 1.0 h | `LOT_APB_v5/main/main.cpp` | Mover para YAML `time.dt_h` |
| H02 | `ctoldP` (tolerância pressão) | 1.0 bar | `LOT_APB_v5/main/main.cpp` | Mover para YAML `time.solver.tol_pressure_bar` |
| H03 | `tolEq` (tolerância equilíbrio) | 1E-8 | `LOT_APB_v5/main/main.cpp` | Mover para YAML `time.solver.tol_eq` |
| H04 | `tac` (tempo de estabilização) | 80 sem × 7d × 24h | `LOT_APB_v5/main/main.cpp` | Mover para YAML `time.solver.stabilization_h` |
| H05 | `e0` da Halita | 1.8792e-6 /h (→ /min) | `LOTTeste.cpp` | Verificar unidades; mover para YAML `rocks[].creep.e0_per_h` |
| H06 | `e0` da Carnalita | 1.581e-4 /h (→ /min) | `LOTTeste.cpp` | Idem acima |
| H07 | Viscosidade fluido LOT | 3.0 cP | `8-BUZ-67D-*.cpp` | Converter para Pa·s no parser |
| H08 | Geometria LOT | `"elliptical"` | `8-BUZ-67D-*.cpp` | Mover para YAML `lot.fracture.geometry` |

## Riscos de formulação

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|--------------|---------|-----------|
| R01 | Convenção de sinais não documentada (compressão +/-) | Alta | Crítico | Auditar via `/formulation-audit` antes de implementar `lot/` e `salt/` |
| R02 | Unidades mistas nos main.cpp (PPG, pol, Pa, cP) | Alta | Alto | Módulo `units/` centralizado; conversão obrigatória no parser |
| R03 | SESTSAL possivelmente divergente entre LOT_Tese e LOT_APB_v5 | Média | Alto | Comparar diretamente os dois arquivos `sestsal/material.cpp` |
| R04 | `APB1da` monolítica: impossível testar módulos isoladamente | Alta | Alto | Fase 7 dedicada à decomposição |
| R05 | Coeficientes de fluência em h⁻¹ convertidos para min⁻¹ inline no legado | Média | Alto | Verificar em cada main; converter para SI (s⁻¹) no parser |
| R06 | Acoplamento LOT-sal via tensão: convenção de tensão efetiva × total | Alta | Crítico | Documentar em `docs/13_coupling_lot_apb_salt.md` antes de implementar |

## Divergências identificadas entre legados

| ID | Divergência | LOT_Tese | LOT_APB_v5 | Status |
|----|------------|----------|------------|--------|
| D01 | SESTSAL — versão/parâmetros | `include/sestsal/` | `include/sestsal/` | Não verificado |
| D02 | Solver parâmetros | Hard-coded no main | Maioria no JSON; alguns hard-coded | H01-H04 acima |
| D03 | Geometrias LOT | 4 variantes em arquivos separados | Não identificado | Verificar no JSON |

## Itens a documentar antes de implementar

Os seguintes pontos devem ser esclarecidos via skill `/formulation-audit`
ANTES de iniciar a Fase 7 (refatoração C++):

- [ ] Convenção de sinais de tensão (compressão positiva ou negativa)
- [ ] Definição de tensão efetiva na interface sal-LOT
- [ ] Conversão de deformação viscosa para variação de volume anular
- [ ] Critério de convergência do loop LOT-sal (δP ou δε?)
- [ ] Tratamento de temperatura na lei de fluência (Kelvin ou Celsius no legado?)
