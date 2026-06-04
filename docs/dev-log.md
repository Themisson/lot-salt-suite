# dev-log — lot-salt-suite

> **LEITURA OBRIGATÓRIA** para Claude Code e Codex na abertura de qualquer sessão.
> Auto-atualizado por `tools/update_devlog.py` após cada `git commit` ou `git push`.
> Invoke `/update-devlog` manualmente quando necessário.

---

## Estado atual do projeto

```
Fase ativa  : 10.10 implementada, aguardando revisao/commit
Branch      : main
Repositório : https://github.com/Themisson/lot-salt-suite
Último push : 2026-06-04
Testes C++  : 203/203 passaram em 2026-06-04
Testes Py   : 3 unittest (3 passaram em 2026-06-01)
Baselines   : 4 capturados (LOT_APB_v5)
Saltcreep   : 133/133 Catch2 baseline + 133/133 Catch2 LSS Eigen + 31/31 Python em 2026-06-04
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

### [2026-06-04] Fase 10.11B — mapeamento `LOT_Tese` para sigma-theta moderno — Codex

**Status:** Documentacao/formulacao concluida nesta sessao, sem commit/push por
instrucao da fase.

**Objetivo:** Formalizar o contrato de mapeamento entre o criterio legado
`LOT_Tese` e os campos do diagnostico sigma-theta moderno, sem comparacao
numerica, sem instrumentar `legance/` e sem alterar runtime.

**Mapeamento documentado:**
- `pw = line_up[lu].pi(idAnnular) + line_up[lu].dP(idAnnular)` -> pressao de
  poco/anular usada contra a parede/rocha vizinha, unidade aparente Pa.
- `sigmaTheta = -line_up[lu].mdl->getSigmaTheta()` ->
  `sigma_theta_compression_positive_Pa`.
- `dP_leakoff = pw - sigmaTheta` -> `margin_Pa`.
- `pw > sigmaTheta` -> `opened` e `legacy_algebra_opened`, apenas como algebra
  legada/experimental.
- `line_up[lu].depth_influence` e `line_up[lu].thickness` foram registrados
  como profundidade e altura de influencia do legado, ainda sem equivalencia
  plena com `wall_gp_*` moderno.

**Lacunas registradas:**
- `LOT_Tese` calcula `pw`, `sigmaTheta`, `margin` e `opened`, mas nao exporta
  diretamente esses campos no `.dat` principal identificado.
- Unidade temporal precisa ser confirmada por causa do historico FA01.
- `LOT_APB_v5` exporta pressao em psi em JSON; o diagnostico moderno usa Pa.
- `getElem(0)` e amostra mais interna/proxima da parede, nao extrapolacao exata.
- Comparacao numerica direta exigira extractor legado, instrumentacao controlada
  ou comparacao limitada aos campos ja exportados.

**Escopo preservado:**
- Nao houve alteracao em C++, testes, CMake, parser, `CaseData`, CLI, YAMLs,
  schemas, `legance/`, `legacy/`, `external/saltcreep/`, baselines ou
  postprocess.

**Resultado:** Contrato documental registrado em `docs/13_coupling_lot_apb_salt.md`
e status `phase_10_11b_lot_tese_sigma_theta_mapping: completed` adicionado em
`tools/docs_status.yaml`.

---

### [2026-06-04] Fase 10.10 — exportacao da matriz sigma-theta — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Provar que o writer experimental `LotSaltSigmaThetaDiagnosticWriter`
consegue exportar a matriz de tres cenarios sigma-theta criada na Fase 10.8B.

**Implementacao:**
- Adicionado teste integrado em
  `tests/cpp/test_lot_salt_sigma_theta_diagnostic_writer.cpp`.
- O teste usa `cases/validation/lot_pkn_minimal.yaml` e constrói tres cenarios:
  - sem geostatica;
  - geostatica sintetica explicita com `-2 MPa`;
  - geostatica litostatica via `with_lithostatic_geostatic(...)`.
- Cada cenario executa `run_lot_salt_sigma_theta_experimental(...)`.
- A matriz e exportada com `write_lot_salt_sigma_theta_diagnostics(...)` para
  diretorio temporario do teste, gerando `points.csv`, `summary.csv` e
  `metadata.json`.
- O teste verifica que os tres cenarios aparecem nos tres artefatos e que a
  contagem de linhas de `points.csv` corresponde a soma dos pontos diagnosticos
  dos tres resultados.

**Escopo preservado:**
- Nao altera writer, driver, diagnostico, breakdown, bridge, CLI, parser,
  `CaseData`, `ResultWriter`, LOT/APB, YAMLs, schemas, saltcreep, legados,
  baselines ou postprocess.
- Nao usa `results/` de producao.
- Nao compara com `LOT_Tese`, nao cria HTML e nao chama pos-processamento
  Python.

**Testes executados:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure`: 203/203 passaram.
- Filtro `writer|Writer|scenario|Scenario|sigma_theta|SigmaTheta|diagnostic|Diagnostic|coupling|Coupling`: 47/47 passaram.
- Filtro `LOT PKN.*identical`: 2/2 passaram.
- `python tools/generate_docs_index.py` executado.
- Validacoes manuais `validate` passaram para:
  - `cases/validation/lot_pkn_minimal.yaml`
  - `cases/validation/lot_pkn_with_leakoff.yaml`
  - `cases/lot_tese_migrated/buz67d_pkn.yaml`
- `run --mode lot-pkn` passou para os tres casos, com saidas em:
  - `results/phase10_10_minimal`
  - `results/phase10_10_leakoff`
  - `results/phase10_10_buz67d`

**Resultado:** Implementado e validado localmente, aguardando revisao/commit.

---

### [2026-06-04] Fase 10.9B — writer experimental CSV/JSON sigma-theta — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar um writer experimental opt-in para exportar resultados de
`LotSaltSigmaThetaDriverResult` em `points.csv`, `summary.csv` e
`metadata.json`, sem conectar ao CLI, sem alterar `ResultWriter` e sem tornar a
saida oficial do simulador.

**Implementacao:**
- Criada API `LotSaltSigmaThetaDiagnosticWriter` em `coupling/`.
- O writer consome cenarios ja calculados pelo driver sigma-theta e escreve:
  - `points.csv`, granular por ponto diagnostico em ordem time-major;
  - `summary.csv`, agregado por cenario;
  - `metadata.json`, com origem experimental, arquivos e caveats.
- A validacao exige `case_id`, `scenario_id`, `scenario_label`, resultado,
  diagnostico e tensao de parede validos, series PKN compatíveis e quantidade
  de pontos igual a `n_steps * n_wall_samples`.
- A fase nao altera `LotSaltSigmaThetaDriver`, `LotSaltSigmaThetaDiagnostic`,
  `LotSaltSigmaThetaBreakdown`, `SaltCreepTimeBridge`, `ResultWriter`,
  `apps/lot-sim.cpp`, parser, `CaseData`, YAMLs, LOT/APB, saltcreep, legados,
  baselines ou postprocess.

