# 17. Roadmap LOT/PKN

## Decisao de prioridade

A migracao de LOT deve priorizar o caminho PKN observado nos legados antes de
implementar familias de fratura adicionais. O motivo e pratico: o PKN e o
caminho com casos e arquivos de resultado mais diretamente conectados aos LOTs
auditados, especialmente em `legance/LOT_Tese/`.

Os modelos circular, eliptico e penny-shaped permanecem catalogados, mas nao
devem bloquear a primeira implementacao moderna.

## Escopo da primeira entrega LOT/PKN

A primeira implementacao moderna deve criar contratos e testes, nao apenas
transcrever equacoes do legado.

Componentes esperados:

| Componente | Responsabilidade |
|------------|------------------|
| `lot::PknModel` | Calcular abertura, comprimento e volume de fratura PKN com entradas SI. |
| `lot::BreakdownDetector` | Detectar inicio de fratura quando a pressao de parede excede o limite definido pela convencao do projeto. |
| `lot::InjectionSchedule` | Representar taxa de injecao, tempo de simulacao, `dt` e tempo de acomodacao/no-injection. |
| `lot::LeakoffState` | Acumular volume vazado/fraturado e expor serie temporal para APB/coupling. |
| Testes Catch2 | Cobrir unidades, monotonias, ativacao de breakdown e conservacao dimensional basica. |

## Contrato de tempo

O `dt` deve ser coerente com a taxa usada pelo modelo fisico. Se a lei de
deformacao ou fluencia estiver expressa por segundo, o `dt` deve estar em
segundos no solver; se a taxa estiver por minuto ou hora, a conversao deve ser
explicita no parser ou no adapter.

O usuario deve poder definir:

- `dt`;
- politica adaptativa futura, quando implementada;
- tempo total de simulacao;
- tempo de acomodacao, definido como periodo sem incrementos termicos nem
  injecao de fluidos.

No codigo moderno, o parser deve converter unidades de campo para SI antes de
entregar os dados ao solver.

## Caminho de migracao

1. Congelar a interpretacao tecnica do PKN legado em `docs/audits/pkn_legacy_path.md`.
2. Criar tipos de entrada LOT em `include/lot/`, separados de parsing.
3. Implementar `PknModel` com entradas SI e sem acesso direto a YAML/JSON.
4. Implementar `BreakdownDetector` seguindo FA01-FA04 e os riscos registrados.
4.5. Criar `cases/lot_tese_migrated/buz67d_pkn.yaml` com os parâmetros
   extraídos de `legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp` e validar
   contra `schemas/lot_case.schema.yaml` antes de conectar ao CLI.
   Este caso é a ponte entre o contrato numérico e o pipeline YAML→CLI.
4.6. Fase 6.2: criar contrato YAML/C++ LOT/PKN, detector sintético e esqueleto
   minimo de `PknModel` sem regressao contra legado enquanto R09 estiver aberto.
4.7. Fase 6.3: auditar R09. Resultado: `/ M_PI / 22` existe em
   `Conv_bbmin_m3h(idQ == 4)`, mas os PKN auditados usam `idQ == 6`. R09 segue
   aberto para regressao numerica porque o fator nao tem justificativa
   documental e o caminho PKN ainda exige ensaio comparativo controlado.
4.8. Fase 6.4: substituir o esqueleto sintetico por `PknModel` fisico minimo
   em SI, com serie temporal, conservacao dimensional basica e testes Catch2,
   sem regressao contra arquivos legados enquanto R09 permanecer aberto.
5. Adicionar testes Catch2 com casos sinteticos e regressao dimensional.
6. Conectar ao CLI apenas depois que o contrato numerico estiver testado e o
   caso YAML (passo 4.5) for reconhecido pelo parser sem erro.
7. Comparar com arquivos legados somente quando o pipeline moderno produzir
   series equivalentes e documentar em `docs/12_validation_results.md`.

## O que foi entregue por fase

