#include "mesh/mesh_refiner.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <map>
#include <stdexcept>

namespace {
constexpr double kTol = 1.0e-10;

bool same_node(const Node& a, const Node& b) {
    return std::abs(a.r - b.r) <= kTol * std::max({1.0, std::abs(a.r), std::abs(b.r)}) &&
           std::abs(a.z - b.z) <= kTol * std::max({1.0, std::abs(a.z), std::abs(b.z)});
}

int add_node(Mesh2D& mesh, const Node& node) {
    mesh.nodes.push_back(node);
    mesh.n_nodes = static_cast<int>(mesh.nodes.size());
    return mesh.n_nodes - 1;
}

int midpoint_node(Mesh2D& mesh,
                  std::map<std::pair<int, int>, int>& cache,
                  int a,
                  int b) {
    const auto key = std::minmax(a, b);
    const auto it = cache.find(key);
    if (it != cache.end())
        return it->second;
    const Node& na = mesh.nodes[a];
    const Node& nb = mesh.nodes[b];
    const int id = add_node(mesh, Node{0.5 * (na.r + nb.r), 0.5 * (na.z + nb.z)});
    cache.emplace(key, id);
    return id;
}

int center_node(Mesh2D& mesh, std::span<const int> conn) {
    Node c;
    for (int node : conn) {
        c.r += mesh.nodes[node].r;
        c.z += mesh.nodes[node].z;
    }
    c.r /= static_cast<double>(conn.size());
    c.z /= static_cast<double>(conn.size());
    return add_node(mesh, c);
}

bool share_q4_edge(const Mesh& mesh, int a, int b) {
    constexpr std::array<std::array<int, 2>, 4> edges = {{
        {{0, 1}}, {{1, 2}}, {{2, 3}}, {{3, 0}}
    }};
    for (const auto& ea : edges) {
        const int a0 = mesh.elem_nodes[4 * a + ea[0]];
        const int a1 = mesh.elem_nodes[4 * a + ea[1]];
        for (const auto& eb : edges) {
            const int b0 = mesh.elem_nodes[4 * b + eb[0]];
            const int b1 = mesh.elem_nodes[4 * b + eb[1]];
            if ((a0 == b0 && a1 == b1) || (a0 == b1 && a1 == b0))
                return true;
        }
    }
    return false;
}

std::vector<char> close_q4_conformity(const Mesh& mesh, std::span<const char> marked) {
    std::vector<char> out(marked.begin(), marked.end());
    bool changed = true;
    while (changed) {
        changed = false;
        for (int e = 0; e < mesh.n_elements; ++e) {
            if (!out[e])
                continue;
            for (int f = 0; f < mesh.n_elements; ++f) {
                if (!out[f] && share_q4_edge(mesh, e, f)) {
                    out[f] = 1;
                    changed = true;
                }
            }
        }
    }
    return out;
}

double triangle_area(const Node& a, const Node& b, const Node& c) {
    return 0.5 * ((b.r - a.r) * (c.z - a.z) - (c.r - a.r) * (b.z - a.z));
}

bool local_q4(const Mesh& mesh, int e, const Node& x, double& xi, double& eta) {
    double rmin = mesh.nodes[mesh.elem_nodes[4 * e]].r;
    double rmax = rmin;
    double zmin = mesh.nodes[mesh.elem_nodes[4 * e]].z;
    double zmax = zmin;
    for (int i = 1; i < 4; ++i) {
        const Node& n = mesh.nodes[mesh.elem_nodes[4 * e + i]];
        rmin = std::min(rmin, n.r);
        rmax = std::max(rmax, n.r);
        zmin = std::min(zmin, n.z);
        zmax = std::max(zmax, n.z);
    }
    if (x.r < rmin - kTol || x.r > rmax + kTol ||
        x.z < zmin - kTol || x.z > zmax + kTol)
        return false;
    xi = 2.0 * (x.r - rmin) / (rmax - rmin) - 1.0;
    eta = 2.0 * (x.z - zmin) / (zmax - zmin) - 1.0;
    return xi >= -1.0 - 1.0e-8 && xi <= 1.0 + 1.0e-8 &&
           eta >= -1.0 - 1.0e-8 && eta <= 1.0 + 1.0e-8;
}

bool local_t3(const Mesh& mesh, int e, const Node& x, double& xi, double& eta) {
    const Node& a = mesh.nodes[mesh.elem_nodes[3 * e + 0]];
    const Node& b = mesh.nodes[mesh.elem_nodes[3 * e + 1]];
    const Node& c = mesh.nodes[mesh.elem_nodes[3 * e + 2]];
    const double A = triangle_area(a, b, c);
    if (std::abs(A) <= 1.0e-30)
        return false;
    const double l1 = triangle_area(x, b, c) / A;
    const double l2 = triangle_area(a, x, c) / A;
    const double l3 = triangle_area(a, b, x) / A;
    xi = l2;
    eta = l3;
    return l1 >= -1.0e-8 && l2 >= -1.0e-8 && l3 >= -1.0e-8 &&
           l1 <= 1.0 + 1.0e-8 && l2 <= 1.0 + 1.0e-8 && l3 <= 1.0 + 1.0e-8;
}

bool local_coords(const Mesh& mesh,
                  const Element& element,
                  int e,
                  const Node& x,
                  double& xi,
                  double& eta) {
    if (element.n_nodes() == 4)
        return local_q4(mesh, e, x, xi, eta);
    if (element.n_nodes() == 3)
        return local_t3(mesh, e, x, xi, eta);
    return false;
}

int find_containing_element(const Mesh& mesh,
                            const Element& element,
                            const Node& x,
                            double& xi,
                            double& eta) {
    for (int e = 0; e < mesh.n_elements; ++e) {
        if (local_coords(mesh, element, e, x, xi, eta))
            return e;
    }
    return -1;
}

std::vector<Node> element_coords(const Mesh& mesh, int e, int nne) {
    std::vector<Node> coords(nne);
    for (int i = 0; i < nne; ++i)
        coords[i] = mesh.nodes[mesh.elem_nodes[nne * e + i]];
    return coords;
}

std::vector<Strain> recover_strain_nodes(const Mesh& mesh,
                                         const Element& element,
                                         const std::vector<Strain>& gp_values) {
    const int nne = element.n_nodes();
    const int n_gp = static_cast<int>(element.gauss_points().size());
    std::vector<Strain> out(mesh.n_nodes, Strain::Zero());
    std::vector<double> wsum(mesh.n_nodes, 0.0);
    if (static_cast<int>(gp_values.size()) != mesh.n_elements * n_gp)
        return out;

    for (int e = 0; e < mesh.n_elements; ++e) {
        const auto coords = element_coords(mesh, e, nne);
        for (int g = 0; g < n_gp; ++g) {
            std::vector<double> N(nne);
            element.shape_functions(element.gauss_points()[g], coords, N);
            const double jw = std::abs(element.jacobian_weight(element.gauss_points()[g], coords));
            for (int i = 0; i < nne; ++i) {
                const int node = mesh.elem_nodes[nne * e + i];
                const double w = std::abs(N[i]) * jw;
                out[node] += w * gp_values[e * n_gp + g];
                wsum[node] += w;
            }
        }
    }
    for (int n = 0; n < mesh.n_nodes; ++n)
        if (wsum[n] > 0.0)
            out[n] /= wsum[n];
    return out;
}

std::vector<InternalState> recover_internal_nodes(
    const Mesh& mesh,
    const Element& element,
    const std::vector<InternalState>& gp_values) {
    const int nne = element.n_nodes();
    const int n_gp = static_cast<int>(element.gauss_points().size());
    std::vector<InternalState> out(mesh.n_nodes, InternalState{});
    std::vector<double> wsum(mesh.n_nodes, 0.0);
    if (static_cast<int>(gp_values.size()) != mesh.n_elements * n_gp)
        return out;

    for (int e = 0; e < mesh.n_elements; ++e) {
        const auto coords = element_coords(mesh, e, nne);
        for (int g = 0; g < n_gp; ++g) {
            std::vector<double> N(nne);
            element.shape_functions(element.gauss_points()[g], coords, N);
            const double jw = std::abs(element.jacobian_weight(element.gauss_points()[g], coords));
            const InternalState& s = gp_values[e * n_gp + g];
            for (int i = 0; i < nne; ++i) {
                const int node = mesh.elem_nodes[nne * e + i];
                const double w = std::abs(N[i]) * jw;
                out[node].eps_v_eff += w * s.eps_v_eff;
                out[node].damage_D += w * s.damage_D;
                out[node].eps_v_primary += w * s.eps_v_primary;
                out[node].eps_v_secondary += w * s.eps_v_secondary;
                out[node].f_hard += w * s.f_hard;
                wsum[node] += w;
            }
        }
    }
    for (int n = 0; n < mesh.n_nodes; ++n) {
        if (wsum[n] <= 0.0)
            continue;
        out[n].eps_v_eff /= wsum[n];
        out[n].damage_D = std::clamp(out[n].damage_D / wsum[n], 0.0, 0.99);
        out[n].eps_v_primary = std::max(0.0, out[n].eps_v_primary / wsum[n]);
        out[n].eps_v_secondary = std::max(0.0, out[n].eps_v_secondary / wsum[n]);
        out[n].f_hard = std::max(0.0, out[n].f_hard / wsum[n]);
    }
    return out;
}
} // namespace

