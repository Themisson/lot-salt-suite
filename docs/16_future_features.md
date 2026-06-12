# 16 — Planejamento de funcionalidades futuras

**Status:** Planejamento técnico  
**Escopo:** funcionalidades futuras que ainda não devem entrar no runtime  
**Restrição:** este documento não autoriza validação física nem alteração de
formulações sem fase própria.

---

## Fase 10.17C — acomodação, shut-in e fluido Zamora

**Status:** `PLANNED_NO_RUNTIME_CHANGE`.

A Fase 10.17C registra o plano para três evoluções que ficaram fora do modo
opcional `volumetric_balance` da Fase 10.17B:

1. agenda operacional com acomodação antes da injeção;
2. fase de shut-in/no-injection após a injeção;
3. modelo de fluido Zamora ou equivalente moderno.

Nenhum desses itens foi implementado nesta fase.

### Acomodação operacional

O legado `LOT_Tese` separa `tac` e `t_no_injection`:

```text
tac            -> acomodação térmica/mecânica antes do carregamento operacional
t_no_injection -> extensão temporal após o fim da injeção LOT
```

No moderno atual, `lot.injection.schedule.accommodation_time` já reduz o tempo
ativo usado pelo `PknModel`, mas ainda não existe uma estrutura explícita de
fases operacionais. A evolução recomendada é criar uma agenda declarativa:

```yaml
lot:
  operation_schedule:
    phases:
      - type: accommodation
        duration: {value: 9.5, unit: min}
      - type: injection
        duration: {value: 12.5, unit: min}
        rate: {value: 0.5, unit: bbl_min}
      - type: shutin
        duration: {value: 9.5, unit: min}
```

Essa agenda deve ser parseada para SI no `CaseParser`, mas não deve ser
conectada automaticamente ao acoplamento sal/APB antes de testes dedicados.

### Shut-in / no-injection

**Status:** implementado de forma opt-in para LOT/PKN na Fase 10.18B.

O legado mantém `Vq = flowRate(tend)` após o fim da injeção quando `t > tend`,
prolongando a simulação com o volume injetado final. Isso não é equivalente a
continuar bombeando: é uma fase de volume imposto constante.

A Fase 10.18A não implementa shut-in. Ela apenas confirma, por diagnóstico
visual, que o modo moderno `volumetric_balance` se aproxima mais da escala de
`pw_Pa` legado do que `pkn_direct` no caso controlado BUZ67D. A diferença
temporal remanescente permanece esperada porque o legado auditado inclui uma
cauda sem injeção até `1320 s`, enquanto o run moderno controlado cobre
`0..750 s`.

Contrato futuro recomendado:

```text
injection phase:
  dV_injected/dt = Q

shutin phase:
  dV_injected/dt = 0
  V_injected = V_injected_at_end_of_injection
```

Para o modo `volumetric_balance`, a fase shut-in altera pressão somente por
termos explicitamente disponíveis no modelo moderno. Na implementação 10.18B,
`Q=0` implica volume injetado constante; sem leakoff/fratura/fechamento ativo,
a pressão permanece constante. Com leakoff ativo, o incremento efetivo pode ser
negativo e a pressão pode declinar. APB, sal, casing elástico e Zamora ainda
não foram conectados a esse ciclo.

### Fluido Zamora

O ramo `legance/LOT_APB_v5` contém uma implementação extensa de correlações
Zamora em:

```text
legance/LOT_APB_v5/include/apb_code/Fluids.h
legance/LOT_APB_v5/src/apb_code/Fluids.cpp
```

Funções e estruturas relevantes observadas em modo read-only:

```text
Zamora
Zamora_Coefficients
setZamora(...)
setZamoraCoefficients(...)
setZamoraPVTinit(...)
setHidrostaticPVTinit(...)
setZamoraKt(...)
setZamoraAlpha(...)
attZamoraPVT(...)
attZamoraKt(...)
attZamoraAlpha(...)
getZamoraRho(...)
getZamoraPressure(...)
getZamoraKt(...)
getZamoraAlpha(...)
getZamoraRhoAtDepth(...)
getZamoraPressureAtDepth(...)
getZamoraKtAtDepth(...)
getZamoraAlphaAtDepth(...)
```

O uso em `APB1da.cpp` atualiza densidade, compressibilidade e expansão térmica
por profundidade/temperatura/pressão durante a solução APB. Essa lógica não
deve ser copiada diretamente para `src/`; a política do projeto exige criar um
contrato moderno próprio.

### API futura recomendada

Criar futuramente um módulo `fluids/` C++ com uma interface pequena:

