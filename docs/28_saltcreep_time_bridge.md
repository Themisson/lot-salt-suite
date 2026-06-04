# 28 — Bridge temporal para o TimeIntegrator do saltcreep

**Status:** Implementado e consumido pelo adapter — Fases 7.8-8.0
**Ultima atualizacao:** 2026-06-03

## Objetivo

A Fase 7.8 cria uma ponte C++ entre o `lot-salt-suite` e o
`TimeIntegrator` do `external/saltcreep/` sem expor os headers de I/O do
backend vendorizado aos headers publicos do projeto.

Classificacao:

```text
TIME_BRIDGE_CONNECTED
```

Isto significa que `TimeIntegrator::advance()` compila e executa por uma
camada intermediaria isolada. Nao significa acoplamento LOT/PKN/APB e nao
substitui ainda o backend minimo do `SaltCreepSaltcreepAdapter`.

Na Fase 7.9, o bridge passou a ser consumido pelo
`SaltCreepSaltcreepAdapter`. Na Fase 8.0, o bridge passou a aceitar pressao de
parede dinamica por passo temporal. O bridge continua isolado do LOT/PKN/APB.

## Problema resolvido

O header do integrador temporal do saltcreep inclui:

```text
external/saltcreep/include/solver/TimeIntegrator.hpp
  -> external/saltcreep/include/io/CaseParser.hpp
  -> external/saltcreep/include/io/VtuWriter.hpp
```

O `lot-salt-suite` tambem possui:

```text
include/io/CaseParser.hpp
include/io/ResultWriter.hpp
```

Se `TimeIntegrator.hpp` for incluido diretamente em targets principais, o
include textual `"io/CaseParser.hpp"` pode resolver para o parser errado
dependendo da ordem de include.

## Solucao

Foi criado `SaltCreepTimeBridge`:

```text
include/salt/SaltCreepTimeBridge.hpp
src/salt/SaltCreepTimeBridge.cpp
```

O header publico expoe apenas tipos simples em SI:

- `SaltCreepTimeBridgeConfig`;
- `SaltCreepTimeBridgeResult`;
- `SaltCreepTimeBridge`.

Ele nao inclui nenhum header de `external/saltcreep/` e nao inclui
`io/CaseParser.hpp`.

Os includes problemáticos ficam confinados a
`src/salt/SaltCreepTimeBridge.cpp`, compilado no target isolado:

```text
lss_saltcreep_time_bridge
```

Esse target usa include order controlada:

```text
build/lss_saltcreep_controlled_eigen_proxy/
external/saltcreep/include/
include/
```

Assim, quando `TimeIntegrator.hpp` inclui `"io/CaseParser.hpp"`, a resolucao
acontece dentro de `external/saltcreep/include/io/CaseParser.hpp`, nao no
parser moderno do `lot-salt-suite`.

## Prova implementada

O teste `tests/cpp/test_salt_creep_time_bridge.cpp` compila em target separado:

```text
saltcreep_time_bridge_tests
```

Esse target recebe apenas `include/` do `lot-salt-suite` como include publico e
linka contra `lss_saltcreep_time_bridge`. Ele nao recebe
`external/saltcreep/include/`.

Os testes cobrem:

- compilacao do bridge por header publico limpo;
- ausencia de exposicao publica de `solver/TimeIntegrator.hpp`;
- resultado inicial finito vindo do `TimeIntegrator`;
- chamada real a `TimeIntegrator::advance()`;
- avanço de tempo;
- rejeicao de tempo decrescente;
- configuracao SI invalida;
- ausencia de dependencia de tipos LOT/PKN;
- pressao de parede dinamica por passo;
- preservacao da resposta elastica de Lame no caso degenerado de pressao
  constante;
- rejeicao de pressao dinamica negativa ou nao finita.

## Pressao dinamica

As sobrecargas:

```cpp
advance_by(dt_s, wall_pressure_Pa)
advance_to(target_time_s, wall_pressure_Pa)
```

atualizam a pressao de parede aplicada ao proximo incremento temporal. A
implementacao usa um campo de pressao por degrau interno para que o
`TimeIntegrator` veja a diferenca entre a pressao no inicio e no fim do passo.

As sobrecargas antigas sem pressao continuam disponiveis e preservam a pressao
configurada inicialmente. Portanto, pressao constante continua sendo o
comportamento padrao e permanece coberta pelos testes de Lame.

## Limites atuais

O bridge usa campo termico constante neutro, material elastico e geostatica
opcional. Como o material usado na prova e `ElasticIsotropic`, o `advance()`
confirma a rota temporal, a manutencao do estado do integrador e a troca
controlada de pressao, mas nao introduz fluencia real nem dano.

Na Fase 8.0, o `SaltCreepSaltcreepAdapter` passa a encaminhar
`query.wall_pressure_Pa` para o bridge. Isso aceita historico variavel vindo de
queries manuais, mas ainda nao conecta LOT/PKN/APB ao sal.

## Proximos passos

1. Decidir como expor deformacao e fechamento vindos do estado temporal.
2. Conectar futuramente LOT/APB ao adapter por uma camada `coupling/` explicita.
3. Somente depois avaliar modelos constitutivos de fluencia e dano.
