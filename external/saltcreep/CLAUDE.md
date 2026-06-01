# SaltCreep — solver de fluência de rocha salina (verificação cruzada + produção)

## O que é este projeto
Solver numérico para fechamento de poços verticais em rocha salina por fluência.
Dois objetivos simultâneos:
1. **Verificador independente** do SESTSAL (motor de produção legado, sucessor do ANVEC).
2. **Motor modernizado** que incorpora fluência primária + secundária + terciária + dano,
   com acoplamento termomecânico FRACO e múltiplos tipos de elemento finito.

Método numérico: **FEM contínuo** (decidido — não BEM/FVM/MPM; ver `docs/method-decision.md`).

## Princípio de construção: incremental, com flags
Cada camada nova precisa passar na verificação antes da próxima entrar. Ordem canônica:
1. Problema elástico (Lamé) — 1D axissimétrico.
2. **Mecanismo duplo (fluência secundária)** — verificar contra TCC e SESTSAL.
3. **Fluência primária** — habilitável junto com a secundária OU isolada, via flag de entrada.
4. Demais elementos finitos (2D) e estudo de convergência.
5. Fluência terciária + dano.
6. **Acoplamento termomecânico fraco** (algoritmo de Vasconcelos, 2019 — ver `docs/thermal-coupling.md`).

Cada estágio é ligado/desligado por flag no YAML do caso (ver `docs/input-spec.md`):
`creep.elastic_only`, `creep.secondary`, `creep.primary`, `creep.tertiary`, `creep.damage`,
`thermal.enabled`.

## Layout do repositório
```
saltcreep/
├── CLAUDE.md
├── CMakeLists.txt
├── .gitignore
├── .claude/             agents/, commands/, settings.json
├── main/                SOMENTE main.cpp (entry point)
│   └── main.cpp
├── include/             TODOS os headers do projeto (.hpp) + Eigen vendored
│   ├── types.hpp        tipos Voigt, GaussPoint, Stress, Strain, InternalState
│   ├── elements/        Element.hpp, axisym_1d_L3.hpp, ...
│   ├── mesh/            Mesh.hpp (Mesh, Mesh1D, Mesh2D)
│   ├── constitutive/    ConstitutiveModel.hpp, double_mechanism.hpp, ...
│   ├── thermal/         ThermalField.hpp, profile_field.hpp, ...
│   ├── solver/          Assembler.hpp, ElasticSolver.hpp, TimeIntegrator.hpp, ...
│   ├── io/              CaseParser.hpp, OutputWriter.hpp
│   └── Eigen/           Eigen 5.x — header-only, ~7.5 MB, versionado no repo
├── src/                 .cpp (implementações; espelha a árvore de include/)
│   ├── elements/  constitutive/  thermal/  solver/  io/
├── cases/               YAML por simulação (input do executável)
│   └── tcc/             oráculos fixos A–F (regressão; não alterar)
├── data/                dados auxiliares versionáveis (ver §Pastas data/ vs cases/)
│   ├── litologias/      propriedades calibradas por litologia
│   ├── ensaios/         dados de ensaios triaxiais (para calibração)
│   └── perfis/          perfis medidos (temperatura, profundidade)
├── post/                Python de pós-processamento (matplotlib, pyvista, pandas)
├── tools/               (opcional, criar se precisar) utilitários gerais:
│                        geração de malha standalone, conversores, scripts de CI
├── bindings/            pybind11 (expõe o motor C++ ao Python)
├── tests/               cpp/ (Catch2) + python/ (pytest)
├── docs/                decisões de arquitetura, física, refs distiladas
│   └── references/      PDFs de bibliografia (gitignored; ver §Bibliografia)
├── legacy/              referência — NÃO editar
│   ├── ModeloDissertacao_31out/   Matlab (AQ9 e outros elementos)
│   ├── sestsal/                   C++ atual (tem seu próprio include/Eigen 3.x)
│   └── sestsal_old/               versão anterior do C++
├── results/             saída das simulações (gitignored; subpasta por caso)
└── build/               artefatos do CMake (gitignored)
```

**Convenção de pastas — regra simples:**
- `include/` = TODOS os `.hpp` do projeto + Eigen vendored. O agente ESCREVE headers aqui.
- `src/`     = TODOS os `.cpp` do projeto (espelha a árvore de `include/`).
- `main/`    = SOMENTE `main.cpp` (entry point). Sem headers.

O CMakeLists aponta `target_include_directories(saltcreep PRIVATE include)`.
Dois Eigens no repo intencionalmente: `include/Eigen/` (5.x, novo) e `legacy/sestsal/include/Eigen/` (3.x, legado). NÃO mesclar.

## Pastas `data/` vs `cases/` — diferença que importa
- **`cases/`** define uma SIMULAÇÃO completa. Um YAML por caso (geometria, litologia, flags de
  creep, malha, tempo). É o input do executável: `./saltcreep cases/modelo_A.yaml`.
