# dev-log — lot-salt-suite

> **LEITURA OBRIGATÓRIA** para Claude Code e Codex na abertura de qualquer sessão.
> Auto-atualizado por `tools/update_devlog.py` após cada `git commit` ou `git push`.
> Invoke `/update-devlog` manualmente quando necessário.

---

## Estado atual do projeto

```
Fase ativa  : 8.1 concluida (substitutibilidade LOT/PKN com adapter saltcreep ocioso)
Branch      : main
Repositório : https://github.com/Themisson/lot-salt-suite
Último push : 2026-06-03
Testes C++  : 112/112 Catch2 lot-salt-suite passaram com LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON em 2026-06-04
Testes Py   : 3 unittest (3 passaram em 2026-06-01)
Baselines   : 4 capturados (LOT_APB_v5)
Saltcreep   : 126/126 testes Catch2 migrado (auto-detect ON, sem flag manual)
Eigen decisao: MIGRATION_COMPLETED
CMake 4     : SUPORTADO (CMAKE_POLICY_VERSION_MINIMUM 3.5, sem flag manual)
VS generator: SUPORTADO (LSS_LOT_SIM_EXECUTABLE via $<TARGET_FILE:lot-sim>)
WDAC tests  : SUPORTADO (LSS_ENABLE_CLI_SUBPROCESS_TESTS=OFF desativa apenas subprocess CLI)
```

### Próximas tarefas (Fase 6)

- [x] Definir governanca de `external/saltcreep/` como dependencia vendorizada ativa
- [x] Auditar caminho LOT/PKN nos legados sem modificar `legance/`
- [x] Catalogar modelos nao PKN como nao prioritarios
- [x] Criar contrato YAML/C++ LOT/PKN com casos sintaticos e migrado BUZ67D
- [x] Implementar `lot::BreakdownDetector` sintetico com testes Catch2
- [x] Criar esqueleto sintetico de `lot::PknModel` com testes Catch2
- [x] Auditar R09 antes de regressao numerica PKN legado x moderno
- [x] Implementar `lot::PknModel` fisico minimo em SI com series temporais sinteticas
- [x] Conectar LOT/PKN ao CLI moderno com saida CSV/JSON sem regressao legado
- [x] Executar ensaio comparativo controlado R09 (`/(pi*22)` vs `/(pi*2)`) sem alterar legado
- [x] Criar pos-processamento moderno minimo LOT/PKN para CSV/JSON sem regressao legado
- [x] Registrar politica C++ first, Python postprocess only
- [x] Implementar `LeakoffModel` C++ estruturado com testes Catch2
- [x] Auditar compatibilidade Eigen do saltcreep sem remover copias Eigen
- [x] Provar forcadamente que saltcreep compila/testa com `include/Eigen` (Fase 6.10B)
- [x] Migrar `include/Eigen` como modo integrado oficial do saltcreep com auto-deteccao (Fase 6.11)

### Achados críticos da auditoria (não alterar sem revisar docs/08_known_issues.md)

| ID | Achado | Impacto |
|----|--------|---------|
| FA01 | `e0` interno em **[1/min]** — LOTTeste.cpp divide por 60 explicitamente | Crítico |
| FA02 | Temperatura SESTSAL em **[°C]** — Q_R é parâmetro empírico, não físico em K | Alto |
| FA03 | Sinal: **compressão positiva** (mecânica dos solos) | Confirmado |
| FA04 | Acoplamento sal→APB é **sequencial fraco** (staggered) | Confirmado |

---

## Entradas de sessão

---

### [2026-06-04] Fase 8.1 — Substitutibilidade LOT/PKN com adapter saltcreep ocioso — Codex

**Status:** Concluido nesta sessao.

**Objetivo:** Provar que a presenca/construcao de `SaltCreepSaltcreepAdapter`
nao altera resultados LOT/PKN enquanto o caminho fisico LOT/PKN ainda nao chama
sal.

**Mudanca implementada:**
- Criado `tests/cpp/test_lot_pkn_salt_adapter_substitutability.cpp`.
- O teste executa `lot_pkn_minimal.yaml` e `lot_pkn_with_leakoff.yaml` em duas
  condicoes: referencia com `NullSaltCreepInterface` presente e adapter real
  construido/disponivel, mas ocioso.
- A comparacao e exata em memoria para `PknResult` e byte a byte para
  `result.json` e `timeseries.csv`.
- Um spy local de `SaltCreepInterface` e o contador `backend_build_count()` do
  adapter confirmam que o sal nao foi chamado pelo fluxo LOT/PKN.

**Resultado de isolamento:**
- `SaltCreepSaltcreepAdapter::backend_build_count() == 0`.
- `SaltCreepAdapterState::step_count() == 0`.
- `SpySaltCreepInterface::call_count() == 0`.
- Resultados LOT/PKN identicos com e sem adapter real presente.

**Limite deliberado:**
- Nao foi criado ponto de injecao em `PknRunner`.
- Nao ha acoplamento LOT-sal, PKN-sal ou APB-sal.
- Nenhum arquivo em `external/saltcreep/`, modelos fisicos, LOT/PKN, APB,
  parser, writer, baselines, `legance/` ou `legacy/` foi alterado.
- Nenhum commit ou push foi executado por instrucao explicita desta fase.

**Testes/builds executados:**
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 112/112 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt|bridge" --output-on-failure`
  passou 59/59 testes.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK` em `validate` e `run`.
- `lot_pkn_with_leakoff.yaml` retornou `OK` em `validate` e `run`.
- `buz67d_pkn.yaml` retornou `OK` em `validate` e `run`.
- Saidas manuais geradas em:
  `results\lot_pkn_minimal_substitutability_review`,
  `results\lot_pkn_with_leakoff_substitutability_review` e
  `results\buz67d_pkn_substitutability_review`.

---

### [2026-06-03] Fase 8.0 — Pressao dinamica no SaltCreepTimeBridge e Adapter — Codex

**Status:** Concluido nesta sessao.

**Objetivo:** Permitir que `SaltCreepTimeBridge` e
`SaltCreepSaltcreepAdapter` aceitem pressao de parede variavel por passo/query
temporal, mantendo o caso de pressao constante como comportamento valido e
mantendo LOT/PKN/APB desacoplados.

**Mudanca implementada:**
- `SaltCreepTimeBridge` ganhou sobrecargas `advance_by(dt_s, wall_pressure_Pa)`
  e `advance_to(target_time_s, wall_pressure_Pa)`.
- A implementacao interna passou a usar um campo de pressao por degrau para que
  o `TimeIntegrator` veja a diferenca entre a pressao do inicio e do fim do
  passo.
- As sobrecargas antigas sem pressao continuam preservadas e usam a pressao
  inicial configurada.
- `SaltCreepSaltcreepAdapter::evaluate_wall_response()` passou a encaminhar
  `query.wall_pressure_Pa` para o bridge, removendo a rejeicao de pressao
  dinamica.
- Criado `tests/cpp/test_salt_creep_time_bridge_dynamic_pressure.cpp`.
- Testes do adapter foram atualizados para cobrir pressao dinamica, tempo
  inicial configurado e rejeicao de pressao dinamica invalida.

**Limite deliberado:**
- A pressao dinamica e aceita apenas no contrato bridge/adapter por query
  temporal; LOT/PKN/APB ainda nao alimentam o adapter automaticamente.
- O bridge continua usando material elastico e campo termico neutro nesta prova.
- Nenhum arquivo em `external/saltcreep/`, modelos fisicos, LOT/PKN, APB,
  parser, writer, baselines, `legance/` ou `legacy/` foi alterado.
- Nenhum commit ou push foi executado por instrucao explicita desta fase.

**Testes/builds executados:**
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 110/110 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt|bridge" --output-on-failure`
  passou 57/57 testes de contrato/adapter/backend/bridge de sal.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_dynamic_pressure_review`.

---

### [2026-06-03] Fase 7.9 — Adapter conectado ao SaltCreepTimeBridge — Codex

**Status:** Concluido nesta sessao.

**Objetivo:** Fazer `SaltCreepSaltcreepAdapter` usar `SaltCreepTimeBridge`
persistente como backend temporal interno, mantendo LOT/PKN/APB desacoplados.

**Mudanca implementada:**
- `SaltCreepSaltcreepAdapter` passou a mapear `SaltCreepAdapterConfig` para
  `SaltCreepTimeBridgeConfig`.
- O `BackendCache` opaco do adapter agora guarda um `SaltCreepTimeBridge`.
- `evaluate_wall_response()` avanca o bridge ate `query.time_s`, converte o
  resultado para `SaltCreepResponse` e registra `SaltCreepAdapterState`.
- O target principal deixou de compilar diretamente os fontes minimos do
  `external/saltcreep`; a rota temporal fica atras de
  `lss_saltcreep_time_bridge`.
- Criado `tests/cpp/test_salt_creep_saltcreep_adapter_time_bridge.cpp`.
- Criado `docs/29_saltcreep_adapter_time_bridge_connection.md`.

**Politica de pressao:** Nesta fase, `query.wall_pressure_Pa` deve ser igual a
`config.wall_pressure.initial_wall_pressure_Pa`. Pressao dinamica e rejeitada
ate o bridge suportar historico/campo temporal de pressao.

**Limite deliberado:**
- O bridge usa material elastico, campo termico neutro e pressao constante.
- LOT/PKN/APB seguem sem instanciar o adapter de sal.
- Nenhum arquivo em `external/saltcreep/`, modelos fisicos, LOT/PKN, APB,
  parser ou writer foi alterado.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 102/102 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt|bridge" --output-on-failure`
  passou 49/49 testes de contrato/adapter/backend/bridge de sal.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_adapter_bridge_review`.

---

### [2026-06-03] Fase 7.8 — Target bridge para TimeIntegrator — Codex

**Status:** Concluido nesta sessao.

**Objetivo:** Criar uma camada C++/CMake intermediaria para compilar e executar
`TimeIntegrator::advance()` sem vazar os headers de I/O do `external/saltcreep`
para os headers publicos ou targets principais do `lot-salt-suite`.

**Classificacao:** `TIME_BRIDGE_CONNECTED`.

**Mudanca implementada:**
- Criado `include/salt/SaltCreepTimeBridge.hpp` com API publica SI limpa.
- Criado `src/salt/SaltCreepTimeBridge.cpp`, unico arquivo do LSS que inclui
  `solver/TimeIntegrator.hpp`.
- Criado target CMake isolado `lss_saltcreep_time_bridge` com include order:
  proxy Eigen, `external/saltcreep/include`, depois `include/`.
- Criado target Catch2 `saltcreep_time_bridge_tests`, sem include publico para
  `external/saltcreep/include`.
- Criado `tests/cpp/test_salt_creep_time_bridge.cpp`.
- Criado `docs/28_saltcreep_time_bridge.md`.

**Limite deliberado:**
- O bridge ainda nao e chamado por `SaltCreepSaltcreepAdapter`.
- LOT/PKN/APB seguem desacoplados do sal temporal.
- Nenhum arquivo em `external/saltcreep/`, modelos fisicos, LOT/PKN, APB,
  parser ou writer foi alterado.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 97/97 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt|Bridge" --output-on-failure`
  passou 44/44 testes de contrato/adapter/backend/bridge de sal.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_time_bridge_review`.

---

### [2026-06-03] Fase 7.7 — Estado temporal persistido sem TimeIntegrator — Codex

**Status:** Concluido nesta sessao.

**Objetivo:** Resolver a fronteira tecnica do `TimeIntegrator` antes de tentar
usa-lo no adapter principal e persistir a rota minima do backend entre queries.

**Classificacao:** `TEMPORAL_STATE_READY_WITHOUT_TIMEINTEGRATOR` para o adapter
principal; `TIMEINTEGRATOR_BLOCKED_BY_INCLUDE_BOUNDARY` para a tentativa de
trazer `TimeIntegrator` ao target `lot-sim`/`lot_sim_tests`.

**Mudanca implementada:**
- Criado `docs/audits/saltcreep_timeintegrator_include_boundary.md`.
- Criado `docs/27_saltcreep_adapter_temporal_state.md`.
- `SaltCreepSaltcreepAdapter` passou a ter cache privado e opaco para
  elemento, material, malha, matriz de rigidez, vetor geostatico e graus fixos.
- `evaluate_wall_response()` continua montando somente a pressao de parede da
  query e registrando resposta em `SaltCreepAdapterState`.
- Criado `tests/cpp/test_salt_creep_saltcreep_adapter_temporal_state.cpp`.

**Limite deliberado:**
- `TimeIntegrator` nao foi conectado ao adapter principal porque
  `external/saltcreep/include/solver/TimeIntegrator.hpp` inclui
  `io/CaseParser.hpp`, nome que tambem existe em `include/io/CaseParser.hpp`.
- Nenhum arquivo em `external/saltcreep/`, LOT/PKN, APB ou modelos fisicos foi
  alterado.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 91/91 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt" --output-on-failure`
  passou 38/38 testes de contrato/adapter/backend de sal.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_adapter_temporal_state`.

---

### [2026-06-03] Revisão 7.6 — patch documental radial_strain — Claude Code

**Status:** Patch aplicado.

**Achado:** `radial_strain = u_r / r_i` é tecnicamente `ε_θ` (hoop strain),
não `ε_r` (radial strain). O sinal está correto para o contrato de dados, mas
a nomenclatura pode confundir em fases futuras com fluência real.

**Patch:** adicionada nota explicativa em
`docs/26_saltcreep_adapter_backend_minimum.md` clarificando a aproximação usada
e quando ela deve ser revisada.

**Verificações:** 88/88 Catch2 passaram. 3 validates LOT/PKN: OK.

---

### [2026-06-03] Fase 7.6 — Backend minimo do adapter saltcreep — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Conectar `SaltCreepSaltcreepAdapter::evaluate_wall_response()` a
uma rota real minima do backend `external/saltcreep`, mantendo LOT/PKN/APB
desacoplados do sal.

**Mudanca implementada:**
- `SaltCreepSaltcreepAdapter::is_available()` passa a retornar `true` para
  configuracoes suportadas pelo backend minimo.
- `state_` passa a ser `mutable` por constancia logica, permitindo registrar
  respostas em `evaluate_wall_response() const`.
- `evaluate_wall_response()` monta e executa uma rota elastica/geostatica com
  `build_mesh_L3`, `AxisymL3`, `ElasticIsotropic`, `Assembler`,
  `ConstantWallPressureField` e `ElasticSolver`.
- Criado `tests/cpp/test_salt_creep_saltcreep_adapter_backend.cpp`.
- Criado `docs/26_saltcreep_adapter_backend_minimum.md`.

**Limite deliberado:**
- `TimeIntegrator` permanece nos targets Catch2 controlados separados nesta
  fase. Ele nao foi linkado ao target principal para evitar conflito de include
  entre `external/saltcreep/include/io/CaseParser.hpp` e
  `include/io/CaseParser.hpp`.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 88/88 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt" --output-on-failure`
  passou 35/35 testes de contrato/adapter de sal.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_adapter_backend_review`.

**Verificacao de desacoplamento:**
- Busca em `src/lot`, `include/lot`, `apps/lot-sim.cpp`, `src/io` e
  `include/io` nao encontrou instanciacao de `SaltCreepSaltcreepAdapter` nem
  uso de `SaltCreepInterface` no caminho LOT/PKN.

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter`, `CaseParser`,
  `src/lot/`, `include/lot/`, APB e modelos fisicos sem alteracao.