**Testes executados:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure`: 202/202 passaram.
- Filtro `writer|Writer|sigma_theta|SigmaTheta|diagnostic|Diagnostic|driver|Driver|coupling|Coupling`: 46/46 passaram.
- Filtro `LOT PKN.*identical`: 2/2 passaram.
- `python tools/generate_docs_index.py` executado.
- Validacoes manuais `validate` passaram para:
  - `cases/validation/lot_pkn_minimal.yaml`
  - `cases/validation/lot_pkn_with_leakoff.yaml`
  - `cases/lot_tese_migrated/buz67d_pkn.yaml`
- `run --mode lot-pkn` passou para os tres casos, com saidas em:
  - `results/phase10_9b_minimal`
  - `results/phase10_9b_leakoff`
  - `results/phase10_9b_buz67d`

**Resultado:** Implementado e validado localmente, aguardando revisao/commit.

---

### [2026-06-04] Fase 10.8B — matriz interna de cenarios sigma-theta — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar uma matriz interna controlada para comparar o diagnostico
sigma-theta em tres cenarios de confinamento, sem envolver `LOT_Tese`, sem
exportador CSV/JSON e sem alterar runtime.

**Implementacao:**
- Adicionado test case em `tests/cpp/test_lot_salt_sigma_theta_driver.cpp`.
- A matriz usa `cases/validation/lot_pkn_minimal.yaml` via parser real.
- Os tres cenarios comparados sao:
  - sem geostatica;
  - geostatica sintetica explicita com `geostatic_* = -2 MPa`;
  - geostatica litostatica via `with_lithostatic_geostatic(...)`.
- Helpers locais ao teste calculam `compressive_count`, `neutral_count`,
  `tensile_count`, min/max de
  `sigma_theta_compression_positive_Pa`, min/max de `margin_Pa`,
  `any_opened` e `any_legacy_algebra_opened`.
- Cada cenario verifica resultado valido, tensao de parede valida,
  diagnostico valido, pontos nao vazios, summary finito e `step_count`
  preservado.

**Observacao do snapshot atual:**
- Sem geostatica: 21 pontos `Tensile`.
- Geostatica sintetica `-2 MPa`: sem pontos `Compressive`.
- Geostatica litostatica: 21 pontos `Compressive`.

**Limites deliberados:**
- Nenhuma API publica foi criada.
- Nao houve alteracao em `LotSaltSigmaThetaDriver`,
  `LotSaltSigmaThetaDiagnostic`, `LotSaltSigmaThetaBreakdown`,
  `LotSaltBridgeConfigBuilder`, `LotSaltLithostaticContext`,
  `SaltCreepTimeBridge`, parser, `CaseData`, CLI, LOT/APB, YAMLs, schemas,
  `external/saltcreep/`, legados, baselines ou postprocess.
- A matriz permanece experimental/opt-in, usa snapshot unico e nao e
  validacao fisica de fratura.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

**Verificacao:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure`: 196/196 passaram.
- Filtro `scenario|Scenario|lithostatic|Lithostatic|driver|Driver|sigma_theta|SigmaTheta|coupling|Coupling`: 42/42 passaram.
- Filtro `LOT PKN.*identical`: 2/2 passaram.
- Teste isolado da matriz confirmou:
  - sem geostatica: 21 pontos `Tensile`;
  - geostatica sintetica `-2 MPa`: 0 pontos `Compressive`;
  - geostatica litostatica: 21 pontos `Compressive`;
  - todos os cenarios preservaram `step_count = 0`.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando
  `results/phase10_8b_minimal`, `results/phase10_8b_leakoff` e
  `results/phase10_8b_buz67d`.

---

### [2026-06-04] Fase 10.7 — teste integrado com geostatica litostatica — Codex

**Status:** Concluido e publicado em `bff4f14`.

**Objetivo:** Adicionar um teste integrado end-to-end para a rota opt-in:
`CaseData -> with_lithostatic_geostatic -> make_lot_salt_bridge_config ->
SaltCreepTimeBridge -> run_lot_salt_sigma_theta_experimental`.

**Implementacao:**
- Adicionado test case em `tests/cpp/test_lot_salt_sigma_theta_driver.cpp`.
- O teste usa `cases/validation/lot_pkn_minimal.yaml` via parser real.
- `with_lithostatic_geostatic()` preenche a geostatica litostatica em
  `LotSaltBridgeConfigOptions`.
- `make_lot_salt_bridge_config()` produz config com
  `geostatic_enabled=true`, tensoes geostaticas negativas e
  `fix_outer_wall=true`.
- O driver sigma-theta experimental roda sobre o bridge sem avancar o estado
  temporal (`step_count` preservado).
- O teste verifica resultado valido, tensao de parede valida, diagnostico
  valido, pontos diagnosticos nao vazios e estado hoop rastreavel.

**Limites deliberados:**
- Nenhuma nova API foi criada.
- `LotSaltLithostaticContext`, `LotSaltBridgeConfigBuilder`,
  `SaltCreepTimeBridge`, driver/diagnosticos sigma-theta, parser, `CaseData`,
  CLI, LOT/APB, YAMLs, schemas, `external/saltcreep/`, legados, baselines e
  postprocess nao foram alterados.
- O teste permanece experimental/opt-in e nao representa validacao fisica de
  fratura ou acoplamento temporal.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

**Verificacao:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure`: 195/195 passaram.
- Filtro `lithostatic|Lithostatic|driver|Driver|sigma_theta|SigmaTheta|bridge_config|BridgeConfig|coupling|Coupling`: 52/52 passaram.
- Filtro `LOT PKN.*identical`: 2/2 passaram.
- Teste isolado da Fase 10.7 confirmou `geostatic_* = -63547092 Pa`,
  `fix_outer_wall=true`, `step_count` preservado em 0 e estado hoop
  rastreavel; houve ao menos um estado `Compressive` no snapshot observado.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando
  `results/phase10_7_minimal`, `results/phase10_7_leakoff` e
  `results/phase10_7_buz67d`.

---

### [2026-06-04] Fase 10.6B — contexto litostatico opt-in para geostatica — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar um helper experimental opt-in em `coupling/` para derivar
uma geostatica litostatica isotropica simples a partir de `CaseData`, sem
alterar parser, `CaseData`, builder principal automaticamente ou runtime LOT.

**Implementacao:**
- Criado `include/coupling/LotSaltLithostaticContext.hpp`.
- Criado `src/coupling/LotSaltLithostaticContext.cpp`.
- Criado `tests/cpp/test_lot_salt_lithostatic_context.cpp`.
- `make_lot_salt_lithostatic_context(data)` seleciona a layer que contem
  `lot.shoe_depth_m`, resolve a rocha por `layer.rock_id`, valida
  `rock.density_kg_m3 > 0` e calcula `rho_rock * g * depth`.
- `with_lithostatic_geostatic(options, data)` retorna options com
  `geostatic_enabled=true` e as tres tensoes geostaticas iguais a
  `-lithostatic_pressure_Pa`.

**Limites deliberados:**
- A aproximacao e isotropica e nao representa tensor in situ real.
- Nao inclui tectonica, pressao de poros, anisotropia ou closure stress.
- Nao identifica automaticamente se a rocha e sal.
- CLI, parser, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter`,
  `SaltCreepTimeBridge`, diagnosticos sigma-theta, pressure map, coupling
  config builder, hydrostatic context, YAMLs, schemas, LOT/APB, sal,
  `external/saltcreep/`, legados, baselines e postprocess nao foram alterados.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

