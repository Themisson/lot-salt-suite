#include "constitutive/edmt.hpp"
#include <cmath>

namespace {
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

Eigen::Matrix4d dm_tangent(const DMParams& dm, const Stress& sigma, double T) {
    const Eigen::Matrix4d P = deviatoric_projector();
    const Eigen::Matrix4d M = voigt_metric();
    const Stress s = P * sigma;
    const double ss = s.transpose() * M * s;
    const double sigma_ef = std::sqrt(1.5 * ss);
    if (sigma_ef < 1.0)
        return Eigen::Matrix4d::Zero();

    const double n = (sigma_ef <= dm.sig0) ? dm.n1 : dm.n2;
    const double arrhenius =
        std::exp(dm.Q_over_R * (1.0/dm.T0 - 1.0/T));
    const double coeff =
        std::sqrt(1.5) * dm.e0_s * arrhenius / std::pow(dm.sig0, n);

    const Eigen::RowVector4d d_sigma_ef =
        ((1.5 / sigma_ef) * (P.transpose() * M * s)).transpose();

    Eigen::Matrix4d J = coeff * std::pow(sigma_ef, n - 1.0) * P;
    J += coeff * (n - 1.0) * std::pow(sigma_ef, n - 2.0) *
         (s * d_sigma_ef);
    return J;
}
} // namespace

EDMT::EDMT(const DMParams& dm, const EdmtParams& edmt,
           double E_Pa, double nu, bool include_secondary)
    : dm_(dm), edmt_(edmt), elastic_(E_Pa, nu), include_secondary_(include_secondary) {}

Eigen::Matrix4d EDMT::D_elastic() const { return elastic_.D_elastic(); }

// Voigt order: {σrr=0, σθθ=1, σzz=2, σrz=3}
ViscousResult EDMT::evaluate(const Stress&        sigma,
                              const InternalState& state,
                              double T, double dt) const {
    // Deviatoric stress
    double p = (sigma[0] + sigma[1] + sigma[2]) / 3.0;
    Stress s = sigma;
    s[0] -= p;  s[1] -= p;  s[2] -= p;

    // Von Mises effective stress
    double ss       = s[0]*s[0] + s[1]*s[1] + s[2]*s[2] + 2.0*s[3]*s[3];
    double sigma_ef = std::sqrt(1.5 * ss);

    if (sigma_ef < 1.0)
        return {Strain::Zero(), state};

    // DM scalar rate [1/s]
    double n       = (sigma_ef <= dm_.sig0) ? dm_.n1 : dm_.n2;
    double edot_DM = dm_.e0_s
                   * std::pow(sigma_ef / dm_.sig0, n)
                   * std::exp(dm_.Q_over_R * (1.0/dm_.T0 - 1.0/T));

    // Transient multiplier from hardening variable εv (InternalState::eps_v_eff)
    double transient = edmt_.K1 * std::exp(-edmt_.K2 * state.eps_v_eff);

    double edot_total = include_secondary_ ? edot_DM * (1.0 + transient)  // primary + secondary
                                           : edot_DM * transient;           // primary only

    // Directional decomposition: ε̇^v_ij = √(3/2) * edot * s_ij / σ_ef
    Strain rate = std::sqrt(1.5) * (edot_total / sigma_ef) * s;

    // Update hardening variable: dεv/dt = |edot_total|
    InternalState new_state = state;
    new_state.eps_v_eff += std::abs(edot_total) * dt;

    return {rate, new_state};
}

Eigen::Matrix4d EDMT::tangent(const Stress& sigma,
                               const InternalState& state,
                               double T) const {
    const double transient = edmt_.K1 * std::exp(-edmt_.K2 * state.eps_v_eff);
    const double multiplier = include_secondary_ ? (1.0 + transient) : transient;
    return multiplier * dm_tangent(dm_, sigma, T);
}
