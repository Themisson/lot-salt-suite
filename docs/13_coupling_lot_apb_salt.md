# 13 — Acoplamento LOT–APB–Sal

**Status:** Planejado | **Última atualização:** 2026-06-04

> A formulação detalhada deve ser verificada via `/formulation-audit`
> comparando os legados antes de implementar o módulo `coupling/`.

## Conceito de acoplamento

O LOT, APB e fluência de sal são fenômenos que se influenciam mutuamente:

1. **LOT → Sal:** pressão de fratura provoca campo de tensão na parede do poço →
   inicia ou acelera fluência do sal
2. **Sal → APB:** fluência do sal deforma a parede → reduz volume anular →
   aumenta pressão no anular (APB)
3. **APB → Sal:** pressão anular muda a tensão efetiva na rocha salina

Na arquitetura atual, o caminho LOT inicial deve ser PKN. O acoplamento com sal
deve passar pelo adapter para `external/saltcreep/`, que e uma dependencia
vendorizada ativa com governanca descrita em `docs/16_saltcreep_governance.md`.
O adapter nao deve depender de scripts Python em runtime. A Fase 6.10B criou a
opcao CMake `LSS_SALTCREEP_FORCE_LSS_EIGEN` e provou que o saltcreep compila e
executa corretamente com `include/Eigen` (via diretorio proxy). As duas copias
de Eigen permanecem preservadas; a migracao definitiva sera decidida apos o
ctest completo do build forcado.

## Política de implementação

O acoplamento LOT/APB/sal deve ser implementado em C++.

Python não deve atuar como intermediário runtime entre LOT e sal, nem montar
condições de contorno para `external/saltcreep` no fluxo principal. A integração
deve ocorrer por interfaces C++, como `SaltCreepInterface`,
`SaltCreepSaltcreepAdapter` e futuros adapters específicos para LOT/sal.
A Fase 7.0 criou apenas o contrato minimo `SaltCreepQuery` /
`SaltCreepResponse` e `NullSaltCreepInterface`; ainda nao ha chamada para
`external/saltcreep` nem acoplamento LOT/sal.
A Fase 7.1 fixou a convencao de sinais LOT-sal em
`docs/23_lot_salt_sign_convention.md`: pressoes compressivas sao positivas,
deslocamento radial positivo aponta para fora e fechamento radial e uma
magnitude positiva separada.
A Fase 7.2 criou `SaltCreepSaltcreepAdapter` como adapter C++ experimental e
isolado. Ele valida queries e preserva a convencao de fechamento, mas ainda
retorna resposta neutra com `is_available() = false`; portanto nao ha
acoplamento LOT/sal nem chamada fisica ao `external/saltcreep`.
A Fase 7.3 provou um caso C++ controlado e isolado do backend `saltcreep` com
Lame elastico, mas manteve o adapter neutro. O teste mostrou que pressao
interna positiva no `WallPressureField` expande a parede (`u_r > 0`), enquanto
pressao externa/confinante fecha (`u_r < 0`). Portanto, o futuro acoplamento
deve mapear cuidadosamente pressoes internas, externas e geostaticas antes de
converter resposta do backend em `radial_closure_m`.

Fluxo esperado:

```text
YAML/JSON → C++ parser → C++ LOT/APB/salt coupling → C++ writer → CSV/JSON
```

Python pode aparecer somente depois, para:

```text
CSV/JSON → Python plot/report/auditoria externa → PNG/HTML
```

## Algoritmo proposto (a verificar com formulação do legado)

```
Para cada passo de tempo dt:
  1. Atualizar campo térmico T(z, t)
  2. Calcular tensão geostática atualizada σ₀(t)
  3. Resolver LOT:
     - Calcular pressão de fratura P_frac
     - Calcular leakoff: volume perdido Q_LOT(t)
  4. Calcular tensão na parede do poço:
     σ_wall = f(P_anular, P_poros, σ₀, geometria)
  5. Chamar SaltCreepInterface::evaluate_wall_response(query):
     - Entradas: tempo [s], pressao de parede compressiva [Pa], temperatura [K] e posicao radial [m]
     - Retorna: deslocamento radial assinado [m], fechamento radial positivo [m], deformacao radial e pressao efetiva de fechamento [Pa]
  6. Calcular variação de volume anular:
     δV_anular = f(ε, geometria do poço)
  7. Atualizar pressão APB:
     δP_APB = δV_anular / (compressibilidade_fluido × V_anular)
  8. Verificar convergência (|δP_APB| < tolP)
  9. Atualizar estado e avançar tempo
```

## Questões em aberto (PENDENTE de auditoria)

| Questão | Impacto | Arquivo de referência |
|---------|---------|----------------------|
| Convenção de sinais de tensão | Crítico | `legance/LOT_Tese/include/apb_code/Rock.h` |
| Definição de tensão efetiva no sal | Crítico | `legance/LOT_Tese/include/sestsal/material.h` |
| Coordenadas: tensão radial × tangencial × axial | Alto | `legance/LOT_Tese/src/apb_code/APB1da.cpp` |
| Critério de convergência do loop | Médio | `legance/LOT_APB_v5/main/main.cpp` |
| Semantica de tempo PKN (`t` absoluto vs. tempo desde breakdown) | Alto | `legance/LOT_Tese/src/apb_code/APB1da.cpp` |
| Conversoes de vazao com fator geometrico embutido | Alto | `legance/LOT_Tese/src/apb_code/APB1da.cpp` |

## Contrato de pressao LOT/PKN -> sal (Fase 9.1A)

A Fase 9.0 criou um ponto experimental de chamada real em `coupling/`:
`evaluate_lot_salt_step()` recebe um `PknResult`, seleciona um passo da serie
temporal, constroi uma `SaltCreepQuery` e chama
`SaltCreepInterface::evaluate_wall_response(query)`.

Na Fase 9.0, `PknResult.net_pressure_series_Pa[step_index]` foi encaminhado
diretamente para `SaltCreepQuery.wall_pressure_Pa`. Esse mapeamento e apenas um
proxy experimental para demonstrar a chamada. Ele nao e o contrato fisico
definitivo.

### Significado de `PknResult.net_pressure_series_Pa`

`PknResult.net_pressure_series_Pa` representa a pressao liquida PKN. No modelo
PKN minimo atual, ela e calculada por:

```text
p_net = E' * w / h
```

onde `E'` e o modulo plano [Pa], `w` e a abertura da fratura [m] e `h` e a
altura PKN [m]. Portanto, `p_net` e uma pressao relativa de fratura associada a
abertura elastica da fratura. Ela nao e, por si so:

- pressao absoluta do poco;
- pressao anular;
- pressao hidrostatica;
- pressao de parede do sal;
- tensao radial efetiva no sal.

Consequencia: `p_net PKN != wall_pressure_Pa fisico do sal`.

### Significado esperado de `SaltCreepQuery.wall_pressure_Pa`

`SaltCreepQuery.wall_pressure_Pa` deve representar uma pressao compressiva
absoluta aplicada na parede do sal, ou uma condicao radial equivalente definida
explicitamente. Ela pertence ao contrato de contorno radial do dominio de sal:
o adapter deve conseguir interpretar esse valor como carregamento normal na
parede do poco/anular, coerente com a convencao geomecanica de compressao
positiva.

Se uma fase futura optar por enviar uma tensao radial equivalente em vez de uma
pressao absoluta, essa equivalencia deve ser nomeada no metodo de mapeamento,
documentada no resultado e testada separadamente. Nao se deve esconder uma
tensao radial efetiva sob o nome `wall_pressure_Pa` sem registrar a referencia
fisica usada.

### Diferenca entre pressoes e tensoes

| Quantidade | Definicao operacional | Pode alimentar `wall_pressure_Pa` diretamente? |
|------------|-----------------------|-----------------------------------------------|
| `p_net` PKN | Pressao liquida de fratura, relativa a abertura PKN (`E' * w / h`). | Somente no modo experimental da Fase 9.0. |
| Pressao de fratura | Pressao no fluido da fratura; em geral exige referencia de tensao/pressao para sair de `p_net`. | Nao sem converter para pressao absoluta ou condicao radial. |
| Pressao absoluta de poco | Pressao fisica no poco/sapata/anular em Pa absolutos. | Sim, e o candidato fisicamente preferivel. |
| Pressao hidrostatica | Componente `rho * g * z` da coluna de fluido, possivelmente somada a pressao de superficie. | Sim, quando representa a pressao absoluta local. |
| Pressao de superficie/bombeio | Pressao imposta/medida na superficie ou no sistema de bombeio. | Nao isoladamente; deve ser propagada ate a profundidade. |
| Pressao anular | Pressao do fluido em anular selado ou aberto no trecho de interesse. | Sim, se for a pressao atuante na parede do sal. |
| Pressao de poros | Pressao do fluido nos poros da formacao. | Nao diretamente; entra em tensao efetiva. |
| Tensao radial | Componente normal radial aplicada ao contorno mecanico. | Pode ser equivalente, mas deve ser documentada como tal. |
| Tensao efetiva | Tensao total corrigida por pressao de poros/convensao efetiva. | Nao deve ser confundida com pressao absoluta de parede. |
| `wall_pressure_Pa` do sal | Pressao compressiva absoluta de parede, ou condicao radial equivalente explicita, enviada a `SaltCreepQuery`. | E o alvo do mapeamento. |

### Metodos candidatos para `LotSaltPressureMap`

A Fase 9.1B deve substituir o uso direto de `net_pressure_series_Pa` por um
mapeador explicito. Metodos candidatos iniciais:

#### Metodo 1 -- `ExperimentalNetPressureProxy`

```text
wall_pressure_Pa = net_pressure_Pa
```

Classificacao: experimental, nao fisico, compatibilidade com a Fase 9.0.

Esse metodo deve existir apenas para preservar a prova de chamada criada na
Fase 9.0 e para manter testes de transicao. Ele nao deve ser apresentado como
pressao anular ou pressao absoluta.

#### Metodo 2 -- `AbsoluteWellborePressure`

```text
wall_pressure_Pa = absolute_wellbore_pressure_Pa
```

Classificacao: fisicamente preferivel quando a pressao absoluta estiver
disponivel.

Esse metodo deve ser o alvo de producao quando o runtime fornecer pressao de
poco/sapata/anular em Pa absolutos, no trecho de sal avaliado.

#### Metodo 3 -- `HydrostaticPlusNetPressure`

```text
wall_pressure_Pa = surface_pressure_Pa + rho * g * depth_m + net_pressure_Pa
```

Classificacao: aproximacao intermediaria, valida somente se
`net_pressure_Pa` for interpretada como incremento sobre a coluna hidrostatica.

Esse metodo nao deve virar padrao sem validacao fisica e sem explicitar qual
referencia transforma `p_net` em incremento de pressao absoluta.

### Dados disponiveis e ausentes hoje

Disponiveis no projeto apos a Fase 9.0:

- `PknResult.net_pressure_series_Pa`;
- `LotConfig.breakdown_pressure_Pa`;
- `FluidData.density_kg_m3`;
- `FluidData.weight_lb_per_gal`;
- `FluidData.surface_pressure_Pa`, quando o modo do fluido exigir;
- `LotConfig.shoe_depth_m`;
- `AnnularData.top_m`, `AnnularData.base_m` e `AnnularData.fluid_id`;
- `units::ppg_hydrostatic_Pa_per_m()`.

Ausentes ou ainda nao integrados ao `coupling/`:

- pressao absoluta de poco por tempo;
- pressao de bombeio/superficie por tempo;
- pressao no fundo/sapata por tempo;
- pressao anular APB por tempo;
- pressao de poros;
- tensao horizontal minima/closure stress;
- tensao radial geostatica de contorno para o sal;
- bloco `wellbore` persistido em `CaseData`;
- estado APB calculado;
- regra explicita para converter pressao PKN em pressao absoluta.

### Contrato proposto para a Fase 9.1B

A proxima fase deve criar um mapeador explicito:

- `include/coupling/LotSaltPressureMap.hpp`;
- `src/coupling/LotSaltPressureMap.cpp`;
- `tests/cpp/test_lot_salt_pressure_map.cpp`.

API conceitual:

```cpp
enum class LotSaltPressureMapMethod {
  ExperimentalNetPressureProxy,
  AbsoluteWellborePressure,
  HydrostaticPlusNetPressure
};

struct LotSaltPressureMapInput {
  double net_pressure_Pa = 0.0;
  double absolute_wellbore_pressure_Pa = 0.0;
  double hydrostatic_pressure_Pa = 0.0;
  double surface_pressure_Pa = 0.0;
  double depth_m = 0.0;
  LotSaltPressureMapMethod method =
      LotSaltPressureMapMethod::ExperimentalNetPressureProxy;
};

struct LotSaltPressureMapResult {
  double wall_pressure_Pa = 0.0;
  LotSaltPressureMapMethod method;
  std::string method_label;
  bool physically_absolute = false;
};

LotSaltPressureMapResult map_lot_pkn_to_salt_wall_pressure(
    const LotSaltPressureMapInput& input);
```

`evaluate_lot_salt_step()` deve ser adaptada futuramente para consumir
`LotSaltPressureMapResult.wall_pressure_Pa`, nao
`PknResult.net_pressure_series_Pa` diretamente.

## `LotSaltPressureMap` implementado (Fase 9.1B)

A Fase 9.1B implementa `LotSaltPressureMap` como camada explicita entre
`PknResult` e `SaltCreepQuery.wall_pressure_Pa`. A funcao
`evaluate_lot_salt_step()` nao escreve mais `net_pressure_series_Pa`
diretamente em `query.wall_pressure_Pa`; ela monta um
`LotSaltPressureMapInput`, chama `map_lot_pkn_to_salt_wall_pressure()` e usa
`LotSaltPressureMapResult.wall_pressure_Pa`.

Metodos implementados:

| Metodo | Formula | `physically_absolute` | Uso |
|--------|---------|-----------------------|-----|
| `ExperimentalNetPressureProxy` | `wall_pressure_Pa = net_pressure_Pa` | `false` | Default temporario para compatibilidade com a Fase 9.0. |
| `AbsoluteWellborePressure` | `wall_pressure_Pa = absolute_wellbore_pressure_Pa` | `true` | Preferivel quando a pressao absoluta de poco/anular estiver disponivel. |
| `HydrostaticPlusNetPressure` | `wall_pressure_Pa = surface_pressure_Pa + hydrostatic_pressure_Pa + net_pressure_Pa` | `true` | Aproximacao intermediaria; exige interpretacao fisica de `p_net` como incremento sobre a coluna. |

O default permanece `ExperimentalNetPressureProxy` apenas para manter o
comportamento numerico da Fase 9.0 e os testes de transicao. Ele nao deve ser
usado como interpretacao fisica de pressao anular.

`HydrostaticPlusNetPressure` recebe `hydrostatic_pressure_Pa` ja calculada. A
Fase 9.1B nao integra ainda o calculo `rho * g * depth` a partir de fluido,
profundidade ou estado de poco dentro do `coupling/`. Esse passo depende de
dados hidraulicos e geomecanicos que ainda nao estao no contrato runtime.

O caminho `lot-sim run --mode lot-pkn` segue desacoplado do sal: a nova camada
apenas organiza o ponto experimental em `coupling/` e nao retroalimenta PKN, nao
conecta APB e nao altera o runner do LOT.

## Utilitarios hidrostaticos puros (Fase 9.2B)

A Fase 9.2B adiciona utilitarios matematicos puros em `include/units/units.hpp`
para calcular pressao hidrostatica a partir de dados ja conhecidos:

```text
hydrostatic_pressure_Pa = density_kg_m3 * g * depth_m
ppg_hydrostatic_pressure_Pa = ppg_hydrostatic_Pa_per_m(ppg, g) * depth_m
surface_plus_hydrostatic_pressure_Pa =
    surface_pressure_Pa + hydrostatic_pressure_Pa(density_kg_m3, depth_m, g)
```

Esses utilitarios rejeitam valores nao finitos, pressoes/densidades/profundidades
negativas e gravidade nao positiva. Profundidade zero e pressao de superficie
zero sao permitidas.

Esta fase nao conecta o calculo automaticamente ao `coupling/`. O metodo
`LotSaltPressureMapMethod::HydrostaticPlusNetPressure` continua recebendo
`hydrostatic_pressure_Pa` pronta em `LotSaltCouplingConfig`. O fluxo
`YAML -> CaseParser -> CaseData -> coupling` ainda nao calcula hidrostática
automaticamente, e `CaseData` continua sem persistir o bloco `wellbore`.

O caminho `lot-sim run --mode lot-pkn` permanece desacoplado do sal e
inalterado. Uma fase futura deve decidir se `hydrostatic_pressure_Pa` sera
derivada de `CaseData`, `FluidData`, `LotConfig.shoe_depth_m` ou de um contexto
especifico do `coupling/`.

## Contexto hidrostatico derivado de `CaseData` (Fase 9.3B)

A Fase 9.3B cria `LotSaltHydrostaticContext` em `coupling/` como helper puro
para derivar uma primeira pressao hidrostatica a partir de `CaseData` ja
parseado. A regra implementada e deliberadamente conservadora:

```text
depth_m = CaseData.lot.shoe_depth_m
annular = unico AnnularData tal que top_m <= depth_m <= base_m
fluid = FluidData referenciado por annular.fluid_id
hydrostatic_pressure_Pa =
    units::hydrostatic_pressure_Pa(fluid.density_kg_m3, depth_m)
```

O helper rejeita sapata nao positiva, ausencia de anular contendo a sapata,
mais de um anular contendo a sapata, fluido referenciado ausente e densidade
invalida. O resultado carrega `depth_m`, `density_kg_m3`,
`hydrostatic_pressure_Pa`, `annular_index`, `fluid_id` e uma string `source`
descrevendo a origem dos dados.

Esta fase ainda nao usa o bloco `wellbore`, porque ele existe no YAML/schema,
mas ainda nao e persistido em `CaseData`. Tambem nao usa `surface_pressure_Pa`,
`weight_lb_per_gal` nem `hydrostatic_depth_profile`; esses campos exigem uma
fase propria de politica hidraulica. O helper nao esta conectado
automaticamente ao `LotSaltPressureMap`, nao altera `evaluate_lot_salt_step()`,
nao calcula APB e nao cria acoplamento iterativo.

O caminho `lot-sim run --mode lot-pkn` permanece desacoplado do sal e
inalterado. Uma fase futura pode usar esse contexto para preencher
explicitamente `LotSaltCouplingConfig.hydrostatic_pressure_Pa` em uma rota de
coupling opt-in, mantendo o runner LOT/PKN padrao preservado.

## Builder opt-in de configuracao hidrostatica (Fase 9.4B)

A Fase 9.4B cria `LotSaltCouplingConfigBuilder` como helper opt-in para montar
`LotSaltCouplingConfig` a partir de `LotSaltHydrostaticContext`, ou diretamente
de `CaseData` via `make_lot_salt_hydrostatic_context(data)`.

O builder preenche:

```text
config.hydrostatic_pressure_Pa = context.hydrostatic_pressure_Pa
config.depth_m = context.depth_m
config.surface_pressure_Pa = options.surface_pressure_Pa
config.temperature_K = options.temperature_K
config.radial_position_m = options.radial_position_m
config.pressure_map_method = options.method
```

O default local do builder e
`LotSaltPressureMapMethod::HydrostaticPlusNetPressure`, porque o helper existe
para a rota hidrostatica opt-in. Isso nao altera o default global de
`LotSaltCouplingConfig`, que continua
`LotSaltPressureMapMethod::ExperimentalNetPressureProxy` para preservar o
comportamento numerico experimental da Fase 9.0.

O builder nao e chamado por `lot-sim`, nao e chamado por `PknRunner`, nao altera
`CaseParser` nem `CaseData` e nao muda `evaluate_lot_salt_step()`. Ele apenas
habilita um encadeamento explicito e testavel:

```text
CaseData -> LotSaltHydrostaticContext -> LotSaltCouplingConfig
         -> LotSaltPressureMap -> evaluate_lot_salt_step()
```

Essa rota ainda nao e acoplamento fisico validado. `HydrostaticPlusNetPressure`
continua exigindo a interpretacao explicita de `p_net` como incremento sobre a
coluna hidrostatica, e nao deve virar default global sem validacao fisica.

## Status fisico de `HydrostaticPlusNetPressure` (Fase 9.5A)

A Fase 9.5 auditou a validade fisica da expressao:

```text
p_wall = p_hydrostatic + p_net
```

ou, na API atual:

```text
wall_pressure_Pa =
    surface_pressure_Pa + hydrostatic_pressure_Pa + net_pressure_Pa
```

Conclusao da auditoria: `HydrostaticPlusNetPressure` deve permanecer como
aproximacao provisoria opt-in. Ele nao e acoplamento fisico validado e nao deve
virar default runtime.

Classificacao operacional:

```text
HydrostaticPlusNetPressure:
  status: provisional approximation / opt-in only
  physical validation: not validated
  runtime default: no
  allowed use: controlled studies, chain tests, preliminary approximations
```

O motivo e a referencia fisica de `p_net`. No `PknModel` moderno,
`PknResult.net_pressure_series_Pa` vem de:

```text
p_net = E' * w / h
```

Essa grandeza e uma pressao liquida PKN associada a abertura elastica da
fratura. Ela nao carrega explicitamente:

- `sigma_closure`;
- tensao horizontal minima;
- pressao de poros;
- tensao radial geostatica;
- pressao absoluta de poco por tempo;
- pressao de bombeio/superficie por tempo;
- uma referencia geomecanica completa.

Assim, `p_net` pode ser interpretado como incremento sobre a coluna hidrostatica
somente por hipotese documentada do chamador. Sem essa hipotese, a soma
`p_hydrostatic + p_net` pode misturar uma pressao absoluta local com uma pressao
relativa de fratura.

`SaltCreepQuery.wall_pressure_Pa`, por outro lado, deve representar pressao
compressiva absoluta na parede do sal ou uma condicao radial equivalente bem
definida. Se uma fase futura precisar enviar tensao radial efetiva, pressao
referenciada a closure stress ou historico APB, isso deve aparecer como metodo
nomeado e testado, nao como uso implicito de `HydrostaticPlusNetPressure`.

Status recomendado dos metodos existentes:

| Metodo | Status fisico | Uso recomendado | Limite |
|--------|---------------|-----------------|--------|
| `ExperimentalNetPressureProxy` | Experimental only | Compatibilidade, teste de chamada e transicao | Nao representa pressao fisica de parede. |
| `AbsoluteWellborePressure` | Preferivel quando disponivel | Pressao absoluta de poco/sapata/anular validada | Exige fonte runtime confiavel. |
| `HydrostaticPlusNetPressure` | Provisional approximation / opt-in only | Estudos controlados, testes de cadeia e aproximacoes preliminares | Exige hipotese explicita de `p_net` como incremento operacional sobre a coluna. |

Metodos futuros candidatos:

- `BreakdownReferencedPressure`: quando o incremento for definido contra
  `LotConfig.breakdown_pressure_Pa` ou uma pressao de iniciacao documentada.
- `ClosureReferencedPressure`: quando `sigma_closure` ou tensao minima
  horizontal estiver disponivel no caso.
- `AnnularPressureHistory`: quando APB fornecer pressao anular absoluta por
  tempo e profundidade.
- `EffectiveRadialPressure`: quando o contrato for uma tensao radial efetiva,
  com pressao de poros e convencao de sinal documentadas.

Checklist minima antes de qualquer wiring runtime acoplado:

- pressao absoluta conhecida por tempo e profundidade;
- referencia de tensao clara para qualquer incremento LOT/PKN;
- profundidade de acoplamento definida;
- fluido selecionado e rastreavel;
- pressao de superficie/bombeio definida quando usada;
- convencao de sinal documentada entre LSS e backend de sal;
- closure stress, tensao minima horizontal ou justificativa equivalente;
- pressao de poros quando houver uso de tensao efetiva;
- testes sinteticos dedicados;
- comparacao com legado ou referencia externa quando aplicavel;
- documentacao atualizada antes de tornar qualquer rota default.

## `BreakdownReferencedPressure` candidato futuro (Fase 9.6A)

A Fase 9.6 auditou um metodo futuro para mapear LOT/PKN para a pressao de parede
do sal usando a pressao de breakdown como referencia:

```text
p_wall = p_breakdown + (p_net_current - p_net_at_breakdown)
```

Classificacao operacional:

```text
BreakdownReferencedPressure:
  status: candidate future method
  implementation: not implemented
  runtime default: no
  physical validation: pending
  required data: breakdown_pressure_Pa valid, p_net_at_breakdown or breakdown_step
```

A interpretacao pretendida e:

- `p_breakdown` seria uma referencia absoluta de pressao no evento de abertura
  ou fratura;
- `p_net_current - p_net_at_breakdown` seria o incremento de pressao liquida PKN
  apos a referencia de breakdown;
- a formula preservaria uma referencia LOT mais direta que a soma
  `p_hydrostatic + p_net`, desde que os dados de breakdown sejam fisicamente
  confiaveis.

O metodo ainda nao deve ser implementado como rota runtime porque os dados
necessarios nao existem de forma robusta no projeto atual. Hoje,
`LotConfig.breakdown_pressure_Pa` e parseado de:

```text
lot.fracture.breakdown.pressure
```

e funciona como parametro/threshold de breakdown do contrato de entrada. Ele
nao e uma serie temporal de pressao absoluta do poco/sapata. Alem disso, no
estado atual o PKN moderno calcula:

```text
p_net = E' * w / h
```

independentemente de `breakdown_pressure_Pa` na evolucao de
`PknResult.net_pressure_series_Pa`.

Tambem ainda nao existem em `PknResult`:

- `p_net_at_breakdown`;
- `net_pressure_at_breakdown`;
- `breakdown_step`;
- `breakdown_time_s`;
- `fracture_initiation_step`.

Inferir `p_net_at_breakdown` diretamente da serie atual nao e robusto. A
formulacao PKN moderna ja propaga a partir do tempo ativo e pode usar largura
minima ou pequenos valores numericos que nao correspondem a um evento fisico
claro de breakdown. Uma fase futura precisa definir uma regra testavel para
breakdown antes de usar essa referencia em mapeamento para o sal.

Comparacao com o metodo hidrostatico provisiorio:

| Metodo | Formula | Status | Vantagem | Fraqueza |
|--------|---------|--------|----------|----------|
| `HydrostaticPlusNetPressure` | `p_wall = p_hydrostatic + p_net` | `provisional approximation / opt-in only` | Usa coluna hidrostatica ja derivavel de `CaseData`. | A referencia de `p_net` e ambigua. |
| `BreakdownReferencedPressure` | `p_wall = p_breakdown + (p_net - p_net_at_breakdown)` | Candidate future method | Usa uma referencia LOT de abertura/fratura. | Faltam `p_net_at_breakdown` e evento robusto de breakdown. |

Condicao especial do BUZ67D: `cases/lot_tese_migrated/buz67d_pkn.yaml` nao deve
ser usado como baseline fisico para `BreakdownReferencedPressure` enquanto
mantiver `breakdown_pressure_Pa = 1 Pa` e marcacoes `R09_PENDING_REVIEW`. Esse
valor e placeholder de contrato sintatico e invalida o caso para validar
pressao fisica de breakdown.

Opcoes futuras:

- Fase futura C -- criar helper de evento de breakdown para identificar
  `breakdown_step`, `breakdown_time_s` e `p_net_at_breakdown`, caso a serie PKN
  possa representar esse evento de forma robusta.
- Fase futura D -- adicionar campos explicitos ao `LotSaltPressureMapInput`,
  como `breakdown_pressure_Pa` e `net_pressure_at_breakdown_Pa`, e implementar
  `BreakdownReferencedPressure` apenas como metodo opt-in.
