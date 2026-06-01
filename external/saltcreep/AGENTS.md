# AGENTS.md — Instruções para agentes de código (Codex / Claude Code / outros)

Este arquivo é a referência ÚNICA para qualquer agente que trabalhe neste repositório. O
`CLAUDE.md` na raiz contém as MESMAS regras — se houver conflito, `CLAUDE.md` prevalece
(ele é atualizado com mais frequência).

**Leia TAMBÉM estes documentos antes de escrever código:**
- `CLAUDE.md` — regras de projeto, invariantes de física, convenções de estilo.
- `docs/dev-log.md` — log de desenvolvimento: o que cada agente implementou, em que ordem.
  **Atualize este arquivo ao final de CADA tarefa** que você completar.
- `docs/getting-started.md` — visão geral da Etapa 0 e contratos das interfaces.
- `docs/constitutive-models.md` — catálogo de leis de fluência com equações.
- `docs/time-integration.md` — explícito vs implícito, Crank-Nicolson.
- `docs/thermal-coupling.md` — acoplamento termomecânico fraco (Vasconcelos 2019).
- `docs/input-spec.md` — schema do YAML de caso.
- `docs/elements.md` — catálogo de elementos e estudo de convergência.
- `docs/architecture.md` — infraestrutura FEM: factory, Mesh genérico e contrato 2D.
- `docs/mesh-adaptation.md` — refinamento adaptativo h por estimador Zienkiewicz-Zhu.
- `docs/final-validation-report.md` — credencial e advertência consolidada de validação.
- `docs/developer-guide.md` — guia seguro para estender modelos, elementos e campos térmicos.
- `docs/post-processing.md` — guia do saltpost: estudos, paper, dashboard e animações.
- `docs/model-selection.md` — seleção de modelo de IA e economia de tokens.
- `docs/method-decision.md` — por que FEM e não BEM/FVM/MPM (decisão fechada).

---

## O que é este projeto
Solver FEM para fechamento de poços verticais em rocha salina por fluência. Dois objetivos:
verificador independente do SESTSAL (legado) e motor modernizado com primária + secundária +
terciária + dano + acoplamento termomecânico fraco + múltiplos tipos de elemento.

## Estado atual do projeto (manter atualizado aqui)
**Última atualização:** 2026-06-01
**Testes:** 120/120 C++ verdes + 21/21 Python saltpost/VTU/deslocamento/dano/viewer/benchmark/edge/dashboard verdes
**Etapas concluídas:**
- [x] Etapa 0: fundação elástica 1D axissimétrica + teste Lamé (8 testes)
- [x] Etapa 1: mecanismo duplo (DM, fluência secundária) + loop temporal explícito +
      regressão TCC A–F + geostatic force + dt schedule calibrado (21 testes)
- [x] Refactor: layout refatorado — .hpp em `include/`, .cpp em `src/`, main.cpp em `main/`
- [x] Etapa 2: EDMT (fluência primária) com flags de toggle primary/secondary/both (27 testes)
- [x] Etapa 3a: infraestrutura genérica para elementos 1D/2D (factory + Mesh + contrato Element)
- [x] Etapa 3b/Q4: `axisym_2d_Q4` + patch + Lamé convergência + regressão TCC
- [x] Etapa 3b/T3: `axisym_2d_T3` + patch + Lamé convergência + regressão TCC
- [x] Etapa 3b/Q8: `axisym_2d_Q8` + patch linear/quadrático + Lamé convergência + regressão TCC
- [x] Etapa 3b/Q9: `axisym_2d_Q9` + patch linear/quadrático + Lamé convergência + regressão TCC
- [x] Etapa 3b/T6: `axisym_2d_T6` + patch linear/quadrático + Lamé convergência + regressão TCC
- [x] Etapa 3b: estudo de convergência completo L3/Q4/T3/Q8/Q9/T6 com `post/convergence.py`
- [x] Etapa 4a: integrador implícito adaptativo (backward Euler + Newton local + step control)
- [x] Etapa 4b: Motta v1 com dano Kachanov + envoltória Spier
- [x] Etapa 5a: `ProfileField` funcional com perfil analítico `T(z)` e parâmetros térmicos
- [x] Pós-processamento: `saltpost` para comparação profissional de casos, elementos e discretizações
- [x] Etapa 5b: `Conduction1DField` radial com Fourier + Crank-Nicolson e BC externa configurável
- [x] Etapa 5c: pseudo-força térmica + Arrhenius acoplado ao `ThermalField`
- [x] Etapa 5: acoplamento termomecânico fraco completo (`profile` + `conduction_1d` + εth)
- [x] Etapa 10: `Conduction2DField` com Fourier 2D axissimétrico e camadas térmicas
- [x] Etapa 6: saída VTU + série temporal `.pvd` para ParaView/PyVista
- [x] Pós-processamento: gráficos de deslocamento físico (`u_wall_m`, perfis radial/vertical e mapa 2D)
- [x] Etapa 6.5: paralelismo OpenMP opcional, timers granulares e benchmark de desempenho
- [x] Etapa 7: `axisym_2d_AQ9` enriquecido com base de Lamé + alta precisão por GDL
- [x] Etapa 8d: diagnóstico de falha por dano (`damage_events.csv`, `damage_wall.csv` e plots)
- [x] Saltpost: cores/markers por caso quando o elemento é igual + viewer interativo `u_r(z)`
- [x] Etapa 8a: `Wang2004` CDM com dano não-linear acoplado à fluência
- [x] Etapa 8b: `AubertinISVSHD` unificado com primária + secundária + terciária + dano
- [x] Etapa 8c: `ISVSHDMunson` primária seno-hiperbólica Munson-Dawson/Chan
- [x] Etapa 9: interface `DilatancyEnvelope` + envoltórias Spier/Ratigan/DeVries/Hunsche
- [x] Etapa 12: refinamento adaptativo h com estimador Zienkiewicz-Zhu + refinadores Q4/T3
- [x] Opção 2a: benchmark suite integral de desempenho e precisão
- [x] Opção 2c: guia de desenvolvimento para extensões
- [x] Opção 2d: limpeza de código, otimizações, sanitizers opcionais e testes de edge case
- [x] Pós-processamento avançado: estudos declarativos, exportação paper, dashboard HTML e animações

