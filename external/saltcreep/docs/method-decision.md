# Decisão de método: por que FEM (e não BEM/FVM/MPM)

Resumo da análise completa (ver o documento de viabilidade separado). Pontos que o agente deve tratar
como decididos:

- **FEM contínuo** é o motor, para 1D radial e 2D axissimétrico.
- **BEM rejeitado como motor principal**: a fluência é um termo de volume (integral de domínio), então
  o BEM precisaria de células internas de qualquer forma, perdendo sua única vantagem; matriz densa e
  não simétrica; dano/variáveis de estado internas são formulados ponto a ponto no domínio (CDM),
  o que não casa com discretização só de contorno. BEM continua útil, se quisermos, como verificador
  independente APENAS do campo elástico/visco-linear inicial.
- **FVM**: viável, sem ganho líquido, e custaria reconstruir a verificação contra ABAQUS (que é FEM).
- **MPM**: ferramenta para grandes deformações/fragmentação/superfície livre (ex.: halocinese geológica),
  não para fechamento sub-porcento de um contínuo bem-comportado. Fraqueza notória em condições de
  contorno na parede — exatamente onde está toda a ação.

## Onde estão o custo e o ganho
- NÃO é gargalo: resolver o sistema linear (K constante → fatorar uma vez).
- É gargalo: loop de integração viscosa por ponto de Gauss × número de passos.
- Ganhos por ordem de retorno: K fatorada uma vez → paralelizar Gauss points (OpenMP) →
  elemento enriquecido de Lamé na parede → integrador implícito adaptativo (destrava taquidrita e
  alta tensão desviadora) → SIMD → (GPU só se N for muito grande).