```cpp
struct FluidStateInput {
  double pressure_Pa = 0.0;
  double temperature_K = 0.0;
  double depth_m = 0.0;
};

struct FluidState {
  double density_kg_m3 = 0.0;
  double compressibility_per_Pa = 0.0;
  double thermal_expansion_per_K = 0.0;
  double viscosity_Pa_s = 0.0;
};

class FluidModel {
 public:
  virtual ~FluidModel() = default;
  virtual FluidState evaluate(const FluidStateInput& input) const = 0;
};
```

Uma implementação futura `ZamoraFluidModel` deve:

- receber coeficientes declarados em YAML;
- converter todas as unidades no parser;
- expor densidade, compressibilidade e expansão térmica em SI;
- ter testes C++ com casos analíticos/fixture pequenos;
- não depender de headers `legance/` ou de código legado;
- não virar default sem fase de validação.

### YAML futuro recomendado

Exemplo conceitual:

```yaml
fluids:
  - id: lot_fluid
    mode: zamora
    viscosity_cP: 3.0
    zamora:
      reference_pressure: {value: 1.0, unit: atm}
      reference_temperature: {value: 60.0, unit: degF}
      coefficients:
        a1: 0.0
        b1: 0.0
        c1: 0.0
        a2: 0.0
        b2: 0.0
        c2: 0.0
```

Esse formato é apenas proposta. A fase de implementação deve auditar as
unidades reais usadas no `LOT_APB_v5` antes de aceitar nomes ou dimensões.

### Ordem recomendada

1. Manter o diagnóstico 10.18C como rota de sink volumétrico por threshold
   simplificado, sem declará-lo equivalente ao critério legado.
2. Criar uma fase de arquitetura opt-in para fornecer
   `SigmaThetaInfluenceLayer` ao balanço volumétrico sem fazer `lot/` depender
   diretamente de `salt/` ou `coupling/`.
3. Só depois reavaliar o critério legado
   `|pi + dP| > |sigma_tangencial(altura_de_influencia)|` como rota runtime
   experimental. O gate atual da Fase 10.18D é
   `SIGMA_THETA_AVAILABLE_DIAGNOSTIC_ONLY`.
4. Auditar a semântica de `dP` legado após abertura/leakoff.
5. Criar `FluidModel` abstrato e `ConstantFluidModel` compatível com o estado atual.
6. Auditar especificamente as unidades Zamora no `LOT_APB_v5`.
7. Implementar `ZamoraFluidModel` experimental, opt-in e sem alterar defaults.

### Riscos

- `tac` legado pode representar acomodação termo-mecânica, não apenas atraso de
  injeção.
- `t_no_injection` representa volume final constante, não vazão residual.
- Zamora no legado mistura pressão, temperatura, profundidade e unidades
  históricas; copiar fórmula sem normalização pode criar erro dimensional.
- Conectar shut-in ao balanço sem sal/APB pode produzir falsa sensação de
  validação.
- A pressão inicial absoluta ainda precisa de contrato próprio antes de comparar
  `pw` legado com `wellbore_pressure_Pa` moderno.
- O critério legado por tensão tangencial não está reproduzido no `PknModel`;
  usar `fracture.breakdown.pressure` como proxy pode antecipar ou atrasar
  artificialmente o desconto de volume de fratura.
- `sigma_theta_compression_positive_Pa` existe no diagnóstico moderno, mas
  ainda não é fonte runtime para `lot-sim run --mode lot-pkn`.
- A Fase 10.18E confirmou que calibrar `fracture.breakdown.pressure` com o
  `dP` legado em `Momento da quebra = 8.5 min` ainda abre a rota moderna cedo
  demais (`30 s` contra `510 s`). Portanto, fases futuras não devem insistir
  apenas em ajuste escalar do threshold; o caminho recomendado é uma rota
  opt-in que forneça `SigmaThetaInfluenceLayer`/altura de influência ao balanço
  volumétrico, mantendo `lot-sim run --mode lot-pkn` desacoplado por default.
- A Fase 10.19A criou o contrato opt-in `sigma_theta_static`, mas o proxy
  escalar ainda abriu cedo demais. A próxima evolução deve trocar o valor
  estático por um provider runtime explícito, por uma rota como:

```text
CaseData -> SaltCreepTimeBridge -> SaltWallStressDiagnostics
         -> SigmaThetaInfluenceLayer -> volumetric_balance
```

  Essa rota futura deve continuar opt-in, sem tornar sal/sigma-theta default
  para `lot-sim run --mode lot-pkn`.
