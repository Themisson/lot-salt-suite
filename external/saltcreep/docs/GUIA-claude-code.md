# SaltCreep no Claude Code — montar a pasta e operar o projeto

Três partes: (A) política de bibliografia no repo; (B) como montar a pasta (com o novo layout
`main/` + `src/` + `results/` e o legado que você já criou); (C) como conduzir a construção
incremental.

Verificado contra a documentação atual do Claude Code (maio/2026, ~v2.1.x).
Docs oficiais: https://docs.claude.com/en/docs/claude-code/overview

═══════════════════════════════════════════════════════════════════════════
## PARTE A — Bibliografia no repo: distile, não despeje
═══════════════════════════════════════════════════════════════════════════

Resposta curta à sua pergunta: **sim, traga a bibliografia para perto do agente — mas distilada em
markdown, não como PDF inline.** Sua dissertação é exatamente o caso de uso: ela tem o algoritmo
completo do acoplamento termomecânico fraco do SESTSAL (Seção 3.3.4), com a equação de Fourier 1D
radial, FEM com elementos quadráticos de 3 nós, integração de Crank–Nicolson, e a decomposição
aditiva ε = ε^e + ε^v + ε^th. Esse conteúdo é OPERACIONAL — o agente vai usar todo dia.

A solução em três camadas, que já está aplicada no scaffold:

1. **PDFs em `docs/references/`** (gitignored por padrão; git-lfs se realmente precisar versionar).
   PDF é caro de ler a cada sessão e bloata o repo. Coloque ali a dissertação, o TCC, os papers da
   Costa & Poiate, Munson, Wang, Aubertin, etc.

2. **Distilação em markdown em `docs/`**. Equações, algoritmos, convenções e armadilhas viram docs
   curtos que o agente lê barato. Já fiz isso para o seu caso: `docs/thermal-coupling.md` agora
   carrega o algoritmo de Vasconcelos (2019) — equação de calor, FEM quadrático 3 nós (a mesma
   família do mecânico, que é o pulo do gato), Crank–Nicolson com β=½, decomposição aditiva, e o
   esqueleto do laço de acoplamento. O agente NÃO precisa abrir o PDF para implementar.

3. **`@docs/references/arquivo.pdf` para drill-down pontual.** Quando o markdown distilado tiver uma
   ambiguidade, mencione o PDF com @ e o agente lê só o necessário. Não inline o conteúdo do PDF no
   `CLAUDE.md` — isso paga o custo a cada sessão sem ganho.

**O que NÃO fazer:** comitar PDFs grandes no git, ou colocar a bibliografia em `CLAUDE.md`. O
`CLAUDE.md` é o brief sempre carregado; documentos longos vão em `docs/`, carregados sob demanda.

═══════════════════════════════════════════════════════════════════════════
## PARTE B — Montar a pasta (com seu legado real)
═══════════════════════════════════════════════════════════════════════════

### B.1 Layout final que vamos criar
```
saltcreep/                              ← abra o `claude` AQUI (raiz)
├── CLAUDE.md                           ← memória de projeto (sempre carregada)
├── CMakeLists.txt                      ← coordenado com main/ + src/ (ver B.4)
├── .gitignore                          ← build/, results/, docs/references/*.pdf, etc.
├── .claude/
│   ├── settings.json                   ← permissões (já bloqueia editar legacy/)
│   ├── agents/   verifier.md, legacy-explorer.md
│   └── commands/ add-model.md, add-element.md, new-case.md
├── main/                               ← .hpp E main.cpp (entry point)
│   ├── main.cpp
│   ├── elements/        Element.hpp, axisym_1d_L3.hpp, ...
│   ├── constitutive/    ConstitutiveModel.hpp, double_mechanism.hpp, ...
│   ├── thermal/         ThermalField.hpp, ...
│   ├── solver/          Assembler.hpp, TimeIntegrator.hpp, ...
│   └── io/              CaseParser.hpp, OutputWriter.hpp
├── src/                                ← apenas .cpp (implementações)
│   ├── elements/        axisym_1d_L3.cpp, ...
│   ├── constitutive/    double_mechanism.cpp, ...
│   ├── thermal/         ...
│   ├── solver/          ...
│   └── io/              ...
├── post/                               ← Python (matplotlib, pyvista, pandas)
├── bindings/                           ← pybind11
├── cases/                              ← YAML por simulação
│   └── tcc/                            ← oráculos A–F (fixos)
├── results/                            ← saída (gitignored; subpasta por caso)
├── tests/                              ← Catch2 (C++) + pytest (Python)
├── docs/
│   ├── method-decision.md, input-spec.md, elements.md, thermal-coupling.md, ...
│   └── references/                     ← PDFs (gitignored ou git-lfs)
├── legacy/                             ← VOCÊ JÁ TEM ISSO; NÃO EDITAR
│   ├── ModeloDissertacao_31out/        Matlab da dissertação (AQ9 + outros elementos)
│   ├── sestsal/                        C++ atual
│   └── sestsal_old/                    C++ antigo (renomeie se vier com espaço no nome)
└── build/                              ← artefatos do CMake (gitignored)
```