- Nenhum script Python novo e nenhum acoplamento LOT/sal implementado.

---

### [2026-06-03] Fase 7.5 — Configuracao e state machine do adapter saltcreep — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Adicionar `SaltCreepAdapterConfig` e `SaltCreepAdapterState` para
preparar o futuro adapter real do `external/saltcreep`, mantendo o backend
desligado, `is_available() = false` e sem acoplar LOT/PKN/APB ao sal.

**Mudanca implementada:**
- Criados `include/salt/SaltCreepAdapterConfig.hpp` e
  `src/salt/SaltCreepAdapterConfig.cpp`.
- Criados `include/salt/SaltCreepAdapterState.hpp` e
  `src/salt/SaltCreepAdapterState.cpp`.
- `SaltCreepSaltcreepAdapter` agora aceita configuracao SI validada, inicializa
  estado local e expoe `config()` / `state()`.
- `evaluate_wall_response()` permanece neutro e nao chama o backend real.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 82/82 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "SaltCreep|saltcreep|salt" --output-on-failure`
  passou 29/29 testes de contrato/adapter de sal.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_salt_adapter_config_state`.

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter`, `CaseParser`,
  `src/lot/`, `include/lot/`, APB e modelos fisicos sem alteracao.
- Nenhum script Python novo e nenhum acoplamento LOT/sal implementado.

---

### [2026-06-03] Fase 7.4 — Tempo, geostatica e termico neutro no backend saltcreep — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Evoluir o caso controlado do backend `external/saltcreep` para
exercitar tempo, campo termico constante neutro, geostatica simplificada e
pressao de parede constante, sem ligar o backend ao adapter real e sem acoplar
LOT/PKN/APB ao sal.

**Auditoria:**
- Criado `docs/audits/saltcreep_backend_time_geostatic_case.md`.
- Classificacao: `TIME_THERMAL_GEOSTATIC_CONTROLLED_TEST_READY`.
- Achado: `TimeIntegrator` aceita `ThermalField`, vetor geostatico por ponto de
  Gauss, `WallPressureField` opcional e passos `advance(dt_s)`.

**Mudanca implementada:**
- Criado `tests/cpp/test_saltcreep_backend_time_geostatic_case.cpp`.
- `CMakeLists.txt` adiciona target separado
  `saltcreep_backend_time_geostatic_tests`.
- O teste usa `ElasticIsotropic`, `ProfileField::make_constant()` com
  `alpha_thermal = 0`, `ConstantWallPressureField`, geostatica explicita e
  `TimeIntegrator::advance()`.

**Resultado tecnico:**
- Caso neutro: dois passos temporais preservam a resposta elastica estatica
  contra `ElasticSolver`.
- Caso geostatico: compressao uniforme simplificada com parede externa fixa
  produz `u_r < 0`, fechamento positivo e `wall_closure_pct() > 0`.
- Nenhum output versionado e gerado pelo teste.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 68/68 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.
- `ctest --test-dir build -C Debug -R "Saltcreep backend" --output-on-failure`
  passou 4/4.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.

**Escopo alterado:**
- `CMakeLists.txt`
- `tests/cpp/test_saltcreep_backend_time_geostatic_case.cpp`
- `docs/audits/saltcreep_backend_time_geostatic_case.md`
- `docs/audits/saltcreep_backend_controlled_case.md`
- `docs/audits/saltcreep_radial_displacement_sign_audit.md`
- `docs/24_saltcreep_adapter_design.md`
- `docs/13_coupling_lot_apb_salt.md`
- `docs/16_saltcreep_governance.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/dev-log.md`
- `tools/docs_status.yaml`
- `docs/index.html`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `SaltCreepSaltcreepAdapter::is_available()` permanece `false`.
- `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter`, `CaseParser`,
  `src/lot/`, `include/lot/`, APB e modelos fisicos sem alteracao.
- Nenhum script Python novo e nenhum acoplamento LOT/sal implementado.

---

### [2026-06-03] Fase 7.3 — Caso C++ controlado do backend saltcreep — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Provar uma rota C++ direta e isolada para instanciar o nucleo do
`external/saltcreep` em um caso elastico sintetico, sem conectar o backend ao
`SaltCreepSaltcreepAdapter` real e sem acoplar LOT/PKN ao sal.

**Mudanca implementada:**
- Criado `tests/cpp/test_saltcreep_backend_controlled_case.cpp`.
- `CMakeLists.txt` adiciona o target separado
  `saltcreep_backend_controlled_tests`, que compila somente fontes minimas do
  backend para o caso de Lame.
- O target usa um proxy de Eigen no build dir, copiado de `include/Eigen/`,
  antes de `external/saltcreep/include`, preservando o Eigen oficial do projeto
  sem alterar as copias versionadas.
- Criado `docs/audits/saltcreep_backend_controlled_case.md`.

**Resultado tecnico:**
- Pressao interna positiva aplicada via `ConstantWallPressureField` produz
  deslocamento radial de parede para fora (`u_r > 0`) e fechamento nulo.
- Pressao externa/confinante positiva produz deslocamento para dentro
  (`u_r < 0`) e fechamento positivo `max(0, -u_r)`.
- Ambos os casos batem a solucao analitica de Lame no raio interno com erro
  relativo menor que `1e-6`.
- Hipoteses do caso: elasticidade linear, pequenas deformacoes, sem fluencia,
  sem dano, sem acoplamento termico e geometria sintetica.
- Conclusao: a API C++ direta do backend e viavel para caso elastico controlado,
  mas o adapter real ainda exige configuracao completa de malha, material,
  temperatura, geostatica, pressoes e integrador.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 66/66 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.

**Escopo alterado:**
- `CMakeLists.txt`
- `tests/cpp/test_saltcreep_backend_controlled_case.cpp`
- `docs/audits/saltcreep_backend_controlled_case.md`
- `docs/audits/saltcreep_radial_displacement_sign_audit.md`
- `docs/24_saltcreep_adapter_design.md`
- `docs/13_coupling_lot_apb_salt.md`
- `docs/16_saltcreep_governance.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/dev-log.md`
- `tools/docs_status.yaml`
- `docs/index.html`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `SaltCreepSaltcreepAdapter::is_available()` permanece `false`.
- `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter`, `CaseParser`,
  `src/lot/`, `include/lot/`, APB e modelos fisicos sem alteracao.
- Nenhum script Python novo e nenhum acoplamento LOT/sal implementado.

---

### [2026-06-03] Fase 7.2 — SaltCreepSaltcreepAdapter experimental e isolado — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Criar o primeiro adapter C++ concreto para preparar a integracao
com `external/saltcreep`, mantendo LOT/PKN, APB e o backend de sal sem
acoplamento fisico nesta fase.

**Auditoria de sinal radial:**
- Criado `docs/audits/saltcreep_radial_displacement_sign_audit.md`.
- Resultado: `SIGN_CONFIRMED_FOR_WALL_DISPLACEMENT_OUTPUT`.
- Evidencias auditadas: `wall_displacement_m()` retorna `state_.u_total[0]`,
  `wall_closure_pct()` calcula `-u_r/Ri*100`, `TimeOutput.cpp` grava
  `wall_disp_m` assinado e `u_wall_m` positivo, e testes do saltcreep exigem
  `wall_displacement_m() < 0` para fechamento.

**Mudanca implementada:**
- `include/salt/SaltCreepSaltcreepAdapter.hpp` define o adapter experimental.
- `src/salt/SaltCreepSaltcreepAdapter.cpp` implementa validacao de query,
  `is_available() = false`, resposta neutra valida e
  `radial_closure_from_displacement()`.
- `tests/cpp/test_salt_creep_saltcreep_adapter.cpp` cobre compilacao,
  disponibilidade documentada, resposta neutra, rejeicoes de query invalida e
  convencao `radial_closure_m = max(0, -radial_displacement_m)`.
- O backend real nao foi conectado porque ainda nao ha API simples do tipo
  "avaliar resposta de parede"; a execucao real exige malha, elemento,
  material, temperatura, geostatica, pressao de parede e integrador.

**Testes/builds executados:**
- `Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue`
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 64/64 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_salt_adapter_review`.

