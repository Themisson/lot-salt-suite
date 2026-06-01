#include "constitutive/wang_2004.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

Wang2004::Wang2004(const DMParams& dm,
                   const Wang2004Params& params,
                   double E_Pa,
                   double nu)
    : params_(params)
    , dm_model_(dm, E_Pa, nu) {
    if (params_.D_max <= 0.0 || params_.D_max >= 1.0)
        throw std::invalid_argument("Wang2004: D_max must be in (0,1)");
    if (params_.n_d < 0.0 || params_.A_d < 0.0 ||
        params_.m_d < 0.0 || params_.p_d < 0.0)
        throw std::invalid_argument("Wang2004: damage parameters must be non-negative");
}

Eigen::Matrix4d Wang2004::D_elastic() const {
    return dm_model_.D_elastic();
}

double Wang2004::clamp_damage(double D) const {
    return std::clamp(D, 0.0, params_.D_max);
}

double Wang2004::effective_stress(const Stress& sigma) const {
    const double p = (sigma[0] + sigma[1] + sigma[2]) / 3.0;
    Stress s = sigma;
    s[0] -= p;
    s[1] -= p;
    s[2] -= p;
    const double ss = s[0]*s[0] + s[1]*s[1] + s[2]*s[2] + 2.0*s[3]*s[3];
    return std::sqrt(std::max(0.0, 1.5 * ss));
}

double Wang2004::damage_rate(const Stress& sigma, double damage_D) const {
    const double sigma_ef = effective_stress(sigma);
    if (sigma_ef < 1.0 || params_.A_d == 0.0)
        return 0.0;
    const double D = clamp_damage(damage_D);
    const double denom = std::pow(std::max(1.0 - D, 1.0e-12), params_.p_d);
    return params_.A_d * std::pow(sigma_ef, params_.m_d) / denom;
}

double Wang2004::integrate_damage(double D_old, double sigma_ef, double dt) const {
    const double D0 = clamp_damage(D_old);
    if (dt <= 0.0 || sigma_ef < 1.0 || params_.A_d == 0.0)
        return D0;

    const double source = dt * params_.A_d * std::pow(sigma_ef, params_.m_d);
    if (source <= 0.0)
        return D0;

    auto residual = [&](double D) {
        const double denom = std::pow(std::max(1.0 - D, 1.0e-12), params_.p_d);
        return D - D0 - source / denom;
    };

    const double hi = params_.D_max;
    if (residual(hi) <= 0.0)
        return hi;

    double lo = D0;
    double upper = hi;
    for (int iter = 0; iter < 80; ++iter) {
        const double mid = 0.5 * (lo + upper);
        if (residual(mid) <= 0.0)
            lo = mid;
        else
            upper = mid;
    }
    return clamp_damage(0.5 * (lo + upper));
}

ViscousResult Wang2004::evaluate(const Stress& sigma,
                                 const InternalState& state,
                                 double T,
                                 double dt) const {
    const double D_old = clamp_damage(state.damage_D);
    const double sigma_ef = effective_stress(sigma);
    const double D_new = integrate_damage(D_old, sigma_ef, dt);

    auto dm_result = dm_model_.evaluate(sigma, state, T, dt);
    const double multiplier =
        1.0 / std::pow(std::max(1.0 - D_new, 1.0e-12), params_.n_d);

    InternalState updated = dm_result.updated_state;
    updated.damage_D = D_new;
    return {dm_result.strain_rate_voigt * multiplier, updated};
}

Eigen::Matrix4d Wang2004::tangent(const Stress& sigma,
                                  const InternalState& state,
                                  double T) const {
    const double D = clamp_damage(state.damage_D);
    const double multiplier =
        1.0 / std::pow(std::max(1.0 - D, 1.0e-12), params_.n_d);
    return multiplier * dm_model_.tangent(sigma, state, T);
}