**Próximas etapas (em ordem):**
- [ ] Próxima etapa a definir

## Layout do repositório
```
saltcreep/
├── CLAUDE.md            Regras de projeto (Claude Code lê este)
├── AGENTS.md            Este arquivo (Codex e outros agentes leem este)
├── CMakeLists.txt       C++20, Ninja, FetchContent para yaml-cpp + Catch2
├── include/             TODOS os .hpp do projeto + Eigen vendored
│   ├── Eigen/           Eigen 5.x (header-only, ~7.5 MB)
│   ├── elements/        Element.hpp, axisym_1d_L3.hpp
│   ├── mesh/            Mesh.hpp (Mesh, Mesh1D, Mesh2D), ErrorEstimator, MeshRefiner
│   ├── constitutive/    ConstitutiveModel.hpp, double_mechanism.hpp, edmt.hpp
│   ├── thermal/         ThermalField.hpp, profile_field.hpp, conduction_1d_field.hpp, conduction_2d_field.hpp
│   ├── solver/          Assembler.hpp, ElasticSolver.hpp, TimeIntegrator.hpp, TimeOutput.hpp, PerformanceStats.hpp, DamageDiagnostics.hpp
│   ├── io/              CaseParser.hpp, VtuWriter.hpp
│   └── types.hpp        Voigt {εr,εθ,εz,εrz}, GaussPoint, Stress, InternalState
├── src/                 TODOS os .cpp (espelha include/)
├── main/                SOMENTE main.cpp
├── cases/               YAML por simulação (tcc/ = oráculos fixos A–F)
├── data/                dados auxiliares (litologias, ensaios, perfis)
├── post/                Python pós-processamento
├── tests/               cpp/ (Catch2) + python/ (pytest)
├── docs/                decisões, física, refs distiladas
├── legacy/              referência — NÃO editar
│   ├── ModeloDissertacao_31out/   Matlab (AQ9 + outros elementos)
│   ├── sestsal/                   C++ atual do SESTSAL
│   └── sestsal_old/               versão anterior
├── results/             saída (gitignored)
└── build/               CMake (gitignored)
```

## Compilador e ambiente
- Windows + Visual Studio (MSVC, C++20). Gerador CMake: Ninja (preferir).
- OpenMP é opcional: o CMake linka `OpenMP::OpenMP_CXX` quando disponível; sem OpenMP o solver compila e roda sequencialmente.
- Eigen vendored em `include/Eigen/` (NÃO usar find_package).
- yaml-cpp e Catch2 via FetchContent.

## Build / test
```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build -j
ctest --test-dir build --output-on-failure
```

## Três interfaces plugáveis (já implementadas)
- `Element` (`include/elements/Element.hpp`) — tipo de elemento FEM.
- `ConstitutiveModel` (`include/constitutive/ConstitutiveModel.hpp`) — lei de fluência.
- `ThermalField` (`include/thermal/ThermalField.hpp`) — campo de temperatura.