**Escopo alterado:**
- `CMakeLists.txt`
- `include/salt/SaltCreepSaltcreepAdapter.hpp`
- `src/salt/SaltCreepSaltcreepAdapter.cpp`
- `tests/cpp/test_salt_creep_saltcreep_adapter.cpp`
- `docs/audits/saltcreep_radial_displacement_sign_audit.md`
- `docs/24_saltcreep_adapter_design.md`
- `docs/13_coupling_lot_apb_salt.md`
- `docs/16_saltcreep_governance.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/22_saltcreep_interface_contract.md`
- `docs/23_lot_salt_sign_convention.md`
- `docs/dev-log.md`
- `tools/docs_status.yaml`
- `docs/index.html`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `PknModel`, `PknRunner`, `LeakoffModel`, `ResultWriter`, `CaseParser`,
  `src/lot/`, `include/lot/`, `src/io/` e `include/io/` sem alteracao.
- Nenhum script Python novo, nenhum adapter real, nenhuma chamada ao saltcreep e
  nenhum acoplamento LOT/sal implementado.

---

### [2026-06-03] Revisão 7.1 — patch mínimo radial_closure_m — Claude Code

**Status:** Patch aplicado e commitado.

**Achado:** `NullSaltCreepInterface::evaluate_wall_response` em `src/salt/SaltCreepInterface.cpp`
atribuía explicitamente `radial_displacement_m`, `radial_strain` e
`effective_closure_pressure_Pa`, mas omitia `radial_closure_m`. O campo estava
correto via default do struct, mas a omissão era inconsistente e potencialmente
confusa para futuros leitores e adapters.

**Patch:** adicionada linha `response.radial_closure_m = 0.0;` para tornar a
implementação self-documenting, consistente com todos os outros campos.

**Verificações:**
- 57/57 Catch2 passaram após o patch.
- 3 validates LOT/PKN: OK.
- `external/saltcreep/`, `legance/`, `legacy/`, `PknModel`, `PknRunner`,
  `LeakoffModel`, `ResultWriter`, `CaseParser` e baselines intocados.

---

### [2026-06-03] Fase 7.1 — Convencao de sinais LOT-saltcreep — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Fixar o contrato de sinais, unidades e fronteira de dados entre
LOT/PKN e um futuro adapter para `external/saltcreep`, sem acoplamento fisico e
sem alterar solver/modelos.

**Mudanca implementada:**
- `SaltCreepResponse` passa a expor `radial_closure_m` como magnitude positiva
  de fechamento.
- O contrato LOT-sal define `wall_pressure_Pa >= 0` como pressao compressiva
  positiva.
- `radial_displacement_m` e deslocamento radial assinado: positivo para fora e
  negativo para dentro.
- `radial_closure_m = max(0, -radial_displacement_m)`.
- `radial_strain` segue o sinal do deslocamento radial.
- `effective_closure_pressure_Pa >= 0` permanece compressivo positivo.
- `docs/23_lot_salt_sign_convention.md` criado como referencia central.

**Testes/builds executados:**
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 57/57 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.

**Escopo alterado:**
- `include/salt/SaltCreepTypes.hpp`
- `tests/cpp/test_salt_creep_interface.cpp`
- `docs/08_known_issues.md`
- `docs/13_coupling_lot_apb_salt.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/22_saltcreep_interface_contract.md`
- `docs/23_lot_salt_sign_convention.md`
- `docs/dev-log.md`
- `tools/docs_status.yaml`
- `docs/index.html`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `PknModel`, `LeakoffModel`, `PknRunner`, `ResultWriter`, `CaseParser`,
  `src/lot/` e `include/lot/` sem alteracao.
- Nenhum adapter real, chamada ao saltcreep ou acoplamento LOT/sal implementado.

---

### [2026-06-03] Fase 7.0 — SaltCreepInterface C++ minima e nao acoplada — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Criar uma fronteira C++ minima, testavel e estavel para futura
integracao LOT/APB/sal, sem acoplar `PknModel` ao sal e sem chamar
`external/saltcreep`.

**Mudanca implementada:**
- `include/salt/SaltCreepTypes.hpp` define `WallPressureSample`,
  `SaltCreepQuery` e `SaltCreepResponse` em SI.
- `include/salt/SaltCreepInterface.hpp` define a interface abstrata e
  `NullSaltCreepInterface`.
- `src/salt/SaltCreepInterface.cpp` valida entradas finitas e rejeita tempo,
  pressao, temperatura e posicao radial invalidos.
- `NullSaltCreepInterface` retorna `is_available() = false` e resposta neutra
  valida (`u_r = 0`, `strain = 0`, `effective_closure_pressure_Pa = 0`,
  `valid = true`) para query valida.
- `tests/cpp/test_salt_creep_interface.cpp` adiciona 9 testes Catch2 do
  contrato.

**Testes/builds executados:**
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
- Resultado: 56/56 Catch2 passaram no modo padrao
  `LSS_ENABLE_CLI_SUBPROCESS_TESTS=ON`; fallback WDAC `OFF` nao foi necessario.

**Validacao manual CLI:**
- `lot_pkn_minimal.yaml` retornou `OK`.
- `lot_pkn_with_leakoff.yaml` retornou `OK`.
- `buz67d_pkn.yaml` retornou `OK`.
- `lot-sim run --mode lot-pkn` gerou `result.json` e `timeseries.csv` em
  `results\lot_pkn_minimal_salt_interface_review`.

**Escopo alterado:**
- `include/salt/SaltCreepTypes.hpp`
- `include/salt/SaltCreepInterface.hpp`
- `src/salt/SaltCreepInterface.cpp`
- `tests/cpp/test_salt_creep_interface.cpp`
- `docs/22_saltcreep_interface_contract.md`
- `CMakeLists.txt`
- `docs/07_target_architecture.md`
- `docs/13_coupling_lot_apb_salt.md`
- `docs/16_saltcreep_governance.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/dev-log.md`
- `tools/docs_status.yaml`
- `docs/index.html`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/`, `tests/baselines/` e
  `postprocess/scripts/` preservados.
- `PknModel`, `LeakoffModel`, `PknRunner`, `ResultWriter`, `CaseParser` e APB
  sem alteracao.
- Nenhum script Python novo e nenhum acoplamento fisico implementado.

---

### [2026-06-03] docs — permissões operacionais Claude Code — Claude Code

**Status:** Concluído.

**Objetivo:** Codificar política permanente de autorização operacional para reduzir
confirmações desnecessárias durante desenvolvimento, sem relaxar restrições de segurança.

**Arquivos alterados:**
- `CLAUDE.md` — nova seção "Autorização operacional — Claude Code" com tabelas allow/confirm
- `AGENTS.md` — nova seção compacta "Autorização operacional — Claude Code / Codex"
- `docs/14_developer_workflow.md` — nova seção "Claude Code operational permissions"
- `.claude/settings.json` — `git push` movido de deny para allow; `git push --force` permanece em deny; adicionados paths `build/Debug/lot-sim.exe`, `Release`, `RelWithDebInfo`
- `docs/dev-log.md` — esta entrada
- `docs/index.html` — regenerado

**Nenhum código C++, CMake, solver ou arquivo de teste foi alterado.**

---

### [2026-06-03] Fase 6.12B — CLI subprocess tests opcionais para Windows WDAC — Codex
**Status:** Concluido nesta sessao.

**Objetivo:** Permitir que ambientes Windows com WDAC/Smart App Control bloqueando
binarios nao assinados executem toda a suite Catch2 sem os dois testes que spawnam
`lot-sim.exe` como subprocesso, mantendo o padrao `ON` para CI e maquinas normais.

**Mudanca implementada:**
- `CMakeLists.txt` adiciona `option(LSS_ENABLE_CLI_SUBPROCESS_TESTS ... ON)`.
- `lot_sim_tests` recebe `LSS_ENABLE_CLI_SUBPROCESS_TESTS=1` quando a opcao esta `ON`
  e `=0` quando esta `OFF`.
- `tests/cpp/test_pkn_runner.cpp` compila os dois testes `CLI run succeeds...` somente
  quando a macro esta ativa; no modo `OFF`, registra um teste sentinela
  `CLI subprocess tests disabled by CMake option`.
- `docs/14_developer_workflow.md` documenta o fluxo Windows WDAC/Smart App Control com
  `-DLSS_ENABLE_CLI_SUBPROCESS_TESTS=OFF` e validacao manual de CLI.

**Testes/builds executados:**
- Modo padrao `ON`: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`,
  `cmake --build build --config Debug -j`, `ctest --test-dir build -C Debug --output-on-failure`.
  Resultado: 47/47 Catch2 passaram nesta execucao.
