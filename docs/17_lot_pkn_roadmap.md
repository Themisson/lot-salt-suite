# 17. Roadmap LOT/PKN

## Decisao de prioridade

A migracao de LOT deve priorizar o caminho PKN observado nos legados antes de
implementar familias de fratura adicionais. O motivo e pratico: o PKN e o
caminho com casos e arquivos de resultado mais diretamente conectados aos LOTs
auditados, especialmente em `legance/LOT_Tese/`.

Os modelos circular, eliptico e penny-shaped permanecem catalogados, mas nao
devem bloquear a primeira implementacao moderna.

## Escopo da primeira entrega LOT/PKN

A primeira implementacao moderna deve criar contratos e testes, nao apenas
transcrever equacoes do legado.

O desenvolvimento tecnico do LOT/PKN segue a politica **C++ first, Python
postprocess only**. Fisica, parser, conversao de unidades, runners, writers,
leakoff, breakdown, dano, acoplamento com sal e integracao com
`external/saltcreep` devem permanecer em C++. Python pode consumir CSV/JSON
modernos para relatorios, graficos, auditorias auxiliares e migracoes pontuais
nao-runtime.

Componentes esperados:

| Componente | Responsabilidade |
|------------|------------------|
| `lot::PknModel` | Calcular abertura, comprimento e volume de fratura PKN com entradas SI. |
| `lot::BreakdownDetector` | Detectar inicio de fratura quando a pressao de parede excede o limite definido pela convencao do projeto. |
| `lot::InjectionSchedule` | Representar taxa de injecao, tempo de simulacao, `dt` e tempo de acomodacao/no-injection. |
| `lot::LeakoffState` | Acumular volume vazado/fraturado e expor serie temporal para APB/coupling. |
| Testes Catch2 | Cobrir unidades, monotonias, ativacao de breakdown e conservacao dimensional basica. |

## Contrato de tempo

O `dt` deve ser coerente com a taxa usada pelo modelo fisico. Se a lei de
deformacao ou fluencia estiver expressa por segundo, o `dt` deve estar em
segundos no solver; se a taxa estiver por minuto ou hora, a conversao deve ser
explicita no parser ou no adapter.

O usuario deve poder definir:

- `dt`;
- politica adaptativa futura, quando implementada;
- tempo total de simulacao;
- tempo de acomodacao, definido como periodo sem incrementos termicos nem
  injecao de fluidos.

No codigo moderno, o parser deve converter unidades de campo para SI antes de
entregar os dados ao solver.

## Caminho de migracao

1. Congelar a interpretacao tecnica do PKN legado em `docs/audits/pkn_legacy_path.md`.
2. Criar tipos de entrada LOT em `include/lot/`, separados de parsing.
3. Implementar `PknModel` com entradas SI e sem acesso direto a YAML/JSON.
4. Implementar `BreakdownDetector` seguindo FA01-FA04 e os riscos registrados.
4.5. Criar `cases/lot_tese_migrated/buz67d_pkn.yaml` com os parâmetros
   extraídos de `legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp` e validar
   contra `schemas/lot_case.schema.yaml` antes de conectar ao CLI.
   Este caso é a ponte entre o contrato numérico e o pipeline YAML→CLI.
4.6. Fase 6.2: criar contrato YAML/C++ LOT/PKN, detector sintético e esqueleto
   minimo de `PknModel` sem regressao contra legado enquanto R09 estiver aberto.
4.7. Fase 6.3: auditar R09. Resultado: `/ M_PI / 22` existe em
   `Conv_bbmin_m3h(idQ == 4)`, mas os PKN auditados usam `idQ == 6`. R09 segue
   aberto para regressao numerica porque o fator nao tem justificativa
   documental e o caminho PKN ainda exige ensaio comparativo controlado.
4.8. Fase 6.4: substituir o esqueleto sintetico por `PknModel` fisico minimo
   em SI, com serie temporal, conservacao dimensional basica e testes Catch2,
   sem regressao contra arquivos legados enquanto R09 permanecer aberto.
4.9. Fase 6.5: conectar `PknModel` ao fluxo moderno de execucao
   `YAML -> CaseParser -> PknInput -> PknModel -> PknResult -> CSV/JSON`, com
   `lot-sim run --mode lot-pkn`, sem declarar regressao contra legado.
