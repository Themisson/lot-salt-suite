# Dev Log — registro compartilhado entre agentes

Cada agente (Claude Code, Codex, ou outro) DEVE atualizar este arquivo ao concluir uma tarefa.
Formato: data, agente, resumo do que foi feito, contagem de testes.

---

## 2026-05-30 — Claude Code — Etapa 0: fundação elástica 1D
- Criadas as 3 interfaces: `Element`, `ConstitutiveModel`, `ThermalField`
- Implementado `axisym_1d_L3` (3 nós, quadrático, matriz B com termo N_i/r)
- Stubs: `elastic_isotropic`, `ProfileField`
- Parser de YAML mínimo (yaml-cpp via FetchContent)
- Solver elástico com `SimplicialLDLT`
- CMakeLists com FetchContent (yaml-cpp 0.8, Catch2 v3.5)
- Testes: 5 Lamé (acurácia + taxa h³) + 3 patch L3
- **8/8 verdes**

## 2026-05-30 — Claude Code — Etapa 1: mecanismo duplo (DM)
- Implementado `DoubleMechanism` (n1=3, n2=5, Arrhenius, direção deviatórica)
- Dados de litologia em `data/litologias/` (halita, taquidrita, carnalita)
- Loop temporal explícito (`TimeIntegrator`): K fatorada uma vez, pseudo-força viscosa
- `assemble_geostatic_force` (bug que causava NaN corrigido)
- Dirichlet no nó externo (u[Re]=0, como SESTSAL %SUPPORT)
- Schedule de dt calibrado (transições graduais, sem salto 50×)
- 6 casos TCC (A–F) em `cases/tcc/`
- `post/plot_tcc.py` para plots de comparação
- **21/21 verdes** (7 DM unitários + 8 Lamé/patch + 6 TCC regressão)

## 2026-05-30 — Claude Code — Refactor layout + Etapa 2: EDMT
- Refactor: todos os `.hpp` movidos de `main/` → `include/` (main/ só com main.cpp)
- CMakeLists atualizado: `target_include_directories(... include)`
- EDMT implementado: ε̇_total = ε̇_DM · (1 + K₁·exp(−K₂·εᵥ)), saturação para DM testada
- Flags: `creep.primary` + `creep.secondary` toggleáveis isoladamente
- 3 variantes de caso A (secondary_only, primary_secondary, primary_only)
- **27/27 verdes** (21 anteriores + 6 EDMT novos)

## 2026-05-30 — Codex — Etapa 3a: infraestrutura genérica 1D/2D
- Criado `ElementFactory` com dispatch inicial para `axisym_1d_L3`
- Criada infraestrutura `Mesh`/`Mesh1D`/`Mesh2D` com nós `(r,z)` e indexação genérica de DOFs
- Contrato de `Element` preparado para pontos locais `(xi, eta)` e coordenadas físicas 2D
- `Assembler`, `TimeIntegrator` e `main.cpp` adaptados para malha/DOFs genéricos preservando o L3
- Parser aceita `element.type` ausente com default `axisym_1d_L3`
- Criado `docs/architecture.md` explicando factory, mesh e contrato 2D
- **27/27 verdes** (regressão preservada)

## 2026-05-30 — Codex — Etapa 3b/Q4: primeiro elemento 2D axissimétrico
- Implementado `axisym_2d_Q4` com funções bilineares, Gauss 2x2, Jacobiano 2D e peso `2*pi*r`
- Registrado `axisym_2d_Q4` no `ElementFactory`
- Adicionados patch tests lineares, Lamé Q4 com convergência h² e regressão TCC modelo_A_Q4
- Criado `cases/tcc/modelo_A_Q4.yaml`

## 2026-05-31 — Claude Code — Etapa 2b: organização de referências bibliográficas
- Criado `docs/reference-index.md`: catálogo ~52 PDFs com status (extraído vs. indexado)
- Criado `docs/reference-extraction-log.md`: template reutilizável + 7 extrações completas:
  * Firme2016 (MD) — parâmetros halita brasileira, 3 mecanismos
  * Firme2018 (EDMT, EDMP) — função transiente F(ξ), parâmetros EDMT
  * Chan1992 (M-D + dano) — Munson-Dawson com dano Kachanov, healing
  * PoiateFalcao2006 (DM aplicado) — calibração por litologia Santos Basin
  * Munson1990 (M-D clássico) — primeira publicação M-D com transiente
  * FeiWu2018 (CDM não-linear) — dano exponencial, sal chinês
  * wang2019 (ciclos) — evolução dano sob ciclos (não é Wang2004)
- Criado `docs/validation-cases.md`: 6 casos padrão (Lamé, patch, TCC, convergência, térmico, dilatância)
- Corrigidos stale paths `main/` → `include/` em:
  * `.claude/commands/add-model.md`
  * `.claude/commands/add-element.md`
  * `docs/constitutive-models.md` (atualizado com EDMT ✓, ISV_SH_DM ⏳)
- **27/27 verdes** (regressão mantida)
- Atualizado `docs/elements.md` com a formulação Q4
- **31/31 verdes** (27 regressões anteriores + 4 testes Q4)

## 2026-05-30 — Codex — Etapa 3b/T3: triângulo linear axissimétrico
- Implementado `axisym_2d_T3` com funções lineares, Jacobiano constante e integração triangular de 3 pontos
- Registrado `axisym_2d_T3` no `ElementFactory`
- Adicionados patch tests lineares, Lamé T3 com convergência h² e regressão TCC modelo_A_T3
- Criado `cases/tcc/modelo_A_T3.yaml`
- Atualizado `docs/elements.md` com a formulação T3
- **35/35 verdes** (31 anteriores + 4 testes T3)