**Verificacao:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure`: 194/194 passaram.
- Filtro `lithostatic|Lithostatic|bridge_config|BridgeConfig|sigma_theta|SigmaTheta|driver|Driver|coupling|Coupling`: 51/51 passaram.
- Filtro `LOT PKN.*identical`: 2/2 passaram.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando
  `results/phase10_6b_minimal`, `results/phase10_6b_leakoff` e
  `results/phase10_6b_buz67d`.

---

### [2026-06-04] Fase 10.5B — classificacao explicita de hoop tensile state — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Permitir que o diagnostico experimental `sigma_theta` represente
explicitamente estados tangenciais trativos em vez de rejeitar
`sigma_theta_compression_positive_Pa < 0` por excecao.

**Implementacao:**
- Adicionado `SigmaThetaHoopState` com estados `Compressive`, `Neutral` e
  `Tensile`.
- Adicionados `classify_sigma_theta_hoop_state()` e `to_string()`.
- `SigmaThetaBreakdownPoint` passou a carregar `hoop_state`,
  `tensile_hoop_state`, `legacy_algebra_opened` e `caveat`.
- `LotSaltSigmaThetaBreakdown` continua rejeitando `NaN`/`Inf`, mas nao rejeita
  mais `sigma_theta_compression_positive_Pa < 0`.
- `LotSaltSigmaThetaDiagnostic` tambem aceita amostras trativas de
  `SaltWallStressDiagnostics` e preserva o estado/caveat no resultado.
- Testes do driver builder -> bridge -> driver deixam de sobrescrever
  `bridge_config.wall_pressure_Pa = 0.0`; a pressao hidrostatica derivada pelo
  builder agora pode produzir estado `Tensile` rastreavel.

**Limites deliberados:**
- `opened` em estado `Tensile` representa apenas algebra experimental/legada
  (`pressure > -getSigmaTheta()`), nao criterio fisico validado.
- CLI, parser, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter`,
  `SaltCreepInterface`, `SaltCreepResponse`, adapters de sal, bridge, pressure
  map, builders hidrostatico/bridge, YAMLs, schemas, LOT/APB, sal,
  `external/saltcreep/`, legados, baselines e postprocess nao foram alterados.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 186/186.
- Filtro `sigma_theta|SigmaTheta|diagnostic|Diagnostic|driver|Driver|
  coupling|Coupling` passou com 36/36.
- Filtro `LOT PKN.*identical` passou com 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase10_5b_minimal`, `results/phase10_5b_leakoff` e
  `results/phase10_5b_buz67d`.

---

### [2026-06-04] Fase 10.4 — geostatica explicita e teste builder-bridge-driver — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Expandir `LotSaltBridgeConfigOptions` com geostatica explicita e
testar a cadeia experimental `CaseData -> LotSaltBridgeConfigBuilder ->
SaltCreepTimeBridge -> LotSaltSigmaThetaDriver`.

**Fase 10.4A — geostatica explicita:**
- `LotSaltBridgeConfigOptions` recebeu
  `geostatic_radial_stress_Pa`, `geostatic_hoop_stress_Pa` e
  `geostatic_vertical_stress_Pa`.
- `geostatic_enabled=true` agora preenche as tres tensoes no
  `SaltCreepTimeBridgeConfig` e marca `fix_outer_wall=true`.
- Tensoes geostaticas precisam ser finitas; `NaN`/`Inf` sao rejeitados.
- O default sem geostatica preserva a Fase 10.3.

**Fase 10.4B — cadeia integrada:**
- Adicionados testes que parseiam `lot_pkn_minimal.yaml`, constroem
  `SaltCreepTimeBridgeConfig` pelo builder, instanciam `SaltCreepTimeBridge` e
  chamam `run_lot_salt_sigma_theta_experimental(data, bridge)`.
- A cadeia foi testada sem geostatica e com geostatica explicita.
- O driver continua usando snapshot unico e nao avanca o bridge.

**Limites deliberados:**
- Geostatica vem de options, nao de `CaseData`.
- Nenhuma tensao litostatica e calculada automaticamente.
- CLI, parser, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter`,
  `SaltCreepTimeBridge`, driver, diagnostic, pressure map, YAMLs, schemas,
  LOT/APB, sal, `external/saltcreep/`, legados, baselines e postprocess nao
  foram alterados.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 180/180.
- Filtro `bridge_config|BridgeConfig|sigma_theta|SigmaTheta|wall_stress|
  WallStress|time_bridge|TimeBridge|saltcreep` passou com 48/48.
- Filtro `LOT PKN.*identical` passou com 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase10_4_minimal`, `results/phase10_4_leakoff` e
  `results/phase10_4_buz67d`.
- `git diff --check` passou com aviso CRLF conhecido em `docs/dev-log.md`.

---

### [2026-06-04] Fase 10.3 — `LotSaltBridgeConfigBuilder` experimental — Codex

**Status:** Implementado nesta sessao, sem commit/push ate a verificacao final.

**Objetivo:** Criar um helper experimental opt-in em `coupling/` para montar
`SaltCreepTimeBridgeConfig` a partir de `CaseData` e options explicitas, sem
construir nem avancar o bridge.

**Implementacao:**
- Criado `include/coupling/LotSaltBridgeConfigBuilder.hpp`.
- Criado `src/coupling/LotSaltBridgeConfigBuilder.cpp`.
- Criado `tests/cpp/test_lot_salt_bridge_config_builder.cpp`.
- O helper seleciona a unica layer que contem `lot.shoe_depth_m`, resolve a
  rocha via `layer.rock_id`, copia `E_Pa` e `nu`, usa geometria/temperatura das
  options e deriva `wall_pressure_Pa` inicial via `LotSaltHydrostaticContext`.

**Limites deliberados:**
- `SaltCreepTimeBridge` nao e construido pelo helper.
- `bridge.advance_to()`, `bridge.advance_by()` e
  `bridge.wall_stress_diagnostics()` nao sao chamados pelo helper.
- Geostatica nao e inferida de `CaseData`; `geostatic_enabled=true` e rejeitado
  nesta fase.
- `height_m = lot.fracture_height_m` e aproximacao experimental documentada.
- CLI, parser, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter`, YAMLs,
  LOT/APB, sal, `external/saltcreep/`, legados, baselines e postprocess
  permanecem fora do escopo.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 175/175.
- Filtro `bridge_config|BridgeConfig|bridge|Bridge|driver|Driver|
  sigma_theta|SigmaTheta|wall_stress|WallStress|coupling|Coupling` passou com
  54/54.
- Filtro `LOT PKN.*identical` passou com 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase10_3_minimal`, `results/phase10_3_leakoff` e
  `results/phase10_3_buz67d`.

---

### [2026-06-04] Fase 10.2B — `LotSaltSigmaThetaDriver` experimental opt-in — Codex

**Status:** Implementado nesta sessao, sem commit/push ate a verificacao final.

**Objetivo:** Criar um driver experimental opt-in em `coupling/` que recebe
`CaseData`, `SaltCreepTimeBridge&` ja configurado e
`LotSaltCouplingConfigOptions`, executando a cadeia diagnostica:

```text
CaseData -> LotSaltCouplingConfigBuilder -> run_pkn_case(data)
         -> bridge.wall_stress_diagnostics()
         -> evaluate_lot_salt_sigma_theta_series(...)
```

**Implementacao:**
- Criado `include/coupling/LotSaltSigmaThetaDriver.hpp`.
- Criado `src/coupling/LotSaltSigmaThetaDriver.cpp`.
- Criado `tests/cpp/test_lot_salt_sigma_theta_driver.cpp`.
- O resultado composto carrega `PknRun`, `LotSaltCouplingConfig`,
  `SaltWallStressDiagnostics`, `LotSaltSigmaThetaDiagnosticResult`, `valid` e
  `caveat`.

**Limites deliberados:**
- O driver nao constroi `SaltCreepTimeBridgeConfig`.
- O driver nao chama `bridge.advance_to()` nem `bridge.advance_by()`.
- O driver nao constroi nem chama `SaltCreepSaltcreepAdapter`.
- O driver nao chama `SaltCreepInterface`.
- O driver nao chama `evaluate_lot_salt_step()`.
- O driver usa snapshot unico de tensao do bridge e nao sincroniza tensoes do
  sal com cada passo PKN.
- CLI, parser, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter`, YAMLs,
  LOT/APB, `external/saltcreep/`, legados, baselines e postprocess permanecem
  fora do escopo.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 167/167.
