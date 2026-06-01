---
description: Adiciona um novo modelo constitutivo seguindo a interface e o protocolo de verificação do projeto.
---

Implemente o modelo constitutivo: $ARGUMENTS

Siga estritamente este protocolo:
1. Primeiro leia `docs/constitutive-models.md` e a interface `include/constitutive/ConstitutiveModel.hpp`.
2. Confirme comigo a equação exata e os parâmetros ANTES de escrever código (cite a referência do PPTX/literatura).
3. Implemente como uma subclasse de `ConstitutiveModel`: cabeçalho em `include/constitutive/`,
   implementação em `src/constitutive/`. NÃO toque no motor.
4. Registre o modelo no dispatch/factory.
5. Escreva um teste unitário: ponto material único sob tensão desviadora constante, comparado com
   a solução analítica da lei (ou com um caso de referência conhecido).
6. Se o modelo tiver fase primária/terciária, verifique o acoplamento com o mecanismo duplo (secundária)
   — o modelo deve saturar para a formulação DM no regime permanente.
7. Rode o subagente `verifier`. Só declare concluído se ele retornar OK.

Pare e me pergunte se a equação for ambígua. Não invente parâmetros.