### B.2 Comandos para criar a estrutura
A partir de onde você já tem o `legacy/` pronto:
```bash
cd saltcreep   # raiz do seu repo
git init       # se ainda não inicializou

# se a pasta veio com espaço ("sestsal old"), renomeie:
[ -d "legacy/sestsal old" ] && mv "legacy/sestsal old" legacy/sestsal_old

# scaffold do projeto
mkdir -p main/{elements,constitutive,thermal,solver,io}
mkdir -p src/{elements,constitutive,thermal,solver,io}
mkdir -p post bindings tests/{cpp,python} cases/tcc results docs/references

# descompacte o conteúdo de saltcreep_claude_setup.zip AQUI (na raiz):
#   CLAUDE.md, GUIA-claude-code.md, docs/*, .claude/*

# .gitignore essencial
cat >> .gitignore <<'GIT'
build/
results/
docs/references/*.pdf
.claude/settings.local.json
__pycache__/
*.o
*.so
GIT

# coloque os PDFs da bibliografia em docs/references/ (gitignored):
# cp /caminho/dissertacao_vasconcelos_2019.pdf docs/references/
# cp /caminho/tcc_araujo_2009.pdf docs/references/

git add -A && git commit -m "scaffold inicial: layout main/+src/, .claude/, docs/, legado preservado"
```

### B.3 Instalar e abrir o Claude Code
```bash
curl -fsSL https://claude.ai/install.sh | bash    # binário nativo (recomendado)
# macOS: brew install --cask claude-code
claude auth login
cd saltcreep
claude                                            # abra na RAIZ — onde está o CLAUDE.md
```
Dentro da sessão:
- `/memory` — confirma que o CLAUDE.md foi carregado.
- **NÃO rode `/init`** desta vez. O `/init` GERA um CLAUDE.md; o seu já é mais rico.
- `/agents` — abre o gerenciador; os subagentes em `.claude/agents/` já aparecem.
- Digite `/` para ver `/add-model`, `/add-element`, `/new-case`.

### B.4 CMakeLists.txt minimal com main/ + src/
O ponto delicado do seu layout é: `target_include_directories` aponta para `main/` (onde estão os
`.hpp`), e as fontes vêm de `src/**.cpp` mais o `main/main.cpp`. Esqueleto:
```cmake
cmake_minimum_required(VERSION 3.20)
project(saltcreep CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Eigen3 3.4 REQUIRED)

file(GLOB_RECURSE SALT_SOURCES CONFIGURE_DEPENDS src/*.cpp)
add_executable(saltcreep main/main.cpp ${SALT_SOURCES})
target_include_directories(saltcreep PRIVATE main)
target_link_libraries(saltcreep PRIVATE Eigen3::Eigen)

enable_testing()
add_subdirectory(tests/cpp)   # quando existir
```
Quando o agente criar o `CMakeLists.txt`, ele deve usar este padrão. O `CLAUDE.md` já diz que a
convenção é `.hpp` em `main/` e `.cpp` em `src/`.

### B.5 Atalhos que valem o dia
- **Shift+Tab** (ou Alt+M): cicla Normal → Auto-Accept → **Plan mode**. Duas vezes Shift+Tab entra
  direto em plan. Plan = pesquisa+propõe, não edita. Use antes de tarefa nova.
- **@arquivo**: menção com autocompletar (`@main/elements/Element.hpp`). Mais rápido e barato que
  deixar o agente procurar. Funciona com PDFs também (`@docs/references/vasconcelos_2019.pdf`).
- **!comando**: roda bash direto e joga saída no contexto sem narração (`!ctest ...`).
- `/clear` entre tarefas não relacionadas; `/compact` em sessão longa; `/cost` para tokens.

### B.6 Resumo das camadas — onde cada coisa vai
- `CLAUDE.md` → fatos/regras sempre verdadeiros (física, layout main/+src/, convenções).
- `.claude/agents/*` → trabalhadores isolados (verificação, leitura do legado).
- `.claude/commands/*` → procedimentos sob demanda que VOCÊ dispara.
- `.claude/settings.json` → permissões (bloqueia editar `legacy/` e `docs/references/`).
- `docs/*.md` → conhecimento distilado da bibliografia, carregado quando relevante.
- `docs/references/*.pdf` → bibliografia bruta, consultada sob demanda via `@arquivo`.
- Hooks (opcional, depois) → garantias determinísticas no nível do sistema.

