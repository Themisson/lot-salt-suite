#include "solver/ImplicitAdaptiveIntegrator.hpp"
#include "solver/TimeOutput.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <Eigen/LU>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace fs = std::filesystem;

void ImplicitAdaptiveIntegrator::apply_dirichlet(Eigen::SparseMatrix<double>& K,
                                                  Eigen::VectorXd& f,
                                                  const std::vector<int>& dofs) {
    K.makeCompressed();
    for (int d : dofs) {
        for (Eigen::SparseMatrix<double>::InnerIterator it(K, d); it; ++it)
            it.valueRef() = 0.0;
        for (int j = 0; j < K.outerSize(); ++j)
            for (Eigen::SparseMatrix<double>::InnerIterator it(K, j); it; ++it)
                if (it.row() == d)
                    it.valueRef() = 0.0;
        K.coeffRef(d, d) = 1.0;
        f[d] = 0.0;
    }
    K.makeCompressed();
}

ImplicitAdaptiveIntegrator::ImplicitAdaptiveIntegrator(
    const Mesh& mesh,
    const Element& element,
    const ConstitutiveModel& model,
    const ThermalField& thermal,
    Eigen::SparseMatrix<double> K,
    Eigen::VectorXd f_external,
    std::vector<Stress> sigma_geo_gp,
    std::vector<int> fixed_dofs,
    ImplicitAdaptiveOptions options,
    PerformanceStats initial_stats,
    std::shared_ptr<const WallPressureField> wall_pressure)
    : mesh_(mesh)
    , element_(element)
    , model_(model)
    , thermal_(thermal)
    , f_external_(std::move(f_external))
    , wall_pressure_(std::move(wall_pressure))
    , sigma_geo_gp_(std::move(sigma_geo_gp))
    , fixed_dofs_(std::move(fixed_dofs))
    , options_(options)
    , stats_(initial_stats)
    , n_gp_(static_cast<int>(element.gauss_points().size()))
    , suggested_dt_s_(options.dt_max_s) {

    if (options_.tol_local <= 0.0 || options_.tol_global <= 0.0 ||
        options_.dt_min_s <= 0.0 || options_.dt_max_s <= 0.0)
        throw std::invalid_argument("ImplicitAdaptiveIntegrator: invalid adaptive options");

    const int total_gp = mesh_.n_elements * n_gp_;
    auto assembly_start = std::chrono::steady_clock::now();
    Eigen::VectorXd f_geo = Assembler::assemble_geostatic_force(
        mesh_, element_, sigma_geo_gp_);
    auto assembly_end = std::chrono::steady_clock::now();
    stats_.time_assembly_s += std::chrono::duration<double>(
        assembly_end - assembly_start).count();
    Eigen::VectorXd f_net = f_external_ - f_geo;

    apply_dirichlet(K, f_net, fixed_dofs_);
    ldlt_.compute(K);
    if (ldlt_.info() != Eigen::Success)
        throw std::runtime_error("ImplicitAdaptiveIntegrator: K factorization failed");

    auto solve_start = std::chrono::steady_clock::now();
    state_.u_total = ldlt_.solve(f_net);
    auto solve_end = std::chrono::steady_clock::now();
    stats_.time_solve_s += std::chrono::duration<double>(
        solve_end - solve_start).count();
    if (ldlt_.info() != Eigen::Success)
        throw std::runtime_error("ImplicitAdaptiveIntegrator: initial elastic solve failed");

    state_.eps_v_gp.assign(total_gp, Strain::Zero());
    state_.eps_th_gp.assign(total_gp, Strain::Zero());
    state_.state_gp.assign(total_gp, InternalState{});
    state_.sigma_gp.resize(total_gp);
    update_stresses(state_);
}

Eigen::VectorXd ImplicitAdaptiveIntegrator::pressure_load_at(double time_s) const {
    if (!wall_pressure_)
        return f_external_;
    return Assembler::assemble_boundary_pressure(
        mesh_, element_, *wall_pressure_, time_s, 0.0);
}