4.10. Fase 6.6: executar ensaio analitico controlado de R09. Resultado:
   `/ M_PI / 22` pertence a `Conv_bbmin_m3h(idQ == 4)`, enquanto os dois PKN
   auditados usam `idQ == 6` e `Conv_bbmin_m3min` com `/ M_PI / 2`. R09 fica
   `MITIGATED_FOR_AUDITED_PKN_CASES`, mas segue `BLOCKER_FOR_IDQ4_REGRESSION`
   e nao libera regressao quantitativa legado x moderno.
4.11. Fase 6.7: criar pós-processamento moderno mínimo para `result.json` e
   `timeseries.csv`, gerando PNGs e `report.html` somente a partir dos outputs
   modernos sintéticos. Resultado: relatórios locais em `reports/`, sem
   comparação com legado e com aviso explícito de ausência de regressão.
4.12. Fase 6.9: implementar `LeakoffModel` C++ estruturado com modelos
   `none`, `constant_rate`, `carter` minimo e `synthetic_constant` de
   compatibilidade, integrado ao `PknModel` e coberto por Catch2.
4.13. Fase 6.10: auditar compatibilidade Eigen do `external/saltcreep/` sem
   alterar o solver. Resultado: baseline e build experimental passaram 125/125
   testes Catch2 do saltcreep e casos `lame_test`/`mud_gradient_1d_8p5ppg`, mas
   a migracao real para `include/Eigen` fica como opcao CMake futura.
4.14. Fase 7.1: fixar a convencao LOT-saltcreep antes do adapter real.
   Resultado: pressao de parede compressiva positiva, deslocamento radial
   assinado (`+` para fora, `-` para dentro), fechamento radial positivo
   `radial_closure_m = max(0, -radial_displacement_m)` e documentacao em
   `docs/23_lot_salt_sign_convention.md`.
5. Adicionar testes Catch2 com casos sinteticos e regressao dimensional.
6. Conectar ao CLI apenas depois que o contrato numerico estiver testado e o
   caso YAML (passo 4.5) for reconhecido pelo parser sem erro.
7. Comparar com arquivos legados somente quando o pipeline moderno produzir
   series equivalentes e documentar em `docs/12_validation_results.md`.

## O que foi entregue por fase

**Fase 6.1 (auditoria e governança):**
- Mapeamento do caminho PKN legado em `docs/audits/pkn_legacy_path.md`.
- Catálogo de modelos não PKN em `docs/audits/non_pkn_models_status.md`.
- Política de saltcreep vendorizado ativo em `docs/16_saltcreep_governance.md`.
- Nenhum código C++ novo.

**Fase 6.2 (contrato sintético):**
- `lot::BreakdownDetector` com 5 testes Catch2 sintéticos (vetor SI, erros controlados).
- Esqueleto sintético de `lot::PknModel` com 4 testes (não usa formulação física validada).
- Três casos YAML validados pelo parser: `lot_pkn_minimal.yaml`, `lot_pkn_with_leakoff.yaml`, `buz67d_pkn.yaml`.
- `buz67d_pkn.yaml` é contrato sintático/migratório — NÃO é baseline numérico.
- R09 (`/ M_PI / 22`) permanece blocker para qualquer regressão PKN legado × moderno.

**Fase 6.3 (auditoria R09):**
- Relatorio criado em `docs/audits/R09_pkn_mpi22_audit.md`.
- A expressao suspeita foi localizada em `Conv_bbmin_m3h`, ramo `idQ == 4`.
- Os casos PKN BUZ67D e 9-BUZ-39DA auditados usam `idQ == 6`, que chama
  `Conv_bbmin_m3min` com `/ M_PI / 2`.
- R09 continua aberto para regressao numerica legado x moderno; a proxima etapa
  deve ser ensaio comparativo controlado ou formulacao fisica minima em SI sem
  usar o legado como baseline.

**Fase 6.4 (modelo fisico minimo em SI):**
- `lot::PknModel` agora calcula ponto e serie temporal em SI.
- Entradas fisicas minimas: taxa, `dt`, tempo total, tempo de acomodacao,
  altura, largura inicial, modulo plano, viscosidade e leakoff opcional.
- Saidas: tempo, volume injetado, abertura, comprimento, volume de fratura,
  volume de leakoff e pressao liquida.
- Testes Catch2 cobrem finitude, nao negatividade, monotonicidade basica,
  leakoff simplificado, determinismo e rejeicao de entradas invalidas.
- A validacao CLI dos tres YAMLs `lot-pkn` continua sendo validacao de
  contrato, nao regressao numerica contra legado.

