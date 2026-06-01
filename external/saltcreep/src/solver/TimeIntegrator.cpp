#include "solver/TimeIntegrator.hpp"
#include "solver/TimeOutput.hpp"
#include <stdexcept>
#include <iostream>
#include <iomanip>
#include <filesystem>
#include <sstream>
#include <chrono>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace fs = std::filesystem;

void TimeIntegrator::apply_dirichlet(Eigen::SparseMatrix<double>& K,
                                      Eigen::VectorXd&             f,
                                      const std::vector<int>&      dofs) {
    K.makeCompressed();
    for (int d : dofs) {
        // Zero column d (CCS inner iterator iterates rows within each column)
        for (Eigen::SparseMatrix<double>::InnerIterator it(K, d); it; ++it)
            it.valueRef() = 0.0;
        // Zero row d (iterate all columns looking for row d)
        for (int j = 0; j < K.outerSize(); ++j)
            for (Eigen::SparseMatrix<double>::InnerIterator it(K, j); it; ++it)
                if (it.row() == d) it.valueRef() = 0.0;
        K.coeffRef(d, d) = 1.0;
        f[d] = 0.0;
    }
    K.makeCompressed();
}

TimeIntegrator::TimeIntegrator(const Mesh&                 mesh,
                                const Element&              element,
                                const ConstitutiveModel&    model,
                                const ThermalField&         thermal,
                                Eigen::SparseMatrix<double> K,
                                Eigen::VectorXd             f_external,
                                std::vector<Stress>         sigma_geo_gp,
                                std::vector<int>            fixed_dofs,
                                PerformanceStats            initial_stats,
                                std::shared_ptr<const WallPressureField> wall_pressure)
    : mesh_(mesh)
    , element_(element)
    , model_(model)
    , thermal_(thermal)
    , f_external_(std::move(f_external))
    , wall_pressure_(std::move(wall_pressure))
    , sigma_geo_gp_(std::move(sigma_geo_gp))
    , fixed_dofs_(std::move(fixed_dofs))
    , stats_(initial_stats)
    , n_gp_(static_cast<int>(element.gauss_points().size()))
{
    const int total_gp = mesh_.n_elements * n_gp_;

    // Geostatic internal-force vector: f_geo = ∫ Bᵀ σ_geo jw
    // Physical role: force the removed cavity rock was exerting on the annulus.
    // Net drilling perturbation: f_net = f_fluid - f_geo  → produces inward closure.
    // Without f_geo the solver applies only fluid pressure on a stress-free medium.
    auto assembly_start = std::chrono::steady_clock::now();
    Eigen::VectorXd f_geo = Assembler::assemble_geostatic_force(
        mesh_, element_, sigma_geo_gp_);
    auto assembly_end = std::chrono::steady_clock::now();
    stats_.time_assembly_s += std::chrono::duration<double>(
        assembly_end - assembly_start).count();
    Eigen::VectorXd f_net = f_external_ - f_geo;

    // Apply Dirichlet BCs before factoring.
    // CRITICAL for well problems: always pin the outer wall (u[Re]=0).
    // Without this, the geostatic force at Re (~σv·2πRe, very large) drives
    // a spurious outward expansion that overwhelms the inward drilling force.
    apply_dirichlet(K, f_net, fixed_dofs_);

    // Factor K (with BCs already baked in) — reused for ALL back-substitutions.
    ldlt_.compute(K);
    if (ldlt_.info() != Eigen::Success)
        throw std::runtime_error("TimeIntegrator: K factorization failed");

    // Initial elastic solve: u₀ = K⁻¹ (f_fluid − f_geo) [with BCs]
    auto solve_start = std::chrono::steady_clock::now();
    state_.u_total = ldlt_.solve(f_net);
    auto solve_end = std::chrono::steady_clock::now();
    stats_.time_solve_s += std::chrono::duration<double>(
        solve_end - solve_start).count();
    if (ldlt_.info() != Eigen::Success)
        throw std::runtime_error("TimeIntegrator: initial elastic solve failed");

    // Initialize viscous state to zero
    state_.eps_v_gp.assign(total_gp, Strain::Zero());
    state_.eps_th_gp.assign(total_gp, Strain::Zero());
    state_.state_gp.assign(total_gp, InternalState{});

    // Compute initial stresses: sigma = D * B * u₀ + sigma_geo
    state_.sigma_gp.resize(total_gp);
    update_stresses();
}

