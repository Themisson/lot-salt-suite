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
