---
description: Cria um arquivo de caso YAML novo em cases/ seguindo o schema, a partir de uma descrição física.
---

Crie um arquivo de caso para: $ARGUMENTS

1. Leia `docs/input-spec.md` para o schema e as regras de validação.
2. Preencha TODOS os campos do schema. Para o que faltar na descrição, use o padrão sensato do schema
   e me avise quais valores você assumiu (não invente litologia, profundidade ou fluido em silêncio).
3. Converta unidades de campo para o que o schema pede (o parser faz SI internamente; o YAML guarda
   lb/gal e polegadas como no TCC).
4. Salve em `cases/<name>.yaml`. Se for um caso do TCC (A–F), salve em `cases/tcc/` e trate como oráculo
   fixo de regressão — esses não mudam depois de criados.
5. Cheque coerência das flags de creep e do tipo de elemento contra as regras de validação do schema;
   se a combinação emitir aviso (ex.: explicit + taquidrita, primary sem secondary), registre o aviso
   no topo do YAML como comentário.

Não rode a simulação — só crie o caso. Pare e pergunte se a física estiver subdeterminada.
