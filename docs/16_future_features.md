# 16 — Planejamento de funcionalidades futuras

**Status:** Planejamento técnico  
**Escopo:** funcionalidades futuras que ainda não devem entrar no runtime  
**Restrição:** este documento não autoriza validação física nem alteração de
formulações sem fase própria.

---

## Fase 11.11I — fonte real de sigma-theta inicial

**Status:** `REAL_SIGMATHETA_INITIAL_SOURCE_STRATEGY_SPECIFIED`.

A fonte primaria futura para
`sigma_theta_initial_compression_positive_Pa` deve ser
`ELASTIC_INITIAL_WELLBORE_STATE`, isto e, o estado pos-perfuracao e pre-LOT na
parede do poco. O trace legado continua permitido apenas como diagnostico:

```text
LOT_TIME_ZERO_NOT_DRILLING_TIME_ZERO
LEGACY_TRACE_NOT_PHYSICAL_VALIDATION_SOURCE
implementation_allowed_next = false
```

A proxima etapa e auditar se o runtime real ja possui sigma-theta inicial,
sigma-theta current e pressao com semantica suficiente.

## Fase 11.11O — validacao controlada da fonte diagnostica

**Status:** `SIGMATHETA_DIAGNOSTIC_CONTROLLED_CASES_VALID`.

A fonte `sigma_theta_diagnostic_input` foi validada em fixtures controladas
para `ReadyNotReached`, `Reached` com PKN e `Reached` com `PENNY_SHAPED`
diagnostico. O resultado permanece limitado:

```text
LIMITED_GATE_CAN_BE_FED_DIAGNOSTICALLY
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
PKN_BEHAVIOR_NOT_CHANGED
```

Essa validacao nao resolve a fonte fisica futura de sigma-theta. A proxima
decisao deve avaliar readiness do gate diagnostico, nao habilitar dispatch
fisico.

## Fase 11.11J — disponibilidade runtime de sigma-theta e pressao

**Status:** `RUNTIME_SIGMATHETA_PRESSURE_AVAILABILITY_AUDITED`.

Resultado da auditoria:

```text
sigma_theta_initial_runtime_available = false
sigma_theta_current_runtime_available = false
wellbore_pressure_runtime_available = true
runtime_real_wiring_allowed_next = false
```

O gate limitado ainda nao pode ser alimentado fisicamente porque faltam fonte
runtime de sigma-theta inicial/current, convencao de sinal runtime resolvida e
referencial total na parede do poco.

## Fase 11.11K — contrato de estado inicial pos-perfuracao

**Status:** `POST_DRILLING_INITIAL_STATE_INTEGRATION_SPECIFIED_BUT_SOURCE_MISSING`.

Contrato especificado:

```text
PostDrillingInitialState
state_time = POST_DRILLING_BEFORE_LOT
sign_convention = COMPRESSION_POSITIVE
reference_frame = WELLBORE_WALL_TOTAL_STRESS
source_status = MISSING_RUNTIME_SIGMATHETA_SOURCE
implementation_allowed_next = false
```

O contrato esta pronto para orientar implementacao futura, mas a implementacao
continua bloqueada enquanto a fonte runtime de sigma-theta nao existir.

## Fase 11.11L — decisao real sigma-theta do limited_gate

**Status:** `LIMITED_GATE_REMAINS_DIAGNOSTIC_BLOCKED_BY_REAL_SOURCE`.

A decisao formal da 11.11L e:

```text
implementation_allowed_next = false
runtime_dispatch_allowed_next = false
buz29_execution_allowed_next = false
pkn_behavior_change_allowed = false
```

Assim, a proxima fase deve manter o gate como diagnostico e planejar a fonte
runtime real de sigma-theta, sem C++.

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
- A Fase 11.9D atualiza formalmente o readiness com base na 11.9C e mantém
  `can_start_11_10A = false`. A próxima evolução deve completar evidência de
  pressão e abertura antes de qualquer YAML candidato BUZ29-PENNY.
- A Fase 11.9E encontra evidência consumível de pressão e abertura no output
  legado `7-BUZ-29D-RJS10_PENNY-SHAPED.dat`: `Time` + blocos `dP` para
  histórico de pressão e `Momento da quebra: 10.4` para abertura. O status é
  `BUZ29_PRESSURE_AND_OPENING_EVIDENCE_COMPLETE`, com
  `can_reopen_11_10A_gate = true`, mas isso apenas recomenda a 11.9F para
  reavaliar readiness; não cria YAML BUZ29-PENNY nem inicia simulação.
- A Fase 11.9F reavalia esse readiness e registra
  `BUZ29_PENNY_CANDIDATE_PARTIAL_BUT_DIAGNOSTIC_SAFE`, com gate
  `BUZ29_PENNY_PARTIAL_DIAGNOSTIC_SAFE_START_11_10A`. Isso autoriza apenas a
  preparação diagnóstica 11.10A, sem validação física, sem equivalência com o
  legado e sem YAML criado pela 11.9F. O caveat
  `PENNY_MODEL_AXISYMMETRIC_1RAD_INTERPRETATION_REQUIRED` fica obrigatório:
  `fracture_volume_proxy_m3` não deve ser tratado automaticamente como volume
  circular completo em 2π sem auditoria matemática específica.
