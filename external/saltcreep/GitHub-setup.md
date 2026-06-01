# GitHub para o SaltCreep — setup e fluxo de trabalho

Três partes: (A) autenticação única, (B) criar o repo `saltcreep` e fazer o primeiro push,
(C) ritmo de commits/pushes a cada melhoria + os perigos a evitar (segredos, PDFs grandes, legado).

═══════════════════════════════════════════════════════════════════════════
## PARTE A — Autenticar uma vez (escolha um dos dois caminhos)
═══════════════════════════════════════════════════════════════════════════

### Caminho recomendado: GitHub CLI (`gh`)
Mais simples; cuida da autenticação E permite criar o repo do terminal em um único comando.

**Instalar:**
```bash
# Ubuntu/Debian
sudo apt install gh
# macOS
brew install gh
# Windows
winget install --id GitHub.cli
```

**Autenticar (uma vez):**
```bash
gh auth login
# Escolha: GitHub.com → HTTPS → autenticar via navegador (cole o código mostrado)
# No final, aceite "Configure git to use GitHub CLI as credential helper"
```
Pronto. Daqui pra frente `git push`/`pull` autenticam sozinhos.

### Caminho alternativo: SSH key
Use se preferir não instalar o `gh`. Você cria a chave aqui, cria o repo manualmente no site.
```bash
ssh-keygen -t ed25519 -C "seu_email@exemplo.com"
cat ~/.ssh/id_ed25519.pub
# Copie a saída. Em https://github.com/settings/keys → "New SSH key", cole e salve.
ssh -T git@github.com   # deve responder "Hi <user>! You've successfully authenticated"
```

═══════════════════════════════════════════════════════════════════════════
## PARTE B — Criar o repo `saltcreep` e primeiro push
═══════════════════════════════════════════════════════════════════════════

**Antes de qualquer push**, rode o `bootstrap.sh` (junto deste arquivo). Ele renomeia
`legacy/sestsal old` → `sestsal_old`, remove duplicatas na raiz, cria `main/`/`src/`/`results/`/`cases/`,
escreve `.gitignore` e um CMakeLists mínimo. É idempotente.

```bash
cd saltcreep
bash bootstrap.sh
git status   # confira o que vai ser commitado
```

### B.1  Com GitHub CLI (uma linha)
```bash
git init -b main
git add -A
git commit -m "Initial scaffold: layout main/+src/, .claude/, docs/, legado preservado"

# privado por padrão (mude para --public se preferir)
gh repo create saltcreep --private --source=. --remote=origin --push
```
Pronto. Repo criado e o primeiro push feito.

### B.2  Sem CLI (rota manual)
1. Em https://github.com/new crie o repo `saltcreep` (deixe vazio — sem README, sem .gitignore,
   sem licença; já temos tudo aqui).
2. No terminal:
```bash
cd saltcreep
git init -b main
git add -A
git commit -m "Initial scaffold: layout main/+src/, .claude/, docs/, legado preservado"
git remote add origin git@github.com:SEU_USUARIO/saltcreep.git
git push -u origin main
```

### B.3  Sanity check pós-push
```bash
git remote -v        # mostra a URL do origin
git log --oneline    # 1 commit
gh repo view --web   # abre no navegador (só com gh)
```
Confira no site se a pasta `legacy/sestsal/include/Eigen/` **não** foi parar lá (são milhares de
arquivos do Eigen, deveriam vir com o `.gitignore` correto — ver Perigos abaixo).

═══════════════════════════════════════════════════════════════════════════
## PARTE C — Ritmo de commits e o que NÃO comitar
═══════════════════════════════════════════════════════════════════════════

### C.1  Ritmo recomendado para este projeto
A construção é incremental e verificável. Comite na granularidade da etapa, não do arquivo. Padrão:

```bash
# Você acabou de implementar+verificar uma coisa coerente (etapa, modelo, elemento, fix de bug):
git status                              # o que mudou?
git diff                                 # revise antes de comitar
git add -A                               # ou seja seletivo: git add main/ src/ tests/
git commit -m "feat(constitutive): mecanismo duplo + teste de regressão modelo A"
git push                                 # sobe para o GitHub
```

**Sempre rode o `verifier` ANTES de comitar.** Esse é o invariante do projeto. Um commit que
quebra a regressão A–F polui o histórico e te custa caro depois (`git bisect` fica inútil).
Sequência boa:
```
trabalho no Claude Code → @verifier OK → git add → git commit → git push
```

