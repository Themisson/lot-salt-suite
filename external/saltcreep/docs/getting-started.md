# Setup inicial e Etapa 0 — fundação do solver

Este doc orienta o agente na PRIMEIRA tarefa do projeto: criar a fundação elástica 1D
axissimétrica com as três interfaces (`Element`, `ConstitutiveModel`, `ThermalField`).
A partir daqui as etapas seguintes (mecanismo duplo, primária, etc.) se encaixam.

## Pré-requisitos no momento da Etapa 0
- Layout de pastas já criado: `main/`, `src/`, `include/Eigen/`, `cases/`, `data/`, `tests/`, ...
- `CMakeLists.txt` na raiz com C++20 e `target_include_directories(... main include)`.
- `.gitignore` configurado.
- Legado em `legacy/` (não tocar; só leitura via `legacy-explorer`).

## O que a Etapa 0 entrega
1. **Três interfaces base** (apenas headers em `main/`, sem implementação pesada ainda):
   - `main/elements/Element.hpp`         — contrato do elemento finito.
   - `main/constitutive/ConstitutiveModel.hpp` — contrato da lei de fluência.
   - `main/thermal/ThermalField.hpp`     — contrato do campo de temperatura.
2. **Primeiro elemento concreto**: `axisym_1d_L3` (3 nós quadrático, radial). Implementação
   em `main/elements/axisym_1d_L3.hpp` + `src/elements/axisym_1d_L3.cpp`.
3. **Parser de caso YAML** mínimo (`main/io/CaseParser.hpp` + `src/io/CaseParser.cpp`) que
   leia o schema de `docs/input-spec.md` — só os campos necessários pra Etapa 0
   (geometria, malha, fluido, K0, profundidades; flags de creep todos `false`).
4. **Solver elástico** que monta K (com termo `u/r` axissimétrico correto) e resolve
   `K·u = f_geo + f_fluido` para um caso elástico-puro.
5. **Saída** em `results/<caso>/` (CSV no mínimo; VTU se trivial — pode ficar pra Etapa 1).
6. **Teste analítico de Lamé**: caso elástico de cilindro vazado com solução fechada,
   tolerância apertada. Esse é o oráculo que vai sustentar TODAS as etapas seguintes.

## O que a Etapa 0 NÃO faz
- Nenhuma lei de fluência implementada ainda (só a interface). Stub que retorna zero é OK.
- Sem térmico (só a interface; implementação stub que devolve T constante).
- Sem 2D ainda. Sem dano. Sem integrador temporal além do passo elástico inicial.

## Contrato esperado das interfaces (esqueleto)

```cpp
// main/elements/Element.hpp
class Element {
public:
    virtual ~Element() = default;

    // Pontos de Gauss em coordenadas locais e seus pesos
    virtual std::span<const GaussPoint> gauss_points() const = 0;

    // Funções de forma e derivadas em ξ
    virtual void shape_functions(double xi, std::span<double> N) const = 0;
    virtual void shape_derivatives(double xi, std::span<double> dN_dxi) const = 0;

    // Matriz B em (r) com termo u/r axissimétrico — onde mais se erra; testar explicitamente
    virtual Eigen::MatrixXd B_matrix(double xi,
                                     std::span<const double> node_coords) const = 0;

    // Jacobiano e fator de peso (inclui 2πr ou r conforme convenção do projeto)
    virtual double jacobian_weight(double xi,
                                   std::span<const double> node_coords) const = 0;

    virtual int n_nodes() const = 0;
    virtual int n_dofs_per_node() const = 0;
};
```

```cpp
// main/constitutive/ConstitutiveModel.hpp
class ConstitutiveModel {
public:
    virtual ~ConstitutiveModel() = default;

    // Taxa de deformação viscosa no ponto material, dado tensão, estado, temperatura, dt.
    // Retorna também a atualização do estado interno e (se houver) dano.
    virtual ViscousResult evaluate(const Stress& sigma,
                                   const InternalState& state,
                                   double T, double dt) const = 0;

    // Matriz constitutiva elástica D (constante para o material — não depende de T no
    // acoplamento fraco). Usada na montagem de K.
    virtual Eigen::MatrixXd D_elastic() const = 0;
};
```

```cpp
// main/thermal/ThermalField.hpp
class ThermalField {
public:
    virtual ~ThermalField() = default;

    // Temperatura no ponto físico x e instante t (acoplamento fraco).
    virtual double temperature_at(const Eigen::Vector2d& x, double t) const = 0;

    // Para uso na pseudo-força térmica: ε^th = α (T − T_ref).
    virtual double alpha_thermal() const = 0;
    virtual double T_reference() const = 0;
};
```

Os tipos auxiliares (`GaussPoint`, `Stress`, `InternalState`, `ViscousResult`) ficam em
`main/types.hpp` ou similar — o agente decide a granularidade.

## Padrão axissimétrico — o lugar onde se erra
Em problema axissimétrico (r,z) com simetria, a matriz B inclui a deformação circunferencial
ε_θθ = u_r / r. Em 1D radial (espessura unitária do TCC), a matriz B em cada ponto de Gauss é:
```
       [ dN_i/dr ]              ← ε_rr
B_i  = [  N_i/r  ]              ← ε_θθ
       [   0     ]              ← ε_zz (impedido)
```
Sem o termo `N_i/r` o resultado parece razoável visualmente mas falha o teste de Lamé. **Esse
teste detecta exatamente esse bug.** Por isso o teste analítico vem ANTES do mecanismo duplo.

## Teste de Lamé (oráculo de aceitação)
Cilindro vazado infinito, pressão interna p_i e externa p_e, material elástico isotrópico:
- σ_rr(r) = A + B/r²
- σ_θθ(r) = A − B/r²
com A e B determinados por p_i e p_e. O deslocamento radial u_r(r) tem forma fechada também.

Casos de teste sugeridos:
1. Só pressão interna (p_e = 0). Comparar u_r(R_i) com solução analítica.
2. Só pressão externa (p_i = 0). Mesmo critério.
3. Ambas (cilindro espesso completo).
4. **Convergência:** rodar com malha 10, 30, 100 elementos; erro deve cair na taxa ~h³ para
   o L3 quadrático. Se cair como ~h² ou pior, há bug na matriz B (provavelmente no `u/r`).

Tolerância: erro relativo no deslocamento radial < 1e-6 para malha de 30 elementos com
progressão geométrica refinando na parede.

## Fluxo recomendado para a Etapa 0
1. **Em plan mode**: propor estrutura de arquivos e cabeçalhos das três interfaces.
2. Aprovar o plano. Sair do plan.
3. Implementar interfaces (só headers) e `axisym_1d_L3`.
4. Implementar parser de YAML mínimo + montagem K + solver elástico.
5. Implementar teste de Lamé.
6. Invocar subagente `verifier`. Se Lamé passa, Etapa 0 concluída.
7. Commit: `feat(solver): fundação elástica 1D axissimétrica + teste Lamé OK`.

## Sem inventar — quando parar e perguntar
- Se uma decisão tem mais de uma escolha razoável e o doc não orienta (ex.: ordem dos GDLs no
  vetor global, convenção de sinal de tensão, formato exato do YAML), PARE e pergunte.
- Se um teste falhar mas a tolerância parece estranha, PARE — não relaxe a tolerância.
- Se for tentado a editar algo em `legacy/`: NÃO. Use o `legacy-explorer`.
