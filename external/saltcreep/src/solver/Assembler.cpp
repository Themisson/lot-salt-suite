#include "solver/Assembler.hpp"
#include <algorithm>
#include <cmath>
#include <string>
#include <stdexcept>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace {

struct ElementForce {
    std::vector<int> gdofs;
    Eigen::VectorXd values;
};

std::vector<double> radial_edges(double Ri, double Re, int n_radial, double ratio,
                                 const std::string& context) {
    if (n_radial < 1)
        throw std::invalid_argument(context + ": n_radial must be >= 1");
    if (ratio <= 0.0)
        throw std::invalid_argument(context + ": ratio must be > 0");

    std::vector<double> edges(n_radial + 1);
    edges[0] = Ri;
    if (std::abs(ratio - 1.0) < 1e-12) {
        const double h = (Re - Ri) / n_radial;
        for (int i = 1; i <= n_radial; ++i)
            edges[i] = Ri + i * h;
    } else {
        const double q = std::pow(ratio, 1.0 / (n_radial - 1));
        const double h0 = (Re - Ri) * (q - 1.0) / (std::pow(q, n_radial) - 1.0);
        double r = Ri;
        for (int i = 0; i < n_radial; ++i) {
            edges[i] = r;
            r += h0 * std::pow(q, i);
        }
        edges[n_radial] = Re;
    }
    return edges;
}

Mesh2D build_q4_mesh_impl(double Ri, double Re, double height,
                          int n_radial, int n_axial, double ratio) {
    if (n_axial < 1)
        throw std::invalid_argument("build_q4_mesh: n_axial must be >= 1");
    const auto r_nodes = radial_edges(Ri, Re, n_radial, ratio, "build_q4_mesh");

    Mesh2D mesh;
    mesh.n_nodes = (n_radial + 1) * (n_axial + 1);
    mesh.n_elements = n_radial * n_axial;
    mesh.nodes_per_element = 4;
    mesh.dofs_per_node = 2;
    mesh.nodes.resize(mesh.n_nodes);

    auto node_id = [n_radial](int ir, int iz) {
        return iz * (n_radial + 1) + ir;
    };

    for (int iz = 0; iz <= n_axial; ++iz) {
        const double z = height * static_cast<double>(iz) / n_axial;
        for (int ir = 0; ir <= n_radial; ++ir)
            mesh.nodes[node_id(ir, iz)] = Node{r_nodes[ir], z};
    }

    mesh.elem_nodes.reserve(static_cast<size_t>(4 * mesh.n_elements));
    for (int iz = 0; iz < n_axial; ++iz) {
        for (int ir = 0; ir < n_radial; ++ir) {
            mesh.elem_nodes.push_back(node_id(ir, iz));
            mesh.elem_nodes.push_back(node_id(ir + 1, iz));
            mesh.elem_nodes.push_back(node_id(ir + 1, iz + 1));
            mesh.elem_nodes.push_back(node_id(ir, iz + 1));
        }
    }
    return mesh;
}

Mesh2D build_t3_mesh_impl(double Ri, double Re, double height,
                          int n_radial, int n_axial, double ratio) {
    Mesh2D mesh = build_q4_mesh_impl(Ri, Re, height, n_radial, n_axial, ratio);
    std::vector<int> tri_conn;
    tri_conn.reserve(static_cast<size_t>(6 * n_radial * n_axial));
    for (int iz = 0; iz < n_axial; ++iz) {
        for (int ir = 0; ir < n_radial; ++ir) {
            const int n00 = iz * (n_radial + 1) + ir;
            const int n10 = n00 + 1;
            const int n01 = (iz + 1) * (n_radial + 1) + ir;
            const int n11 = n01 + 1;
            tri_conn.push_back(n00);
            tri_conn.push_back(n10);
            tri_conn.push_back(n11);
            tri_conn.push_back(n00);
            tri_conn.push_back(n11);
            tri_conn.push_back(n01);
        }
    }
    mesh.elem_nodes = std::move(tri_conn);
    mesh.n_elements = 2 * n_radial * n_axial;
    mesh.nodes_per_element = 3;
    mesh.dofs_per_node = 2;
    return mesh;
}

