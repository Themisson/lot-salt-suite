# Integração temporal — explícito vs implícito adaptativo

## Decisão padrão por etapa
- **Etapas 0–2** (elástico → mecanismo duplo → primária): integrador **explícito** ("fully
  explicit", Zienkiewicz & Taylor 2000). Simples, suficiente para halita e tensões moderadas.
- **Etapa 4** (terciária + dano) e antes dos **casos severos** (taquidrita, k0 > 1):
  integrador **implícito adaptativo** (backward Euler com Newton local no ponto de Gauss +
  passo adaptativo). Sem isso, repete o problema do "modelo F" do TCC (resultado contra a
  segurança a partir de ~100h de simulação).
- **Etapa 6** (térmico): Crank-Nicolson (β=½) no problema térmico isolado, incondicionalmente
  estável. Acoplamento ao mecânico é fraco — cada um tem seu próprio ∆t.

A flag `time.scheme` no YAML do caso seleciona: `explicit` | `implicit_adaptive`.

## Por que explícito funciona na Etapa 1–2
A K elástica é constante e fatorada uma vez. A cada passo:
1. Avaliar lei constitutiva em cada ponto de Gauss → taxa viscosa ε̇^v.
2. Montar pseudo-força viscosa Δf^v = ∫ Bᵀ D ε̇^v dt dΩ.
3. Resolver K Δu = Δf^v (back-substitution barata).
4. Atualizar tensões, estado, e seguir.

Custo por passo: O(N · banda). Custo total: linear no número de passos. Para halita com
tensões moderadas, ∆t ~ 0.5h dá milhares de passos numa simulação de 480h — segundos no C++.

## Quando o explícito quebra
Três sintomas, todos visíveis nos resultados do TCC:
1. **Tensão desviadora alta** (k0 > 1, ou pressão de fluido baixa): a taxa de creep cresce
   muito rápido com a tensão; o passo explícito subestima a relaxação e o deslocamento
   começa a oscilar ou divergir.
2. **Litologia muito móvel** (taquidrita, carnalita): taxa ~10^7× a halita. Mesmo passo
   pequeno não basta; o erro acumula.
3. **Início da terciária**: a aceleração da deformação viola a hipótese de quasi-equilíbrio
   por passo do explícito.

Sintoma diagnóstico: o subagente `verifier` flagga "erro contra a segurança" — o solver
estima MENOS deformação que o ABAQUS/SESTSAL. Isso NÃO é otimismo numérico; é instabilidade.

## Integrador implícito adaptativo (Etapa 4+)
Esquema sugerido (backward Euler com Newton local):
```
para cada passo Δt:
    chute inicial: estado^{n+1} = estado^n
    repetir (Newton local em cada PG):
        avaliar lei constitutiva em estado^{n+1}
        formar resíduo R = ε̇^v · Δt − (ε^{v,n+1} − ε^{v,n})
        resolver J · δ = −R  (J = ∂R/∂ε^{v,n+1}, pequena: tamanho do tensor desviador)
        ε^{v,n+1} += δ
    até ‖R‖ < tol_local
    montar pseudo-força com a taxa convergida
    resolver K Δu = Δf^v com a K constante já fatorada
    estimar erro do passo (ex.: comparação com passo Δt/2)
    se erro > tol_global: rejeitar passo, reduzir Δt; senão aceitar e aumentar Δt
```

Pontos críticos:
- O Newton local é **por ponto de Gauss**, não global. A jacobiana é pequena (3×3 ou 6×6
  no tensor desviador). Custo: ~5–10 iterações por PG, em poucos passos do esquema externo.
- O erro global é estimado por comparação (passo dobrado vs. dois meio-passos) ou por uma
  fórmula embedded (estilo Runge-Kutta-Fehlberg).
- ∆t mínimo: parar a simulação se ∆t < ∆t_min indica modelo mal-condicionado, não solver ruim.

## Crank-Nicolson no térmico (Etapa 6)
- β = ½: 2ª ordem, incondicionalmente estável. Permite ∆t térmico >> ∆t mecânico.
- A matriz térmica `[C₂₂ + Δt·β·H₂₂]` é constante para Δt fixo — fatore uma vez.
- O problema térmico avança seu próprio passo; o mecânico interpola T(x, t) no ponto de
  Gauss quando precisa.
- Detalhe completo em `docs/thermal-coupling.md`.

## Verificação do integrador
- **Conservação no elástico-puro**: sem creep, sem térmico, o solver não deve mover nada
  entre passos (∆u = 0 após o passo elástico inicial).
- **Saturação primária→secundária**: na Etapa 2, com primária + secundária habilitadas, o
  estado interno deve saturar e a taxa convergir para a do mecanismo duplo puro.
- **Convergência temporal**: rodar o mesmo caso com ∆t, ∆t/2, ∆t/4 — solução deve convergir
  na taxa esperada do método (1ª ordem para Euler, 2ª para Crank-Nicolson).
- **Sem oscilação**: trajetória de fechamento × tempo deve ser monotônica não-decrescente
  em casos com pressão constante. Oscilação visível = passo grande demais (ou bug).

## O que NÃO fazer
- Não use Euler explícito para o térmico transiente — é condicionalmente estável e o ∆t
  estável é minúsculo (h² / α). Crank-Nicolson é o padrão.
- Não tente integrar primária + secundária + terciária + dano com explícito "porque é mais
  simples". Vai falhar silenciosamente nos casos severos.
- Não recalcule K a cada passo "para mais precisão". K é constante no acoplamento fraco; a
  única coisa que muda no lado esquerdo é se você trocar o integrador (e mesmo assim, só na
  primeira chamada do novo integrador).
