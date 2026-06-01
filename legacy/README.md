# legacy/ — Código Legado Congelado

Este diretório é a referência para os códigos legados do projeto.
O código-fonte físico está em `legance/` (herança histórica de nomenclatura).

## Conteúdo

| Diretório | Localização física | Descrição |
|-----------|-------------------|-----------|
| `LOT_Tese/` | `../legance/LOT_Tese/` | Código C++ usado na tese. 13+ arquivos main de caso. |
| `LOT_APB_v5/` | `../legance/LOT_APB_v5/` | Versão com entrada JSON. 1 main + ~10 JSONs. |

## Regras invioláveis

1. **NUNCA editar** qualquer arquivo nestes diretórios.
2. **NUNCA apagar** resultados ou arquivos de entrada.
3. **NUNCA recompilar** sem documentar a versão do compilador usada.
4. **SEMPRE usar** estes arquivos como referência de leitura somente.

## Como usar os legados

### Para extrair parâmetros físicos

```bash
# Ler apenas (nunca editar)
cat legance/LOT_Tese/LOTTeste.cpp
cat legance/LOT_APB_v5/SCORE-MRO-28_input.json
```

### Para criar baselines

```bash
# Ver docs/06_validation_plan.md para procedimento
# Resultados salvos em tests/baselines/ (imutáveis)
```

### Para migrar um caso legado para YAML

```bash
# Usar ferramenta de migração (não modificar o legado)
python tools/migrate_lot_tese_cpp_case.py \
    legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-elliptical.cpp \
    cases/lot_tese_migrated/8_buz_67d_elliptical.yaml

python tools/migrate_lot_apb_json_to_yaml.py \
    legance/LOT_APB_v5/SCORE-MRO-28_input.json \
    cases/lot_apb_v5_migrated/score_mro_28.yaml
```

## Inventário resumido

### LOT_Tese — arquivos main identificados

| Arquivo | Tipo |
|---------|------|
| `LOTTeste.cpp` | LOT simples (2 anulares) |
| `8-BUZ-67D-RJS-VISCO.cpp` | LOT+APB+Sal — caso chave da tese |
| `8-BUZ-67D-RJS-VISCO-FULL-3rd-well.cpp` | LOT+APB+Sal — poço 3 completo |
| `9-BUZ-39DA-RJS-VISCO.cpp` | LOT+APB+Sal — 3 anulares |
| `9-BUZ-39DA-RJS-VISCO-2.cpp` | Variação do acima |
| `7-BUZ-60D-RJS-VISCO-2nd-Well.cpp` | LOT+APB — poço 2 |
| `BUZ29-VISCO-DELL_PC_APTO.cpp` | APB+Sal — validação |
| `BUZ29-VISCO-ZAMORA.cpp` | APB+Sal+Stress (modelo Zamora) |
| `BUZ29-VISCO-first-well.cpp` | APB+Sal — poço 1 |
| `BUZ29-CENÁRIO1-PRESC.cpp` | APB+Sal — cenário 1 prescrito |
| `BUZ29-CENÁRIO1-ZAMORA.cpp` | APB+Sal — cenário 1 Zamora |
| `BUZ29-CENÁRIO2-PRESC.cpp` | APB+Sal — cenário 2 prescrito |
| `BUZ29-CENÁRIO2-ZAMORA.cpp` | APB+Sal — cenário 2 Zamora |
| `main/8-BUZ-67D-*-circular.cpp` | LOT geometria circular |
| `main/8-BUZ-67D-*-elliptical.cpp` | LOT geometria elíptica |
| `main/8-BUZ-67D-*-penny-shaped.cpp` | LOT geometria penny-shaped |
| `main/8-BUZ-67D-*-pkn.cpp` | LOT geometria PKN |

### LOT_APB_v5 — arquivos JSON identificados

| Arquivo | Tipo |
|---------|------|
| `SCORE-MRO-28_input.json` | Caso completo (~33000 min) |
| `SCORE-MRO-28_output.json` | Resultado correspondente |
| `SCORE-MRO-28_original_input.json` | Versão original (referência) |
| `SCORE-MRO-28_elastic_input.json` | Versão sem sal (elástico puro) |
| `SCORE-MRO-28_Ev_temp_input.json` | Com evolução térmica |
| `MRO-28_min_times_input.json` | Versão reduzida (300 min) para testes rápidos |

## Referência para documentação

Ver `docs/01_repository_inventory.md` para inventário completo.
Ver `docs/09_migration_plan.md` para plano detalhado de migração.