Mesh2D build_q8_mesh_impl(double Ri, double Re, double height,
                          int n_radial, int n_axial, double ratio) {
    if (n_axial < 1)
        throw std::invalid_argument("build_q8_mesh: n_axial must be >= 1");
    const auto r_edges = radial_edges(Ri, Re, n_radial, ratio, "build_q8_mesh");

    const int nr_fine = 2 * n_radial;
    const int nz_fine = 2 * n_axial;
    std::vector<double> r_fine(nr_fine + 1);
    for (int i = 0; i < n_radial; ++i) {
        r_fine[2 * i] = r_edges[i];
        r_fine[2 * i + 1] = 0.5 * (r_edges[i] + r_edges[i + 1]);
    }
    r_fine[nr_fine] = Re;

    std::vector<int> id((nr_fine + 1) * (nz_fine + 1), -1);
    auto fine_index = [nr_fine](int ir, int iz) {
        return iz * (nr_fine + 1) + ir;
    };

    Mesh2D mesh;
    mesh.nodes_per_element = 8;
    mesh.dofs_per_node = 2;

    for (int iz = 0; iz <= nz_fine; ++iz) {
        const double z = height * static_cast<double>(iz) / nz_fine;
        for (int ir = 0; ir <= nr_fine; ++ir) {
            if ((ir % 2 == 1) && (iz % 2 == 1))
                continue;
            id[fine_index(ir, iz)] = static_cast<int>(mesh.nodes.size());
            mesh.nodes.push_back(Node{r_fine[ir], z});
        }
    }

    auto node_id = [&](int ir, int iz) {
        const int value = id[fine_index(ir, iz)];
        if (value < 0)
            throw std::logic_error("build_q8_mesh: requested cell-center node");
        return value;
    };

    mesh.elem_nodes.reserve(static_cast<size_t>(8 * n_radial * n_axial));
    for (int iz = 0; iz < n_axial; ++iz) {
        for (int ir = 0; ir < n_radial; ++ir) {
            const int i = 2 * ir;
            const int j = 2 * iz;
            mesh.elem_nodes.push_back(node_id(i, j));
            mesh.elem_nodes.push_back(node_id(i + 2, j));
            mesh.elem_nodes.push_back(node_id(i + 2, j + 2));
            mesh.elem_nodes.push_back(node_id(i, j + 2));
            mesh.elem_nodes.push_back(node_id(i + 1, j));
            mesh.elem_nodes.push_back(node_id(i + 2, j + 1));
            mesh.elem_nodes.push_back(node_id(i + 1, j + 2));
            mesh.elem_nodes.push_back(node_id(i, j + 1));
        }
    }
    mesh.n_nodes = static_cast<int>(mesh.nodes.size());
    mesh.n_elements = n_radial * n_axial;
    return mesh;
}

Mesh2D build_q9_mesh_impl(double Ri, double Re, double height,
                          int n_radial, int n_axial, double ratio) {
    if (n_axial < 1)
        throw std::invalid_argument("build_q9_mesh: n_axial must be >= 1");
    const auto r_edges = radial_edges(Ri, Re, n_radial, ratio, "build_q9_mesh");

    const int nr_fine = 2 * n_radial;
    const int nz_fine = 2 * n_axial;
    std::vector<double> r_fine(nr_fine + 1);
    for (int i = 0; i < n_radial; ++i) {
        r_fine[2 * i] = r_edges[i];
        r_fine[2 * i + 1] = 0.5 * (r_edges[i] + r_edges[i + 1]);
    }
    r_fine[nr_fine] = Re;

    auto node_id = [nr_fine](int ir, int iz) {
        return iz * (nr_fine + 1) + ir;
    };

    Mesh2D mesh;
    mesh.n_nodes = (nr_fine + 1) * (nz_fine + 1);
    mesh.n_elements = n_radial * n_axial;
    mesh.nodes_per_element = 9;
    mesh.dofs_per_node = 2;
    mesh.nodes.resize(mesh.n_nodes);

    for (int iz = 0; iz <= nz_fine; ++iz) {
        const double z = height * static_cast<double>(iz) / nz_fine;
        for (int ir = 0; ir <= nr_fine; ++ir)
            mesh.nodes[node_id(ir, iz)] = Node{r_fine[ir], z};
    }

    mesh.elem_nodes.reserve(static_cast<size_t>(9 * n_radial * n_axial));
    for (int iz = 0; iz < n_axial; ++iz) {
        for (int ir = 0; ir < n_radial; ++ir) {
            const int i = 2 * ir;
            const int j = 2 * iz;
            mesh.elem_nodes.push_back(node_id(i, j));
            mesh.elem_nodes.push_back(node_id(i + 2, j));
            mesh.elem_nodes.push_back(node_id(i + 2, j + 2));
            mesh.elem_nodes.push_back(node_id(i, j + 2));
            mesh.elem_nodes.push_back(node_id(i + 1, j));
            mesh.elem_nodes.push_back(node_id(i + 2, j + 1));
            mesh.elem_nodes.push_back(node_id(i + 1, j + 2));
            mesh.elem_nodes.push_back(node_id(i, j + 1));
            mesh.elem_nodes.push_back(node_id(i + 1, j + 1));
        }
    }
    return mesh;
}

