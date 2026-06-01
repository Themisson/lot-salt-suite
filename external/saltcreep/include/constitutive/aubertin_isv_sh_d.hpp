#pragma once

#include "ConstitutiveModel.hpp"
#include "elastic_isotropic.hpp"
#include "io/CaseParser.hpp"

// Aubertin/Firme-style unified ISV_SH_D model.
//
// Operational Etapa 8b form:
//   eps_dot = e0 * (sigma_ef/sigma0)^n * exp((Q/R)*(1/T0 - 1/T))
//             * (1 + K1*exp(-K2*eps_v_primary)) / (1-D)^n_d
//   dD/dt   = A_d * sigma_ef^m_d * (1-D)^p_d * g(eps_v)
//
// The primary and secondary ISV accumulators are stored separately in
// InternalState; eps_v_eff is kept synchronized with their sum for generic
// diagnostics.
class AubertinISVSHD : public ConstitutiveModel {
public:
    AubertinISVSHD(const AubertinISVSHDParams& params,
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
    double scalar_rate(double sigma_ef, double T,
                       double eps_v_primary, double damage_D) const;
    double damage_rate(double sigma_ef, double damage_D, double eps_v_total) const;

private:
    AubertinISVSHDParams params_;
    ElasticIsotropic elastic_;

    double clamp_damage(double D) const;
};
