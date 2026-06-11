# BUZ-29D legacy audit

## Resumo executivo

A Fase 10.29C auditou o material BUZ-29D em `legance/LOT_Tese/` em modo
read-only. O resultado é:

```text
buz29d_source_status = BUZ29D_MODERN_YAML_NOT_READY
model_status = BUZ29D_NOT_PKN
future_yaml_readiness = BUZ29D_MODERN_YAML_NOT_READY
```

Há fontes, scripts e saídas BUZ-29D no legado, inclusive saídas com PKN no nome.
Ainda assim, os fontes principais auditados não definem um caso PKN moderno
pronto. Os candidatos ativos observados usam `penny-shaped`, `circular`/Zamora
ou ficam ambíguos. Portanto, a fase não cria YAML moderno.

## Arquivos encontrados

| Arquivo | Tipo | Modelo observado | Status |
|---|---|---|---|
| `legance/LOT_Tese/BUZ29-VISCO-first-well.cpp` | fonte | `penny-shaped` ativo | `EXTRACTED_NON_PKN` |
| `legance/LOT_Tese/BUZ29-CENÁRIO1 -PRESC.cpp` | fonte | `penny-shaped` ativo | `EXTRACTED_NON_PKN` |
| `legance/LOT_Tese/BUZ29-CENÁRIO1 -ZAMORA.cpp` | fonte | `circular`/Zamora | `EXTRACTED_NON_PKN` |
| `legance/LOT_Tese/BUZ29-CENÁRIO2-PRESC.cpp` | fonte | `circular` ativo | `EXTRACTED_NON_PKN` |
| `legance/LOT_Tese/BUZ29-CENÁRIO2 -ZAMORA.cpp` | fonte | `circular`/Zamora | `EXTRACTED_NON_PKN` |
| `legance/LOT_Tese/BUZ29-VISCO-ZAMORA.cpp` | fonte | `circular`/Zamora | `EXTRACTED_NON_PKN` |
| `legance/LOT_Tese/BUZ29-VISCO-DELL_PC_APTO.cpp` | fonte | modelo não declarado no gate | `AMBIGUOUS` |
| `legance/LOT_Tese/results/7-BUZ-29D-RJS10_PKN.dat` | saída | PKN no nome | `OUTPUT_ONLY` |
| `legance/LOT_Tese/results/7-BUZ-29D-RJS10_Test-PKN.dat` | saída | PKN no nome | `OUTPUT_ONLY` |

## Modelos identificados

Os candidatos BUZ-29D ativos não estão prontos para o runner moderno PKN:

```text
penny-shaped: observado em BUZ29-VISCO-first-well.cpp e CENÁRIO1-PRESC
circular/KGD: observado nos cenários Zamora e CENÁRIO2-PRESC
PKN: aparece em linhas comentadas e em nomes de saída, mas não como fonte auditado pronto
```

Esse resultado mantém BUZ-29D fora da rota `modern-refined` por enquanto.

## Parâmetros extraídos

O candidato principal auditado contém campos úteis, mas associados a modelo não
PKN:

| Parâmetro | Valor observado | Unidade | Status |
|---|---|---|---|
| fluido | `setPFluid(11., 8E-4, 6.40E-10)` ou variantes `6.67E-10` | ppg, 1/degC, 1/Pa | `EXTRACTED` |
| vazão | `Q = 0.4` com `idQ = 6` | bbl/min legado convertido por regra histórica | `EXTRACTED` |
| tempo total | `tend = 13` ou `15` | min | `EXTRACTED` |
| dt | `0.1` ou `0.01` | min | `EXTRACTED` |
| profundidade inicial/seabed | `2061` ou `2206` | m | `EXTRACTED` |
| intervalo salino | exemplos em `mdepths` até `3506` ou `3332.95` | m | `EXTRACTED` |
| modelo LOT | `penny-shaped`/`circular` ativos | n/a | `EXTRACTED_NON_PKN` |
| saída PKN | `.dat` com PKN no nome | n/a | `OUTPUT_ONLY` |

## Campos ausentes

Para criar um YAML moderno BUZ-29D `modern-refined`, ainda faltam:

- fonte PKN ativo rastreável, ou justificativa técnica para converter saída PKN
  legada em caso moderno;
- definição inequívoca de modelo de fratura que o runner moderno suporta;
- mapeamento completo de geometria/anular para `CaseData`;
- confirmação de schedule, shut-in e pressão inicial no mesmo contrato;
- critério de compliance/sink/sigmaTheta compatível com o estado moderno;
- decisão se Zamora deve permanecer fora da fase, como exigido pelas restrições.

## Por que ainda não virou YAML moderno

Criar `cases/validation/buz29d_pkn_modern_refined.yaml` nesta fase exigiria
inventar ou inferir parâmetros críticos a partir de saídas e fontes não-PKN.
Isso violaria o contrato metodológico das fases 10.28-10.29:

```text
Não inventar dados.
Não forçar adaptação de caso não-PKN.
Não misturar legacy-equivalence com modern-refined.
```

## Possíveis rotas

| Rota | Condição | Status |
|---|---|---|
| PKN modern-refined | localizar fonte PKN ativo completo ou auditar proveniência de `7-BUZ-29D-RJS10_PKN.dat` | `FUTURE_WORK` |
| KGD/penny future work | implementar suporte moderno não-PKN com fase própria | `FUTURE_WORK` |
| legacy-only reference | usar BUZ-29D apenas como referência documental/legada | `AVAILABLE_NOW` |

## Próxima fase recomendada

A próxima fase não deve criar YAML BUZ-29D ainda. As opções seguras são:

1. continuar refinando infraestrutura `modern-refined` com BUZ-67D e o runner
   genérico;
2. abrir uma fase específica para auditar a proveniência das saídas PKN
   `7-BUZ-29D-RJS10_PKN.dat`;
3. planejar suporte moderno para KGD/penny-shaped apenas se esses modelos
   entrarem no escopo científico do projeto.

## Caveat

Esta auditoria é estrutural e documental. Ela não valida equivalência física,
não compara curvas de pressão BUZ-29D e não modifica `legance/`.