Mesh2D build_t6_mesh_impl(double Ri, double Re, double height,
                          int n_radial, int n_axial, double ratio) {
    Mesh2D mesh = build_q9_mesh_impl(Ri, Re, height, n_radial, n_axial, ratio);
    const int nr_fine = 2 * n_radial;
    auto node_id = [nr_fine](int ir, int iz) {
        return iz * (nr_fine + 1) + ir;
    };

    std::vector<int> tri_conn;
    tri_conn.reserve(static_cast<size_t>(12 * n_radial * n_axial));
    for (int iz = 0; iz < n_axial; ++iz) {
        for (int ir = 0; ir < n_radial; ++ir) {
            const int i = 2 * ir;
            const int j = 2 * iz;

            tri_conn.push_back(node_id(i, j));
            tri_conn.push_back(node_id(i + 2, j));
            tri_conn.push_back(node_id(i + 2, j + 2));
            tri_conn.push_back(node_id(i + 1, j));
            tri_conn.push_back(node_id(i + 2, j + 1));
            tri_conn.push_back(node_id(i + 1, j + 1));

            tri_conn.push_back(node_id(i, j));
            tri_conn.push_back(node_id(i + 2, j + 2));
            tri_conn.push_back(node_id(i, j + 2));
            tri_conn.push_back(node_id(i + 1, j + 1));
            tri_conn.push_back(node_id(i + 1, j + 2));
            tri_conn.push_back(node_id(i, j + 1));
        }
    }

    mesh.elem_nodes = std::move(tri_conn);
    mesh.n_elements = 2 * n_radial * n_axial;
    mesh.nodes_per_element = 6;
    mesh.dofs_per_node = 2;
    return mesh;
}

} // namespace

// Build a geometric-progression mesh of AxisymL3 elements.
// Each element has 3 nodes (endpoints + midpoint).
// With n_elem elements there are 2*n_elem+1 nodes total (shared endpoints).
Mesh1D build_mesh_L3(double Ri, double Re, int n_elem, double ratio) {
    if (n_elem < 1)
        throw std::invalid_argument("build_mesh_L3: n_elem must be >= 1");
    if (ratio <= 0.0)
        throw std::invalid_argument("build_mesh_L3: ratio must be > 0");

    // Geometric sequence: h_k = h0 * q^k, sum = h0*(q^n - 1)/(q-1) = Re-Ri
    // ratio = h_{n-1} / h_0 = q^{n-1}
    const int n_nodes = 2 * n_elem + 1;
    std::vector<double> node_r(n_nodes);
    node_r[0] = Ri;

    if (std::abs(ratio - 1.0) < 1e-10) {
        // uniform mesh
        double h = (Re - Ri) / n_elem;
        for (int i = 1; i < n_nodes; ++i)
            node_r[i] = Ri + i * h * 0.5;
    } else {
        double q  = std::pow(ratio, 1.0 / (n_elem - 1));  // growth factor per element
        double h0 = (Re - Ri) * (q - 1.0) / (std::pow(q, n_elem) - 1.0);
        double r  = Ri;
        for (int e = 0; e < n_elem; ++e) {
            double he = h0 * std::pow(q, e);
            int left_node  = 2 * e;
            int mid_node   = 2 * e + 1;
            int right_node = 2 * e + 2;
            node_r[left_node]  = r;
            node_r[mid_node]   = r + 0.5 * he;
            node_r[right_node] = r + he;
            r += he;
        }
        // Correct last node to exactly Re (avoid floating-point drift)
        node_r[n_nodes - 1] = Re;
    }

    // Connectivity: element e uses nodes {2e, 2e+1, 2e+2}
    std::vector<int> conn(3 * n_elem);
    for (int e = 0; e < n_elem; ++e) {
        conn[3 * e + 0] = 2 * e;
        conn[3 * e + 1] = 2 * e + 1;
        conn[3 * e + 2] = 2 * e + 2;
    }

    Mesh1D mesh;
    mesh.node_r = std::move(node_r);
    mesh.nodes.reserve(n_nodes);
    for (double r_node : mesh.node_r)
        mesh.nodes.push_back(Node{r_node, 0.0});
    mesh.elem_nodes = std::move(conn);
    mesh.n_elements = n_elem;
    mesh.n_nodes = n_nodes;
    mesh.nodes_per_element = 3;
    mesh.dofs_per_node = 1;
    return mesh;
}

