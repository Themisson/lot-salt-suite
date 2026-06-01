# Arquitetura de infraestrutura FEM

Este documento registra a refatoração da Etapa 3a: preparar o solver para elementos
1D e 2D axissimétricos sem alterar a física já validada de Lamé, DM ou EDMT.

## ElementFactory

O executável não instancia elementos concretos diretamente. O YAML define:

```yaml
element:
  type: axisym_1d_L3
```

`make_element(element.type)` cria a subclasse correta de `Element`. Nesta etapa o
factory registra apenas:

- `axisym_1d_L3` -> `AxisymL3`

Na Etapa 3b, cada novo elemento 2D deve ser adicionado ao mesmo factory:

- `axisym_2d_Q4`
- `axisym_2d_T3`
- `axisym_2d_Q8`
- `axisym_2d_Q9`
- `axisym_2d_AQ9`
- `axisym_2d_T6`

Tipo desconhecido deve falhar cedo com erro claro, antes da montagem.

## Mesh

A malha genérica armazena nós em coordenadas axissimétricas físicas:

```cpp
struct Node {
    double r;
    double z;
};
```

`Mesh` contém:

- `nodes`: coordenadas `(r,z)`;
- `elem_nodes`: conectividade achatada;
- `n_elements`, `n_nodes`, `nodes_per_element`;
- `dofs_per_node`;
- `dof_index(node_id, local_dof)`.

`Mesh1D` herda de `Mesh` e mantém `node_r` por compatibilidade com testes e rotinas
1D existentes. Para `axisym_1d_L3`, os nós são `Node{r, 0}` e `dofs_per_node = 1`.

`Mesh2D` já existe como tipo de armazenamento para a Etapa 3b. Elementos 2D usarão
`dofs_per_node = 2`, com graus de liberdade locais:

```text
local_dof 0 -> u_r
local_dof 1 -> u_z
```

O índice global é sempre:

```text
global_dof = node_id * dofs_per_node + local_dof
```

## Contrato de Element

`Element` trabalha com pontos de Gauss em coordenadas locais:

```cpp
struct GaussPoint {
    double xi;
    double weight;
    double eta;
};
```

Elementos 1D usam `xi` e ignoram `eta`. Elementos 2D usam ambos.

Elementos clássicos calculam `N` e derivadas apenas a partir do ponto local. Elementos
geometry-aware, como o `axisym_2d_AQ9`, também podem depender das coordenadas físicas do elemento
por meio dos overloads:

```cpp
void shape_functions(
    const GaussPoint& gp,
    std::span<const Node> node_coords,
    std::span<double> N) const;

void shape_derivatives(
    const GaussPoint& gp,
    std::span<const Node> node_coords,
    std::span<double> dN_dxi,
    std::span<double> dN_deta) const;
```

O default desses overloads chama as versões antigas, então L3/Q4/T3/Q8/Q9/T6 preservam exatamente
o contrato anterior.

A matriz `B` recebe o ponto local completo e as coordenadas físicas dos nós:

```cpp
Eigen::MatrixXd B_matrix(
    const GaussPoint& gp,
    std::span<const Node> node_coords) const;
```

A ordem Voigt é invariável:

```text
[epsilon_rr, epsilon_tt, epsilon_zz, gamma_rz]
```

Para elementos 2D axissimétricos, a matriz `B` deve implementar:

```text
epsilon_rr = du_r/dr
epsilon_tt = u_r/r
epsilon_zz = du_z/dz
gamma_rz   = du_r/dz + du_z/dr
```

O termo `epsilon_tt = u_r/r` usa o raio interpolado no ponto de Gauss:

```text
r_gp = sum_i N_i(r,z) * r_i
```

O peso de integração retornado por `jacobian_weight()` inclui o fator axissimétrico:

```text
1D: 2*pi*r_gp*|J|*w
2D: 2*pi*r_gp*|detJ|*w
```

## Montagem

`Assembler` usa apenas `Mesh`, `Element` e `ConstitutiveModel`. A montagem segue:

```text
K_e += B^T * D * B * jacobian_weight
```

O espalhamento para o vetor/matriz global usa `mesh.dof_index()`. Portanto o caminho
1D permanece idêntico (`dofs_per_node = 1`) e o caminho 2D já tem endereçamento para
`u_r, u_z` por nó.

As pseudo-forças viscosas e geostáticas continuam usando a mesma física:

```text
f_v   = integral B^T * D * delta_epsilon_v dOmega
f_geo = integral B^T * sigma_geo dOmega
```

Nenhuma lei constitutiva foi alterada nesta refatoração.

## Como adicionar um elemento 2D na Etapa 3b

Para cada novo elemento:

1. Criar `include/elements/<nome>.hpp` e `src/elements/<nome>.cpp`.
2. Herdar de `Element`.
3. Definir pontos de Gauss, funções de forma, derivadas locais e `B_matrix()`.
4. Garantir `n_dofs_per_node() == 2` e `n_strain_comp() == 4`.
5. Retornar `jacobian_weight()` com `2*pi*r_gp*|detJ|*w`.
6. Registrar no `ElementFactory`.
7. Adicionar `element.type` ao parser/schema se ainda não listado.
8. Adicionar patch test, Lamé convergência e convergência vs. L3 no caso TCC.

Se for necessário alterar DM, EDMT, Arrhenius, decomposição aditiva ou a regra de K
constante, a implementação saiu do escopo da Etapa 3 e deve parar para revisão.
