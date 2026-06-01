#pragma once
#include "ConstitutiveModel.hpp"
#include "elastic_isotropic.hpp"
#include "io/CaseParser.hpp"

// Double-Mechanism creep law (Costa & Poiate, 2008).
// Secondary (steady-state) creep only — no internal state variables.
//
// Rate:  ε̇^v = e0 * (σ_ef/σ₀)^n * exp[Q/R*(1/T₀ − 1/T)]
//   n = n1 if σ_ef ≤ σ₀ (dislocation glide)
//   n = n2 if σ_ef  > σ₀ (dislocation climb)
//
// Direction: ε̇^v_ij = √(3/2) * ε̇^v * s_ij / σ_ef
//   s = deviatoric stress (zero trace); zero volumetric rate implicit.
//
// Voigt order: {σrr=0, σθθ=1, σzz=2, σrz=3}  — project standard (Etapa 0).
class DoubleMechanism : public ConstitutiveModel {
public:
    DoubleMechanism(const DMParams& dm, double E_Pa, double nu);

    ViscousResult   evaluate(const Stress&        sigma,
                             const InternalState& state,
                             double T, double dt) const override;

    Eigen::Matrix4d D_elastic() const override;
    Eigen::Matrix4d tangent(const Stress& sigma,
                            const InternalState& state,
                            double T) const override;

private:
    DMParams         params_;
    ElasticIsotropic elastic_;
};
