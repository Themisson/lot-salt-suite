# Prompt mestre para Codex

Use as instruções de `AGENTS.md`.

## Tarefa inicial

Inspecione o projeto sem modificar código.

Leia:

- `legacy/LOT_Tese/`
- `legacy/LOT_APB_v5/`
- `external/saltcreep/AGENTS.md`
- `external/saltcreep/CLAUDE.md`
- `external/saltcreep/include/io/CaseParser.hpp`
- `external/saltcreep/include/constitutive/ConstitutiveModel.hpp`
- `external/saltcreep/docs/input-spec.md`

Produza `docs/01_legacy_inventory.md` contendo:

1. Mapa dos arquivos principais.
2. Quais arquivos são casos.
3. Quais arquivos são solver.
4. Quais arquivos são modelos físicos.
5. Quais arquivos fazem leitura de entrada.
6. Quais arquivos fazem saída.
7. Quais arquivos fazem pós-processamento.
8. Quais conceitos existem em `LOT_Tese` mas não em `LOT_APB_v5`.
9. Quais conceitos existem em `LOT_APB_v5` mas não em `LOT_Tese`.
10. Como `saltcreep` pode ser usado como núcleo moderno de sal.
11. Riscos técnicos.
12. Proposta de ordem de migração.

Não implemente código nesta tarefa.