- Modo `OFF`: `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug -DLSS_ENABLE_CLI_SUBPROCESS_TESTS=OFF`,
  `cmake --build build --config Debug -j`, `ctest --test-dir build -C Debug --output-on-failure`.
  Resultado: 46/46 Catch2 passaram; os dois testes de subprocesso foram substituidos por
  um teste sentinela.
- Validates manuais: `lot_pkn_minimal.yaml`, `lot_pkn_with_leakoff.yaml` e
  `buz67d_pkn.yaml` retornaram `OK`.
- Run manual: `lot_pkn_minimal.yaml --mode lot-pkn` gerou `result.json` e
  `timeseries.csv` em `results\lot_pkn_minimal_wdac_manual`.

**Escopo alterado:**
- `CMakeLists.txt`
- `tests/cpp/test_pkn_runner.cpp`
- `docs/14_developer_workflow.md`
- `docs/dev-log.md`
- `docs/index.html`
- `tools/docs_status.yaml`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/`, `include/Eigen/`,
  `external/saltcreep/include/Eigen/` e `tests/baselines/` preservados.
- Modelos fisicos, `PknModel`, `LeakoffModel`, `PknRunner`, `ResultWriter` e
  `CaseParser` sem alteracao.

---

### [2026-06-02] Fase 6.12 — Compatibilidade Windows Visual Studio / CMake 4 — Claude Code
**Status:** Concluido nesta sessao.

**Objetivo:** Corrigir dois problemas ao buildar em nova maquina Windows com VS2026 e CMake 4.3:
1. yaml-cpp via FetchContent falhava com CMake 4 (`Compatibility with CMake < 3.5 has been removed`)
2. Testes CLI em `test_pkn_runner.cpp` procuravam `build/lot-sim.exe` mas VS usa `build/Debug/lot-sim.exe`

**Mudancas implementadas:**

**1. CMakeLists.txt — compatibilidade CMake 4:**
- Adicionado `set(CMAKE_POLICY_VERSION_MINIMUM 3.5 ...)` antes de `FetchContent_MakeAvailable(yaml-cpp)`.
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug` agora funciona sem flag manual em CMake 4.

**2. CMakeLists.txt — path do executavel via generator expression:**
- `target_compile_definitions(lot_sim_tests PRIVATE LSS_LOT_SIM_EXECUTABLE="$<TARGET_FILE:lot-sim>")` no target `lot_sim_tests`.
- Resolve para caminho absoluto correto em qualquer gerador (single-config e multi-config).

**3. CMakeLists.txt — catch_discover_tests em modo PRE_TEST:**
- `DISCOVERY_MODE PRE_TEST` evita erro `unknown error` no post-build step do MSBuild.
- Descuberta de testes adiada para o momento em que `ctest` e invocado.

**4. tests/cpp/test_pkn_runner.cpp — funcao lot_sim_executable() robusta:**
- Usa `LSS_LOT_SIM_EXECUTABLE` (definido pelo CMake via generator expression).
- Fallback: probe Debug/Release/RelWithDebInfo/MinSizeRel e raiz `build/`.

**Resultados:**
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`: OK sem flag manual
- `cmake --build build --config Debug -j`: OK, `build\Debug\lot-sim.exe` e `build\Debug\lot_sim_tests.exe`
- `ctest --test-dir build -C Debug --output-on-failure`: **45/47 passaram**
- 2 testes CLI falharam exclusivamente por WDAC enforcement mode nesta maquina
  (`UsermodeCodeIntegrityPolicyEnforcementStatus = 2`). O path para `lot-sim.exe` esta correto;
  o kernel bloqueia CreateProcess para binarios nao assinados.
  Workaround: desabilitar Smart App Control ou assinar os binarios.
  Ver `docs/14_developer_workflow.md` — secao "Windows / Visual Studio / CMake 4".

**Escopo alterado:**
- `CMakeLists.txt` — tres patches: CMAKE_POLICY_VERSION_MINIMUM, LSS_LOT_SIM_EXECUTABLE, DISCOVERY_MODE PRE_TEST
- `tests/cpp/test_pkn_runner.cpp` — lot_sim_executable() robusto com fallback multi-config
- `docs/14_developer_workflow.md` — secao "Windows / Visual Studio / CMake 4 notes"
- `docs/dev-log.md`

**Nao alterado:**
- `legance/`, `legacy/`, `external/saltcreep/` — preservados
- `include/Eigen/` — preservado
- Modelos fisicos, PknModel, LeakoffModel, PknRunner, CaseParser, ResultWriter — sem alteracao
- Baselines — preservados

---

### [2026-06-01 21:51] `eac8fac` — Themisson
**Commit:** `feat(saltcreep): migrate to lss Eigen by default via auto-detection (Fase 6.11)`
**Testes C++:** 7 arquivos | **Testes Python:** 1 arquivos
**Último resultado ctest:** nenhum (módulos ainda não implementados)
**Arquivos alterados:**
- `docs/13_coupling_lot_apb_salt.md`
- `docs/16_saltcreep_governance.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/20_saltcreep_eigen_migration_plan.md`
- `docs/21_saltcreep_eigen_migration_result.md`
- `docs/index.html`
- `tools/docs_status.yaml`

**⚠ Modificações em external/saltcreep/:**
- `external/saltcreep/CMakeLists.txt`
> Atualizar a seção 'Modificações em andamento no saltcreep' abaixo.

---

### [2026-06-01] Fase 6.11 — Migracao controlada Eigen oficial no saltcreep — Claude Code
**Status:** Concluido nesta sessao.
**Decisao:** `MIGRATION_COMPLETED`

**Objetivo:** Tornar `include/Eigen` o Eigen ativo do saltcreep por padrao no contexto do
`lot-salt-suite`, sem flags manuais, preservando `external/saltcreep/include/Eigen` como fallback.

**Mudanca implementada:**
- `external/saltcreep/CMakeLists.txt` agora auto-detecta o contexto `lot-salt-suite` verificando
  se `../../include/Eigen` existe. Se sim, `LSS_SALTCREEP_FORCE_LSS_EIGEN` default = `ON`.
- Fora da arvore do projeto (standalone), o default e `OFF` (Eigen interno — sem quebra).
- Mensagem de fallback atualizada: `Saltcreep Eigen mode: internal fallback`.

**Tres provas objetivas (build migrado sem flag manual):**
1. CMake configure: `Saltcreep Eigen mode: lot-salt-suite include/Eigen (proxy at ...)`
2. `tests_unit.vcxproj` `AdditionalIncludeDirectories`: `lss_eigen_proxy` PRIMEIRO
3. Macro runtime `test_eigen_source`: `LSS_SALTCREEP_EIGEN_MODE = lss`

**Testes/builds executados:**
- Build migrado (auto-detect ON, sem flag): 126/126 Catch2 passaram
- Caso APB `mud_gradient_1d_8p5ppg.yaml`: `closure=0.300817%` (identico ao baseline)
- lot-salt-suite: 47/47 Catch2, validates OK (3 casos), run lot-pkn OK

**Escopo alterado:**
- `external/saltcreep/CMakeLists.txt` — auto-deteccao de contexto, default ON dentro de lot-salt-suite
- `docs/20_saltcreep_eigen_migration_plan.md` — decisao `MIGRATION_COMPLETED`, opcao D
- `docs/16_saltcreep_governance.md` — politica Eigen atualizada
- `docs/13_coupling_lot_apb_salt.md` — nota de dependencia Eigen atualizada
- `docs/17_lot_pkn_roadmap.md` — Fase 6.11 registrada
- `docs/21_saltcreep_eigen_migration_result.md` — criado com resultado completo
- `docs/dev-log.md`, `tools/docs_status.yaml`

**Nao alterado:**
- `external/saltcreep/include/Eigen/` — preservado
- `include/Eigen/` — preservado
- `legance/`, `legacy/`, `tests/baselines/` — preservados
- Modelos fisicos, casos e resultados do saltcreep — preservados
- `PknModel`, `LeakoffModel`, `PknRunner`, `ResultWriter`, `CaseParser` — sem alteracao

---

### [2026-06-01] Fase 6.10B — Prova forcada Eigen oficial no saltcreep — Claude Code
**Status:** Concluido nesta sessao.
**Decisao:** `PROVEN_SAFE_TO_MIGRATE`

**Problema resolvido:** A Fase 6.10 usou `CMAKE_CXX_FLAGS=-I...` para adicionar `include/` ao
build experimental do saltcreep, mas o gerador Visual Studio listava `external/saltcreep/include`
ANTES do include forcado no `AdditionalIncludeDirectories` do `.vcxproj`. Portanto a Fase 6.10
nao provou que o saltcreep usou de fato `include/Eigen`.

**Solucao implementada:**
- `external/saltcreep/CMakeLists.txt` recebeu `option(LSS_SALTCREEP_FORCE_LSS_EIGEN ... OFF)`.
- Quando `ON`: o CMake cria `${CMAKE_BINARY_DIR}/lss_eigen_proxy/` com apenas `Eigen/` (copiado
  de `include/Eigen/`) e o adiciona com `BEFORE PRIVATE` antes de `PRIVATE include`.
- Isso garante que `<Eigen/Core>` resolva para o proxy (LSS Eigen) primeiro, sem conflitar com
  headers relativos do saltcreep como `"io/CaseParser.hpp"`.
- `external/saltcreep/tests/test_eigen_source.cpp` confirma o modo em runtime via macro
  `LSS_SALTCREEP_EIGEN_MODE` setada pelo CMake.

**Tres provas objetivas:**
1. CMake configure: `Saltcreep Eigen mode: lot-salt-suite include/Eigen (proxy at ...)`
2. `tests_unit.vcxproj` `AdditionalIncludeDirectories`: `lss_eigen_proxy` PRIMEIRO, `saltcreep/include` SEGUNDO
3. Macro runtime `test_eigen_source`: baseline→`internal`, forcado→`lss`

**Testes/builds executados:**
- Baseline (`OFF`): 126/126 Catch2 passaram em 996.27 s
- Forcado (`ON`): 126/126 Catch2 passaram em 1024.06 s
- Caso APB `mud_gradient_1d_8p5ppg.yaml`: baseline `closure=0.300817%`, forcado `closure=0.300817%`
- lot-salt-suite: 47/47 Catch2, validates OK, run lot-pkn OK

**Escopo alterado:**
- `external/saltcreep/CMakeLists.txt` — opcao + proxy dir + BEFORE PRIVATE + macro
- `external/saltcreep/tests/test_eigen_source.cpp` — criado (diagnostico)
- `docs/audits/saltcreep_eigen_compatibility_audit.md` — Fase 6.10B documentada
- `docs/20_saltcreep_eigen_migration_plan.md` — decisao `PROVEN_SAFE_TO_MIGRATE`
- `docs/16_saltcreep_governance.md`, `docs/13_coupling_lot_apb_salt.md`, `docs/17_lot_pkn_roadmap.md`
- `docs/dev-log.md`, `tools/docs_status.yaml`
- `.claude/settings.json` — permissao granular para `external/saltcreep/CMakeLists.txt`

**Nao alterado:**
- `external/saltcreep/include/Eigen/` — preservado
- `include/Eigen/` — preservado
- `legance/`, `legacy/`, `tests/baselines/` — preservados
- Modelos fisicos, casos e resultados do saltcreep — preservados

---

### [2026-06-01] Fase 6.10 — Auditoria Eigen do saltcreep — Codex
**Status:** Concluido nesta sessao.
**Testes/comandos saltcreep:** `cmake -S external/saltcreep -B external/saltcreep/build_baseline -DCMAKE_BUILD_TYPE=Debug -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`, `cmake --build external/saltcreep/build_baseline -j`, `ctest --test-dir external/saltcreep/build_baseline --output-on-failure -j 4`, build experimental em `external/saltcreep/build_lss_eigen` com `include/Eigen` no include path, e `ctest` equivalente.
**Resultado saltcreep:** baseline 125/125 testes passaram em 1028.24 s; build experimental 125/125 testes passaram em 1020.63 s.
**Casos saltcreep executados:** `external/saltcreep/cases/tcc/lame_test.yaml` e `external/saltcreep/cases/apb/mud_gradient_1d_8p5ppg.yaml` nos dois builds. O caso APB reportou `closure=0.300817%` em ambos.
**Testes/comandos lot-salt-suite:** `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build -j`, `ctest --test-dir build --output-on-failure`, `lot-sim validate --case` para `lot_pkn_minimal.yaml` e `lot_pkn_with_leakoff.yaml`, e `lot-sim run --mode lot-pkn` para `lot_pkn_minimal.yaml`.
**Resultado lot-salt-suite:** 47/47 testes Catch2 passaram; validates retornaram `OK`; run gerou `result.json` e `timeseries.csv` em `results\lot_pkn_minimal_saltcreep_eigen_review`.
**Escopo:** nenhum arquivo em `external/saltcreep/`, `legance/`, `legacy/`, `tests/baselines/` ou `include/Eigen/` foi removido ou alterado.

**Conclusao:**
- O `saltcreep` permanece compativel com a copia Eigen vendorizada.
- O build experimental tolera `include/Eigen` no include path, mas o Visual Studio ainda coloca `external/saltcreep/include` antes de `include/`.
- A migracao real para `include/Eigen` deve ser opcao CMake futura, nao mudanca implicita.

**Documentos criados/alterados:**
- `docs/audits/saltcreep_eigen_compatibility_audit.md`.
- `docs/20_saltcreep_eigen_migration_plan.md`.
- `docs/16_saltcreep_governance.md`, `docs/13_coupling_lot_apb_salt.md`, `docs/17_lot_pkn_roadmap.md`.

---

### [2026-06-01] Revisao commit 9048683 — LeakoffModel e Eigen/CMake — Codex
**Status:** Aprovado com ressalvas corrigidas nesta sessao.
**Commit revisado:** `9048683 feat(lot): add structured leakoff model`.
**Testes/comandos:** `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build -j`, `ctest --test-dir build --output-on-failure`, `lot-sim validate --case` para os tres contratos LOT/PKN e `lot-sim run --mode lot-pkn` para os dois casos modernos de validacao.
**Resultado:** 47/47 testes Catch2 passaram; validates e runs retornaram `OK` e geraram `result.json`/`timeseries.csv` em `results\lot_pkn_minimal_leakoff_review` e `results\lot_pkn_with_leakoff_review`.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/`, `tests/baselines/` ou `postprocess/scripts/` foi alterado.

