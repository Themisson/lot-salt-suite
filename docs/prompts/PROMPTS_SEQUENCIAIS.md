# Prompts sequenciais sugeridos

## 1. Congelar legados

```text
Crie `legacy/README.md` explicando que `LOT_Tese` e `LOT_APB_v5` são referências congeladas. Não altere código legado. Liste como cada pasta será usada para regressão.
```

## 2. Criar baselines

```text
Identifique os casos executáveis mínimos em `legacy/LOT_APB_v5` e `legacy/LOT_Tese`. Crie um plano para rodar esses casos e salvar saídas em `tests/baselines/`. Não modifique solver.
```

## 3. Definir schema YAML

```text
Com base nos JSONs de `LOT_APB_v5` e nos YAMLs de `saltcreep`, crie `docs/05_input_case_schema.md` e `schemas/lot_salt_case.schema.yaml`. O schema deve suportar LOT, APB, sal, térmico, leakoff, leakage e saída.
```

## 4. Criar CLI inicial

```text
Implemente um executável `lot-sim` com subcomandos `run`, `inspect`, `validate` e `migrate-json`. Inicialmente, `run` pode apenas carregar o YAML e imprimir resumo do caso. Adicione testes do parser.
```

## 5. Migrar JSON LOT_APB_v5

```text
Crie `tools/migrate_lot_apb_json_to_yaml.py` para converter um JSON de `legacy/LOT_APB_v5` em YAML do novo schema. Teste com `SCORE-MRO-28_input.json`.
```

## 6. Migrar um main da tese

```text
Analise `legacy/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-circular.cpp` e gere manualmente um YAML equivalente em `cases/lot_tese_migrated/`. Não tente migrar todos os casos ainda.
```

## 7. Separar APB1da

```text
Use a skill de C++ refactor. Proponha a decomposição de `APB1da` em `APBSolver`, `PressureBalance`, `VolumeBalance`, `LeakoffModel`, `LeakageModel`, `ResultWriter` e `TimeStepper`. Não implemente tudo. Faça apenas o primeiro módulo com teste.
```

## 8. Criar adapter para sal

```text
Crie a interface `SaltCreepAdapter` para consumir modelos do `external/saltcreep` sem acoplar o LOT diretamente a uma implementação constitutiva específica. Comece apenas com um caso salt-only minimal.
```

## 9. LOT-salt mínimo

```text
Implemente um caso mínimo em que pressão do LOT gera estado de tensão na parede do poço, chama o adapter de sal, calcula deslocamento/variação volumétrica e corrige pressão no próximo passo. Validar contra caso simplificado.
```

## 10. Pós-processamento

```text
Crie pacote `post/lotsaltpost` para ler resultados, comparar baselines, gerar gráficos de pressão-tempo, pressão-volume, leakoff, deslocamento radial e relatório HTML.
```