Mesh2D build_mesh_structured_2d(const std::string& element_type,
                                double Ri,
                                double Re,
                                double height,
                                int n_radial,
                                int n_axial,
                                double ratio) {
    if (element_type == "axisym_2d_Q4")
        return build_q4_mesh_impl(Ri, Re, height, n_radial, n_axial, ratio);
    if (element_type == "axisym_2d_T3")
        return build_t3_mesh_impl(Ri, Re, height, n_radial, n_axial, ratio);
    if (element_type == "axisym_2d_Q8")
        return build_q8_mesh_impl(Ri, Re, height, n_radial, n_axial, ratio);
    if (element_type == "axisym_2d_Q9")
        return build_q9_mesh_impl(Ri, Re, height, n_radial, n_axial, ratio);
    if (element_type == "axisym_2d_AQ9")
        return build_q9_mesh_impl(Ri, Re, height, n_radial, n_axial, ratio);
    if (element_type == "axisym_2d_T6")
        return build_t6_mesh_impl(Ri, Re, height, n_radial, n_axial, ratio);
    throw std::invalid_argument("build_mesh_structured_2d: unsupported element type " +
                                element_type);
}

Eigen::SparseMatrix<double> Assembler::assemble_K(
    const Mesh& mesh,
    const Element& element,
    const ConstitutiveModel& model)
{
    const int n_dof = mesh.total_dofs();
    const int nne   = element.n_nodes();       // 3 for L3
    const int ndpn  = element.n_dofs_per_node();  // 1 for L3
    const int ne_dof = nne * ndpn;

    using Triplet = Eigen::Triplet<double>;
    std::vector<std::vector<Triplet>> element_triplets(mesh.n_elements);

    const Eigen::Matrix4d D = model.D_elastic();
    const auto gps = element.gauss_points();

#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for (int e = 0; e < mesh.n_elements; ++e) {
        // Local node coordinates
        std::vector<Node> coords(nne);
        std::vector<int>    gdofs(ne_dof);
        for (int i = 0; i < nne; ++i) {
            int gnode = mesh.elem_nodes[nne * e + i];
            coords[i] = mesh.nodes[gnode];
            for (int d = 0; d < ndpn; ++d)
                gdofs[i * ndpn + d] = mesh.dof_index(gnode, d);
        }

        Eigen::MatrixXd Ke = Eigen::MatrixXd::Zero(ne_dof, ne_dof);
        for (const auto& gp : gps) {
            Eigen::MatrixXd B  = element.B_matrix(gp, coords);
            double          jw = element.jacobian_weight(gp, coords);
            Ke += B.transpose() * D * B * jw;
        }

        // Scatter into global triplets
        element_triplets[e].reserve(static_cast<size_t>(ne_dof * ne_dof));
        for (int i = 0; i < ne_dof; ++i)
            for (int j = 0; j < ne_dof; ++j)
                element_triplets[e].emplace_back(gdofs[i], gdofs[j], Ke(i, j));
    }

    std::vector<Triplet> triplets;
    triplets.reserve(static_cast<size_t>(ne_dof * ne_dof * mesh.n_elements));
    for (auto& local : element_triplets)
        triplets.insert(triplets.end(), local.begin(), local.end());

    Eigen::SparseMatrix<double> K(n_dof, n_dof);
    K.setFromTriplets(triplets.begin(), triplets.end());
    return K;
}