**Patches de revisao:**
- `CMakeLists.txt` agora formaliza `lss_eigen`/`lss::eigen` apontando para `include/Eigen`, sem adicionar `external/saltcreep/include` aos targets modernos.
- `AGENTS.md`, `CLAUDE.md`, `include/AGENTS.md` e `docs/16_saltcreep_governance.md` documentam que `include/Eigen` e o Eigen oficial do `lot-salt-suite` e que a copia do saltcreep deve ficar preservada.
- `PknModel` passa a rejeitar tambem `input.leakoff.coefficient_m_sqrt_s` e `input.leakoff.constant_rate_m3_s` negativos.
- `tests/cpp/test_leakoff_model.cpp` cobre a rejeicao dos campos estruturados negativos.

**Ressalva remanescente:** ainda nao existe um target `saltcreep_eigen` no CMake raiz porque `external/saltcreep` nao e buildado por este target nesta fase. Registrar como candidata a Fase 6.10 se o adapter saltcreep entrar no build.

---

### [2026-06-01] Fase 6.9 — LeakoffModel C++ estruturado — Codex
**Status:** Implementado nesta sessao.
**Testes/comandos:** `cmake --build build --config Debug`, `ctest --test-dir build --output-on-failure` e `lot-sim validate --case` para `lot_pkn_minimal.yaml`, `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml` executados com sucesso.
**Resultado:** 46/46 testes Catch2 passaram; os tres contratos YAML LOT/PKN retornaram `OK`.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/`, `tests/baselines/`, `postprocess/scripts/` ou `.dat` foi alterado/usado.

**Mudanca principal:**
- `lot::LeakoffModel` agora encapsula `none`, `constant_rate`, `carter` minimo e `synthetic_constant` de compatibilidade.
- `PknModel` substituiu o calculo embutido de leakoff pela chamada ao modulo estruturado e continua limitando `V_leakoff <= V_inj`.
- Parser/schema aceitam `constant_rate_m3_s` e o modelo `constant_rate`, mantendo `synthetic_constant`.
- Carter permanece forma estrutural/monotonica minima, nao calibracao fisica dependente de pressao.

**Arquivos criados/alterados:**
- `src/lot/LeakoffModel.cpp`, `include/lot/LeakoffModel.hpp`, `include/lot/LotTypes.hpp`.
- `src/lot/PknModel.cpp`, `include/lot/PknInput.hpp`, `src/lot/PknRunner.cpp`.
- `include/core/types.hpp`, `src/io/CaseParser.cpp`, `schemas/lot_case.schema.yaml`.
- `include/Eigen/` — Eigen header-only mantido em `include/` para calculos futuros do simulador.
- `tests/cpp/test_leakoff_model.cpp`, `CMakeLists.txt`.
- `docs/02_lot_formulation.md`, `docs/05_input_output_formats.md`, `docs/12_validation_results.md`, `docs/17_lot_pkn_roadmap.md`, `tools/docs_status.yaml`, `docs/index.html`.

**Proxima etapa recomendada:** tornar o `PknModel` mais rigoroso quanto ao tempo desde breakdown e consolidar `BreakdownCriterion` C++ antes de iniciar adapters LOT/saltcreep.

---

### [2026-06-01] Fase 6.8 — Política C++ first, Python postprocess only — Codex
**Status:** Implementado nesta sessao.
**Testes/comandos:** `python tools\generate_docs_index.py`, `git diff --name-only` e `git status` executados. Fase documental; `ctest` nao foi executado porque nao houve alteracao em C++, CMake, schema ou testes.
**Escopo:** somente documentos de governanca e manual gerado. Nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/`, `tests/baselines/`, `apps/`, `tests/` ou `postprocess/scripts/` foi alterado. Em `include/` e `src/`, apenas `AGENTS.md` de governanca foram atualizados.

**Politica registrada:**
- Motor de simulacao primario e C++.
- Parser, conversao de unidades, modelos fisicos, runners, writers, leakoff, breakdown, dano, acoplamento LOT/APB/sal e integracao com `external/saltcreep` devem ser C++.
- Python fica restrito a pos-processamento, graficos, relatorios, auditorias externas e migracoes pontuais nao-runtime em `tools/`.
- Fluxo runtime: `YAML/JSON -> C++ parser -> C++ model/runner -> C++ writer -> CSV/JSON`.
- Fluxo Python permitido: `CSV/JSON -> Python plot/report -> PNG/HTML`.

**Arquivos alterados:**
- `AGENTS.md`, `CLAUDE.md`, `postprocess/AGENTS.md`, `src/AGENTS.md`, `include/AGENTS.md`.
- `docs/10_postprocessing_plan.md`, `docs/14_developer_workflow.md`, `docs/17_lot_pkn_roadmap.md`, `docs/07_target_architecture.md`, `docs/13_coupling_lot_apb_salt.md`.
- `docs/dev-log.md`, `tools/docs_status.yaml`, `docs/index.html`.

**Proxima etapa recomendada:** implementar `LeakoffModel` C++ com testes Catch2, depois evoluir `PknModel`, `BreakdownCriterion` e adapter LOT/saltcreep em C++.

---