## 2026-05-30 — Codex — Etapa 3b/Q8: quadrilátero serendipity quadrático
- Implementado `axisym_2d_Q8` com funções serendipity, Jacobiano 2D e integração Gauss 3x3
- Registrado `axisym_2d_Q8` no `ElementFactory`
- Adicionados patch tests linear/quadrático, Lamé Q8 com convergência h³ e regressão TCC modelo_A_Q8
- Criado `cases/tcc/modelo_A_Q8.yaml`
- Atualizado `docs/elements.md` com a formulação Q8
- **39/39 verdes** (35 anteriores + 4 testes Q8)

## 2026-05-30 — Codex — Etapa 3b/Q9: quadrilátero Lagrangiano quadrático
- Implementado `axisym_2d_Q9` com base Lagrange tensorial 3x3, Jacobiano 2D e integração Gauss 3x3
- Registrado `axisym_2d_Q9` no `ElementFactory`
- Adicionados patch tests linear/quadrático, Lamé Q9 com convergência h³ e regressão TCC modelo_A_Q9
- Criado `cases/tcc/modelo_A_Q9.yaml`
- Atualizado `docs/elements.md` com a formulação Q9
- **43/43 verdes** (39 anteriores + 4 testes Q9)

## 2026-05-30 — Codex — Etapa 3b/T6: triângulo quadrático axissimétrico
- Implementado `axisym_2d_T6` com funções quadráticas baricêntricas, Jacobiano 2D e integração triangular Dunavant de 6 pontos
- Registrado `axisym_2d_T6` no `ElementFactory`
- Adicionados patch tests linear/quadrático, Lamé T6 com convergência h³ e regressão TCC modelo_A_T6
- Criado `cases/tcc/modelo_A_T6.yaml`
- Atualizado `docs/elements.md` com a formulação T6
- **47/47 verdes** (43 anteriores + 4 testes T6)

## 2026-05-30 — Codex — Etapa 3b: estudo de convergência completo
- Criado `post/convergence.py` para montar o problema elástico de Lamé e comparar L3/Q4/T3/Q8/Q9/T6
- Script gera `results/convergence/lame_convergence.csv`, `lame_error_vs_dofs.png` e `lame_error_vs_time.png`
- Atualizado `docs/elements.md` com erro final, taxa mínima observada e tempo local por elemento
- Etapa 3b concluída: todos os elementos planejados implementados, testados e comparados no mesmo caso Lamé
- **47/47 verdes** (sem novos testes C++; documentação/script de pós-processamento)

## 2026-05-30 — Codex — Etapa 4a: integrador implícito adaptativo
- Criado `ImplicitAdaptiveIntegrator` com backward Euler, Newton local por ponto de Gauss e controle adaptativo por step-doubling
- Mantido `TimeIntegrator` explícito como caminho padrão e regressão intacta
- Adicionado `ConstitutiveModel::tangent()` com fallback numérico e tangentes analíticas para DM e EDMT
- Parser e `main.cpp` aceitam `time.scheme: implicit_adaptive` e tolerâncias `tol_local`, `tol_global`, `dt_min_h`, `dt_max_h`
- Adicionados testes de tangente, equivalência explícito/implícito no Modelo A, convergência temporal e caso severo com taquidrita
- **51/51 verdes** (47 anteriores + 4 testes 4a)

## 2026-05-30 — Codex — Etapa 4b: Motta v1 com dano
- Verificada a convenção de sinal do código: no Modelo A, `sigma_geo = [-119.7, -119.7, -119.7, 0] MPa`, ou seja, compressão é negativa internamente
- Implementado `MottaV1` com taxa `eps_dot_DM/(1-D)^n_d`, evolução de dano Kachanov e saturação `D_max = 0.99`
- Implementada envoltória Spier ajustada à convenção tensão-positiva: `f_dil = sqrt(J2) + a*I1 - b`
- Parser e `main.cpp` aceitam `creep.tertiary`, `creep.damage`, `tertiary_model: MottaV1`, `dilatancy_envelope: Spier` e parâmetros `motta_v1`/`spier`
- Adicionados testes de sinal da Spier, equivalência DM sem dano, bloqueio abaixo da envoltória, monotonia, saturação, aceleração, tangente e caso severo implícito
- **59/59 verdes** (51 anteriores + 8 testes Motta v1)

## 2026-05-31 — Codex — Etapa 5a: ProfileField funcional
- `ProfileField` deixou de ser temperatura pré-computada e passou a avaliar `T(z) = T_seabed + grad*(depth_origin + z)`
- Mantida compatibilidade com o comportamento 1D anterior: para malha radial, `z=0` e a temperatura fica constante na profundidade do caso
- Parser aceita `thermal.enabled`, `geothermal_gradient_C_per_m`, `alpha_thermal` e `T_reference_C`, preservando `grad_C_per_m`
- Adicionados testes de perfil analítico, parâmetros de expansão térmica e aliases do parser
- **62/62 verdes** (59 anteriores + 3 testes ProfileField)

## 2026-05-31 — Codex — Pós-processamento profissional saltpost
- `main.cpp` passou a gravar `metadata.json` em cada pasta de resultado com caso, elemento, malha, GDLs, esquema temporal, flags de fluência, térmica, tempo total e tempo de parede
- Criado pacote `post/saltpost/` com módulos `io`, `registry`, `compare`, `plots`, `style` e `cli`
- Criado wrapper `post/compare_cases.py` para comparar casos específicos, glob por elemento, glob por GDLs e tabela-resumo
- Gráficos padronizados em PNG/PDF: fechamento vs tempo, erro relativo vs tempo e fechamento final vs GDLs
- Adicionados testes Python de IO, alinhamento/erro relativo e descoberta de resultados
- **62/62 C++ verdes + 3/3 Python saltpost verdes**

