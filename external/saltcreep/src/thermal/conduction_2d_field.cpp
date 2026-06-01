#include "thermal/conduction_2d_field.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#include <utility>

#include <Eigen/LU>

namespace {
constexpr double kPi = 3.14159265358979323846;

Eigen::MatrixXd submatrix(const Eigen::MatrixXd& M,
                          const std::vector<int>& rows,
                          const std::vector<int>& cols) {
    Eigen::MatrixXd out(rows.size(), cols.size());
    for (int i = 0; i < static_cast<int>(rows.size()); ++i)
        for (int j = 0; j < static_cast<int>(cols.size()); ++j)
            out(i, j) = M(rows[i], cols[j]);
    return out;
}

Eigen::VectorXd subvector(const Eigen::VectorXd& v,
                          const std::vector<int>& rows) {
    Eigen::VectorXd out(rows.size());
    for (int i = 0; i < static_cast<int>(rows.size()); ++i)
        out[i] = v[rows[i]];
    return out;
}

void scatter(Eigen::VectorXd& target,
             const std::vector<int>& rows,
             const Eigen::VectorXd& values) {
    for (int i = 0; i < static_cast<int>(rows.size()); ++i)
        target[rows[i]] = values[i];
}

bool contains(const std::vector<int>& values, int value) {
    return std::find(values.begin(), values.end(), value) != values.end();
}

void add_unique(std::vector<int>& ids, int id) {
    if (!contains(ids, id))
        ids.push_back(id);
}

struct ShapeEval {
    std::vector<double> N;
    std::vector<double> dN_dxi;
    std::vector<double> dN_deta;
};

ShapeEval eval_shape(const Element& element,
                     const GaussPoint& gp,
                     const std::vector<Node>& coords) {
    const int nne = element.n_nodes();
    ShapeEval out;
    out.N.assign(nne, 0.0);
    out.dN_dxi.assign(nne, 0.0);
    out.dN_deta.assign(nne, 0.0);
    element.shape_functions(gp, coords, out.N);
    element.shape_derivatives(gp, coords, out.dN_dxi, out.dN_deta);
    return out;
}

bool local_coordinates(const Element& element,
                       const std::vector<Node>& coords,
                       const Eigen::Vector2d& x,
                       double& xi,
                       double& eta) {
    xi = (element.n_nodes() == 3 || element.n_nodes() == 6) ? 1.0 / 3.0 : 0.0;
    eta = (element.n_nodes() == 3 || element.n_nodes() == 6) ? 1.0 / 3.0 : 0.0;
    for (int iter = 0; iter < 12; ++iter) {
        const GaussPoint gp{xi, eta, 1.0};
        const auto shape = eval_shape(element, gp, coords);
        double r = 0.0;
        double z = 0.0;
        double dr_dxi = 0.0;
        double dr_deta = 0.0;
        double dz_dxi = 0.0;
        double dz_deta = 0.0;
        for (int i = 0; i < element.n_nodes(); ++i) {
            r += shape.N[i] * coords[i].r;
            z += shape.N[i] * coords[i].z;
            dr_dxi += shape.dN_dxi[i] * coords[i].r;
            dr_deta += shape.dN_deta[i] * coords[i].r;
            dz_dxi += shape.dN_dxi[i] * coords[i].z;
            dz_deta += shape.dN_deta[i] * coords[i].z;
        }
        Eigen::Matrix2d J;
        J << dr_dxi, dr_deta,
             dz_dxi, dz_deta;
        const double detJ = J.determinant();
        if (std::abs(detJ) < 1.0e-30)
            return false;
        const Eigen::Vector2d delta = J.fullPivLu().solve(x - Eigen::Vector2d(r, z));
        xi += delta[0];
        eta += delta[1];
        if (delta.norm() < 1.0e-12)
            return true;
    }
    return true;
}
} // namespace