- A Fase 11.10A cria `cases/validation/non_pkn/buz29_penny_candidate.yaml` e
  `cases/validation/non_pkn/studies_index.yaml` como artefatos diagnósticos
  inativos. O status é `BUZ29_PENNY_DIAGNOSTIC_ROUTE_PARTIAL_STARTED`, com
  `NOT_PHYSICALLY_VALIDATED`, `NOT_LEGACY_EQUIVALENT` e
  `NOT_ACTIVE_SIMULATION_CASE`. A próxima exigência é
  `AXISYMMETRIC_1RAD_INTERNAL_TOTAL_VOLUME_OUTPUT_REQUIRED`; a rota ainda não
  executa BUZ29, não altera `lot-pkn` e não cria runner não-PKN.
- A Fase 11.10B inspeciona os campos do candidato contra a API real do
  `PennyShapedDiagnosticAdapter` e classifica
  `BUZ29_PENNY_ADAPTER_INPUTS_PARTIAL`. Pressão e abertura são consumíveis
  como evidência, mas as entradas elásticas, de viscosidade, vazão e
  `sigma_theta_compression_positive_Pa` ainda não estão adapter-ready. A
  próxima fase permanece `PHASE11_10C_AUDIT_PENNY_SHAPED_MODEL_MATH_AXISYMMETRIC_1RAD`
  antes de qualquer execução diagnóstica.
- A Fase 11.10C audita a matemática do `PennyShapedModel` na interpretação
  axissimétrica de 1 rad e classifica a rota como
  `PENNY_MATH_HYDRAULIC_DIAGNOSTIC_SCALING` /
  `PENNY_MATH_AXISYMMETRIC_1RAD_PROXY`. A auditoria passa sem correção C++,
  mas exige `PHASE11_10D_DEFINE_AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT` antes
  de tratar `fracture_volume_proxy_m3` como volume físico total.
- A Fase 11.10D especifica esse contrato de saída:
  `AXISYMMETRIC_1RAD_2PI_OUTPUT_CONTRACT_SPECIFIED`. Saídas futuras devem
  preservar `*_1rad_m3`, reportar equivalentes `*_equivalent_2pi_m3` apenas com
  campo `source`/caveat, e manter `volume_multiplier` como
  `VOLUME_MULTIPLIER_EMPIRICAL_NOT_2PI`. A próxima etapa é criar fixtures de
  saída diagnóstica, ainda sem writer/runtime C++.
- A Fase 11.10E materializa o contrato da 11.10D em fixtures JSON/CSV/metadata
  pequenos e versionados, com validador Python. O status é
  `PENNY_DIAGNOSTIC_OUTPUT_FIXTURES_VALID`; ainda não há writer C++,
  execução BUZ29-PENNY, validação física ou equivalência legada.
- A Fase 11.10F-aux registra uma restrição lateral da trilha sal/APB:
  `legacy/sestsal` não deve ser usado como motor standalone de validação. A
  função de fluência normaliza por `norm_sigd`, o estado hidrostático puro pode
  gerar `NaN`, e a referência legada deve permanecer acoplada ao `APB1da`.
  Comparações de deslocamento total legado versus deslocamento perturbacional
  moderno ficam bloqueadas até alinhamento de referencial.
- A Fase 11.10F especifica, sem implementar, o writer diagnóstico
  PennyShaped opt-in. O status é `PENNY_DIAGNOSTIC_WRITER_SPECIFIED`, com
  `IMPLEMENTATION_NOT_ALLOWED_IN_11_10F` e
  `RUNTIME_EXECUTION_NOT_ALLOWED_IN_11_10F`. A especificação preserva o
  contrato 1 rad ↔ 2π da 11.10D, as fixtures da 11.10E, caveats obrigatórios e
  a separação entre `volume_multiplier` empírico e fator geométrico `2π`. A
  próxima fase provável é
  `PHASE11_10G_IMPLEMENT_PENNY_DIAGNOSTIC_WRITER_OPT_IN`.
- A Fase 11.10G implementa o writer diagnóstico PennyShaped opt-in em C++,
  com `PENNY_DIAGNOSTIC_WRITER_IMPLEMENTED_OPT_IN`. O writer emite JSON/CSV em
  memória, preserva `*_1rad_m3`, calcula equivalentes `*_equivalent_2pi_m3`
  com `source`, exige caveats diagnósticos e rejeita validação física,
  equivalência legada, caso ativo e `volume_multiplier` como `2π`. A fase não
  implementa runner, não executa BUZ29-PENNY e não altera `lot-pkn`.
- A Fase 11.10H registra o gate para runner diagnóstico não-PKN e classifica a
  rota como `NON_PKN_DIAGNOSTIC_RUNNER_SPEC_PARTIAL`. Adapter e writer existem,
  mas BUZ29 continua parcial para execução: campos adapter-ready e semânticas
  de pressão, tempo e `sigmaTheta` permanecem diferidos. A implementação de
  runner, execução BUZ29-PENNY e qualquer impacto em `lot-pkn` continuam
  proibidos nesta fase.