// Neumann BC for axisymmetric cylinder:
// At r=Ri: force on inner wall node = p_inner * 2π*Ri (outward traction → positive f)
// At r=Re: force on outer wall node = -p_outer * 2π*Re (inward confining pressure)
Eigen::VectorXd Assembler::assemble_neumann(
    const Mesh& mesh,
    double p_inner,
    double p_outer)
{
    constexpr double kTwoPi = 2.0 * 3.14159265358979323846;
    Eigen::VectorXd f = Eigen::VectorXd::Zero(mesh.total_dofs());
    f[mesh.dof_index(0, 0)] = p_inner * kTwoPi * mesh.nodes.front().r;
    f[mesh.dof_index(mesh.n_nodes - 1, 0)] = -p_outer * kTwoPi * mesh.nodes.back().r;
    return f;
}

Eigen::VectorXd Assembler::assemble_boundary_pressure(
    const Mesh& mesh,
    const Element& element,
    double p_inner,
    double p_outer)
{
    ConstantWallPressureField pressure(p_inner);
    return assemble_boundary_pressure(mesh, element, pressure, 0.0, p_outer);
}

Eigen::VectorXd Assembler::assemble_boundary_pressure(
    const Mesh& mesh,
    const Element& element,
    const WallPressureField& inner_pressure,
    double time_s,
    double p_outer)
{
    if (mesh.dofs_per_node == 1)
        return assemble_neumann(
            mesh,
            inner_pressure.pressure_at(Eigen::Vector2d{mesh.nodes.front().r, 0.0}, time_s),
            p_outer);

    constexpr double kTwoPi = 2.0 * 3.14159265358979323846;
    const int nne = element.n_nodes();
    Eigen::VectorXd f = Eigen::VectorXd::Zero(mesh.total_dofs());

    const auto [min_it, max_it] = std::minmax_element(
        mesh.nodes.begin(), mesh.nodes.end(),
        [](const Node& a, const Node& b) { return a.r < b.r; });
    const double Ri = min_it->r;
    const double Re = max_it->r;
    const double tol = 1.0e-10 * std::max(1.0, std::abs(Re));

    auto close = [tol](double a, double b) {
        return std::abs(a - b) <= tol;
    };

    auto add_edge = [&](int e, double xi, bool inner_edge, bool radial_sign,
                        const std::vector<double>& params,
                        const std::vector<double>& weights) {
        std::vector<Node> coords(nne);
        for (int i = 0; i < nne; ++i)
            coords[i] = mesh.nodes[mesh.elem_nodes[nne * e + i]];

        std::vector<double> N(nne), dN_dxi(nne), dN_deta(nne);
        for (size_t q = 0; q < params.size(); ++q) {
            const double s = params[q];
            GaussPoint gp{xi, weights[q], s};
            element.shape_functions(gp, coords, N);
            element.shape_derivatives(gp, coords, dN_dxi, dN_deta);

            double r_gp = 0.0;
            double z_gp = 0.0;
            double dr_ds = 0.0;
            double dz_ds = 0.0;
            for (int i = 0; i < nne; ++i) {
                r_gp += N[i] * coords[i].r;
                z_gp += N[i] * coords[i].z;
                dr_ds += dN_deta[i] * coords[i].r;
                dz_ds += dN_deta[i] * coords[i].z;
            }

            const double line_weight = kTwoPi * r_gp *
                std::sqrt(dr_ds * dr_ds + dz_ds * dz_ds) * weights[q];
            const double sign = radial_sign ? 1.0 : -1.0;
            const double pressure = inner_edge
                ? inner_pressure.pressure_at(Eigen::Vector2d{r_gp, z_gp}, time_s)
                : p_outer;
            for (int i = 0; i < nne; ++i) {
                const int gn = mesh.elem_nodes[nne * e + i];
                f[mesh.dof_index(gn, 0)] += sign * N[i] * pressure * line_weight;
            }
        }
    };

    auto add_tri_edge = [&](int e, bool inner_edge, bool radial_sign, bool outer_edge,
                            const std::vector<double>& params,
                            const std::vector<double>& weights) {
        std::vector<Node> coords(nne);
        for (int i = 0; i < nne; ++i)
            coords[i] = mesh.nodes[mesh.elem_nodes[nne * e + i]];

        std::vector<double> N(nne), dN_dxi(nne), dN_deta(nne);
        for (size_t q = 0; q < params.size(); ++q) {
            const double s = params[q];
            const double xi = outer_edge ? 0.5 * (1.0 - s) : 0.0;
            const double eta = 0.5 * (1.0 + s);
            GaussPoint gp{xi, weights[q], eta};
            element.shape_functions(gp, coords, N);
            element.shape_derivatives(gp, coords, dN_dxi, dN_deta);

            double r_gp = 0.0;
            double z_gp = 0.0;
            double dr_ds = 0.0;
            double dz_ds = 0.0;
            for (int i = 0; i < nne; ++i) {
                r_gp += N[i] * coords[i].r;
                z_gp += N[i] * coords[i].z;
                const double dN_ds = outer_edge
                    ? 0.5 * (-dN_dxi[i] + dN_deta[i])
                    : 0.5 * dN_deta[i];
                dr_ds += dN_ds * coords[i].r;
                dz_ds += dN_ds * coords[i].z;
            }

            const double line_weight = kTwoPi * r_gp *
                std::sqrt(dr_ds * dr_ds + dz_ds * dz_ds) * weights[q];
            const double sign = radial_sign ? 1.0 : -1.0;
            const double pressure = inner_edge
                ? inner_pressure.pressure_at(Eigen::Vector2d{r_gp, z_gp}, time_s)
                : p_outer;
            for (int i = 0; i < nne; ++i) {
                const int gn = mesh.elem_nodes[nne * e + i];
                f[mesh.dof_index(gn, 0)] += sign * N[i] * pressure * line_weight;
            }
        }
    };

    const double a2 = 1.0 / std::sqrt(3.0);
    const std::vector<double> line_2 = {-a2, a2};
    const std::vector<double> w_2 = {1.0, 1.0};
    const double a3 = std::sqrt(3.0 / 5.0);
    const std::vector<double> line_3 = {-a3, 0.0, a3};
    const std::vector<double> w_3 = {5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0};

    for (int e = 0; e < mesh.n_elements; ++e) {
        std::vector<Node> coords(nne);
        for (int i = 0; i < nne; ++i)
            coords[i] = mesh.nodes[mesh.elem_nodes[nne * e + i]];

        if ((nne == 4 || nne == 8 || nne == 9) &&
            close(coords[0].r, Ri) && close(coords[3].r, Ri)) {
            const auto& points = (nne == 4) ? line_2 : line_3;
            const auto& weights = (nne == 4) ? w_2 : w_3;
            add_edge(e, -1.0, true, true, points, weights);
        }
        if ((nne == 4 || nne == 8 || nne == 9) &&
            close(coords[1].r, Re) && close(coords[2].r, Re) && p_outer != 0.0) {
            const auto& points = (nne == 4) ? line_2 : line_3;
            const auto& weights = (nne == 4) ? w_2 : w_3;
            add_edge(e, 1.0, false, false, points, weights);
        }
        if ((nne == 3 || nne == 6) &&
            close(coords[0].r, Ri) && close(coords[2].r, Ri)) {
            const auto& points = (nne == 3) ? line_2 : line_3;
            const auto& weights = (nne == 3) ? w_2 : w_3;
            add_tri_edge(e, true, true, false, points, weights);
        }
        if ((nne == 3 || nne == 6) &&
            close(coords[1].r, Re) && close(coords[2].r, Re) && p_outer != 0.0) {
            const auto& points = (nne == 3) ? line_2 : line_3;
            const auto& weights = (nne == 3) ? w_2 : w_3;
            add_tri_edge(e, false, false, true, points, weights);
        }
    }

    return f;
}

