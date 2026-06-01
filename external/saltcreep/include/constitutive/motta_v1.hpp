#pragma once
#include "ConstitutiveModel.hpp"
#include "dilatancy_envelope.hpp"
#include "double_mechanism.hpp"
#include "elastic_isotropic.hpp"
#include "io/CaseParser.hpp"

// Motta v1 tertiary creep with scalar Kachanov damage and a pluggable
// dilatancy envelope.
//
// Project stress convention verified in Etapa 4b:
//   compression is negative in code stresses (tension-positive mechanics).
// Therefore confinement-dependent envelopes use I1_comp = -I1:
//   f_dil = sqrt(J2) - a*I1_comp - b = sqrt(J2) + a*I1 - b.
// This keeps hydrostatic compression safe (f_dil <= 0).
class MottaV1 : public ConstitutiveModel {
public:
    MottaV1(const DMParams& dm,
            const MottaV1Params& motta,
            const SpierParams& spier,
            double E_Pa,
            double nu);
    MottaV1(const DMParams& dm,
            const MottaV1Params& motta,
            std::unique_ptr<DilatancyEnvelope> envelope,
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

    double dilatancy_value(const Stress& sigma) const;
    double damage_rate(const Stress& sigma, double damage_D) const;

private:
    DMParams dm_params_;
    MottaV1Params motta_;
    std::unique_ptr<DilatancyEnvelope> dilatancy_;
    DoubleMechanism dm_model_;
};