- A Fase 10.19B auditou a hipótese de erro de vazão e classificou a convenção
  como `FLOWRATE_CONVENTION_MATCHES_LEGACY`. O salto moderno de primeiro passo
  é compatível com compressão pura do fluido, enquanto o legado inclui o termo
  geométrico `dV` no balanço. Antes de avançar para sigma-theta runtime como
  validação física, deve existir uma fase opt-in para `annular_compliance` ou
  `wellbore_compliance`, sem fator empírico.
- A Fase 10.19C implementou uma compliance geométrica constante e opt-in no
  `volumetric_balance`. O resultado foi classificado como
  `COMPLIANCE_EFFECTIVE` para o caso BUZ67D controlado porque reproduziu a
  escala do primeiro `dP` e aproximou a faixa maxima de pressao. Ainda assim,
  o valor foi inferido de um unico passo legado e permanece
  `GEOMETRIC_COMPLIANCE_DIAGNOSTIC_ONLY`. Fases futuras devem substituir esse
  equivalente constante por um modelo mecanico explícito de deformabilidade do
  anular/revestimento/formacao, mantendo o default sem compliance.
- A Fase 10.20A formulou o candidato `elastic_annular_simple`. O gate ficou
  `MECHANICAL_COMPLIANCE_FORMULATION_PARTIAL`, porque a estimativa elastica
  simples e testavel, mas produz apenas cerca de `0.93%` da compliance
  diagnostica inferida na 10.19C. A proxima implementacao pode prosseguir como
  rota experimental/opt-in, com expectativa de diagnosticar se o modelo e
  subcompliant em BUZ67D antes de adicionar calibracoes ou modelos mais ricos.
- A Fase 10.20B implementou `elastic_annular_simple`. O proximo passo deve ser
  diagnosticar BUZ67D contra legado/sem compliance/`constant_geometric`, sem
  calibrar silenciosamente o modelo. Se o resultado for subcompliant, a
  evolucao correta e formular um modelo mecanico mais completo ou uma
  calibracao opt-in explicita, nao esconder um fator empirico no solver.
- A Fase 10.20C confirmou `ELASTIC_COMPLIANCE_UNDERCOMPLIANT` para BUZ67D. O
  primeiro `dP` elastico simples foi `43.64 MPa`, contra `1.845 MPa` no legado
  e no proxy `constant_geometric`. O modelo deve permanecer experimental; fase
  futura deve tratar casing/formacao/sal de modo mais completo ou criar
  calibracao opt-in declarada.
- A Fase 10.21A extraiu uma compliance aparente reduzida do trace auditado e
  classificou a serie como `APPARENT_COMPLIANCE_PRESSURE_DEPENDENT`. A media
  pre-abertura ficou acima do proxy constante da 10.19C, enquanto o primeiro
  passo coincide com ele. Uma fase futura deve avaliar `tabulated_pressure`,
  `pressure_dependent` ou `elastic_scaled` opt-in, idealmente depois de exportar
  `dV_geom`, `dMl`, `dV_leakoff` e `k` diretamente do legado.
- O adendo termico da 10.21B bloqueia a implementacao imediata de
  `pressure_tabulated_geometric` a partir da serie bruta. Embora
  `k_legacy = C_fluid_modern = 6.4e-10 1/Pa`, o termo `alpha*dT` e dominante
  no layer 16 pre-abertura (`mean_thermal_fraction ~= 0.867`,
  `max_abs_thermal_fraction ~= 1.526`). A proxima evolucao deve produzir uma
  serie corrigida por termo termico ou reinstrumentar temporariamente o legado
  para exportar `dT`, `alpha`, `k`, `dV_geom`, `dMl` e `dV_leakoff` no mesmo
  trace.
- A Fase 10.21C produziu essa primeira serie corrigida por perfil termico, mas
  nao liberou `pressure_tabulated_geometric`. A correcao principal
  `dP_mech = dP - alpha*dT/k` ficou
  `THERMAL_CORRECTED_COMPLIANCE_SIGN_AMBIGUOUS`, com quatro pontos
  pre-abertura de pressao mecanica negativa e um incremento mecanico nao
  positivo. O gate futuro permanece:
  `PRESSURE_TABULATED_STILL_BLOCKED_MISSING_BALANCE_TERMS` e
  `PRESSURE_TABULATED_STILL_BLOCKED_SIGN_CONVENTION_AMBIGUOUS`. Uma evolucao
  futura deve instrumentar ou extrair `dV_geom`, `dMl`, `dV_leakoff`, `k`,
  `dT` e `opened` no mesmo trace antes de qualquer tabela de compliance.