═══════════════════════════════════════════════════════════════════════════
## PARTE C — Conduzir a construção incremental
═══════════════════════════════════════════════════════════════════════════

Cada etapa é uma sessão (ou poucas), sempre no ciclo **Explore → Plan → Code → Verify**, test-first.

### Etapa 0 — fundação (elástico 1D, sem creep, sem térmico)
> Em plan mode (Shift+Tab×2): "Proponha a estrutura inicial de `main/` e `src/` com as três
> interfaces (`Element`, `ConstitutiveModel`, `ThermalField`), o parser de caso YAML descrito em
> `docs/input-spec.md`, e o solver elástico 1D axissimétrico (elemento `axisym_1d_L3`). Use o
> `legacy-explorer` para checar como o TCC monta a matriz B com o termo `u/r`. Proponha o
> `CMakeLists.txt` no padrão main/+src/ documentado em CLAUDE.md."
Saia do plan, mande implementar + o teste `analytic_lame`. Rode o `verifier`.

### Etapa 1 — mecanismo duplo (fluência secundária)
> "Use o `legacy-explorer` para mapear o mecanismo duplo no Matlab da dissertação em
> `legacy/ModeloDissertacao_31out/` E no SESTSAL em `legacy/sestsal/`. Reporte se as duas
> implementações batem ou divergem. Implemente como `ConstitutiveModel`, habilitável por
> `creep.secondary`. Escreva o teste de regressão A–F (`cases/tcc/`) com as tolerâncias do TCC —
> deve falhar antes da implementação. Implemente até passar."
Comparar com o TCC E com o SESTSAL antes de seguir.

### Etapa 2 — fluência primária, com flags
> "Implemente a primária (EDMT) como `ConstitutiveModel`, habilitável por `creep.primary`. Garanta
> que primária+secundária SATURA para o mecanismo duplo no regime permanente (teste isso). Crie
> casos: (a) só secundária; (b) primária+secundária; (c) primária isolada. Rode o `verifier`."

### Etapa 3 — elementos 2D + estudo de convergência
Um elemento por sessão via `/add-element`: Q4 → T3 → Q8 → Q9 → T6. Cada um entra no
`post/convergence.py`. Compare erro × GDL × tempo nos mesmos casos físicos. O **AQ9** da
dissertação (legacy/ModeloDissertacao_31out/) entra DEPOIS dos clássicos validados, para servir
como "topo de linha" no estudo de convergência (campo enriquecido de Lamé).

### Etapa 4 — terciária + dano
Via `/add-model`, um modelo de cada vez (Motta v1/v2, Wang 2004, Aubertin ISV_SH_D) + envoltórias
de dilatância (Spier/Ratigan/DeVries/Hunsche). Antes dos casos severos (taquidrita, k0>1),
implemente o integrador `implicit_adaptive` — o explícito quebra aí.

### Etapa 5 — acoplamento termomecânico fraco
> "Leia `docs/thermal-coupling.md` (algoritmo de Vasconcelos 2019 distilado). Implemente
> `ThermalField` no modo `profile` primeiro — reproduz T(z) do TCC. Conecte ao Arrhenius da lei de
> creep e à ε^th na decomposição aditiva. Verifique que K mecânica continua constante (acoplamento
> FRACO). Depois adicione `conduction_1d` com FEM L3 (mesmos elementos do mecânico) e integração
> Crank-Nicolson β=½. Teste consistência com `profile` no limite linear estacionário. Em caso de
> ambiguidade, consulte @docs/references/vasconcelos_2019.pdf seção 3.3.4."
`conduction_2d` só se um caso exigir contraste de condutividade ao longo de z.

### Princípios em toda etapa
- **Test-first inegociável.** Você tem oráculos de verdade: Lamé analítico, TCC A–F (com a Tabela 6
  de tempos), SESTSAL/ABAQUS, e os casos da sua dissertação. Vire cada um em teste vermelho ANTES
  de implementar.
- **Verificação cruzada como teste, não tarefa manual.** Formalize a comparação com o SESTSAL
  como teste no ctest; o `verifier` roda sozinho.
- **Opus para o difícil** (arquitetura, integrador implícito, acoplamento primária↔secundária);
  exploração de legado em modelos baratos (definido no front-matter dos subagentes).
- **Higiene de contexto.** `/clear` entre etapas; `/compact` antes de tarefa difícil em sessão longa.

### Codex em paralelo (opcional)
Mesma filosofia: um `AGENTS.md` com os MESMOS invariantes de física e protocolo de verificação. O
que carrega a qualidade é o brief preciso + os oráculos numéricos — não a ferramenta.