Conduction2DField::Conduction2DField(const Mesh2D& mesh,
                                     const Element& element,
                                     Conduction2DOptions options)
    : mesh_(mesh)
    , element_(element)
    , options_(std::move(options))
    , T_(Eigen::VectorXd::Constant(mesh.n_nodes, options_.initial_T_K)) {
    if (mesh_.n_nodes < 3 || mesh_.n_elements < 1)
        throw std::invalid_argument("Conduction2DField: empty mesh");
    if (mesh_.dofs_per_node != 2)
        throw std::invalid_argument("Conduction2DField: Mesh2D must have 2 mechanical DOFs per node");
    if (options_.k_W_m_K <= 0.0 || options_.rho_kg_m3 <= 0.0 ||
        options_.cp_J_kg_K <= 0.0)
        throw std::invalid_argument("Conduction2DField: thermal properties must be positive");
    if (options_.dt_thermal_s <= 0.0)
        throw std::invalid_argument("Conduction2DField: dt_thermal_s must be positive");
    if (options_.beta < 0.0 || options_.beta > 1.0)
        throw std::invalid_argument("Conduction2DField: beta must be in [0, 1]");
    if (options_.outer_bc != "prescribed" && options_.outer_bc != "flux_zero")
        throw std::invalid_argument("Conduction2DField: outer_bc must be prescribed or flux_zero");
    if (options_.top_bc != "prescribed" && options_.top_bc != "flux_zero")
        throw std::invalid_argument("Conduction2DField: top_bc must be prescribed or flux_zero");
    if (options_.bottom_bc != "prescribed" && options_.bottom_bc != "flux_zero")
        throw std::invalid_argument("Conduction2DField: bottom_bc must be prescribed or flux_zero");
    for (const auto& layer : options_.layers) {
        if (layer.z_bottom_m <= layer.z_top_m ||
            layer.k_W_m_K <= 0.0 || layer.rho_kg_m3 <= 0.0 || layer.cp_J_kg_K <= 0.0)
            throw std::invalid_argument("Conduction2DField: invalid thermal layer");
    }
    if (!options_.initial_nodal_T_K.empty()) {
        if (static_cast<int>(options_.initial_nodal_T_K.size()) != mesh_.n_nodes)
            throw std::invalid_argument("Conduction2DField: initial_nodal_T_K size mismatch");
        for (int i = 0; i < mesh_.n_nodes; ++i)
            T_[i] = options_.initial_nodal_T_K[i];
    }

    setup_boundary_sets();
    apply_prescribed_temperatures(T_);
    T_initial_ = T_;
    assemble_matrices();
}

void Conduction2DField::setup_boundary_sets() {
    prescribed_.clear();
    unknown_.clear();
    const auto r_minmax = std::minmax_element(
        mesh_.nodes.begin(), mesh_.nodes.end(),
        [](const Node& a, const Node& b) { return a.r < b.r; });
    const auto z_minmax = std::minmax_element(
        mesh_.nodes.begin(), mesh_.nodes.end(),
        [](const Node& a, const Node& b) { return a.z < b.z; });
    const double Ri = r_minmax.first->r;
    const double Re = r_minmax.second->r;
    const double z_top = z_minmax.first->z;
    const double z_bottom = z_minmax.second->z;
    const double r_tol = 1.0e-10 * std::max(1.0, std::abs(Re - Ri));
    const double z_tol = 1.0e-10 * std::max(1.0, std::abs(z_bottom - z_top));

    for (int n = 0; n < mesh_.n_nodes; ++n) {
        const Node& node = mesh_.nodes[n];
        if (std::abs(node.r - Ri) <= r_tol)
            add_unique(prescribed_, n);
        if (options_.outer_bc == "prescribed" && std::abs(node.r - Re) <= r_tol)
            add_unique(prescribed_, n);
        if (options_.top_bc == "prescribed" && std::abs(node.z - z_top) <= z_tol)
            add_unique(prescribed_, n);
        if (options_.bottom_bc == "prescribed" && std::abs(node.z - z_bottom) <= z_tol)
            add_unique(prescribed_, n);
    }
    std::sort(prescribed_.begin(), prescribed_.end());

    for (int i = 0; i < mesh_.n_nodes; ++i) {
        if (!contains(prescribed_, i))
            unknown_.push_back(i);
    }
}