- A Fase 11.10I reconcilia a trilha anterior com a decisão arquitetural de
  manter uma rota LOT/fracture unificada. O futuro seletor deve usar
  `lot.fracture.fracture_model`, com `PKN` como default quando o campo estiver
  ausente e `PENNY_SHAPED` apenas como opt-in explícito, diagnóstico e não
  fisicamente validado. `KGD`, `RADIAL`, `ELLIPTICAL` e variantes permanecem
  bloqueados. A fase não implementa runner, parser/schema ou execução
  BUZ29-PENNY.
- A Fase 11.10J especifica o guard desse seletor: ausência do campo preserva
  PKN, valor vazio explícito é erro, `PENNY_SHAPED` continua opt-in
  diagnóstico, modelos não suportados são bloqueados e a execução permanece
  condicionada a `fracture_initiation_gate` e à convenção explícita de sinal de
  `sigma_theta`. A fase não altera C++, parser, schema, CLI ou `lot-pkn`.
- A Fase 11.10K implementa o guard como helper C++ isolado
  `FractureModelSelector`, com testes Catch2 e auditoria Python. O helper
  normaliza `PKN`/`PENNY_SHAPED`, rejeita valor vazio explícito e bloqueia
  modelos não suportados, mas ainda não é integrado ao parser, schema, CLI ou
  runtime.
- A Fase 11.10L especifica a integração futura do guard ao parser/schema. A
  política recomendada é `SCHEMA_STRICT_CANONICAL_ONLY`, com `PKN` e
  `PENNY_SHAPED` como valores canônicos, ausência do campo defaultando para
  PKN, valor vazio explícito como erro e execução BUZ29-PENNY ainda bloqueada.
- A Fase 11.10M integra `lot.fracture.fracture_model` ao parser/schema com
  default retrocompatível `PKN`. `PENNY_SHAPED` explícito é aceito somente
  como metadado diagnóstico; `runtime_dispatch_enabled` permanece falso,
  BUZ29-PENNY não é executado e o próximo gate obrigatório é
  `SIGMATHETA_INITIAL_STATE_REQUIRED_BEFORE_MODEL_DISPATCH`.
- A Fase 11.10N audita esse gate e mantém o dispatch bloqueado. A classificação
  é `SIGMATHETA_INITIAL_STATE_MISSING` e
  `FRACTURE_GATE_REQUIRES_INITIAL_STATE_WIRING`: o runtime consegue consumir
  sigma-theta diagnóstico, mas ainda não prova um
  `sigma_theta_initial_after_drilling` calculado antes do gate. A próxima fase
  deve especificar esse wiring inicial antes de qualquer execução BUZ29-PENNY
  ou dispatch físico por `fracture_model`.
- A Fase 11.10O especifica o wiring futuro do estado inicial
  `sigma_theta_compression_positive_Pa`. A fonte preferencial passa a ser
  `ELASTIC_INITIAL_WELLBORE_STATE`, representando o estado geomecânico
  pós-perfuração e pré-LOT. O status é
  `SIGMATHETA_INITIAL_STATE_WIRING_SPECIFIED`, com
  `implementation_allowed_next = true`, mas `dispatch_allowed_next = false`:
  a próxima etapa pode implementar o guard de wiring, não executar BUZ29-PENNY
  nem liberar dispatch físico.
- A Fase 11.10P implementa `SigmaThetaInitialStateGuard` como helper C++
  isolado. O guard valida estado inicial, fonte, tempo, referencial, sinal e
  compatibilidade pressão x sigma-theta, mas não é chamado pelo runtime. A
  próxima fase planejada deve especificar a integração futura do guard ao
  `fracture_initiation_gate` sem liberar BUZ29-PENNY.
- A Fase 11.10Q especifica essa integração futura em nível arquitetural:
  `FractureModelSelector -> SigmaThetaInitialStateGuard -> criterio pressao x
  sigma_theta -> dispatch`. O dispatch permanece bloqueado. A próxima fase
  deve especificar o critério pressão x sigma-theta e a convenção de sinal
  associada antes de qualquer runtime físico.
## Fase 11.10R — guard futuro do critério pressão x sigma-theta

A próxima implementação recomendada é:

```text
PHASE11_10S_IMPLEMENT_PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD
```

Esse guard deve implementar apenas a validação algébrica especificada na
11.10R, preservando `lot-pkn`, parser/schema e dispatch runtime bloqueados até
que os testes provem semântica de pressão, sinal compression-positive e
referencial compatível.

## Fase 11.10S — PressureSigmaThetaFractureCriterionGuard

A Fase 11.10S implementa o helper C++ isolado
`PressureSigmaThetaFractureCriterionGuard` e registra:

```text
PHASE11_10S_PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD_IMPLEMENTED
PRESSURE_SIGMATHETA_FRACTURE_CRITERION_GUARD_IMPLEMENTED
SIGMATHETA_COMPRESSION_POSITIVE_CRITERION_IMPLEMENTED
PRESSURE_GREATER_THAN_SIGMATHETA_SHORTCUT_FORBIDDEN
RUNTIME_DISPATCH_NOT_CHANGED
LOT_PKN_BEHAVIOR_NOT_CHANGED
```