- Fase futura com closure stress -- adiar metodo fisico rigoroso ate existirem
  `sigma_closure`, tensao minima horizontal, pressao de poros e pressao absoluta
  de poco.

`BreakdownReferencedPressure` e especifico para LOT/PKN. Para APB futuro, os
metodos mais adequados continuam sendo candidatos baseados em pressao anular
absoluta por tempo e profundidade, como `AnnularPressureHistory`,
`AbsoluteAnnularWallPressure` ou `AbsoluteWellborePressure`.

## Limitacoes de inferencia de breakdown no PKN atual (Fase 9.7A)

A Fase 9.7 auditou se o fluxo PKN moderno ja permite definir um evento fisico
robusto de breakdown para alimentar metodos referenciados a ruptura. A
conclusao e negativa: o `PknModel` atual nao produz uma rampa pre-breakdown ate
a ruptura nem registra um evento dinamico de iniciacao.

Hoje, `breakdown_pressure_Pa` e parseado de
`lot.fracture.breakdown.pressure`, armazenado em `CaseData.lot` e repassado
para `PknInput.breakdown.pressure_Pa`. Esse valor tambem pode aparecer como
`input.net_pressure_Pa`, mas `PknModel` nao o usa para iniciar a fratura,
detectar ruptura ou calibrar `PknResult.net_pressure_series_Pa`.

Portanto, `p_net_at_breakdown` nao deve ser inferido automaticamente por:

- primeiro `p_net > 0`;
- primeiro `width > tolerancia`;
- primeiro `length > tolerancia`;
- primeiro `volume > tolerancia`;
- `breakdown_pressure_Pa`;
- aplicacao direta de `BreakdownDetector` sobre
  `PknResult.net_pressure_series_Pa`.

Esses criterios sao marcadores numericos ou heuristicos no modelo atual, nao
eventos fisicos robustos de breakdown. Em particular, pequenos valores positivos
de largura ou pressao liquida podem vir de minimos numericos, tempo ativo ou
hipoteses de propagacao ja iniciada, sem corresponder ao instante de ruptura da
formacao.

O `BreakdownDetector` existente continua adequado para curvas pressao-volume
absolutas, observadas ou estimadas, quando a pressao representa a pressao
fisica do poco/sapata. Ele nao deve ser aplicado diretamente a
`PknResult.net_pressure_series_Pa` isolado, porque essa serie e pressao liquida
PKN (`p_net = E' * w / h`), nao pressao absoluta de poco.

Status reforcado para o metodo futuro:

```text
BreakdownReferencedPressure:
  status: candidate future method
  implementation: not implemented
  runtime default: no
  physical validation: pending
  blocked by: missing p_net_at_breakdown / breakdown_step
```

Um caminho futuro conservador seria criar um diagnostico opt-in, separado do
solver e marcado como heuristico enquanto nao houver pressao absoluta ou curva
LOT validada:

```cpp
struct PknBreakdownDiagnostics {
  bool found = false;
  std::size_t step_index = 0;
  double time_s = 0.0;
  double net_pressure_Pa = 0.0;
  std::string method;
  std::string caveat;
};

PknBreakdownDiagnostics diagnose_pkn_breakdown(
    const PknResult& result,
    const PknBreakdownDiagnosticConfig& config);
```

Um diagnostico fisico mais rigoroso exigiria pelo menos uma das referencias
seguintes, idealmente combinadas em contrato explicito:

- pressao absoluta de poco por tempo;
- curva pressao-volume de LOT;
- `closure stress`;
- tensao horizontal minima;
- pressao de poros;
- referencia externa validada para o evento de ruptura.

Enquanto essas referencias nao existirem, futuras rotas de acoplamento nao
devem tratar marcadores numericos do PKN como evento fisico de breakdown.

## Diagnostico experimental por `sigma_theta` em sal (Fase 9.8)

A Fase 9.8 adiciona um diagnostico experimental puro em `coupling/` inspirado
na logica observada no legado `LOT_Tese` para camadas salinas. O objetivo e
comparar uma pressao aplicada contra uma tensao tangencial de referencia ja
convertida para a convencao de compressao positiva:

```text
opened = pressure_Pa > sigma_theta_compression_positive_Pa
margin_Pa = pressure_Pa - sigma_theta_compression_positive_Pa
```

Se `margin_Pa > 0`, o diagnostico indica abertura/quebra experimental naquela
camada ou altura de influencia. Igualdade (`margin_Pa = 0`) nao indica
abertura.

A API recebe explicitamente `sigma_theta_compression_positive_Pa`; ela nao faz
conversao automatica de sinal. Para reproduzir a convencao observada no legado,
quando `getSigmaTheta()` retornar compressao negativa, o chamador deve fornecer:

```text
sigma_theta_compression_positive_Pa = -getSigmaTheta()
```

Essa fase implementa apenas o criterio baseado em `sigma_theta`. O valor
`getDeviatoricStress()` observado no legado permanece candidato futuro para uma
auditoria propria; dano, fluencia terciaria e criterios constitutivos avancados
nao entram nesta implementacao.

O modulo `LotSaltSigmaThetaBreakdown` nao chama `SaltCreepInterface`, nao chama
`LotSaltPressureMap`, nao altera `LotSaltCouplingStep` e nao e conectado ao
CLI. Ele trabalha somente com pressoes e tensoes de referencia ja fornecidas,
em SI, e retorna pontos ordenados por tempo externo e camada interna:

```text
para cada tempo:
  para cada camada:
    avaliar pressure_Pa > sigma_theta_compression_positive_Pa
```

Esse diagnostico nao e acoplamento fisico validado. Ele existe para estudos
controlados, comparacao futura com o legado e preparacao de criterios mais
rigorosos quando `sigma_theta`, historicos absolutos de pressao e referencias
geomecanicas forem disponibilizados por rotas validadas.

## Classificacao explicita de estado hoop `sigma_theta` (Fase 10.5B)

A Fase 10.5B formaliza que `sigma_theta_compression_positive_Pa < 0` nao e
uma resistencia compressiva negativa. Esse valor significa que a tensao
tangencial bruta do saltcreep esta trativa no ponto amostrado:

```text
sigma_theta_compression_positive_Pa = -sigma_theta_Pa
sigma_theta_compression_positive_Pa < 0  <=>  sigma_theta_Pa > 0
```

O diagnostico passa a classificar explicitamente o estado hoop:

```text
sigma_theta_compression_positive_Pa > 0  -> Compressive
sigma_theta_compression_positive_Pa == 0 -> Neutral
sigma_theta_compression_positive_Pa < 0  -> Tensile
```

Para `Compressive`, o comportamento anterior e preservado:

```text
margin_Pa = pressure_Pa - sigma_theta_compression_positive_Pa
opened = margin_Pa > 0
```

Para `Neutral`, a mesma algebra experimental se aplica; pressao zero nao abre
por igualdade, e pressao positiva produz `opened = true`.

Para `Tensile`, o diagnostico nao lanca excecao. O resultado carrega
`hoop_state = Tensile`, `tensile_hoop_state = true`, `legacy_algebra_opened` e
um caveat:

```text
tensile hoop state; legacy algebra only; not a validated fracture criterion
```

Nesse estado, `opened` representa apenas a algebra experimental herdada da
comparacao `pressure > -getSigmaTheta()`. Isso e util para rastrear e comparar
o comportamento historico observado no `LOT_Tese`, no qual um
`getSigmaTheta()` trativo geraria um limiar negativo e qualquer pressao positiva
abriria pela algebra. Nao e uma validacao fisica de fratura do sal.

Essa mudanca tambem remove a necessidade do workaround usado na Fase 10.4: os
testes builder -> bridge -> driver podem manter a `wall_pressure_Pa`
hidrostatica derivada pelo builder e representar o estado trativo resultante
explicitamente, em vez de sobrescrever `bridge_config.wall_pressure_Pa = 0.0`
apenas para evitar uma excecao.

## Diagnostico opt-in de tensao de parede do sal (Fase 9.9B)

A Fase 9.9B cria `SaltWallStressDiagnostics` como DTO publico do
`lot-salt-suite` e adiciona ao `SaltCreepTimeBridge` um metodo opt-in para
expor diagnosticos de tensao na parede:

```text
SaltCreepTimeBridge::wall_stress_diagnostics()
```

Esse metodo usa internamente o estado atual do `TimeIntegrator` do
`external/saltcreep`, em particular `TimeState::sigma_gp`, e amostra os pontos
de Gauss mais proximos da parede interna por meio de `stress_sampler`. Os
headers publicos do `lot-salt-suite` nao expõem `TimeIntegrator`, `TimeState`,
`StressSampler`, `stress_utils`, `types.hpp` ou Eigen.

O diagnostico retorna, para cada amostra de parede:

- identificadores de ponto de Gauss, elemento e ponto local;
- coordenadas `r_m`, `z_m` e `depth_m`;
- `sigma_rr_Pa`, `sigma_theta_Pa`, `sigma_zz_Pa` e `sigma_rz_Pa`;
- `sigma_theta_compression_positive_Pa`;
- `mean_stress_Pa`;
- `j2_Pa2`;
- `von_mises_effective_stress_Pa`.

A conversao de sinal e explicita:

```text
sigma_theta_compression_positive_Pa = -sigma_theta_Pa
```

Isso preserva a fronteira entre a convencao interna do `saltcreep`, onde
compressao no vetor `Stress` aparece negativa nessa rota, e a convencao do LSS
para diagnosticos de abertura por compressao positiva.

Limites deliberados:

- a amostra de "parede" e o ponto de Gauss mais proximo da parede interna, nao
  uma extrapolacao exata para `r = Ri`;
- o diagnostico nao altera `SaltCreepInterface`;
- o diagnostico nao altera `SaltCreepResponse`;
- o diagnostico nao altera `LotSaltSigmaThetaBreakdown`;
- o diagnostico nao e conectado automaticamente ao CLI nem ao fluxo
  `lot-sim run --mode lot-pkn`;
- `deviatoric`, `J2` e von Mises sao expostos como diagnostico, mas nao entram
  no criterio experimental da Fase 9.8.

Essa ponte prepara uma fase futura em que
`sigma_theta_compression_positive_Pa` podera alimentar explicitamente
`LotSaltSigmaThetaBreakdown`, mantendo o criterio `pressure_Pa >
sigma_theta_compression_positive_Pa` opt-in e nao validado como criterio fisico
de fratura.

## Diagnostico end-to-end `sigma_theta` opt-in (Fase 10.1)

A Fase 10.1 cria `LotSaltSigmaThetaDiagnostic` como helper puro em
`coupling/` para conectar, de forma experimental e opcional, os blocos ja
existentes:

```text
PknResult
  -> LotSaltPressureMap
  -> SaltWallStressDiagnostics
  -> LotSaltSigmaThetaBreakdown
  -> diagnostico experimental por sigma_theta
```

O helper recebe explicitamente:

- `PknResult`;
- `LotSaltCouplingConfig`;
- `SaltWallStressDiagnostics`.

Para cada passo PKN, ele monta um `LotSaltPressureMapInput`, chama
`map_lot_pkn_to_salt_wall_pressure()` e usa
`LotSaltPressureMapResult.wall_pressure_Pa` como pressao no criterio
experimental. Para cada amostra de parede, ele cria uma
`SigmaThetaInfluenceLayer` com:

```text
layer_id = wall_gp_<indice>
influence_depth_m = sample.depth_m
sigma_theta_compression_positive_Pa =
    sample.sigma_theta_compression_positive_Pa
```

Em seguida chama `evaluate_sigma_theta_breakdown_point()`. O resultado preserva
metadados do mapeamento de pressao e da amostra de tensao: identificadores de
ponto de Gauss, elemento, ponto local, coordenadas, profundidade, tensao media,
`J2` e tensao efetiva de von Mises.

Limites deliberados:

- o helper nao chama `SaltCreepInterface`;
- o helper nao chama `SaltCreepTimeBridge`;
- o helper nao chama `SaltCreepSaltcreepAdapter`;
- o helper nao inclui headers de `external/saltcreep/`;
- o helper nao altera `LotSaltCouplingStep`;
- o helper nao e chamado por `lot-sim`;
- o fluxo `lot-sim run --mode lot-pkn` permanece desacoplado do sal.

`SaltWallStressDiagnostics` e tratado como snapshot fornecido pelo chamador. A
Fase 10.1 nao garante que esse snapshot esteja sincronizado temporalmente com
cada passo de `PknResult`; essa sincronizacao fica sob responsabilidade do
chamador ou de uma fase futura. Usar o mesmo snapshot para toda a serie PKN e
uma simplificacao experimental, adequada para teste de cadeia e auditoria, mas
nao para validacao fisica.

Classificacao operacional:

```text
LotSaltSigmaThetaDiagnostic:
  status: experimental / opt-in only
  physical validation: not validated
  runtime default: no
  CLI wiring: none
```

Esse diagnostico nao e criterio fisico validado de fratura no sal. Ele apenas
torna rastreavel a comparacao experimental:

```text
wall_pressure_Pa > sigma_theta_compression_positive_Pa
```

com a pressao vindo de `LotSaltPressureMap` e a tensao tangencial vindo do DTO
publico de tensao de parede.

## Driver experimental `LotSaltSigmaThetaDriver` (Fase 10.2B)

A Fase 10.2B cria `LotSaltSigmaThetaDriver` como driver experimental opt-in
para encadear os blocos da cadeia diagnostica a partir de um `CaseData` e de
um `SaltCreepTimeBridge&` ja configurado pelo chamador:

```text
CaseData
  -> make_hydrostatic_lot_salt_coupling_config(data, options)
  -> run_pkn_case(data)
  -> bridge.wall_stress_diagnostics()
  -> evaluate_lot_salt_sigma_theta_series(...)
  -> LotSaltSigmaThetaDriverResult
```

