#include "constitutive/aubertin_isv_sh_d.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace {
constexpr double R_gas = 8.314;

Eigen::Matrix4d deviatoric_projector() {
    Eigen::Matrix4d P = Eigen::Matrix4d::Zero();
    P(0,0) =  2.0/3.0; P(0,1) = -1.0/3.0; P(0,2) = -1.0/3.0;
    P(1,0) = -1.0/3.0; P(1,1) =  2.0/3.0; P(1,2) = -1.0/3.0;
    P(2,0) = -1.0/3.0; P(2,1) = -1.0/3.0; P(2,2) =  2.0/3.0;
    P(3,3) = 1.0;
    return P;
}

Eigen::Matrix4d voigt_metric() {
    Eigen::Matrix4d M = Eigen::Matrix4d::Identity();
    M(3,3) = 2.0;
    return M;
}
} // namespace

AubertinISVSHD::AubertinISVSHD(const AubertinISVSHDParams& params,
                               double E_Pa,
                               double nu)
    : params_(params)
    , elastic_(E_Pa, nu) {
    if (params_.e0_s < 0.0 || params_.sig0 <= 0.0 || params_.n < 0.0 ||
        params_.K1 < 0.0 || params_.K2 < 0.0 || params_.A_d < 0.0 ||
        params_.m_d < 0.0 || params_.n_d < 0.0 || params_.p_d < 0.0)
        throw std::invalid_argument("AubertinISVSHD: parameters must be non-negative");
    if (params_.D_max <= 0.0 || params_.D_max >= 1.0)
        throw std::invalid_argument("AubertinISVSHD: D_max must be in (0,1)");
    if (params_.T0 <= 0.0)
        throw std::invalid_argument("AubertinISVSHD: T0 must be positive");
}

Eigen::Matrix4d AubertinISVSHD::D_elastic() const {
    return elastic_.D_elastic();
}

double AubertinISVSHD::clamp_damage(double D) const {
    return std::clamp(D, 0.0, params_.D_max);
}

double AubertinISVSHD::effective_stress(const Stress& sigma) const {
    const double p = (sigma[0] + sigma[1] + sigma[2]) / 3.0;
    Stress s = sigma;
    s[0] -= p;
    s[1] -= p;
    s[2] -= p;
    const double ss = s[0]*s[0] + s[1]*s[1] + s[2]*s[2] + 2.0*s[3]*s[3];
    return std::sqrt(std::max(0.0, 1.5 * ss));
}

double AubertinISVSHD::scalar_rate(double sigma_ef, double T,
                                   double eps_v_primary,
                                   double damage_D) const {
    if (sigma_ef < 1.0)
        return 0.0;
    const double arrhenius =
        std::exp((params_.Q_J_mol / R_gas) * (1.0 / params_.T0 - 1.0 / T));
    const double base = params_.e0_s *
        std::pow(sigma_ef / params_.sig0, params_.n) * arrhenius;
    const double f_primary =
        1.0 + params_.K1 * std::exp(-params_.K2 * std::max(0.0, eps_v_primary));
    const double D = clamp_damage(damage_D);
    const double f_creep =
        1.0 / std::pow(std::max(1.0 - D, 1.0e-12), params_.n_d);
    return base * f_primary * f_creep;
}

double AubertinISVSHD::damage_rate(double sigma_ef, double damage_D,
                                   double eps_v_total) const {
    if (sigma_ef < 1.0 || params_.A_d == 0.0)
        return 0.0;
    const double D = clamp_damage(damage_D);
    const double g = std::max(0.0, eps_v_total);
    if (g == 0.0)
        return 0.0;
    return params_.A_d * std::pow(sigma_ef, params_.m_d) *
           std::pow(std::max(1.0 - D, 0.0), params_.p_d) * g;
}