- **`data/`** são DADOS auxiliares que múltiplos casos consomem: tabelas de propriedades por
  litologia, ensaios triaxiais para calibração, perfis medidos. Um caso em `cases/` REFERENCIA
  arquivos em `data/`; sem `data/`, ou você duplica tabelas em todo caso, ou usa paths absolutos.
- Arquivos grandes (> 10 MB) em `data/` devem usar git-lfs ou referência externa, não git regular.

## Compilador e ambiente
- **Windows + Visual Studio (MSVC, C++20).** Gerador CMake: Ninja (preferir) ou
  `"Visual Studio 17 2022"`.
- No MSVC use `/W4` em vez de `-Wall -Wextra` (que são GCC/Clang). O CMakeLists já trata isso
  condicionalmente por `CXX_COMPILER_ID`.
- **Eigen via vendoring** em `include/Eigen/` (NÃO usar `find_package(Eigen3)`). Header-only,
  basta o `target_include_directories` apontar para `include/`.
- **Dois Eigens no repo, intencionalmente:** o novo em `include/Eigen/` (5.x) e o do legado em
  `legacy/sestsal/include/Eigen/` (3.x). Cada projeto compila separado com o seu. NÃO mesclar.

## Bibliografia — política
- **PDFs em `docs/references/`** (gitignored por padrão; git-lfs se for crítico versionar).
  Não comitar PDFs grandes no git regular.
- O diretório mantém apenas arquivos pequenos de controle, como `docs/references/README.md`;
  referências brutas ficam em armazenamento externo e o conhecimento extraído vai para `docs/*.md`.
- **Conhecimento operacional vai para `docs/*.md`.** Equações, algoritmos e convenções extraídos
  das referências viram docs curtos (ex.: `docs/thermal-coupling.md` carrega o algoritmo de
  Vasconcelos, 2019, sem o agente precisar reler o PDF a cada sessão).
- Para trecho específico do PDF, mencionar com `@docs/references/arquivo.pdf` — o agente lê só o
  necessário. NÃO inline PDFs no CLAUDE.md.

## Build / test / run
```bash
# Configurar (Windows com Ninja, recomendado):
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo

# Alternativa sem Ninja:
cmake -S . -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo

# Compilar / testar / rodar:
cmake --build build -j
ctest --test-dir build --output-on-failure
pytest tests/python -q
./build/saltcreep cases/modelo_A.yaml          # saída vai para results/modelo_A/
python post/plot_case.py results/modelo_A
```
Compilador: C++20. Build padrão `RelWithDebInfo`; para perfilar use `Release`.

## Dependências (não trocar sem registrar em docs/)
- **Vendored** (no repo, em `include/`): Eigen 5.x (esparsa via `SimplicialLDLT`).
- **Externas** (a instalar): pybind11, Catch2, Ninja (opcional mas recomendado).
- **Python**: numpy, scipy, matplotlib, pyvista, pandas, pyyaml, pytest.

## Três interfaces plugáveis — o coração da arquitetura
O motor conhece SÓ interfaces; implementações se registram em factories.
- `ConstitutiveModel` — leis de fluência (DM, EDMT, ISV_SH_DM, Motta, Wang, Aubertin+D...).
- `Element`           — tipos de elemento (axissim 1D L3; 2D Q4/T3/Q8/Q9/T6; AQ9 do legado).
- `ThermalField`      — fonte de T(x) consumida pelo Arrhenius da lei de creep.

Trocar de modelo / elemento / térmico é escolha no YAML do caso, não mudança de código.
Elementos são instanciados por `ElementFactory`; a malha genérica (`Mesh`, `Mesh1D`, `Mesh2D`)
armazena nós em `(r,z)` e DOFs por nó. Ver `docs/architecture.md`.

## Tipos de elemento (ver `docs/elements.md`)
1D axissim L3 (TCC) primeiro → 2D Q4/T3 → 2D Q8/Q9/T6 → (futuro) elemento enriquecido AQ9 da
dissertação. Tipo é flag de caso → permite estudo de convergência comparando o mesmo caso físico.
Refinamento adaptativo é camada posterior, não MVP.

## Acoplamento termomecânico FRACO (ver `docs/thermal-coupling.md`)
- One-way: térmico → mecânico, NÃO mecânico → térmico. Algoritmo de Vasconcelos (2019, dissertação UFAL).
- Decomposição aditiva da deformação: ε_total = ε_elástica + ε_viscosa + ε_térmica.
  A temperatura entra (i) na ε_térmica direta, e (ii) no Arrhenius da lei de creep.
- Equação de calor 1D axissimétrica radial (Fourier) resolvida por FEM com a MESMA família de
  elementos quadráticos do problema mecânico, integrada por Crank-Nicolson (β=½, incond. estável).
