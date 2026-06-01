#include "thermal/conduction_1d_field.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <utility>

#include "elements/axisym_1d_L3.hpp"

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
} // namespace

Conduction1DField::Conduction1DField(const Mesh1D& mesh,
                                     Conduction1DOptions options)
    : mesh_(mesh)
    , options_(std::move(options))
    , T_(Eigen::VectorXd::Constant(mesh.n_nodes, options_.initial_T_K)) {
    if (mesh_.n_nodes < 2 || mesh_.n_elements < 1)
        throw std::invalid_argument("Conduction1DField: empty mesh");
    if (options_.k_W_m_K <= 0.0 || options_.rho_kg_m3 <= 0.0 ||
        options_.cp_J_kg_K <= 0.0)
        throw std::invalid_argument("Conduction1DField: thermal properties must be positive");
    if (options_.dt_thermal_s <= 0.0)
        throw std::invalid_argument("Conduction1DField: dt_thermal_s must be positive");
    if (options_.beta < 0.0 || options_.beta > 1.0)
        throw std::invalid_argument("Conduction1DField: beta must be in [0, 1]");
    if (options_.outer_bc != "prescribed" && options_.outer_bc != "flux_zero")
        throw std::invalid_argument("Conduction1DField: outer_bc must be prescribed or flux_zero");

    if (!options_.initial_nodal_T_K.empty()) {
        if (static_cast<int>(options_.initial_nodal_T_K.size()) != mesh_.n_nodes)
            throw std::invalid_argument("Conduction1DField: initial_nodal_T_K size mismatch");
        for (int i = 0; i < mesh_.n_nodes; ++i)
            T_[i] = options_.initial_nodal_T_K[i];
    }

    setup_boundary_sets();
    apply_prescribed_temperatures(T_);
    T_initial_ = T_;
    assemble_matrices();
}

void Conduction1DField::setup_boundary_sets() {
    prescribed_.clear();
    unknown_.clear();
    prescribed_.push_back(0);
    if (options_.outer_bc == "prescribed")
        prescribed_.push_back(mesh_.n_nodes - 1);

    for (int i = 0; i < mesh_.n_nodes; ++i) {
        const bool is_prescribed =
            std::find(prescribed_.begin(), prescribed_.end(), i) != prescribed_.end();
        if (!is_prescribed)
            unknown_.push_back(i);
    }
}

void Conduction1DField::apply_prescribed_temperatures(Eigen::VectorXd& T) const {
    T[0] = options_.inner_wall_T_K;
    if (options_.outer_bc == "prescribed")
        T[mesh_.n_nodes - 1] = options_.outer_T_K;
}

void Conduction1DField::assemble_matrices() {
    AxisymL3 element;
    C_ = Eigen::MatrixXd::Zero(mesh_.n_nodes, mesh_.n_nodes);
    H_ = Eigen::MatrixXd::Zero(mesh_.n_nodes, mesh_.n_nodes);

    const auto gps = element.gauss_points();
    for (int e = 0; e < mesh_.n_elements; ++e) {
        std::vector<Node> coords(3);
        std::vector<int> nodes(3);
        for (int i = 0; i < 3; ++i) {
            nodes[i] = mesh_.elem_nodes[3 * e + i];
            coords[i] = mesh_.nodes[nodes[i]];
        }

        for (const auto& gp : gps) {
            double N[3];
            double dNdxi[3];
            element.shape_functions(gp.xi, N);
            element.shape_derivatives(gp.xi, dNdxi);

            double J = 0.0;
            double r = 0.0;
            for (int i = 0; i < 3; ++i) {
                J += dNdxi[i] * coords[i].r;
                r += N[i] * coords[i].r;
            }
            if (r <= 0.0 || std::abs(J) < 1.0e-30)
                throw std::domain_error("Conduction1DField: invalid thermal Jacobian");

            const double jw = 2.0 * kPi * r * std::abs(J) * gp.weight;
            for (int i = 0; i < 3; ++i) {
                const double dNi_dr = dNdxi[i] / J;
                for (int j = 0; j < 3; ++j) {
                    const double dNj_dr = dNdxi[j] / J;
                    C_(nodes[i], nodes[j]) +=
                        options_.rho_kg_m3 * options_.cp_J_kg_K * N[i] * N[j] * jw;
                    H_(nodes[i], nodes[j]) +=
                        options_.k_W_m_K * dNi_dr * dNj_dr * jw;
                }
            }
        }
    }
}

void Conduction1DField::advance_to(double t_s) const {
    if (t_s < current_time_s_ - 1.0e-9) {
        T_ = T_initial_;
        current_time_s_ = 0.0;
        last_boundary_heat_J_ = 0.0;
    }

    while (current_time_s_ + 1.0e-12 < t_s) {
        const double dt = std::min(options_.dt_thermal_s, t_s - current_time_s_);
        advance_one_step(dt);
        current_time_s_ += dt;
    }
}

void Conduction1DField::advance_one_step(double dt_s) const {
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

    const Eigen::MatrixXd A = Cuu + dt_s * beta * Huu;
    const Eigen::VectorXd rhs =
        (Cuu - dt_s * (1.0 - beta) * Huu) * Tu_old
        - Cup * (Tp_new - Tp_old)
        - dt_s * Hup * ((1.0 - beta) * Tp_old + beta * Tp_new);

    const Eigen::VectorXd Tu_new = A.ldlt().solve(rhs);
    if (!Tu_new.allFinite())
        throw std::runtime_error("Conduction1DField: thermal solve failed");
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

double Conduction1DField::temperature_at(const Eigen::Vector2d& x, double t) const {
    advance_to(t);
    return interpolate_temperature(x[0]);
}

double Conduction1DField::interpolate_temperature(double r) const {
    const double r_min = mesh_.nodes.front().r;
    const double r_max = mesh_.nodes.back().r;
    if (r <= r_min)
        return T_[0];
    if (r >= r_max)
        return T_[mesh_.n_nodes - 1];

    for (int e = 0; e < mesh_.n_elements; ++e) {
        const int left = mesh_.elem_nodes[3 * e];
        const int mid = mesh_.elem_nodes[3 * e + 1];
        const int right = mesh_.elem_nodes[3 * e + 2];
        const double r_left = mesh_.nodes[left].r;
        const double r_right = mesh_.nodes[right].r;
        if (r >= r_left - 1.0e-14 && r <= r_right + 1.0e-14) {
            const double xi = 2.0 * (r - r_left) / (r_right - r_left) - 1.0;
            const double N1 = 0.5 * xi * (xi - 1.0);
            const double N2 = 1.0 - xi * xi;
            const double N3 = 0.5 * xi * (xi + 1.0);
            return N1 * T_[left] + N2 * T_[mid] + N3 * T_[right];
        }
    }
    return T_[mesh_.n_nodes - 1];
}

double Conduction1DField::total_energy_J() const {
    return Eigen::VectorXd::Ones(mesh_.n_nodes).dot(C_ * T_);
}
