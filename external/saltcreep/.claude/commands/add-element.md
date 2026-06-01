---
description: Adiciona um tipo de elemento finito seguindo a interface Element e o protocolo de convergência.
---

Implemente o tipo de elemento: $ARGUMENTS

1. Leia `docs/elements.md` e a interface `include/elements/Element.hpp`.
2. Confirme comigo a ordem de integração e as funções de forma ANTES de codar.
3. Implemente como subclasse de `Element`: cabeçalho em `include/elements/`, implementação em
   `src/elements/`, e registre no factory. NÃO toque no motor.
4. Atenção ao termo axissimétrico `u/r` (ε_θθ) e ao peso de integração (2πr / r). É o erro mais comum.
5. Teste unitário do elemento isolado:
   - patch test (campo de deslocamento linear/quadrático reproduzido exatamente);
   - solução elástica de Lamé com refinamento crescente → erro cai na taxa esperada para a ordem
     do elemento (~h² linear, ~h³ quadrático).
6. Adicione o novo tipo ao estudo de convergência (`post/convergence.py`) comparando com os elementos
   já existentes no mesmo caso físico.
7. Rode o subagente `verifier`. Só declare concluído se ele retornar OK e a convergência bater.

Pare e pergunte se a formulação for ambígua.
