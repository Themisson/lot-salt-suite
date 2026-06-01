# R09 — Ensaio comparativo controlado das conversões PKN

**Data:** 2026-06-01  
**Escopo:** ensaio analítico/documental, sem executar legado, sem usar `.dat` como baseline e sem alterar `legance/`, `legacy/`, `external/saltcreep/` ou `tests/baselines/`.  
**Script:** `tools/audit_r09_pkn_conversion.py`  
**Tabela gerada:** `docs/audits/R09_pkn_conversion_table.csv`

## 1. Resumo executivo

**Classificação após o ensaio:** `MITIGATED_FOR_AUDITED_PKN_CASES`

O ensaio confirma que:

- A expressão suspeita `Q * 9.53924 / M_PI / 22` existe no legado `LOT_Tese`.
- Ela pertence ao ramo `Conv_bbmin_m3h(double Q)`, selecionado quando `idQ == 4`.
- Os dois casos PKN auditados (`8-BUZ-67D-RJS-VISCO-pkn.cpp` e
  `9-BUZ-39DA-RJS-VISCO-2.cpp`) usam `idQ == 6`, portanto chamam
  `Conv_bbmin_m3min(double Q) = Q * 0.158987 / M_PI / 2`.
- O literal `/22` não afeta diretamente esses dois casos PKN auditados.
- O risco permanece para qualquer regressão ou caso que use `idQ == 4`.

Conclusão operacional: **Rota B** — marcar R09 como mitigado para os casos PKN
auditados, mas manter bloqueio para regressões envolvendo `idQ == 4` ou para
qualquer uso geral da família de conversões do legado como referência física.

## 2. Localização dos caminhos de conversão

Arquivo principal auditado:

```text
legance/LOT_Tese/src/apb_code/APB1da.cpp
```

| Linha aprox. | Função | Opção | Expressão | Entrada presumida | Saída presumida |
|--------------|--------|-------|-----------|-------------------|-----------------|
| 4 | `Conv_bbs_m3s` | `idQ == 0` | `Q * 0.158987 / M_PI / 2` | bbl/s | m3/s normalizado por `2*pi` |
| 5 | `Conv_bbmin_m3s` | `idQ == 1` | `Q * 0.00264979 / M_PI / 2` | bbl/min | m3/s normalizado por `2*pi` |
| 6 | `Conv_bbh_m3s` | `idQ == 2` | `Q * 4.41631E-5 / M_PI / 2` | bbl/h | m3/s normalizado por `2*pi` |
| 7 | `Conv_bbs_m3h` | `idQ == 3` | `Q * 572.354 / M_PI / 2` | bbl/s | m3/h normalizado por `2*pi` |
| 8 | `Conv_bbmin_m3h` | `idQ == 4` | `Q * 9.53924 / M_PI / 22` | bbl/min | m3/h normalizado por `22*pi` |
| 9 | `Conv_bbh_m3h` | `idQ == 5` | `Q * 0.158987 / M_PI / 2` | bbl/h | m3/h normalizado por `2*pi` |
| 10 | `Conv_bbmin_m3min` | `idQ == 6` | `Q * 0.158987 / M_PI / 2` | bbl/min | m3/min normalizado por `2*pi` |

Seleção em `APB1da::ConvflowRate()` e `APB1da::ConvflowRate(double Q)`:

```text
idQ == 4 -> Conv_bbmin_m3h(Q)
idQ == 6 -> Conv_bbmin_m3min(Q)
```

`calculateLOTFracturedSaltRock(...)` obtém `Qinj` por `ConvflowRate()` e usa
essa vazão no bloco de fratura, incluindo o ramo PKN.

Na varredura de `legance/LOT_APB_v5/`, não foram encontrados
`Conv_bbmin_m3h`, `Conv_bbmin_m3min`, `Q * 9.53924` nem `M_PI / 22`.

## 3. Casos PKN auditados

| Caso | Linha aprox. | Configuração LOT | `idQ` | Conversão associada | Passa por `/M_PI/22`? | Conclusão |
|------|--------------|------------------|-------|---------------------|-----------------------|-----------|
| `legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp` | 43, 137 | `setLeakoffProps("pa_min", 3., "pkn")`; `APB1da(..., true, 6, 0.5, 9.5)` | 6 | `Q * 0.158987 / M_PI / 2` | Não | R09 `/22` não está no caminho ativo deste caso. |
| `legance/LOT_Tese/9-BUZ-39DA-RJS-VISCO-2.cpp` | 41, 140 | `setLeakoffProps("pa_min", 1., "pkn")`; `APB1da(..., true, 6, 0.3)` | 6 | `Q * 0.158987 / M_PI / 2` | Não | R09 `/22` não está no caminho ativo deste caso. |

Observação: o comentário do segundo caso diz "0.4 bpm", mas o argumento passado
ao construtor é `0.3`. Este ensaio registra o valor de código, não corrige o
legado.

## 4. Tabela comparativa de fatores

A tabela abaixo usa o fator dimensional de `Conv_bbmin_m3h`, isto é,
`Q * 9.53924`, para comparar apenas o efeito dos divisores angulares.

