#pragma once
#include <vector>
#include <fstream>
#include <filesystem>
#include <memory>
#include <Eigen/Sparse>
#include <Eigen/SparseCholesky>

#include "types.hpp"
#include "elements/Element.hpp"
#include "constitutive/ConstitutiveModel.hpp"
#include "thermal/ThermalField.hpp"
#include "solver/Assembler.hpp"
#include "solver/DamageDiagnostics.hpp"
#include "solver/PerformanceStats.hpp"
#include "solver/StressSampler.hpp"
#include "solver/TimeState.hpp"
#include "io/CaseParser.hpp"
#include "io/VtuWriter.hpp"

// Explicit (Euler forward) time integrator for secondary creep.
//
// Algorithm per step (follows SESTSAL, no internal sub-stepping):
//   1. Evaluate DM rate at all GPs → delta_eps_v = rate * dt
//   2. Assemble incremental pseudo-force f_v + f_th = ∫ Bᵀ D (Δε^v + Δε^th) jw
//   3. Solve  K_factored * delta_u = f_v + f_th  (back-substitution only)
//   4. u_total += delta_u
//   5. eps_v += delta_eps_v
//   6. Recompute sigma = D * (B*u_total - eps_v - eps_th) + sigma_geo
//
// K is factored exactly once in the constructor and reused every step.
class TimeIntegrator {
public:
    // sigma_geo_gp: geostatic stress {-k0*σv, -k0*σv, -σv, 0} per GP
    //   index e * n_gp + g (same ordering as delta_eps_v_gp)
    // fixed_dofs: DOFs pinned to zero (Dirichlet BCs applied to K before factoring).
    //   For well simulations: always pass {mesh.n_nodes-1} to fix the outer wall (u[Re]=0).
    //   The SESTSAL (%SUPPORT) pins the outer wall; without it, the geostatic force at Re
    //   drives a spurious large outward expansion.
    TimeIntegrator(const Mesh&              mesh,
                   const Element&           element,
                   const ConstitutiveModel& model,
                   const ThermalField&      thermal,
                   Eigen::SparseMatrix<double> K,
                   Eigen::VectorXd             f_external,
                   std::vector<Stress>         sigma_geo_gp,
                   std::vector<int>            fixed_dofs = {},
                   PerformanceStats            initial_stats = {},
                   std::shared_ptr<const WallPressureField> wall_pressure = nullptr);

    // Execute one Euler step of size dt_s [s].
    void advance(double dt_s);

    // Run with uniform dt from t=0 to t_end_s, writing every `output_every` steps to CSV.
    void run(double dt_s, double t_end_s, int output_every,
             const std::filesystem::path& out_dir,
             VtuOutputOptions vtu_options = {},
             const DamageTrackingOptions& damage_options = {},
             StressDiagnosticsOptions stress_options = {});

    // Run with variable dt schedule: list of (until_s, dt_s) segments.
    // Switches to the next segment's dt when t passes segment.until_s.
    void run_schedule(const std::vector<TimeSegment>& schedule,
                      double t_end_s, int output_every,
                      const std::filesystem::path& out_dir,
                      VtuOutputOptions vtu_options = {},
                      const DamageTrackingOptions& damage_options = {},
                      StressDiagnosticsOptions stress_options = {});

    // Wall closure as positive percentage: -u_total[0] / Ri * 100
    double wall_closure_pct() const;
    double wall_displacement_m() const { return state_.u_total[0]; }

    const TimeState& state() const { return state_; }
    const PerformanceStats& performance_stats() const { return stats_; }

private:
    const Mesh&              mesh_;
    const Element&           element_;
    const ConstitutiveModel& model_;
    const ThermalField&      thermal_;

    Eigen::SimplicialLDLT<Eigen::SparseMatrix<double>> ldlt_;
    Eigen::VectorXd      f_external_;
    std::shared_ptr<const WallPressureField> wall_pressure_;
    std::vector<Stress>  sigma_geo_gp_;
    std::vector<int>     fixed_dofs_;
    PerformanceStats     stats_;

    // Apply Dirichlet BCs: zero row/col, diagonal=1, RHS=0.
    static void apply_dirichlet(Eigen::SparseMatrix<double>& K, Eigen::VectorXd& f,
                                 const std::vector<int>& dofs);

    TimeState state_;
    int       n_gp_;   // gauss points per element
    double    current_time_s_ = 0.0;

    // Recompute sigma at all GPs from u_total, eps_v
    void update_stresses();
    Eigen::VectorXd pressure_load_at(double time_s) const;

    // Compute r-coordinate of GP (e, g)
    double gauss_r(int e, int g) const;
    Eigen::Vector2d gauss_position(int e, int g) const;
    Strain thermal_strain_at(int e, int g, double time_s) const;
};
