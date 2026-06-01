# Referencias bibliograficas externas

Os PDFs, PPTX e materiais brutos de pesquisa nao fazem parte do nucleo compilavel do
SaltCreep. Eles foram removidos do versionamento para manter o repositorio leve e evitar que
clones novos baixem centenas de megabytes de arquivos binarios.

## Onde manter os arquivos brutos

Guarde os PDFs e materiais originais em armazenamento externo controlado pelo projeto, por
exemplo OneDrive, Google Drive, Zotero, Git LFS ou outro repositorio de referencias. Se algum
arquivo precisar voltar ao Git, prefira Git LFS e registre a decisao no dev-log.

## Conhecimento ja extraido

As informacoes tecnicas extraidas das referencias continuam versionadas em Markdown:

- `docs/reference-index.md` — catalogo das referencias usadas no projeto.
- `docs/reference-extraction-log.md` — notas tecnicas e equacoes extraidas.
- `docs/constitutive-models.md` — leis constitutivas implementadas e skeletons.
- `docs/thermal-coupling.md` — acoplamento termomecanico fraco.
- `docs/elements.md` — elementos finitos e resultados de convergencia.

## Politica para agentes

- Nao comitar PDFs, PPTX ou arquivos binarios grandes em `docs/references/`.
- Se precisar consultar uma referencia, use a copia externa e registre somente o conhecimento
  operacional em `docs/*.md`.
- Mantenha este diretorio com arquivos pequenos de controle e documentacao.