## 2026-05-31 — Codex — Etapa 5b: Conduction1DField radial
- Implementado `Conduction1DField` como `ThermalField` transiente para Fourier radial 1D com elementos L3
- Montadas matrizes térmicas `C` e `H` axissimétricas com peso `2*pi*r` e integração Gauss do L3
- Integração temporal por método theta com `beta=0.5` padrão (Crank-Nicolson), mantendo suporte a `beta=0` e `beta=1`
- Parser e `main.cpp` aceitam `thermal.mode: conduction_1d`, propriedades térmicas, `dt_thermal_h`, `inner_wall_temp_C`, `outer_temp_C` e `outer_bc`
- Suporte a `thermal.outer_bc: prescribed` (padrão) e `thermal.outer_bc: flux_zero`
- Integradores explícito e implícito passam o tempo físico ao `ThermalField` para permitir temperatura transiente no Arrhenius
- Adicionados testes de estado estacionário logarítmico, convergência temporal, balanço de energia e parsing das BCs térmicas
- **66/66 C++ verdes + 3/3 Python saltpost verdes**

## 2026-05-31 — Codex — Etapa 5c: pseudo-força térmica e Etapa 5 completa
- `TimeState` passou a armazenar `eps_th_gp` para a decomposição aditiva `eps = eps_e + eps_v + eps_th`
- Integradores explícito e implícito montam pseudo-força térmica incremental `f_th = integral B^T D delta_eps_th dV`
- Tensões agora são recomputadas com `sigma = D*(B*u - eps_v - eps_th) + sigma_geo`
- `eps_th = alpha*(T_gp - T_ref)*[1, 1, 1, 0]`, com `alpha=0` preservando exatamente o caminho anterior
- `Conduction1DField` passou a permitir consultas temporais fora de ordem, necessário para o step-doubling do implícito
- Adicionados testes de `alpha=0`, expansão livre analítica em deformação plana e sinal físico de fechamento por aquecimento radial
- Etapa 5 concluída: `profile`, `conduction_1d`, Arrhenius via `ThermalField` e pseudo-força térmica estão integrados
- **69/69 C++ verdes + 3/3 Python saltpost verdes**

## 2026-05-31 — Claude Code — Etapa 11: verificação formal vs. SESTSAL
- Criado conversor `tools/sestsal_converter.py`: parse `.inp` (SESTSAL) → `.yaml` (SaltCreep)
  * Extrai: profundidade, k0, pressão fluido, temperatura, E, ν, mesh radial, schedule de dt
  * Suporta múltiplas camadas, litologias, overburden e configurações térmicas
  * Tratamento de quotes e erro robusto para templates/placeholders
- Criado extrator de oráculo `tools/sestsal_oracle.py`: lê `.out` (SESTSAL) → C++ header com closure % esperado
  * Extrai 5 casos válidos: base_model (1.66%), hello_repasse (1.06%), base_model2D (0.037%), hello_repasse2D (0.53%), repasse2D (0.25%)
  * Gera `include/test_sestsal_oracle.hpp` com struct de oráculo
- Convertidos 7 arquivos `.inp` → `cases/sestsal/*.yaml` (4 válidos com oracle + 2 templates sem oracle)
- Criados testes iniciais em `tests/cpp/test_sestsal_verification.cpp` (RED agora, aguardando DM + TimeIntegrator)
  * 3 testes: base_model, hello_repasse, base_model2D com helper `run_saltcreep_case()`
  * Compara closure % final contra oracle com tolerância ±5% (±10% para 2D)
- Criado relatório `docs/sestsal-comparison.md`: documenta mapeamento, oráculo, protocolo e status
- Atualizado `docs/dev-log.md` com entrada Etapa 11
- **69/69 C++ verdes (regressão preservada) + 3 testes SESTSAL RED (aguardando implementação de DM/TimeIntegrator)**

## 2026-05-31 — Codex — Etapa 6: saída VTU/PVD
- Criado `VtuWriter` em `include/io/` + `src/io/` para exportar malha, deslocamentos, tensão, deformação viscosa, dano e temperatura em `.vtu`
- Integradores explícito e implícito escrevem série temporal `caso_0000.vtu`, `caso_0001.vtu`, ... e índice `.pvd`, respeitando `output.vtu_every_n_steps` e sempre gravando o passo final
- Caminho `elastic_only` também grava VTU/PVD quando `output.vtu: true`
- Parser aceita `output.vtu`, `output.vtu_every_n_steps`, `output.revolve_3d` e `output.every_n_steps`
- Criado `post/saltpost/vtk.py` para carregar VTU com PyVista quando disponível
- Adicionado teste Python que executa um caso elástico mínimo, valida `.vtu`/`.pvd` e confere arrays nodais esperados
- Manual `docs/index.html` atualizado seguindo `docs/manual-maintenance.md`
- **69/69 C++ verdes + 4/4 Python saltpost/VTU verdes**

## 2026-05-31 — Codex — Fix main: habilitação dos elementos 2D no CLI
- Removido o guard legado de Etapa 3a que bloqueava `axisym_2d_Q4/T3/Q8/Q9/T6` no `main.cpp`
- Promovido o builder estruturado 2D para o caminho de produção, usando `n_elements_radial`, `n_elements_axial`, `ratio`, `Ri` e `Re` do YAML
- `main.cpp` agora monta pressão na parede interna para elementos 2D e aplica travamentos radial externo + axial conforme os testes TCC 2D
- Verificado `build/saltcreep.exe cases/tcc/modelo_A_Q8.yaml`: gera `results/modelo_A_Q8/closure.csv` e `metadata.json`
- **69/69 C++ verdes**