- A Fase 10.22A confirmou diretamente a algebra ativa do balanco PKN legado:
  `dP = alpha*dT/k + (Vq - dV + dMl/(rho_f2*FC))/(Vi*k)`. A reconstrução
  termo-a-termo bateu com `dP` com residual maximo `1.86e-9 Pa`, mas a rota
  `pressure_tabulated_geometric` ainda deve permanecer bloqueada. O trace
  continua parcial: `opened`, `sigmaTheta`, `margin` e o estado antes/depois da
  abertura nao foram exportados no mesmo registro. A proxima evolucao deve ser
  uma fase de analise/instrumentacao adicional ou uma tentativa diagnostica
  claramente opt-in usando a compliance termo-a-termo, nunca default runtime.
- A Fase 10.22B tentou essa extracao diagnostica de compliance geometrica
  direta. A serie acumulada pre-abertura teve media `4.44e-10 1/Pa`, apenas
  `2.39%` do proxy `constant_geometric` da 10.19C, e CV `0.95`. A serie
  incremental teve media negativa (`-3.85e-8 1/Pa`) e CV `3.28`. Ambas foram
  classificadas como `TERMWISE_GEOM_COMPLIANCE_NOISY`, com dependencia de fase.
  Assim, `pressure_tabulated_geometric` segue bloqueado ate existir trace
  complementar com `opened/sigmaTheta/margin` no mesmo registro.
- A Fase 10.22C produziu esse trace complementar de forma temporaria e
  read-only sobre `LOT_Tese`, confirmando `opened` em `510 s`, primeiro sink
  positivo em `540 s` e `sink_delay_s = 30 s`. A classificacao
  `PHASE_DEPENDENCE_EXPLAINED_BY_SINK` melhora a evidencia para uma fase de
  formulacao, mas ainda nao libera runtime: uma evolucao futura deve decidir se
  a informacao vira apenas diagnostico, uma tabela opt-in controlada ou um
  modelo mecanico de acomodacao/sink mais explicito.
- A Fase 10.23B combinou `constant_geometric`, `sigma_theta_static` fixo da
  10.22C e `sink_timing: next_step`. O resultado
  `COMBINED_DIAGNOSTIC_PRESSURE_OK_OPENING_SHIFTED` mostra que o pico de
  pressao e o atraso de sink estao adequados para diagnostico, mas a abertura
  moderna ainda ocorre tarde (`660 s` contra `510 s`). A proxima evolucao deve
  ser uma fase de decisao: priorizar sigma-theta runtime, compliance dependente
  de fase ou manter `constant_geometric` apenas como diagnostico suficiente para
  comparar outros pocos. `pressure_tabulated_geometric` continua bloqueado.
- A Fase 10.23C tomou essa decisao: `NEXT_MODEL_SIGMA_THETA_RUNTIME`. O motivo e
  que a combinacao 10.23B ja preserva escala de pressao e `sink_delay_s = 30 s`,
  mas ainda desloca o instante de abertura. Assim, a proxima evolucao deve focar
  em uma rota opt-in para sigma-theta runtime ou criterio de abertura mais fiel.
  `pressure_tabulated_geometric` permanece bloqueado e `constant_geometric`
  continua apenas diagnostico.
- A Fase 10.24A implementou o primeiro contrato arquitetural dessa rota:
  `SigmaThetaProvider` em `lot/`. Ele permite que o `PknModel` consulte
  `sigma_theta_compression_positive_Pa` de uma fonte runtime opt-in, sem incluir
  `saltcreep`, `SaltCreepTimeBridge` ou `SaltWallStressDiagnostics`.
- A Fase 10.24B implementou o provider diagnostico `sigma_theta_time_series`
  por YAML, com interpolacao linear e clamp. Essa rota ainda e fixture minima
  de wiring e nao substitui uma fonte fisica real. As fases futuras devem
  avaliar se `SaltWallStressDiagnostics` pode ser a fonte runtime fisicamente
  controlada. O default de `lot-sim run --mode lot-pkn` permanece inalterado.
- A Fase 10.24C diagnosticou o caso BUZ67D combinado e classificou a rota como
  `SIGMA_THETA_TIMESERIES_PRESSURE_OK_OPENING_SHIFTED`. A pressao maxima, a
  pressao na abertura, o shut-in final e o atraso de sink ficaram bons em escala
  diagnostica, mas a abertura moderna ainda ocorreu em `660 s` contra `510 s`
  no legado. A proxima fase deve melhorar/auditar a fonte temporal de
  sigma-theta antes de promover `SaltWallStressDiagnostics` como provider
  runtime.