- Filtro `driver|Driver|sigma_theta|SigmaTheta|diagnostic|Diagnostic|
  wall_stress|WallStress|coupling|Coupling` passou com 28/28.
- Filtro `LOT PKN.*identical` passou com 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase10_2b_minimal`, `results/phase10_2b_leakoff` e
  `results/phase10_2b_buz67d`.

---

### [2026-06-04] Fase 10.1 — `LotSaltSigmaThetaDiagnostic` opt-in — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar um helper puro em `coupling/` para diagnostico experimental
end-to-end por `sigma_theta`, recebendo `PknResult`, `LotSaltCouplingConfig` e
`SaltWallStressDiagnostics`.

**Implementacao:**
- Criado `include/coupling/LotSaltSigmaThetaDiagnostic.hpp`.
- Criado `src/coupling/LotSaltSigmaThetaDiagnostic.cpp`.
- Criado `tests/cpp/test_lot_salt_sigma_theta_diagnostic.cpp`.
- O helper monta `LotSaltPressureMapInput`, chama
  `map_lot_pkn_to_salt_wall_pressure()` e usa
  `LotSaltPressureMapResult.wall_pressure_Pa` no criterio experimental.
- Cada `SaltWallStressSample` vira uma `SigmaThetaInfluenceLayer` deterministica
  `wall_gp_<indice>`, preservando metadados de ponto de Gauss, elemento,
  coordenadas, profundidade, tensao media, `J2` e von Mises no resultado.

**Limites deliberados:**
- O helper nao chama `SaltCreepInterface`.
- O helper nao chama `SaltCreepTimeBridge`.
- O helper nao chama `SaltCreepSaltcreepAdapter`.
- `LotSaltCouplingStep`, `LotSaltPressureMap`,
  `LotSaltSigmaThetaBreakdown`, `LotSaltHydrostaticContext`,
  `LotSaltCouplingConfigBuilder`, parser, `CaseData`, LOT/APB, CLI, YAMLs,
  `external/saltcreep/`, legados, baselines e postprocess nao foram alterados.
- `SaltWallStressDiagnostics` e snapshot fornecido pelo chamador; a fase nao
  garante sincronizacao temporal com cada passo PKN.
- O diagnostico permanece experimental, opt-in e nao validado como criterio
  fisico de fratura.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 164/164.
- Filtro `sigma_theta|SigmaTheta|diagnostic|Diagnostic|wall_stress|WallStress|
  coupling|Coupling` passou com 25/25.
- Filtro `LOT PKN.*identical` passou com 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase10_1_minimal`, `results/phase10_1_leakoff` e
  `results/phase10_1_buz67d`.

---

### [2026-06-04] Fase 9.9B — `SaltWallStressDiagnostics` opt-in — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Expor diagnostico opt-in de tensao de parede a partir de
`SaltCreepTimeBridge`, usando DTOs publicos do LSS e sem expor headers de
`external/saltcreep/` na API publica.

**Pre-verificacao do saltcreep:**
- `StressSampler` usa namespace real `stress_sampler`.
- A assinatura real usada e
  `stress_sampler::sample_wall_gauss_points(const Mesh&, const Element&,
  const TimeState&, double depth_origin_m)`.
- O tipo real `StressSample` carrega `gp_id`, `element_id`, `local_gp_id`,
  `r_m`, `z_m`, `depth_m`, `sigma`, `deviatoric`, `mean_stress_Pa`,
  `J2_Pa2` e `sigma_ef_Pa`.
- `TimeIntegrator::state()` retorna `const TimeState&`.
- O `SaltCreepTimeBridge::Impl` ja possui `mesh`, `element` e `integrator`.

**Implementacao:**
- Criado `SaltWallStressDiagnostics` com amostras de tensao de parede em tipos
  LSS puros.
- `SaltCreepTimeBridge::wall_stress_diagnostics()` converte internamente os
  `StressSample` do saltcreep para DTOs LSS.
- `sigma_theta_compression_positive_Pa` e obtido por
  `stress_utils::sigma_theta_compression_positive(sample.sigma)`.
- A amostra de parede e o ponto de Gauss mais proximo da parede interna, sem
  extrapolacao para `r = Ri`.

**Limites deliberados:**
- `SaltCreepInterface` e `SaltCreepResponse` nao foram alterados.
- `LotSaltSigmaThetaBreakdown` nao foi alterado.
- O diagnostico nao e chamado pelo CLI e nao altera `lot-sim run --mode
  lot-pkn`.
- `deviatoric`, `J2` e von Mises sao expostos como diagnostico, mas nao viram
  criterio fisico validado de fratura.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 158/158.
- Filtro `wall_stress|WallStress|stress_diagnostics|StressDiagnostics|
  sigma_theta|SigmaTheta|bridge|Bridge|coupling|Coupling` passou com 37/37.
- Filtro `LOT PKN.*identical` passou com 2/2.

---

### [2026-06-04] Fase 9.8 — diagnostico experimental por `sigma_theta` — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar `LotSaltSigmaThetaBreakdown` como diagnostico puro em
`coupling/` para comparar uma pressao de parede contra
`sigma_theta_compression_positive_Pa` por camada/altura de influencia.

**Criterio implementado:**

```text
margin_Pa = pressure_Pa - sigma_theta_compression_positive_Pa
opened = margin_Pa > 0
```

Igualdade nao indica abertura. A funcao de serie retorna pontos em ordem
deterministica tempo externo/camada interna.

**Convencao de sinal:**
- A API recebe `sigma_theta_compression_positive_Pa` ja convertido.
- Para reproduzir o legado quando `getSigmaTheta()` retornar compressao
  negativa, o chamador deve usar `sigma_theta_compression_positive_Pa =
  -getSigmaTheta()`.
- Nenhuma conversao automatica de sinal foi implementada.

**Limites deliberados:**
- O diagnostico nao chama `SaltCreepInterface`.
- `getDeviatoricStress()` foi mantido como candidato futuro e nao foi
  implementado.
- `LotSaltPressureMap`, `LotSaltCouplingStep`, `LotSaltHydrostaticContext`,
  `LotSaltCouplingConfigBuilder`, `PknRunner`, `PknModel`, parser,
  `CaseData`, CLI, YAMLs, LOT/APB, sal externo, baselines e postprocess nao
  foram alterados.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

**Verificacao executada:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou com 153/153.
- Filtro `sigma_theta|SigmaTheta|breakdown|Breakdown|coupling|Coupling`
  passou com 14/14.
