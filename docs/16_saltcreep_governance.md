# 16. Governanca do saltcreep

## Decisao de governanca

`external/saltcreep/` passa a ser tratado como dependencia vendorizada ativa do
`lot-salt-suite`, e nao apenas como referencia imutavel. Isso corrige a tensao
entre a arquitetura alvo, que depende de um resolvedor de fluencia de sal
operacional, e a regra anterior que impedia qualquer evolucao controlada no
codigo de sal.

Essa decisao nao autoriza edicoes livres. O diretorio continua protegido por
contrato tecnico: qualquer alteracao deve ter escopo explicito, testes,
documentacao e registro no `docs/dev-log.md`.

## Politica operacional

| Tema | Politica |
|------|----------|
| Uso normal | Consumir `external/saltcreep/` por adapter em `src/salt/`, sem copiar codigo constitutivo. |
| Edicoes permitidas | Apenas quando o objetivo depender diretamente do solver de sal: pressao de parede, dano, pos-processamento, acoplamento ou I/O necessario. |
| Edicoes proibidas | Mudancas oportunistas, refatoracoes cosmeticas, alteracao de formulacao fisica sem registro em `docs/08_known_issues.md` e sem validação dedicada. |
| Testes | Toda mudanca em `external/saltcreep/` exige testes do proprio saltcreep quando existentes e testes de integracao no `lot-salt-suite` quando houver adapter afetado. |
| Rastreabilidade | Registrar motivacao, arquivos, testes e riscos em `docs/dev-log.md`; se a formulacao mudar, registrar tambem em `docs/08_known_issues.md`. |
| Legado LOT/APB | `legance/` e `legacy/` continuam congelados e somente leitura. |

## Fronteira de responsabilidade

O `lot-salt-suite` deve conter a orquestracao, parsing, conversoes de unidade,
contratos de dados e adapters. O `external/saltcreep/` deve continuar contendo
o nucleo numerico de fluencia, dano e campos de pressao aplicados a parede.

## Politica Eigen

`include/Eigen/` e o Eigen oficial do `lot-salt-suite` e deve ser exposto aos
targets modernos pelo target CMake `lss::eigen`. A copia em
`external/saltcreep/include/Eigen/` permanece preservada como fallback.

Desde a Fase 6.11, o `external/saltcreep/CMakeLists.txt` auto-detecta o contexto
`lot-salt-suite` e ativa `include/Eigen` por padrao quando o saltcreep e buildado
dentro da arvore do projeto. O mecanismo usa um diretorio proxy no build dir
contendo apenas `Eigen/` (copiado de `include/Eigen/`), adicionado com
`BEFORE PRIVATE` para garantir precedencia de include mesmo no gerador Visual
Studio. Essa abordagem foi validada com 126/126 testes Catch2 e resultado APB
identico ao baseline (`closure=0.300817%`).

Nenhum target deve receber simultaneamente `include/` e
`external/saltcreep/include/` como fontes ativas de Eigen; o proxy resolve apenas
`Eigen/` e os includes relativos do saltcreep (`"io/CaseParser.hpp"` etc.)
continuam resolvendo para `external/saltcreep/include/`.

Ver `docs/audits/saltcreep_eigen_compatibility_audit.md`,
`docs/20_saltcreep_eigen_migration_plan.md` e
`docs/21_saltcreep_eigen_migration_result.md`.

O adapter esperado e:

1. Receber casos ja convertidos para SI pelo parser do `lot-salt-suite`.
2. Construir os campos de pressao/temperatura requeridos pelo saltcreep.
3. Executar ou acionar o solver de sal.
4. Retornar deslocamento, fechamento radial, tensoes/dano diagnostico e series
   temporais necessarias para LOT/APB.
5. Nunca expor parsing YAML/JSON do caso principal para dentro do solver.

## Pontos tecnicos ja existentes no saltcreep

A auditoria de Fase 6.0 identificou capacidades relevantes ja presentes:

- `WallPressureField` para aplicar perfil de pressao na parede.
- Casos APB com gradiente de lama em `cases/apb/`.
- Saidas de diagnostico de dano, incluindo eventos e campos associados.
- Pos-processamento de pressao de parede e fechamento/diametro.

Esses pontos devem ser preferidos como superficie de integracao antes de criar
novas rotas paralelas.

## Regras para futuras alteracoes no saltcreep

Antes de alterar `external/saltcreep/`, abrir uma tarefa tecnica com:

- objetivo fisico/numerico;
- arquivos esperados;
- testes que serao executados;
- impacto no contrato do adapter;
- risco de regressao;
- necessidade ou nao de atualizar `docs/08_known_issues.md`.

Ao finalizar, registrar:

- arquivos alterados;
- testes executados;
- diferencas numericas observadas;
- risco remanescente;
- proximo passo de validacao.

## Estado nesta fase

Na Fase 6.10, `external/saltcreep/` foi auditado em modo somente leitura para
a compatibilidade Eigen. Nenhum arquivo do saltcreep foi alterado e as duas
copias de Eigen foram preservadas.

Na Fase 6.10B, `external/saltcreep/CMakeLists.txt` foi alterado com escopo
explicito para adicionar a opcao `LSS_SALTCREEP_FORCE_LSS_EIGEN` (default `OFF`)
e o arquivo de teste diagnostico `tests/test_eigen_source.cpp` foi criado.
Tres provas objetivas confirmaram que o build forcado usou `include/Eigen`.
Decisao: `PROVEN_SAFE_TO_MIGRATE`.