- A Fase 10.25A extraiu uma serie refinada de `sigmaTheta` diretamente do
  ponto do criterio legado `pw > sigmaTheta`. A serie refinada tem `44` pontos,
  cobre `30..1320 s`, confirma abertura em `510 s` e sink em `540 s`, e mostra
  que a fixture 10.24B era esparsa: em `660 s`, o refinado tem
  `65445500 Pa`, contra `66666600 Pa` no YAML anterior. O gate
  `SIGMA_THETA_REFINED_PROVIDER_UPDATE_ALLOWED` permite criar um novo caso
  diagnostico opt-in com essa serie. Ainda assim, isso nao valida fratura fisica
  nem promove `SaltWallStressDiagnostics` runtime; apenas melhora a fonte
  temporal diagnostica antes da decisao seguinte.
- A Fase 10.25B criou o caso opt-in
  `cases/validation/buz67d_pkn_legacy_sigma_theta_refined_timeseries.yaml`
  com os 44 pontos refinados. O diagnostico permaneceu
  `SIGMA_THETA_REFINED_TIMESERIES_PRESSURE_OK_OPENING_SHIFTED`: pressao maxima,
  pressao na abertura, pressao final e sink delay continuam bons, mas a abertura
  moderna segue em `660 s` contra `510 s` no legado. A proxima decisao deve
  priorizar auditoria de `pressure_source`/timing ou mapeamento temporal antes
  de promover uma fonte runtime real de `SaltWallStressDiagnostics`.
- A Fase 10.25C comparou 10.24C contra 10.25B e decidiu
  `NEXT_MODEL_PRESSURE_SOURCE_TIMING_REVIEW`. Como a serie refinada nao alterou
  o erro de abertura (`+150 s`), a proxima implementacao/auditoria deve focar a
  amostragem e uso de `wellbore_pressure_before_step_Pa`,
  `wellbore_pressure_trial_Pa` e `wellbore_pressure_after_step_Pa` no criterio
  moderno antes de conectar fonte runtime real de tensao de sal.
- A Fase 10.26A auditou os campos exportados e, no adendo geometrico, bloqueou
  uma correcao prematura de `pressure_source`/timing. A evidencia bruta ainda
  mostra `MISSING_PRESSURE_TRACE_FIELDS` e melhor candidato abrindo em `600 s`
  (`+90 s`), mas o gate final e
  `LEGACY_EQUIVALENCE_REQUIRES_MESH_MATCHING`: o `APBSalt1D` legado usa
  `outer_radius_m = 8 m`, `nelem = 15`, `ratio = 10`, `integration_order = 3`
  e amostra `mdl->getElem(0)->getSigmaTheta()`, enquanto a rota moderna
  diagnostica/bridge usa defaults de dominio e refinamento diferentes. A proxima
  fase deve primeiro reproduzir uma configuracao APBSalt1D equivalente no
  moderno; so depois disso a auditoria de `before/trial/after` e timing deve ser
  retomada.
- A Fase 10.26B criou essa rota como contrato opt-in inicial:
  `sigma_theta_runtime_geometry` declara `outer_radius_m = 8 m`,
  `radial_elements = 15`, `ratio = 10`, `integration_order = 3` e
  `sampling = legacy_elem0_sig_2_0`. Nesta fase, porem, o status permanece
  `APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED`: a configuracao e validada e
  rastreavel, mas ainda nao alimenta um provider runtime real. Uma fase futura
  deve consumir essa geometria em `SaltWallStressDiagnostics`/bridge opt-in ou
  documentar formalmente que a malha moderna refinada nao busca equivalencia
  com o legado.
- A Fase 10.26C decidiu formalmente
  `APBSALT1D_METADATA_ONLY_CONFIRMED` e
  `NEXT_PHASE_IMPLEMENT_SAMPLING_BRIDGE`. O moderno ja tem malha radial L3,
  `outer_radius_m`, `radial_elements` e diagnostico de tensao de parede, mas
  ainda falta consumir `ratio = 10`, expor a amostragem
  `legacy_elem0_sig_2_0` e ligar essa amostra a um `SigmaThetaProvider` opt-in.
  `pressure_source`/timing segue bloqueado ate que a geometria seja consumida
  ou rejeitada explicitamente.
- A Fase 10.26D tentou o primeiro gate de sampling bridge e confirmou
  `APBSALT1D_SAMPLING_BRIDGE_METADATA_ONLY`. A rota atual
  `sigma_theta_time_series` nao possui amostras espaciais, raio de amostra,
  elemento ou ponto de Gauss; portanto `legacy_elem0_sig_2_0` nao pode ser
  consumido sem uma fonte espacial real. A proxima fase deve implementar um
  provider/sampler opt-in baseado em amostras de parede, ou documentar
  formalmente que a equivalencia APBSalt1D nao sera perseguida. Ajustes de
  `pressure_source`/timing continuam bloqueados ate essa decisao.