// Geostatic internal force: f_geo = Σ_e Σ_gp  Bᵀ · σ_geo · jw
// Note: σ_geo is used directly (no D multiplication), consistent with SESTSAL fisg.
Eigen::VectorXd Assembler::assemble_geostatic_force(
    const Mesh&                 mesh,
    const Element&              element,
    const std::vector<Stress>&  sigma_geo_gp)
{
    const int nne  = element.n_nodes();
    const int ndpn = element.n_dofs_per_node();
    const auto gps = element.gauss_points();
    const int n_gp = static_cast<int>(gps.size());
    std::vector<ElementForce> element_forces(mesh.n_elements);

#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for (int e = 0; e < mesh.n_elements; ++e) {
        std::vector<Node> coords(nne);
        std::vector<int>    gdofs(nne * ndpn);
        for (int i = 0; i < nne; ++i) {
            int gnode  = mesh.elem_nodes[nne * e + i];
            coords[i]  = mesh.nodes[gnode];
            for (int d = 0; d < ndpn; ++d)
                gdofs[i * ndpn + d] = mesh.dof_index(gnode, d);
        }
        Eigen::VectorXd fe_total = Eigen::VectorXd::Zero(nne * ndpn);
        for (int g = 0; g < n_gp; ++g) {
            const Stress& sig  = sigma_geo_gp[e * n_gp + g];
            Eigen::MatrixXd B  = element.B_matrix(gps[g], coords);
            double          jw = element.jacobian_weight(gps[g], coords);
            Eigen::VectorXd fe = B.transpose() * sig * jw;
            for (int i = 0; i < static_cast<int>(gdofs.size()); ++i)
                fe_total[i] += fe[i];
        }
        element_forces[e] = ElementForce{std::move(gdofs), std::move(fe_total)};
    }

    Eigen::VectorXd f = Eigen::VectorXd::Zero(mesh.total_dofs());
    for (const auto& local : element_forces)
        for (int i = 0; i < static_cast<int>(local.gdofs.size()); ++i)
            f[local.gdofs[i]] += local.values[i];
    return f;
}

