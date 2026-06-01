#pragma once
#include <algorithm>
#include <cmath>
#include <Eigen/Core>
#include "types.hpp"

class ConstitutiveModel {
public:
    virtual ~ConstitutiveModel() = default;

    // Viscous strain rate at a material point. Returns zero in elastic stub.
    // sigma: current Voigt stress {σrr, σθθ, σzz, σrz}
    // state: current internal state
    // T: temperature at this point (K), from ThermalField
    // dt: time increment (s)
    virtual ViscousResult evaluate(const Stress&        sigma,
                                   const InternalState& state,
                                   double T, double dt) const = 0;

    // Elastic constitutive matrix D, 4×4, Voigt order {εr, εθ, εz, εrz}.
    // Constant (does not depend on T under weak coupling assumption).
    virtual Eigen::Matrix4d D_elastic() const = 0;

    // Tangent of viscous strain rate with respect to stress:
    // d(eps_dot_v) / d(sigma), both in project Voigt order.
    // The default central finite-difference implementation is intentionally
    // conservative; constitutive models used by the implicit integrator should
    // override it analytically when possible.
    virtual Eigen::Matrix4d tangent(const Stress& sigma,
                                    const InternalState& state,
                                    double T) const {
        Eigen::Matrix4d J = Eigen::Matrix4d::Zero();
        for (int j = 0; j < 4; ++j) {
            const double h = std::max(1.0, std::abs(sigma[j])) * 1.0e-6;
            Stress sp = sigma;
            Stress sm = sigma;
            sp[j] += h;
            sm[j] -= h;
            const Strain rp = evaluate(sp, state, T, 0.0).strain_rate_voigt;
            const Strain rm = evaluate(sm, state, T, 0.0).strain_rate_voigt;
            J.col(j) = (rp - rm) / (2.0 * h);
        }
        return J;
    }
};