Implementações existentes:
- `axisym_1d_L3` — 1D radial, 3 nós quadrático (do TCC).
- `axisym_2d_Q4` — 2D axissimétrico, quadrilátero bilinear, 4 nós.
- `axisym_2d_T3` — 2D axissimétrico, triângulo linear, 3 nós.
- `axisym_2d_Q8` — 2D axissimétrico, quadrilátero serendipity quadrático, 8 nós.
- `axisym_2d_Q9` — 2D axissimétrico, quadrilátero Lagrangiano quadrático, 9 nós.
- `axisym_2d_AQ9` — 2D axissimétrico, quadrilátero de 9 nós enriquecido com base de Lamé `{1,r,1/r}`.
- `axisym_2d_T6` — 2D axissimétrico, triângulo quadrático, 6 nós.
- `DoubleMechanism` — DM, fluência secundária, n1=3/n2=5, Arrhenius.
- `EDMT` — fluência primária, satura para DM.
- `ISVSHDMunson` — fluência primária com relação `sinh` e hardening seno-hiperbólico.
- `MottaV1` — fluência terciária com dano Kachanov e envoltória de dilatância plugável.
- `DilatancyEnvelope` — critérios Spier, Ratigan, DeVries e Hunsche para início de dano.
- `Wang2004` — CDM terciário com dano não-linear acoplado por tensão efetiva de von Mises.
- `AubertinISVSHD` — lei ISV unificada com primária, secundária, dano intrínseco e terciária.
- `elastic_isotropic` — stub elástico puro.
- `ProfileField` — T(z) analítico.
- `Conduction1DField` — condução transiente radial com Fourier + Crank-Nicolson.
- `Conduction2DField` — condução transiente 2D (r,z) com propriedades por camada.
- `ErrorEstimator` — Zienkiewicz-Zhu em norma de energia para marcar erro de tensão/dano.
- `MeshRefiner` — subdivisão h Q4→4 e T3→3 com transferência de campos.

## Flags de fluência no YAML
```yaml
creep:
  elastic_only: false
  secondary: true        # DM
  primary: false          # EDMT | isv_sh_dm
  tertiary: false         # MottaV1 | wang_2004 | aubertin_isv_sh_d
  damage: false           # Spier + dano Kachanov
  primary_model: EDMT     # EDMT | isv_sh_dm
  tertiary_model: MottaV1 # MottaV1 | wang_2004 | aubertin_isv_sh_d
  dilatancy_envelope: Spier # Spier | Ratigan | DeVries | Hunsche
```

## Física — invariantes INVIOLÁVEIS
- Deformação medida a partir da configuração geostática, após o furo.
- Decomposição aditiva ε = ε^e + ε^v + ε^th.
- Taxa volumétrica viscosa = 0 (creep desviador, isotrópico).
- K elástica CONSTANTE → fatorar UMA vez, back-substitution por passo.
- Temperatura entra SÓ via ε^th e Arrhenius (fraco) — NÃO altera K.
- Primária + secundária SATURA para DM no regime permanente.
- Taquidrita: taxa ~10^7× halita → passo pequeno ou implícito.
- Compressão é POSITIVA (convenção geomecânica).
- Voigt axissimétrico: [σ_rr, σ_θθ, σ_zz, σ_rz].

## Protocolo de verificação
1. Lamé analítico (erro < tol)
2. Patch test de cada elemento
3. Regressão TCC A–F
4. Convergência entre elementos (taxa ~h² linear, ~h³ quadrático)
5. Consistência térmica
6. Comparação vs SESTSAL/ABAQUS
NUNCA relaxar tolerância. Erro contra a segurança em A–D = bug.

## Protocolo de interoperabilidade (Claude Code ↔ Codex ↔ outros)
1. **Ao iniciar:** leia `CLAUDE.md`, `AGENTS.md`, e `docs/dev-log.md` para entender o estado.
2. **Ao concluir:** atualize `docs/dev-log.md` com o que fez (data, agente, resumo, testes).
3. **Se criar doc novo:** registre em `AGENTS.md` na lista de documentos no topo.
4. **Se alterar convenção:** atualize TANTO `CLAUDE.md` QUANTO `AGENTS.md`.
5. **Commits:** padrão Conventional Commits (`feat(...)`, `fix(...)`, `test(...)`, `docs(...)`).
6. **Legado:** NÃO editar `legacy/`. Leia para referência.
7. **Testes:** SEMPRE rodar `ctest --test-dir build --output-on-failure` antes de declarar pronto.
   Todos os testes existentes DEVEM continuar verdes (regressão). Novos testes são obrigatórios.

## Estilo de código
- C++20, `snake_case` funções/variáveis, `PascalCase` tipos.
- Headers `.hpp` em `include/`, sources `.cpp` em `src/`.
- Sem `using namespace std;` em headers.
- SI internamente; conversões só no parser de YAML.
- Python: PEP 8, type hints.

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