- Filtro `LOT PKN.*identical` passou com 2/2.
- `lot-sim validate` e `lot-sim run --mode lot-pkn` passaram para os casos
  `lot_pkn_minimal.yaml`, `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.

---

### [2026-06-04] Fase 9.7A — limitacoes de inferencia de breakdown no PKN atual — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Documentar que o fluxo PKN moderno atual ainda nao fornece um
evento fisico robusto de breakdown nem `p_net_at_breakdown`.

**Conclusao documental:**
- `breakdown_pressure_Pa` e parseado, validado e repassado para `PknInput`, mas
  nao controla diretamente o inicio da fratura, a geracao das series PKN ou
  `PknResult.net_pressure_series_Pa`.
- `PknModel` gera uma resposta PKN ja iniciada/ativa, nao uma rampa
  pre-breakdown ate ruptura.
- `PknResult` ainda nao expoe `breakdown_step`, `breakdown_time_s`,
  `p_net_at_breakdown` ou `fracture_initiation_step`.
- `p_net_at_breakdown` nao deve ser inferido por primeiro `p_net > 0`, primeiro
  `width`, `length` ou `volume` positivo, `breakdown_pressure_Pa` ou aplicacao
  direta de `BreakdownDetector` sobre `net_pressure_series_Pa`.
- `BreakdownDetector` continua adequado para curvas pressao-volume absolutas,
  observadas ou estimadas, mas nao para a serie PKN isolada de pressao liquida.
- `BreakdownReferencedPressure` permanece candidato futuro, nao implementado,
  nao default runtime e bloqueado pela ausencia de `p_net_at_breakdown` /
  `breakdown_step` robustos.

**Caminho futuro registrado:**
- Possivel `PknBreakdownDiagnostics` opt-in, separado do solver e marcado como
  heuristico ate existir pressao absoluta, curva LOT validada, closure stress,
  tensao minima horizontal, pressao de poros ou referencia externa robusta.

**Limite deliberado:**
- Nenhum codigo C++ foi alterado.
- `CMakeLists.txt`, testes, YAMLs, parser, `CaseData`, `PknRunner`,
  `PknModel`, `ResultWriter`, `apps/lot-sim.cpp`, `external/saltcreep/`,
  `legacy/`, `legance/`, baselines e postprocess nao foram alterados.

---

### [2026-06-04] Fase 9.6A — `BreakdownReferencedPressure` candidato futuro — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Documentar `BreakdownReferencedPressure` como metodo candidato
futuro para mapeamento LOT/PKN -> sal, sem implementar codigo runtime.

**Formula conceitual registrada:**

```text
p_wall = p_breakdown + (p_net_current - p_net_at_breakdown)
```

**Classificacao documental:**
- `status: candidate future method`;
- `implementation: not implemented`;
- `runtime default: no`;
- `physical validation: pending`;
- requer `breakdown_pressure_Pa` fisicamente valido e `p_net_at_breakdown` ou
  `breakdown_step` robusto.

**Motivo para nao implementar ainda:**
- `LotConfig.breakdown_pressure_Pa` e parseado de
  `lot.fracture.breakdown.pressure` e hoje funciona como parametro/threshold
  do contrato, nao como serie temporal de pressao absoluta do poco.
- `PknModel` calcula `PknResult.net_pressure_series_Pa` por
  `p_net = E' * w / h`, independente de `breakdown_pressure_Pa` na evolucao da
  serie.
- `PknResult` ainda nao expoe `p_net_at_breakdown`,
  `net_pressure_at_breakdown`, `breakdown_step`, `breakdown_time_s` ou
  `fracture_initiation_step`.
- `cases/lot_tese_migrated/buz67d_pkn.yaml` contem
  `breakdown_pressure_Pa = 1 Pa` como placeholder/R09_PENDING_REVIEW e nao pode
  validar fisicamente esse metodo.

**Documentacao atualizada:**
- `docs/13_coupling_lot_apb_salt.md` recebeu a secao do candidato
  `BreakdownReferencedPressure`, comparacao com `HydrostaticPlusNetPressure`,
  condicao especial do BUZ67D, opcoes futuras e separacao conceitual de APB.
- `docs/02_lot_formulation.md` registra o status atual de
  `breakdown_pressure_Pa` e a ausencia de campos de breakdown em `PknResult`.
- `tools/docs_status.yaml` registra a Fase 9.6A como concluida.

**Limite deliberado:**
- Nenhum codigo C++ foi alterado.
- `CMakeLists.txt`, testes, YAMLs, parser, `CaseData`, `PknRunner`,
  `PknModel`, `ResultWriter`, `apps/lot-sim.cpp`, `external/saltcreep/`,
  `legacy/`, `legance/`, baselines e postprocess nao foram alterados.

---

### [2026-06-04] Fase 9.5A — formulacao fisica de `HydrostaticPlusNetPressure` — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Documentar formalmente as limitacoes fisicas do metodo
`HydrostaticPlusNetPressure` antes de qualquer wiring runtime ou acoplamento
operacional.

**Conclusao documental:**
- `HydrostaticPlusNetPressure` permanece `provisional approximation / opt-in only`.
- A validacao fisica do metodo ainda nao esta concluida.
- O metodo nao deve virar default runtime.
- O uso permitido fica restrito a estudos controlados, testes de cadeia e
  aproximacoes preliminares.

**Motivo fisico:**
- `PknResult.net_pressure_series_Pa` vem de `p_net = E' * w / h`.
- `p_net` e pressao liquida PKN associada a abertura elastica da fratura.
- `p_net` nao carrega explicitamente `sigma_closure`, tensao horizontal minima,
  pressao de poros, tensao radial geostatica ou referencia geomecanica completa.
- `SaltCreepQuery.wall_pressure_Pa` deve representar pressao compressiva
  absoluta na parede do sal ou condicao radial equivalente bem definida.

**Documentacao atualizada:**
- `docs/13_coupling_lot_apb_salt.md` recebeu a classificacao formal do metodo,
  status dos mapeamentos existentes, candidatos futuros e checklist minima antes
  de wiring runtime.
- `docs/02_lot_formulation.md` reforca que `p_net` nao inclui closure stress,
  tensao minima horizontal, pressao de poros ou referencia geomecanica completa.
- `docs/03_apb_formulation.md` registra que APB futuro deve fornecer pressao
  anular absoluta por tempo/profundidade por metodo proprio, separado de
  `HydrostaticPlusNetPressure`.
- `tools/docs_status.yaml` registra a Fase 9.5A como concluida.

**Limite deliberado:**
- Nenhum codigo C++ foi alterado.
- `CMakeLists.txt`, testes, YAMLs, parser, `CaseData`, `PknRunner`,
  `PknModel`, `ResultWriter`, `apps/lot-sim.cpp`, `external/saltcreep/`,
  `legacy/`, `legance/`, baselines e postprocess nao foram alterados.
- `lot-sim run --mode lot-pkn` permanece desacoplado.

---

### [2026-06-04] Fase 9.4B — `LotSaltCouplingConfigBuilder` opt-in — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar um builder opt-in em `coupling/` para montar
`LotSaltCouplingConfig` a partir de `LotSaltHydrostaticContext` ou diretamente
de `CaseData`, sem alterar `evaluate_lot_salt_step()`, CLI, parser, `CaseData`
ou o fluxo `lot-sim run --mode lot-pkn`.

**Mudanca implementada:**
- Criado `include/coupling/LotSaltCouplingConfigBuilder.hpp`.
- Criado `src/coupling/LotSaltCouplingConfigBuilder.cpp`.
- Criado `tests/cpp/test_lot_salt_coupling_config_builder.cpp`.
- `CMakeLists.txt` passou a incluir o novo source e o novo teste no target
  existente.

**Regra implementada:**
- O builder a partir de `LotSaltHydrostaticContext` copia
  `hydrostatic_pressure_Pa` e `depth_m` do contexto.
- `surface_pressure_Pa`, `temperature_K`, `radial_position_m` e
  `pressure_map_method` vêm de `LotSaltCouplingConfigOptions`.