## 2026-05-31 — Codex — Manual: visualização e física da terciária
- Atualizado `docs/index.html` conforme `docs/manual-maintenance.md`
- Adicionada seção `#visualization` com saltpost, convergência, ParaView, PyVista e comparação de estágios de fluência
- Adicionado bloco em `#physics` sobre dano, início da terciária, envoltória de dilatância, uso de `implicit_adaptive` e calibração experimental
- Confirmadas contagens do manual: **69 testes C++ + 4 testes Python = 73 verdes**

## 2026-05-31 — Codex — Gráficos de deslocamento físico
- `closure.csv` passou a incluir `u_wall_m` mantendo `wall_disp_m` para retrocompatibilidade
- Integradores explícito e implícito agora gravam `displacements_profile.csv` e `wall_profile.csv` nos tempos de saída
- Criado `post/saltpost/units.py` com escala automática μm/mm/cm/m
- Saltpost ganhou plots `--plot displacement`, `radial_profile`, `wall_profile` e `field_map`
- Manual e AGENTS atualizados com os novos arquivos, comandos e contagem de testes
- **69/69 C++ verdes + 6/6 Python saltpost/VTU/deslocamento verdes**

## 2026-05-31 — Codex — Etapa 6.5: OpenMP e benchmarking
- CMake agora detecta OpenMP opcionalmente e linka `OpenMP::OpenMP_CXX` quando disponível, preservando fallback sequencial
- Paralelizados os loops externos de elementos na montagem de rigidez, pseudo-forças, força térmica/geostática e avaliação constitutiva dos integradores explícito e implícito
- Mantida montagem global determinística via contribuição local por elemento e scatter serial ordenado; teste novo compara Q8 Modelo A com 1 vs 2 threads
- Criado `PerformanceStats` e metadados `omp_threads`, `time_assembly_s`, `time_solve_s`, `time_constitutive_s` em `metadata.json`
- Criado `post/benchmark.py` para rodar Modelo A Q8 com 1/2/4 threads e gerar speedup, breakdown de tempo e CSV em `results/benchmark/`
- Manual e AGENTS atualizados com OpenMP, benchmark e contagem de testes
- **70/70 C++ verdes + 6/6 Python saltpost/VTU/deslocamento verdes**

## 2026-05-31 — Codex — Etapa 7: AQ9 enriquecido com base de Lamé
- Implementado `axisym_2d_AQ9` como elemento de 9 nós, 2 DOFs/nó, com base radial racional `{1, r, 1/r}` e base quadrática em `eta`
- Adicionados overloads geometry-aware no contrato `Element`; o default preserva as chamadas antigas dos elementos L3/Q4/T3/Q8/Q9/T6
- Portada a quadratura radial especial do legado Matlab com validação explícita de pesos positivos e cache `thread_local`
- Registrado `axisym_2d_AQ9` no `ElementFactory`, no builder estruturado 2D, no CLI e no YAML de caso `cases/tcc/modelo_A_AQ9.yaml`
- Adicionados testes de patch linear, reprodução exata da base de Lamé na matriz B, Lamé com 1 elemento em erro de machine epsilon e regressão TCC Modelo A AQ9
- Atualizado `post/convergence.py`, `docs/elements.md`, `docs/index.html`, `docs/input-spec.md`, `docs/architecture.md` e `AGENTS.md`
- **75/75 C++ verdes + 6/6 Python saltpost/VTU/deslocamento verdes**

## 2026-05-31 — Codex — Etapa 8d: diagnóstico de falha por dano
- Criado `DamageDiagnostics` para registrar `damage_events.csv` e `damage_wall.csv` durante simulações com `output.damage_tracking: true` e `creep.damage: true`
- Eventos registrados: cruzamento de limiares de D, critério operacional `failure_D_critical`, taxa de fluência acima de múltiplo da taxa DM pura e inflexão estimada por três passos consecutivos
- Integradores explícito e implícito chamam o diagnóstico apenas em passos aceitos, preservando o caminho sem dano e sem gerar CSVs quando o rastreamento está desligado
- Parser e metadados aceitam `damage_tracking`, `damage_thresholds`, `failure_D_critical` e `creep_rate_multiplier_threshold`
- Saltpost ganhou plots `--plot damage`, `creep_rate`, `damage_comparison` e `phase_space`
- Criados casos demonstrativos em `cases/damage/` para comparação com/sem dano e taquidrita severa
- Manual, `docs/input-spec.md`, `docs/constitutive-models.md` e `AGENTS.md` atualizados com diagnóstico de falha
- **80/80 C++ verdes + 7/7 Python saltpost/VTU/deslocamento/dano verdes**

## 2026-05-31 — Codex — Saltpost: cores por caso e viewer interativo de deslocamento
- Corrigida a paleta dos plots comparativos: quando todos os resultados usam o mesmo elemento, cores e markers passam a distinguir cada caso
- Mantido o comportamento anterior de cores fixas por elemento quando há mistura de tipos de elemento
- Legendas agora incluem sempre nome do caso + elemento, inclusive com `--group-by`
- Criado `post/displacement_viewer.py` para explorar `u_r(z)` na parede com slider temporal, Play/Pause e modo HTML standalone
- O HTML embute `wall_profile.csv`, inverte o eixo de profundidade, oferece tooltip e exportação PNG
- Adicionados testes Python para `get_color`, markers, legenda e geração de HTML válido
- **80/80 C++ verdes + 11/11 Python saltpost/VTU/deslocamento/dano/viewer verdes**

