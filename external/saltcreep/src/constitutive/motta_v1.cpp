#include "constitutive/motta_v1.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <utility>

namespace {
double clamp_damage(double D, double D_max) {
    return std::clamp(D, 0.0, D_max);
}
} // namespace

MottaV1::MottaV1(const DMParams& dm,
                 const MottaV1Params& motta,
                 const SpierParams& spier,
                 double E_Pa,
                 double nu)
    : MottaV1(dm, motta, std::make_unique<SpierEnvelope>(spier), E_Pa, nu) {}

MottaV1::MottaV1(const DMParams& dm,
                 const MottaV1Params& motta,
                 std::unique_ptr<DilatancyEnvelope> envelope,
                 double E_Pa,
                 double nu)
    : dm_params_(dm)
    , motta_(motta)
    , dilatancy_(std::move(envelope))
    , dm_model_(dm, E_Pa, nu) {
    if (motta_.D_max <= 0.0 || motta_.D_max >= 1.0)
        throw std::invalid_argument("MottaV1: D_max must be in (0,1)");
    if (motta_.n_d < 0.0 || motta_.A_d < 0.0 || motta_.m_d < 0.0 || motta_.p_d < 0.0)
        throw std::invalid_argument("MottaV1: damage parameters must be non-negative");
    if (!dilatancy_)
        throw std::invalid_argument("MottaV1: dilatancy envelope must not be null");
}

Eigen::Matrix4d MottaV1::D_elastic() const {
    return dm_model_.D_elastic();
}

double MottaV1::dilatancy_value(const Stress& sigma) const {
    return dilatancy_->evaluate(sigma);
}

double MottaV1::damage_rate(const Stress& sigma, double damage_D) const {
    const double f_dil = dilatancy_value(sigma);
    if (f_dil <= 0.0)
        return 0.0;
    const double D = clamp_damage(damage_D, motta_.D_max);
    const double denom = std::pow(std::max(1.0 - D, 1.0e-12), motta_.p_d);
    return motta_.A_d * std::pow(f_dil, motta_.m_d) / denom;
}

ViscousResult MottaV1::evaluate(const Stress& sigma,
                                const InternalState& state,
                                double T,
                                double dt) const {
    auto dm_result = dm_model_.evaluate(sigma, state, T, dt);
    const double D = clamp_damage(state.damage_D, motta_.D_max);
    const double multiplier =
        1.0 / std::pow(std::max(1.0 - D, 1.0e-12), motta_.n_d);

    InternalState updated = dm_result.updated_state;
    updated.damage_D = D;
    if (dt > 0.0) {
        const double dD = damage_rate(sigma, D) * dt;
        updated.damage_D = clamp_damage(D + dD, motta_.D_max);
    }

    return {dm_result.strain_rate_voigt * multiplier, updated};
}

Eigen::Matrix4d MottaV1::tangent(const Stress& sigma,
                                  const InternalState& state,
                                  double T) const {
    const double D = clamp_damage(state.damage_D, motta_.D_max);
    const double multiplier =
        1.0 / std::pow(std::max(1.0 - D, 1.0e-12), motta_.n_d);
    return multiplier * dm_model_.tangent(sigma, state, T);
}
