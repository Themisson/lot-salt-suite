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

1. Revisar o diagnóstico 10.18B porque `initial_pressure_Pa` somado ao balanço
   moderno superestima a pressão máxima legada no BUZ67D controlado.
2. Auditar a semântica de `dP` legado após abertura/leakoff.
3. Criar `FluidModel` abstrato e `ConstantFluidModel` compatível com o estado atual.
4. Auditar especificamente as unidades Zamora no `LOT_APB_v5`.
5. Implementar `ZamoraFluidModel` experimental, opt-in e sem alterar defaults.

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
