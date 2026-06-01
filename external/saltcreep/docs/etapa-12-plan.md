# Etapa 12 — Refinamento adaptativo h (Zienkiewicz-Zhu)

Status: plano arquitetural, sem implementação.

Objetivo: adicionar um ciclo adaptativo `solve -> estimate -> mark -> refine -> transfer`
sem alterar as leis constitutivas, a decomposição aditiva ou o contrato físico já validado.
O primeiro alvo de produção deve ser malha 2D axissimétrica em `Q4` e `T3`, mantendo o
estimador genérico para todos os elementos. Para elementos que ainda não tenham subdivisor
topológico (`Q8`, `Q9`, `AQ9`, `T6`), o adaptativo pode estimar erro e, se nenhum elemento
for marcado, encerrar sem alterar a malha; se houver marcação em tipo ainda sem refino,
falha cedo com mensagem clara.

## Escopo e invariantes

- Não mudar a física de fluência, dano, térmica ou a montagem de tensões.
- Não relaxar tolerâncias existentes.
- Não alterar `Element` nesta etapa, salvo se for inevitável; o estimador deve usar o
  contrato atual de `gauss_points()`, `B_matrix()` e `jacobian_weight()`.
- Refinamento adaptativo é uma camada acima de `Mesh`/`Element`/solver: o solver continua
  recebendo uma malha comum e um elemento comum.
- A primeira implementação deve preservar malhas conformes, sem hanging nodes.
- O schema mínimo aprovado é:

```yaml
mesh:
  adaptive: true
  error_threshold: 0.10
  max_refinement_levels: 3
```

Proposta opcional para o teste com dano:

```yaml
mesh:
  damage_refinement_threshold: 0.30  # opcional; default: desabilitado
```

Se este campo não for aprovado, o teste de dano pode chamar o marcador diretamente em nível
unitário com limiar `D > 0.3`, sem ampliar o YAML.

## Classe `ErrorEstimator`

Arquivos planejados:

- `include/mesh/error_estimator.hpp`
- `src/mesh/error_estimator.cpp`

Interface proposta:

```cpp
struct ElementError {
    int element_id;
    double eta_abs;
    double eta_rel;
    double stress_energy;
    double damage_indicator;
};

struct ErrorEstimatorOptions {
    double error_threshold = 0.10;
    double damage_refinement_threshold = -1.0; // <0 desliga
};

class ErrorEstimator {
public:
    std::vector<ElementError> compute_errors(
        const Mesh& mesh,
        const Element& element,
        const ConstitutiveModel& model,
        const TimeState& state) const;

    std::vector<char> mark_for_refinement(
        std::span<const ElementError> errors,
        const ErrorEstimatorOptions& options) const;
};
```

### Recuperação de tensões `sigma*`

Entrada disponível após uma simulação:

- tensões descontínuas por ponto de Gauss: `state.stress_gp`;
- coordenadas físicas por elemento e por ponto de Gauss;
- estados internos por ponto de Gauss para indicadores auxiliares (`D`, `eps_v_primary`,
  `eps_v_secondary`).

Procedimento Zienkiewicz-Zhu inicial:

1. Para cada ponto de Gauss, calcular `sigma_h`.
2. Projetar `sigma_h` para nós por média ponderada:
   `sigma_node[n] += w_gp * N_i * sigma_h`, `weight_node[n] += w_gp * N_i`.
3. Normalizar `sigma_node[n]`.
4. Em cada ponto de Gauss, interpolar a tensão recuperada:
   `sigma*_gp = sum_i N_i(gp) * sigma_node[node_i]`.
5. Calcular o erro energético local:

```text
eta_e^2 = integral_e (sigma_h - sigma*)^T D_elastic^{-1} (sigma_h - sigma*) dOmega
```

6. Calcular a energia de referência:

```text
energy_e = integral_e sigma_h^T D_elastic^{-1} sigma_h dOmega
eta_rel_e = sqrt(eta_e^2 / max(energy_e, eps))
```

Observações:

- Este é o ZZ por suavização nodal ponderada. Superconvergent patch recovery pode ser
  uma melhoria posterior, mas não é necessária para a primeira etapa.
- A norma usa `D_elastic^{-1}`, portanto mede erro em energia elástica e independe do
  modelo viscoso instantâneo.
- Para `AQ9` no problema de Lamé enriquecido, espera-se `eta_rel` próximo de zero; isso
  permite validar que o adaptativo não refina quando o espaço de aproximação já contém a
  solução.

### Marcação

Critério principal:

```text
marked[e] = eta_rel_e > error_threshold
```

Critério complementar para dano, se aprovado:

```text
marked[e] |= max_gp(D_e) > damage_refinement_threshold
```

Motivação do critério de dano: em problemas terciários a maior necessidade de resolução
pode aparecer antes de o erro elástico suavizado crescer muito; `D > 0.3` é um marcador
operacional de localização de dano já usado na interpretação física do projeto.

Para evitar explosão de GDLs:

- não refinar além de `max_refinement_levels`;
- ignorar elementos que já atingiram o nível máximo;
- registrar em metadados: `adaptive_iterations`, `n_marked`, `eta_global`,
  `final_n_dofs`.

## Classe `MeshRefiner`

Arquivos planejados:

- `include/mesh/mesh_refiner.hpp`
- `src/mesh/mesh_refiner.cpp`

Interface proposta:

```cpp
struct FieldTransferResult {
    Eigen::VectorXd u;
    TimeState state;
};

struct RefinedMesh {
    Mesh2D mesh;
    std::vector<int> parent_element;
    std::vector<int> refinement_level;
};

class MeshRefiner {
public:
    RefinedMesh refine_elements(
        const Mesh& old_mesh,
        const Element& element,
        std::span<const char> marked,
        std::span<const int> old_levels) const;

    FieldTransferResult interpolate_fields(
        const Mesh& old_mesh,
        const Mesh& new_mesh,
        const Element& old_element,
        const Element& new_element,
        const Eigen::VectorXd& old_u,
        const TimeState& old_state,
        std::span<const int> parent_element) const;
};
```

### Subdivisão Q4 -> 4 Q4

Para cada quadrilátero marcado:

```text
3 ----- 2          3 --- m32 --- 2
|       |          |      |      |
|       |    ->   m03 --- c --- m12
|       |          |      |      |
0 ----- 1          0 --- m01 --- 1
```

Filhos:

```text
[0, m01, c, m03]
[m01, 1, m12, c]
[c, m12, 2, m32]
[m03, c, m32, 3]
```

Conformidade:

- nós de aresta são cacheados por par ordenado `(min_node,max_node)`;
- se um Q4 compartilha aresta com elemento refinado, o vizinho deve ser refinado também
  por fechamento de conformidade;
- o fechamento pode propagar marcações até não haver aresta refinada encostando em aresta
  grossa.

### Subdivisão T3 -> 3 T3

Conforme pedido, a primeira opção para `T3` é split por centroide, sem nós nas arestas:

```text
      2                  2
     / \                /|\
    /   \      ->      / | \
   /     \            /  c  \
  0 ----- 1          0 ----- 1
```

Filhos:

```text
[0, 1, c]
[1, 2, c]
[2, 0, c]
```

Vantagens:

- não cria hanging nodes em arestas compartilhadas;
- preserva uma malha conforme mesmo com refinamento local isolado;
- é suficiente para concentrar GDLs em regiões de erro alto.

Risco:

- pode gerar triângulos mais alongados do que o red-refinement por três pontos médios.
  Se a qualidade cair, uma segunda versão pode implementar `T3 -> 4 T3` com fechamento
  de aresta.

### Transferência de campos

Campos a transferir:

- deslocamentos nodais `u`;
- `eps_v_eff`;
- `eps_v_primary`;
- `eps_v_secondary`;
- `damage_D`;
- `f_hard`;
- `eps_th_gp`, quando o acoplamento térmico estiver ativo.

Plano:

1. Cada filho guarda `parent_element`.
2. Cada novo nó conhece sua coordenada física `(r,z)`.
3. Para `u`, localizar o ponto local `(xi,eta)` do novo nó dentro do elemento pai e interpolar:

```text
u_new(node) = sum_i N_i_parent(xi,eta) * u_old(parent_node_i)
```

4. Para estados em ponto de Gauss, recuperar cada escalar antigo para nós do elemento pai
   por média ponderada dos GPs do pai.
5. Interpolar esses escalares recuperados no novo ponto de Gauss.
6. Aplicar clamps físicos:

```text
D in [0, 0.99]
eps_v_* >= 0 quando representarem acumulados escalares
f_hard >= 0
```

7. Recalcular tensões no passo seguinte pelo solver, usando `B*u - eps_v - eps_th` como hoje.

Motivo para não copiar o GP mais próximo: cópia por vizinho é simples, mas cria
descontinuidades artificiais justamente no campo que guia a adaptação. A recuperação nodal
escalares -> interpolação é mais suave e combina com o ZZ.

## Loop adaptativo

Local de integração: `main.cpp` deve coordenar, mas a lógica deve ficar em uma função/classe
pequena para não inflar o entry point. Nome sugerido para etapa posterior:
`AdaptiveRunner`.

Pseudocódigo:

```text
mesh = build_initial_mesh(case)
levels = zeros(mesh.n_elements)
state/u = empty initial state

for adapt_iter in 0..max_refinement_levels:
    build K, f, sigma_geo for mesh
    solver.run(mesh, initial_state=state, initial_u=u)

    errors = ErrorEstimator.compute_errors(mesh, element, model, solver.state())
    marked = ErrorEstimator.mark_for_refinement(errors, options)
    marked = remove_elements_at_max_level(marked, levels)

    if none(marked):
        break

    refined = MeshRefiner.refine_elements(mesh, element, marked, levels)
    transfer = MeshRefiner.interpolate_fields(
        mesh, refined.mesh, element, element, solver.u(), solver.state(), refined.parent_element)

    mesh = refined.mesh
    levels = refined.refinement_level
    u = transfer.u
    state = transfer.state
```