Eigen::VectorXd TimeIntegrator::pressure_load_at(double time_s) const {
    if (!wall_pressure_)
        return f_external_;
    return Assembler::assemble_boundary_pressure(
        mesh_, element_, *wall_pressure_, time_s, 0.0);
}

void TimeIntegrator::update_stresses() {
    const Eigen::Matrix4d D = model_.D_elastic();
    const auto gps = element_.gauss_points();
    const int nne  = element_.n_nodes();
    const int ndpn = element_.n_dofs_per_node();
    const int ne_dof = nne * ndpn;

#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for (int e = 0; e < mesh_.n_elements; ++e) {
        std::vector<Node> coords(nne);
        Eigen::VectorXd   ue(ne_dof);
        for (int i = 0; i < nne; ++i) {
            int gn  = mesh_.elem_nodes[nne * e + i];
            coords[i] = mesh_.nodes[gn];
            for (int d = 0; d < ndpn; ++d)
                ue[i * ndpn + d] = state_.u_total[mesh_.dof_index(gn, d)];
        }
        for (int g = 0; g < n_gp_; ++g) {
            int idx = e * n_gp_ + g;
            Eigen::MatrixXd B = element_.B_matrix(gps[g], coords);
            Strain strain_total = B * ue;
            Strain strain_el    = strain_total - state_.eps_v_gp[idx]
                                  - state_.eps_th_gp[idx];
            state_.sigma_gp[idx] = D * strain_el + sigma_geo_gp_[idx];
        }
    }
}

void TimeIntegrator::advance(double dt_s) {
    const int  total_gp = mesh_.n_elements * n_gp_;

    std::vector<double> T_gp(total_gp);
    std::vector<Strain> eps_th_new_gp(total_gp);
    for (int e = 0; e < mesh_.n_elements; ++e) {
        for (int g = 0; g < n_gp_; ++g) {
            const int idx = e * n_gp_ + g;
            const Eigen::Vector2d x_gp = gauss_position(e, g);
            T_gp[idx] = thermal_.temperature_at(x_gp, current_time_s_);
        }
    }
    for (int e = 0; e < mesh_.n_elements; ++e) {
        for (int g = 0; g < n_gp_; ++g) {
            const int idx = e * n_gp_ + g;
            eps_th_new_gp[idx] = thermal_strain_at(e, g, current_time_s_ + dt_s);
        }
    }

    // 1. Evaluate DM rate at all GPs and build delta_eps_v / delta_eps_th
    std::vector<Strain> delta_eps_v(total_gp);
    std::vector<Strain> delta_eps_th(total_gp);
    auto constitutive_start = std::chrono::steady_clock::now();
#ifdef _OPENMP
#pragma omp parallel for schedule(static)
#endif
    for (int e = 0; e < mesh_.n_elements; ++e) {
        // Gauss point radial coordinate (constant in 1D axisym → no z variation)
        for (int g = 0; g < n_gp_; ++g) {
            int idx = e * n_gp_ + g;

            auto result = model_.evaluate(state_.sigma_gp[idx],
                                           state_.state_gp[idx],
                                           T_gp[idx], dt_s);
            delta_eps_v[idx]       = result.strain_rate_voigt * dt_s;
            state_.state_gp[idx]   = result.updated_state;
            delta_eps_th[idx] = eps_th_new_gp[idx] - state_.eps_th_gp[idx];
        }
    }
    auto constitutive_end = std::chrono::steady_clock::now();
    stats_.time_constitutive_s += std::chrono::duration<double>(
        constitutive_end - constitutive_start).count();

    // 2. Assemble incremental pseudo-force
    auto assembly_start = std::chrono::steady_clock::now();
    Eigen::VectorXd f_v = Assembler::assemble_pseudo_force(
        mesh_, element_, model_, delta_eps_v);
    Eigen::VectorXd f_th = Assembler::assemble_pseudo_force(
        mesh_, element_, model_, delta_eps_th);
    Eigen::VectorXd f_pressure_delta = Eigen::VectorXd::Zero(mesh_.total_dofs());
    if (wall_pressure_) {
        f_pressure_delta =
            pressure_load_at(current_time_s_ + dt_s) - pressure_load_at(current_time_s_);
    }
    Eigen::VectorXd f_total = f_v + f_th + f_pressure_delta;
    auto assembly_end = std::chrono::steady_clock::now();
    stats_.time_assembly_s += std::chrono::duration<double>(
        assembly_end - assembly_start).count();

    // Zero fixed DOFs in RHS so the constrained K gives delta_u=0 there
    for (int d : fixed_dofs_) f_total[d] = 0.0;

    // 3. Back-substitution: K * delta_u = f_v  (K already has BCs from constructor)
    auto solve_start = std::chrono::steady_clock::now();
    Eigen::VectorXd delta_u = ldlt_.solve(f_total);
    auto solve_end = std::chrono::steady_clock::now();
    stats_.time_solve_s += std::chrono::duration<double>(
        solve_end - solve_start).count();
    if (ldlt_.info() != Eigen::Success)
        throw std::runtime_error("TimeIntegrator::advance: solve failed");

    // 4-5. Update totals
    state_.u_total += delta_u;
    for (int idx = 0; idx < total_gp; ++idx) {
        state_.eps_v_gp[idx] += delta_eps_v[idx];
        state_.eps_th_gp[idx] += delta_eps_th[idx];
    }

    // 6. Recompute stresses
    update_stresses();
    current_time_s_ += dt_s;
    if (wall_pressure_)
        f_external_ = pressure_load_at(current_time_s_);
}

