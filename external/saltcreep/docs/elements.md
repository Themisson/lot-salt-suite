# Tipos de elemento e estudo de convergência

## Interface `Element` (contrato)
Todo elemento expõe o mesmo contrato; o motor não sabe qual tipo está usando:
- funções de forma N(ξ) e derivadas dN/dξ nos pontos de Gauss;
- mapeamento isoparamétrico para coordenadas físicas e Jacobiano;
- matriz B (deformação–deslocamento) em coordenadas axissimétricas (inclui o termo u/r);
- número e posições dos pontos de Gauss;
- montagem da contribuição elementar de K e das pseudo-forças viscosas.

A formulação axissimétrica integra com peso 2πr (ou r, com a espessura unitária do TCC no 1D).
O termo `u/r` da deformação circunferencial ε_θθ é obrigatório e é onde mais se erra — teste isso
explicitamente.

## Catálogo (ordem de implementação)
1. `axisym_1d_L3` — radial, 3 nós, quadrático. É o do TCC. MVP.
2. `axisym_2d_Q4` — quadrilátero bilinear (r,z), 4 nós. Primeiro 2D; barato, baixa ordem. **Implementado.**
3. `axisym_2d_T3` — triângulo linear, 3 nós. Para malhas não estruturadas / geometrias com intercalação. **Implementado.**
4. `axisym_2d_Q8` — quadrilátero serendipity, 8 nós, quadrático. Boa precisão por GDL; recomendado p/ 2D. **Implementado.**
5. `axisym_2d_Q9` — Lagrangiano, 9 nós. Compare com Q8. **Implementado.**
6. `axisym_2d_T6` — triângulo quadrático, 6 nós. **Implementado.**
7. `axisym_2d_AQ9` — quadrilátero de 9 nós enriquecido pela base radial de Lamé `{1, r, 1/r}`.
   **Implementado.** Mantém 2 DOFs por nó, mas substitui a base radial polinomial do Q9 por uma base
   racional nodal que representa exatamente `u_r = a r + b/r`.

## Estudo de convergência (workflow)
Como o tipo de elemento é flag de caso, gere variantes do mesmo caso físico mudando só `element.type`
e `mesh.*`, rode todas, e compare:
- contra a solução elástica analítica de Lamé (erro deve cair ao refinar, na taxa esperada para a ordem
  do elemento: ~h² para linear, ~h³ para quadrático no deslocamento);
- entre si (devem convergir para a mesma resposta);
- custo (GDL, tempo) vs. precisão — é isso que decide o "melhor elemento para o caso".
O script `post/convergence.py` plota erro × GDL e erro × tempo para a família de variantes.

## Estudo de convergência Lamé — Etapa 3b completa
Caso comum usado no script: cilindro vazado elástico axissimétrico com `Ri = 1 m`, `Re = 3 m`,
`p_i = 1 MPa`, `p_e = 0`, `E = 25 GPa`, `nu = 0.30`. O erro medido é relativo em
`u_r(Ri)` contra a solução analítica de Lamé. Para os elementos 2D, `u_z` é fixado em todos
os nós e `u_r(Re)` recebe o deslocamento analítico, exatamente como nos testes de convergência.

Resultados atualizados por `python post/convergence.py` em 2026-05-31:

| Elemento | Malhas radiais | GDL final | Erro final | Taxa minima observada | Tempo final local |
| --- | ---: | ---: | ---: | ---: | ---: |
| `axisym_1d_L3` | 5, 10, 20, 40 | 81 | 9.771e-08 | 3.81 | 0.002 s |
| `axisym_2d_Q4` | 5, 10, 20, 40 | 1722 | 2.694e-04 | 1.91 | 0.089 s |
| `axisym_2d_T3` | 5, 10, 20, 40 | 3362 | 2.690e-04 | 1.88 | 0.193 s |
| `axisym_2d_Q8` | 3, 6, 12, 24 | 1874 | 5.214e-07 | 3.58 | 0.106 s |
| `axisym_2d_Q9` | 3, 6, 12, 24 | 2450 | 5.214e-07 | 3.58 | 0.121 s |
| `axisym_2d_AQ9` | 1, 2, 4 | 54 | 4.436e-16 | exato (machine epsilon) | 0.044 s |
| `axisym_2d_T6` | 3, 6, 12, 24 | 2450 | 4.614e-06 | 2.67 | 0.110 s |