O helper calcula a forma preferencial:

```text
tensile_condition_Pa = -sigma_theta_current_compression_positive_Pa
fracture_margin_Pa = tensile_condition_Pa - tensile_strength_Pa
```

A forma alternativa por `fracture_threshold_pressure_Pa` tambem existe, mas
apenas como opcao explicita. Parser, schema, runtime dispatch, BUZ29-PENNY e
comportamento `lot-pkn` permanecem inalterados. A proxima fase recomendada e
`PHASE11_10T_SPECIFY_FRACTURE_GATE_RUNTIME_WIRING_WITH_GUARDS`.

## Fase 11.10T — especificar wiring runtime do fracture gate

Status registrado:

```text
PHASE11_10T_FRACTURE_GATE_RUNTIME_WIRING_SPECIFIED
FRACTURE_GATE_RUNTIME_WIRING_SPECIFIED
FRACTURE_MODEL_SELECTOR_REQUIRED
SIGMATHETA_INITIAL_STATE_GUARD_REQUIRED
PRESSURE_SIGMATHETA_CRITERION_GUARD_REQUIRED
RUNTIME_WIRING_NOT_IMPLEMENTED
DISPATCH_REMAINS_BLOCKED
```

A especificacao define a ordem futura dos guards, mas nao altera runtime. PKN
permanece default retrocompativel; `PENNY_SHAPED` e BUZ29-PENNY permanecem
bloqueados ate haver fixtures e testes de wiring explicitos.

## Fase 11.10U — fixtures do wiring runtime do fracture gate

Status registrado:

```text
PHASE11_10U_FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_DEFINED
FRACTURE_GATE_RUNTIME_WIRING_FIXTURES_VALID
RUNTIME_WIRING_NOT_IMPLEMENTED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_DIAGNOSTIC_ONLY
```

A fase adiciona fixtures e validador Python para o contrato do futuro
`fracture_initiation_gate`. Nenhum runtime wiring, dispatch ou BUZ29-PENNY e
executado.

## Fase 11.10V — plano de implementacao do runtime wiring

Status registrado:

```text
PHASE11_10V_RUNTIME_WIRING_IMPLEMENTATION_PLAN_SPECIFIED
RUNTIME_WIRING_IMPLEMENTATION_PLAN_SPECIFIED
RUNTIME_WIRING_IMPLEMENTATION_ALLOWED_NEXT
RUNTIME_EXECUTION_STILL_BLOCKED
BUZ29_EXECUTION_STILL_BLOCKED
PKN_BEHAVIOR_CHANGE_NOT_ALLOWED
```

A 11.10V autoriza apenas a proxima implementacao isolada do helper
`FractureGateRuntimeWiring`. Ela nao libera execucao runtime, nao altera
`lot-pkn`, nao chama `PknModel` ou `PennyShapedDiagnosticAdapter` e nao executa
BUZ29-PENNY.

## Fase 11.10W — FractureGateRuntimeWiring implementado

Status registrado:

```text
PHASE11_10W_FRACTURE_GATE_RUNTIME_WIRING_IMPLEMENTED
FRACTURE_GATE_RUNTIME_WIRING_IMPLEMENTED
RUNTIME_EXECUTION_NOT_ENABLED
PKN_MODEL_NOT_CALLED
PENNY_ADAPTER_NOT_CALLED
BUZ29_EXECUTION_BLOCKED
```

O helper C++ isolado esta disponivel para testes de gate/dispatch, mas ainda
nao e conectado ao runtime real. A proxima fase deve especificar o gate de
integracao antes de qualquer mudanca em `lot-pkn` ou execucao BUZ29-PENNY.

## Fase 11.10X — gate de integracao runtime

Status registrado:

```text
PHASE11_10X_RUNTIME_INTEGRATION_GATE_SPECIFIED
RUNTIME_INTEGRATION_GATE_SPECIFIED
DIAGNOSTIC_PRE_RUNNER_OPT_IN_SELECTED
RUNTIME_PHYSICAL_DISPATCH_NOT_ALLOWED
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_CHANGE_NOT_ALLOWED
```

A fase seleciona uma integracao futura opt-in e diagnostica entre parse/validacao
e `run_pkn_case(data)`. A integracao completa com dispatch fisico permanece
bloqueada.

## Fase 11.10Y — diagnostic pre-runner runtime gate

Status registrado:

```text
PHASE11_10Y_DIAGNOSTIC_PRE_RUNNER_RUNTIME_GATE_IMPLEMENTED
DIAGNOSTIC_PRE_RUNNER_OPT_IN_IMPLEMENTED
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
PKN_BEHAVIOR_NOT_CHANGED
BUZ29_EXECUTION_BLOCKED
```

