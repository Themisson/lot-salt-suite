# Prompt mestre para Claude Code

Você está atuando como orquestrador técnico de um projeto científico em C++/Python para integração de LOT, APB e fluência de sal.

## Contexto

Existem três bases principais:

1. `legacy/LOT_Tese/`: versão da tese, com muitos arquivos `main` específicos de caso. Esses arquivos embutem dados de poço, fluido, rocha, temperatura, LOT e pós-processamento diretamente em C++.
2. `legacy/LOT_APB_v5/`: versão mais madura, com entrada JSON via `LoadModel`, exportação JSON e classes APB/fluido/rocha/sólidos/temperatura. Ainda contém parâmetros hard-coded no `main` e concentração excessiva de responsabilidades em `APB1da`.
3. `external/saltcreep/`: repositório moderno com YAML, `CaseParser`, modelos constitutivos de sal, elementos axissimétricos, térmico, testes e pós-processamento `saltpost`.

## Objetivo

Criar uma arquitetura nova, modular e validável para rodar LOT, APB, LOT-salt, APB-salt e LOT-APB-salt usando arquivos de caso YAML e um executável único com flags.

## Regras

- Não editar código dentro de `legacy/`.
- Não alterar formulações físicas sem registrar justificativa.
- Não misturar refatoração com correção física.
- Preservar baselines legados.
- Usar SI internamente.
- Documentar conversões de unidade.
- Rodar testes e comparar resultados após qualquer mudança numérica.

## Primeira tarefa

Faça apenas inventário e planejamento. Não implemente código ainda.

Produza ou atualize:

1. `docs/01_legacy_inventory.md`
2. `docs/08_known_issues.md`
3. `docs/09_target_architecture.md`
4. `docs/06_validation_plan.md`

O inventário deve separar:

- arquivos de caso;
- solver;
- modelos físicos;
- leitura de entrada;
- escrita de saída;
- pós-processamento;
- duplicações entre `LOT_Tese`, `LOT_APB_v5` e `saltcreep`;
- pontos que devem ser preservados;
- pontos que devem ser migrados;
- pontos que devem ser reescritos.

Depois proponha uma sequência de tarefas pequenas para Codex implementar.