## 2026-05-31 — Codex — Etapa 10: Conduction2DField
- Implementado `Conduction2DField` como `ThermalField` para Fourier 2D axissimétrico em `(r,z)`
- Montadas matrizes térmicas `Cij = integral rho*cP*Ni*Nj*2*pi*r*dA` e `Hij = integral k*gradNi.gradNj*2*pi*r*dA` usando o mesmo `Element` 2D do caso mecânico
- Integração temporal por Crank-Nicolson com fatoração reutilizada de `[C22 + dt*beta*H22]` para `dt` fixo
- Parser e `main.cpp` aceitam `thermal.mode: conduction_2d`, `top_bc`, `bottom_bc` e `thermal.layers` com propriedades por camada
- `temperature_at(r,z,t)` interpola a temperatura nodal 2D no elemento físico encontrado
- Adicionados testes de consistência com `Conduction1D`, perfil logarítmico estacionário, contraste vertical, balanço de energia e parser de camadas
- Manual, `docs/input-spec.md`, `docs/thermal-coupling.md` e `AGENTS.md` atualizados
- **85/85 C++ verdes + 11/11 Python saltpost/VTU/deslocamento/dano/viewer verdes**

## 2026-05-31 — Codex — Etapa 8a: Wang 2004 CDM
- Implementado `Wang2004` em `include/constitutive/wang_2004.hpp` + `src/constitutive/wang_2004.cpp`
- Lei CDM: `eps_dot = eps_dot_DM/(1-D)^n_d`, `dD/dt = A_d*sigma_ef^m_d/(1-D)^p_d`, `sigma_ef = sqrt(3/2*s:s)` e `D <= 0.99`
- Parser aceita `creep.tertiary_model: wang_2004`, parâmetros `creep.wang_2004` e defaults por litologia para halita/taquidrita
- Registrado no dispatch constitutivo do `main.cpp`; criado `cases/sestsal/caso_wang.yaml`
- Adicionados testes de redução exata a DM sem evolução de dano, monotonia, saturação, equivalência de fechamento e regressão `caso_wang` com envelope ±5%
- Manual, `docs/input-spec.md`, `docs/constitutive-models.md` e `AGENTS.md` atualizados
- **90/90 C++ verdes + 11/11 Python saltpost/VTU/deslocamento/dano/viewer verdes**

## 2026-05-31 — Codex — Etapa 8b: Aubertin ISV_SH_D
- Implementado `AubertinISVSHD` em `include/constitutive/aubertin_isv_sh_d.hpp` + `src/constitutive/aubertin_isv_sh_d.cpp`
- Lei unificada ISV: primária exponencial, secundária base, amplificação por dano e evolução `dD/dt = A_d*sigma_ef^m_d*(1-D)^p_d*g(eps_v)`
- `InternalState` agora armazena também `eps_v_primary` e `eps_v_secondary`, preservando `eps_v_eff` para modelos legados
- Parser aceita `creep.tertiary_model: aubertin_isv_sh_d` e bloco `creep.aubertin_isv_sh_d`; o modelo tem dano intrínseco e não exige `creep.damage:true`
- Criado `cases/sestsal/caso_aubertin.yaml`
- Adicionados testes de redução a EDMT sem dano, monotonia/limite de ISVs e D, comparação leve com Motta e regressão `caso_aubertin` com envelope ±10%
- Manual, `docs/input-spec.md`, `docs/constitutive-models.md` e `AGENTS.md` atualizados
- **94/94 C++ verdes + 11/11 Python saltpost/VTU/deslocamento/dano/viewer verdes**

## 2026-05-31 — Codex — Etapa 8c: ISV_SH_DM Munson
- Implementado `ISVSHDMunson` em `include/constitutive/isv_sh_dm.hpp` + `src/constitutive/isv_sh_dm.cpp`
- Lei primária Munson-Dawson/Chan: `eps_dot_primary = e0*sinh(sigma_ef/sigma_ref)^n*Arrhenius*h(eps_v_primary)`, com `h` seno-hiperbólico regularizado e saturação para DM quando `secondary:true`
- Parser e `main.cpp` aceitam `creep.primary_model: isv_sh_dm` e bloco `creep.isv_sh_dm`
- `InternalState` agora expõe `f_hard` como diagnóstico derivado da função de hardening ISV
- Criado `cases/sestsal/caso_isv_sh_dm.yaml`
- Adicionados testes de transiente comparável à EDMT calibrada, saturação para DM, tangente analítica e regressão `caso_isv_sh_dm` com envelope ±5%
- Manual, `docs/input-spec.md`, `docs/constitutive-models.md` e `AGENTS.md` atualizados
- **98/98 C++ verdes + 11/11 Python saltpost/VTU/deslocamento/dano/viewer verdes**

## 2026-05-31 — Codex — Etapa 9: envoltórias de dilatância
- Criada interface `DilatancyEnvelope` com método virtual `dilatancy_function(I1, J2)` e avaliação por invariantes de tensão
- Refatorado `MottaV1` para receber uma envoltória polimórfica em tempo de execução, preservando o construtor antigo com `SpierParams`
- Implementadas `SpierEnvelope`, `RatiganEnvelope`, `DeVriesEnvelope` e `HunscheEnvelope`, respeitando a convenção interna de compressão negativa via `I1_comp = -I1`
- Parser e `main.cpp` aceitam `creep.dilatancy_envelope: Spier|Ratigan|DeVries|Hunsche` e blocos opcionais `spier`, `ratigan`, `devries`, `hunsche`
- Adicionados testes de sinal hidrostático seguro, ativação nos limiares configurados, factory por nome e divergência de curvas de dano no Motta
- Manual, `docs/input-spec.md`, `docs/constitutive-models.md` e `AGENTS.md` atualizados
- **102/102 C++ verdes + 11/11 Python saltpost/VTU/deslocamento/dano/viewer verdes**

