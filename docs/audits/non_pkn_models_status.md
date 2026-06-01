# Status dos modelos nao PKN

## Objetivo

Catalogar modelos de fratura encontrados nos legados que nao devem entrar na
primeira entrega moderna de LOT/PKN.

## Modelos encontrados

| Modelo | ID legado | Status |
|--------|-----------|--------|
| Circular/KGD circular | 0 | Catalogado; nao prioritario. |
| Eliptico/KGD elliptic | 1 | Catalogado; nao prioritario. |
| Penny-shaped | 3 | Catalogado; nao prioritario. |

## Motivo para nao priorizar

O objetivo imediato e migrar um caminho LOT suficientemente rastreavel para
servir de base de validacao. O PKN tem casos e resultados legados mais diretos
para essa finalidade. Implementar todos os modelos simultaneamente aumentaria o
risco de misturar convencoes, unidades e erros historicos.

## Condicoes para reabrir

Um modelo nao PKN pode virar prioridade quando houver:

- caso legado inequivoco;
- saida congelada disponivel;
- formulacao documentada;
- criterio de breakdown claro;
- testes Catch2 propostos;
- justificativa de uso no acoplamento LOT/APB/sal.

## Riscos conhecidos

- Arquivos de caso podem ter nomes de geometria inconsistentes com a string
  efetivamente passada para `setLeakoffProps`.
- Parte das constantes empiricas aparece diretamente no bloco de calculo, sem
  fonte explicita no codigo.
- A semantica de volume varia entre geometrias e precisa de auditoria dedicada
  antes de migracao.