| Q original | Alternativa | Valor convertido | Razão vs `/M_PI/2` | Observação |
|------------|-------------|------------------|--------------------|------------|
| 0.1 | `Q * 9.53924 / (M_PI * 22)` | 0.0138019745395 | 0.0909090909091 | Mesmo valor de `/M_PI/22`. |
| 0.1 | `Q * 9.53924 / (M_PI * 2)` | 0.151821719934 | 1.0 | Referência `/2`. |
| 0.1 | `Q * 9.53924 / (2 * M_PI)` | 0.151821719934 | 1.0 | Idêntico a `/M_PI/2`. |
| 0.3 | `Q * 9.53924 / (M_PI * 22)` | 0.0414059236184 | 0.0909090909091 | Mesmo valor de `/M_PI/22`. |
| 0.3 | `Q * 9.53924 / (M_PI * 2)` | 0.455465159802 | 1.0 | Referência `/2`. |
| 0.3 | `Q * 9.53924 / (2 * M_PI)` | 0.455465159802 | 1.0 | Idêntico a `/M_PI/2`. |
| 0.5 | `Q * 9.53924 / (M_PI * 22)` | 0.0690098726973 | 0.0909090909091 | Mesmo valor de `/M_PI/22`. |
| 0.5 | `Q * 9.53924 / (M_PI * 2)` | 0.75910859967 | 1.0 | Referência `/2`. |
| 0.5 | `Q * 9.53924 / (2 * M_PI)` | 0.75910859967 | 1.0 | Idêntico a `/M_PI/2`. |
| 1.0 | `Q * 9.53924 / (M_PI * 22)` | 0.138019745395 | 0.0909090909091 | Mesmo valor de `/M_PI/22`. |
| 1.0 | `Q * 9.53924 / (M_PI * 2)` | 1.51821719934 | 1.0 | Referência `/2`. |
| 1.0 | `Q * 9.53924 / (2 * M_PI)` | 1.51821719934 | 1.0 | Idêntico a `/M_PI/2`. |

Resumo numérico:

```text
(Q * 9.53924 / (pi * 22)) / (Q * 9.53924 / (pi * 2)) = 2 / 22 = 1/11
```

Logo, para o ramo `idQ == 4`, a expressão com `/22` gera uma vazão convertida
onze vezes menor que a alternativa com `/2`.

## 5. Interpretação física/dimensional

O fator `9.53924` é compatível com a conversão dimensional pura:

```text
1 bbl/min * 0.158987 m3/bbl * 60 min/h ~= 9.53922 m3/h
```

Dividir por `M_PI`, `2` ou `22` não altera unidade, pois todos são fatores
adimensionais. A unidade presumida de saída de `Conv_bbmin_m3h` continua sendo
`m3/h`, mas a magnitude é modificada por uma normalização geométrica ou empírica
não documentada.

Em C++, os operadores de divisão são associativos à esquerda:

```text
Q * 9.53924 / M_PI / 2  == (Q * 9.53924 / M_PI) / 2  == Q * 9.53924 / (M_PI * 2)
Q * 9.53924 / M_PI / 22 == (Q * 9.53924 / M_PI) / 22 == Q * 9.53924 / (M_PI * 22)
```

A diferença entre `/22` e `/2` é exatamente fator 11 porque:

```text
(1 / (pi * 2)) / (1 / (pi * 22)) = 22 / 2 = 11
```

## 6. Impacto no projeto moderno

**O `PknModel` moderno deve copiar alguma dessas expressões?**  
Não. O modelo moderno deve receber vazão em SI puro e deixar fatores
geométricos dentro da formulação física documentada, não no parser nem em uma
conversão de unidade herdada.

**O `PknModel` moderno deve continuar usando apenas SI?**  
Sim. A Fase 6.6 reforça que conversão de unidade e fator geométrico devem ficar
separados. O parser moderno deve converter `bbl_min`, `m3_min`, `m3_h` etc. para
`m3/s` sem embutir `pi`, `2` ou `22`.

**A regressão legado x moderno pode ser liberada?**  
Não de forma geral. A regressão quantitativa contra o legado continua bloqueada
para qualquer caso que use `idQ == 4` e para qualquer comparação que dependa da
família de conversões do legado sem separar unidade e fator geométrico.

**Para quais casos o R09 ainda bloqueia comparação?**  
Bloqueia casos com `idQ == 4`, casos cujo `idQ` de geração do `.dat` não esteja
confirmado, e regressões que tentem tratar a família `ConvflowRate()` como uma
referência física geral.

**Para quais casos o R09 pode ser considerado mitigado?**  
Para os dois casos PKN explicitamente auditados:

- `8-BUZ-67D-RJS-VISCO-pkn.cpp`;
- `9-BUZ-39DA-RJS-VISCO-2.cpp`.

Neles, o ramo ativo é `idQ == 6`, não `idQ == 4`, portanto o literal `/22` não
altera diretamente a vazão usada no bloco PKN.

## 7. Conclusão operacional

**Rota escolhida:** Rota B — marcar R09 como
`MITIGATED_FOR_AUDITED_PKN_CASES`, mas manter `BLOCKER_FOR_IDQ4_REGRESSION`.

Justificativa:

- Há prova direta de que os dois casos PKN auditados usam `idQ == 6`.
- Há prova direta de que `/M_PI/22` é usado por `idQ == 4`, não por `idQ == 6`.
- O ensaio analítico quantifica o impacto: `/22` produz `1/11` da conversão
  correspondente com `/2`.
- Ainda não há justificativa documental para o `22`.
- Ainda não houve regressão numérica legado x moderno.

Portanto, R09 fica mais preciso: não é bloqueio total para evoluir o pipeline
moderno e para fazer comparações qualitativas cuidadosamente rotuladas nos dois
casos PKN auditados, mas continua bloqueando regressão quantitativa legado x
moderno quando `idQ == 4` ou o caminho de geração do dado legado não estiver
provado.