ImplicitAdaptiveIntegrator::LocalResult
ImplicitAdaptiveIntegrator::solve_local_gp(const Stress& sigma_n,
                                            const InternalState& state_n,
                                            double T,
                                            double dt_s) const {
    const Eigen::Matrix4d D = model_.D_elastic();
    LocalResult out;
    out.updated_state = state_n;

    auto initial = model_.evaluate(sigma_n, state_n, T, dt_s);
    Strain deps = initial.strain_rate_voigt * dt_s;

    for (int iter = 0; iter < options_.max_newton_iters; ++iter) {
        const Stress sigma_trial = sigma_n - D * deps;
        auto result = model_.evaluate(sigma_trial, state_n, T, dt_s);
        const Strain residual = deps - result.strain_rate_voigt * dt_s;
        if (residual.norm() <= options_.tol_local) {
            out.delta_eps_v = deps;
            out.updated_state = result.updated_state;
            out.converged = true;
            return out;
        }

        const Eigen::Matrix4d tangent = model_.tangent(sigma_trial, state_n, T);
        const Eigen::Matrix4d J =
            Eigen::Matrix4d::Identity() + dt_s * tangent * D;
        const Strain delta = J.fullPivLu().solve(-residual);
        if (!delta.allFinite())
            return out;
        deps += delta;
        if (delta.norm() <= options_.tol_local) {
            const Stress final_sigma = sigma_n - D * deps;
            auto final_result = model_.evaluate(final_sigma, state_n, T, dt_s);
            out.delta_eps_v = deps;
            out.updated_state = final_result.updated_state;
            out.converged = true;
            return out;
        }
    }
    return out;
}

ImplicitAdaptiveIntegrator::TrialResult
ImplicitAdaptiveIntegrator::take_step(const TimeState& base,
                                      double time_s,
                                      double dt_s) const {
    const int total_gp = mesh_.n_elements * n_gp_;
    TrialResult trial;
    trial.state = base;
    trial.converged = true;

    std::vector<double> T_gp(total_gp);
    std::vector<Strain> eps_th_new_gp(total_gp);
    for (int e = 0; e < mesh_.n_elements; ++e) {
        for (int g = 0; g < n_gp_; ++g) {
            const int idx = e * n_gp_ + g;
            const Eigen::Vector2d x_gp = gauss_position(e, g);
            T_gp[idx] = thermal_.temperature_at(x_gp, time_s + dt_s);
            eps_th_new_gp[idx] = thermal_strain_at(e, g, time_s + dt_s);
        }
    }

    std::vector<Strain> delta_eps_v(total_gp);
    std::vector<char> local_converged(total_gp, 1);
    auto constitutive_start = std::chrono::steady_clock::now();
#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for (int e = 0; e < mesh_.n_elements; ++e) {
        for (int g = 0; g < n_gp_; ++g) {
            const int idx = e * n_gp_ + g;

            LocalResult local = solve_local_gp(base.sigma_gp[idx],
                                               base.state_gp[idx],
                                               T_gp[idx], dt_s);
            if (!local.converged) {
                local_converged[idx] = 0;
                continue;
            }
            delta_eps_v[idx] = local.delta_eps_v;
            trial.state.state_gp[idx] = local.updated_state;
            trial.state.eps_th_gp[idx] = eps_th_new_gp[idx];
        }
    }
    auto constitutive_end = std::chrono::steady_clock::now();
    stats_.time_constitutive_s += std::chrono::duration<double>(
        constitutive_end - constitutive_start).count();

    if (std::any_of(local_converged.begin(), local_converged.end(),
                    [](char ok) { return ok == 0; })) {
        trial.converged = false;
        return trial;
    }

    auto assembly_start = std::chrono::steady_clock::now();
    Eigen::VectorXd f_v = Assembler::assemble_pseudo_force(
        mesh_, element_, model_, delta_eps_v);
    std::vector<Strain> delta_eps_th(total_gp);
    for (int idx = 0; idx < total_gp; ++idx)
        delta_eps_th[idx] = trial.state.eps_th_gp[idx] - base.eps_th_gp[idx];
    Eigen::VectorXd f_th = Assembler::assemble_pseudo_force(
        mesh_, element_, model_, delta_eps_th);
    Eigen::VectorXd f_pressure_delta = Eigen::VectorXd::Zero(mesh_.total_dofs());
    if (wall_pressure_) {
        f_pressure_delta = pressure_load_at(time_s + dt_s) - pressure_load_at(time_s);
    }
    Eigen::VectorXd f_total = f_v + f_th + f_pressure_delta;
    auto assembly_end = std::chrono::steady_clock::now();
    stats_.time_assembly_s += std::chrono::duration<double>(
        assembly_end - assembly_start).count();
    for (int d : fixed_dofs_)
        f_total[d] = 0.0;

    auto solve_start = std::chrono::steady_clock::now();
    Eigen::VectorXd delta_u = ldlt_.solve(f_total);
    auto solve_end = std::chrono::steady_clock::now();
    stats_.time_solve_s += std::chrono::duration<double>(
        solve_end - solve_start).count();
    if (ldlt_.info() != Eigen::Success || !delta_u.allFinite()) {
        trial.converged = false;
        return trial;
    }

    trial.state.u_total = base.u_total + delta_u;
    for (int idx = 0; idx < total_gp; ++idx)
        trial.state.eps_v_gp[idx] = base.eps_v_gp[idx] + delta_eps_v[idx];
    update_stresses(trial.state);
    return trial;
}

