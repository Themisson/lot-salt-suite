# Caminho PKN legado

## Entrada do caso

O caso PKN mais direto auditado e `legance/LOT_Tese/main/8-BUZ-67D-RJS-VISCO-pkn.cpp`.
Ele configura:

- profundidade de teste;
- fluido anular com densidade, expansibilidade e compressibilidade;
- `setLeakoffProps("pa_min", 3., "pkn")`;
- geometria de pocos, revestimentos, cimentos e rochas;
- simulacao em minutos com `dt = 0.5`, tempo final `12.5`, vazao `0.5 bpm` e
  tempo sem injecao `9.5`.

Ha tambem o caso `legance/LOT_Tese/9-BUZ-39DA-RJS-VISCO-2.cpp`, que usa PKN com
viscosidade `1 cP` convertida para `pa_min` e escreve resultado PKN proprio.

## Rota de execucao

1. O caso chama `Fluids::setLeakoffProps(...)`.
2. A string `pkn` e convertida para `idTypeFracture == 2`.
3. `APB1da::getLOT(...)` injeta fluido nos elementos anulares durante a janela
   ativa de injecao.
4. `APB1da::calculateLOTFracturedSaltRock(...)` avalia a parede anular contra a
   rocha vizinha.
5. Quando a pressao de parede excede o limite usado pelo legado, o tempo de
   quebra e registrado.
6. Para `idTypeFracture == 2`, o bloco PKN calcula altura, abertura, comprimento
   e volume de leakoff/fratura.
7. `getdV(...)` incorpora `dV_leakoff` ao balanco volumetrico.
8. `saveFile(...)` grava series de pressao, volume, deslocamento, leakoff e
   momento da quebra.

## Variaveis fisicas observadas

| Variavel legado | Sentido observado |
|-----------------|------------------|
| `pw` | Pressao na parede/anular apos incremento. |
| `sigmaTheta` | Tensao circunferencial usada como limite, com inversao de sinal no legado. |
| `Qinj` | Vazao convertida pela familia `ConvflowRate()`. |
| `mu` | Viscosidade convertida para a unidade temporal escolhida. |
| `time` | Tempo desde o primeiro excesso de pressao, embora trechos PKN tambem usem `t`. |
| `h` | Altura efetiva calculada para PKN. |
| `w0` | Abertura caracteristica. |
| `L1` | Comprimento caracteristico. |
| `dV_leakoff` | Volume que entra no balanco APB/LOT. |

## Pontos que nao devem ser copiados cegamente

- A conversao de vazao mistura unidade e fator geometrico; o modelo moderno deve
  separar conversao SI de convencao geometrica.
- O bloco PKN usa `time` em algumas formulas e `t` absoluto em outra. Isso deve
  ser resolvido antes de declarar equivalencia.
- O volume PKN usa `w0 * L1 * M_PI`; ha alternativa comentada no legado. A
  escolha moderna precisa ser documentada.
- O criterio de breakdown deve obedecer as convencoes FA01-FA04 ja registradas.

## Referencia para implementacao moderna

A implementacao futura deve reproduzir o comportamento relevante por contrato:

- entrada SI;
- calendario de injecao e acomodacao explicito;
- deteccao de breakdown testavel;
- modelo PKN isolado de parsing;
- saida temporal comparavel aos arquivos `.dat` legados;
- documentacao de qualquer divergencia fisica.