RefinedMesh MeshRefiner::refine_elements(const Mesh& old_mesh,
                                         const Element& element,
                                         std::span<const char> marked_elements,
                                         std::span<const int> old_levels) const {
    if (static_cast<int>(marked_elements.size()) != old_mesh.n_elements)
        throw std::invalid_argument("MeshRefiner: marked_elements size mismatch");
    const int nne = element.n_nodes();
    if (nne != 3 && nne != 4)
        throw std::invalid_argument("MeshRefiner: only Q4 and T3 are supported");

    std::vector<char> marked(marked_elements.begin(), marked_elements.end());
    if (nne == 4)
        marked = close_q4_conformity(old_mesh, marked);

    RefinedMesh refined;
    refined.mesh.nodes = old_mesh.nodes;
    refined.mesh.n_nodes = old_mesh.n_nodes;
    refined.mesh.nodes_per_element = nne;
    refined.mesh.dofs_per_node = old_mesh.dofs_per_node;

    std::map<std::pair<int, int>, int> edge_midpoints;
    for (int e = 0; e < old_mesh.n_elements; ++e) {
        const int old_level = old_levels.empty() ? 0 : old_levels[e];
        auto push_element = [&](std::initializer_list<int> conn, int level) {
            refined.mesh.elem_nodes.insert(refined.mesh.elem_nodes.end(), conn.begin(), conn.end());
            refined.parent_element.push_back(e);
            refined.refinement_level.push_back(level);
        };

        if (!marked[e]) {
            for (int i = 0; i < nne; ++i)
                refined.mesh.elem_nodes.push_back(old_mesh.elem_nodes[nne * e + i]);
            refined.parent_element.push_back(e);
            refined.refinement_level.push_back(old_level);
            continue;
        }

        if (nne == 4) {
            const int n0 = old_mesh.elem_nodes[4 * e + 0];
            const int n1 = old_mesh.elem_nodes[4 * e + 1];
            const int n2 = old_mesh.elem_nodes[4 * e + 2];
            const int n3 = old_mesh.elem_nodes[4 * e + 3];
            const int m01 = midpoint_node(refined.mesh, edge_midpoints, n0, n1);
            const int m12 = midpoint_node(refined.mesh, edge_midpoints, n1, n2);
            const int m23 = midpoint_node(refined.mesh, edge_midpoints, n2, n3);
            const int m30 = midpoint_node(refined.mesh, edge_midpoints, n3, n0);
            const std::array<int, 4> conn = {{n0, n1, n2, n3}};
            const int c = center_node(refined.mesh, conn);
            push_element({n0, m01, c, m30}, old_level + 1);
            push_element({m01, n1, m12, c}, old_level + 1);
            push_element({c, m12, n2, m23}, old_level + 1);
            push_element({m30, c, m23, n3}, old_level + 1);
        } else {
            const int n0 = old_mesh.elem_nodes[3 * e + 0];
            const int n1 = old_mesh.elem_nodes[3 * e + 1];
            const int n2 = old_mesh.elem_nodes[3 * e + 2];
            const std::array<int, 3> conn = {{n0, n1, n2}};
            const int c = center_node(refined.mesh, conn);
            push_element({n0, n1, c}, old_level + 1);
            push_element({n1, n2, c}, old_level + 1);
            push_element({n2, n0, c}, old_level + 1);
        }
    }

    refined.mesh.n_elements = static_cast<int>(refined.parent_element.size());
    refined.mesh.n_nodes = static_cast<int>(refined.mesh.nodes.size());
    return refined;
}