Na Fase 6.11, o default foi migrado de `OFF` para auto-deteccao: dentro da arvore
`lot-salt-suite`, o CMake detecta automaticamente `include/Eigen` e ativa o modo
integrado sem flags manuais. O build standalone fora do projeto usa Eigen interno
(`internal fallback`). Resultado: 126/126 Catch2, `closure=0.300817%` no APB,
47/47 no lot-salt-suite. Decisao: `MIGRATION_COMPLETED`.

Na Fase 7.0, o `lot-salt-suite` criou `SaltCreepInterface` e
`NullSaltCreepInterface` como contrato C++ minimo em `include/salt/` e
`src/salt/`. O `external/saltcreep/` permaneceu somente leitura; nenhum target
do projeto passou a linkar o solver vendorizado. O contrato estabiliza tipos SI
para futura integracao, mas ainda nao implementa adapter nem acoplamento fisico.

Na Fase 7.2, o `lot-salt-suite` criou `SaltCreepSaltcreepAdapter` como adapter
C++ experimental em `include/salt/` e `src/salt/`. O adapter ainda nao linka nem
executa o backend real: `is_available() = false` e respostas validas sao
neutras. A auditoria `docs/audits/saltcreep_radial_displacement_sign_audit.md`
confirmou que, nos caminhos auditados do `external/saltcreep`, `u_r < 0`
representa fechamento para dentro e fechamento positivo e calculado como
`-u_r`. O `external/saltcreep/` permaneceu somente leitura nesta fase.

Na Fase 7.3, o `lot-salt-suite` adicionou um teste Catch2 separado que compila
fontes minimas do `external/saltcreep` para um caso elastico de Lame controlado.
O teste confirma que a API C++ direta do backend e viavel para esse caso
isolado e que o sinal de fechamento depende da condicao de contorno fisica:
pressao interna positiva expande a parede, pressao externa/confinante positiva
fecha. Nenhum arquivo em `external/saltcreep/` foi alterado, e o adapter
permaneceu neutro com `is_available() = false`.

Na Fase 7.4, outro target Catch2 separado passou a compilar `TimeIntegrator`,
`ProfileField`, `ConstantWallPressureField` e a montagem geostatica do backend
em um caso controlado sem outputs versionados. Classificacao:
`TIME_THERMAL_GEOSTATIC_CONTROLLED_TEST_READY`. O `external/saltcreep/`
permaneceu somente leitura e o adapter continuou neutro.

Na Fase 7.5, `SaltCreepAdapterConfig` e `SaltCreepAdapterState` foram
implementados no `lot-salt-suite` para formalizar configuracao SI e estado
temporal do futuro adapter real. Nenhum arquivo em `external/saltcreep/` foi
alterado; `SaltCreepSaltcreepAdapter::is_available()` permanece `false` e nao
ha chamada ao backend real.

Na Fase 7.6, `SaltCreepSaltcreepAdapter` passou a compilar e executar uma rota
elastica/geostatica minima do backend `external/saltcreep` por adapter, usando
fontes vendorizadas sem modifica-las. `TimeIntegrator` permanece apenas nos
targets controlados separados ate uma fase dedicada resolver a fronteira de
includes e estado temporal.

Na Fase 7.7, a fronteira de includes do `TimeIntegrator` foi auditada em
`docs/audits/saltcreep_timeintegrator_include_boundary.md` e classificada como
`TIMEINTEGRATOR_BLOCKED_BY_INCLUDE_BOUNDARY` para o target principal. Nenhum
arquivo em `external/saltcreep/` foi alterado. O adapter passou a persistir
malha, elemento, material, matriz de rigidez, vetor geostatico e graus fixos da
rota minima entre queries.

Na Fase 7.8, o bloqueio foi resolvido por target intermediario no
`lot-salt-suite`, sem alterar `external/saltcreep/`. O target
`lss_saltcreep_time_bridge` compila `TimeIntegrator` com include order
controlada e expõe apenas `SaltCreepTimeBridge.hpp` como header publico limpo.
Classificacao: `TIME_BRIDGE_CONNECTED`. LOT/PKN/APB seguem desacoplados.

Na Fase 7.9, `SaltCreepSaltcreepAdapter` passou a usar
`SaltCreepTimeBridge` como backend interno persistente. A integracao continua
dentro de `src/salt/` e `include/salt/`; nenhum arquivo em
`external/saltcreep/` foi alterado e LOT/PKN/APB permanecem desacoplados.

Na Fase 8.0, `SaltCreepTimeBridge` e `SaltCreepSaltcreepAdapter` passaram a
aceitar pressao de parede dinamica por passo/query temporal, mantendo a
integracao dentro de `src/salt/` e `include/salt/`. Nenhum arquivo em
`external/saltcreep/` foi alterado e nenhum modelo fisico, LOT/PKN, APB,
parser, writer ou baseline foi modificado.

Na Fase 8.1, a presenca do adapter real foi testada como substituivel por
`NullSaltCreepInterface` no caminho LOT/PKN atual. O teste constroi
`SaltCreepSaltcreepAdapter`, mas confirma que o backend nao e construido nem
chamado enquanto `PknRunner` nao possuir ponto explicito de integracao com sal.
Isso preserva a governanca: `external/saltcreep/` permanece somente leitura e
qualquer acoplamento futuro deve entrar por fase propria, com interface
explicita e testes dedicados.
