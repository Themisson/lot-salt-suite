#include "constitutive/isv_sh_dm.hpp"

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

ISVSHDMunson::ISVSHDMunson(const DMParams& dm,
                           const ISVSHDMunsonParams& params,
                           double E_Pa,
                           double nu,
                           bool include_secondary)
    : dm_(dm)
    , params_(params)
    , elastic_(E_Pa, nu)
    , dm_model_(dm, E_Pa, nu)
    , include_secondary_(include_secondary) {
    if (params_.e0_s < 0.0 || params_.sig_ref <= 0.0 || params_.n < 0.0 ||
        params_.Q_J_mol < 0.0 || params_.T0 <= 0.0 || params_.K_h <= 0.0)
        throw std::invalid_argument("ISVSHDMunson: invalid non-positive parameter");
}

Eigen::Matrix4d ISVSHDMunson::D_elastic() const {
    return elastic_.D_elastic();
}

double ISVSHDMunson::effective_stress(const Stress& sigma) const {
    const double p = (sigma[0] + sigma[1] + sigma[2]) / 3.0;
    Stress s = sigma;
    s[0] -= p;
    s[1] -= p;
    s[2] -= p;
    const double ss = s[0]*s[0] + s[1]*s[1] + s[2]*s[2] + 2.0*s[3]*s[3];
    return std::sqrt(std::max(0.0, 1.5 * ss));
}

double ISVSHDMunson::hardening(double eps_v_primary) const {
    const double eps = std::max(0.0, eps_v_primary);
    return 1.0 / std::sinh(std::asinh(1.0) + params_.K_h * eps);
}

double ISVSHDMunson::dm_scalar_rate(double sigma_ef, double T) const {
    if (sigma_ef < 1.0)
        return 0.0;
    const double n = (sigma_ef <= dm_.sig0) ? dm_.n1 : dm_.n2;
    return dm_.e0_s * std::pow(sigma_ef / dm_.sig0, n) *
           std::exp(dm_.Q_over_R * (1.0 / dm_.T0 - 1.0 / T));
}

double ISVSHDMunson::primary_scalar_rate(double sigma_ef, double T,
                                         double eps_v_primary) const {
    if (sigma_ef < 1.0)
        return 0.0;
    const double x = sigma_ef / params_.sig_ref;
    const double sh = std::sinh(x);
    const double arrhenius =
        std::exp((params_.Q_J_mol / R_gas) * (1.0 / params_.T0 - 1.0 / T));
    return params_.e0_s * std::pow(sh, params_.n) * arrhenius *
           hardening(eps_v_primary);
}

ViscousResult ISVSHDMunson::evaluate(const Stress& sigma,
                                     const InternalState& state,
                                     double T,
                                     double dt) const {
    const Eigen::Matrix4d P = deviatoric_projector();
    const Stress s = P * sigma;
    const double sigma_ef = effective_stress(sigma);
    if (sigma_ef < 1.0)
        return {Strain::Zero(), state};

    const double eps_p = std::max(0.0, state.eps_v_primary);
    const double primary = primary_scalar_rate(sigma_ef, T, eps_p);
    const double secondary = include_secondary_ ? dm_scalar_rate(sigma_ef, T) : 0.0;
    const double total = primary + secondary;

    Strain rate = std::sqrt(1.5) * (total / sigma_ef) * s;

    InternalState updated = state;
    updated.eps_v_primary = eps_p + std::abs(primary) * std::max(0.0, dt);
    if (include_secondary_)
        updated.eps_v_secondary = std::max(0.0, state.eps_v_secondary) +
                                  std::abs(secondary) * std::max(0.0, dt);
    updated.eps_v_eff = updated.eps_v_primary + updated.eps_v_secondary;
    updated.f_hard = hardening(updated.eps_v_primary);
    return {rate, updated};
}

Eigen::Matrix4d ISVSHDMunson::primary_tangent(const Stress& sigma,
                                              const InternalState& state,
                                              double T) const {
    const Eigen::Matrix4d P = deviatoric_projector();
    const Eigen::Matrix4d M = voigt_metric();
    const Stress s = P * sigma;
    const double ss = s.transpose() * M * s;
    const double sigma_ef = std::sqrt(std::max(0.0, 1.5 * ss));
    if (sigma_ef < 1.0)
        return Eigen::Matrix4d::Zero();

    const double x = sigma_ef / params_.sig_ref;
    const double sh = std::sinh(x);
    if (std::abs(sh) < 1.0e-30)
        return Eigen::Matrix4d::Zero();

    const double arrhenius =
        std::exp((params_.Q_J_mol / R_gas) * (1.0 / params_.T0 - 1.0 / T));
    const double h = hardening(state.eps_v_primary);
    const double edot = params_.e0_s * std::pow(sh, params_.n) * arrhenius * h;
    const double dedot_dsigma =
        params_.e0_s * arrhenius * h * params_.n *
        std::pow(sh, params_.n - 1.0) * std::cosh(x) / params_.sig_ref;

    const Eigen::RowVector4d d_sigma_ef =
        ((1.5 / sigma_ef) * (P.transpose() * M * s)).transpose();
    const double A = std::sqrt(1.5) * edot / sigma_ef;
    const double dA_dsigma_ef =
        std::sqrt(1.5) * (dedot_dsigma * sigma_ef - edot) /
        (sigma_ef * sigma_ef);

    return A * P + dA_dsigma_ef * (s * d_sigma_ef);
}

Eigen::Matrix4d ISVSHDMunson::tangent(const Stress& sigma,
                                      const InternalState& state,
                                      double T) const {
    Eigen::Matrix4d J = primary_tangent(sigma, state, T);
    if (include_secondary_)
        J += dm_model_.tangent(sigma, state, T);
    return J;
}