**Fase 6.1 (auditoria e governança):**
- Mapeamento do caminho PKN legado em `docs/audits/pkn_legacy_path.md`.
- Catálogo de modelos não PKN em `docs/audits/non_pkn_models_status.md`.
- Política de saltcreep vendorizado ativo em `docs/16_saltcreep_governance.md`.
- Nenhum código C++ novo.

**Fase 6.2 (contrato sintético):**
- `lot::BreakdownDetector` com 5 testes Catch2 sintéticos (vetor SI, erros controlados).
- Esqueleto sintético de `lot::PknModel` com 4 testes (não usa formulação física validada).
- Três casos YAML validados pelo parser: `lot_pkn_minimal.yaml`, `lot_pkn_with_leakoff.yaml`, `buz67d_pkn.yaml`.
- `buz67d_pkn.yaml` é contrato sintático/migratório — NÃO é baseline numérico.
- R09 (`/ M_PI / 22`) permanece blocker para qualquer regressão PKN legado × moderno.

**Fase 6.3 (auditoria R09):**
- Relatorio criado em `docs/audits/R09_pkn_mpi22_audit.md`.
- A expressao suspeita foi localizada em `Conv_bbmin_m3h`, ramo `idQ == 4`.
- Os casos PKN BUZ67D e 9-BUZ-39DA auditados usam `idQ == 6`, que chama
  `Conv_bbmin_m3min` com `/ M_PI / 2`.
- R09 continua aberto para regressao numerica legado x moderno; a proxima etapa
  deve ser ensaio comparativo controlado ou formulacao fisica minima em SI sem
  usar o legado como baseline.

**Fase 6.4 (modelo fisico minimo em SI):**
- `lot::PknModel` agora calcula ponto e serie temporal em SI.
- Entradas fisicas minimas: taxa, `dt`, tempo total, tempo de acomodacao,
  altura, largura inicial, modulo plano, viscosidade e leakoff opcional.
- Saidas: tempo, volume injetado, abertura, comprimento, volume de fratura,
  volume de leakoff e pressao liquida.
- Testes Catch2 cobrem finitude, nao negatividade, monotonicidade basica,
  leakoff simplificado, determinismo e rejeicao de entradas invalidas.
- A validacao CLI dos tres YAMLs `lot-pkn` continua sendo validacao de
  contrato, nao regressao numerica contra legado.

## Fora de escopo até R09 ser resolvido

- Comparação numérica com `legance/LOT_Tese` ou `legance/LOT_APB_v5`.
- Uso de `buz67d_pkn.yaml` como referência de resultado.
- Conexão do subcomando `run` ao `PknModel`.
- Acoplamento com sal ou APB.

## Proxima fase recomendada

Enquanto R09 permanecer aberto, seguir um destes caminhos:

1. Ensaio comparativo controlado das variantes de conversao (`/(pi*22)` versus
   `/(pi*2)`) em ferramenta externa ao legado congelado.
2. Conectar `PknModel` ao subcomando `run` com saida CSV/JSON moderna e
   documentar que `validate` segue restrito a schema/contrato.
3. Evoluir o leakoff para uma lei calibravel e conectar breakdown sem misturar
   parsing com solver.

## Riscos tecnicos a resolver antes da implementacao

- O legado usa conversoes de vazao com fatores geometricos embutidos e ao menos
  uma expressao suspeita (`/ M_PI / 22`) que deve ser auditada antes de servir
  como referencia numerica.
- O tempo de fratura mistura `t` absoluto e tempo desde breakdown em trechos do
  legado; o modelo moderno deve escolher uma unica convencao.
- O volume PKN legado usa uma forma simplificada (`w0 * L1 * pi`) e mantem uma
  alternativa comentada; a escolha precisa ser documentada antes de validar.
- A convencao de tensao circunferencial deve respeitar FA01-FA04 e nao pode ser
  reinterpretada sem registro em `docs/08_known_issues.md`.
