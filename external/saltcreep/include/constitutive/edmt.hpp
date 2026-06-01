#pragma once
#include "ConstitutiveModel.hpp"
#include "elastic_isotropic.hpp"
#include "io/CaseParser.hpp"  // provides EdmtParams (K1, K2)

// EDMT — Empirical Double Mechanism with Transient (primary + secondary creep).
// Reference: Costa & Poiate Jr. (2009).
//
// Scalar viscous rate:
//   ε̇_total = ε̇_DM · (1 + K₁ · exp(−K₂ · εv))    [primary + secondary]
//   ε̇_DM   = e0 · (σ_ef/σ₀)^n · exp[Q/R·(1/T₀ − 1/T)]
//
// Hardening state variable εv (accumulated effective viscous strain, InternalState):
//   dεv/dt = |ε̇_total|   [scalar, always non-negative]
//
// Saturation: as εv → ∞,  exp(−K₂ · εv) → 0  →  ε̇_total → ε̇_DM  ✓
// Initial:    εv = 0  →  ε̇_total = (1 + K₁) · ε̇_DM  (transient amplification)
//
// include_secondary=true  → primary + secondary (rate saturates to DM)
// include_secondary=false → primary only (rate decays to 0; warn in main)
//
// Full parameter set is EdmtParams (from CaseParser.hpp):
//   DM part:        e0_s, sig0, T0, n1, n2, Q_over_R
//   Transient part: K1, K2

class EDMT : public ConstitutiveModel {
public:
    // dm:  base DM parameters (secondary creep)
    // edmt: transient (primary) parameters K1, K2
    EDMT(const DMParams& dm, const EdmtParams& edmt,
         double E_Pa, double nu, bool include_secondary);

    ViscousResult   evaluate(const Stress&        sigma,
                             const InternalState& state,
                             double T, double dt) const override;
    Eigen::Matrix4d D_elastic() const override;
    Eigen::Matrix4d tangent(const Stress& sigma,
                            const InternalState& state,
                            double T) const override;

private:
    DMParams         dm_;
    EdmtParams       edmt_;
    ElasticIsotropic elastic_;
    bool             include_secondary_;
};