A fase implementa um diagnostico pre-runner opt-in que grava
`diagnostic_fracture_gate.json` sem alterar `result.json`, `timeseries.csv`,
`PknModel` ou `PknRunner`. A execucao fisica de modelos nao-PKN e a rota
BUZ29-PENNY continuam como trabalho futuro bloqueado.

## Fase 11.10Z — fixtures do diagnostic pre-runner

Status registrado:

```text
PHASE11_10Z_DIAGNOSTIC_PRE_RUNNER_FIXTURES_DEFINED
DIAGNOSTIC_PRE_RUNNER_FIXTURES_VALID
BUZ29_EXECUTION_BLOCKED
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
```

A fase cria fixtures de contrato para exercitar o diagnostico pre-runner sem
habilitar dispatch fisico. A proxima etapa pode validar casos controlados com o
diagnostico habilitado, mantendo o resultado PKN fisico separado.

## Fase 11.11A — validacao controlada do diagnostic pre-runner

Status registrado:

```text
PHASE11_11A_DIAGNOSTIC_PRE_RUNNER_CONTROLLED_CASES_VALIDATED
DIAGNOSTIC_PRE_RUNNER_CONTROLLED_CASES_VALID
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
```

A fase valida o contrato das fixtures sem comparar ainda os outputs fisicos PKN
em profundidade. Essa comparacao fica para a 11.11B.

## Fase 11.11B — comparacao PKN com diagnostico opt-in

Status registrado:

```text
PHASE11_11B_PKN_OUTPUTS_COMPARED_WITH_DIAGNOSTICS
PKN_OUTPUTS_UNCHANGED_WITH_DIAGNOSTICS
DIAGNOSTIC_OUTPUT_ISOLATED
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
```

A fase compara `result.json` e `timeseries.csv` com diagnostico disabled/enabled
e confirma que o diagnostico pre-runner nao muda os outputs fisicos PKN. A
integracao segue limitada a diagnostico opt-in; dispatch fisico continua
bloqueado.

## Fase 11.11C — readiness da integracao runtime limitada

Status registrado:

```text
RUNTIME_WIRING_READY_FOR_LIMITED_GATE_SPEC
RUNTIME_PHYSICAL_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_DIAGNOSTIC_ONLY
```

A fase decide que a proxima etapa pode especificar uma integracao limitada do
fracture gate no runtime, mas ainda sem mudar comportamento PKN default e sem
habilitar dispatch fisico.

## Fase 11.11D — especificacao da integracao limitada

Status registrado:

```text
LIMITED_FRACTURE_GATE_RUNTIME_INTEGRATION_SPECIFIED
IMPLEMENTATION_ALLOWED_NEXT_WITH_DISPATCH_DISABLED
PKN_BEHAVIOR_CHANGE_NOT_ALLOWED
BUZ29_EXECUTION_BLOCKED
```

A especificacao permite uma implementacao futura apenas diagnostica. A proxima
fase deve provar novamente que `result.json` e `timeseries.csv` permanecem
preservados e que `diagnostic_fracture_gate.json` e isolado.
A Fase 11.11E adiciona a integracao runtime limitada do fracture gate. Esta
etapa reduz a lacuna entre diagnostico pre-runner e runtime, mas ainda nao
habilita dispatch fisico. O proximo incremento deve adicionar fixtures
controladas para `limited_gate` e continuar bloqueando BUZ29-PENNY.

```text
PHASE11_11F_ADD_LIMITED_GATE_CASE_FIXTURES
```

## Fase 11.11F — fixtures limited_gate

Status registrado:

```text
PHASE11_11F_LIMITED_GATE_FIXTURES_DEFINED
LIMITED_GATE_FIXTURES_VALID
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
PKN_BEHAVIOR_CHANGE_NOT_ALLOWED
```

A fase adiciona fixtures pequenas para o modo `limited_gate` e um validador
Python dedicado. A proxima etapa deve validar esses fixtures em casos
controlados, sem liberar dispatch fisico.

## Fase 11.11G — validação controlada limited_gate

Status registrado:

