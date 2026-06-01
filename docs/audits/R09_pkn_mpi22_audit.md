# R09 — Auditoria `/ M_PI / 22` no caminho PKN

**Data:** 2026-06-01  
**Escopo:** auditoria somente leitura de `legance/LOT_Tese/` e `legance/LOT_APB_v5/`.  
**Classificacao:** `NAO RESOLVIDO: requer ensaio numerico comparativo`.

## Localizacao exata

A expressao suspeita aparece uma unica vez na varredura dos legados:

```cpp
constexpr double Conv_bbmin_m3h(double Q) { return Q * 9.53924 / M_PI / 22; }
```

Localizacao:

| Item | Valor |
|------|-------|
| Arquivo | `legance/LOT_Tese/src/apb_code/APB1da.cpp` |
| Linha aproximada | 8 |
| Funcao | `Conv_bbmin_m3h(double Q)` |
| Entrada | `Q`, vazao informada pelo caso |
| Saida | `Qt`, vazao convertida em `APB1da::ConvflowRate()` quando `idQ == 4` |
| Expressao suspeita | `Q * 9.53924 / M_PI / 22` |

O bloco de conversoes no topo do arquivo e:

```cpp
constexpr double Conv_bbs_m3s(double Q) { return Q * 0.158987 / M_PI / 2; }
constexpr double Conv_bbmin_m3s(double Q) { return Q * 0.00264979 / M_PI / 2; }
constexpr double Conv_bbh_m3s(double Q) { return Q * 4.41631E-5 / M_PI / 2; }
constexpr double Conv_bbs_m3h(double Q) { return Q * 572.354 / M_PI / 2; }
constexpr double Conv_bbmin_m3h(double Q) { return Q * 9.53924 / M_PI / 22; }
constexpr double Conv_bbh_m3h(double Q) { return Q * 0.158987 / M_PI / 2; }
constexpr double Conv_bbmin_m3min(double Q) { return Q * 0.158987 / M_PI / 2; }
```

## Fluxo de dados

`APB1da` recebe `idQ` e `Q` nos construtores LOT:

```cpp
APB1da(..., const bool _LOT, unsigned int _idQ, double _Q)
APB1da(..., const bool _LOT, unsigned int _idQ, double _Q, const double _t_no_injection)
```

Esses valores sao armazenados em `this->idQ` e `this->Q`. A funcao
`APB1da::ConvflowRate()` seleciona a conversao:

```cpp
if (idQ == 4) {
    Qt = Conv_bbmin_m3h(Q);
}
else if (idQ == 6) {
    Qt = Conv_bbmin_m3min(Q);
}
```

No caminho de fratura, `calculateLOTFracturedSaltRock(...)` usa:

```cpp
double Qinj = ConvflowRate(); // Vazao de injecao
```

Para PKN (`idTypeFracture == 2`), `Qinj` entra em:

```cpp
double h = ... pow(mu * Qinj * Qinj * t * G * pow(dP_leakoff, 2) * ..., 1. / 3) ...
double w0 = 2.5 * pow((1 - nu) * mu * pow(Qinj, 2) / (G * h), 1. / 5.) * pow(time, 1. / 5.);
double L1 = 0.68 * pow(G * pow(Qinj, 3) / ((1 - nu) * mu * pow(h, 4)), 1. / 5.) * pow(time, 4. / 5.);
this->layers.line_up[lu].dV_leakoff(idAnnular) = w0 * L1 * M_PI;
```

Depois, `dV_leakoff` entra no balanco de volume:

```cpp
this->layers.line_up[lu].dV(e) += this->layers.line_up[lu].dV_leakoff(e);
```

E e escrito multiplicado por `2 * M_PI`:

```cpp
this->results[lu].dV_leakoff * 2. * M_PI
```

## Achado importante: BUZ67D PKN nao usa `idQ == 4`

O caso PKN auditado `legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp` usa:

```cpp
APB1da simulation(0.5, 0.1, 1E-8, 12.5, 0, false, true, 6, 0.5, 9.5);
```

Ou seja, `idQ == 6`. Esse caminho chama:

```cpp
constexpr double Conv_bbmin_m3min(double Q) { return Q * 0.158987 / M_PI / 2; }
```

O caso `legance/LOT_Tese/9-BUZ-39DA-RJS-VISCO-2.cpp` tambem usa `idQ == 6`.

Conclusao local: a expressao `/ M_PI / 22` existe e e suspeita, mas nao foi
encontrada como conversao ativa nos dois casos PKN explicitamente auditados.
Ela pertence ao ramo `bb/min -> m3/h` (`idQ == 4`), enquanto esses PKN usam
`bb/min -> m3/min` (`idQ == 6`).

## Inspecao em `LOT_APB_v5`

Na varredura de `legance/LOT_APB_v5/`, nao foi encontrada a expressao
`/ M_PI / 22`. O ramo moderno APB/JSON tem `dV_leakoff`, mas usa outra logica de
leakoff (`leakoff_coefficient * sqrt(time * dP_leakoff)`) e nao o bloco PKN do
`LOT_Tese`.

## Analise dimensional

Para `Conv_bbmin_m3h`, o nome sugere conversao de barris por minuto para metros
cubicos por hora.

Conversao dimensional pura:

```text
Q [bbl/min] * 0.158987 [m3/bbl] * 60 [min/h]
= Q * 9.53922 [m3/h]
```