### [2026-06-01] Fase 6.7 — Pós-processamento moderno LOT/PKN — Codex
**Status:** Implementado nesta sessao.
**Testes:** `python -m unittest discover tests\python` executado; 3/3 passaram. `python -m pytest tests\python` foi tentado, mas o ambiente local nao possui `pytest` instalado.
**Execucao CLI moderna:** `.\build\lot-sim.exe run --case cases\validation\lot_pkn_minimal.yaml --mode lot-pkn --output results\lot_pkn_minimal` e `.\build\lot-sim.exe run --case cases\validation\lot_pkn_with_leakoff.yaml --mode lot-pkn --output results\lot_pkn_with_leakoff` executados com sucesso.
**Pós-processamento:** `python postprocess\scripts\lot_pkn_report.py --run-dir results\lot_pkn_minimal --output reports\lot_pkn_minimal` e `python postprocess\scripts\lot_pkn_report.py --run-dir results\lot_pkn_with_leakoff --output reports\lot_pkn_with_leakoff` geraram 5 PNGs e `report.html` para cada caso.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/`, `tests/baselines/`, `include/`, `src/` ou `apps/` foi alterado. `results/` e `reports/` permanecem fora do versionamento.

**Resultado:**
- `postprocess/scripts/lot_pkn_report.py` valida arquivos de entrada, colunas obrigatorias, `NaN`/`Inf` e gera relatorio HTML.
- Relatorios sao rotulados como `Modern synthetic LOT/PKN output - no legacy regression`.
- Nao houve leitura de `.dat`, comparacao com legado ou declaracao de validacao legado x moderno.
- R09 continua `MITIGATED_FOR_AUDITED_PKN_CASES; BLOCKER_FOR_IDQ4_REGRESSION`.

**Arquivos criados/alterados:**
- `postprocess/scripts/lot_pkn_report.py` — script de graficos/relatorio.
- `tests/python/test_lot_pkn_postprocess.py` e `tests/fixtures/lot_pkn_modern/` — testes e fixture minima.
- `.gitignore` — inclui `reports/`.
- `docs/10_postprocessing_plan.md`, `docs/11_cli_usage.md`, `docs/12_validation_results.md`, `docs/17_lot_pkn_roadmap.md`, `tools/docs_status.yaml`, `docs/index.html` — documentacao/status atualizados.

**Proxima etapa recomendada:** evoluir leakoff/breakdown moderno ou confirmar metadados de `idQ` antes de qualquer comparacao legado x moderno.

---

### [2026-06-01] Fase 6.6 — Ensaio controlado R09 `/22` vs `/2` — Codex
**Status:** Implementado nesta sessao.
**Classificacao R09:** `MITIGATED_FOR_AUDITED_PKN_CASES; BLOCKER_FOR_IDQ4_REGRESSION`.
**Testes/comandos:** `python tools\audit_r09_pkn_conversion.py`, `python tools\generate_docs_index.py` e `python tools\generate_docs_index.py --dry-run` executados com sucesso. Nao houve alteracao C++, portanto `ctest` nao foi reexecutado nesta fase.
**Escopo:** inspecao somente leitura de `legance/LOT_Tese/` e `legance/LOT_APB_v5/`; nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/` foi alterado.

**Resultado:**
- `Conv_bbmin_m3h(Q) = Q * 9.53924 / M_PI / 22` pertence ao ramo `idQ == 4`.
- `Conv_bbmin_m3min(Q) = Q * 0.158987 / M_PI / 2` pertence ao ramo `idQ == 6`.
- Os casos PKN auditados `8-BUZ-67D-RJS-VISCO-pkn.cpp` e `9-BUZ-39DA-RJS-VISCO-2.cpp` usam `idQ == 6`; portanto, nao passam pelo literal `/22`.
- Para a mesma base `Q * 9.53924`, `/22` produz `1/11` do valor de `/2`.

**Arquivos criados/alterados:**
- `docs/audits/R09_pkn_conversion_experiment.md` — relatorio da Fase 6.6.
- `docs/audits/R09_pkn_conversion_table.csv` — tabela analitica gerada pelo script.
- `tools/audit_r09_pkn_conversion.py` — script independente do legado.
- `docs/08_known_issues.md`, `docs/12_validation_results.md`, `docs/17_lot_pkn_roadmap.md`, `tools/docs_status.yaml`, `tools/generate_docs_index.py`, `docs/index.html` — status e manual atualizados.

**Proxima etapa recomendada:** criar pos-processamento moderno/compare qualitativo cuidadosamente rotulado para os dois PKN auditados, ou confirmar metadados de geracao dos `.dat` antes de qualquer regressao quantitativa.

---

### [2026-06-01] Revisao Fase 6.5 — LOT/PKN CSV/JSON — Codex
**Status:** Aprovado com ressalvas corrigidas nesta sessao.
**Commit revisado:** `f18bca1 feat(lot): run pkn cases to csv json`.
**Testes:** `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build -j` e `ctest --test-dir build --output-on-failure` executados; 37/37 passaram apos inclusao de teste negativo do `ResultWriter`.
**Validacao CLI:** `lot-sim validate --case` retornou `OK` para `cases/validation/lot_pkn_minimal.yaml`, `cases/validation/lot_pkn_with_leakoff.yaml` e `cases/lot_tese_migrated/buz67d_pkn.yaml`.
**Validacao schema:** os tres YAMLs LOT/PKN foram validados contra `schemas/lot_case.schema.yaml`.
**Execucao CLI:** `lot-sim run --mode lot-pkn` executou `lot_pkn_minimal.yaml` e `lot_pkn_with_leakoff.yaml`, gerando `result.json` e `timeseries.csv` em `results\lot_pkn_minimal_review` e `results\lot_pkn_with_leakoff_review`.
**Escopo:** `legance/`, `legacy/`, `external/saltcreep/` e `tests/baselines/` permaneceram intocados; `results/` permanece ignorado pelo git.

**Patches aplicados na revisao:**
- `docs/05_input_output_formats.md` — removido trecho PowerShell/hashtable colado indevidamente no Markdown e mantida documentacao limpa de saida CSV futura.
- `src/io/ResultWriter.cpp` e `tests/cpp/test_result_writer.cpp` — writer agora rejeita valores nao finitos antes de gravar CSV/JSON, com teste Catch2 dedicado.
- `docs/index.html` — regenerado a partir dos Markdown corrigidos.

**Conclusao:** fluxo moderno `YAML -> CaseParser -> PknInput -> PknModel -> PknResult -> CSV/JSON` aprovado para a Fase 6.5. Nao houve regressao contra legado; R09 permanece blocker para comparacao legado x moderno.

---

### [2026-06-01] Template SaltCreep no manual gerado — Codex
**Status:** Implementado nesta sessao.
**Testes:** `python tools\generate_docs_index.py` e `python tools\generate_docs_index.py --dry-run` executados com sucesso. Verificacao estrutural confirmou sidebar, busca, fontes Fraunces/Hanken/IBM Plex Mono, hero, cards de metricas, links de navegacao agrupados, 21 secoes e script de destaque/copia.
**Escopo:** `external/saltcreep/docs/index.html` foi usado apenas como referencia visual; nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/` foi alterado.

**Mudanca principal:**
- `tools/generate_docs_index.py` agora gera `docs/index.html` no layout do manual SaltCreep: sidebar fixa escura, busca na navegacao, grupos de documentos, hero editorial, metricas em cards, conteudo em largura de leitura, blocos de codigo com botao de copia e responsividade mobile.
- Como o manual SaltCreep vendorizado e mantido manualmente, o padrao visual foi adaptado no gerador local sem depender de arquivos de `external/saltcreep/`.

**Observacao:** tentativa de abrir o HTML no navegador interno falhou por erro local do runtime da sandbox (`windows sandbox failed: spawn setup refresh`); a verificacao seguiu por geracao deterministica e inspeção estrutural do HTML.

---

### [2026-06-01] Fase 6.5 — Execucao moderna LOT/PKN CSV/JSON — Codex
**Status:** Implementado nesta sessao.
**Testes:** `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build -j` e `ctest --test-dir build --output-on-failure` executados; 36/36 passaram.
**Validacao CLI:** `lot-sim validate --case` retornou `OK` para `cases/validation/lot_pkn_minimal.yaml`, `cases/validation/lot_pkn_with_leakoff.yaml` e `cases/lot_tese_migrated/buz67d_pkn.yaml`.
**Execucao CLI:** `lot-sim run --mode lot-pkn` executou `lot_pkn_minimal.yaml` e `lot_pkn_with_leakoff.yaml`, gerando `result.json` e `timeseries.csv` em `results\lot_pkn_minimal` e `results\lot_pkn_with_leakoff`.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/` foi alterado. `results/` permanece ignorado pelo git.

**Arquivos criados/alterados:**
- `include/lot/PknRunner.hpp`, `src/lot/PknRunner.cpp` — convertem `CaseData` em `PknInput` e executam `PknModel`.
- `include/io/ResultWriter.hpp`, `src/io/ResultWriter.cpp` — gravam `result.json` e `timeseries.csv`.
- `apps/lot-sim.cpp` — adiciona `run --case ... --mode lot-pkn --output ...`.
- `tests/cpp/test_pkn_runner.cpp`, `tests/cpp/test_result_writer.cpp` — cobrem runner, writer e CLI.
- `include/core/types.hpp`, `src/io/CaseParser.cpp`, `schemas/lot_case.schema.yaml`, `cases/validation/lot_pkn_with_leakoff.yaml` — mantem viscosidade e coeficiente de leakoff em SI no contrato moderno.
- `docs/11_cli_usage.md`, `docs/05_input_output_formats.md`, `docs/12_validation_results.md`, `docs/17_lot_pkn_roadmap.md`, `tools/docs_status.yaml`, `docs/index.html` — documentacao/status atualizados.

**R09:** permanece blocker para validacao numerica legado x moderno. Esta fase nao executou regressao contra `.dat`, `legance/LOT_Tese` ou `legance/LOT_APB_v5`.

**Proxima etapa recomendada:** criar ensaio comparativo controlado de R09 ou evoluir leakoff/breakdown com fixtures modernas pequenas, mantendo legado fora do caminho de validacao.

---