double ImplicitAdaptiveIntegrator::advance(double dt_s) {
    double dt = std::min(dt_s, options_.dt_max_s);
    const TimeState base = state_;

    while (dt >= options_.dt_min_s) {
        TrialResult full = take_step(base, current_time_s_, dt);
        if (!full.converged) {
            dt *= 0.5;
            continue;
        }

        TrialResult half1 = take_step(base, current_time_s_, 0.5 * dt);
        if (!half1.converged) {
            dt *= 0.5;
            continue;
        }
        TrialResult half2 = take_step(half1.state, current_time_s_ + 0.5 * dt, 0.5 * dt);
        if (!half2.converged) {
            dt *= 0.5;
            continue;
        }

        const double denom = std::max(half2.state.u_total.norm(), 1.0e-30);
        const double err = (full.state.u_total - half2.state.u_total).norm() / denom;
        if (!std::isfinite(err) || err > options_.tol_global) {
            dt *= 0.5;
            continue;
        }

        state_ = std::move(half2.state);
        current_time_s_ += dt;
        if (wall_pressure_)
            f_external_ = pressure_load_at(current_time_s_);
        last_error_ = err;
        double factor = 1.25;
        if (err < 0.1 * options_.tol_global) {
            const double safe_err = std::max(err, 1.0e-16);
            factor = std::min(2.0, 0.9 * std::sqrt(options_.tol_global / safe_err));
        }
        suggested_dt_s_ = std::min(options_.dt_max_s, dt * factor);
        return dt;
    }

    throw std::runtime_error(
        "ImplicitAdaptiveIntegrator: passo mínimo atingido — modelo mal-condicionado");
}

void ImplicitAdaptiveIntegrator::update_stresses(TimeState& state) const {
    const Eigen::Matrix4d D = model_.D_elastic();
    const auto gps = element_.gauss_points();
    const int nne = element_.n_nodes();
    const int ndpn = element_.n_dofs_per_node();
    const int ne_dof = nne * ndpn;

    for (int e = 0; e < mesh_.n_elements; ++e) {
        std::vector<Node> coords(nne);
        Eigen::VectorXd ue(ne_dof);
        for (int i = 0; i < nne; ++i) {
            const int gn = mesh_.elem_nodes[nne * e + i];
            coords[i] = mesh_.nodes[gn];
            for (int d = 0; d < ndpn; ++d)
                ue[i * ndpn + d] = state.u_total[mesh_.dof_index(gn, d)];
        }
        for (int g = 0; g < n_gp_; ++g) {
            const int idx = e * n_gp_ + g;
            Eigen::MatrixXd B = element_.B_matrix(gps[g], coords);
            Strain strain_total = B * ue;
            Strain strain_el = strain_total - state.eps_v_gp[idx]
                               - state.eps_th_gp[idx];
            state.sigma_gp[idx] = D * strain_el + sigma_geo_gp_[idx];
        }
    }
}