Leitura: os elementos lineares Q4/T3 mantêm a taxa esperada próxima de h²; os quadráticos
Q8/Q9/T6 ficam acima do critério h³ operacional usado nos testes (`>= h^2.5`). O L3 continua
sendo o baseline radial mais eficiente para o Lamé puro; entre os 2D quadráticos, Q8 e Q9
empataram neste caso de geometria retangular, com Q8 usando menos GDL por não possuir nó central.
O AQ9 é o resultado de precisão por GDL: com 1 elemento radial ele já representa o campo de Lamé
no nível de erro de arredondamento, porque `1/r` pertence ao espaço de interpolação.

## Elementos implementados

### `axisym_2d_Q4`
- Domínio de referência: quadrado `xi, eta ∈ [-1,1]`.
- Ordem nodal anti-horária: `(-1,-1)`, `(1,-1)`, `(1,1)`, `(-1,1)`.
- Funções de forma: bilineares padrão `N_i = 1/4 (1 ± xi)(1 ± eta)`.
- Integração: Gauss `2x2`, quatro pontos `(±1/sqrt(3), ±1/sqrt(3))`, peso combinado `1`.
- DOFs por nó: `u_r`, `u_z`.
- Matriz B em Voigt `[epsilon_rr, epsilon_tt, epsilon_zz, gamma_rz]`, com
  `epsilon_tt = u_r/r_gp` usando `r_gp` interpolado no ponto de Gauss.
- Peso de integração: `2*pi*r_gp*abs(detJ)*w`.
- Verificação inicial: patch test linear, Lamé com taxa medida `>= h^1.8`, e regressão
  `modelo_A_Q4` compatível com a referência L3 dentro de 15% em regime permanente.

### `axisym_2d_T3`
- Domínio de referência: triângulo `xi >= 0`, `eta >= 0`, `xi + eta <= 1`.
- Ordem nodal: `(0,0)`, `(1,0)`, `(0,1)`.
- Funções de forma: `N0 = 1 - xi - eta`, `N1 = xi`, `N2 = eta`.
- Derivadas locais: constantes por elemento.
- Integração: regra triangular de 3 pontos em `(1/6,1/6)`, `(2/3,1/6)`, `(1/6,2/3)`,
  pesos `1/6` cada. A regra de centróide de 1 ponto reproduz patch linear, mas subintegra
  levemente o termo axissimétrico `N/r` no Lamé; os 3 pontos recuperam a taxa h² esperada.
- DOFs por nó: `u_r`, `u_z`.
- Matriz B em Voigt `[epsilon_rr, epsilon_tt, epsilon_zz, gamma_rz]`, com
  `epsilon_tt = u_r/r_gp` usando `r_gp` interpolado no ponto de Gauss.
- Peso de integração: `2*pi*r_gp*abs(detJ)*w`.
- Verificação inicial: patch test linear, Lamé com taxa medida `>= h^1.8`, e regressão
  `modelo_A_T3` compatível com a referência L3 dentro de 15% em regime permanente.

### `axisym_2d_Q8`
- Domínio de referência: quadrado `xi, eta ∈ [-1,1]`.
- Ordem nodal: cantos anti-horários `(-1,-1)`, `(1,-1)`, `(1,1)`, `(-1,1)`, seguidos
  pelos pontos médios `(0,-1)`, `(1,0)`, `(0,1)`, `(-1,0)`.
- Funções de forma: serendipity quadráticas de 8 nós.
- Integração: Gauss `3x3`, pontos `{-sqrt(3/5), 0, sqrt(3/5)}` e pesos `{5/9, 8/9, 5/9}`.
- DOFs por nó: `u_r`, `u_z`.
- Matriz B em Voigt `[epsilon_rr, epsilon_tt, epsilon_zz, gamma_rz]`, com
  `epsilon_tt = u_r/r_gp` usando `r_gp` interpolado no ponto de Gauss.
- Peso de integração: `2*pi*r_gp*abs(detJ)*w`.
- Verificação inicial: patch test linear, patch test quadrático, Lamé com taxa medida
  `>= h^2.5`, e regressão `modelo_A_Q8` compatível com a referência L3 dentro de 15%
  em regime permanente.

### `axisym_2d_Q9`
- Domínio de referência: quadrado `xi, eta ∈ [-1,1]`.
- Ordem nodal: cantos anti-horários e pontos médios como Q8, com centro `(0,0)` como nó 8.
- Funções de forma: produto tensorial dos polinômios de Lagrange 1D quadráticos em
  `{-1,0,1}`.
