# 20. Plano de migracao Eigen do saltcreep

## Decisao atual

O Eigen oficial do `lot-salt-suite` e `include/Eigen/`, exposto aos targets
modernos por `lss::eigen`. A copia em `external/saltcreep/include/Eigen/`
permanece preservada porque o `saltcreep` ainda e um solver vendorizado ativo
com CMake proprio e includes privados.

A Fase 6.10 nao migra o `saltcreep` para `include/Eigen`. A recomendacao e
manter uma rota experimental controlada ate existir adapter C++ de sal no build
principal.

## Opcoes avaliadas

| Opcao | Descricao | Beneficio | Risco | Decisao |
|-------|-----------|-----------|-------|---------|
| A | Manter `external/saltcreep/include/Eigen` para builds do saltcreep | Preserva estabilidade e historico de validacao | Duplica Eigen no repositorio | Aceita por enquanto |
| B | Forcar `include/Eigen` via flags externas | Teste rapido sem editar `external/saltcreep` | Nao garante precedencia no Visual Studio | Apenas diagnostico |
| C | Criar opcao CMake explicita `SALTCREEP_USE_LSS_EIGEN` | Prova reprodutivel e reversivel | Exige alteracao governada no CMake do saltcreep | Recomendada para fase futura |

## Plano recomendado

1. Manter `include/Eigen/` e `external/saltcreep/include/Eigen/` no repositorio.
2. Continuar usando `lss::eigen` nos targets modernos do `lot-salt-suite`.
3. Quando o adapter `SaltCreepInterface` entrar no build, adicionar opcao
   explicita no CMake do `saltcreep`, sem remover a copia vendorizada.
4. A opcao futura deve garantir include order verificavel:

```cmake
option(SALTCREEP_USE_LSS_EIGEN "Use lot-salt-suite include/Eigen for saltcreep" OFF)
```

5. A aceitacao da opcao deve exigir:
   - build baseline com Eigen vendorizado;
   - build experimental com `include/Eigen`;
   - `ctest` completo do `saltcreep`;
   - casos `lame_test.yaml` e `mud_gradient_1d_8p5ppg.yaml`;
   - comparacao numerica de outputs principais;
   - registro em `docs/audits/`.

## Criterios de rollback

Desativar a opcao experimental e voltar ao Eigen vendorizado se ocorrer qualquer
um destes sinais:

- falha de compilacao em MSVC, GCC ou Clang;
- falha em teste Catch2 do `saltcreep`;
- diferenca numerica nao explicada em fechamento, deslocamento, tensao ou dano;
- necessidade de alterar modelo constitutivo para compilar;
- conflito com o contrato de adapter C++.

## Proximo passo

Implementar primeiro o adapter C++ de sal no `lot-salt-suite`. Depois disso,
introduzir a opcao CMake experimental para o `saltcreep` como tarefa isolada,
sem remover diretorios Eigen existentes.