// Pseudo-force from viscous strain increments: f_v = Σ_e Σ_gp  Bᵀ D Δε^v jw
// delta_eps_v_gp[e * n_gp + g]: Strain (Voigt 4-vector) for element e, gauss point g.
Eigen::VectorXd Assembler::assemble_pseudo_force(
    const Mesh&                mesh,
    const Element&             element,
    const ConstitutiveModel&   model,
    const std::vector<Strain>& delta_eps_v_gp)
{
    const int nne  = element.n_nodes();
    const int ndpn = element.n_dofs_per_node();  // 1 for L3
    const Eigen::Matrix4d D = model.D_elastic();
    const auto gps = element.gauss_points();
    const int n_gp = static_cast<int>(gps.size());
    std::vector<ElementForce> element_forces(mesh.n_elements);

#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for (int e = 0; e < mesh.n_elements; ++e) {
        std::vector<Node> coords(nne);
        std::vector<int>    gdofs(nne * ndpn);
        for (int i = 0; i < nne; ++i) {
            int gnode  = mesh.elem_nodes[nne * e + i];
            coords[i]  = mesh.nodes[gnode];
            for (int d = 0; d < ndpn; ++d)
                gdofs[i * ndpn + d] = mesh.dof_index(gnode, d);
        }

        Eigen::VectorXd fe_total = Eigen::VectorXd::Zero(nne * ndpn);
        for (int g = 0; g < n_gp; ++g) {
            const Strain& depsv = delta_eps_v_gp[e * n_gp + g];
            Eigen::MatrixXd B   = element.B_matrix(gps[g], coords);
            double          jw  = element.jacobian_weight(gps[g], coords);
            Eigen::VectorXd fe  = B.transpose() * (D * depsv) * jw;
            for (int i = 0; i < static_cast<int>(gdofs.size()); ++i)
                fe_total[i] += fe[i];
        }
        element_forces[e] = ElementForce{std::move(gdofs), std::move(fe_total)};
    }

    Eigen::VectorXd f = Eigen::VectorXd::Zero(mesh.total_dofs());
    for (const auto& local : element_forces)
        for (int i = 0; i < static_cast<int>(local.gdofs.size()); ++i)
            f[local.gdofs[i]] += local.values[i];
    return f;
}