**Fase 6.5 (execucao moderna LOT/PKN):**
- `lot-sim run --case ... --mode lot-pkn --output ...` executa casos YAML
  LOT/PKN modernos.
- `PknRunner` constrói `PknInput` a partir de `CaseData` em SI, escolhendo a
  rocha da camada que contém a sapata e calculando `E' = E/(1 - nu^2)`.
- `ResultWriter` grava `result.json` e `timeseries.csv` com unidades SI.
- `results/` permanece fora do versionamento; fixtures de teste são geradas em
  diretório temporário.
- O status de saída é `synthetic_modern_no_legacy_regression`: não há validação
  contra legado nesta fase.

**Fase 6.6 (ensaio controlado R09):**
- `docs/audits/R09_pkn_conversion_experiment.md` documenta os ramos `idQ == 4`
  e `idQ == 6` e quantifica `/22` versus `/2`.
- `tools/audit_r09_pkn_conversion.py` calcula a tabela analitica sem depender
  de legado e gera `docs/audits/R09_pkn_conversion_table.csv`.
- Para a mesma base `Q * 9.53924`, `/22` produz `1/11` do valor de `/2`.
- Os casos PKN auditados usam `idQ == 6`; portanto, o literal `/22` nao afeta
  diretamente esses dois casos.
- Nao houve validacao numerica legado x moderno e nenhum `.dat` foi usado como
  baseline.

**Fase 6.7 (pós-processamento moderno LOT/PKN):**
- `postprocess/scripts/lot_pkn_report.py` lê `timeseries.csv` e `result.json`.
- São gerados `pressure_vs_time.png`, `pressure_vs_volume.png`,
  `length_vs_time.png`, `width_vs_time.png`, `leakoff_vs_time.png` e
  `report.html`.
- Os relatórios são rotulados como `Modern synthetic LOT/PKN output - no legacy regression`.
- O script valida colunas obrigatórias, arquivos ausentes e valores `NaN`/`Inf`.
- `reports/` permanece fora do versionamento.
- Não houve regressão contra legado; R09 segue mitigado apenas para os PKN
  auditados e ainda bloqueia `idQ == 4`.

**Fase 6.9 (LeakoffModel C++ estruturado):**
- `lot::LeakoffModel` separa o calculo de leakoff do `PknModel`.
- Modelos suportados: `none`, `constant_rate`, `carter` minimo e
  `synthetic_constant` para compatibilidade dos casos existentes.
- O modulo rejeita `dt <= 0`, entradas negativas, `NaN` e `Inf`.
- `PknModel` passa a chamar o modulo e limita o acumulado por `V_inj`.
- Testes Catch2 cobrem o modulo isolado e a integracao PKN; nao houve regressao
  numerica contra legado.

**Fase 6.10 (auditoria Eigen do saltcreep):**
- `docs/audits/saltcreep_eigen_compatibility_audit.md` registra inventario,
  builds, testes e casos executados.
- `docs/20_saltcreep_eigen_migration_plan.md` recomenda manter a migracao para
  `include/Eigen` atras de opcao CMake experimental futura.
- `external/saltcreep/` permaneceu somente leitura; `include/Eigen/` e
  `external/saltcreep/include/Eigen/` foram preservados.
- `ctest` do `saltcreep` passou 125/125 no baseline e 125/125 no build
  experimental; o build experimental ainda resolveu Eigen pela copia
  vendorizada devido a precedencia de include do CMake atual.

**Fase 6.11 (migracao controlada Eigen oficial):**
- `external/saltcreep/CMakeLists.txt` recebeu auto-deteccao de contexto `lot-salt-suite`.
- Quando `../../include/Eigen` existe, `LSS_SALTCREEP_FORCE_LSS_EIGEN` default = `ON` automaticamente.
- Build standalone fora da arvore usa Eigen interno sem quebra (fallback preservado).
- Prova migrada: 126/126 testes Catch2, `closure=0.300817%` no APB, `LSS_SALTCREEP_EIGEN_MODE = lss`.
- Decisao: `MIGRATION_COMPLETED`. Proximo passo: `SaltCreepInterface` / `SaltCreepSaltcreepAdapter`.

**Fase 7.0 (SaltCreepInterface minima e nao acoplada):**
- `include/salt/SaltCreepTypes.hpp` define `WallPressureSample`,
  `SaltCreepQuery` e `SaltCreepResponse` em SI.