double ImplicitAdaptiveIntegrator::wall_closure_pct() const {
    return -state_.u_total[mesh_.dof_index(0, 0)] / mesh_.nodes.front().r * 100.0;
}

double ImplicitAdaptiveIntegrator::gauss_r(int e, int g) const {
    return gauss_position(e, g)[0];
}

Eigen::Vector2d ImplicitAdaptiveIntegrator::gauss_position(int e, int g) const {
    const int nne = element_.n_nodes();
    auto gps = element_.gauss_points();
    std::vector<Node> coords(nne);
    for (int i = 0; i < nne; ++i)
        coords[i] = mesh_.nodes[mesh_.elem_nodes[nne * e + i]];
    std::vector<double> N(nne);
    element_.shape_functions(gps[g], coords, N);
    Eigen::Vector2d x = Eigen::Vector2d::Zero();
    for (int i = 0; i < nne; ++i) {
        x[0] += N[i] * coords[i].r;
        x[1] += N[i] * coords[i].z;
    }
    return x;
}

Strain ImplicitAdaptiveIntegrator::thermal_strain_at(int e, int g, double time_s) const {
    const double alpha = thermal_.alpha_thermal();
    if (alpha == 0.0)
        return Strain::Zero();

    const Eigen::Vector2d x_gp = gauss_position(e, g);
    const double delta_T = thermal_.temperature_at(x_gp, time_s) - thermal_.T_reference();
    Strain eps = Strain::Zero();
    eps[0] = alpha * delta_T;
    eps[1] = alpha * delta_T;
    eps[2] = alpha * delta_T;
    return eps;
}