void Conduction2DField::apply_prescribed_temperatures(Eigen::VectorXd& T) const {
    const auto r_minmax = std::minmax_element(
        mesh_.nodes.begin(), mesh_.nodes.end(),
        [](const Node& a, const Node& b) { return a.r < b.r; });
    const auto z_minmax = std::minmax_element(
        mesh_.nodes.begin(), mesh_.nodes.end(),
        [](const Node& a, const Node& b) { return a.z < b.z; });
    const double Ri = r_minmax.first->r;
    const double Re = r_minmax.second->r;
    const double z_top = z_minmax.first->z;
    const double z_bottom = z_minmax.second->z;
    const double r_tol = 1.0e-10 * std::max(1.0, std::abs(Re - Ri));
    const double z_tol = 1.0e-10 * std::max(1.0, std::abs(z_bottom - z_top));

    for (int n = 0; n < mesh_.n_nodes; ++n) {
        const Node& node = mesh_.nodes[n];
        if (std::abs(node.r - Ri) <= r_tol) {
            T[n] = options_.inner_wall_T_K;
        } else if (options_.outer_bc == "prescribed" && std::abs(node.r - Re) <= r_tol) {
            T[n] = options_.outer_T_K;
        } else if (options_.top_bc == "prescribed" && std::abs(node.z - z_top) <= z_tol) {
            T[n] = options_.top_T_K;
        } else if (options_.bottom_bc == "prescribed" && std::abs(node.z - z_bottom) <= z_tol) {
            T[n] = options_.bottom_T_K;
        }
    }
}

Conduction2DField::LayerProperties Conduction2DField::properties_at(double z) const {
    for (const auto& layer : options_.layers) {
        if (z >= layer.z_top_m - 1.0e-12 && z <= layer.z_bottom_m + 1.0e-12)
            return {layer.k_W_m_K, layer.rho_kg_m3 * layer.cp_J_kg_K};
    }
    return {options_.k_W_m_K, options_.rho_kg_m3 * options_.cp_J_kg_K};
}

void Conduction2DField::assemble_matrices() {
    const int nne = element_.n_nodes();
    C_ = Eigen::MatrixXd::Zero(mesh_.n_nodes, mesh_.n_nodes);
    H_ = Eigen::MatrixXd::Zero(mesh_.n_nodes, mesh_.n_nodes);
    const auto gps = element_.gauss_points();

    for (int e = 0; e < mesh_.n_elements; ++e) {
        std::vector<Node> coords(nne);
        std::vector<int> nodes(nne);
        for (int i = 0; i < nne; ++i) {
            nodes[i] = mesh_.elem_nodes[nne * e + i];
            coords[i] = mesh_.nodes[nodes[i]];
        }

        for (const auto& gp : gps) {
            const auto shape = eval_shape(element_, gp, coords);
            double r = 0.0;
            double z = 0.0;
            double dr_dxi = 0.0;
            double dr_deta = 0.0;
            double dz_dxi = 0.0;
            double dz_deta = 0.0;
            for (int i = 0; i < nne; ++i) {
                r += shape.N[i] * coords[i].r;
                z += shape.N[i] * coords[i].z;
                dr_dxi += shape.dN_dxi[i] * coords[i].r;
                dr_deta += shape.dN_deta[i] * coords[i].r;
                dz_dxi += shape.dN_dxi[i] * coords[i].z;
                dz_deta += shape.dN_deta[i] * coords[i].z;
            }
            Eigen::Matrix2d J;
            J << dr_dxi, dr_deta,
                 dz_dxi, dz_deta;
            const double detJ = J.determinant();
            if (r <= 0.0 || std::abs(detJ) < 1.0e-30)
                throw std::domain_error("Conduction2DField: invalid thermal Jacobian");
            const Eigen::Matrix2d invJT = J.inverse().transpose();
            const auto props = properties_at(z);
            const double jw = 2.0 * kPi * r * std::abs(detJ) * gp.weight;

            for (int i = 0; i < nne; ++i) {
                const Eigen::Vector2d grad_i =
                    invJT * Eigen::Vector2d(shape.dN_dxi[i], shape.dN_deta[i]);
                for (int j = 0; j < nne; ++j) {
                    const Eigen::Vector2d grad_j =
                        invJT * Eigen::Vector2d(shape.dN_dxi[j], shape.dN_deta[j]);
                    C_(nodes[i], nodes[j]) += props.rho_cp * shape.N[i] * shape.N[j] * jw;
                    H_(nodes[i], nodes[j]) += props.k * grad_i.dot(grad_j) * jw;
                }
            }
        }
    }
}

void Conduction2DField::advance_to(double t_s) const {
    if (t_s < current_time_s_ - 1.0e-9) {
        T_ = T_initial_;
        current_time_s_ = 0.0;
        last_boundary_heat_J_ = 0.0;
        cached_dt_s_ = -1.0;
    }

    while (current_time_s_ + 1.0e-12 < t_s) {
        const double dt = std::min(options_.dt_thermal_s, t_s - current_time_s_);
        advance_one_step(dt);
        current_time_s_ += dt;
    }
}