### [2026-06-01] Template visual do manual tecnico — Codex
**Status:** Implementado nesta sessao.
**Testes:** `python tools\generate_docs_index.py` e `python tools\generate_docs_index.py --dry-run` executados com sucesso. Verificacao estrutural do HTML confirmou 21 secoes documentais, 4 cards de status e sumario com links ancorados.
**Escopo:** apenas gerador do manual e HTML gerado foram alterados; nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/` foi alterado.

**Mudanca principal:**
- `tools/generate_docs_index.py` passa a gerar o `docs/index.html` com layout claro inspirado no resumo executivo anexado: header em gradiente, sumario sticky em chips, cards de status, secoes amplas, tabelas legiveis, blocos de codigo contrastados e responsividade mobile.
- O sumario usa o primeiro titulo real de cada Markdown em vez de nomes tecnicos de arquivo.
- O aviso de validacao foi alinhado ao estado atual: sem regressao numerica legado x moderno validada, mas com testes sinteticos/contratuais registrados.

**Observacao:** tentativa de abrir o HTML no navegador interno falhou por erro local do runtime da sandbox; a verificacao seguiu por geracao deterministica e inspeção estrutural do HTML.

---

### [2026-06-01] Fase 6.4 — PknModel fisico minimo em SI — Codex
**Status:** Implementado nesta sessao.
**Commit:** `537f4cc feat(lot): implement minimal SI PKN model`.
**Testes:** `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build -j` e `ctest --test-dir build --output-on-failure` executados; 30/30 passaram.
**Validacao CLI:** `lot-sim validate --case` retornou `OK` para `cases/validation/lot_pkn_minimal.yaml`, `cases/validation/lot_pkn_with_leakoff.yaml` e `cases/lot_tese_migrated/buz67d_pkn.yaml`.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/` foi alterado.

**Modelo implementado:**
- `lot::PknModel::simulate` gera serie temporal em SI usando `rate_m3_s`, `dt_s`, `total_time_s`, `accommodation_time_s`, altura de fratura, modulo plano e viscosidade.
- A largura usa escala PKN minima proporcional a `(mu * Q^2 * t / (E' * h))^(1/5)`, com piso numerico e largura inicial.
- O volume injetado e `Q * max(0, t - tac)`; o volume de fratura e o volume injetado menos leakoff acumulado simplificado.
- A pressao liquida e estimada por `E' * width / h`; resultados escalares e series sao finitos e nao negativos.

**R09:** permanece blocker para validacao numerica legado x moderno. Esta fase nao executou regressao contra `.dat` legado nem usou `buz67d_pkn.yaml` como baseline numerico.

**Proxima etapa recomendada:** conectar o modelo ao subcomando `run` apenas depois de definir output numerico e manter R09 separado como ensaio comparativo controlado.

---