- A Fase 10.27A registrou a decisao estrategica entre `legacy-equivalence mode`
  e `modern-refined mode`. Abertura em `510 s` so deve ser exigida quando o
  objetivo for regressao estrita contra o `LOT_Tese` e a geometria APBSalt1D
  for consumida de forma real. Em `modern-refined mode`, abertura em `660 s`
  pode ser uma divergencia aceitavel de malha/dominio/amostragem, nao erro
  automatico. O gate novo e
  `LEGACY_EQUIVALENCE_VS_MODERN_REFINED_DECISION_RECORDED`.
- A Fase 10.27B consolidou o BUZ-67D como pacote `modern-refined`: pressao e
  sink delay sustentam o diagnostico, enquanto abertura em `660 s` permanece
  diferenca documentada e nao regressao estrita. A proxima evolucao deve
  validar/sensibilizar o modo moderno em mais casos ou preparar graficos de
  publicacao antes de qualquer tentativa de solver APBSalt1D equivalente.
- A Fase 10.27C registrou o roadmap pos-10.27 em
  `docs/32_post_10_27_roadmap.md`. A proxima fase recomendada e `10.28A`,
  consolidando `modern-refined mode` em casos adicionais, seguida por
  sensibilidade de malha/dominio/sampling (`10.28B`) e graficos de publicacao
  (`10.28C`). A rota `legacy-equivalence` com solver APBSalt1D fica opcional e
  condicionada a necessidade explicita de regressao estrita.
- A Fase 10.28A criou o pacote de planejamento
  `docs/33_phase10_28a_modern_refined_validation_package.md`. O gate novo e
  `ADDITIONAL_WELLS_OR_SENSITIVITY_MATRIX`: usar casos/poços adicionais apenas
  com dados completos; caso contrario, executar matriz de sensibilidade
  BUZ-67D sem transformar divergencias temporais ou numericas em erro
  automatico.
- A Fase 10.28B aplicou esse gate. BUZ-29D foi encontrado no legado, mas nao
  como caso PKN moderno pronto: fontes principais usam modelos alternativos ou
  precisam de auditoria adicional, e saidas PKN nao bastam para criar YAML sem
  inventar parametros. A rota escolhida para 10.28C e
  `ADDITIONAL_WELL_BLOCKED_SENSITIVITY_SELECTED`, com matriz BUZ-67D
  `modern-refined` S0-S3.
- A Fase 10.28C executou a matriz S0-S3. O resultado
  `PHASE10_28C_SENSITIVITY_MATRIX_RUN_OK` mostra sensibilidade relevante a
  `constant_geometric`: `0.75x` aproximou a abertura de `510 s`, `1.25x` nao
  abriu na janela e `same_step` removeu o atraso de sink. Esse achado deve
  orientar novas sensibilidades ou auditoria de compliance, mas nao autoriza
  calibracao automatica nem mistura com `legacy-equivalence`.
- A Fase 10.29A refinou essa sensibilidade em `0.60x..1.00x`. O melhor fator
  por abertura e score combinado foi `0.75x`; o melhor fator por pressao maxima
  isolada foi `0.60x`. A conclusao tecnica e que a abertura modern-refined e
  fortemente controlada por `constant_geometric`, ainda como diagnostico.
- A Fase 10.29B criou `tools/run_lot_pkn_sensitivity_matrix.py` como
  infraestrutura generica para matrizes LOT/PKN. A ferramenta valida/roda casos
  declarados em YAML e sumariza `timeseries.csv`, mas permanece pos-processo de
  diagnostico em `tools/`: nao muda runtime C++, nao cria modelo fisico novo e
  nao transforma sensibilidade em calibracao automatica.
- A Fase 10.29C auditou BUZ-29D e manteve
  `BUZ29D_MODERN_YAML_NOT_READY`. Existem fontes e saidas BUZ-29D, inclusive
  saidas PKN, mas os fontes ativos auditados sao `penny-shaped`, `circular` ou
  ambiguos. Uma fase futura deve auditar a proveniencia das saidas PKN ou
  planejar suporte KGD/penny-shaped antes de criar YAML moderno.
- A Fase 10.30A criou uma matriz YAML versionada para a sensibilidade BUZ-67D
  `modern-refined`: `buz67d_modern_refined_cgeom_matrix.yaml`. Essa matriz
  deve ser a entrada preferencial para reproducao local da sensibilidade por
  `tools/run_lot_pkn_sensitivity_matrix.py`. Ela nao altera solver nem promove
  fator de compliance a calibracao automatica.