O driver retorna um resultado composto com:

- `PknRun`;
- `LotSaltCouplingConfig`;
- `SaltWallStressDiagnostics`;
- `LotSaltSigmaThetaDiagnosticResult`;
- `valid`;
- `caveat`.

O bridge nao e construido pelo driver. A configuracao de geometria, malha,
material, temperatura, geostatica e pressao inicial do sal permanece
responsabilidade explicita do chamador. Isso evita inferir dados fisicos ainda
ausentes ou ambiguos em `CaseData`.

Limites deliberados:

- o driver nao chama `bridge.advance_to()`;
- o driver nao chama `bridge.advance_by()`;
- o driver nao constroi `SaltCreepTimeBridgeConfig`;
- o driver nao constroi `SaltCreepSaltcreepAdapter`;
- o driver nao chama `SaltCreepInterface`;
- o driver nao chama `SaltCreepSaltcreepAdapter`;
- o driver nao chama `evaluate_lot_salt_step()`;
- o driver nao e chamado por `lot-sim`;
- o fluxo `lot-sim run --mode lot-pkn` permanece desacoplado.

`SaltWallStressDiagnostics` e usado como snapshot unico do estado atual do
bridge. O driver nao garante sincronizacao temporal entre o estado de tensao do
sal e cada passo da serie PKN; essa sincronizacao fica para fase futura. Assim,
a Fase 10.2B ainda nao implementa acoplamento temporal real, acoplamento fisico
validado, dano, fluencia terciaria ou criterio constitutivo avancado.

Classificacao operacional:

```text
LotSaltSigmaThetaDriver:
  status: experimental / opt-in only
  stress policy: single bridge snapshot
  physical validation: not validated
  runtime default: no
  CLI wiring: none
```

## Builder experimental de config do bridge (Fase 10.3)

A Fase 10.3 cria `LotSaltBridgeConfigBuilder` como helper experimental opt-in
para montar um `SaltCreepTimeBridgeConfig` a partir de `CaseData` e de opcoes
explicitas do chamador:

```text
CaseData + LotSaltBridgeConfigOptions -> SaltCreepTimeBridgeConfig
```

O helper nao constroi `SaltCreepTimeBridge` e nao avanca o bridge. Ele apenas
prepara uma configuracao rastreavel para testes e fases futuras.

Regras implementadas:

- a profundidade de referencia e `data.lot.shoe_depth_m`;
- a layer usada e a unica que contem a sapata;
- a rocha vem de `layer.rock_id`;
- `elastic_modulus_Pa` e `poisson_ratio` vêm da rocha selecionada;
- `inner_radius_m`, `outer_radius_m` e `radial_elements` vêm de
  `LotSaltBridgeConfigOptions`;
- `height_m = data.lot.fracture_height_m`;
- `wall_pressure_Pa` inicial vem de `LotSaltHydrostaticContext`;
- `temperature_K` vem de options;
- geostatica nao e inferida de `CaseData`.

`height_m = lot.fracture_height_m` e uma aproximacao experimental: altura PKN
ou altura de fratura nao e necessariamente a altura fisica do dominio salino.
A escolha foi feita apenas para remover hardcode dos testes e preparar uma
ponte rastreavel para a proxima fase.

Se `geostatic_enabled=true` for solicitado nas options, o helper rejeita a
configuracao nesta fase, porque `CaseData` ainda nao fornece tensoes
geostaticas completas e as options ainda nao carregam esses campos. O helper
tambem nao usa perfil termico de `CaseData`; a temperatura permanece explicita
em options ate existir persistencia termica apropriada.

Classificacao operacional:

```text
LotSaltBridgeConfigBuilder:
  status: experimental / opt-in only
  output: SaltCreepTimeBridgeConfig
  builds bridge: no
  advances bridge: no
  geostatic inference: no
  runtime default: no
  CLI wiring: none
```

O fluxo `lot-sim run --mode lot-pkn` permanece desacoplado. A Fase 10.3 nao
implementa driver temporal, acoplamento fisico validado, dano, fluencia
terciaria nem criterio constitutivo avancado.

## Geostatica explicita no bridge config builder (Fase 10.4)

A Fase 10.4 expande `LotSaltBridgeConfigOptions` para aceitar tensoes
geostaticas explicitas:

```text
geostatic_enabled
geostatic_radial_stress_Pa
geostatic_hoop_stress_Pa
geostatic_vertical_stress_Pa
```

Esses valores vêm exclusivamente de options. A fase nao infere geostatica de
`CaseData`, nao calcula tensao litostatica automaticamente e nao altera parser,
YAML ou schema. Quando `geostatic_enabled = true`, o builder preenche
`SaltCreepTimeBridgeConfig` com as tres tensoes fornecidas e marca
`fix_outer_wall = true`, porque essa aproximacao de confinamento externo exige
fronteira externa restringida no bridge.

Quando `geostatic_enabled = false`, o comportamento default da Fase 10.3 e
preservado: tensoes geostaticas zeradas, geostatica desabilitada e
`fix_outer_wall = false`.

A Fase 10.4 tambem adiciona testes integrados da cadeia:

```text
CaseData
  -> make_lot_salt_bridge_config(data, options)
  -> SaltCreepTimeBridge
  -> run_lot_salt_sigma_theta_experimental(data, bridge)
```

Esses testes cobrem a cadeia sem geostatica e com geostatica explicita. O driver
continua usando snapshot unico de tensao de parede, nao avanca o bridge e nao
sincroniza temporalmente tensao do sal com cada passo PKN.

Ressalva historica: antes da Fase 10.5B, os testes integrados precisavam
sobrescrever `bridge_config.wall_pressure_Pa = 0.0` para evitar que a pressao
hidrostatica derivada pelo builder gerasse
`sigma_theta_compression_positive_Pa < 0` e fosse rejeitada pelo diagnostico.
Com a classificacao explicita de estado hoop, esse workaround nao e mais
necessario: o estado trativo e representado como `Tensile`, com caveat de
algebra legada experimental.

Classificacao operacional:

```text
LotSaltBridgeConfigOptions.geostatic_*:
  status: experimental / opt-in only
  source: explicit options
  CaseData inference: no
  fix_outer_wall when enabled: true
  runtime default: no
```

O fluxo `lot-sim run --mode lot-pkn` permanece desacoplado. A Fase 10.4 nao
implementa acoplamento temporal nem acoplamento fisico validado.

## Contexto litostatico opt-in para geostatica do bridge (Fase 10.6B)

A Fase 10.6B cria `LotSaltLithostaticContext` como helper experimental opt-in
em `coupling/` para derivar uma primeira estimativa litostatica isotropica a
partir de `CaseData` ja parseado:

```text
depth_m = data.lot.shoe_depth_m
layer = unica LayerData tal que top_m <= depth_m <= base_m
rock = RockData referenciada por layer.rock_id
lithostatic_pressure_Pa = rock.density_kg_m3 * g * depth_m
geostatic_stress_Pa = -lithostatic_pressure_Pa
```

O sinal negativo em `geostatic_stress_Pa` segue a convencao da rota atual do
`saltcreep`, na qual compressao geostatica aparece como tensao negativa nos
campos geostaticos do bridge.

O helper tambem fornece:

```text
with_lithostatic_geostatic(options, data)
```

Essa funcao retorna uma copia de `LotSaltBridgeConfigOptions` com:

```text
geostatic_enabled = true
geostatic_radial_stress_Pa = geostatic_stress_Pa
geostatic_hoop_stress_Pa = geostatic_stress_Pa
geostatic_vertical_stress_Pa = geostatic_stress_Pa
```

Isso nao altera `LotSaltBridgeConfigBuilder` automaticamente e nao muda o
default global. A geostatica litostatica so entra se o chamador invocar
explicitamente o helper e passar as options resultantes para
`make_lot_salt_bridge_config()`.

Caveats fisicos:

- a aproximacao e isotropica;
- nao representa tensor in situ real;
- nao inclui tectonica;
- nao inclui pressao de poros;
- nao e closure stress validado;
- nao e criterio fisico final;
- nao identifica automaticamente se a rocha e sal.

Classificacao operacional:

```text
LotSaltLithostaticContext:
  status: experimental / opt-in only
  source: CaseData layer at lot.shoe_depth_m + RockData.density_kg_m3
  formula: rho_rock * g * depth
  geostatic convention: negative compression for saltcreep bridge fields
  runtime default: no
  CLI wiring: none
```

O fluxo `lot-sim run --mode lot-pkn` permanece desacoplado. A Fase 10.6B nao
implementa acoplamento temporal, nao deriva geostatica automaticamente em
runtime e nao valida fisicamente o estado de tensoes do sal.

## Teste integrado opt-in com geostatica litostatica (Fase 10.7)

A Fase 10.7 adiciona um teste integrado end-to-end para a rota experimental
opt-in de geostatica litostatica:

```text
CaseData
-> with_lithostatic_geostatic(...)
-> make_lot_salt_bridge_config(...)
-> SaltCreepTimeBridge
-> run_lot_salt_sigma_theta_experimental(...)
-> LotSaltSigmaThetaDriverResult
```

O teste usa `cases/validation/lot_pkn_minimal.yaml`, aplica
`with_lithostatic_geostatic()` sobre `LotSaltBridgeConfigOptions`, constroi o
bridge e executa o driver sigma-theta experimental. A geostatica usada na
configuracao do bridge segue:

```text
sigma_lithostatic = rho_rock * g * depth
geostatic_stress = -sigma_lithostatic
```

Para o caso minimo, a verificacao esperada usa `rho_rock = 2160 kg/m3` e
`depth = 3000 m`, resultando em aproximadamente `63.547092 MPa` de pressao
litostatica e `-63.547092 MPa` nos tres campos geostaticos do bridge. O teste
tambem verifica `fix_outer_wall = true`.

O teste confirma que:

- o resultado do driver e valido;
- a amostragem de tensao de parede e valida;
- o diagnostico sigma-theta e valido;
- ha pontos diagnosticos com estado hoop rastreavel;
- o bridge nao e avancado pelo driver (`step_count` permanece constante);
- o `caveat` experimental permanece presente.

Essa cobertura continua sendo apenas um teste de encadeamento opt-in. O driver
ainda usa um snapshot unico de tensao, nao chama `bridge.advance_to()` ou
`bridge.advance_by()`, nao sincroniza temporalmente LOT/PKN e sal, nao valida
fratura fisica e nao e chamado por `lot-sim`. O fluxo
`lot-sim run --mode lot-pkn` permanece desacoplado.

## Matriz interna de cenarios sigma-theta (Fase 10.8B)

A Fase 10.8B adiciona uma matriz interna de teste para comparar, no mesmo
`CaseData`, tres cenarios experimentais de confinamento usados pelo diagnostico
sigma-theta:

```text
1. sem geostatica
2. geostatica sintetica explicita
3. geostatica litostatica derivada
```

A matriz usa `cases/validation/lot_pkn_minimal.yaml` e executa a mesma cadeia
experimental opt-in de driver em cada cenario:

```text
CaseData
-> LotSaltBridgeConfigOptions
-> make_lot_salt_bridge_config(...)
-> SaltCreepTimeBridge
-> run_lot_salt_sigma_theta_experimental(...)
```

No cenario sem geostatica, `geostatic_enabled=false`. No cenario sintetico, os
tres campos geostaticos sao definidos explicitamente como `-2 MPa`. No cenario
litostatico, `with_lithostatic_geostatic(...)` calcula a tensao geostatica a
partir de:

```text
geostatic_stress = -rho_rock * g * depth
```

Para cada cenario, a matriz calcula apenas metricas locais ao teste:

```text
compressive_count
neutral_count
tensile_count
min/max sigma_theta_compression_positive_Pa
min/max margin_Pa
any_opened
any_legacy_algebra_opened
```

O objetivo e comparar comportamento diagnostico interno, nao produzir saida de
analise. A Fase 10.8B nao cria exportador CSV/JSON, nao cria pos-processamento,
nao compara com `LOT_Tese`, nao altera o driver, nao avanca o bridge e nao
implementa acoplamento temporal. O diagnostico continua usando snapshot unico
de tensao de parede.

No snapshot atual do backend para o caso minimo, a matriz observou:

```text
sem geostatica: 21 pontos Tensile
geostatica sintetica -2 MPa: sem pontos Compressive
geostatica litostatica: 21 pontos Compressive
```

Esses resultados sao uma caracterizacao do backend/teste atual, nao validacao
fisica de fratura. O fluxo `lot-sim run --mode lot-pkn` permanece desacoplado.

## Writer experimental CSV/JSON sigma-theta (Fase 10.9B)

A Fase 10.9B adiciona um writer experimental opt-in para materializar resultados
do `LotSaltSigmaThetaDriverResult` em arquivos tabulares rastreaveis. O writer
vive em `coupling/` e consome resultados ja calculados pelo driver; ele nao
chama o driver, nao avanca o bridge, nao executa `lot-sim` e nao se conecta ao
`ResultWriter` oficial do simulador.

A API escreve tres arquivos no diretorio escolhido pelo chamador:

```text
points.csv
summary.csv
metadata.json
```

`points.csv` e granular por ponto diagnostico, preservando a ordem
time-major usada pelo diagnostico sigma-theta:

```text
step_index = point_index / n_wall_samples
sample_index = point_index % n_wall_samples
```

As colunas incluem identificacao do caso e cenario, indices de passo/amostra,
metadados do ponto de Gauss, fontes de pressao e tensao, metodo de
`LotSaltPressureMap`, pressao de parede, pressao liquida PKN, termos de
hidrostatica/superficie/poco absoluto presentes na config, estado hoop,
`sigma_theta_compression_positive_Pa`, margem, flags de abertura e invariantes
de tensao (`mean_stress_Pa`, `j2_Pa2`, `von_mises_effective_stress_Pa`).

`summary.csv` agrega cada cenario com:

```text
n_points
n_compressive
n_neutral
n_tensile
min/max sigma_theta_compression_positive_Pa
min/max margin_Pa
any_opened
any_legacy_algebra_opened
first_open_time_s
first_open_pressure_Pa
first_open_layer_id
```

`metadata.json` registra a origem experimental do artefato, `case_id`,
`input_case`, arquivos gerados, cenarios exportados, contagens de passos/amostras
e caveats fornecidos pelo chamador.

O writer valida que:

- `case_id`, `scenario_id` e `scenario_label` nao estao vazios;
- cada cenario tem `result.valid`, `diagnostic.valid` e `wall_stress.valid`;
- as series PKN de tempo e pressao liquida existem e tem o mesmo tamanho;
- existe pelo menos uma amostra de tensao de parede;
- `diagnostic.points.size() == n_steps * n_wall_samples`.

Esta saida e somente um artefato experimental de diagnostico interno. Ela nao e
saida oficial do `lot-sim`, nao compara com `LOT_Tese`, nao cria HTML ou
pos-processamento Python, nao valida fratura fisica e nao altera o fluxo
`lot-sim run --mode lot-pkn`, que permanece desacoplado.

## Exportacao da matriz sigma-theta de tres cenarios (Fase 10.10)

A Fase 10.10 adiciona um teste integrado/exportador controlado que usa o writer
experimental da Fase 10.9B para materializar a matriz de tres cenarios criada
na Fase 10.8B. O teste executa a cadeia opt-in:

```text
CaseData
-> LotSaltBridgeConfigOptions
-> make_lot_salt_bridge_config(...)
-> SaltCreepTimeBridge
-> run_lot_salt_sigma_theta_experimental(...)
-> write_lot_salt_sigma_theta_diagnostics(...)
```

Os tres cenarios exportados sao:

```text
1. sem geostatica
2. geostatica sintetica explicita (-2 MPa)
3. geostatica litostatica derivada por with_lithostatic_geostatic(...)
```

O teste usa `cases/validation/lot_pkn_minimal.yaml`, gera arquivos apenas em
diretorio temporario do teste e verifica:

```text
points.csv
summary.csv
metadata.json
```

`points.csv` deve conter os tres `scenario_id` e estados hoop rastreaveis.
`summary.csv` deve conter uma linha por cenario e as colunas agregadas de
contagem (`n_compressive`, `n_neutral`, `n_tensile`). `metadata.json` registra
`case_id`, `input_case`, arquivos gerados, cenarios exportados e caveats como:

```text
experimental opt-in
single wall-stress snapshot
not physically validated fracture criterion
not LOT_Tese comparison
```

Essa exportacao continua sendo apenas preparacao para comparacao futura com a
tese. Ela nao compara com `LOT_Tese`, nao cria pos-processamento Python, nao
cria HTML, nao altera o formato do writer, nao usa `results/` de producao e nao
conecta nada ao CLI. O fluxo `lot-sim run --mode lot-pkn` segue desacoplado.

## Mapeamento `LOT_Tese` para diagnostico sigma-theta moderno (Fase 10.11B)

A Fase 10.11B formaliza o contrato documental entre o criterio legado observado
em `LOT_Tese` e os campos do diagnostico sigma-theta moderno. Esta fase nao
implementa comparacao numerica, nao instrumenta `legance/`, nao cria parser de
saida legada e nao altera o runtime.

O criterio legado relevante foi localizado em:

```text
legance/LOT_Tese/src/apb_code/APB1da.cpp
APB1da::calculateLOTFracturedSaltRock(...)
```

A forma auditada e:

```text
pw = line_up[lu].pi(idAnnular) + line_up[lu].dP(idAnnular)
sigmaTheta = -line_up[lu].mdl->getSigmaTheta()
margin = pw - sigmaTheta
opened = pw > sigmaTheta
```

`pw` e interpretado como a pressao de poco/anular usada contra a parede/rocha
vizinha. A unidade aparente no bloco legado e Pa. Essa pressao nao e
`PknResult.net_pressure_series_Pa`, nao e apenas pressao liquida de fratura e
nao deve ser confundida com `p_net = E' * w / h`. No legado, `pi` representa a
pressao inicial no anular/camada e `dP` representa o incremento APB/LOT no passo.

O termo `sigmaTheta` vem do caminho:

```text
APBSalt1D::getSigmaTheta()
-> mdl->getElem(0)->getSigmaTheta()

Element::getSigmaTheta()
-> sig(2,0)
```

Portanto, o legado usa o elemento mais interno/proximo da parede no modelo 1D de
sal. Como o criterio aplica `-getSigmaTheta()`, o campo moderno correspondente e:

```text
sigma_theta_compression_positive_Pa = -sigma_theta_raw
```

No diagnostico moderno, essa grandeza deve alimentar
`SigmaThetaInfluenceLayer::sigma_theta_compression_positive_Pa` e os pontos
exportados pelo writer em `sigma_theta_compression_positive_Pa`.

A margem legada:

```text
dP_leakoff = pw - sigmaTheta
```

corresponde conceitualmente a `margin_Pa`. A condicao:

```text
pw > sigmaTheta
```

corresponde a `opened` e `legacy_algebra_opened`. Essa equivalencia e apenas
algebra legada/experimental. Ela nao constitui criterio fisico moderno validado
de fratura no sal.

Camada, profundidade e altura de influencia tambem tem correspondentes apenas
parciais. No legado:

```text
line_up[lu]                  -> camada/subdivisao vertical
line_up[lu].depth_influence  -> profundidade no centro da altura de influencia
line_up[lu].thickness        -> espessura/altura de influencia
```

No diagnostico moderno, os campos existentes sao `layer_id`,
`wall_stress_depth_m`, `depth_m`, `gp_id`, `element_id` e `local_gp_id`. Esses
campos rastreiam o ponto de amostragem do bridge/saltcreep, mas ainda nao sao
equivalentes plenos a `line_up[lu].depth_influence` e
`line_up[lu].thickness`.

O tempo tambem exige cuidado. O legado chama `checkPwAndSaveTime()` no primeiro
instante em que `pw > sigmaTheta`, armazenando `firstTimePwExceedsSigmaMin = t`.
Depois, em formulas de fratura, aparece:

```text
time = t - firstTimePwExceedsSigmaMin
```

Antes de qualquer comparacao numerica, a unidade temporal precisa ser auditada e
normalizada. O historico FA01 registra uso interno em `[1/min]` em trechos do
legado, enquanto o diagnostico moderno exporta `time_s`.

O bloco legado tambem chama:

```cpp
getDeviatoricStress()
```

mas esse valor nao controla diretamente o `if (pw > sigmaTheta)`. Em fases
futuras, ele pode ser relacionado aos campos modernos de invariantes:

```text
getDeviatoricStress()
-> stress_utils::deviatoric_stress(...)
-> j2_Pa2
-> von_mises_effective_stress_Pa
```

Essa relacao permanece diagnostica/futura, nao criterio principal desta fase.

As saidas legadas identificadas em `APB1da::saveFile(...)` incluem:

```text
Time
Layer
dT
dP
dV
u
Compressibilidade
C_Exp
Vq
dV_leakoff
V_outflow
```

Lacuna critica: o legado calcula `pw`, `sigmaTheta`, `margin` e `opened`, mas
nao exporta diretamente esses campos no arquivo `.dat` principal identificado.

| Campo legado | Descricao | Campo moderno sugerido | Disponivel hoje? | Transformacao necessaria | Observacoes |
|---|---|---|---|---|---|
| `pw = pi + dP` | Pressao de poco/anular usada contra a parede/rocha vizinha | `wall_pressure_Pa` ou `pressure_Pa` | Parcial | Somar `pi` e `dP`; garantir Pa | Nao e `p_net` PKN |
| `sigmaTheta = -getSigmaTheta()` | Tensao tangencial convertida para compressao positiva | `sigma_theta_compression_positive_Pa` | Sim, no diagnostico moderno | Inverter sinal do valor bruto se compressao vier negativa | Vem de `getElem(0)` no legado |
| `pw - sigmaTheta` | Margem de abertura/leakoff | `margin_Pa` | Sim | `pressure_Pa - sigma_theta_compression_positive_Pa` | Igualdade nao abre |
| `pw > sigmaTheta` | Abertura segundo algebra legada | `opened` / `legacy_algebra_opened` | Sim | Comparacao estrita `margin_Pa > 0` | Nao e criterio fisico validado |
| `line_up[lu]` | Camada/subdivisao vertical do legado | `layer_id` | Parcial | Mapear indice legado para camada/ponto moderno | Ainda sem correspondencia direta |
| `depth_influence` | Centro da altura de influencia | `depth_m` / `wall_stress_depth_m` | Parcial | Comparar profundidades apos definir tolerancia | Ponto moderno e Gauss/snapshot |
| `thickness` | Espessura/altura de influencia | `height_m` futuro / `influence_height_m` futuro | Nao | Criar campo/contrato futuro se necessario | Nao equivale automaticamente a `lot.fracture_height_m` |
| `t` / `timeResults` | Tempo do legado | `time_s` | Parcial | Confirmar unidade e converter para segundos | FA01 torna isso obrigatorio |
| `dV_leakoff` | Volume de leakoff/fratura acumulado no balanco | Campo futuro de leakoff/fracture output | Parcial | Normalizar fator geometrico e unidade | O legado escreve `dV_leakoff * 2*pi` |
| `getDeviatoricStress()` | Tensão desviadora disponivel no legado | `j2_Pa2` / `von_mises_effective_stress_Pa` | Sim no diagnostico moderno | Recalcular invariantes com convencao moderna | Nao controla o criterio `pw > sigmaTheta` |

Antes de qualquer comparacao com `LOT_Tese`, ficam registradas as lacunas:

- `LOT_Tese` nao exporta diretamente `sigmaTheta`, `pw`, `margin` ou `opened`.
- A unidade temporal precisa ser confirmada e normalizada.
- `LOT_APB_v5` exporta pressao em psi em JSON; o diagnostico moderno usa Pa.
- `getElem(0)` e a amostra mais interna/proxima da parede, nao extrapolacao
  exata para a parede.
- `wall_gp_*` moderno ainda nao equivale automaticamente a layer fisica/altura
  de influencia do legado.
- `height_m = lot.fracture_height_m` nao equivale automaticamente a
  `line_up[lu].thickness`.
- Comparacao numerica direta exigira extractor legado, instrumentacao
  controlada ou comparacao limitada aos campos ja exportados.

## Extrator read-only de outputs legados (Fase 10.12B)

A Fase 10.12B cria uma ferramenta nao-runtime em
`tools/extract_legacy_lot_outputs.py` para ler outputs existentes do
`LOT_Tese` e do `LOT_APB_v5` sem modificar `legance/`, sem instrumentar o
legado e sem conectar nada ao CLI moderno. A ferramenta materializa uma
representacao intermediaria para comparacao futura, mas nao compara
numericamente com o diagnostico sigma-theta moderno nesta fase.

O extrator aceita arquivos individuais ou diretorios:

```text
python tools/extract_legacy_lot_outputs.py --input legance/LOT_Tese/results/8-BUZ-67D-PKN.dat --output-dir results/legacy_extract/8-BUZ-67D-PKN
python tools/extract_legacy_lot_outputs.py --input legance/LOT_Tese/results --output-dir results/legacy_extract/LOT_Tese
```

A saida e sempre composta por:

```text
legacy_points.csv
legacy_summary.csv
legacy_metadata.json
```

Para arquivos `.dat` do `LOT_Tese`, o parser le os blocos textuais exportados
por `APB1da::saveFile(...)`:

```text
Time
Layer
dT
dP
dV
u
Compressibilidade
C_Exp
Vq
dV_leakoff
V_outflow
Momento da quebra
```

O formato legado e tratado como matriz por bloco: cada `Layer` ativa o indice
1-based da camada, o campo seguinte define o tipo de registro e as linhas
seguintes sao expandidas contra a serie `Time`. A unidade de tempo permanece
`unknown` quando nao for inequívoca; por isso `time_s` nao e inferido para
`.dat` nesta fase. `Momento da quebra` e preservado como escalar bruto.

Para JSONs do `LOT_APB_v5`, o extrator le `annuli[*].results_by_time[*]` de
forma tolerante e extrai, quando presentes:

```text
pressure.start
pressure.final
pressure.diff
pressure.APB
volume.start
volume.final
volume.diff
vented_bbl
leakage_bbl
leakage_mass
salt_displacement
```

As pressoes do `LOT_APB_v5` sao interpretadas como psi e convertidas para Pa
com:

```text
1 psi = 6894.757293168 Pa
```

O `legacy_metadata.json` registra os grupos de campos:

```text
directly_comparable:
  Time, Layer, dP, dV, dV_leakoff, V_outflow

requires_transformation:
  Time -> time_s
  Layer -> layer_id/depth mapping
  pressure psi -> Pa
  dV_leakoff -> metric only, not opened

missing_without_instrumentation:
  pw, sigmaTheta, margin, opened, hoop_state, j2, von_mises
```

Os campos `pw`, `sigmaTheta`, `margin` e `opened` continuam ausentes nos
outputs existentes e sao marcados como nao disponiveis no resumo. O extrator
nao tenta reconstruir `pw = pi + dP`, nao calcula `sigmaTheta`, nao calcula
`margin` e nao infere `opened`. Essa decisao evita transformar um artefato de
auditoria em uma instrumentacao fisica implícita.

Esta fase tambem nao altera `ResultWriter`, `apps/lot-sim.cpp`, parser,
`CaseData`, YAMLs, schemas, LOT/APB, `external/saltcreep/`, `legacy/`,
`legance/`, baselines ou postprocess. A saida e intermediaria e serve apenas
como preparacao para uma comparacao futura controlada.

A estrategia de comparacao entre esses outputs legados e os artefatos modernos
do diagnostico sigma-theta esta formalizada em
`docs/14_comparison_strategy.md`.

## Comparacao estrutural Nível 0 com fixtures (Fase 10.14A)