- O default local do builder e `HydrostaticPlusNetPressure`.
- O default global de `LotSaltCouplingConfig` permanece
  `ExperimentalNetPressureProxy`.

**Limite deliberado:**
- `LotSaltCouplingStep` nao foi alterado.
- `LotSaltPressureMap` nao foi alterado.
- `CaseParser`, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter` e
  `apps/lot-sim.cpp` nao foram alterados.
- O builder nao e chamado por `lot-sim` nem por `PknRunner`.
- A fase habilita apenas encadeamento opt-in testavel, nao acoplamento fisico
  completo.

**Testes/builds executados:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou: 146/146.
- `ctest --test-dir build -C Debug --output-on-failure -R "config_builder|ConfigBuilder|hydrostatic|Hydrostatic|pressure_map|lot_salt|coupling|Coupling|units"` passou: 30/30.
- `ctest --test-dir build -C Debug --output-on-failure -R "LOT PKN.*identical"` passou: 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase9_4b_minimal`, `results/phase9_4b_leakoff` e
  `results/phase9_4b_buz67d`.

---

### [2026-06-04] Fase 9.3B — `LotSaltHydrostaticContext` em `coupling/` — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Criar um helper puro em `coupling/` para derivar
`hydrostatic_pressure_Pa` a partir de `CaseData` ja parseado, sem alterar parser,
runner, YAMLs ou fluxo `lot-sim run --mode lot-pkn`.

**Mudanca implementada:**
- Criado `include/coupling/LotSaltHydrostaticContext.hpp`.
- Criado `src/coupling/LotSaltHydrostaticContext.cpp`.
- Criado `tests/cpp/test_lot_salt_hydrostatic_context.cpp`.
- `CMakeLists.txt` passou a incluir o novo source e o novo teste no target
  existente.

**Regra implementada:**
- Usa `CaseData.lot.shoe_depth_m` como profundidade.
- Seleciona exatamente um `AnnularData` que contem a sapata.
- Seleciona `FluidData` pelo `annular.fluid_id`.
- Calcula `hydrostatic_pressure_Pa` com
  `units::hydrostatic_pressure_Pa(fluid.density_kg_m3, shoe_depth_m)`.

**Limite deliberado:**
- `LotSaltPressureMap` nao foi alterado.
- `LotSaltCouplingStep` nao foi alterado.
- `CaseParser`, `CaseData`, `PknRunner`, `PknModel`, `ResultWriter` e
  `apps/lot-sim.cpp` nao foram alterados.
- O helper nao usa `wellbore`, `surface_pressure_Pa`, `weight_lb_per_gal` ou
  `hydrostatic_depth_profile` nesta fase.
- O helper ainda nao esta conectado automaticamente ao coupling step.
- `lot-sim run --mode lot-pkn` segue desacoplado do sal.

**Testes/builds executados:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou: 139/139.
- `ctest --test-dir build -C Debug --output-on-failure -R "hydrostatic|Hydrostatic|pressure_map|lot_salt|coupling|Coupling|units"` passou: 23/23.
- `ctest --test-dir build -C Debug --output-on-failure -R "LOT PKN.*identical"` passou: 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase9_3b_minimal`, `results/phase9_3b_leakoff` e
  `results/phase9_3b_buz67d`.

---

### [2026-06-04] Fase 9.2B — Utilitarios hidrostaticos puros em `units/` — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Fornecer a base matematica reutilizavel para calcular pressao
hidrostatica sem automatizar ainda o fluxo `YAML -> CaseParser -> CaseData ->
coupling`.

**Mudanca implementada:**
- `include/units/units.hpp` recebeu:
  - `hydrostatic_pressure_Pa(density_kg_m3, depth_m, g)`;
  - `ppg_hydrostatic_pressure_Pa(ppg, depth_m, g)`;
  - `surface_plus_hydrostatic_pressure_Pa(surface_pressure_Pa,
    density_kg_m3, depth_m, g)`.
- As novas funcoes usam validacao robusta e rejeitam NaN, infinito, densidade
  negativa, ppg negativo, profundidade negativa, gravidade nao positiva e
  pressao de superficie negativa.
- `tests/cpp/test_units.cpp` cobre calculo SI, calculo por ppg, superficie +
  hidrostatica, profundidade zero e entradas invalidas.

**Limite deliberado:**
- `LotSaltPressureMap` nao foi alterado.
- `LotSaltCouplingStep` nao foi alterado.
- `CaseParser` e `CaseData` nao foram alterados.
- `HydrostaticPlusNetPressure` continua recebendo `hydrostatic_pressure_Pa`
  pronta.
- `lot-sim run --mode lot-pkn` segue desacoplado do sal.

**Testes/builds executados:**
- `cmake --build build --config Debug -j` passou.
- `ctest --test-dir build -C Debug --output-on-failure` passou: 131/131.
- `ctest --test-dir build -C Debug --output-on-failure -R "units|hydrostatic|pressure_map|lot_salt|coupling|Coupling"` passou: 12/12.
- `ctest --test-dir build -C Debug --output-on-failure -R "LOT PKN.*identical"` passou: 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results/phase9_2b_minimal`, `results/phase9_2b_leakoff` e
  `results/phase9_2b_buz67d`.

---

### [2026-06-04] Fase 9.1B — `LotSaltPressureMap` explicito para LOT/PKN -> sal — Codex

**Status:** Implementado nesta sessao, sem commit/push por instrucao da fase.

**Objetivo:** Remover o uso direto de `PknResult.net_pressure_series_Pa` como
`SaltCreepQuery.wall_pressure_Pa` dentro de `evaluate_lot_salt_step()`,
mantendo o comportamento default da Fase 9.0 por compatibilidade.

**Mudanca implementada:**
- Criado `include/coupling/LotSaltPressureMap.hpp`.
- Criado `src/coupling/LotSaltPressureMap.cpp`.
- Criado `tests/cpp/test_lot_salt_pressure_map.cpp`.
- `LotSaltCouplingConfig` recebeu `pressure_map_method`,
  `absolute_wellbore_pressure_Pa`, `hydrostatic_pressure_Pa`,
  `surface_pressure_Pa` e `depth_m`.
- `LotSaltCouplingStepResult` passou a expor `pressure_map`.
- `evaluate_lot_salt_step()` monta `LotSaltPressureMapInput`, chama
  `map_lot_pkn_to_salt_wall_pressure()` e usa
  `LotSaltPressureMapResult.wall_pressure_Pa` na query do sal.

**Metodos implementados:**
- `ExperimentalNetPressureProxy`: `wall_pressure_Pa = net_pressure_Pa`,
  `physically_absolute = false`. Default temporario para compatibilidade com
  a Fase 9.0.
- `AbsoluteWellborePressure`: usa `absolute_wellbore_pressure_Pa` e ignora
  `net_pressure_Pa`, com `physically_absolute = true`.
- `HydrostaticPlusNetPressure`: soma `surface_pressure_Pa`,
  `hydrostatic_pressure_Pa` e `net_pressure_Pa`, com
  `physically_absolute = true`. O calculo `rho*g*depth` ainda nao foi integrado
  ao `coupling/`.

**Escopo preservado:**
- Nenhum arquivo em `external/saltcreep/`, `legacy/`, `legance/`,
  `tests/baselines/`, `postprocess/`, `src/lot/`, `include/lot/`,
  `src/apb/`, `include/apb/`, `src/io/`, `include/io/`,
  `PknRunner`, `PknModel`, `CaseParser`, `ResultWriter` ou
  `apps/lot-sim.cpp` foi alterado.
