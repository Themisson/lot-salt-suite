#include "constitutive/double_mechanism.hpp"
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
} // namespace

DoubleMechanism::DoubleMechanism(const DMParams& dm, double E_Pa, double nu)
    : params_(dm), elastic_(E_Pa, nu) {}

Eigen::Matrix4d DoubleMechanism::D_elastic() const {
    return elastic_.D_elastic();
}

// Voigt order: {σrr=0, σθθ=1, σzz=2, σrz=3}
//
// Deviatoric stress:
//   p = (σrr + σθθ + σzz) / 3
//   s = {σrr−p, σθθ−p, σzz−p, σrz}  (σrz is shear; no mean pressure on off-diag)
//
// Von Mises:
//   s:s = s₀² + s₁² + s₂² + 2·s₃²   (Voigt factor 2 for shear — correct for tensor contraction)
//   σ_ef = √(3/2 · s:s)
//
// Rate:
//   ε̇^v_ij = √(3/2) · ε̇^v · s_ij / σ_ef
ViscousResult DoubleMechanism::evaluate(const Stress&        sigma,
                                         const InternalState& state,
                                         double T, double) const {
    // deviatoric stress
    double p  = (sigma[0] + sigma[1] + sigma[2]) / 3.0;
    Stress s  = sigma;
    s[0] -= p;  s[1] -= p;  s[2] -= p;
    // s[3] = σrz unchanged (shear deviatoric = shear total for off-diagonal)

    // von Mises effective stress
    double ss      = s[0]*s[0] + s[1]*s[1] + s[2]*s[2] + 2.0*s[3]*s[3];
    double sigma_ef = std::sqrt(1.5 * ss);

    // guard: no creep when stress is negligible (pre-drilling geostatic state)
    if (sigma_ef < 1.0)
        return {Strain::Zero(), state};

    // exponent selection
    double n = (sigma_ef <= params_.sig0) ? params_.n1 : params_.n2;

    // DM scalar rate  [1/s]
    double edot = params_.e0_s
                * std::pow(sigma_ef / params_.sig0, n)
                * std::exp(params_.Q_over_R * (1.0/params_.T0 - 1.0/T));

    // viscous strain rate tensor (Voigt)
    // rate_i = √(3/2) * edot * s_i / σ_ef
    double factor = std::sqrt(1.5) * edot / sigma_ef;
    Strain rate   = factor * s;

    return {rate, state};
}

Eigen::Matrix4d DoubleMechanism::tangent(const Stress& sigma,
                                          const InternalState&,
                                          double T) const {
    const Eigen::Matrix4d P = deviatoric_projector();
    const Eigen::Matrix4d M = voigt_metric();
    const Stress s = P * sigma;
    const double ss = s.transpose() * M * s;
    const double sigma_ef = std::sqrt(1.5 * ss);
    if (sigma_ef < 1.0)
        return Eigen::Matrix4d::Zero();

    const double n = (sigma_ef <= params_.sig0) ? params_.n1 : params_.n2;
    const double arrhenius =
        std::exp(params_.Q_over_R * (1.0/params_.T0 - 1.0/T));
    const double coeff =
        std::sqrt(1.5) * params_.e0_s * arrhenius / std::pow(params_.sig0, n);

    const Eigen::RowVector4d d_sigma_ef =
        ((1.5 / sigma_ef) * (P.transpose() * M * s)).transpose();

    Eigen::Matrix4d J =
        coeff * std::pow(sigma_ef, n - 1.0) * P;
    J += coeff * (n - 1.0) * std::pow(sigma_ef, n - 2.0) *
         (s * d_sigma_ef);
    return J;
}
