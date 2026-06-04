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

## Dependencia Eigen no acoplamento

Targets novos do `lot-salt-suite` devem receber Eigen por `lss::eigen`, que
aponta para `include/Eigen/`. O acoplamento com `external/saltcreep/` deve ser
feito por adapter e contrato de dados, sem misturar include paths apenas para
resolver headers Eigen.

A Fase 6.11 completou a migracao Eigen do saltcreep (`MIGRATION_COMPLETED`):
`external/saltcreep/CMakeLists.txt` agora auto-detecta o contexto `lot-salt-suite`
e usa `include/Eigen` por padrao. A duplicacao de Eigen (via proxy no build dir)
e aceitavel ate o adapter `SaltCreepSaltcreepAdapter` estabilizar.