A Fase 10.14A adiciona a primeira comparacao executavel da estrategia
legado-moderno, ainda limitada a fixtures Python temporarios. O teste
`tests/python/test_compare_legacy_modern_level0.py` cria `legacy_points.csv`,
`legacy_summary.csv`, `modern_points.csv` e `modern_summary.csv` dentro de um
diretorio temporario e valida apenas metricas estruturais:

```text
n_records
n_times
time_min/time_max brutos
n_layers
n_points modernos
n_steps modernos
amostras modernas por step
```

Essa comparacao e deliberadamente estrutural. Ela nao processa outputs reais
grandes de `legance/LOT_Tese/results/`, nao escreve em `results/`, nao altera
o extrator read-only e nao declara validacao fisica.

Os caveats obrigatorios permanecem parte do contrato:

```text
legacy time unit is unknown
legacy Layer is 1-based and not equivalent to wall_gp_*
sigmaTheta is not exported by legacy output
pw is not exported by legacy output
margin is not exported by legacy output
opened is not exported by legacy output
comparison is structural only, not physical validation
```

Portanto, a Fase 10.14A nao compara `sigmaTheta`, `pw`, `margin`, `opened`,
`hoop_state`, `j2`, von Mises, dano ou fratura. A rota apenas congela o
contrato minimo para uma futura ferramenta
`tools/compare_legacy_modern_level0_level1.py`.

## Comparacao Nível 0 com dados reais reduzidos (Fase 10.14B)

A Fase 10.14B complementa o contrato da Fase 10.14A com um par pequeno de
fixtures versionados em `tests/fixtures/comparison/`:

```text
legacy_buz67d_sample.dat
legacy_score_mro28_sample.json
modern_buz67d_sample.csv
README.md
```

O lado legado representa recortes reais reduzidos de
`legance/LOT_Tese/results/8-BUZ-67D-PKN.dat` e
`legance/LOT_APB_v5/SCORE-MRO-28_output.json`. O lado moderno representa um
recorte real reduzido de `lot-sim run --mode lot-pkn` para o caso BUZ67D
migrado. Esses arquivos nao sao baselines fisicos; sao apenas amostras
estruturais pequenas para testar o contrato Nível 0.

A comparacao continua restrita a contagens, faixas de tempo brutas, camadas ou
amostras e caveats obrigatorios. Ela nao compara `sigmaTheta`, `pw`, `margin`,
`opened`, `hoop_state`, `j2`, von Mises, dano ou fratura, e nao declara
validacao fisica legado-moderno.

## Normalizacao documental de campos legado-moderno (Fase 10.14C)

A Fase 10.14C adiciona `tests/fixtures/comparison/field_mapping_level0.json`
como contrato documental testavel para os campos de comparacao Nível 0. Essa
fase nao altera `coupling/`, nao altera o bridge, nao altera o driver
sigma-theta e nao cria validacao fisica LOT/APB/sal.

A unidade temporal do `Time` legado permanece classificada como
`BLOCKED_UNKNOWN_UNIT`: o valor deve continuar raw e nao deve ser comparado
numericamente contra `time_s` moderno. `Layer` legado permanece um indice
1-based nao equivalente a `wall_gp_*`, e `dP` legado permanece semanticamente
ambíguo frente a `net_pressure_Pa`.

Os campos `sigmaTheta`, `pw`, `margin` e `opened` seguem fora da comparacao
legacy-modern ate que existam exportacoes auditaveis nos dois lados. Portanto,
esta normalizacao e documental/estrutural e nao valida o acoplamento fisico.

## Evidence gate temporal legado-moderno (Fase 10.14D)

A Fase 10.14D registra uma normalizacao temporal documental para a comparacao
legacy-modern. Por contexto fornecido pelo autor da tese, `APB1da` usa minutos
para `dt`, `ttime` e para o campo `Time` exportado nos `.dat` LOT_Tese. A
conversao permitida e:

```text
time_s = Time_raw * 60.0
```

Essa decisao fica registrada em `docs/15_field_normalization.md`,
`tests/fixtures/comparison/field_mapping_level0.json` e
`tests/fixtures/comparison/level1_readiness_gate.json`.

O status da rota e:

```text
LEVEL1_TIME_UNIT_RESOLVED_CASE_EQUIVALENCE_PENDING
```

Nos fixtures reduzidos atuais, o legado cobre `0..12.5 min`, equivalente a
`0..750 s`, enquanto o recorte moderno cobre `0..420 s`. Portanto, a unidade
temporal esta resolvida, mas a equivalencia de caso/duracao ainda nao esta. A
Fase 10.14D nao compara `sigmaTheta`, `pw`, `margin`, `opened`, `hoop_state`,
`j2`, von Mises, dano, fratura, nem `dP` legado contra `net_pressure_Pa`
moderno. Tambem nao altera `coupling/`, parser, `CaseData`, CLI ou
`lot-sim run --mode lot-pkn`.

## Caso BUZ67D/PKN controlado legacy-aligned (Fase 10.14EF)

A Fase 10.14EF extrai parametros legados em modo somente leitura e cria um novo
YAML moderno controlado:

```text
cases/validation/buz67d_pkn_legacy_aligned.yaml
```

O caso original `cases/lot_tese_migrated/buz67d_pkn.yaml` nao e alterado. O
novo YAML e classificado como `CONTROLLED_EQUIVALENT` porque tempo, injecao,
geometria, fluido, formacao/sal e identificacao PKN foram localizados no main
legado hard-coded `legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp`.

O campo temporal usado no YAML novo e:

```text
lot.injection.schedule.total_time = 12.5 min
time.total_h = 0.2083333333
```

equivalente a `750 s`. A fase valida o YAML com `lot-sim validate`, mas nao
executa `lot-sim run` no caso novo e nao habilita comparacao fisica. O gate
permanece:

```text
level1_ready = false
physical_validation = false
numeric_equivalence = false
```

## Interface proposta para coupling/

```cpp
// include/coupling/LotApbSaltCoupling.hpp
class LotApbSaltCoupling {
public:
    struct Config {
        double tol_pressure_Pa;
        int max_iterations;
        bool salt_enabled;
        bool lot_enabled;
        bool apb_enabled;
    };

    // Executa um passo de tempo acoplado
    void step(double dt_s, const Config& cfg);

private:
    // Referências para módulos físicos
    WellboreGeometry& wellbore_;
    FluidProperties& fluids_;
    ThermalField& thermal_;
    SaltCreepInterface& salt_;
    LotSolver& lot_;
    ApbSolver& apb_;
};
```

## Contrato PKN/saltcreep

O `coupling/` nao deve conhecer detalhes internos do PKN legado nem do FEM de
sal. O fluxo esperado e:

1. `lot/` calcula pressao, breakdown, abertura/comprimento PKN e volume de
   leakoff/fratura.
2. `coupling/` transforma a pressao anular/LOT em condicoes de contorno para sal.
3. `SaltCreepSaltcreepAdapter` delega para o `external/saltcreep/`, usando
   mecanismos existentes de pressao de parede quando aplicaveis.
4. O retorno do sal atualiza deslocamento radial assinado, fechamento radial
   positivo, volume anular e diagnosticos de dano.
5. `apb/` atualiza pressao anular a partir do volume e compressibilidade.

Na Fase 7.0, somente o `NullSaltCreepInterface` existe. Ele valida entradas SI
e retorna resposta neutra valida (`u_r = 0`, `strain = 0`,
`effective_closure_pressure_Pa = 0`) com `is_available() = false`, para deixar
claro que o solver real ainda nao esta conectado.
Na Fase 7.1, o contrato passou a expor tambem `radial_closure_m = 0` na
resposta neutra. Para respostas reais futuras, `radial_displacement_m < 0`
significa fechamento para dentro e `radial_closure_m = max(0,
-radial_displacement_m)` deve ser usado por calculos que esperam magnitude
positiva de fechamento.
Na Fase 7.2, `SaltCreepSaltcreepAdapter` implementa a mesma interface, mas
permanece neutro e indisponivel enquanto a configuracao completa do backend
(malha, material, temperatura, geostatica, pressao de parede e integrador) nao
for formalizada.
Na Fase 7.3, a rota C++ direta do backend foi validada apenas para um caso
elastico controlado em target Catch2 separado. Isso reduz risco de integracao,
mas nao autoriza acoplamento LOT/sal nem mudanca em `PknModel`.
Na Fase 7.4, `TimeIntegrator` tambem foi exercitado em target Catch2 separado
com campo termico constante neutro, vetor geostatico simplificado e pressao de
parede constante. Isso confirma uma rota controlada para tempo/geostatica, mas
continua fora do `coupling/` e nao muda o status neutro do adapter.
Na Fase 7.5, `SaltCreepAdapterConfig` e `SaltCreepAdapterState` foram
adicionados como fronteira C++ testada para geometria, malha, material,
termico, geostatica, tempo e pressao inicial de parede. O adapter continua sem
chamar o backend real: `evaluate_wall_response()` permanece neutro e
`is_available()` permanece `false`.
Na Fase 7.6, o adapter passou a chamar uma rota elastica/geostatica minima do
backend `external/saltcreep`, ainda isolada. `is_available()` agora indica que
a configuracao e suportada por essa superficie minima. Isso nao conecta
LOT/PKN/APB ao sal e nao altera `PknModel` ou `lot-sim run --mode lot-pkn`.
Na Fase 7.7, o adapter passou a persistir os objetos dessa superficie minima
entre queries, mas `TimeIntegrator` continua fora do target principal por
fronteira de includes entre `external/saltcreep/include/io/CaseParser.hpp` e
`include/io/CaseParser.hpp`. Portanto, ainda nao ha acoplamento temporal real
de fluencia nem chamada do sal pelo fluxo LOT/PKN/APB.
Na Fase 7.8, `SaltCreepTimeBridge` passou a compilar e executar
`TimeIntegrator::advance()` em target isolado com include boundary controlada.
Isso resolve a prova tecnica do integrador temporal, mas ainda nao conecta o
bridge ao adapter principal nem ao fluxo LOT/PKN/APB.
Na Fase 7.9, o `SaltCreepSaltcreepAdapter` passou a consumir esse bridge
temporal internamente. Ainda assim, `lot-sim run --mode lot-pkn`, `PknModel`,
`PknRunner`, APB e `coupling/` continuam sem instanciar o adapter de sal.
Na Fase 8.0, o bridge e o adapter passaram a aceitar pressao de parede dinamica
por query temporal. Isso remove a restricao artificial de pressao constante no
adapter, mas nao implementa acoplamento LOT/APB/sal: nenhuma pressao PKN ou APB
e encaminhada automaticamente para o sal, e `coupling/` continua planejado.
Na Fase 8.1, foi adicionada uma prova automatizada de substitutibilidade:
executar LOT/PKN com `NullSaltCreepInterface` presente ou com
`SaltCreepSaltcreepAdapter` real construido, mas ocioso, gera resultados
identicos. A comparacao cobre `PknResult`, `result.json` e `timeseries.csv` com
igualdade exata para os casos LOT/PKN minimo e com leakoff. O adapter permanece
sem chamadas (`backend_build_count() == 0`), confirmando que a presenca do sal
no binario nao altera o caminho LOT/PKN nesta fase.
Na Fase 9.0, o primeiro ponto experimental de injecao foi criado em
`include/coupling/LotSaltCouplingStep.hpp` e `src/coupling/LotSaltCouplingStep.cpp`.
A funcao `evaluate_lot_salt_step(pkn_result, step_index, config, salt)` constroi
uma `SaltCreepQuery` a partir de um passo da serie temporal de `PknResult` e
chama `salt.evaluate_wall_response()`. O teste com `SpySaltCreepInterface` prova
`call_count() == 1`, tornando o ponto de injecao semanticamente verificado por
contraste com a Fase 8.1 (onde `call_count() == 0`). Esta fase e feedforward:
nao retroalimenta PKN, nao altera `PknResult`, nao conecta APB ao sal e nao
implementa acoplamento fisico completo.

**Atencao fisica:** `net_pressure_series_Pa[step_index]` e usado como
`wall_pressure_Pa` apenas como sinal experimental. Ele nao representa a pressao
anular real de parede no sal; o mapeamento fisico correto fica pendente.

O caminho `lot-sim run --mode lot-pkn` segue desacoplado. `PknRunner`,
`PknModel`, `CaseParser`, `ResultWriter` e `apps/lot-sim.cpp` nao foram alterados.

## Gate runtime para critério sigma-theta no LOT/PKN — Fase 10.18D

**Gate:** `SIGMA_THETA_AVAILABLE_DIAGNOSTIC_ONLY`.

A Fase 10.18D auditou se o critério sigma-theta moderno poderia ser usado como
gatilho runtime de fratura no modo `volumetric_balance`, substituindo o
placeholder `fracture.breakdown.pressure = 1 Pa` do caso BUZ67D controlado.

O critério legado documentado é:

```text
pw = line_up[lu].pi(idAnnular) + line_up[lu].dP(idAnnular)
sigmaTheta = -line_up[lu].mdl->getSigmaTheta()
margin = pw - sigmaTheta
opened = pw > sigmaTheta
```

No contrato moderno, o campo equivalente de tensão é:

```text
sigma_theta_compression_positive_Pa
```

e o cálculo de margem/abertura já existe em
`evaluate_sigma_theta_breakdown_point(...)`:

```text
margin_Pa = pressure_Pa - sigma_theta_compression_positive_Pa
legacy_algebra_opened = margin_Pa > 0
opened = legacy_algebra_opened
```

### Resultado da auditoria

