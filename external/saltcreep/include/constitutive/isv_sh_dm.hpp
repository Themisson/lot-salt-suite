#pragma once

#include "ConstitutiveModel.hpp"
#include "double_mechanism.hpp"
#include "elastic_isotropic.hpp"
#include "io/CaseParser.hpp"

// ISV_SH_DM Munson-Dawson-style primary creep.
//
// The model is an alternative to EDMT for the primary transient. With
// include_secondary=true, the total scalar rate is:
//   eps_dot = eps_dot_DM + e0*sinh(sigma_ef/sigma_ref)^n
//             * exp((Q/R)*(1/T0 - 1/T)) * h(eps_v_primary)
// where h is a finite, sinh-based hardening multiplier that starts at one and
// decays monotonically. As eps_v_primary grows, the primary term vanishes and
// the model saturates to DM.
class ISVSHDMunson : public ConstitutiveModel {
public:
    ISVSHDMunson(const DMParams& dm,
                 const ISVSHDMunsonParams& params,
                 double E_Pa,
                 double nu,
                 bool include_secondary);

    ViscousResult evaluate(const Stress& sigma,
                           const InternalState& state,
                           double T,
                           double dt) const override;

    Eigen::Matrix4d D_elastic() const override;
    Eigen::Matrix4d tangent(const Stress& sigma,
                            const InternalState& state,
                            double T) const override;

    double effective_stress(const Stress& sigma) const;
    double hardening(double eps_v_primary) const;
    double primary_scalar_rate(double sigma_ef, double T, double eps_v_primary) const;

private:
    DMParams dm_;
    ISVSHDMunsonParams params_;
    ElasticIsotropic elastic_;
    DoubleMechanism dm_model_;
    bool include_secondary_;

    double dm_scalar_rate(double sigma_ef, double T) const;
    Eigen::Matrix4d primary_tangent(const Stress& sigma,
                                    const InternalState& state,
                                    double T) const;
};
