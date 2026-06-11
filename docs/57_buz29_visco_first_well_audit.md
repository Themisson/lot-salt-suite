# BUZ29-VISCO first-well audit (Fase 11.6A)

## Resumo executivo

A Fase 11.6A auditou `BUZ29-VISCO-first-well.cpp` em modo somente leitura para
decidir se o caso pode entrar diretamente na rota `modern-refined` LOT/PKN.

Resultado:

```text
source_status = BUZ29_VISCO_FIRST_WELL_SOURCE_FOUND
primary_classification = BUZ29_VISCO_FIRST_WELL_NOT_PKN
future_yaml_readiness = BUZ29_VISCO_FIRST_WELL_MODERN_YAML_NOT_READY
recommended_next_phase = PHASE11_6B_NON_PKN_ROADMAP
```

O arquivo existe e possui parâmetros úteis de fluido, tempo, camadas, rochas e
saída. Porém, a linha PKN está comentada e o modelo LOT ativo é
`penny-shaped`. Portanto, criar um YAML moderno PKN nesta fase exigiria forçar
uma adaptação não justificada.

## Fonte primária

```text
legance/LOT_Tese/BUZ29-VISCO-first-well.cpp
```

A fase não modificou `legance/` e não executou instrumentação no legado.

## Achados principais

| Item | Valor auditado | Status |
|---|---|---|
| Fonte BUZ29-VISCO-first-well | presente | `EXTRACTED` |
| Modelo LOT ativo | `penny-shaped` | `BUZ29_VISCO_FIRST_WELL_NOT_PKN` |
| Evidência PKN | linha `setLeakoffProps(..., "pkn")` comentada | `COMMENT_ONLY` |
| Fluido principal | `setPFluid(11., 8E-4, 6.40E-10)` | `EXTRACTED` |
| Simulação | `APB1da simulation(0.1, 0.1, 1E-8, 13., 0, false, true, 6, 0.4)` | `EXTRACTED` |
| Vazão | `Q = 0.4`, `idQ = 6` | `EXTRACTED_FROM_SIMULATION_TUPLE` |
| Tempo total | `13 min` | `EXTRACTED_FROM_SIMULATION_TUPLE` |
| Intervalo principal | `2061 m` a `3506 m` | `EXTRACTED` |
| Saída legada | `results/7-BUZ-29D-RJS10_PENNY-SHAPED.dat` | `EXTRACTED` |
| Conversões de creep | fatores `* 60` e comentários de minuto/hora | `EXTRACTED` |

## Candidatos relacionados

O repositório legado também contém fontes BUZ29 com `circular`/Zamora e saídas
com `PKN` no nome. Esses artefatos não bastam para criar caso moderno PKN:

- fontes ativas auditadas usam modelos não-PKN ou permanecem ambíguas;
- saídas `*.dat` com `PKN` são output-only sem contrato de fonte completo;
- a rota `modern-refined` atual suporta LOT/PKN, não penny-shaped/KGD/Zamora.

## Por que o YAML moderno não foi criado

O caso `BUZ29-VISCO-first-well.cpp` não está pronto para virar
`cases/validation/buz29...modern_refined.yaml` porque o modelo ativo não é PKN.
Converter esse caso para PKN agora misturaria hipóteses de modelo e poderia
transformar uma auditoria documental em uma calibração implícita.

## Gate

```text
BUZ29_VISCO_FIRST_WELL_AUDITED
BUZ29_VISCO_FIRST_WELL_NOT_PKN
BUZ29_VISCO_FIRST_WELL_MODERN_YAML_NOT_READY
NEXT_PHASE_NON_PKN_ROADMAP
```

## Próxima fase recomendada

A próxima fase deve ser a 11.6B: consolidar um roadmap não-PKN para decidir se
o projeto deve priorizar penny-shaped, KGD/circular, Zamora/compositional fluid
ou manter BUZ29 apenas como referência legada por enquanto.

## Caveats

- Esta fase não valida pressão, abertura, dano ou ruptura.
- Esta fase não compara BUZ29 com outputs modernos.
- Esta fase não altera `legance/`, C++, parser, schemas ou casos protegidos.
- PKN output-only não é evidência suficiente de readiness para YAML moderno.