### [2026-06-01] Fase 6.3 — Auditoria R09 `/ M_PI / 22` — Codex
**Status:** Auditoria documental implementada nesta sessão.
**Testes:** `git diff --name-only` executado; `ctest` nao executado porque apenas documentacao/status foram alterados.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/`, `include/lot/`, `src/lot/` ou `tests/baselines/` foi alterado.

**Classificacao R09:** `NAO RESOLVIDO: requer ensaio numerico comparativo`.

**Achados principais:**
- `/ M_PI / 22` aparece uma unica vez em `legance/LOT_Tese/src/apb_code/APB1da.cpp`, funcao `Conv_bbmin_m3h(double Q)`, ramo `idQ == 4`.
- Os casos PKN auditados (`8-BUZ-67D-RJS-VISCO-pkn.cpp` e `9-BUZ-39DA-RJS-VISCO-2.cpp`) usam `idQ == 6`, que chama `Conv_bbmin_m3min(Q) = Q * 0.158987 / M_PI / 2`.
- `LOT_APB_v5` nao contem `/ M_PI / 22` no caminho auditado.
- Dimensionalmente, `22` e adimensional; preserva unidade, mas muda `Qinj` por fator 11 contra a hipotese `/ M_PI / 2`.

**Arquivos criados/alterados:**
- `docs/audits/R09_pkn_mpi22_audit.md` — relatorio completo da auditoria
- `docs/08_known_issues.md` — R09 atualizado: escopo reduzido, ainda blocker
- `docs/17_lot_pkn_roadmap.md` — fase 6.3 e proximos passos
- `docs/12_validation_results.md` — auditoria registrada sem validacao numerica
- `docs/dev-log.md`, `tools/docs_status.yaml`, `docs/index.html` — status/indice atualizados

**Proxima etapa recomendada:** ensaio comparativo controlado fora de `legance/` ou implementacao fisica minima em SI sem usar `.dat` legado como baseline.

---

### [2026-06-01 15:44] `d41076e` — Themisson
**Commit:** `docs: patch review Fase 6.2 — README saltcreep policy + roadmap fora de escopo`
**Testes C++:** 4 arquivos | **Testes Python:** 0 arquivos
**Último resultado ctest:** All tests passed (2 assertions in 1 test case)
**Arquivos alterados:**
- `README.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/index.html`

---

### [2026-06-01] Fase 6.2 — Contrato LOT/PKN YAML+C++ — Codex
**Status:** Implementado nesta sessão.
**Testes C++:** 27 Catch2 | **Resultado ctest:** 27 passaram.
**Validação YAML/schema:** `lot_pkn_minimal.yaml`, `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml` validaram contra `schemas/lot_case.schema.yaml`.
**CLI:** `.\build\lot-sim.exe validate --case ...` executado nos 3 casos LOT/PKN com `OK`.
**Escopo:** nenhum arquivo em `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/` foi alterado.

**Arquivos criados:**
- `include/lot/LotTypes.hpp`
- `include/lot/InjectionSchedule.hpp`
- `include/lot/LeakoffModel.hpp`
- `include/lot/PknInput.hpp`
- `include/lot/PknResult.hpp`
- `include/lot/BreakdownDetector.hpp`
- `include/lot/PknModel.hpp`
- `src/lot/BreakdownDetector.cpp`
- `src/lot/PknModel.cpp`
- `tests/cpp/test_breakdown_detector.cpp`
- `tests/cpp/test_pkn_model_synthetic.cpp`
- `cases/validation/lot_pkn_minimal.yaml`
- `cases/validation/lot_pkn_with_leakoff.yaml`
- `cases/lot_tese_migrated/buz67d_pkn.yaml`

**Arquivos alterados:**
- `schemas/lot_case.schema.yaml` — aceita `simulation.mode: lot-pkn` e contrato LOT/PKN
- `include/core/types.hpp` — `LotConfig` expandido com campos SI do contrato PKN
- `src/io/CaseParser.cpp` — parsing e conversao SI para taxa, tempo, comprimento e pressao
- `tests/cpp/test_case_parser.cpp` — cobertura dos novos YAMLs LOT/PKN
- `CMakeLists.txt` — inclui modulo `lot` e novos testes
- `docs/02_lot_formulation.md`, `docs/05_input_output_formats.md`, `docs/12_validation_results.md`, `docs/17_lot_pkn_roadmap.md` — contrato e ressalvas documentados
- `tools/docs_status.yaml`, `docs/index.html` — status/indice atualizados

**R09:** permanece blocker para validacao numerica contra legado. Nenhuma regressao PKN legado x moderno foi declarada.

**Proxima etapa recomendada:** auditar R09 (`/ M_PI / 22`) ou evoluir `PknModel` com formulacao controlada, ainda sem usar baseline legado como verdade numerica.

---

### [2026-06-01 15:25] `75adb3c` — Themisson
**Commit:** `docs: patch review Fase 6.0/6.1 — R09 blocker + roadmap step 4.5`
**Testes C++:** 2 arquivos | **Testes Python:** 0 arquivos
**Último resultado ctest:** All tests passed (2 assertions in 1 test case)
**Arquivos alterados:**
- `docs/08_known_issues.md`
- `docs/17_lot_pkn_roadmap.md`
- `docs/index.html`

---

### [2026-06-01] Fase 6.0/6.1 — Governanca saltcreep e auditoria LOT/PKN — Codex
**Status:** Documentacao e auditoria implementadas nesta sessão.
**Testes:** `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`, `cmake --build build -j` e `ctest --test-dir build --output-on-failure` executados; 15/15 passaram. Nenhuma validacao numerica declarada.
**Escopo:** nenhum arquivo em `legance/`, `legacy/` ou `external/saltcreep/` foi alterado.

**Decisoes:**
- `external/saltcreep/` passa a ser dependencia vendorizada ativa, com edicao controlada por escopo explicito, testes, documentacao e dev-log.
- A primeira migracao moderna de LOT deve priorizar o caminho PKN auditado em `legance/LOT_Tese/`.
- Modelos circular, eliptico e penny-shaped ficam catalogados, mas fora do primeiro caminho critico.

**Achados principais:**
- O caminho PKN passa por `Fluids::setLeakoffProps(..., "pkn")`, `idTypeFracture == 2` e `APB1da::calculateLOTFracturedSaltRock(...)`.
- O legado mistura conversao de vazao com fator geometrico; uma conversao contem expressao suspeita `/ M_PI / 22`.
- O bloco PKN mistura tempo absoluto e tempo desde breakdown em trechos auditados.
- O volume PKN legado usa forma simplificada e tem alternativa comentada, exigindo decisao documentada antes de validacao.

**Arquivos adicionados/alterados:**
- `docs/16_saltcreep_governance.md` — politica de dependencia ativa para saltcreep
- `docs/17_lot_pkn_roadmap.md` — roadmap da primeira entrega LOT/PKN
- `docs/audits/lot_legacy_inventory.md` — inventario LOT nos legados
- `docs/audits/pkn_legacy_path.md` — rota tecnica PKN legado
- `docs/audits/non_pkn_models_status.md` — status dos modelos nao PKN
- `AGENTS.md` e `CLAUDE.md` — regras ajustadas para saltcreep vendorizado ativo
- `docs/07_target_architecture.md` e `docs/13_coupling_lot_apb_salt.md` — arquitetura e acoplamento atualizados

---

### [2026-06-01 14:45] `89d03e0` — Themisson
**Commit:** `docs: clarify dt unit coupling with creep rate`
**Testes C++:** 2 arquivos | **Testes Python:** 0 arquivos
**Último resultado ctest:** All tests passed (2 assertions in 1 test case)
**Arquivos alterados:**
- `docs/08_known_issues.md`

---

### [2026-06-01] Ajuste R08 — Codex + orientação do usuário
**Status:** Documentação ajustada nesta sessão.
**Testes:** não executados (mudança somente documental)

**Correção conceitual:**
- `dt` não é sempre horas ou minutos por natureza; ele deve ser coerente com a unidade temporal da taxa de deformação do backend ativo.
- No `LOT_APB_v5`, a auditoria segue indicando `dt` em [h].
- Se a taxa estiver em [1/s], [1/min] ou [1/h], o passo temporal correspondente deve estar em segundos, minutos ou horas, respectivamente, ou ser convertido explicitamente na fronteira.
- `tac`/tempo de acomodação é o intervalo inicial sem incrementos térmicos ou injeção/variação operacional de fluidos.

**Arquivos alterados:**
- `docs/08_known_issues.md` — R08 reescrito como regra dimensional geral + conclusão específica para `LOT_APB_v5`

---

### [2026-06-01] Fase 5-E — Codex
**Status:** Implementado nesta sessão.
**Testes C++:** 15 Catch2 | **Resultado ctest:** 15 passaram
**Validação YAML:** `cases/validation/lot_minimal.yaml` e `cases/validation/lot_double_mechanism_reference.yaml` válidos contra `schemas/lot_case.schema.yaml`

**Arquivos adicionados/alterados:**
- `docs/08_known_issues.md` — R08 resolvido: `dt` do wrapper APB/SESTSAL em [h], com risco lateral documentado
- `src/io/CaseParser.cpp` — valida listas mínimas e referências `annulars[].fluid`/`layers[].rock`
- `tests/cpp/test_case_parser.cpp` — testes de referências inválidas e lista obrigatória vazia
- `schemas/lot_case.schema.yaml` — `minItems` para listas semanticamente obrigatórias
- `apps/lot-sim.cpp` — subcomando `validate --case`

**Execução manual:**
`lot-sim validate --case cases/validation/lot_minimal.yaml` imprime `OK: lot_minimal_validation`.

---

### [2026-06-01] Fase 5-A..5-D — Codex
**Status:** Implementado nesta sessão.
**Testes C++:** 12 Catch2 | **Resultado ctest:** 12 passaram
**Validação YAML:** `cases/validation/lot_minimal.yaml` e `cases/validation/lot_double_mechanism_reference.yaml` válidos contra `schemas/lot_case.schema.yaml`

**Arquivos adicionados/alterados:**
- `include/units/units.hpp` — conversões header-only C++20, incluindo PPG, pol, psi, bar, cP, temperatura, torque e gradiente hidrostático
- `include/core/types.hpp` — structs de `CaseData` e subestruturas com FA01/FA02 documentadas nos campos
- `include/io/CaseParser.hpp` + `src/io/CaseParser.cpp` — parser YAML com conversões para SI e validações mínimas
- `schemas/lot_case.schema.yaml` — schema principal comentado, incluindo `hydrostatic_depth_profile`
- `cases/validation/lot_minimal.yaml` — caso mínimo LOT sem sal, validável
- `cases/validation/lot_double_mechanism_reference.yaml` — caso pequeno para testar FA01/FA02
- `apps/lot-sim.cpp` — subcomando `inspect --case`
- `tests/cpp/test_units.cpp` + `tests/cpp/test_case_parser.cpp` — cobertura inicial Catch2
- `CMakeLists.txt` — targets `lot-sim` e `lot_sim_tests`; workaround local para `yaml-cpp` com GCC 16

**Execução manual:**
`lot-sim inspect --case cases/validation/lot_minimal.yaml` imprime resumo do caso sem erro.

---

### [2026-06-01 12:17] `13eb5c3` — Themisson
**Commit:** `feat(saltcreep): sync saltcreep with LOT/APB integration updates`
**Testes C++:** 0 arquivos | **Testes Python:** 0 arquivos
**Último resultado ctest:** nenhum (módulos ainda não implementados)

**⚠ Modificações em external/saltcreep/:**
- `external/saltcreep/.gitignore`
- `external/saltcreep/AGENTS.md`
- `external/saltcreep/CLAUDE.md`
- `external/saltcreep/CMakeLists.txt`
- `external/saltcreep/cases/apb/mud_gradient_1d_8p5ppg.yaml`
- `external/saltcreep/cases/apb/mud_gradient_2d_Q8_8p5ppg.yaml`
- `external/saltcreep/cases/sestsal/base_model.yaml`
- `external/saltcreep/cases/sestsal/base_model2D.yaml`
- … e mais 38 arquivos
> Atualizar a seção 'Modificações em andamento no saltcreep' abaixo.

---

### [2026-06-01 11:47] `3b45136` — Themisson
**Commit:** `feat: add dev-log system with auto-update hook`
**Testes C++:** 0 arquivos | **Testes Python:** 0 arquivos
**Último resultado ctest:** nenhum (módulos ainda não implementados)
**Arquivos alterados:**
- `.agents/skills/update-devlog/SKILL.md`
- `.claude/settings.json`
- `.claude/skills/update-devlog/SKILL.md`
- `AGENTS.md`
- `CLAUDE.md`
- `tools/update_devlog.py`

---

### [2026-06-01 10:36] `4739d4b` — Themisson
**Commit:** `docs: formulation audit results (Fase 3 /formulation-audit)`
**Fase:** 3 — Auditoria de formulação
**Arquivos alterados:**
- `docs/08_known_issues.md` — FA01-FA04 documentados com evidência de código
- `docs/12_validation_results.md` — seção de baselines atualizada
- `docs/index.html` — regenerado com novos achados
**Saltcreep:** não alterado neste commit
**Testes:** nenhum (documentação)
**Resultado:** Convenções de sinais, unidades de e0 e temperatura confirmadas

---

### [2026-06-01 10:30] `4f9957a` — Themisson
**Commit:** `feat: capture LOT_APB_v5 baseline outputs (Fase 4)`
**Fase:** 4 — Baselines
**Arquivos alterados:**
- `.gitignore` — excluir inputs pesados (57MB) e detailed_output (29MB)
- `docs/12_validation_results.md` — metadados reais de compilação
- `tests/baselines/apbv5_SCORE-MRO-28_output.json` (47 KB) ← **BASELINE PRINCIPAL**
- `tests/baselines/apbv5_SCORE-MRO-28_original_output.json` (27 KB)
- `tests/baselines/apbv5_SCORE-MRO-28_Ev_temp_output.json` (47 KB)
**Nota compilação:** g++16.1 + `-w -fpermissive` (Eigen antigo × GCC16 incompatibilidade)
**Testes:** LOT_APB_v5 executado com 3 JSONs — output gerado em 0.1–0.3s

---

### [2026-06-01 10:04] `72c8ca4` — Themisson
**Commit:** `chore: add external/saltcreep as vendored reference (8.5MB)`
**Fase:** 1 — Estrutura
**Saltcreep:** adicionado como cópia controlada (sem .git próprio no workspace)
**Regra:** NÃO editar, NÃO duplicar modelos constitutivos

---

### [2026-06-01 10:04] `7dc3959` — Themisson
**Commit:** `chore: exclude legance/ from git (400MB legacy code — local only)`
**Fase:** 1 — Estrutura
**Nota:** `legance/` (400MB) excluído permanentemente do git — apenas local

---

### [2026-06-01 10:03] `78d17df` — Themisson
**Commit:** `docs: add 16 technical docs, interactive index.html and AGENTS.md per directory`
**Fase:** 2 — Documentação
**Entregáveis:**
- `docs/00_project_overview.md` … `docs/15_changelog.md` (16 arquivos)
- `docs/index.html` (66KB, 16 seções, offline-first)
- `tools/docs_status.yaml` + `tools/generate_docs_index.py`
- 11 × `AGENTS.md` por diretório

---

### [2026-06-01 10:03] `623ec68` — Themisson
**Commit:** `feat: add Claude Code agents, skills and Codex agent configuration`
**Fase:** 3 — Agentes e skills
**Entregáveis:**
- `.claude/agents/`: cpp-pro, verifier, legacy-explorer, docs-sync, salt-adapter
- `.claude/skills/` + `.agents/skills/`: formulation-audit, cpp-refactor, validation-benchmark, postprocess-report, docs-html-report, lot-salt-integration
- `.claude/settings.json`: Allow/Deny configurado
- `.codex/agents/`: cpp-pro.toml, expert-cpp-software-engineer.toml

---

### [2026-06-01 10:02] `a0502d7` — Themisson
**Commit:** `chore: initialize lot-salt-suite project structure`
**Fase:** 1 — Estrutura inicial
**Entregáveis:** CLAUDE.md, AGENTS.md, README.md, .gitignore, CMakeLists.txt, pyproject.toml

---

## Seção: Modificações em external/saltcreep — histórico

### [2026-06-01] Sincronização 1 — WallPressureField + APB cases

**Status:** Concluído e commitado (`13eb5c3`)

**Novos arquivos adicionados:**

| Arquivo | Relevância para lot-salt-suite |
|---------|-------------------------------|
| `include/solver/WallPressureField.hpp` | Interface-chave para pressão de lama → sal |
| `src/solver/WallPressureField.cpp` | Confirma FC=119.826 (mesmo valor que APB1da) |
| `cases/apb/mud_gradient_1d_8p5ppg.yaml` | Formato YAML para casos APB com gradiente de lama |
| `cases/apb/mud_gradient_2d_Q8_8p5ppg.yaml` | Variante 2D Q8 do caso APB |
| `post/saltpost/diameter.py` | Rastreamento de diâmetro — útil para APB |
| `post/saltpost/layers.py` | Pós-processamento por camada |
| `tests/cpp/test_wall_pressure_field.cpp` | Testes Catch2 para WallPressureField |

**Arquivos modificados (impacto):**

| Arquivo | O que mudou |
|---------|------------|
| `include/solver/Assembler.hpp` | Suporte a WallPressureField como BC |
| `include/solver/TimeIntegrator.hpp` | Conexão com WallPressureField |
| `include/io/CaseParser.hpp` | Novo modo `fluid.mode: hydrostatic_depth_profile` |
| `src/io/CaseParser.cpp` | Parser para o novo modo de fluido APB |

**Impacto direto no design da Fase 8 (SaltCreepInterface):**

```
WallPressureField é a ponte que faltava:
  lot-salt-suite/include/salt/SaltCreepInterface.hpp
    recebe WallPressureField* como parâmetro
    ou como dependência injetada no SaltCreepSaltcreepAdapter

Fluxo confirmado:
  APBSolver → WallPressureField → SaltCreepSaltcreepAdapter
    → saltcreep::Assembler → deformação viscosa → δV anular → δP APB

Constante confirmada: kLbPerGalToKgPerM3 = 119.826 (saltcreep)
                      FC = 119.826427 (APB1da legado)  ← mesmo valor
```

**fluid.mode novo no YAML saltcreep:**
```yaml
fluid:
  mode: hydrostatic_depth_profile  # novo
  weight_lb_per_gal: 8.5
  surface_pressure_Pa: 0.0
```
→ Este modo deve ser incorporado ao schema `schemas/lot_case.schema.yaml` na Fase 5.
