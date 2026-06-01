# Guia de desenvolvimento para extensões

Este guia explica como estender o SaltCreep com segurança. A regra central é simples:
adicione comportamento novo pelas interfaces plugáveis, preserve os invariantes físicos e só declare
pronto depois de passar pela bateria completa de verificação.

## 1. Arquitetura geral

```text
Parser YAML
  -> factories criam Element, ConstitutiveModel e ThermalField
  -> Mesh (nodes, elements)
  -> Assembler (monta K, f e pseudo-forças)
  -> TimeIntegrator (resolve u, atualiza estado)
  -> ConstitutiveModel (avalia eps_dot, D_dot, sigma)
  -> Output (CSV, VTU/PVD, closure, metadados)
```

Fluxo de execução:

1. `CaseParser` carrega o YAML e converte unidades para SI.
2. As factories selecionam elemento, modelo constitutivo e campo térmico pelo nome.
3. O pre-processamento opcional executa refinamento adaptativo h.
4. O loop temporal avança em `dt`: resolve deslocamentos, atualiza deformações viscosas/dano e
   grava saídas.
5. `metadata.json` registra malha, flags, timers, threads e opções principais para pós-processamento.

## 2. Como adicionar um novo modelo constitutivo

### Passo a passo

1. Herde de `ConstitutiveModel`.

```cpp
class MeuModelo : public ConstitutiveModel {
public:
    EvaluationResult evaluate(const Stress& sigma,
                              const InternalState& state_in,
                              double T,
                              double dt) const override;

    Eigen::Matrix4d D_elastic() const override;
};
```

2. Implemente `evaluate()`.

- Receba a tensão atual, estado anterior, temperatura e passo de tempo.
- Calcule a taxa viscosa `eps_dot_v = f(sigma, state, T)`.
- Integre o estado local: `state_new = state_old + dt * rate`.
- Aplique clamping físico: `D` em `[0, 0.99]`, deformações acumuladas não negativas.
- Retorne `strain_rate`, `state_new` e tangente.

3. Tangente.

Use tangente analítica quando a equação for simples. Se for complexa, use diferença finita central
em teste e tangente simplificada no modelo somente quando isso estiver documentado:

```cpp
D_tangent = (evaluate(sigma + eps) - evaluate(sigma - eps)) / (2.0 * eps);
```

4. Registre no dispatch/factory correspondente.

```cpp
if (model_name == "meu_modelo") {
    return std::make_unique<MeuModelo>(params);
}
```

5. Adicione YAML.

```yaml
creep:
  secondary: true
  tertiary_model: meu_modelo
  meu_modelo:
    param1: 1.0
    param2: 2.0
```

6. Testes mínimos.

- Tensão zero: taxa viscosa zero, sem NaN.
- Monotonia de dano, se houver `D`.
- Saturação/limite de variáveis internas.
- Regressão contra caso existente ou oráculo.

7. Documentação.

- Equações e parâmetros em `docs/constitutive-models.md`.
- Card ou linha de referência em `docs/index.html`.
- Caso YAML de exemplo em `cases/` quando aplicável.

## 3. Como adicionar um novo elemento

### Contrato

Herde de `Element` e implemente:

```cpp
class MeuElemento : public Element {
public:
    int n_nodes() const override;
    int n_dofs_per_node() const override;
    std::vector<GaussPoint> gauss_points() const override;
    void shape_functions(const GaussPoint& gp,
                         const std::vector<Node>& coords,
                         std::vector<double>& N) const override;
    Eigen::MatrixXd B_matrix(const GaussPoint& gp,
                             const std::vector<Node>& coords) const override;
    double jacobian_weight(const GaussPoint& gp,
                           const std::vector<Node>& coords) const override;
};
```

### Funções de forma e B

Implemente `N_i(xi, eta)` e derivadas paramétricas. Use mapeamento isoparamétrico para obter
derivadas físicas. Em 2D axissimétrico, a matriz B deve respeitar:

```text
B = [ dN/dr     0   ]
    [ N/r       0   ]  <- eps_theta_theta = u_r/r
    [ 0       dN/dz ]
    [ dN/dz   dN/dr ]
```

O peso de integração segue a convenção axissimétrica:

```text
weight = 2*pi*r_gp*|detJ|*w_gp
```

Lance erro se `r_gp <= 0` ou `|detJ|` estiver abaixo da tolerância geométrica.

### Registro e builder

Registre o nome no `ElementFactory` e no builder estruturado se o elemento puder ser malhado
automaticamente:

```cpp
if (type == "axisym_2d_meu_elemento") {
    return std::make_unique<MeuElemento>();
}
```

### Testes mínimos

- Patch test linear.
- Patch test quadrático para elementos quadráticos.
- Lamé analítico e taxa de convergência.
- Regressão TCC compatível com L3/Q8 ao refinar.

## 4. Como adicionar um novo campo térmico

Herde de `ThermalField`:

```cpp
class MeuCampoTermico : public ThermalField {
public:
    double temperature_at(double r, double z, double t) const override;
    double alpha_thermal() const override;
    double T_reference() const override;
};
```

Orientações:

- Campos estacionários podem ignorar `t`.
- Campos transientes devem interpolar a solução térmica no ponto `(r,z)`.
- O campo térmico só entra por Arrhenius e deformação térmica fraca; não altere `K`.
- Registre `thermal.mode` no parser/factory.

YAML:

```yaml
thermal:
  enabled: true
  mode: meu_campo
  meu_campo:
    param1: valor
```

## 5. Estrutura de testes

### C++ Catch2

```cpp
TEST_CASE("MeuModelo: tensao zero nao gera creep", "[constitutive]") {
    MeuModelo modelo(params);
    Stress sigma = Stress::Zero();
    InternalState state;

    auto result = modelo.evaluate(sigma, state, 359.15, 1.0);
    REQUIRE(result.strain_rate.norm() == Catch::Approx(0.0).margin(1.0e-16));
}
```

### Python unittest

```python
class TestMeuModelo(unittest.TestCase):
    def test_closure_matches_regression(self):
        output = run_saltcreep("cases/test_meu_modelo.yaml")
        self.assertAlmostEqual(output["closure"], 0.524, places=3)
```

### Patch test

O patch test deve montar forças consistentes e verificar que o elemento reproduz exatamente o campo
imposto dentro da ordem polinomial esperada.

### Extensões do saltpost

Funcionalidades novas de pós-processamento devem entrar como módulos pequenos em
`post/saltpost/` e ser acionadas pelo CLI em `post/saltpost/cli.py`. O padrão atual é:

- `studies.py` para descoberta declarativa (`--study`, `--vary`).
- `export.py` para formatos de publicação (`--format paper`).
- `report.py` para dashboards HTML estáticos (`--report`).
- `animations.py` para GIF/MP4 (`--animate`).

Sempre adicione testes em `tests/python/` com dados sintéticos pequenos. Evite exigir PyVista,
ffmpeg ou resultados reais para os testes básicos; quando uma dependência externa for opcional,
o teste deve pular graciosamente.

## 6. Como rodar testes e validar

```bash
# Build
cmake -S . -B build -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build -j

# Testes C++
ctest --test-dir build --output-on-failure

# Testes Python
python -m unittest discover tests/python -v

# Smoke test
./build/saltcreep cases/tcc/modelo_A.yaml

# Benchmark
python post/benchmark_suite.py --preset smoke

# Validação SESTSAL quando disponível
ctest -R sestsal_verification --test-dir build
```

## 7. Checklist de extensão

- [ ] Herdei da classe base correta: `ConstitutiveModel`, `Element` ou `ThermalField`.
- [ ] Implementei todos os métodos virtuais obrigatórios.
- [ ] Registrei no factory/dispatch correspondente.
- [ ] Adicionei testes unitários, regressão e smoke test.
- [ ] Documentei equações em `docs/constitutive-models.md` ou `docs/elements.md`.
- [ ] Atualizei `docs/index.html`.
- [ ] Atualizei `AGENTS.md` quando criei documento novo ou mudei contagem de testes.
- [ ] Rodei `ctest --test-dir build --output-on-failure`.
- [ ] Rodei `python -m unittest discover tests/python -v`, se houver Python afetado.
- [ ] Criei caso YAML de exemplo quando o recurso é acionado por input.
- [ ] Validei contra SESTSAL, Lamé ou caso de regressão existente.

## 8. Boas práticas

- Evite alocações em loops de elementos/pontos de Gauss.
- Use `const` onde possível; isso facilita raciocínio e paralelismo.
- Documente hipóteses: pequenas deformações, isotropia, incompressibilidade viscosa.
- Teste extremos: tensão quase zero, `D` próximo de 0.99, temperatura extrema, `dt` extremo.
- Prefira mensagens de erro explícitas a fallback silencioso.
- Use sanitizers quando disponíveis: AddressSanitizer e UndefinedBehaviorSanitizer.
- Preserve unidades SI internamente; conversões pertencem ao parser.
- Faça revisão por pares em código de física e validação.