void ImplicitAdaptiveIntegrator::run(double dt_s, double t_end_s, int output_every,
                                      const fs::path& out_dir,
                                      VtuOutputOptions vtu_options,
                                      const DamageTrackingOptions& damage_options) {
    fs::create_directories(out_dir);
    ConstantWallPressureField fallback_pressure(0.0);
    const WallPressureField& pressure =
        wall_pressure_ ? *wall_pressure_ : fallback_pressure;
    std::ofstream csv(out_dir / "closure.csv");
    std::ofstream profile_csv(out_dir / "displacements_profile.csv");
    std::ofstream wall_csv(out_dir / "wall_profile.csv");
    std::ofstream pressure_csv(out_dir / "wall_pressure_profile.csv");
    time_output::write_closure_header(csv);
    time_output::write_displacement_profile_header(profile_csv);
    time_output::write_wall_profile_header(wall_csv);
    time_output::write_wall_pressure_profile_header(pressure_csv);
    csv << std::fixed << std::setprecision(12);
    profile_csv << std::fixed << std::setprecision(12);
    wall_csv << std::fixed << std::setprecision(12);
    pressure_csv << std::fixed << std::setprecision(12);
    time_output::write_closure_record(
        csv, mesh_, state_.u_total, 0.0, wall_closure_pct());
    time_output::write_displacement_profile_record(
        profile_csv, mesh_, state_.u_total, 0.0);
    time_output::write_wall_profile_record(
        wall_csv, mesh_, state_.u_total, 0.0,
        vtu_options.depth_origin_m, vtu_options.well_radius_m);
    time_output::write_wall_pressure_profile_record(
        pressure_csv, mesh_, pressure, thermal_, 0.0, 0.0,
        vtu_options.depth_origin_m);

    double t = 0.0;
    int step = 0;
    double dt = std::min(dt_s, options_.dt_max_s);
    std::vector<VtuFrame> vtu_frames;
    const std::string vtu_case = vtu_options.case_name.empty()
        ? out_dir.filename().string()
        : vtu_options.case_name;
    auto write_vtu = [&](double time_s, bool force) {
        if (!vtu_options.enabled)
            return;
        if (!force && (step % vtu_options.every_n_steps != 0))
            return;
        if (!vtu_frames.empty() &&
            std::abs(vtu_frames.back().time_s - time_s) < 1.0e-9)
            return;
        const std::string file = VtuWriter::frame_filename(
            vtu_case, static_cast<int>(vtu_frames.size()));
        VtuSnapshot snapshot{&state_.u_total, &state_.sigma_gp, &state_.eps_v_gp,
                             &state_.state_gp, &thermal_, time_s};
        VtuWriter::write(out_dir / file, mesh_, element_, snapshot);
        vtu_frames.push_back(VtuFrame{file, time_s});
    };
    write_vtu(0.0, true);
    DamageDiagnostics damage(out_dir, mesh_, element_, thermal_, damage_options);
    damage.initialize(state_, model_, 0.0);
    while (t < t_end_s - 1.0e-12) {
        const double accepted = advance(std::min(dt, t_end_s - t));
        t += accepted;
        ++step;
        dt = suggested_dt_s_;
        damage.record(state_, model_, t);
        if (step % output_every == 0) {
            const double t_h = t / 3600.0;
            time_output::write_closure_record(
                csv, mesh_, state_.u_total, t_h, wall_closure_pct());
            time_output::write_displacement_profile_record(
                profile_csv, mesh_, state_.u_total, t_h);
            time_output::write_wall_profile_record(
                wall_csv, mesh_, state_.u_total, t_h,
                vtu_options.depth_origin_m, vtu_options.well_radius_m);
            time_output::write_wall_pressure_profile_record(
                pressure_csv, mesh_, pressure, thermal_, t_h, t,
                vtu_options.depth_origin_m);
        }
        write_vtu(t, false);
    }
    time_output::write_closure_record(
        csv, mesh_, state_.u_total, t / 3600.0, wall_closure_pct());
    time_output::write_displacement_profile_record(
        profile_csv, mesh_, state_.u_total, t / 3600.0);
    time_output::write_wall_profile_record(
        wall_csv, mesh_, state_.u_total, t / 3600.0,
        vtu_options.depth_origin_m, vtu_options.well_radius_m);
    time_output::write_wall_pressure_profile_record(
        pressure_csv, mesh_, pressure, thermal_, t / 3600.0, t,
        vtu_options.depth_origin_m);
    write_vtu(t, true);
    if (vtu_options.enabled)
        VtuWriter::write_pvd(out_dir / (vtu_case + ".pvd"), vtu_frames);
    std::cout << "[time] t=" << (t/3600.0) << "h  closure=" << wall_closure_pct() << "%\n";
}