| Campo/Função | Arquivo | Papel | Pode ser reutilizado no runtime? | Status |
|---|---|---|---|---|
| `stress_utils::sigma_theta_compression_positive(...)` | `external/saltcreep/include/physics/stress_utils.hpp` | Converte `sigma[1]` para compressão positiva por `-sigma_theta`. | Não diretamente; fica atrás do bridge/adapters. | `EXTRACTED` |
| `SaltWallStressSample::sigma_theta_compression_positive_Pa` | `include/salt/SaltWallStressDiagnostics.hpp` | DTO moderno da amostra de parede. | Não pelo fluxo LOT/PKN atual. | `DIAGNOSTIC_ONLY` |
| `SaltCreepTimeBridge::wall_stress_diagnostics()` | `src/salt/SaltCreepTimeBridge.cpp` | Amostra pontos de Gauss próximos da parede a partir do estado do saltcreep. | Não é chamado por `lot-sim run --mode lot-pkn`. | `DIAGNOSTIC_ONLY` |
| `evaluate_sigma_theta_breakdown_point(...)` | `src/coupling/LotSaltSigmaThetaBreakdown.cpp` | Calcula `margin_Pa`, `legacy_algebra_opened` e `opened`. | Reutilizável conceitualmente, mas sem dados de tensão no runtime LOT/PKN. | `PARTIALLY_EXTRACTED` |
| `run_lot_salt_sigma_theta_experimental(...)` | `src/coupling/LotSaltSigmaThetaDriver.cpp` | Encadeia `CaseData`, bridge, PKN e diagnóstico sigma-theta. | Apenas helper opt-in de teste/diagnóstico. | `DIAGNOSTIC_ONLY` |
| `PknModel::apply_volumetric_balance(...)` | `src/lot/PknModel.cpp` | Calcula `wellbore_pressure_Pa` e aplica sinks após abertura. | Runtime LOT/PKN, mas não conhece sal/bridge/sigma-theta. | `RUNTIME_ACCESSIBLE` |

### Pressão correta para o critério

O legado compara `pw = pi + dP` contra `sigmaTheta`; portanto, no moderno a
pressão candidata correta seria:

```text
wellbore_pressure_Pa
```

e não:

```text
net_pressure_Pa
```

No modo `volumetric_balance`, `wellbore_pressure_Pa` inclui
`initial_pressure_Pa` mais o incremento acumulado do balanço anular. O
diagnóstico sigma-theta experimental, porém, é construído a partir de
`LotSaltPressureMap` e do `PknResult` em `coupling/`; ele não é parte do cálculo
runtime de `PknModel`.

### Ponto de influência

O legado usa a tensão tangencial na altura de influência da camada. O moderno
possui metadados de amostra como:

```text
wall_gp_*
gp_id
element_id
local_gp_id
wall_stress_depth_m
```

mas o caminho runtime não possui uma regra validada para escolher, a cada passo,
o ponto sigma-theta mais próximo de `profTeste = 4374 m` ou da altura de
influência legada. A classificação da Fase 10.18D é:

```text
INFLUENCE_POINT_PARTIALLY_MAPPED
```

O fallback `first_wall_sample` existe apenas como padrão diagnóstico em testes
e não deve ser usado silenciosamente como critério runtime de fratura.

### Decisão

A implementação runtime foi bloqueada nesta fase. O motivo não é ausência do
campo `sigma_theta_compression_positive_Pa`, mas ausência de uma fronteira
runtime segura:

```text
lot-sim run --mode lot-pkn
  nao instancia SaltCreepTimeBridge
  nao coleta SaltWallStressDiagnostics
  nao sincroniza estado de sal por passo
  nao mapeia altura de influencia para wall_gp_*
  nao fornece sigma-theta ao PknModel
```

Assim, conectar o critério agora exigiria uma das duas ações indesejadas:

1. fazer `lot/` depender de `coupling/`/`salt/`; ou
2. duplicar a álgebra de `LotSaltSigmaThetaBreakdown` dentro do solver LOT.

Ambas foram rejeitadas. O status correto da Fase 10.18D é:

```text
SIGMA_THETA_AVAILABLE_DIAGNOSTIC_ONLY
```

Próxima etapa recomendada: criar uma fase de arquitetura opt-in para um
orquestrador runtime LOT/sal que possa fornecer ao balanço volumétrico uma
fonte explícita de `SigmaThetaInfluenceLayer`, sem alterar o default
`lot-sim run --mode lot-pkn`.

## Threshold estático legado para breakdown — Fase 10.18E

A Fase 10.18E calibra de forma diagnóstica o valor de
`fracture.breakdown.pressure` usando o audit legado existente. O objetivo foi
testar se um threshold estático extraído do `LOT_Tese` melhoraria o modo
`volumetric_balance`, sem conectar `sigma_theta_compression_positive_Pa` ao
runtime e sem alterar o default `pkn_direct`.

Fonte da evidência:

```text
results/comparison/level1_buz67d/legacy_audit/buz67d_audit_timeseries.csv
results/comparison/level1_buz67d/legacy_audit/legacy_native_output.dat
Momento da quebra: 8.5
```

O marcador legado indica `8.5 min = 510 s`. A linha usada no CSV foi a de maior
`pw_Pa` no instante do evento:

| Campo | Valor |
|---|---:|
| `layer` | `16` |
| `annular_index` | `1` |
| `pw_Pa` absoluto | `67342521.84592447 Pa` |
| `dP` legado | `8131435.236221395 Pa` |
| volume injetado | `0.67569475 m3` |

O artefato de extração registra ambos os valores:

```text
breakdown_pressure_Pa       = 67342521.84592447
breakdown_delta_pressure_Pa = 8131435.236221395
modern_static_threshold_Pa  = 8131435.236221395
```

O caso moderno criado é:

```text
cases/validation/buz67d_pkn_legacy_static_breakdown.yaml
```

Ele usa `fracture.breakdown.pressure = 8131435.236221395 Pa` porque o
`PknModel` atual interpreta esse campo como limiar incremental acima de
`initial_pressure_Pa`. Usar o `pw_Pa` absoluto diretamente mudaria a semântica
do campo e misturaria pressão absoluta legada com o contrato incremental
moderno.

Resultado da comparação diagnóstica:

| Modo | Máxima pressão | Diferença contra legado | Observação |
|---|---:|---:|---|
| `LOT_Tese` auditado | `69.035836 MPa` | `0.000` | referência `pw_Pa` |
| 10.18B | `82.129237 MPa` | `+0.190` | pressão inicial + shut-in |
| 10.18C | `26.732215 MPa` | `-0.613` | sink com placeholder simplificado |
| 10.18E | `26.732215 MPa` | `-0.613` | `STATIC_BREAKDOWN_OPENED_TOO_EARLY` |

A primeira abertura/sink no moderno ocorreu em `30 s`, enquanto o marcador
legado de quebra está em `510 s`. Portanto, a Fase 10.18E demonstra que uma
calibração estática de `fracture.breakdown.pressure` não é suficiente para
reproduzir o critério legado por `sigmaTheta`.

Status correto:

```text
PHASE10_18E_STATIC_LEGACY_BREAKDOWN_DIAGNOSTIC_COMPLETE
physical_validation: false
sigma_theta_runtime: false
classification: STATIC_BREAKDOWN_OPENED_TOO_EARLY
```

Essa fase não valida fratura, dano, ruptura, sal ou equivalência quantitativa.
Ela apenas documenta um threshold rastreável e confirma que a próxima evolução
deve tratar a rota sigma-theta/influence-height, não apenas ajustar um número
estático no YAML.

## Arquitetura opt-in `sigma_theta_static` no LOT/PKN — Fase 10.19A

A Fase 10.19A criou uma ponte arquitetural mínima para que o runtime LOT/PKN
possa receber um valor estático de `sigma_theta_compression_positive_Pa` sem
instanciar `SaltCreepTimeBridge` e sem fazer `PknModel` depender de
`saltcreep`.

O gate da auditoria foi:

```text
SIGMA_THETA_STATIC_PROVIDER_IMPLEMENTATION_ALLOWED
```

A nova rota é:

```text
YAML -> CaseParser -> CaseData -> PknRunner -> PknInput -> PknModel
```

Ela é explícita e opt-in:

```yaml
lot:
  fracture:
    initiation:
      type: sigma_theta_static
      pressure_source: wellbore_pressure_Pa
      comparison: legacy_algebra
```

A álgebra é compatível com o diagnóstico em `LotSaltSigmaThetaBreakdown`:

```text
margin_Pa = wellbore_pressure_trial_Pa - sigma_theta_compression_positive_Pa
opened = margin_Pa > 0
```

Diferença entre modos:

| Modo | Fonte | Status |
|---|---|---|
| `constant_pressure` | `fracture.breakdown.pressure` | fallback existente |
| `sigma_theta_static` | valor YAML estático | diagnóstico opt-in |
| `sigma_theta_runtime` | futuro bridge/salt wall stress | não implementado |

Essa fase não conecta `SaltWallStressDiagnostics` real ao runtime, não cria
acoplamento temporal sal/LOT e não altera `lot-sim run --mode lot-pkn` sem
opção explícita no YAML.

Diagnóstico BUZ67D:

```text
case: cases/validation/buz67d_pkn_legacy_sigma_theta_static.yaml
classification: SIGMA_THETA_STATIC_OPENED_TOO_EARLY
fracture_initiation_time_s: 30.0
fracture_initiation_pressure_Pa: 82129237.46813472
fracture_initiation_sigma_theta_Pa: 67342521.84592447
fracture_initiation_margin_Pa: 14786715.62221025
```

O resultado confirma que a arquitetura está pronta para receber uma fonte
sigma-theta, mas o proxy estático de abertura ainda não reproduz a altura de
influência legada. A próxima fase deve substituir o valor estático por uma
fonte opt-in runtime de `SigmaThetaInfluenceLayer`, ainda sem tornar isso
default global.

## Auditoria de vazao e complacencia do balanço LOT — Fase 10.19B

A Fase 10.19B investigou se a abertura precoce do caso
`sigma_theta_static` vinha de erro de vazao, unidade ou fator `2*pi`.

Resultado:

```text
FLOWRATE_CONVENTION_MATCHES_LEGACY
ROOT_CAUSE_MISSING_GEOMETRIC_COMPLIANCE
```

No legado `APB1da`, `idQ = 6` converte `0.5 bbl/min` para:

```text
Q_total = 0.0794935 m3/min
Q_rad = 0.01265178346867558 m3/min/rad
dV_30s_rad = 0.00632589173433779 m3/rad
```

O legado calcula internamente `Vq` e `Vi` por radiano. O moderno usa volumes
totais no `volumetric_balance`, mas a razao de pressurizacao e equivalente
quando numerador e denominador usam a mesma convencao:

```text
dV_rad / (C * V_rad) == dV_total / (C * V_total)
```

O calculo de fechamento do primeiro passo com compressao pura de fluido resultou
em:

```text
dP_theoretical = 55396919.53121999 Pa
```

No traço legado auditado, o primeiro passo tem:

```text
legacy_first_dP = 1845413.7784679066 Pa
```

A diferenca e coerente com a presença, no legado, de `dV` geometrico calculado
a partir de deslocamentos anulares e inserido em:

```text
dP = (alpha*dT - (-Vq + dV - dMl/(rho*FC))) / Vi / k
```

Portanto, esta fase nao altera `LotSaltPressureMap`,
`LotSaltCouplingStep`, sigma-theta runtime ou `lot-sim run --mode lot-pkn`.
O proximo avanço fisico deve modelar explicitamente `annular_compliance` ou
`wellbore_compliance` antes de declarar equivalencia com `pw_Pa` legado.

## Volume anular BUZ67D com drill pipe (Fase 10.16)

A Fase 10.16 adiciona suporte diagnostico para volume anular inicial com drill
pipe no caso controlado `buz67d_pkn_legacy_aligned.yaml`.

Auditoria do legado:

```text
legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp
  Solids(true, 1922., profTeste, ..., di = 4.67, de = 5.5, ...)

legance/LOT_Tese/src/apb_code/Solids.cpp
  getRi_m() = di * 0.0254 / 2
  getRe_m() = de * 0.0254 / 2

legance/LOT_Tese/src/apb_code/Layers.cpp
  Vi = 0.5 * (R_outer^2 - R_inner^2) * thickness
```

Portanto, a convencao moderna registrada para diagnostico e:

```text
volume_per_radian_m3 = 0.5 * (R_outer^2 - R_inner^2) * length
volume_total_m3 = 2*pi*volume_per_radian_m3
```

Sem drill pipe, `R_inner = 0`, preservando o comportamento anterior. Com drill
pipe, `R_inner` e o raio externo do drill pipe quando ele alcanca a sapata.

O resultado `lot-sim run --mode lot-pkn` passa a exportar os campos de volume
anular em `result.json`, mas o solver PKN continua sem consumir esse volume
para calcular `net_pressure_Pa`. Assim, a fase corrige a geometria diagnostica
e prepara comparacoes Level 1B, sem declarar acoplamento fisico ou equivalencia
com `pw_Pa` legado.

Para a configuracao BUZ67D controlada atual, o volume moderno diagnostico cai
de `1.39698074804365 m3` para `1.12107852567506 m3` total ao descontar o drill
pipe de `5.5 in` OD.

## Compliance geometrica opt-in no balanco volumetrico LOT (Fase 10.19C)

A Fase 10.19C adiciona uma rota opt-in e diagnostica para testar a hipotese
levantada na Fase 10.19B: a escala de pressurizacao moderna estava dominada por
compressao pura de fluido, enquanto o legado possui um termo geometrico `dV` no
balanco anular.

O modelo novo e limitado a `lot.pressure_model = volumetric_balance` e so atua
quando o YAML declara explicitamente:

```yaml
lot:
  volumetric_balance:
    compliance:
      enabled: true
      model: constant_geometric
      geometric_compressibility:
        value: 1.8571966938610005e-8
        unit: "1/Pa"
      source: DIAGNOSTIC_FROM_LEGACY_FIRST_STEP
```

A formula usada no balanco e:

```text
C_eff = C_fluid + C_geom
dP = dV_eff / (C_eff * V_annular)
```

onde `C_geom` e uma compressibilidade geometrica equivalente, constante e
inferida do primeiro passo legado. Ela nao representa ainda rigidez mecanica de
revestimento, formacao, cimentacao, sal ou APB.

