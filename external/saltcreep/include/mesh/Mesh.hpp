#pragma once
#include <vector>
#include "types.hpp"

struct Mesh {
    std::vector<Node> nodes;
    std::vector<int> elem_nodes;
    int n_elements = 0;
    int n_nodes = 0;
    int nodes_per_element = 0;
    int dofs_per_node = 1;

    int total_dofs() const { return n_nodes * dofs_per_node; }

    int dof_index(int node_id, int local_dof) const {
        return node_id * dofs_per_node + local_dof;
    }
};

struct Mesh1D : Mesh {
    std::vector<double> node_r;
};

struct Mesh2D : Mesh {};
