#pragma once
#include <filesystem>
#include <memory>
#include <vector>
#include <Eigen/Sparse>
#include <Eigen/SparseCholesky>

#include "constitutive/ConstitutiveModel.hpp"
#include "elements/Element.hpp"
#include "io/CaseParser.hpp"
#include "io/VtuWriter.hpp"
#include "solver/Assembler.hpp"
#include "solver/DamageDiagnostics.hpp"
#include "solver/PerformanceStats.hpp"
#include "solver/TimeState.hpp"
#include "thermal/ThermalField.hpp"

struct ImplicitAdaptiveOptions {
    double tol_local = 1.0e-10;
    double tol_global = 1.0e-4;
    double dt_min_s = 1.0e-12 * 3600.0;
    double dt_max_s = 10.0 * 3600.0;
    int max_newton_iters = 25;
};

// Backward-Euler creep integrator with local Newton iterations and adaptive
// step control. K remains elastic, constant, and factored once in the
// constructor; all nonlinearity stays in the pseudo-force right-hand side.
class ImplicitAdaptiveIntegrator {
public:
    ImplicitAdaptiveIntegrator(const Mesh& mesh,
                               const Element& element,
                               const ConstitutiveModel& model,
                               const ThermalField& thermal,
                               Eigen::SparseMatrix<double> K,
                               Eigen::VectorXd f_external,
                               std::vector<Stress> sigma_geo_gp,
                               std::vector<int> fixed_dofs = {},
                               ImplicitAdaptiveOptions options = {},
                               PerformanceStats initial_stats = {},
                               std::shared_ptr<const WallPressureField> wall_pressure = nullptr);

    // Try an adaptive step with initial size dt_s. Returns the accepted size.
    double advance(double dt_s);

    void run(double dt_s, double t_end_s, int output_every,
             const std::filesystem::path& out_dir,
             VtuOutputOptions vtu_options = {},
             const DamageTrackingOptions& damage_options = {});

    void run_schedule(const std::vector<TimeSegment>& schedule,
                      double t_end_s, int output_every,
                      const std::filesystem::path& out_dir,
                      VtuOutputOptions vtu_options = {},
                      const DamageTrackingOptions& damage_options = {});

    double wall_closure_pct() const;
    double wall_displacement_m() const { return state_.u_total[0]; }
    double last_error() const { return last_error_; }
    double suggested_dt_s() const { return suggested_dt_s_; }

    const TimeState& state() const { return state_; }
    const PerformanceStats& performance_stats() const { return stats_; }

private:
    struct LocalResult {
        Strain delta_eps_v = Strain::Zero();
        InternalState updated_state;
        bool converged = false;
    };

    struct TrialResult {
        TimeState state;
        bool converged = false;
    };

    const Mesh& mesh_;
    const Element& element_;
    const ConstitutiveModel& model_;
    const ThermalField& thermal_;

    Eigen::SimplicialLDLT<Eigen::SparseMatrix<double>> ldlt_;
    Eigen::VectorXd f_external_;
    std::shared_ptr<const WallPressureField> wall_pressure_;
    std::vector<Stress> sigma_geo_gp_;
    std::vector<int> fixed_dofs_;
    ImplicitAdaptiveOptions options_;
    mutable PerformanceStats stats_;

    TimeState state_;
    int n_gp_ = 0;
    double current_time_s_ = 0.0;
    double last_error_ = 0.0;
    double suggested_dt_s_ = 0.0;

    static void apply_dirichlet(Eigen::SparseMatrix<double>& K,
                                Eigen::VectorXd& f,
                                const std::vector<int>& dofs);

    TrialResult take_step(const TimeState& base, double time_s, double dt_s) const;
    LocalResult solve_local_gp(const Stress& sigma_n,
                               const InternalState& state_n,
                               double T,
                               double dt_s) const;
    void update_stresses(TimeState& state) const;
    Eigen::VectorXd pressure_load_at(double time_s) const;
    double gauss_r(int e, int g) const;
    Eigen::Vector2d gauss_position(int e, int g) const;
    Strain thermal_strain_at(int e, int g, double time_s) const;
};