- Integração: Gauss `3x3`, pontos `{-sqrt(3/5), 0, sqrt(3/5)}` e pesos `{5/9, 8/9, 5/9}`.
- DOFs por nó: `u_r`, `u_z`.
- Matriz B em Voigt `[epsilon_rr, epsilon_tt, epsilon_zz, gamma_rz]`, com
  `epsilon_tt = u_r/r_gp` usando `r_gp` interpolado no ponto de Gauss.
- Peso de integração: `2*pi*r_gp*abs(detJ)*w`.
- Verificação inicial: patch test linear, patch test quadrático, Lamé com taxa medida
  `>= h^2.5`, e regressão `modelo_A_Q9` compatível com a referência L3 dentro de 15%
  em regime permanente.

### `axisym_2d_AQ9`
- Domínio de referência legado: `xi ∈ [1,2]`, `eta ∈ [-1,1]`; no contrato público, chamadas de
  borda com `xi = -1` e `xi = 1` são convertidas para `xi = 1` e `xi = 2`.
- Ordem nodal: a mesma do Q9 (`BL, BR, TR, TL, BM, RM, TM, LM, C`), com 2 DOFs por nó
  (`u_r`, `u_z`) e sem DOFs extras de enriquecimento.
- Base radial enriquecida: funções nodais `R_L(r)`, `R_M(r)`, `R_R(r)` interpolam exatamente
  a base `{1, r, 1/r}` nos raios `rL`, `rM = (rL+rR)/2`, `rR`.
- Base axial: Lagrange quadrática padrão em `eta = {-1,0,1}`. As funções de forma são o produto
  tensorial `R_a(r) E_b(eta)`.
- Integração: 4 pontos radiais especiais x 3 pontos de Gauss em `eta`, seguindo o Matlab legado.
  A quadratura radial ajusta momentos de `1`, `xi`, `xi^2`, `xi^3`, `1/(xi-ct)`,
  `1/(xi-ct)^2`, `1/(xi-ct)^3`; todos os pesos são validados como positivos.
- Matriz B: mesma ordem Voigt do restante do solver `[epsilon_rr, epsilon_tt, epsilon_zz, gamma_rz]`,
  com `epsilon_tt = u_r/r_gp`.
- Verificação inicial: patch linear, reprodução exata da base de Lamé na matriz B, Lamé com 1 elemento
  em erro de machine epsilon, e regressão `modelo_A_AQ9` compatível com a referência L3.

### `axisym_2d_T6`
- Domínio de referência: triângulo `xi >= 0`, `eta >= 0`, `xi + eta <= 1`.
- Coordenadas baricêntricas: `L1 = 1 - xi - eta`, `L2 = xi`, `L3 = eta`.
- Ordem nodal: cantos `(0,0)`, `(1,0)`, `(0,1)`, seguidos pelos pontos médios
  `(1/2,0)`, `(1/2,1/2)`, `(0,1/2)`.
- Funções de forma: quadráticas padrão
  `L1(2L1-1)`, `L2(2L2-1)`, `L3(2L3-1)`, `4L1L2`, `4L2L3`, `4L3L1`.
- Integração: Dunavant de 6 pontos, grau 4, com pesos de área somando `1/2`.
- DOFs por nó: `u_r`, `u_z`.
- Matriz B em Voigt `[epsilon_rr, epsilon_tt, epsilon_zz, gamma_rz]`, com
  `epsilon_tt = u_r/r_gp` usando `r_gp` interpolado no ponto de Gauss.
- Peso de integração: `2*pi*r_gp*abs(detJ)*w`.
- Verificação inicial: patch test linear, patch test quadrático, Lamé com taxa medida
  `>= h^2.5`, e regressão `modelo_A_T6` compatível com a referência L3 dentro de 15%
  em regime permanente.

## Refinamento adaptativo (camada posterior, NÃO no MVP)
- Estimador de erro a posteriori (ex.: recuperação de gradiente tipo Zienkiewicz–Zhu) marca elementos
  com erro alto (concentrados na parede do poço) para refino h.
- Só implementar depois que a malha fixa em progressão geométrica estiver validada — o refino na parede
  por progressão geométrica já resolve a maior parte do ganho com custo trivial.
- A escolha "adaptativo vs. progressão geométrica fixa" é por caso: para o poço axissimétrico, a
  localização do gradiente é conhecida (parede), então malha graduada fixa costuma bastar; adaptativo
  ganha quando há intercalações com gradientes em posições não óbvias.