- A Fase 10.30B executou essa matriz versionada e adicionou verificacao de
  `summary.csv`/`metadata.json` por
  `tools/verify_phase10_30b_sensitivity_run.py`. A classificacao
  `VERSIONED_SENSITIVITY_RUN_OK` confirma reprodutibilidade operacional da
  matriz, nao calibracao fisica.
- A Fase 10.30C criou `tools/report_lot_pkn_sensitivity_matrix.py` para gerar
  relatorios JSON/Markdown reproduziveis a partir de `summary.csv` e
  `metadata.json`. O ranking de fatores e diagnostico e nao deve ser usado como
  calibracao automatica.
- A Fase 10.31A criou `tools/run_buz67d_modern_refined_package.py` e
  `docs/42_buz67d_modern_refined_reproducible_package.md`, consolidando o fluxo
  end-to-end BUZ-67D `modern-refined` para outro computador/agente. O pacote
  continua diagnostico e grava artefatos apenas em `results/`.
- A Fase 10.31B fecha formalmente a Etapa 10 com
  `PHASE10_CLOSED_READY_FOR_STAGE11` e recomenda a Etapa 11 como
  `STAGE11_PARAMETRIC_INFRASTRUCTURE`. O foco futuro deve ser infraestrutura
  paramétrica, índices de estudos e relatórios multi-estudo, sem promover
  sensibilidade diagnóstica a calibração física.
- A Fase 11.1A registra o plano técnico da Etapa 11 em
  `docs/44_stage11_parametric_infrastructure_plan.md`. A primeira implementação
  recomendada é `STAGE11_1B_MULTI_STUDY_MATRIX_INDEX`, mantendo solver e casos
  protegidos inalterados.
- A Fase 11.1B adiciona `cases/validation/sensitivity/studies_index.yaml` e
  `tools/list_lot_pkn_sensitivity_studies.py`, registrando
  `buz67d_cgeom_sensitivity` como primeiro estudo ativo. O runner permanece
  inalterado e continua recebendo matrizes por caminho explícito.
- A Fase 11.2A especifica o contrato `schema_version: 2` para matrizes
  paramétricas `base_case + overrides`, com validador dedicado em
  `tools/validate_lot_pkn_parametric_matrix.py`. A geração materializada e a
  integração com o runner ficam planejadas para 11.2B/11.2C; casos derivados
  devem permanecer em `results/` até promoção manual.
- A Fase 11.2B adiciona `tools/materialize_lot_pkn_parametric_matrix.py` para
  gerar YAMLs derivados de matrizes v2 em `results/` ou diretório temporário.
  O materializador é utilitário de validação/diagnóstico, não pré-processador
  obrigatório do runtime, e não promove casos automaticamente para
  `cases/validation/`.
- A Fase 11.2C integra matrizes v2 ao runner genérico. O runner materializa
  cenários em `<output-dir>/materialized_cases/`, registra
  `materialized_case_path` em summary/metadata e preserva compatibilidade com
  matrizes v1. A variante `buz67d_cgeom_sensitivity_v2` fica registrada no
  índice de estudos.
- A Fase 11.3A executa a matriz v2 BUZ-67D e confirma
  `V2_REPRODUCES_V1_DIAGNOSTICS` para os cenários selecionados. Os YAMLs
  materializados continuam artefatos locais em `results/`, não casos
  versionados.
- A Fase 11.3B adiciona execução por `study_id` com
  `tools/run_lot_pkn_sensitivity_study.py`. O estudo
  `buz67d_cgeom_sensitivity_v2` passa a ser executável a partir do índice sem
  informar manualmente o caminho da matriz. O wrapper delega ao runner genérico
  e mantém `results/` fora do Git.
- A Fase 11.3C adiciona `tools/run_lot_pkn_study.py` como comando canônico de
  estudo. Ele resolve `study_id`, chama a execução por estudo, gera relatório
  quando há outputs reais e escreve `study_manifest.json`/`run_commands.txt` em
  `results/`.
- A Fase 11.4A define `study_manifest.json` `schema_version: 1` e adiciona
  provenance operacional completa aos estudos LOT/PKN: Git, ambiente Python,
  plataforma, executável `lot-sim`, matriz, `base_case`, outputs, cenários e
  comandos de reprodução.
- A Fase 11.4B adiciona verificação formal de diretórios de resultado por
  `tools/verify_lot_pkn_study_results.py`, cobrindo manifesto v1, outputs,
  resumo, metadados, relatórios opcionais e cenários.