FieldTransferResult MeshRefiner::interpolate_fields(
    const Mesh& old_mesh,
    const Mesh& new_mesh,
    const Element& old_element,
    const Element& new_element,
    const Eigen::VectorXd& old_u,
    const TimeState& old_state,
    std::span<const int> parent_element) const {
    if (old_u.size() != old_mesh.total_dofs())
        throw std::invalid_argument("MeshRefiner: old_u size mismatch");
    if (static_cast<int>(parent_element.size()) != new_mesh.n_elements)
        throw std::invalid_argument("MeshRefiner: parent_element size mismatch");

    FieldTransferResult result;
    result.u = Eigen::VectorXd::Zero(new_mesh.total_dofs());

    const int old_nne = old_element.n_nodes();
    for (int n = 0; n < new_mesh.n_nodes; ++n) {
        int old_node = -1;
        for (int candidate = 0; candidate < old_mesh.n_nodes; ++candidate) {
            if (same_node(new_mesh.nodes[n], old_mesh.nodes[candidate])) {
                old_node = candidate;
                break;
            }
        }
        if (old_node >= 0) {
            for (int d = 0; d < new_mesh.dofs_per_node; ++d)
                result.u[new_mesh.dof_index(n, d)] = old_u[old_mesh.dof_index(old_node, d)];
            continue;
        }

        double xi = 0.0;
        double eta = 0.0;
        const int e = find_containing_element(old_mesh, old_element, new_mesh.nodes[n], xi, eta);
        if (e < 0)
            throw std::runtime_error("MeshRefiner: could not locate new node in old mesh");
        const auto coords = element_coords(old_mesh, e, old_nne);
        std::vector<double> N(old_nne);
        old_element.shape_functions(GaussPoint{xi, 1.0, eta}, coords, N);
        for (int d = 0; d < new_mesh.dofs_per_node; ++d) {
            double value = 0.0;
            for (int i = 0; i < old_nne; ++i) {
                const int old_id = old_mesh.elem_nodes[old_nne * e + i];
                value += N[i] * old_u[old_mesh.dof_index(old_id, d)];
            }
            result.u[new_mesh.dof_index(n, d)] = value;
        }
    }

    const int new_n_gp = static_cast<int>(new_element.gauss_points().size());
    const int total_new_gp = new_mesh.n_elements * new_n_gp;
    result.state.u_total = result.u;
    result.state.sigma_gp.assign(total_new_gp, Stress::Zero());
    result.state.eps_v_gp.assign(total_new_gp, Strain::Zero());
    result.state.eps_th_gp.assign(total_new_gp, Strain::Zero());
    result.state.state_gp.assign(total_new_gp, InternalState{});

    const auto sigma_nodes = recover_strain_nodes(old_mesh, old_element, old_state.sigma_gp);
    const auto eps_v_nodes = recover_strain_nodes(old_mesh, old_element, old_state.eps_v_gp);
    const auto eps_th_nodes = recover_strain_nodes(old_mesh, old_element, old_state.eps_th_gp);
    const auto internal_nodes = recover_internal_nodes(old_mesh, old_element, old_state.state_gp);

    const int new_nne = new_element.n_nodes();
    for (int e = 0; e < new_mesh.n_elements; ++e) {
        const int parent = parent_element[e];
        for (int g = 0; g < new_n_gp; ++g) {
            const auto new_coords = element_coords(new_mesh, e, new_nne);
            std::vector<double> N_new(new_nne);
            new_element.shape_functions(new_element.gauss_points()[g], new_coords, N_new);
            Node x;
            for (int i = 0; i < new_nne; ++i) {
                x.r += N_new[i] * new_coords[i].r;
                x.z += N_new[i] * new_coords[i].z;
            }

            double xi = 0.0;
            double eta = 0.0;
            if (!local_coords(old_mesh, old_element, parent, x, xi, eta))
                throw std::runtime_error("MeshRefiner: child GP outside parent element");
            const auto old_coords = element_coords(old_mesh, parent, old_nne);
            std::vector<double> N_old(old_nne);
            old_element.shape_functions(GaussPoint{xi, 1.0, eta}, old_coords, N_old);

            const int idx = e * new_n_gp + g;
            InternalState s;
            for (int i = 0; i < old_nne; ++i) {
                const int old_node = old_mesh.elem_nodes[old_nne * parent + i];
                result.state.sigma_gp[idx] += N_old[i] * sigma_nodes[old_node];
                result.state.eps_v_gp[idx] += N_old[i] * eps_v_nodes[old_node];
                result.state.eps_th_gp[idx] += N_old[i] * eps_th_nodes[old_node];
                s.eps_v_eff += N_old[i] * internal_nodes[old_node].eps_v_eff;
                s.damage_D += N_old[i] * internal_nodes[old_node].damage_D;
                s.eps_v_primary += N_old[i] * internal_nodes[old_node].eps_v_primary;
                s.eps_v_secondary += N_old[i] * internal_nodes[old_node].eps_v_secondary;
                s.f_hard += N_old[i] * internal_nodes[old_node].f_hard;
            }
            s.eps_v_eff = std::max(0.0, s.eps_v_eff);
            s.damage_D = std::clamp(s.damage_D, 0.0, 0.99);
            s.eps_v_primary = std::max(0.0, s.eps_v_primary);
            s.eps_v_secondary = std::max(0.0, s.eps_v_secondary);
            s.f_hard = std::max(0.0, s.f_hard);
            result.state.state_gp[idx] = s;
        }
    }

    return result;
}