O fator `9.53924` e coerente com essa conversao. Dividir por `M_PI` e por `22`
nao muda dimensao, porque ambos sao adimensionais, mas altera o valor numerico.
Portanto:

- antes de `/ M_PI / 22`: `m3/h`;
- depois de `/ M_PI / 22`: continua `m3/h`, mas escalado por `1 / (22*pi)`;
- a unidade e preservada, mas a grandeza fisica e mascarada por fator geometrico
  ou empirico sem documentacao local.

Como as outras conversoes usam `/ M_PI / 2`, ha um padrao claro de dividir a
vazao por `2*pi`. Isso parece representar uma normalizacao axissimetrica ou por
simetria angular, especialmente porque resultados de volume sao posteriormente
multiplicados por `2*pi` na escrita. Nesse contexto, o `22` destoa do padrao.

## Comparacao com alternativas

Para a mesma vazao bruta `Q * 9.53924`, as alternativas sao:

| Hipotese | Fator aplicado | Relacao contra `/ M_PI / 22` |
|----------|----------------|-------------------------------|
| `/ M_PI / 22` | `1 / (22*pi)` | referencia |
| `/ M_PI / 2` | `1 / (2*pi)` | 11 vezes maior |
| `/ (M_PI * 2)` | `1 / (2*pi)` | 11 vezes maior |
| `/ (M_PI * 22)` | `1 / (22*pi)` | igual ao codigo atual |
| fator empirico | indeterminado | requer fonte externa ou ajuste documentado |

Em C++, `/ M_PI / 22` e avaliado como `(valor / M_PI) / 22`, equivalente a
`valor / (M_PI * 22)`. A hipotese `/ (M_PI * 22)` nao e alternativa numerica:
ela descreve exatamente o comportamento atual.

Quantificacao:

```text
(valor / (pi * 2)) / (valor / (pi * 22)) = 22 / 2 = 11
```

Assim, se um caso usar `idQ == 4`, trocar conceitualmente `22` por `2` aumenta
`Qinj` por fator 11. O inverso reduz `Qinj` para `1/11` do valor esperado pelo
padrao das demais conversoes.

## Impacto numerico esperado

Se o ramo `idQ == 4` for usado em PKN:

- `Qinj` fica 11 vezes menor com `/22` do que ficaria com `/2`.
- `h`, `w0` e `L1` dependem de potencias de `Qinj`, entao o efeito nao e apenas
  linear nas variaveis intermediarias.
- `dV_leakoff = w0 * L1 * M_PI` muda diretamente, e depois e somado em `dV`.
- Como `dV` entra no balanco APB/LOT, a pressao calculada e o ponto aparente de
  fratura podem mudar.

Para os casos PKN auditados com `idQ == 6`, o impacto direto esperado e nulo,
porque o codigo chama `Conv_bbmin_m3min`, nao `Conv_bbmin_m3h`. Ainda assim, o
risco permanece para qualquer caso futuro que configure `idQ == 4` ou para
qualquer tentativa de usar a familia de conversoes do legado como referencia
geral sem separar unidade e fator geometrico.

## Conclusao

**Classificacao:** `NAO RESOLVIDO: requer ensaio numerico comparativo`.

Motivo:

- A expressao `/ M_PI / 22` e real, unica e dimensionalmente adimensional.
- Ela contradiz o padrao das demais conversoes (`/ M_PI / 2`).
- Nao ha comentario, tese, artigo ou fonte no codigo que justifique `22`.
- A auditoria demonstrou que os PKN BUZ67D e 9-BUZ-39DA auditados usam `idQ == 6`,
  entao o literal suspeito nao esta no caminho ativo desses casos.
- Mesmo assim, nao ha prova documental suficiente para substituir `22` por `2`
  ou para declarar o legado numericamente confiavel em todos os modos de vazao.

## Recomendacao para o projeto

1. O `PknModel` moderno nao deve reproduzir `Conv_bbmin_m3h` nem qualquer
   conversao com fator geometrico embutido.
2. O parser/contrato moderno deve converter taxa para SI puro (`m3/s`) e deixar
   qualquer fator geometrico dentro da formulacao fisica documentada do PKN.
3. `cases/lot_tese_migrated/buz67d_pkn.yaml` deve manter `R09_PENDING_REVIEW`,
   pois ainda ha outros pontos PKN pendentes: volume `w0 * L1 * M_PI`, uso de
   `t` absoluto na altura e uso de `time` nas demais expressoes.
4. A regressao PKN legado x moderno deve continuar bloqueada enquanto a
   consistencia numerica do caminho legado nao for demonstrada.
5. Podem avancar mesmo com R09 aberto:
   - testes unitarios sinteticos;
   - implementacao fisica minima em SI sem comparar contra legado;
   - testes dimensionais e monotonicidade;
   - comparacao controlada interna entre formulacoes documentadas.
6. Para desbloquear regressao contra legado, executar ensaio comparativo
   controlado com duas variantes locais fora do legado congelado:
   - variante A: comportamento atual `/ (pi * 22)` para `idQ == 4`;
   - variante B: hipotese padrao `/ (pi * 2)`;
   - e confirmar se os arquivos `.dat` PKN existentes foram gerados por `idQ == 6`
     ou por algum caminho que acione `idQ == 4`.