Caso diagnostico:

```text
cases/validation/buz67d_pkn_legacy_compliance.yaml
```

Comparacao local gerada por:

```text
tools/compare_phase10_19c.py
```

Resultados observados:

| Metrica | Valor |
|---|---:|
| `C_fluid_1_Pa` | `6.4e-10` |
| `C_geom_1_Pa` | `1.8571966938610005e-8` |
| `C_eff_1_Pa` | `1.9211966938610006e-8` |
| `legacy_first_dP_Pa` | `1845413.7784679066` |
| `modern_first_dP_no_compliance_Pa` | `55397022.29498486` |
| `modern_first_dP_with_compliance_Pa` | `1845417.2017930523` |
| `max_pressure_legacy_Pa` | `69035836.1743195` |
| `max_pressure_with_compliance_Pa` | `67331393.612597` |
| `relative_error_max_pressure` | `-0.02468924338685035` |
| `fracture_initiation_time_s` | `690.0` |

Classificacao:

```text
COMPLIANCE_EFFECTIVE
GEOMETRIC_COMPLIANCE_DIAGNOSTIC_ONLY
```

Essa classificacao significa apenas que a compliance equivalente explica a
escala do primeiro incremento e aproxima a faixa maxima de pressao no caso
controlado. Ela nao valida fratura fisica, nao valida `sigmaTheta`, nao compara
`opened` legado e nao torna o acoplamento sal/APB ativo.

O comportamento padrao permanece inalterado:

- casos sem `lot.volumetric_balance.compliance.enabled: true` continuam usando
  apenas `C_fluid`;
- `pkn_direct` ignora a compliance volumetrica;
- `lot-sim run --mode lot-pkn` segue desacoplado de sal/APB;
- resultados locais em `results/comparison/phase10_19c/` sao artefatos de
  diagnostico e nao devem ser versionados.

## Auditoria de compliance mecanica anular/wellbore (Fase 10.20A)

A Fase 10.20A auditou a rota mecanica legada que alimenta o termo `dV` usado
no balanco APB/LOT. No legado:

```text
APB1da::getNodalDisplacement(lu) -> line_up[lu].u
APB1da::getdV(lu) -> line_up[lu].dV
```

e o volume anular deformado por radiano e:

```text
V_deformado = 0.5 * thickness * ((b + u_outer)^2 - (a + u_inner)^2)
dV = V_deformado - Vi + dV_leakoff
```

Esse `dV` entra na formula de `dP` antes da avaliacao de fratura/leakoff:

```text
dP = (alpha*dT - (-Vq + dV - dMl/(rho*FC))) / Vi / k
```

A auditoria nao alterou `legance/`, `external/saltcreep/`, `LotSaltPressureMap`
ou `lot-sim run --mode lot-pkn`. O gate ficou:

```text
MECHANICAL_COMPLIANCE_FORMULATION_PARTIAL
```

O modelo escolhido para uma proxima implementacao opt-in e
`elastic_annular_simple`: uma compliance radial equivalente baseada em
propriedades elasticas e geometria. Ele e deliberadamente reduzido e deve ser
tratado como diagnostico, porque nao reproduz o sistema global legado nem a
fluencia temporal do sal.

## Modelo elastico simples de compliance anular (Fase 10.20B)

A Fase 10.20B implementou `elastic_annular_simple` como rota opt-in no
`volumetric_balance`. O modelo nao altera `LotSaltPressureMap`, nao chama
`SaltCreepTimeBridge` e nao conecta APB/sal ao runtime padrão.

Formula:

```text
c_inner = r_inner^2 / (E_inner * t_inner)
c_outer = (1 + nu_outer) * r_outer / E_outer
C_geom = 2 * (r_outer*c_outer + r_inner*c_inner) /
         (r_outer^2 - r_inner^2)
C_eff = C_fluid + C_geom
```

`constant_geometric` continua disponível como baseline diagnostico da 10.19C.
`elastic_annular_simple` e uma tentativa mecanica reduzida e deve ser comparado
separadamente no BUZ67D antes de qualquer promoção de maturidade.

## Diagnostico BUZ67D com compliance elastica simples (Fase 10.20C)

A Fase 10.20C adicionou um caso BUZ67D controlado com
`lot.volumetric_balance.compliance.model = elastic_annular_simple`:

```text
cases/validation/buz67d_pkn_legacy_elastic_compliance.yaml
```

O caso foi comparado com:

- legado auditado em `results/comparison/level1_buz67d/legacy_audit/`;
- moderno sem compliance;
- moderno com `constant_geometric` da 10.19C;
- moderno com `elastic_annular_simple` da 10.20B.

A ferramenta `tools/compare_phase10_20c.py` gerou `phase10_20c_summary.csv`,
`phase10_20c_metadata.json` e figuras diagnosticas locais em
`results/comparison/phase10_20c/`. Esses artefatos nao devem ser versionados.

Resultado:

```text
classification = ELASTIC_COMPLIANCE_UNDERCOMPLIANT
modern_first_dP_elastic_compliance_Pa = 43639672.35675542
modern_first_dP_constant_compliance_Pa = 1845417.2017930523
legacy_first_dP_Pa = 1845413.7784679066
fracture_initiation_time_elastic_s = 30.0
fracture_initiation_time_legacy_s = 510.0
```

Conclusao: o modelo elastico simples melhora a pressao frente a compressao pura
do fluido, mas e insuficientemente complacente para reproduzir a escala de
`dP` do legado. A fase nao altera o runtime padrao, nao conecta APB/sal, nao
implementa Zamora e nao valida fratura fisica.

## Extracao da compliance aparente legado (Fase 10.21A)

A Fase 10.21A criou `tools/extract_phase10_21a_apparent_compliance.py` para
extrair uma serie incremental de compliance aparente a partir do trace auditado
do LOT_Tese. A rota nao modifica `legance/LOT_Tese/` e nao altera o solver
moderno.

Formula legado auditada:

```text
dP = (alpha*dT - (-Vq + dV - dMl/(rho*FC))) / Vi / k
```

Formula reduzida usada com o trace disponivel:

```text
C_eff_apparent = delta_Vq_m3_rad / (Vi_m3_rad * delta_dP_Pa)
C_geom_apparent = C_eff_apparent - k
```

Campos ausentes no trace usado:

```text
dV_geom_m3_rad
dV_leakoff_m3_rad
dMl_term_m3_rad
Vi_m3_rad
k_1_Pa
opened
```

Resultado BUZ67D:

```text
classification = APPARENT_COMPLIANCE_PRESSURE_DEPENDENT
mean_C_eff_apparent_pre_opening = 8.737997966365286e-8 1/Pa
mean_C_geom_apparent_pre_opening = 8.673997966365285e-8 1/Pa
cv_C_eff_apparent = 0.24223657359536746
correlation_vs_pressure = 0.7678090262667732
ratio_pre_mean_to_constant_10_19C = 4.670478897058859
ratio_elastic_10_20C_to_pre_mean = 0.0019878729366281296
```

Conclusao: o proxy `constant_geometric` da 10.19C captura o primeiro passo, mas
nao representa toda a curva pre-abertura. A proxima fase deve planejar um
modelo tabulado/dependente de pressao ou calibracao opt-in explicita, sem
promover essa extracao reduzida a validacao fisica.

## Adendo 10.21B — gate termico/compressibilidade para compliance tabulada

A rota `pressure_tabulated_geometric` nao deve ser implementada a partir da
compliance aparente bruta da 10.21A antes de auditar o termo termico legado. O
balanco ativo do `LOT_Tese` contem:

```text
dP = (alpha*dT - (-Vq + dV - dMl/(rho*FC))) / Vi / k
```

No BUZ67D PKN, o fluido principal usa `alpha = 8.0e-4 1/degC` e
`k = 6.4e-10 1/Pa`. O moderno controlado usa o mesmo valor de
compressibilidade (`C_fluid_modern = 6.4e-10 1/Pa`), portanto nao foi
identificado mismatch de compressibilidade.

O `.dat` nativo auditado exporta `dT`, `Compressibilidade` e `C_Exp`. Para o
layer 16, o ponto de abertura legado (`8.5 min`) possui:

```text
dT = 3.282587105 degC
alpha*dT = 0.002626069684
thermal_pressure_equivalent = alpha*dT/k = 4.10323388125e6 Pa
dP = 8.131435236e6 Pa
thermal_fraction = 0.5046137320363699
```

Na janela pre-abertura, a fracao termica media e `0.8670835951244072` e o
maximo absoluto e `1.5259151388269308`. A classificacao e:

```text
THERMAL_EFFECT_DOMINANT
THERMAL_EFFECT_NEEDS_CORRECTION_BEFORE_TABULATION
COMPRESSIBILITY_CONFIRMED_MATCHING_LEGACY
PRESSURE_TABULATED_COMPLIANCE_BLOCKED_THERMAL_EFFECT_RELEVANT
```

Consequencia: a 10.21B nao deve promover `pressure_tabulated_geometric` nesta
forma. A proxima etapa deve produzir uma serie corrigida por termo termico, ou
reinstrumentar temporariamente o legado para exportar `dT`, `alpha`, `k`,
`dV_geom`, `dMl` e `dV_leakoff` em um trace unico. Ate la, a compliance
aparente da 10.21A permanece diagnostica e bruta.

## Compliance aparente corrigida por perfil termico (Fase 10.21C)

A Fase 10.21C criou
`tools/extract_phase10_21c_thermal_corrected_compliance.py` para reconstruir,
sem modificar `legance/LOT_Tese/`, uma serie diagnostica de compliance aparente
corrigida pelo termo termico do balanco legado.

A ferramenta usa o caso legado:

```text
legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp
```

e o trace auditado existente:

```text
results/comparison/level1_buz67d/legacy_audit/buz67d_audit_timeseries.csv
```

Para o anular A, no `profTeste = 4374 m`, a interpolacao linear dos vetores
`dA`, `A0` e `Af` resulta em:

```text
T_initial_degC = 89.17547550432276
T_final_degC   = 92.31236311239194
DTmax_degC     = 3.1368876080691734
alpha          = 8.0e-4 1/degC
k              = 6.4e-10 1/Pa
```

A evolucao temporal segue a forma legada:

```text
dT(t) = DTmax * t / (Tlimit + t)
Tlimit = 0.25 min
thermal_pressure_equivalent = alpha*dT/k
```

A correcao compatível com a formula ativa:

```text
dP = (alpha*dT - (-Vq + dV - dMl/(rho*FC))) / Vi / k
```

foi avaliada como:

```text
dP_mech_subtract = dP - alpha*dT/k
```

Tambem foi gerada uma rota de sensibilidade de sinal:

```text
dP_mech_add = dP + alpha*dT/k
```

Essa segunda rota e apenas diagnostica; ela nao substitui a leitura da formula
legada.

Resultado BUZ67D pre-abertura:

| Serie | Media `C_eff` [1/Pa] | Mediana `C_eff` [1/Pa] | CV | Observacao |
|---|---:|---:|---:|---|
| Bruta 10.21A | `8.737997966365286e-8` | `9.689922710105396e-8` | `0.24223657359536746` | pressure-dependent |
| Corrigida `dP - alpha*dT/k` | `1.1972273085205066e-7` | `1.0434903008590042e-7` | `0.36756131042159057` | sinal ambiguo |
| Sensibilidade `dP + alpha*dT/k` | `7.793012068107723e-8` | `9.013453455649825e-8` | `0.3326728131235428` | pressure-dependent |

Para `C_geom` corrigido por subtracao:

```text
mean_C_geom_apparent_thermal_corrected_subtract = 1.1908273085205067e-7 1/Pa
median_C_geom_apparent_thermal_corrected_subtract = 1.0370903008590043e-7 1/Pa
std_C_geom_apparent_thermal_corrected_subtract = 4.4005443839231133e-8 1/Pa
cv_C_geom_apparent_thermal_corrected_subtract = 0.36953673739565013
ratio_to_C_geom_constant_10_19C = 6.411961169523989
```

O ponto decisivo e que a correcao por subtracao produziu:

```text
negative_mechanical_pressure_n = 4
non_positive_delta_pressure_n = 1
classification = THERMAL_CORRECTED_COMPLIANCE_SIGN_AMBIGUOUS
```

Portanto, a Fase 10.21C melhora a rastreabilidade da serie, mas nao libera a
implementacao de `pressure_tabulated_geometric`. O gate permanece fechado:

```text
THERMAL_CORRECTION_EXTRACTED_DIAGNOSTIC_ONLY
PRESSURE_TABULATED_STILL_BLOCKED_MISSING_BALANCE_TERMS
PRESSURE_TABULATED_STILL_BLOCKED_SIGN_CONVENTION_AMBIGUOUS
```

Campos ainda ausentes para fechar a reconstrucao fisica:

```text
dV_geom_m3_rad
dMl_term_m3_rad
dV_leakoff_m3_rad
opened
```

Conclusao: nao usar a serie corrigida como modelo solver, nao versionar os
artefatos em `results/` e nao promover `pressure_tabulated_geometric`. A proxima
fase deve reinstrumentar temporariamente o legado, ou criar uma extracao que
una explicitamente `dT`, `dV_geom`, `dMl`, `dV_leakoff`, `k` e `opened` no mesmo
trace.

## Dependencia Eigen no acoplamento

Targets novos do `lot-salt-suite` devem receber Eigen por `lss::eigen`, que
aponta para `include/Eigen/`. O acoplamento com `external/saltcreep/` deve ser
feito por adapter e contrato de dados, sem misturar include paths apenas para
resolver headers Eigen.

A Fase 6.11 completou a migracao Eigen do saltcreep (`MIGRATION_COMPLETED`):
`external/saltcreep/CMakeLists.txt` agora auto-detecta o contexto `lot-salt-suite`
e usa `include/Eigen` por padrao. A duplicacao de Eigen (via proxy no build dir)
e aceitavel ate o adapter `SaltCreepSaltcreepAdapter` estabilizar.