## 2026-05-31 — Codex — Etapa 12: refinamento adaptativo h
- Implementado `ErrorEstimator` Zienkiewicz-Zhu com recuperação nodal de tensões e erro relativo em norma de energia
- Implementado `MeshRefiner` para Q4→4 e T3→3, com conservação de área, fechamento conformante para Q4 e transferência de `u`, tensões, deformações e `InternalState`
- Parser aceita `mesh.adaptive`, `mesh.error_threshold`, `mesh.max_refinement_levels` e `mesh.damage_refinement_threshold`
- `main.cpp` executa um pre-refinamento elástico antes da simulação final e grava `mesh_adaptive`, `adaptive_iterations` e `final_n_elements` no `metadata.json`
- Criados `docs/mesh-adaptation.md` e `docs/etapa-12-plan.md`; manual, `docs/input-spec.md` e `AGENTS.md` atualizados
- Adicionados testes de estimador sem marcação espúria, salto de tensão, marcação por dano, refino Q4/T3, transferência de campos e parsing YAML adaptativo
- **110/110 C++ verdes + 11/11 Python saltpost/VTU/deslocamento/dano/viewer verdes**

## 2026-05-31 — Codex — Opção 2a: benchmark suite integral
- Criado `post/benchmark_suite.py` para gerar YAMLs temporários e rodar combinações de elementos L3/Q4/T3/Q8/Q9/T6/AQ9, modelos DM/EDMT/Wang/Aubertin/ISV_SH_DM, modos térmicos, envelopes Wang e threads OpenMP
- A suite coleta `wall_time_s`, timers granulares, `closure_final`, GDLs e `omp_threads` de `metadata.json` e `closure.csv`
- Gerados `benchmark_suite.json`, `benchmark_report.md` e gráfico `benchmark_time_vs_dofs.png/pdf` em `results/benchmark/`
- O CLI oferece presets `smoke`, `standard` e `full`, com `--dry-run`, `--max-runs`, `--timeout-s` e `--stop-on-failure`
- Adicionados testes Python para matriz smoke, geração de relatório sintético e execução real de um benchmark pequeno com verificação de metadados/closure
- Manual e `AGENTS.md` atualizados com comandos da suite e nova contagem
- **110/110 C++ verdes + 14/14 Python saltpost/VTU/deslocamento/dano/viewer/benchmark verdes**

## 2026-05-31 — Codex — Opção 2b: relatório final de validação
- Criado `docs/final-validation-report.md` como documento de credencial e advertência do solver
- Consolidada validação contra SESTSAL, convergência Lamé por elemento, regimes de fluência, acoplamento térmico, dano/falha, performance OpenMP, adaptação de malha, recomendações de uso e troubleshooting
- Manual ganhou seção `Final Report` com link para o relatório consolidado
- `AGENTS.md` atualizado para registrar o novo documento de referência
- **110/110 C++ verdes + 14/14 Python verdes preservados (alteração documental)**

## 2026-05-31 — Codex — Opção 2c: guia de desenvolvimento para extensões
- Criado `docs/developer-guide.md` com arquitetura geral do solver, fluxo de execução e checkpoints de extensão
- Documentado passo a passo para adicionar `ConstitutiveModel`, `Element` e `ThermalField`
- Incluídos padrões de teste C++/Python, checklist de validação, comandos de build/test/smoke/benchmark e boas práticas
- Manual ganhou seção `Developer Guide`; `AGENTS.md` registra o novo documento
- **110/110 C++ + 14/14 Python preservados (alteração documental)**

## 2026-06-01 — Codex — Opção 2d: limpeza, otimizações e edge cases
- Adicionadas opções CMake `ENABLE_SANITIZERS` e `ENABLE_WERROR` para builds de diagnóstico sem afetar o build padrão
- `ENABLE_SANITIZERS` agora detecta suporte real de compilação e link antes de aplicar flags; no MinGW desta máquina o runtime ASan/UBSan não está disponível, então o build cai para modo não instrumentado com aviso explícito
- `ENABLE_WERROR` passa no código do projeto; apenas o falso positivo `-Wstringop-overflow` do Eigen vendorizado é mantido como warning não fatal no GCC
- Criado `tests/cpp/test_edge_cases.cpp` cobrindo destrutores virtuais, tensão zero, temperaturas extremas, saturação EDMT, dano próximo de `D_max`, AQ9 com pesos positivos, solução mínima L3 e parser com `max_refinement_levels: 0`
- Criado `tests/python/test_edge_cases.py` cobrindo malha adaptativa com zero níveis e caso com `dt` extremamente pequeno
- Manual e `AGENTS.md` atualizados com a nova contagem de testes
- **120/120 C++ verdes + 16/16 Python verdes**

## 2026-06-01 — Codex — Pós-processamento avançado
- Criado `post/saltpost/studies.py` para descobrir estudos declarativos com `--study` e `--vary element|constitutive|thermal`
- Criado `post/saltpost/export.py` para o modo `--format paper`, gerando pacote `paper/` com figuras PNG/PDF, tabelas CSV/Markdown/LaTeX e `paper_manifest.csv`
- Criado `post/saltpost/report.py` para dashboard HTML estático com figuras, resumo de metadados e links para CSV/VTU/PVD
- Criado `post/saltpost/animations.py` para animações GIF/MP4 de fechamento, deslocamento radial, dano e temperatura
- `post/compare_cases.py` agora aceita `--study`, `--vary`, `--results-root`, `--format paper`, `--report`, `--animate`, `--animation-format` e `--fps`
- Criado `docs/post-processing.md`; manual e `AGENTS.md` atualizados com comandos e nova contagem
- Adicionados testes Python para descoberta de estudos, exportação paper, dashboard HTML, animação de fechamento e fluxo CLI combinado
- **120/120 C++ verdes + 21/21 Python verdes**

