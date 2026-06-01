# Acoplamento termomecânico fraco

Referência operacional: Vasconcelos, T. S. *Modelagem termomecânica do crescimento de pressão em
anulares confinados em poços de petróleo na presença de evaporitos*. Dissertação de Mestrado, UFAL,
2019. Seção 3.3.4. PDF em `docs/references/vasconcelos_2019.pdf` (se versionado).

Este documento distila o algoritmo da dissertação no que é necessário para implementar — o agente
NÃO precisa reler o PDF salvo para ambiguidade pontual (use `@docs/references/vasconcelos_2019.pdf`).

## Decisão
Acoplamento **fraco** (one-way): térmico → mecânico, **não** mecânico → térmico. Justificativa
direto da dissertação (Dadvand, 2007, classifica acoplamento por nível de interação; aqui o
mecânico sobre o térmico é desprezível, e o ganho de manter K constante é grande).

## Como a temperatura entra no problema mecânico (dois caminhos)
**Decomposição aditiva da deformação total** (Lubliner, 2006):
$$\varepsilon = \varepsilon^{e} + \varepsilon^{v} + \varepsilon^{th}$$

1. **ε^th direto**: deformação térmica do material, contribui para o lado direito do sistema mecânico
   como pseudo-força térmica equivalente.
2. **Arrhenius na lei de creep**: T(x,t) entra em `exp[(Q/R)(1/T0 − 1/T)]` na taxa viscosa do
   mecanismo duplo (Costa & Poiate Jr., 2008). A temperatura no ponto material acelera/desacelera ε^v.

Resultado: K elástica continua constante; T só altera o lado direito (ε^th e ε̇^v).

Convenção de unidade: os modelos constitutivos recebem sempre temperatura em Kelvin. O parser
converte campos YAML com sufixo `_C` para K; campos `T_K` e parâmetros constitutivos `T0`
devem ser fornecidos diretamente em Kelvin.

Na implementação mecânica incremental:
$$\varepsilon^{th} = \alpha (T_{gp} - T_{ref}) [1, 1, 1, 0]^T$$
e a pseudo-força térmica é montada como
$$\Delta\mathbf{f}^{th} = \int B^T D\,\Delta\varepsilon^{th}\,dV.$$
As tensões são atualizadas por
$$\sigma = D(Bu - \varepsilon^v - \varepsilon^{th}) + \sigma_{geo}.$$

## Problema térmico — 1D axissimétrico radial (Fourier)
Equação governante (sem geração interna):
$$\frac{1}{r}\frac{\partial}{\partial r}\!\left(k\,r\,\frac{\partial T}{\partial r}\right) = \rho\,c_P\,\frac{\partial T}{\partial t}$$

Condições:
- Inicial: T(r,0) = T_0  (perfil inicial uniforme ou geostático).
- Contorno interno r = Ri: temperatura prescrita T(Ri,t) = T̄(t) (perfil de produção/perfuração).
- Contorno externo r = Re: temperatura prescrita T(Re,t) = T_ext por padrão (`outer_bc: prescribed`)
  ou fluxo radial nulo q_r(Re,t) = 0 (`outer_bc: flux_zero`) para domínio suficientemente afastado.

## Problema térmico — 2D axissimétrico (r,z)
Quando há intercalações ou contraste vertical de condutividade, o modo `conduction_2d` resolve:
$$\frac{1}{r}\frac{\partial}{\partial r}\!\left(k\,r\,\frac{\partial T}{\partial r}\right)
 + \frac{\partial}{\partial z}\!\left(k\,\frac{\partial T}{\partial z}\right)
 = \rho\,c_P\,\frac{\partial T}{\partial t}$$

A discretização usa a mesma malha 2D e o mesmo `Element` declarado no YAML. As matrizes são:
$$C_{ij} = \int \rho c_P N_i N_j\,2\pi r\,dA,\qquad
H_{ij} = \int k(\nabla N_i\cdot\nabla N_j)\,2\pi r\,dA,$$
com $\nabla=[\partial/\partial r,\partial/\partial z]$. Em cada ponto de Gauss, `k`, `rho` e
`cP` vêm da camada `thermal.layers` cujo intervalo contém a coordenada z do ponto. Sem `layers`,
o campo usa as propriedades térmicas uniformes do bloco `thermal`.

Condições de contorno:
- Parede interna r = Ri: temperatura prescrita do fluido (`inner_wall_temp_C`).
- Borda externa r = Re: `outer_bc: prescribed` ou `flux_zero`.
- Topo z = 0: `top_bc: prescribed` ou `flux_zero`.
- Base z = L: `bottom_bc: prescribed` ou `flux_zero`.