```text
PHASE11_11G_LIMITED_GATE_CONTROLLED_CASES_VALIDATED
LIMITED_GATE_CONTROLLED_CASES_VALID
PKN_OUTPUTS_UNCHANGED_WITH_LIMITED_GATE
DIAGNOSTIC_OUTPUT_ISOLATED
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

A fase confirma que `limited_gate` e reproduzivel em fixtures controladas e
que a comparacao PKN disabled/enabled continua preservando `result.json` e
`timeseries.csv`. A proxima decisao deve avaliar readiness sem liberar dispatch
fisico automaticamente.

## Fase 11.11H — readiness runtime diagnóstico

Status registrado:

```text
PHASE11_11H_LIMITED_GATE_RUNTIME_READINESS_DECIDED
LIMITED_GATE_READY_FOR_DIAGNOSTIC_RUNTIME_USE
LIMITED_GATE_NOT_READY_FOR_PHYSICAL_DISPATCH
BUZ29_EXECUTION_BLOCKED
PKN_BEHAVIOR_NOT_CHANGED
```

A próxima frente técnica deve especificar a fonte real de sigma_theta inicial
pós-perfuração antes de qualquer tentativa de gate fisicamente alimentado.
### Fase 11.11M — plano para completar fonte sigma-theta do limited_gate

Status:

```text
LIMITED_GATE_REMAINS_DIAGNOSTIC_SIGMATHETA_SOURCE_PLAN_RECORDED
```

A fase registrou que o `limited_gate` permanece diagnostico enquanto nao houver
fonte runtime real de sigma-theta inicial/current com semantica de pressao,
convencao de sinal e referencial resolvidos.

Proxima fase recomendada:

```text
PHASE11_11N_IMPLEMENT_OR_CONNECT_SIGMATHETA_SOURCE
```

Guardas preservados:

```text
runtime_dispatch_enabled = false
buz29_execution_allowed = false
pkn_behavior_changed = false
penny_shaped_runtime_enabled = false
```

### Fase 11.11N — fonte diagnostica explicita de sigma-theta

Status:

```text
SIGMATHETA_DIAGNOSTIC_SOURCE_IMPLEMENTED
LIMITED_GATE_CAN_BE_FED_DIAGNOSTICALLY
```

A fase adiciona `lot.fracture.sigma_theta_diagnostic_input` como entrada
opt-in para alimentar os guards do `limited_gate` em testes controlados. A fonte
nao e fisicamente validada, nao e equivalente ao legado e nao habilita dispatch.

Proxima fase:

```text
PHASE11_11O_VALIDATE_SIGMATHETA_DIAGNOSTIC_SOURCE_ON_CONTROLLED_CASES
```

### Fase 11.11P — readiness do gate sigma-theta diagnostico

Status:

```text
PHASE11_11P_DIAGNOSTIC_SIGMATHETA_GATE_READINESS_DECIDED
DIAGNOSTIC_SIGMATHETA_GATE_READY
READY_FOR_DIAGNOSTIC_USE
NOT_READY_FOR_PHYSICAL_VALIDATION
NOT_READY_FOR_PHYSICAL_DISPATCH
```

A fonte `sigma_theta_diagnostic_input` esta pronta para exercitar o
`limited_gate` em casos controlados. Isso ainda nao e validacao fisica, nao e
equivalencia com legado e nao habilita dispatch.

Proxima fase recomendada:

```text
PHASE11_11Q_SPECIFY_REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH
```

### Fase 11.11Q — caminho da fonte real sigma-theta

Status:

```text
PHASE11_11Q_REAL_SIGMATHETA_SOURCE_INTEGRATION_PATH_SPECIFIED
PRIMARY_REAL_SOURCE_ELASTIC_INITIAL_WELLBORE_STATE
POST_DRILLING_SIGMATHETA_PROVIDER_REQUIRED
IMPLEMENTATION_NOT_ALLOWED_NEXT
RUNTIME_DISPATCH_NOT_ALLOWED
```

A fase especifica `PostDrillingSigmaThetaProvider` como componente futuro. A
proxima fase deve criar fixtures do contrato antes de implementar qualquer
provider real.

### Fonte elástica inicial de sigma-theta

Status:

```text
ELASTIC_INITIAL_WELLBORE_SIGMATHETA_SOURCE_IMPLEMENTED
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

A fonte `ELASTIC_INITIAL_WELLBORE_STATE` foi implementada no
`PostDrillingSigmaThetaProvider` como rota opt-in para alimentar o
`limited_gate`. A aproximacao usa
`sigma_theta_current = far_field_stress_compression_positive_Pa -
wellbore_pressure_Pa`.

Ela permanece semi-fisica e diagnostica: nao e validacao fisica plena, nao e
equivalencia com legado, nao habilita dispatch fisico e nao libera BUZ29-PENNY.

### Validação analítica da fonte elástica sigma-theta

Status:

```text
ELASTIC_SIGMATHETA_ANALYTIC_CASES_VALID
FORMULA_VERIFIED
SIGN_CONVENTION_VERIFIED
THRESHOLD_BEHAVIOR_VERIFIED
```

A validação analítica cobre cinco casos controlados e confirma que o threshold
exato e classificado como `Reached`. A próxima decisão deve avaliar readiness
diagnóstico da fonte elástica sem promover o resultado a validação física plena.

### Readiness da fonte elástica sigma-theta

Status:

```text
ELASTIC_SIGMATHETA_SOURCE_READY_FOR_DIAGNOSTIC_SEMIPHYSICAL_USE
READY_FOR_KIRSCH_OR_AXISYMMETRIC_UPGRADE_SPEC
PHYSICALLY_VALIDATED_FALSE
LEGACY_EQUIVALENT_FALSE
RUNTIME_DISPATCH_NOT_ENABLED
```

A fonte `ELASTIC_INITIAL_WELLBORE_STATE` está pronta para diagnóstico
semi-físico controlado. A próxima evolução deve especificar Kirsch/hoop stress
ou uma formulação elástica axisimétrica mais alinhada ao runtime, ainda sem
dispatch físico e sem BUZ29-PENNY.

### Upgrade axisimétrico da fonte elástica sigma-theta

Status:

