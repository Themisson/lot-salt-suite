#pragma once

#include "ConstitutiveModel.hpp"
#include "double_mechanism.hpp"
#include "elastic_isotropic.hpp"
#include "io/CaseParser.hpp"

// Wang 2004-style Continuum Damage Mechanics (CDM) tertiary creep.
//
// The implementation follows the reduced contract adopted for Etapa 8a:
//   eps_dot = eps_dot_DM / (1-D)^n_d
//   dD/dt   = A_d * sigma_ef^m_d / (1-D)^p_d
// with sigma_ef as von Mises equivalent stress and scalar D clamped to D_max.
class Wang2004 : public ConstitutiveModel {
public:
    Wang2004(const DMParams& dm,
             const Wang2004Params& params,
             double E_Pa,
             double nu);

    ViscousResult evaluate(const Stress& sigma,
                           const InternalState& state,
                           double T,
                           double dt) const override;

    Eigen::Matrix4d D_elastic() const override;
    Eigen::Matrix4d tangent(const Stress& sigma,
                            const InternalState& state,
                            double T) const override;

    double effective_stress(const Stress& sigma) const;
    double damage_rate(const Stress& sigma, double damage_D) const;

private:
    Wang2004Params params_;
    DoubleMechanism dm_model_;

    double clamp_damage(double D) const;
    double integrate_damage(double D_old, double sigma_ef, double dt) const;
};