double TimeIntegrator::wall_closure_pct() const {
    // Positive closure = inward displacement of inner wall
    return -state_.u_total[mesh_.dof_index(0, 0)] / mesh_.nodes.front().r * 100.0;
}

double TimeIntegrator::gauss_r(int e, int g) const {
    return gauss_position(e, g)[0];
}

Eigen::Vector2d TimeIntegrator::gauss_position(int e, int g) const {
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

Strain TimeIntegrator::thermal_strain_at(int e, int g, double time_s) const {
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

void TimeIntegrator::run(double dt_s, double t_end_s, int output_every,
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

    double t = 0.0;
    int    step = 0;
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

    // Record initial state
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
    write_vtu(0.0, true);
    DamageDiagnostics damage(out_dir, mesh_, element_, thermal_, damage_options);
    damage.initialize(state_, model_, 0.0);

    while (t + dt_s * 0.999 < t_end_s) {
        double actual_dt = std::min(dt_s, t_end_s - t);
        advance(actual_dt);
        t    += actual_dt;
        step += 1;
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
    // Always record final state
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

void TimeIntegrator::run_schedule(const std::vector<TimeSegment>& schedule,
                                   double t_end_s, int output_every,
                                   const fs::path& out_dir,
                                   VtuOutputOptions vtu_options,
                                   const DamageTrackingOptions& damage_options) {
    if (schedule.empty()) {
        throw std::runtime_error("TimeIntegrator::run_schedule: empty schedule");
    }
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

    double t    = 0.0;
    int    step = 0;
    int    seg  = 0;  // current segment index
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

    while (t < t_end_s - 1e-12) {
        // Find current segment
        while (seg + 1 < static_cast<int>(schedule.size()) &&
               t >= schedule[seg].until_s)
            ++seg;

        double dt = std::min({schedule[seg].dt_s,
                              schedule[seg].until_s - t,
                              t_end_s - t});
        if (dt <= 0.0) break;

        advance(dt);
        t    += dt;
        step += 1;
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
    // Final record
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