### C.2  Mensagens de commit no padrão Conventional Commits
Curtas, em prefixo + escopo, ajudam muito ao ler `git log --oneline` daqui a um ano:
- `feat(elements): Q4 axissimétrico + patch test`
- `feat(thermal): conduction_1d com Crank–Nicolson β=½`
- `fix(constitutive): termo Arrhenius com T_ref correto`
- `test(regression): casos A–F do TCC com tolerâncias publicadas`
- `docs(thermal): algoritmo de Vasconcelos 2019 destilado`
- `refactor(solver): fatoração de K elástica fora do loop temporal`
- `chore: bump CMake mínimo para 3.24`

### C.3  Branches para mudanças grandes
Para mexer em algo arquitetural (integrador implícito, novo tipo de elemento de grande porte),
trabalhe em branch e abra pull request — fica fácil reverter se algo der errado:
```bash
git checkout -b feat/implicit-integrator
# ...trabalho, commits, verifier OK...
git push -u origin feat/implicit-integrator
gh pr create --fill           # com gh; ou abra no site
# após revisar, merge no main
```
Para mudanças pequenas (um arquivo, um teste, uma doc), trabalhar direto em `main` está bom.

### C.4  Perigos a evitar (cada um já mordeu alguém antes)

**1. PDFs grandes.** Os 4 arquivos em `docs/references/` somam ~16 MB. O `.gitignore` do bootstrap
já exclui `*.pdf`, `*.pptx`, `*.docx` dessa pasta — **propositadamente**. Esses ficam só na sua
máquina. Se um dia precisar versionar um PDF específico (ex.: documento oficial do projeto), use
**git-lfs** em vez de commitar direto:
```bash
git lfs install
git lfs track "docs/references/manual_oficial.pdf"
git add .gitattributes docs/references/manual_oficial.pdf
```

**2. Eigen no legado.** `legacy/sestsal/include/Eigen/` tem **milhares** de arquivos. Eles serão
commitados (porque estão dentro do legado, que é referência). Isso é OK uma vez — pode tornar o
push inicial lento e o repo grande (~30–50 MB). Se incomodar, alternativas:
- substituir o Eigen embarcado por uma instrução em `legacy/sestsal/README.md` ("baixar Eigen
  3.x e colocar em `include/`"), e adicionar `legacy/sestsal/include/Eigen/` ao `.gitignore`.
- ignorar o problema (recomendado se o repo continuar privado e ninguém clonar muito).

**3. Resultados de simulação.** A pasta `results/` está no `.gitignore` — gere localmente, não
versione. O que você quer versionar é o **caso** (`cases/*.yaml`) e o **código** que gera, não a
saída numérica.

**4. Segredos.** `.claude/settings.local.json` está no `.gitignore`. Nunca cole tokens da API,
chaves SSH, senhas em commit. Se cair sem querer, use `git filter-repo` para limpar histórico E
**revogue o token imediatamente** — git não tem "desfazer push" gratuito.

**5. Commits gigantes "WIP".** Evite `git add -A && git commit -m "wip"` com 40 arquivos
modificados. Quebrar em commits pequenos por intenção (um por etapa do roadmap) faz o `git log`
contar a história do solver — vira documentação viva.

### C.5  Comandos úteis do dia-a-dia
```bash
git status                              # o que mudou
git diff                                # mudanças não staged
git diff --staged                       # mudanças staged
git log --oneline --graph -20           # últimos 20 commits, em árvore
git restore <arquivo>                   # descarta mudança não staged
git restore --staged <arquivo>          # tira do stage
git commit --amend                      # corrige a mensagem do último commit (antes do push)
gh pr status                            # PRs abertos (com gh)
```

### C.6  Integração com o Claude Code
- O `.claude/settings.json` já bloqueia `git push` por padrão (em `permissions.deny`). Isso é de
  propósito — o push é decisão sua, não do agente. O Claude pode te ajudar a escrever a mensagem
  de commit, mas você roda o `git push`.
- Quando pedir ao Claude para fazer um commit, peça assim: "rode `git status` e `git diff`, escreva
  um commit no padrão Conventional Commits, faça `git add` e `git commit`, **mas não dê push**."
- Os arquivos do legado (`legacy/`) também estão bloqueados para edição. Eles vão para o git, mas
  o agente não mexe neles.

═══════════════════════════════════════════════════════════════════════════
## TL;DR
═══════════════════════════════════════════════════════════════════════════
```bash
bash bootstrap.sh                       # ajusta a estrutura uma vez
gh auth login                           # autentica no GitHub uma vez
git init -b main
git add -A && git commit -m "Initial scaffold"
gh repo create saltcreep --private --source=. --remote=origin --push

# daí pra frente, a cada melhoria:
@verifier OK → git add → git commit -m "feat(...): ..." → git push
```