void ImplicitAdaptiveIntegrator::run_schedule(const std::vector<TimeSegment>& schedule,
                                               double t_end_s, int output_every,
                                               const fs::path& out_dir,
                                               VtuOutputOptions vtu_options,
                                               const DamageTrackingOptions& damage_options) {
    if (schedule.empty())
        throw std::runtime_error("ImplicitAdaptiveIntegrator::run_schedule: empty schedule");

    fs::create_directories(out_dir);
    ConstantWallPressureField fallback_pressure(0.0);
    const WallPressureField& pressure =
        wall_pressure_ ? *wall_pressure_ : fallback_pressure;
    std::ofstream csv(out_dir / "closure.csv");
    std::ofstream profile_csv(out_dir / "displacements_profile.csv");
    std::ofstream wall_csv(out_dir / "wall_profile.csv");
    std::ofstream pressure_csv(out_dir / "wall_pressure_profile.csv");
    time_output::write_closure_header(csv);
    time_output::write_displacement_profile_header(profile_csv);
    time_output::write_wall_profile_header(wall_csv);
    time_output::write_wall_pressure_profile_header(pressure_csv);
    csv << std::fixed << std::setprecision(12);
    profile_csv << std::fixed << std::setprecision(12);
    wall_csv << std::fixed << std::setprecision(12);
    pressure_csv << std::fixed << std::setprecision(12);
    time_output::write_closure_record(
        csv, mesh_, state_.u_total, 0.0, wall_closure_pct());
    time_output::write_displacement_profile_record(
        profile_csv, mesh_, state_.u_total, 0.0);
    time_output::write_wall_profile_record(
        wall_csv, mesh_, state_.u_total, 0.0,
        vtu_options.depth_origin_m, vtu_options.well_radius_m);
    time_output::write_wall_pressure_profile_record(
        pressure_csv, mesh_, pressure, thermal_, 0.0, 0.0,
        vtu_options.depth_origin_m);

    double t = 0.0;
    int step = 0;
    int seg = 0;
    double dt = std::min(schedule.front().dt_s, options_.dt_max_s);
    std::vector<VtuFrame> vtu_frames;
    const std::string vtu_case = vtu_options.case_name.empty()
        ? out_dir.filename().string()
        : vtu_options.case_name;
    auto write_vtu = [&](double time_s, bool force) {
        if (!vtu_options.enabled)
            return;
        if (!force && (step % vtu_options.every_n_steps != 0))
            return;
        if (!vtu_frames.empty() &&
            std::abs(vtu_frames.back().time_s - time_s) < 1.0e-9)
            return;
        const std::string file = VtuWriter::frame_filename(
            vtu_case, static_cast<int>(vtu_frames.size()));
        VtuSnapshot snapshot{&state_.u_total, &state_.sigma_gp, &state_.eps_v_gp,
                             &state_.state_gp, &thermal_, time_s};
        VtuWriter::write(out_dir / file, mesh_, element_, snapshot);
        vtu_frames.push_back(VtuFrame{file, time_s});
    };
    write_vtu(0.0, true);
    DamageDiagnostics damage(out_dir, mesh_, element_, thermal_, damage_options);
    damage.initialize(state_, model_, 0.0);
    while (t < t_end_s - 1.0e-12) {
        while (seg + 1 < static_cast<int>(schedule.size()) &&
               t >= schedule[seg].until_s) {
            ++seg;
            dt = std::min(dt, schedule[seg].dt_s);
        }

        const double segment_remaining = schedule[seg].until_s - t;
        const double trial_dt = std::min({dt, segment_remaining, t_end_s - t, options_.dt_max_s});
        if (trial_dt <= 0.0)
            break;

        const double accepted = advance(trial_dt);
        t += accepted;
        ++step;
        dt = std::min(suggested_dt_s_, schedule[seg].dt_s);
        damage.record(state_, model_, t);

        if (step % output_every == 0) {
            const double t_h = t / 3600.0;
            time_output::write_closure_record(
                csv, mesh_, state_.u_total, t_h, wall_closure_pct());
            time_output::write_displacement_profile_record(
                profile_csv, mesh_, state_.u_total, t_h);
            time_output::write_wall_profile_record(
                wall_csv, mesh_, state_.u_total, t_h,
                vtu_options.depth_origin_m, vtu_options.well_radius_m);
            time_output::write_wall_pressure_profile_record(
                pressure_csv, mesh_, pressure, thermal_, t_h, t,
                vtu_options.depth_origin_m);
        }
        write_vtu(t, false);
    }
    time_output::write_closure_record(
        csv, mesh_, state_.u_total, t / 3600.0, wall_closure_pct());
    time_output::write_displacement_profile_record(
        profile_csv, mesh_, state_.u_total, t / 3600.0);
    time_output::write_wall_profile_record(
        wall_csv, mesh_, state_.u_total, t / 3600.0,
        vtu_options.depth_origin_m, vtu_options.well_radius_m);
    time_output::write_wall_pressure_profile_record(
        pressure_csv, mesh_, pressure, thermal_, t / 3600.0, t,
        vtu_options.depth_origin_m);
    write_vtu(t, true);
    if (vtu_options.enabled)
        VtuWriter::write_pvd(out_dir / (vtu_case + ".pvd"), vtu_frames);
    std::cout << "[time] t=" << (t/3600.0) << "h  closure=" << wall_closure_pct() << "%\n";
}