ViscousResult AubertinISVSHD::evaluate(const Stress& sigma,
                                       const InternalState& state,
                                       double T,
                                       double dt) const {
    const Eigen::Matrix4d P = deviatoric_projector();
    const Stress s = P * sigma;
    const double sigma_ef = effective_stress(sigma);
    if (sigma_ef < 1.0)
        return {Strain::Zero(), state};

    const double eps_p0 = std::max(0.0, state.eps_v_primary);
    const double eps_s0 = std::max(0.0, state.eps_v_secondary);
    const double D0 = clamp_damage(state.damage_D);

    double eps_p = eps_p0;
    double eps_s = eps_s0;
    double D = D0;
    double edot_total = scalar_rate(sigma_ef, T, eps_p, D);

    if (dt > 0.0) {
        for (int iter = 0; iter < 25; ++iter) {
            const double transient =
                params_.K1 * std::exp(-params_.K2 * std::max(0.0, eps_p));
            const double D_safe = clamp_damage(D);
            const double f_creep =
                1.0 / std::pow(std::max(1.0 - D_safe, 1.0e-12), params_.n_d);
            const double base = scalar_rate(sigma_ef, T, eps_p, 0.0) /
                (1.0 + transient);
            const double edot_primary = base * transient * f_creep;
            const double edot_secondary = base * f_creep;

            const double next_eps_p = eps_p0 + dt * std::abs(edot_primary);
            const double next_eps_s = eps_s0 + dt * std::abs(edot_secondary);
            const double eps_total = next_eps_p + next_eps_s;
            const double dD = damage_rate(sigma_ef, D_safe, eps_total);
            const double next_D = clamp_damage(D0 + dt * dD);

            eps_p = 0.5 * eps_p + 0.5 * next_eps_p;
            eps_s = 0.5 * eps_s + 0.5 * next_eps_s;
            D = 0.5 * D + 0.5 * next_D;
        }
        D = clamp_damage(D);
        edot_total = scalar_rate(sigma_ef, T, eps_p, D);
    }

    const double factor = std::sqrt(1.5) * edot_total / sigma_ef;
    Strain rate = factor * s;

    InternalState updated = state;
    updated.eps_v_primary = eps_p;
    updated.eps_v_secondary = eps_s;
    updated.eps_v_eff = eps_p + eps_s;
    updated.damage_D = D;
    return {rate, updated};
}

Eigen::Matrix4d AubertinISVSHD::tangent(const Stress& sigma,
                                        const InternalState& state,
                                        double T) const {
    const Eigen::Matrix4d P = deviatoric_projector();
    const Eigen::Matrix4d M = voigt_metric();
    const Stress s = P * sigma;
    const double ss = s.transpose() * M * s;
    const double sigma_ef = std::sqrt(std::max(0.0, 1.5 * ss));
    if (sigma_ef < 1.0)
        return Eigen::Matrix4d::Zero();

    const double arrhenius =
        std::exp((params_.Q_J_mol / R_gas) * (1.0 / params_.T0 - 1.0 / T));
    const double D = clamp_damage(state.damage_D);
    const double f_primary =
        1.0 + params_.K1 *
        std::exp(-params_.K2 * std::max(0.0, state.eps_v_primary));
    const double f_creep =
        1.0 / std::pow(std::max(1.0 - D, 1.0e-12), params_.n_d);
    const double coeff =
        std::sqrt(1.5) * params_.e0_s * arrhenius * f_primary * f_creep /
        std::pow(params_.sig0, params_.n);

    const Eigen::RowVector4d d_sigma_ef =
        ((1.5 / sigma_ef) * (P.transpose() * M * s)).transpose();

    Eigen::Matrix4d J =
        coeff * std::pow(sigma_ef, params_.n - 1.0) * P;
    if (params_.n > 0.0) {
        J += coeff * (params_.n - 1.0) *
             std::pow(sigma_ef, params_.n - 2.0) * (s * d_sigma_ef);
    }
    return J;
}