## 2026-06-01 — Codex — Limpeza Fase 1: artefatos versionados e referencias pesadas
- Removido `build2/` do versionamento (artefatos CMake/Visual Studio, executaveis, PDB/ILK/LIB e dependencias FetchContent materializadas)
- Removido `docs/references/new_references/` do versionamento; o conhecimento operacional permanece em `docs/reference-index.md`, `docs/reference-extraction-log.md` e demais documentos tecnicos
- Removidos outputs binarios/textuais grandes de `legacy/sestsal/examples` (`*.out` e `mesh.mp4`) sem tocar no codigo legado
- Reforcado `.gitignore` para bloquear builds, artefatos MSVC, resultados, referencias brutas e outputs temporarios do legado
- Criado `docs/references/README.md` explicando a politica de referencias externas
- **120/120 C++ verdes + 21/21 Python verdes**

## 2026-06-01 — Codex — Compatibilizacao dos YAMLs SESTSAL legados
- Atualizados 7 YAMLs em `cases/sestsal/` para o schema atual: `mesh.n_elements_radial`, `lithology.primary`, `time.total_h`, `time.dt_h` e `time.steps`
- Corrigidos os campos de fluido dos casos convertidos incorretamente: valores de profundidade em `weight_lb_per_gal` foram substituidos pelos ppg lidos dos `.inp` legados (`14.75`, `16.0`, `17.5`)
- Rodados `base_model`, `base_model2D`, `hello_repasse`, `hello_repasse2D`, `keywords`, `project61` e `repasse2D`; todos geraram `closure.csv` e `metadata.json` com fechamento final finito
- Gerado pos-processamento por caso em `results/<caso>/postprocess_<caso>/` e comparacao nomeada em `results/comparisons/sestsal_legacy_fixed_7_cases/`
- **120/120 C++ verdes + 21/21 Python verdes**

## 2026-06-01 — Codex — Saltpost: diametro do poco, litologias e setor 3D
- `metadata.json` passou a registrar geometria do poco, diametro original, profundidade de referencia, espessura 2D, modelos constitutivos/térmicos e camadas litologicas visuais
- `closure.csv` e `wall_profile.csv` ganharam colunas retrocompativeis para diametro instantaneo em m/in e profundidade absoluta da parede
- Parser aceita `geometry.layer_thickness_m` e `lithology.layers`/`intercalations` para anotacao visual; a fisica mecanica continua homogenea por `lithology.primary`
- Criados `saltpost.diameter`, `saltpost.layers`, `saltpost.axisym3d` e o wrapper `post/axisym_solid_3d.py`
- CLI ganhou `--plot diameter_profile`, `diameter_time`, `lithology_column` e `axisym_3d`, permitindo comparar DM vs EDMT por profundidade e reproduzir perfis de diametro tipo SESTSAL/ABAQUS
- Manual, `docs/input-spec.md`, `docs/post-processing.md` e `AGENTS.md` atualizados
- **120/120 C++ verdes + 25/25 Python verdes**

## 2026-06-01 — Codex — Pressão hidrostática por peso de lama em 1D/2D
- Criado `WallPressureField` com `ConstantWallPressureField` e `HydrostaticMudPressureField`
- Parser aceita `fluid.mode: constant|hydrostatic_depth_profile`, `surface_pressure_Pa` e mantém `weight_lb_per_gal` legado retrocompatível
- `Assembler` passou a avaliar pressão variável nos pontos de Gauss da parede interna 2D; no 1D a pressão é calculada na profundidade do caso
- Integradores explícito e implícito adicionam o incremento de carga `f_p(t+dt)-f_p(t)` sem alterar a fatoração única de K
- Saída temporal ganhou `wall_pressure_profile.csv` com `p_wall_Pa` e `T_wall_K` na parede interna
- Criados casos `cases/apb/mud_gradient_1d_8p5ppg.yaml` e `cases/apb/mud_gradient_2d_Q8_8p5ppg.yaml`
- Testes novos cobrem cálculo hidrostático, parser legado/APB, equivalência 1D, integração 2D da força na parede e execução real dos casos APB 1D/2D
- Manual, `docs/input-spec.md`, `docs/post-processing.md`, `docs/architecture.md` e `AGENTS.md` atualizados
- **125/125 C++ verdes + 26/26 Python verdes**

## 2026-06-01 — Codex — Saltpost: gráficos de pressão na parede
- `CaseResult` agora carrega `wall_pressure_profile.csv` quando disponível
- CLI ganhou `--plot wall_pressure_profile`, `--plot wall_pressure_time` e `--plot wall_pressure_map`
- Os plots geram perfis `p_wall(z)`, séries `p_wall(t)` em profundidades selecionadas e mapa `p_wall(z,t)`, com escala automática Pa/kPa/MPa
- Manual e `docs/post-processing.md` atualizados com os comandos de visualização da pressão de lama
- Adicionado teste Python sintético para validar geração dos três gráficos
- **125/125 C++ verdes + 27/27 Python verdes**

## 2026-06-01 — Codex — Acoplamento APB por CSV externo
- Criado `TimeDepthTable` para ler grades CSV completas `t,z,valor` com interpolação linear e clamp nas bordas
- Criado `CsvWallPressureField` para `fluid.mode: csv_time_depth_profile`, avaliando `p_wall(t,z)` nos pontos de Gauss da parede
- Criado `CsvWallTemperatureField` para `thermal.mode: csv_wall_temperature`, entregando `T_wall_K(t,z)` aos modelos constitutivos e à pseudo-força térmica fraca
- Parser e `main.cpp` aceitam caminhos CSV relativos ao YAML, colunas configuráveis e registram `fluid_csv`/`thermal_csv` no `metadata.json`
- Manual, `docs/input-spec.md`, `docs/architecture.md`, `docs/thermal-coupling.md` e `AGENTS.md` atualizados
- Adicionados testes C++ para interpolação, campos CSV e parser dos novos modos
- **128/128 C++ verdes + 27/27 Python verdes**