- A Fase 11.5A amplia a sensibilidade BUZ-67D `modern-refined` de `C_geom` com
  matriz v2 e execução por `study_id`, mantendo a interpretação como
  diagnóstico e não calibração física.
- A Fase 11.5B adiciona a matriz cruzada BUZ-67D `C_geom x sink_timing` por
  `study_id`. Ela separa efeitos de compliance e temporização do sink, confirma
  o atraso operacional de 30 s para `next_step` nos pares com abertura e mantém
  a classificação como diagnóstico, não calibração física.
- A Fase 11.5C consolida os estudos BUZ-67D 11.5A/11.5B em um relatório
  interpretativo. O bloco fecha com `C_geom=0.75x` como melhor ranking
  diagnóstico combinado, `C_geom=0.55x` como melhor ranking por pressão máxima
  e transição recomendada para auditoria BUZ29-VISCO-first-well.
- A Fase 11.6A auditou `BUZ29-VISCO-first-well.cpp` e confirmou que o caso
  existe, mas não está pronto para YAML moderno LOT/PKN: o modelo ativo é
  `penny-shaped` e a linha PKN está comentada. A próxima evolução deve ser um
  roadmap não-PKN, cobrindo penny-shaped/KGD/Zamora como escopo futuro separado
  da infraestrutura BUZ-67D modern-refined.
- A Fase 11.6B registra esse roadmap não-PKN: priorizar auditoria de formulação
  `penny-shaped`, manter KGD/circular/elliptical como rota opcional, bloquear
  Zamora/compositional fluid até gate próprio e auditar proveniência dos outputs
  PKN antes de usá-los como referência.
- A Fase 11.5D adiciona máximos de fratura, leakoff, comprimento, abertura e
  pressão líquida aos summaries de estudos LOT/PKN. A mudança é Python-only e
  usa colunas já exportadas pelo runtime moderno; não altera formulação física.
- A Fase 11.7A decide a primeira trilha não-PKN pós-BUZ29:
  `PENNY_SHAPED`. A decisão é documental e técnica; não implementa modelo novo,
  não cria YAML BUZ29 e não declara validação física. A próxima etapa segura é
  auditar matematicamente a formulação penny-shaped antes de qualquer solver.
- A Fase 11.7B audita a matemática penny-shaped legada e extrai relações
  mínimas para `w0`, `R`, `pressureFactor` e volume proxy. O status permite
  especificação YAML/IO e eventual núcleo C++ isolado, mas continua bloqueando
  validação BUZ29 e equivalência com o legado completo.
- A Fase 11.7C especifica o YAML/IO mínimo do modelo `penny_shaped` em uma
  fixture versionada, com validador Python e status
  `SPEC_FIXTURE_ONLY_NOT_RUNTIME_SCHEMA`. Isso prepara a 11.8A sem alterar
  parser, schema oficial, runtime ou casos protegidos.
- A Fase 11.8A adiciona o núcleo C++ isolado `lot::PennyShapedModel`, com
  testes Catch2 para as fórmulas auditadas. O código não é conectado ao CLI,
  parser, `PknRunner`, `PknModel` ou BUZ29; permanece base diagnóstica para
  decisão futura de integração.
- A Fase 11.8B seleciona `PENNY_ADAPTER_OPT_IN_SELECTED` como caminho seguro de
  integração. O próximo passo é especificar um adapter diagnóstico opt-in, sem
  promover `penny_shaped` a rota oficial do `lot-sim`.
- A Fase 11.8C especifica o contrato desse adapter diagnóstico opt-in usando
  os campos reais do `PennyShapedInput`. A especificação é fixture-only,
  sem schema runtime, sem CLI e sem validação BUZ29.
- A Fase 11.8D implementa o adapter C++ diagnóstico opt-in
  `PennyShapedDiagnosticAdapter`, preservando o núcleo isolado e mantendo
  `lot-pkn`, parser, schema e casos protegidos sem alteração de comportamento.
- A Fase 11.9A cria um caso sintético mínimo `penny_shaped` em
  `cases/validation/non_pkn/`, verificado por Python. Ele é fixture/caso
  diagnóstico, não entrada oficial do runtime.
- A Fase 11.9B classifica BUZ29 como `BUZ29_PENNY_CANDIDATE_PARTIAL` e bloqueia
  11.10A até existir evidência consumível de pressão, `sigmaTheta`, tempo desde
  abertura e estado APB/sal.
- A Fase 11.9C audita essas evidências e mantém a classificação como parcial:
  há fonte legada e indícios documentais, mas pressão, `sigmaTheta`, tempo de
  abertura, tempo desde abertura e estado APB/sal ainda não formam contrato
  consumível para iniciar a rota BUZ29-PENNY.