Primeira implementação conservadora:

- rodar cada iteração adaptativa como uma simulação completa até `total_h`;
- transferir o estado final para a próxima malha apenas como chute inicial/continuidade se
  o integrador já suportar estado inicial;
- se os integradores não aceitarem estado inicial de forma limpa, reiniciar do zero em cada
  malha e usar a adaptação como processo de geração de malha. Isso é mais simples e seguro
  para a primeira versão, mas menos eficiente.

Preferência para produção:

- adicionar overloads nos integradores para aceitar `u0` e `TimeState state0`;
- manter o tempo físico contínuo apenas se a transferência estiver testada;
- caso contrário, adaptar em pré-processo elástico/curto e então rodar a simulação final.

## Exemplo de desenho: cilindro 4 x 2

Malha inicial estruturada `Q4`, com 4 elementos radiais e 2 axiais:

```text
z
^
|  [4] [5] [6] [7]     linha superior
|  [0] [1] [2] [3]     linha inferior
+------------------> r
   Ri              Re
```

Interpretação esperada para poço:

- erro maior perto da parede interna `Ri`, por gradiente radial de deslocamento/tensão;
- erro baixo no domínio externo;
- em problemas com camada térmica/litológica, erro adicional perto da interface em `z`.

### Iteração 1

Se o maior erro estiver na parede interna:

```text
z
^
|  [4*] [5]  [6]  [7]
|  [0*] [1]  [2]  [3]
+--------------------> r
```

Elementos marcados:

- `0` e `4`, coluna radial junto ao poço.

Após `Q4 -> 4 Q4`:

```text
z
^
|  [4a][4b] [5] [6] [7]
|  [4c][4d]
|  [0a][0b] [1] [2] [3]
|  [0c][0d]
+------------------------> r
```

Em implementação conforme, vizinhos que compartilhem uma aresta com midpoint são refinados
se necessário. Em uma malha estruturada por colunas, isso pode refinar a coluna vizinha
dependendo da estratégia de fechamento adotada.

### Iteração 2

Depois da primeira redistribuição de GDLs, espera-se:

- queda do erro na primeira coluna;
- eventual marcação apenas nos subelementos mais próximos da parede interna;
- se houver interface litológica horizontal, marcação também nos elementos atravessados por
  `z_interface`.

Exemplo com concentração persistente no canto parede/topo:

```text
z
^
|  [4a*][4b] [5] [6] [7]
|  [4c ][4d]
|  [0a ][0b] [1] [2] [3]
|  [0c*][0d]
+------------------------> r
```

Resultado esperado após a iteração 2:

- refinamento mais fino em regiões localizadas;
- `eta_global` reduzindo monotonicamente ou quase monotonicamente;
- número de GDLs crescendo sublinearmente quando comparado a refino uniforme equivalente.

Critério de convergência:

```text
max(eta_rel_e) <= error_threshold
ou nenhum elemento novo pode ser refinado por max_refinement_levels
```

## Testes planejados

1. `ErrorEstimator`: em solução de Lamé com `AQ9`, erro ZZ próximo de zero; adaptativo não
   marca elementos e a resposta uniforme/adaptativa coincide.
2. `MeshRefiner Q4`: um Q4 unitário marcado vira quatro Q4 com área total preservada e
   conectividade válida.
3. `MeshRefiner T3`: um T3 marcado vira três T3 com área total preservada.
4. `Transfer u`: campo linear `u_r = a + b r + c z`, `u_z = d + e r + f z` é reproduzido
   nos novos nós.
5. Intercalação halita/carnalita: com contraste de material/térmico no `z`, elementos próximos
   à interface são marcados.
6. Dano: com `damage_D > 0.3` em uma região, esses elementos são marcados pelo indicador
   complementar.
7. Regressão completa: todos os testes existentes continuam verdes.

## Documentação posterior à aprovação

Na implementação aprovada, atualizar:

- `docs/mesh-adaptation.md`: algoritmo ZZ, refinadores suportados, limitações;
- `docs/input-spec.md`: flags `mesh.adaptive`, `mesh.error_threshold`,
  `mesh.max_refinement_levels`;
- `docs/index.html`: seção de mesh adaptation e construtor interativo;
- `docs/dev-log.md`: entrada Etapa 12;
- `AGENTS.md`: estado atual e contagem de testes.

## Riscos e decisões a aprovar

1. Suporte topológico inicial: confirmar que `Q4 -> 4` e `T3 -> 3` são suficientes para a
   primeira entrega; demais elementos apenas estimam erro até ganharem refiner próprio.
2. Conformidade Q4: aprovar refinamento por fechamento de vizinhos para evitar hanging nodes.
3. Dano como indicador: aprovar ou não o campo opcional `mesh.damage_refinement_threshold`.
4. Loop temporal: decidir se a primeira versão pode adaptar como processo de geração de malha
   reiniciando a simulação em cada malha, ou se já deve transferir estado final e continuar
   o tempo físico na malha refinada.
