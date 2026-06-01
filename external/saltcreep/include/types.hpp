#pragma once
#include <Eigen/Core>
#include <Eigen/Sparse>

// Voigt order for axisymmetric problems: {εr=0, εθ=1, εz=2, εrz=3}
// i.e. {σrr, σθθ, σzz, σrz}
// NOTE: legacy Matlab (fMatrizB.m) uses {εr, εz, γrz, εθ} — opposite convention.
// The new project adopts CLAUDE.md order throughout.

struct GaussPoint {
    double xi;
    double weight;
    double eta = 0.0;
};

struct Node {
    double r = 0.0;
    double z = 0.0;
};

// 4-component Voigt stress/strain vector: {σrr, σθθ, σzz, σrz}
using Stress  = Eigen::Vector4d;
using Strain  = Eigen::Vector4d;

// State internal variables.
// Etapa 0-1 (DM secondary only): all zero — DM has no memory.
// Etapa 2 (EDMT primary + secondary): eps_v_eff tracks accumulated effective
//   viscous strain used by the transient decay  exp(-K₂ · εv).
struct InternalState {
    double eps_v_eff = 0.0;  // accumulated effective viscous strain [dimensionless]
    double damage_D = 0.0;   // scalar damage for tertiary creep, clamped to [0, D_max)
    double eps_v_primary = 0.0;    // ISV primary viscous strain accumulator
    double eps_v_secondary = 0.0;  // ISV secondary viscous strain accumulator
    double f_hard = 1.0;           // ISV hardening multiplier, derived diagnostic
};

struct ViscousResult {
    Strain       strain_rate_voigt;  // ε̇^v in Voigt notation
    InternalState updated_state;
};
