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