void Conduction2DField::advance_one_step(double dt_s) const {
    if (unknown_.empty()) {
        last_boundary_heat_J_ = 0.0;
        return;
    }

    const double beta = options_.beta;
    const Eigen::VectorXd T_old = T_;
    Eigen::VectorXd T_new = T_old;
    apply_prescribed_temperatures(T_new);

    const Eigen::MatrixXd Cuu = submatrix(C_, unknown_, unknown_);
    const Eigen::MatrixXd Huu = submatrix(H_, unknown_, unknown_);
    const Eigen::MatrixXd Cup = submatrix(C_, unknown_, prescribed_);
    const Eigen::MatrixXd Hup = submatrix(H_, unknown_, prescribed_);

    const Eigen::VectorXd Tu_old = subvector(T_old, unknown_);
    const Eigen::VectorXd Tp_old = subvector(T_old, prescribed_);
    const Eigen::VectorXd Tp_new = subvector(T_new, prescribed_);

    if (std::abs(cached_dt_s_ - dt_s) > 1.0e-12) {
        cached_factor_.compute(Cuu + dt_s * beta * Huu);
        cached_dt_s_ = dt_s;
    }

    const Eigen::VectorXd rhs =
        (Cuu - dt_s * (1.0 - beta) * Huu) * Tu_old
        - Cup * (Tp_new - Tp_old)
        - dt_s * Hup * ((1.0 - beta) * Tp_old + beta * Tp_new);

    const Eigen::VectorXd Tu_new = cached_factor_.solve(rhs);
    if (!Tu_new.allFinite())
        throw std::runtime_error("Conduction2DField: thermal solve failed");
    scatter(T_new, unknown_, Tu_new);
    apply_prescribed_temperatures(T_new);

    const Eigen::VectorXd T_theta = (1.0 - beta) * T_old + beta * T_new;
    const Eigen::VectorXd T_dot = (T_new - T_old) / dt_s;
    const Eigen::VectorXd residual = C_ * T_dot + H_ * T_theta;
    double boundary_heat_rate = 0.0;
    for (int id : prescribed_)
        boundary_heat_rate += residual[id];
    last_boundary_heat_J_ = boundary_heat_rate * dt_s;

    T_ = std::move(T_new);
}

double Conduction2DField::temperature_at(const Eigen::Vector2d& x, double t) const {
    advance_to(t);
    return interpolate_temperature(x);
}

double Conduction2DField::interpolate_temperature(const Eigen::Vector2d& x) const {
    const int nne = element_.n_nodes();
    double best_dist2 = std::numeric_limits<double>::infinity();
    double nearest_T = T_[0];

    for (int n = 0; n < mesh_.n_nodes; ++n) {
        const double dr = mesh_.nodes[n].r - x[0];
        const double dz = mesh_.nodes[n].z - x[1];
        const double dist2 = dr * dr + dz * dz;
        if (dist2 < best_dist2) {
            best_dist2 = dist2;
            nearest_T = T_[n];
        }
    }

    for (int e = 0; e < mesh_.n_elements; ++e) {
        std::vector<Node> coords(nne);
        double r_min = std::numeric_limits<double>::infinity();
        double r_max = -std::numeric_limits<double>::infinity();
        double z_min = std::numeric_limits<double>::infinity();
        double z_max = -std::numeric_limits<double>::infinity();
        for (int i = 0; i < nne; ++i) {
            coords[i] = mesh_.nodes[mesh_.elem_nodes[nne * e + i]];
            r_min = std::min(r_min, coords[i].r);
            r_max = std::max(r_max, coords[i].r);
            z_min = std::min(z_min, coords[i].z);
            z_max = std::max(z_max, coords[i].z);
        }
        const double tol = 1.0e-12;
        if (x[0] < r_min - tol || x[0] > r_max + tol ||
            x[1] < z_min - tol || x[1] > z_max + tol)
            continue;

        double xi = 0.0;
        double eta = 0.0;
        if (!local_coordinates(element_, coords, x, xi, eta))
            continue;
        const GaussPoint gp{xi, eta, 1.0};
        std::vector<double> N(nne);
        element_.shape_functions(gp, coords, N);
        double T = 0.0;
        for (int i = 0; i < nne; ++i)
            T += N[i] * T_[mesh_.elem_nodes[nne * e + i]];
        return T;
    }
    return nearest_T;
}

double Conduction2DField::total_energy_J() const {
    return Eigen::VectorXd::Ones(mesh_.n_nodes).dot(C_ * T_);
}