## Discretização espacial — FEM, MESMA família de elementos do mecânico
Resíduos ponderados (Galerkin) com integração por partes resulta em:
$$\mathbf{C}\,\dot{\mathbf{T}} + \mathbf{H}\,\mathbf{T} + \mathbf{f} = \mathbf{0}$$
onde C é a matriz de capacidade térmica e H a de condutividade. **Use elementos quadráticos de 3 nós
no 1D (L3), os mesmos do problema mecânico** — assim a interpolação de T no ponto de Gauss da lei
de creep é trivial. Para 2D, use o mesmo tipo do mecânico declarado no YAML.

Sistema particionado (T1 = grau prescrito da parede; T2 = demais graus):
$$\mathbf{C}_{22}\dot{\mathbf{T}}_2 + \mathbf{H}_{22}\mathbf{T}_2 + \mathbf{C}_{21}\dot{\mathbf{T}}_1 + \mathbf{H}_{21}\mathbf{T}_1 = \mathbf{0}$$

## Integração temporal — Crank–Nicolson (β = ½)
Equação de recorrência:
$$\bigl[\mathbf{C}_{22} + \Delta t\,\beta\,\mathbf{H}_{22}\bigr]\mathbf{T}_2^{t+\Delta t}
= \bigl[\mathbf{C}_{22} - \Delta t(1-\beta)\,\mathbf{H}_{22}\bigr]\mathbf{T}_2^{t} - \ldots$$

β = ½ → Crank–Nicolson, **incondicionalmente estável, precisão de 2ª ordem**. Esse é o padrão do
modo `conduction_*`. Para diagnóstico, suporte também β=1 (Euler implícito) e β=0 (Euler explícito,
condicional).

## Acoplamento ao laço mecânico
O problema térmico tem seu próprio ∆t térmico (Crank–Nicolson permite passos maiores que o mecânico).
Estratégia padrão:
```
inicialização:
    montar C, H (uma vez; k e ρ·cP constantes por litologia)
    fatorar [C22 + Δt·β·H22] uma vez por valor de Δt térmico
loop temporal mecânico:
    se hora de atualizar T:
        avançar T um (ou poucos) passos de Crank-Nicolson
    para cada ponto de Gauss mecânico:
        T_pg = interpola T no ponto                  # do ThermalField
        ε^th = α (T_pg − T_ref)                       # pseudo-força térmica
        ε̇^v  = lei_de_creep(σ, estado, T_pg, dt)      # Arrhenius usa T_pg
    montar Δf = Δf^v + Δf^th ;  resolver K Δu = Δf ;  atualizar
```
Como K é constante, fatorada uma vez. A matriz térmica [C22 + Δt·β·H22] também é constante para Δt
fixo — fatore uma vez também.

## Modos do `ThermalField`
- `profile` (default): T(z) analítico do TCC (gradientes por camada). Sem EDP térmica. Mais barato.
  Use quando o transiente térmico for irrelevante para o caso.
- `conduction_1d`: resolve a EDP de Fourier 1D radial pelo algoritmo acima. Padrão para casos com
  prescrição de T(t) na parede (produção/perfuração). O contorno externo pode ser `prescribed`
  (padrão; validação estacionária com perfil logarítmico) ou `flux_zero`.
- `conduction_2d`: resolve (r,z) com propriedades por camada; use quando contraste de condutividade
  ao longo de z importar.

## Interface
`ThermalField::temperature_at(x, t) -> T`. Implementações: `ProfileField`, `Conduction1DField`,
`Conduction2DField`. A lei de creep recebe T pela assinatura de `evaluate(...)` — ela não sabe de
onde T veio.

## Verificação (parte do `verifier`)
1. `profile` reproduz exatamente o T(z) do TCC (Equação 3 do TCC) para os casos A–F.
2. `conduction_1d` reproduz `profile` no limite estacionário com k uniforme e gradiente linear.
3. `conduction_2d` reproduz `conduction_1d` no limite uniforme com fluxo nulo em topo/base, conserva
   energia discretamente e mostra atraso térmico qualitativo em camada de baixa condutividade.
4. Reprodução qualitativa dos casos termomecânicos da dissertação Vasconcelos (2019) quando o
   caso existir em `cases/`.
5. Conservação de energia no problema térmico isolado (integral de fluxo bate com variação de
   energia interna, dentro da tolerância).

## O que NÃO fazer
- Não monte um sistema acoplado [K_uu K_uT; K_Tu K_TT]. Isso é forte; aqui é fraco.
- Não atualize K a cada passo "porque a temperatura mudou". Os módulos elásticos do sal NÃO dependem
  fortemente de T na faixa de operação (Costa & Poiate Jr., 2008); ignorar a variação é parte da
  hipótese de acoplamento fraco. Se um dia for necessário, vira outra decisão arquitetural.
- Não use o mesmo Δt no térmico e no mecânico só "porque é mais simples". Crank–Nicolson aceita Δt
  grande; o mecânico no regime de taquidrita não.