## 2026-06-01 — Codex — Casos APB operacionais com histórico de lama
- Criado `data/apb/mud_schedule_example.csv` com grade `t_h,z_m,p_wall_Pa,T_wall_K`
- Criados `cases/apb/apb_1d_constant_mud.yaml`, `apb_1d_schedule_mud_temperature.yaml` e `apb_2d_layered_schedule_Q8.yaml`
- Os casos 1D usam halita com fluência ativa (DM+EDMT) e integrador implícito adaptativo; o caso agendado lê pressão e temperatura do CSV
- O caso 2D Q8 usa o mesmo histórico operacional, camadas litológicas visuais e `geostatic_mode: depth_profile`; roda com `implicit_adaptive` para evitar instabilidade explícita
- Teste Python novo roda os casos operacionais 1D/2D, exige fechamento finito positivo e confere valores de `p_wall_Pa`/`T_wall_K`
- Manual e `docs/post-processing.md` atualizados com comandos dos casos APB
- **128/128 C++ verdes + 28/28 Python verdes**

## 2026-06-01 — Codex — Benchmark de custo da pressão na parede
- Criado `post/benchmark_wall_pressure.py` para gerar YAMLs temporários Q8 2D e comparar `fluid.mode: constant`, `hydrostatic_depth_profile` e `csv_time_depth_profile`
- O script aceita presets `smoke|standard|full`, lista de threads OpenMP, `--dry-run`, limite de execuções e timeout por caso
- Saídas consolidadas em `results/benchmark_wall_pressure/`: JSON bruto, CSV plano, relatório Markdown e gráficos tempo × GDL, sobrecusto × GDL e breakdown montagem/solve/constitutivo
- Adicionados testes Python para matriz do benchmark, geração de relatório/gráficos e execução real mínima de um caso hidrostático Q8
- Manual e `docs/post-processing.md` atualizados com comandos do benchmark dedicado APB
- **128/128 C++ verdes + 31/31 Python verdes**

## 2026-06-04 — Codex — Diagnóstico de tensão APB na parede
- Criado `physics/stress_utils.hpp` para centralizar `sigma_theta`, tensão média, desviador, `J2` e `sigma_ef`
- Criado `StressSampler`/`StressDiagnosticsWriter` para gravar `wall_stress.csv` e, com escopo `all_gauss`, `stress_profile.csv`
- Parser aceita `output.stress_diagnostics` e `output.stress_diagnostics_scope: wall|all_gauss`; o default preserva todos os casos existentes
- Integradores explícito e implícito, inclusive schedules, escrevem tensões a partir de `TimeState::sigma_gp` sem alterar física, cargas, K ou constitutivos
- `metadata.json` registra se o diagnóstico de tensão estava ativo e o escopo usado
- Adicionados testes C++ para convenção APB `sigma_theta_comp_Pa = -sigma_theta`, tensão desviadora/von Mises, amostragem 1D e perfil 2D de parede
- Verificado caso real temporário `results/_tmp_stress_diagnostics_1d.yaml`, gerando `results/_tmp_stress_diagnostics_1d/wall_stress.csv`
- **132/132 C++ verdes** (rodado em dois blocos por timeout do comando global: 1–111 e 112–132). Testes Python não rodaram nesta sessão porque `pytest` não está instalado no Python do sistema nem no runtime empacotado.

---
## 2026-06-04 — Codex — Auditoria de sincronizacao vendorizada no lot-salt-suite
- Revisadas as atualizacoes locais trazidas para `external/saltcreep`: entrada CSV `t,z` para pressao/temperatura de parede, casos APB operacionais, benchmark de pressao de parede, `StressSampler` e diagnosticos `wall_stress.csv`/`stress_profile.csv`
- Restaurada a integracao CMake com o Eigen oficial do `lot-salt-suite` por `LSS_SALTCREEP_FORCE_LSS_EIGEN`, proxy `lss_eigen_proxy/Eigen`, macro `LSS_SALTCREEP_EIGEN_MODE` e teste `tests/test_eigen_source.cpp`
- Adicionado `/FS` no MSVC para evitar disputa de escrita de PDB em build paralelo
- Build baseline com Eigen interno: `cmake --build external\saltcreep\build_baseline --config Debug -j` verde
- Build LSS Eigen: `cmake --build external\saltcreep\build_lss_eigen --config Debug -j` verde
- `ctest --test-dir external\saltcreep\build_baseline -C Debug --output-on-failure -j 4`: 133/133 verdes
- `ctest --test-dir external\saltcreep\build_lss_eigen -C Debug --output-on-failure -j 4`: 133/133 verdes
- `python -m unittest discover -s external\saltcreep\tests\python -p "test_*.py"`: 31/31 verdes, com 7 skips esperados
- Casos APB `apb_1d_constant_mud.yaml`, `apb_1d_schedule_mud_temperature.yaml` e `apb_2d_layered_schedule_Q8.yaml` executados no binario baseline com fechamento final finito
- No repositório integrador, o `CMakeLists.txt` raiz passou a compilar as novas fontes vendorizadas `TimeDepthTable.cpp` e `StressSampler.cpp`; 112/112 Catch2 do `lot-salt-suite` permaneceram verdes
- **133/133 C++ verdes em baseline + 133/133 C++ verdes com LSS Eigen + 31/31 Python verdes**

---
*Próxima entrada: o agente que iniciar a próxima etapa registra aqui.*
