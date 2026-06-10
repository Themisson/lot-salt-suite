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
