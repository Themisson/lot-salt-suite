#pragma once
#include <algorithm>
#include <cmath>
#include <map>
#include <stdexcept>
#include <utility>
#include <vector>

#include <Eigen/Sparse>

#include "constitutive/elastic_isotropic.hpp"
#include "elements/axisym_2d_aq9.hpp"
#include "elements/axisym_2d_q4.hpp"
#include "elements/axisym_2d_q8.hpp"
#include "elements/axisym_2d_q9.hpp"
#include "elements/axisym_2d_t3.hpp"
#include "elements/axisym_2d_t6.hpp"
#include "mesh/Mesh.hpp"
#include "solver/ElasticSolver.hpp"

inline Mesh2D build_q4_mesh(double Ri, double Re, double height,
                            int n_radial, int n_axial, double ratio = 1.0) {
    if (n_radial < 1 || n_axial < 1)
        throw std::invalid_argument("build_q4_mesh: element counts must be positive");

    std::vector<double> r_nodes(n_radial + 1);
    r_nodes[0] = Ri;
    if (std::abs(ratio - 1.0) < 1e-12) {
        const double h = (Re - Ri) / n_radial;
        for (int i = 1; i <= n_radial; ++i)
            r_nodes[i] = Ri + i * h;
    } else {
        const double q = std::pow(ratio, 1.0 / (n_radial - 1));
        const double h0 = (Re - Ri) * (q - 1.0) / (std::pow(q, n_radial) - 1.0);
        double r = Ri;
        for (int i = 0; i < n_radial; ++i) {
            r_nodes[i] = r;
            r += h0 * std::pow(q, i);
        }
        r_nodes[n_radial] = Re;
    }

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

    mesh.elem_nodes.reserve(4 * mesh.n_elements);
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

inline Mesh2D build_t3_mesh(double Ri, double Re, double height,
                            int n_radial, int n_axial, double ratio = 1.0) {
    Mesh2D mesh = build_q4_mesh(Ri, Re, height, n_radial, n_axial, ratio);
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

inline Mesh2D build_q8_mesh(double Ri, double Re, double height,
                            int n_radial, int n_axial, double ratio = 1.0) {
    if (n_radial < 1 || n_axial < 1)
        throw std::invalid_argument("build_q8_mesh: element counts must be positive");

    std::vector<double> r_edges(n_radial + 1);
    r_edges[0] = Ri;
    if (std::abs(ratio - 1.0) < 1e-12) {
        const double h = (Re - Ri) / n_radial;
        for (int i = 1; i <= n_radial; ++i)
            r_edges[i] = Ri + i * h;
    } else {
        const double q = std::pow(ratio, 1.0 / (n_radial - 1));
        const double h0 = (Re - Ri) * (q - 1.0) / (std::pow(q, n_radial) - 1.0);
        double r = Ri;
        for (int i = 0; i < n_radial; ++i) {
            r_edges[i] = r;
            r += h0 * std::pow(q, i);
        }
        r_edges[n_radial] = Re;
    }

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

inline Mesh2D build_q9_mesh(double Ri, double Re, double height,
                            int n_radial, int n_axial, double ratio = 1.0) {
    if (n_radial < 1 || n_axial < 1)
        throw std::invalid_argument("build_q9_mesh: element counts must be positive");

    std::vector<double> r_edges(n_radial + 1);
    r_edges[0] = Ri;
    if (std::abs(ratio - 1.0) < 1e-12) {
        const double h = (Re - Ri) / n_radial;
        for (int i = 1; i <= n_radial; ++i)
            r_edges[i] = Ri + i * h;
    } else {
        const double q = std::pow(ratio, 1.0 / (n_radial - 1));
        const double h0 = (Re - Ri) * (q - 1.0) / (std::pow(q, n_radial) - 1.0);
        double r = Ri;
        for (int i = 0; i < n_radial; ++i) {
            r_edges[i] = r;
            r += h0 * std::pow(q, i);
        }
        r_edges[n_radial] = Re;
    }

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

inline Mesh2D build_aq9_mesh(double Ri, double Re, double height,
                             int n_radial, int n_axial, double ratio = 1.0) {
    return build_q9_mesh(Ri, Re, height, n_radial, n_axial, ratio);
}

inline Mesh2D build_t6_mesh(double Ri, double Re, double height,
                            int n_radial, int n_axial, double ratio = 1.0) {
    Mesh2D mesh = build_q9_mesh(Ri, Re, height, n_radial, n_axial, ratio);
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

inline Eigen::SparseMatrix<double> dense_to_sparse(const Eigen::MatrixXd& dense) {
    std::vector<Eigen::Triplet<double>> triplets;
    triplets.reserve(static_cast<size_t>(dense.rows() * dense.cols()));
    for (int i = 0; i < dense.rows(); ++i)
        for (int j = 0; j < dense.cols(); ++j)
            if (dense(i, j) != 0.0)
                triplets.emplace_back(i, j, dense(i, j));
    Eigen::SparseMatrix<double> sparse(dense.rows(), dense.cols());
    sparse.setFromTriplets(triplets.begin(), triplets.end());
    return sparse;
}

inline void apply_nonzero_dirichlet(Eigen::MatrixXd& K, Eigen::VectorXd& f,
                                    const std::map<int, double>& prescribed) {
    for (const auto& [dof, value] : prescribed)
        f -= K.col(dof) * value;

    for (const auto& [dof, value] : prescribed) {
        K.row(dof).setZero();
        K.col(dof).setZero();
        K(dof, dof) = 1.0;
        f[dof] = value;
    }
}

inline Eigen::VectorXd solve_with_dirichlet(Eigen::SparseMatrix<double> K_sparse,
                                            Eigen::VectorXd f,
                                            const std::map<int, double>& prescribed) {
    Eigen::MatrixXd K = Eigen::MatrixXd(K_sparse);
    apply_nonzero_dirichlet(K, f, prescribed);
    return ElasticSolver{}.solve(dense_to_sparse(K), f, {}).u;
}

inline std::vector<Node> element_coords(const Mesh& mesh, int elem_id, int nne) {
    std::vector<Node> coords(nne);
    for (int i = 0; i < nne; ++i)
        coords[i] = mesh.nodes[mesh.elem_nodes[nne * elem_id + i]];
    return coords;
}

inline Eigen::VectorXd assemble_inner_pressure_q4(const Mesh& mesh, const AxisymQ4& elem,
                                                  int n_radial, int n_axial,
                                                  double pressure) {
    constexpr double kTwoPi = 2.0 * 3.14159265358979323846;
    Eigen::VectorXd f = Eigen::VectorXd::Zero(mesh.total_dofs());
    const double a = 1.0 / std::sqrt(3.0);
    const double etas[2] = {-a, a};

    for (int iz = 0; iz < n_axial; ++iz) {
        const int elem_id = iz * n_radial;
        auto coords = element_coords(mesh, elem_id, elem.n_nodes());
        for (double eta : etas) {
            GaussPoint gp{-1.0, 1.0, eta};
            double N[4];
            elem.shape_functions(gp, N);
            double r_gp = 0.0;
            double dz_deta = 0.0;
            double dN_dxi[4], dN_deta[4];
            elem.shape_derivatives(gp, dN_dxi, dN_deta);
            for (int i = 0; i < 4; ++i) {
                r_gp += N[i] * coords[i].r;
                dz_deta += dN_deta[i] * coords[i].z;
            }
            const double line_weight = kTwoPi * r_gp * std::abs(dz_deta);
            for (int local : {0, 3}) {
                const int gn = mesh.elem_nodes[4 * elem_id + local];
                f[mesh.dof_index(gn, 0)] += N[local] * pressure * line_weight;
            }
        }
    }
    return f;
}

inline Eigen::VectorXd assemble_inner_pressure_t3(const Mesh& mesh, const AxisymT3& elem,
                                                  int n_radial, int n_axial,
                                                  double pressure) {
    constexpr double kTwoPi = 2.0 * 3.14159265358979323846;
    Eigen::VectorXd f = Eigen::VectorXd::Zero(mesh.total_dofs());
    const double a = 1.0 / std::sqrt(3.0);
    const double s_points[2] = {-a, a};

    for (int iz = 0; iz < n_axial; ++iz) {
        const int elem_id = 2 * (iz * n_radial) + 1;
        auto coords = element_coords(mesh, elem_id, elem.n_nodes());
        for (double s : s_points) {
            const double n0 = 0.5 * (1.0 - s);
            const double n2 = 0.5 * (1.0 + s);
            const double r_gp = n0 * coords[0].r + n2 * coords[2].r;
            const double dz_ds = 0.5 * (coords[2].z - coords[0].z);
            const double line_weight = kTwoPi * r_gp * std::abs(dz_ds);

            const int gn0 = mesh.elem_nodes[3 * elem_id + 0];
            const int gn2 = mesh.elem_nodes[3 * elem_id + 2];
            f[mesh.dof_index(gn0, 0)] += n0 * pressure * line_weight;
            f[mesh.dof_index(gn2, 0)] += n2 * pressure * line_weight;
        }
    }
    return f;
}

inline Eigen::VectorXd assemble_inner_pressure_q8(const Mesh& mesh, const AxisymQ8& elem,
                                                  int n_radial, int n_axial,
                                                  double pressure) {
    constexpr double kTwoPi = 2.0 * 3.14159265358979323846;
    Eigen::VectorXd f = Eigen::VectorXd::Zero(mesh.total_dofs());
    const double a = std::sqrt(3.0 / 5.0);
    const double etas[3] = {-a, 0.0, a};
    const double weights[3] = {5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0};

    for (int iz = 0; iz < n_axial; ++iz) {
        const int elem_id = iz * n_radial;
        auto coords = element_coords(mesh, elem_id, elem.n_nodes());
        for (int q = 0; q < 3; ++q) {
            GaussPoint gp{-1.0, weights[q], etas[q]};
            double N[8], dN_dxi[8], dN_deta[8];
            elem.shape_functions(gp, N);
            elem.shape_derivatives(gp, dN_dxi, dN_deta);
            double r_gp = 0.0;
            double dr_deta = 0.0;
            double dz_deta = 0.0;
            for (int i = 0; i < 8; ++i) {
                r_gp += N[i] * coords[i].r;
                dr_deta += dN_deta[i] * coords[i].r;
                dz_deta += dN_deta[i] * coords[i].z;
            }
            const double line_weight = kTwoPi * r_gp *
                std::sqrt(dr_deta * dr_deta + dz_deta * dz_deta) * weights[q];
            for (int local : {0, 3, 7}) {
                const int gn = mesh.elem_nodes[8 * elem_id + local];
                f[mesh.dof_index(gn, 0)] += N[local] * pressure * line_weight;
            }
        }
    }
    return f;
}

inline Eigen::VectorXd assemble_inner_pressure_q9(const Mesh& mesh, const AxisymQ9& elem,
                                                  int n_radial, int n_axial,
                                                  double pressure) {
    constexpr double kTwoPi = 2.0 * 3.14159265358979323846;
    Eigen::VectorXd f = Eigen::VectorXd::Zero(mesh.total_dofs());
    const double a = std::sqrt(3.0 / 5.0);
    const double etas[3] = {-a, 0.0, a};
    const double weights[3] = {5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0};

    for (int iz = 0; iz < n_axial; ++iz) {
        const int elem_id = iz * n_radial;
        auto coords = element_coords(mesh, elem_id, elem.n_nodes());
        for (int q = 0; q < 3; ++q) {
            GaussPoint gp{-1.0, weights[q], etas[q]};
            double N[9], dN_dxi[9], dN_deta[9];
            elem.shape_functions(gp, N);
            elem.shape_derivatives(gp, dN_dxi, dN_deta);
            double r_gp = 0.0;
            double dr_deta = 0.0;
            double dz_deta = 0.0;
            for (int i = 0; i < 9; ++i) {
                r_gp += N[i] * coords[i].r;
                dr_deta += dN_deta[i] * coords[i].r;
                dz_deta += dN_deta[i] * coords[i].z;
            }
            const double line_weight = kTwoPi * r_gp *
                std::sqrt(dr_deta * dr_deta + dz_deta * dz_deta) * weights[q];
            for (int local : {0, 3, 7}) {
                const int gn = mesh.elem_nodes[9 * elem_id + local];
                f[mesh.dof_index(gn, 0)] += N[local] * pressure * line_weight;
            }
        }
    }
    return f;
}

inline Eigen::VectorXd assemble_inner_pressure_aq9(const Mesh& mesh, const AxisymAQ9& elem,
                                                   int n_radial, int n_axial,
                                                   double pressure) {
    constexpr double kTwoPi = 2.0 * 3.14159265358979323846;
    Eigen::VectorXd f = Eigen::VectorXd::Zero(mesh.total_dofs());
    const double a = std::sqrt(3.0 / 5.0);
    const double etas[3] = {-a, 0.0, a};
    const double weights[3] = {5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0};

    for (int iz = 0; iz < n_axial; ++iz) {
        const int elem_id = iz * n_radial;
        auto coords = element_coords(mesh, elem_id, elem.n_nodes());
        for (int q = 0; q < 3; ++q) {
            GaussPoint gp{-1.0, weights[q], etas[q]};
            double N[9], dN_dxi[9], dN_deta[9];
            elem.shape_functions(gp, coords, N);
            elem.shape_derivatives(gp, coords, dN_dxi, dN_deta);
            double r_gp = 0.0;
            double dr_deta = 0.0;
            double dz_deta = 0.0;
            for (int i = 0; i < 9; ++i) {
                r_gp += N[i] * coords[i].r;
                dr_deta += dN_deta[i] * coords[i].r;
                dz_deta += dN_deta[i] * coords[i].z;
            }
            const double line_weight = kTwoPi * r_gp *
                std::sqrt(dr_deta * dr_deta + dz_deta * dz_deta) * weights[q];
            for (int local : {0, 3, 7}) {
                const int gn = mesh.elem_nodes[9 * elem_id + local];
                f[mesh.dof_index(gn, 0)] += N[local] * pressure * line_weight;
            }
        }
    }
    return f;
}

inline Eigen::VectorXd assemble_inner_pressure_t6(const Mesh& mesh, const AxisymT6& elem,
                                                  int n_radial, int n_axial,
                                                  double pressure) {
    constexpr double kTwoPi = 2.0 * 3.14159265358979323846;
    Eigen::VectorXd f = Eigen::VectorXd::Zero(mesh.total_dofs());
    const double a = std::sqrt(3.0 / 5.0);
    const double s_points[3] = {-a, 0.0, a};
    const double weights[3] = {5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0};

    for (int iz = 0; iz < n_axial; ++iz) {
        const int elem_id = 2 * (iz * n_radial) + 1;
        auto coords = element_coords(mesh, elem_id, elem.n_nodes());
        for (int q = 0; q < 3; ++q) {
            const double eta = 0.5 * (1.0 + s_points[q]);
            GaussPoint gp{0.0, weights[q], eta};
            double N[6], dN_dxi[6], dN_deta[6];
            elem.shape_functions(gp, N);
            elem.shape_derivatives(gp, dN_dxi, dN_deta);

            double r_gp = 0.0;
            double dr_deta = 0.0;
            double dz_deta = 0.0;
            for (int i = 0; i < 6; ++i) {
                r_gp += N[i] * coords[i].r;
                dr_deta += dN_deta[i] * coords[i].r;
                dz_deta += dN_deta[i] * coords[i].z;
            }
            const double line_weight = kTwoPi * r_gp *
                0.5 * std::sqrt(dr_deta * dr_deta + dz_deta * dz_deta) * weights[q];
            for (int local : {0, 2, 5}) {
                const int gn = mesh.elem_nodes[6 * elem_id + local];
                f[mesh.dof_index(gn, 0)] += N[local] * pressure * line_weight;
            }
        }
    }
    return f;
}

inline std::map<int, double> all_axial_fixed(const Mesh& mesh) {
    std::map<int, double> bc;
    for (int n = 0; n < mesh.n_nodes; ++n)
        bc[mesh.dof_index(n, 1)] = 0.0;
    return bc;
}