- `include/salt/SaltCreepInterface.hpp` define a interface abstrata e
  `NullSaltCreepInterface`.
- `src/salt/SaltCreepInterface.cpp` valida query SI e retorna resposta neutra
  quando a query e valida.
- Testes Catch2 cobrem disponibilidade, resposta neutra e rejeicoes de
  `NaN`, `Inf`, tempo negativo, pressao negativa, temperatura nao positiva e
  posicao radial negativa.
- Nao ha adapter real, chamada para `external/saltcreep` nem acoplamento com
  `PknModel`.

**Fase 7.1 (convencao de sinais LOT-saltcreep):**
- `SaltCreepResponse` passa a expor `radial_closure_m` como magnitude positiva
  de fechamento.
- `docs/23_lot_salt_sign_convention.md` fixa a fronteira: pressao compressiva
  positiva, deslocamento radial assinado e fechamento separado.
- `docs/08_known_issues.md`, `docs/13_coupling_lot_apb_salt.md` e
  `docs/22_saltcreep_interface_contract.md` apontam para o mesmo contrato.
- Nenhum solver, modelo fisico, `src/lot/`, `include/lot/` ou
  `external/saltcreep/` foi alterado.

**Fase 6.10B (prova forcada do Eigen oficial):**
- `external/saltcreep/CMakeLists.txt` recebeu a opcao `LSS_SALTCREEP_FORCE_LSS_EIGEN`.
- Mecanismo: diretorio proxy no build dir com apenas `Eigen/` + `BEFORE PRIVATE`
  no CMake; funciona corretamente com gerador Visual Studio.
- `external/saltcreep/tests/test_eigen_source.cpp` criado para confirmar o modo
  em runtime via macro `LSS_SALTCREEP_EIGEN_MODE`.
- Tres provas objetivas documentadas: CMake status, vcxproj include order, macro runtime.
- Baseline: 126/126 testes (inclui `test_eigen_source`); forcado: pendente ctest completo.
- Caso APB: `closure=0.300817%` em ambos os builds.
- Decisao: `PROVEN_SAFE_TO_MIGRATE` (126/126 testes forcados passaram; APB identico).

## Fora de escopo até R09 ser totalmente resolvido

- Comparação numérica com `legance/LOT_Tese` ou `legance/LOT_APB_v5`.
- Uso de `buz67d_pkn.yaml` como referência de resultado.
- Acoplamento com sal ou APB.

## Proxima fase recomendada

Com R09 mitigado para os dois PKN auditados, mas ainda aberto para `idQ == 4`,
priorizar desenvolvimento C++ nesta ordem:

1. Tornar `PknModel` C++ mais rigoroso, documentando tempo desde breakdown,
   volume, largura e comprimento.
2. Consolidar `BreakdownCriterion` C++ e remover qualquer heuristica solta de
   pos-processamento.
3. Criar `SaltCreepSaltcreepAdapter` C++ usando a convencao da Fase 7.1 para
   integrar `external/saltcreep` sem script Python intermediario.
4. Se o adapter exigir unificacao de Eigen, adicionar opcao CMake experimental
   no `saltcreep` e repetir a auditoria 6.10 com prova de include order.
5. Implementar acoplamento LOT/sal em C++ e só depois ampliar
   pos-processamento ou comparacao externa.

Antes de qualquer comparacao legado x moderno, confirmar o `idQ` de
   geracao dos `.dat` e manter qualquer resultado como qualitativo ate resolver
   os demais pontos PKN (`t` absoluto, `time` desde breakdown, `w0 * L1 * M_PI`).
Para liberar regressao quantitativa envolvendo `idQ == 4`, obter justificativa
fisica/documental para `22` ou excluir esse ramo como referencia valida.

## Riscos tecnicos a resolver antes da implementacao

- O legado usa conversoes de vazao com fatores geometricos embutidos e ao menos
  uma expressao suspeita (`/ M_PI / 22`) que deve ser auditada antes de servir
  como referencia numerica.
- O tempo de fratura mistura `t` absoluto e tempo desde breakdown em trechos do
  legado; o modelo moderno deve escolher uma unica convencao.
- O volume PKN legado usa uma forma simplificada (`w0 * L1 * pi`) e mantem uma
  alternativa comentada; a escolha precisa ser documentada antes de validar.
- A convencao de tensao circunferencial deve respeitar FA01-FA04 e nao pode ser
  reinterpretada sem registro em `docs/08_known_issues.md`.