- Modos disponíveis: `profile` (T(z) analítico, como no TCC), `conduction_1d`, `conduction_2d`.
- K elástica continua **constante** — temperatura entra só no lado direito (pseudo-força térmica
  e taxa viscosa). Não perdemos o ganho de fatorar K uma vez.

## Física — invariantes que NÃO podem ser violados
- Deformação medida a partir da configuração geostática, no instante logo após o furo.
- Estado geostático não gera deformação; só a nova configuração gera.
- Decomposição aditiva ε = ε^e + ε^v + ε^th (acoplamento fraco).
- Taxa de deformação viscosa volumétrica unidimensional = 0 (creep desviador; material isotrópico).
- K elástica é constante → fatorar UMA vez, só back-substitution por passo.
- Não linearidade vive no lado direito (pseudo-forças viscosas + térmicas).
- Temperatura entra SÓ via ε^th e via Arrhenius (acoplamento FRACO) — não altera K.
- Primária + secundária deve **saturar para o mecanismo duplo** no regime permanente.
- Taquidrita: taxa de creep ~10^7× a halita → exige passo pequeno ou integrador implícito.

## Protocolo de verificação (em ordem; pare no primeiro que regredir)
1. Solução elástica analítica de Lamé (cilindro vazado) — erro < tolerância.
2. Patch test de cada tipo de elemento (campos lineares/quadráticos reproduzidos exatamente).
3. Reprodução dos modelos A–F do TCC (regressão + tempos da Tabela 6).
4. Convergência entre tipos de elemento no mesmo caso (taxa ~h² linear, ~h³ quadrático).
5. Consistência térmica: `profile` vs `conduction_1d` no limite de gradiente linear e k uniforme.
6. Reprodução dos casos termomecânicos da dissertação (Vasconcelos, 2019) — quando o caso existir.
7. Comparação vs. SESTSAL/ABAQUS — formalizada como teste no ctest, não checagem manual.

NUNCA relaxe uma tolerância para um teste passar. Erro contra a segurança nos casos A–D = bug.

## Arquivos de caso
YAML em `cases/`. Saída em `results/<nome_do_caso>/` (VTU + CSV). Casos do TCC fixos em `cases/tcc/`.
Use o slash command `/new-case` para gerar pelo schema de `docs/input-spec.md`.

## O que pedir antes de agir
- Modelo constitutivo novo: ler `docs/constitutive-models.md` e `include/constitutive/ConstitutiveModel.hpp`.
- Elemento novo: ler `docs/elements.md` e `include/elements/Element.hpp`.
- Infraestrutura de elemento/malha/factory: ler `docs/architecture.md`.
- Integrador temporal: ler `docs/time-integration.md`.
- Térmico: ler `docs/thermal-coupling.md`.
- Setup inicial / arquitetura geral: ler `docs/getting-started.md`.
- Dúvida de qual modelo de Claude usar / como economizar tokens: ler `docs/model-selection.md`.
- Tocar no legado: NÃO. `legacy/` é referência. Use o subagente `legacy-explorer`.

## O que NÃO comitar (já no .gitignore)
- `build/`, `results/`, artefatos `.o/.so/.exe`
- `docs/references/*.pdf`, `*.pptx`, `*.docx`
- `.claude/settings.local.json`
- `__pycache__/`, `.pytest_cache/`, `.venv/`

## Estilo
- Mudanças pequenas e verificáveis. Um modelo / elemento / feature por PR.
- Teste ANTES de declarar concluído. Sempre rodar o subagente `verifier` antes do commit.
- C++: `snake_case` funções/variáveis, `PascalCase` tipos. Headers `.hpp` em `include/`, sources
  `.cpp` em `src/`. Sem `using namespace std;` em headers. SI internamente; conversões só no
  parser de YAML.
- Python: PEP 8, type hints em funções públicas.
- Mensagens de commit no padrão Conventional Commits
  (`feat(constitutive): ...`, `fix(solver): ...`, `test(regression): ...`, `docs(thermal): ...`).

## Manutenção do manual HTML (OBRIGATÓRIO)

O manual técnico interativo vive em `docs/index.html`. Ele DEVE ser atualizado no MESMO ciclo
de trabalho sempre que você:
- adicionar/alterar uma classe pública (elemento, modelo constitutivo, campo térmico, solver);
- adicionar um tipo de elemento (atualizar tabela de convergência + card);
- adicionar um modelo constitutivo ou envoltória de dilatância;
- mudar o schema YAML de entrada (atualizar exemplo + construtor interativo);
- mudar a contagem de testes (atualizar badge, hero, seção de verificação, footer).

**No Claude Code:** invoque o subagente `docs-sync` ao final da etapa.
**No Codex (ou manual):** siga `docs/manual-maintenance.md` e edite `docs/index.html` diretamente.

A regra: nenhuma etapa que toca a API pública fecha sem o manual refletir a mudança. Documentação
desatualizada é considerada regressão. Atualize o manual ANTES do commit final da etapa.