- `lot-sim run --mode lot-pkn` segue desacoplado do sal.

**Testes/builds executados:**
- `cmake --build build --config Debug -j`: OK.
- `ctest --test-dir build -C Debug --output-on-failure`: 127/127 passaram.
- `ctest --test-dir build -C Debug --output-on-failure -R "pressure_map|lot_salt|coupling|Coupling"`:
  8/8 passaram.
- `ctest --test-dir build -C Debug --output-on-failure -R "PressureMap|pressure_map|lot_salt|coupling|Coupling"`:
  12/12 passaram.
- `ctest --test-dir build -C Debug --output-on-failure -R "LOT PKN result is identical"`:
  1/1 passou; filtro ampliado `LOT PKN.*identical` passou 2/2.
- `lot-sim validate` passou para `lot_pkn_minimal.yaml`,
  `lot_pkn_with_leakoff.yaml` e `buz67d_pkn.yaml`.
- `lot-sim run --mode lot-pkn` passou para os tres casos, gerando saidas em
  `results\phase9_1b_minimal`, `results\phase9_1b_leakoff` e
  `results\phase9_1b_buz67d`.

---

### [2026-06-04] Fase 9.1A — Formalizacao documental da pressao de parede LOT/PKN/sal — Codex

**Status:** Concluido nesta sessao como fase documental/formulacional.

**Objetivo:** Formalizar o contrato de pressao entre o resultado LOT/PKN e a
interface de sal antes de implementar `LotSaltPressureMap`.

**Conclusao fisica documentada:**
- `PknResult.net_pressure_series_Pa` representa a pressao liquida PKN.
- No modelo PKN minimo, `p_net = E' * w / h`.
- `p_net` e uma pressao relativa de fratura associada a abertura `w` e ao
  modulo plano `E'`; nao e pressao absoluta de poco, pressao anular ou pressao
  fisica de parede do sal.
- `SaltCreepQuery.wall_pressure_Pa` deve representar uma pressao compressiva
  absoluta aplicada na parede do sal, ou uma condicao radial equivalente
  explicitamente definida.

**Contrato preparado para Fase 9.1B:**
- Documentados os metodos candidatos `ExperimentalNetPressureProxy`,
  `AbsoluteWellborePressure` e `HydrostaticPlusNetPressure`.
- Documentados dados disponiveis hoje (`net_pressure_series_Pa`,
  `breakdown_pressure_Pa`, densidade de fluido, campos hidrostaticos quando
  aplicaveis, profundidade da sapata, anulares e gradiente ppg).
- Documentados dados ausentes ou ainda nao integrados: pressao absoluta por
  tempo, pressao de bombeio/superficie por tempo, pressao na sapata por tempo,
  pressao anular APB por tempo, pressao de poros, closure stress, tensao radial
  geostatica, `wellbore` persistido em `CaseData`, estado APB calculado e regra
  explicita para converter PKN em pressao absoluta.
- Proposta API conceitual para `LotSaltPressureMap`.

**Arquivos alterados:**
- `docs/13_coupling_lot_apb_salt.md`
- `docs/02_lot_formulation.md`
- `docs/03_apb_formulation.md`
- `docs/dev-log.md`
- `tools/docs_status.yaml`
- `docs/index.html`

**Escopo preservado:**
- Nenhum codigo C++, CMake, teste, caso YAML, `external/saltcreep/`, `legacy/`,
  `legance/`, baseline ou `postprocess/` foi alterado.
- Nenhum commit ou push foi executado por instrucao da fase.

---

### [2026-06-04 09:21] `c6c5867` — Themisson
**Commit:** `feat(coupling): add experimental salt injection point for LOT/PKN (Fase 9.0)`
**Testes C++:** 20 arquivos | **Testes Python:** 1 arquivos
**Último resultado ctest:** All tests passed (6 assertions in 1 test case)
**Arquivos alterados:**
- `CMakeLists.txt`
- `docs/13_coupling_lot_apb_salt.md`
- `docs/16_saltcreep_governance.md`
- `docs/index.html`
- `include/coupling/LotSaltCouplingStep.hpp`
- `src/coupling/LotSaltCouplingStep.cpp`
- `tests/cpp/test_lot_pkn_salt_coupling_step.cpp`
- `tools/docs_status.yaml`

---

### [2026-06-04] Fase 9.0 — Ponto experimental de injecao em coupling/ — Claude Code

**Status:** Concluido nesta sessao.

**Objetivo:** Criar o primeiro ponto de chamada real de `SaltCreepInterface` a
partir de um resultado LOT/PKN, em caminho experimental separado em `coupling/`,
sem alterar `PknRunner`, `PknModel`, `lot-sim` ou o caminho padrao `lot-pkn`.

**Mudanca implementada:**
- Criado `include/coupling/LotSaltCouplingStep.hpp` com `LotSaltCouplingConfig`,
  `LotSaltCouplingStepResult` e `evaluate_lot_salt_step()`.
- Criado `src/coupling/LotSaltCouplingStep.cpp` com a implementacao que
  constroi `SaltCreepQuery` a partir de `PknResult.time_series_s[step_index]`
  e `net_pressure_series_Pa[step_index]` e chama `salt.evaluate_wall_response()`.
- Criado `tests/cpp/test_lot_pkn_salt_coupling_step.cpp` com 6 testes Catch2.
- `CMakeLists.txt` atualizado para incluir o novo fonte e teste no mesmo commit
  (prevencao do problema `cb61159`).

**Prova central:**
- `SpySaltCreepInterface::call_count() == 1` apos uma chamada a `evaluate_lot_salt_step`.
- `SpySaltCreepInterface::call_count() == 3` apos tres chamadas consecutivas.
- Isso contrasta com a Fase 8.1, onde `call_count() == 0` porque o spy nunca foi injetado.

**Limite deliberado — fisico:**
- `net_pressure_series_Pa[step_index]` e usado como `wall_pressure_Pa` apenas
  como sinal experimental de demonstracao. Ele nao representa a pressao anular
  real de parede no sal. O mapeamento fisico correto (pressao anular/poco ->
  condicao de contorno do sal) fica pendente para fase futura.
- A funcao e feedforward: nao retroalimenta PKN, nao altera `PknResult`.
- APB nao foi conectado ao sal.
- Sem acoplamento fisico completo.

**Limite deliberado — estrutural:**
- `PknRunner`, `PknModel`, `CaseParser`, `ResultWriter` e `apps/lot-sim.cpp`
  nao foram alterados.
- `lot-sim run --mode lot-pkn` produz resultados identicos ao estado anterior.
- Nenhum arquivo em `external/saltcreep/`, `legance/`, `legacy/`, `src/lot/`,
  `include/lot/`, `src/apb/`, `include/apb/`, `src/io/`, `include/io/`,
  `tests/baselines/` ou `postprocess/` foi alterado.

**Testes/builds executados:**
- `cmake --build build --config Debug -j`: OK.
- `ctest --test-dir build -C Debug --output-on-failure`
  Resultado: 118/118 Catch2 passaram (era 112 antes da Fase 9.0).
- `ctest -R "lot_salt|coupling|Coupling|salt_coupling"`: 6/6 novos testes.
- `ctest -R "LOT PKN result is identical"`: 1/1 (Fase 8.1 continua passando).