```text
ELASTIC_SIGMATHETA_UPGRADE_SOURCE_IMPLEMENTED
AXISYMMETRIC_ELASTIC_WELLBORE_STATE
RUNTIME_DISPATCH_NOT_ENABLED
BUZ29_EXECUTION_BLOCKED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

A fonte `AXISYMMETRIC_ELASTIC_WELLBORE_STATE` foi adicionada ao provider
pós-perfuração como rota diagnóstica opt-in. Ela usa os campos atualmente
disponíveis (`far_field_stress_compression_positive_Pa`,
`wellbore_pressure_Pa` e `tensile_strength_Pa`) e registra caveats
axisimétricos explícitos.

Kirsch completo permanece bloqueado até existirem `sigma_H`, `sigma_h` e
azimute no contrato de entrada. A nova source não é validação física, não é
equivalência com legado e não habilita dispatch físico.

### Validação analítica do upgrade axisimétrico sigma-theta

Status:

```text
ELASTIC_SIGMATHETA_UPGRADE_ANALYTIC_CASES_VALID
FORMULA_VERIFIED
SIGN_CONVENTION_VERIFIED
THRESHOLD_BEHAVIOR_VERIFIED
```

A validação analítica da source `AXISYMMETRIC_ELASTIC_WELLBORE_STATE` cobre
cinco casos controlados e confirma que o threshold exato permanece classificado
como atingido. O próximo gate deve decidir readiness diagnóstico da source sem
promovê-la a validação física plena.

### Readiness do upgrade axisimétrico sigma-theta

Status:

```text
ELASTIC_SIGMATHETA_UPGRADE_READY_FOR_DIAGNOSTIC_USE
AXISYMMETRIC_ELASTIC_WELLBORE_STATE
READY_FOR_DIAGNOSTIC_USE
READY_FOR_CONTROLLED_PHYSICAL_COMPARISON_FALSE
READY_FOR_PHYSICAL_DISPATCH_FALSE
```

A source axisimétrica está pronta para uso diagnóstico controlado, mas continua
fora de validação física plena, equivalência com o LOT_Tese e dispatch físico.
Kirsch completo segue bloqueado até que `sigma_H`, `sigma_h` e azimute existam
como campos auditados no contrato de entrada.

### Comparação analítica controlada da source axisimétrica

Status:

```text
ELASTIC_SIGMATHETA_SOURCE_REFERENCE_COMPARISON_VALID
ANALYTIC_CONTROLLED_REFERENCE
WITHIN_TOLERANCE_TRUE
PHYSICALLY_VALIDATED_FALSE
LEGACY_EQUIVALENT_FALSE
```

A source `AXISYMMETRIC_ELASTIC_WELLBORE_STATE` foi comparada contra uma
referência analítica controlada versionada em fixtures. A comparação verifica
fórmula, sinal e comportamento de threshold, mas não usa trace legado como
validação física e não libera dispatch runtime.

### Readiness para preparar gate BUZ/Legacy

Status:

```text
READY_FOR_BUZ_OR_LEGACY_COMPARISON_GATE
READY_FOR_PHYSICAL_VALIDATION_FALSE
LEGACY_EQUIVALENCE_ALLOWED_FALSE
BUZ29_EXECUTION_ALLOWED_FALSE
```

A source axisimétrica pode avançar para a preparação de um gate BUZ/Legacy,
mas essa decisão permite apenas organizar escopo, campos, tolerâncias e
caveats. Ela não autoriza comparação física executada, equivalência com o
LOT_Tese, BUZ29-PENNY ou dispatch runtime.

### Gate BUZ/Legacy preparado para source elástica sigma-theta

Status:

```text
BUZ_OR_LEGACY_COMPARISON_GATE_PREPARED
RECOMMENDED_FIRST_COMPARISON_ANALYTIC_OR_BUZ67D_PKN_DIAGNOSTIC
PHYSICAL_VALIDATION_ALLOWED_FALSE
LEGACY_EQUIVALENCE_ALLOWED_FALSE
BUZ29_PENNY_EXECUTION_ALLOWED_FALSE
```

O gate define que a primeira comparação futura deve permanecer em referência
analítica ou BUZ67D/PKN diagnóstico. Antes de qualquer comparação com legado,
devem ser alinhados pressão, tensão, tempo, semântica de pressão, referencial de
tensão e convenção de sinais. BUZ29-PENNY continua bloqueado.

### First Controlled Reference Comparison

Status:

```text
FIRST_CONTROLLED_REFERENCE_COMPARISON_VALID
ANALYTIC_AXISYMMETRIC_CONTROLLED_REFERENCE
PHYSICAL_VALIDATION_NOT_CLAIMED
LEGACY_EQUIVALENCE_NOT_CLAIMED
BUZ29_PENNY_NOT_EXECUTED
RUNTIME_DISPATCH_NOT_ENABLED
PKN_BEHAVIOR_NOT_CHANGED
```

A primeira comparação após o gate BUZ/Legacy usa sete fixtures axisimétricas
independentes para fixar a álgebra de `AXISYMMETRIC_ELASTIC_WELLBORE_STATE`.
O próximo passo progressivo é
`PHASE_DECIDE_BUZ67D_PKN_REFERENCE_READINESS`.

### BUZ67D PKN Reference Readiness

Status:

```text
BUZ67D_PKN_READY_FOR_DIAGNOSTIC_REFERENCE
PHYSICAL_VALIDATION_NOT_CLAIMED
LEGACY_EQUIVALENCE_NOT_CLAIMED
BUZ29_PENNY_NOT_EXECUTED
RUNTIME_DISPATCH_NOT_ENABLED
PKN_BEHAVIOR_NOT_CHANGED
```

BUZ67D/PKN pode ser usado como primeira referência diagnóstica controlada antes
de qualquer BUZ29/PENNY. O próximo passo é preparar o manifesto de insumos
BUZ29/PENNY sem executar o caso.

### BUZ29 Penny Diagnostic Inputs

Status:

```text
BUZ29_PENNY_DIAGNOSTIC_INPUTS_PREPARED
EXECUTION_NOT_ALLOWED_YET
DIAGNOSTIC_ONLY
PHYSICAL_VALIDATION_NOT_CLAIMED
LEGACY_EQUIVALENCE_NOT_CLAIMED
RUNTIME_DISPATCH_NOT_ENABLED
```

Os insumos mínimos para o próximo gate diagnóstico foram registrados em
manifesto versionado. BUZ29/PENNY ainda não foi executado.

### BUZ29 Penny Diagnostic Execution Gate

Status:

```text
BUZ29_PENNY_DIAGNOSTIC_EXECUTION_ALLOWED_NEXT
PHASE_RUN_BUZ29_PENNY_DIAGNOSTIC_COMPARISON_ALLOWED_NEXT
BUZ29_PENNY_NOT_EXECUTED_IN_GATE
RUNTIME_DISPATCH_NOT_ENABLED
```

This is a narrow future-work authorization for diagnostic comparison. It is not
physical validation and it is not legacy equivalence.

### BUZ29 Penny Diagnostic Run Blocker

Status:

```text
BUZ29_PENNY_DIAGNOSTIC_RUN_BLOCKED
BUZ29_PENNY_DIAGNOSTIC_EXECUTION_BLOCKED_BY_MISSING_RUNNER
RUNTIME_DISPATCH_NOT_ENABLED
PKN_BEHAVIOR_NOT_CHANGED
```

Future work should add a dedicated diagnostic runner, or explicitly complete
the missing adapter-ready BUZ29/PENNY inputs before attempting execution again.

### BUZ29 Penny Diagnostic Runner

Status:

```text
BUZ29_PENNY_DIAGNOSTIC_RUNNER_IMPLEMENTED_INPUTS_PARTIAL
SYNTHETIC_COMPLETE_CASE_RUNS
REAL_BUZ29_INPUTS_STILL_PARTIAL
RUNTIME_DISPATCH_NOT_ENABLED
PENNY_SHAPED_RUNTIME_NOT_ENABLED
```

The dedicated runner now exists as an isolated diagnostic path around the
PennyShaped adapter and writer. It does not enable non-PKN runtime dispatch and
does not change PKN behavior. Future work should complete the BUZ29/PENNY
adapter-ready input set before attempting a real candidate diagnostic run.

### BUZ29 Penny Adapter Inputs Still Partial

Status:

```text
BUZ29_PENNY_ADAPTER_INPUTS_STILL_PARTIAL
PHYSICAL_VALIDATION_NOT_CLAIMED
LEGACY_EQUIVALENCE_NOT_CLAIMED
RUNTIME_DISPATCH_NOT_ENABLED
PKN_BEHAVIOR_NOT_CHANGED
```

The adapter input matrix identifies five missing fields and two semantically
ambiguous fields. Future work must resolve these from explicit BUZ29 sources,
not synthetic fixtures.

### APB/LOT Modern Output And Mode Contracts

Status:

```text
APB_LOT_JSON_OUTPUT_IMPLEMENTED
LEAKOFF_VOLUME_BALANCE_MODE_IMPLEMENTED
PRE_ITERATIVE_SALT_DISPLACEMENT_IMPLEMENTED
APB_LOT_MODERN_METHOD_VALIDATED
LEGACY_MODE_PRESERVED_FOR_COMPARISON
PKN_BEHAVIOR_NOT_CHANGED
```

The APB/LOT modernization route now has isolated contracts for `*_out.json`,
`volume_balance` leakoff coupling and `pre_iterative` salt displacement
scheduling. These contracts do not enable a full APB solver, do not alter PKN,
and do not resolve BUZ29/PENNY adapter inputs.

### APB/LOT Extended Regression Suite

Status:

```text
APB_LOT_EXTENDED_REGRESSION_PASSED
MODERN_APB_LOT_MODES_VALID
LEGACY_APB_LOT_MODES_PRESERVED
JSON_OUTPUT_CONTRACT_VALID
PKN_BEHAVIOR_NOT_CHANGED
BUZ29_PENNY_NOT_EXECUTED
```

This is a contract-level regression. Runtime APB metrics remain unavailable
until a real APB runner/case is connected to the modern path.