**Validacao manual CLI:**
- `cases/validation/lot_pkn_minimal.yaml`: `validate` OK, `run` OK.
- `cases/validation/lot_pkn_with_leakoff.yaml`: `validate` OK, `run` OK.
- `cases/lot_tese_migrated/buz67d_pkn.yaml`: `validate` OK, `run` OK.
- Saidas geradas em `results/phase9_minimal`, `results/phase9_leakoff`,
  `results/phase9_buz67d`.

---

### [2026-06-04] Auditoria/sync `external/saltcreep` — APB CSV e diagnostico de tensao — Codex

**Status:** Concluido nesta sessao.

**Objetivo:** Revisar as atualizacoes feitas em `external/saltcreep/`, restaurar
a compatibilidade do build integrado com `include/Eigen`, validar os builds
`build_baseline` e `build_lss_eigen`, e confirmar que o `lot-salt-suite`
continua funcional com as novas fontes vendorizadas.

**Mudanca de integracao aplicada:**
- `external/saltcreep/CMakeLists.txt` preserva novamente a opcao
  `LSS_SALTCREEP_FORCE_LSS_EIGEN`, o proxy `lss_eigen_proxy/Eigen`, a macro
  `LSS_SALTCREEP_EIGEN_MODE` e o teste diagnostico `tests/test_eigen_source.cpp`.
- O build MSVC do saltcreep recebeu `/FS` para evitar disputa de escrita de PDB
  durante builds paralelos.
- O `CMakeLists.txt` raiz passou a compilar as novas dependencias vendorizadas
  `TimeDepthTable.cpp` e `StressSampler.cpp`, necessarias para os campos CSV e
  diagnosticos de tensao do `external/saltcreep`.

**Atualizacoes detectadas no saltcreep:**
- Pressao e temperatura de parede por CSV operacional `t,z`.
- Casos APB 1D/2D com historico de lama e temperatura.
- `StressSampler` e saidas `wall_stress.csv`/`stress_profile.csv`.
- Pos-processamento e benchmark dedicados a pressao de parede.
- Diretorio `external/saltcreep/legacy/` adicionado como referencia interna do
  subprojeto vendorizado.

**Testes/builds executados:**
- `cmake -S external\saltcreep -B external\saltcreep\build_baseline -DCMAKE_BUILD_TYPE=Debug -DLSS_SALTCREEP_FORCE_LSS_EIGEN=OFF`
- `cmake --build external\saltcreep\build_baseline --config Debug -j`
- `ctest --test-dir external\saltcreep\build_baseline -C Debug --output-on-failure -j 4`
  passou 133/133 testes.
- `cmake -S external\saltcreep -B external\saltcreep\build_lss_eigen -DCMAKE_BUILD_TYPE=Debug -DLSS_SALTCREEP_FORCE_LSS_EIGEN=ON`
- `cmake --build external\saltcreep\build_lss_eigen --config Debug -j`
- `ctest --test-dir external\saltcreep\build_lss_eigen -C Debug --output-on-failure -j 4`
  passou 133/133 testes.
- `python -m unittest discover -s external\saltcreep\tests\python -p "test_*.py"`
  passou 31/31 testes, com 7 skips esperados.
- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug`
- `cmake --build build --config Debug -j`
- `ctest --test-dir build -C Debug --output-on-failure`
  passou 112/112 testes.
- `ctest --test-dir build -C Debug --output-on-failure -R "SaltCreep|saltcreep|salt|bridge"`
  passou 59/59 testes.
- `ctest --test-dir build -C Debug --output-on-failure -R "Saltcreep backend"`
  passou 4/4 testes controlados do backend.

**Validacao manual CLI:**
- `cases/validation/lot_pkn_minimal.yaml` retornou `OK` em `validate` e `run`.
- `cases/validation/lot_pkn_with_leakoff.yaml` retornou `OK` em `validate` e `run`.
- `cases/lot_tese_migrated/buz67d_pkn.yaml` retornou `OK` em `validate` e `run`.
- Os casos saltcreep `apb_1d_constant_mud.yaml`,
  `apb_1d_schedule_mud_temperature.yaml` e `apb_2d_layered_schedule_Q8.yaml`
  executaram com fechamento final finito.

**Escopo preservado:**
- Nenhum arquivo em `legance/`, `legacy/` raiz, `tests/baselines/`,
  modelos LOT/PKN/APB, parser/writer raiz ou modelos fisicos raiz foi alterado.
- As mudancas em `external/saltcreep/` foram tratadas como dependencia
  vendorizada ativa, com build/testes proprios e registro documental.

---

### [2026-06-04 07:06] `aedace9` — Themisson
**Commit:** `docs(audit): record post-commit audit findings for Fases 8.0-8.1`
**Testes C++:** 19 arquivos | **Testes Python:** 1 arquivos
**Último resultado ctest:** All tests passed (176 assertions in 1 test case)
**Arquivos alterados:**
- `docs/index.html`
- `tools/docs_status.yaml`

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
- `cases/validation/lot_pkn_minimal.yaml` retornou `OK` em `validate` e `run`.
- `cases/validation/lot_pkn_with_leakoff.yaml` retornou `OK` em `validate` e `run`.
- `cases/lot_tese_migrated/buz67d_pkn.yaml` retornou `OK` em `validate` e `run`.
- Saidas manuais geradas em:
  `results\lot_pkn_minimal_substitutability_review`,
  `results\lot_pkn_with_leakoff_substitutability_review` e
  `results\buz67d_pkn_substitutability_review`.

---

### [2026-06-04] Auditoria pos-commit — Fases 8.0 e 8.1 — Claude Code

**Status:** Aprovado com ressalva. Correcoes documentais aplicadas.

**HEAD auditado:** `fada793` (test(salt): prove structural LOT PKN isolation with idle adapter)
**Fase 8.0:** `cb61159` (feat(salt): accept dynamic wall pressure in bridge and adapter)

**Estado verificado:**
- Working tree limpo e sincronizado com `origin/main`.
- 112/112 Catch2 passaram. Tres casos LOT/PKN validaram e rodaram.
- Escopo protegido preservado (sem toque em `external/saltcreep/`, `legance/`, `legacy/`,
  `tests/baselines/`, `postprocess/`, `src/lot`, `include/lot`, `src/apb`, `include/apb`,
  `src/io`, `include/io`).

**Filtro ctest correto para os testes da Fase 8.1:**

```bash
ctest --test-dir build -C Debug --output-on-failure -R "LOT PKN result is identical"
```

O filtro `-R "substitutab"` nao encontra os testes porque os nomes dos test cases
comecam com "LOT PKN result is identical with null salt or idle saltcreep adapter".

**Ressalva — commit intermediario `cb61159` nao compila isoladamente:**

O `CMakeLists.txt` do commit `cb61159` (Fase 8.0) referencia:

```text
tests/cpp/test_lot_pkn_salt_adapter_substitutability.cpp
```

antes desse arquivo existir no repositorio. O arquivo foi criado apenas no commit
seguinte, `fada793` (Fase 8.1). Qualquer checkout ou `git bisect` que landing em
exatamente `cb61159` resultaria em falha de build por arquivo ausente.

Nao e possivel corrigir sem reescrever historico publicado (proibido pela politica
do projeto). Mitigacao para `git bisect`:

```bash
git bisect skip cb61159
```

**Correcoes documentais aplicadas nesta entrada:**
- Caminho de `buz67d_pkn.yaml` corrigido para `cases/lot_tese_migrated/buz67d_pkn.yaml`
  na entrada da Fase 8.1.
- `tools/docs_status.yaml`: `last_updated` atualizado para `2026-06-04`.
- `docs/index.html` regenerado.

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
