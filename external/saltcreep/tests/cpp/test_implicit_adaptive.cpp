#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <stdexcept>
#include <vector>

#include "constitutive/double_mechanism.hpp"
#include "elements/axisym_1d_L3.hpp"
#include "io/CaseParser.hpp"
#include "solver/Assembler.hpp"
#include "solver/ImplicitAdaptiveIntegrator.hpp"
#include "solver/TimeIntegrator.hpp"
#include "thermal/profile_field.hpp"

namespace fs = std::filesystem;

namespace {
fs::path find_tcc_case(const std::string& name) {
    for (const auto& candidate : {
             fs::path("cases/tcc") / name,
             fs::path("../cases/tcc") / name,
             fs::path("../../cases/tcc") / name}) {
        if (fs::exists(candidate))
            return candidate;
    }
    throw std::runtime_error("Cannot find case file: " + name);
}

std::vector<Stress> build_geostatic(const Mesh& mesh,
                                    const Element& elem,
                                    const CaseData& cd) {
    const double depth = cd.depths.burial_m + cd.depths.water_depth_m + cd.depths.salt_above_m;
    const double sigma_v = -cd.overburden_grad_Pa_per_m * depth;
    const double sigma_h = cd.k0 * sigma_v;
    const int total_gp = mesh.n_elements * static_cast<int>(elem.gauss_points().size());
    return std::vector<Stress>(total_gp, Stress{sigma_h, sigma_h, sigma_v, 0.0});
}

ProfileField make_thermal(const CaseData& cd) {
    return (cd.thermal.mode == "profile")
        ? ProfileField::make_profile(cd.thermal.seabed_temp_C,
                                     cd.depths.burial_m + cd.depths.water_depth_m,
                                     cd.thermal.grad_C_per_m)
        : ProfileField::make_constant(cd.thermal.T_K);
}

double run_explicit(CaseData cd, double total_h, double dt_h, int n_radial) {
    cd.mesh.n_radial = n_radial;
    cd.mesh.ratio = 50.0;
    const double Ri = cd.geom.Ri;
    const double Re = Ri * cd.geom.outer_factor;
    (void)Re;

    AxisymL3 elem;
    DoubleMechanism model(cd.dm, cd.E_Pa, cd.nu);
    ProfileField thermal = make_thermal(cd);
    Mesh1D mesh = build_mesh_L3(Ri, Ri * cd.geom.outer_factor, cd.mesh.n_radial, cd.mesh.ratio);
    auto K = Assembler::assemble_K(mesh, elem, model);
    auto f = Assembler::assemble_neumann(mesh, cd.fluid_Pa, 0.0);
    auto sigma_geo = build_geostatic(mesh, elem, cd);
    std::vector<int> fixed_dofs = {mesh.n_nodes - 1};

    TimeIntegrator integrator(mesh, elem, model, thermal, K, f, sigma_geo, fixed_dofs);
    const fs::path tmp = fs::temp_directory_path() / "saltcreep_test" / "implicit_explicit";
    integrator.run(dt_h * 3600.0, total_h * 3600.0, 999999, tmp);
    return integrator.wall_closure_pct();
}

double run_implicit(CaseData cd, double total_h, double dt_h, int n_radial,
                    double tol_global, double dt_max_h) {
    cd.mesh.n_radial = n_radial;
    cd.mesh.ratio = 50.0;
    const double Ri = cd.geom.Ri;

    AxisymL3 elem;
    DoubleMechanism model(cd.dm, cd.E_Pa, cd.nu);
    ProfileField thermal = make_thermal(cd);
    Mesh1D mesh = build_mesh_L3(Ri, Ri * cd.geom.outer_factor, cd.mesh.n_radial, cd.mesh.ratio);
    auto K = Assembler::assemble_K(mesh, elem, model);
    auto f = Assembler::assemble_neumann(mesh, cd.fluid_Pa, 0.0);
    auto sigma_geo = build_geostatic(mesh, elem, cd);
    std::vector<int> fixed_dofs = {mesh.n_nodes - 1};

    ImplicitAdaptiveOptions options;
    options.tol_local = 1.0e-10;
    options.tol_global = tol_global;
    options.dt_min_s = 1.0e-12 * 3600.0;
    options.dt_max_s = dt_max_h * 3600.0;

    ImplicitAdaptiveIntegrator integrator(mesh, elem, model, thermal,
                                          K, f, sigma_geo, fixed_dofs, options);
    const fs::path tmp = fs::temp_directory_path() / "saltcreep_test" / "implicit_adaptive";
    integrator.run(dt_h * 3600.0, total_h * 3600.0, 999999, tmp);
    return integrator.wall_closure_pct();
}

Stress make_deviatoric(double sigma_ef) {
    return Stress{2.0/3.0*sigma_ef, -1.0/3.0*sigma_ef, -1.0/3.0*sigma_ef, 0.0};
}
}

TEST_CASE("DM tangent: analytic tangent matches central finite difference",
          "[implicit][constitutive]") {
    CaseData cd = parse_case(find_tcc_case("modelo_A.yaml"));
    DoubleMechanism model(cd.dm, cd.E_Pa, cd.nu);
    Stress sigma = make_deviatoric(18.0e6);
    InternalState state;
    const double T = cd.thermal.T_K;

    Eigen::Matrix4d analytic = model.tangent(sigma, state, T);
    Eigen::Matrix4d numeric = Eigen::Matrix4d::Zero();
    for (int j = 0; j < 4; ++j) {
        const double h = std::max(1.0, std::abs(sigma[j])) * 1.0e-6;
        Stress sp = sigma;
        Stress sm = sigma;
        sp[j] += h;
        sm[j] -= h;
        const Strain rp = model.evaluate(sp, state, T, 0.0).strain_rate_voigt;
        const Strain rm = model.evaluate(sm, state, T, 0.0).strain_rate_voigt;
        numeric.col(j) = (rp - rm) / (2.0 * h);
    }
    REQUIRE((analytic - numeric).norm() / numeric.norm() < 1.0e-5);
}

TEST_CASE("Implicit adaptive: Modelo A smooth case matches explicit closure",
          "[implicit][equivalence]") {
    CaseData cd = parse_case(find_tcc_case("modelo_A.yaml"));
    const double explicit_closure = run_explicit(cd, 1.0, 0.002, 10);
    const double implicit_closure = run_implicit(cd, 1.0, 0.05, 10, 1.0e-5, 0.05);

    REQUIRE(std::isfinite(explicit_closure));
    REQUIRE(std::isfinite(implicit_closure));
    REQUIRE(std::abs(implicit_closure - explicit_closure) / std::abs(explicit_closure) < 0.01);
}

TEST_CASE("Implicit adaptive: closure converges as global tolerance tightens",
          "[implicit][convergence]") {
    CaseData cd = parse_case(find_tcc_case("modelo_A.yaml"));
    const double c1 = run_implicit(cd, 0.5, 0.1, 8, 1.0e-3, 0.1);
    const double c2 = run_implicit(cd, 0.5, 0.1, 8, 1.0e-4, 0.1);
    const double c3 = run_implicit(cd, 0.5, 0.1, 8, 1.0e-5, 0.1);

    REQUIRE(std::isfinite(c1));
    REQUIRE(std::isfinite(c2));
    REQUIRE(std::isfinite(c3));
    REQUIRE(std::abs(c2 - c3) <= std::abs(c1 - c2));
}

TEST_CASE("Implicit adaptive: severe taquidrita case converges with finite closure",
          "[implicit][severe]") {
    CaseData cd = parse_case(find_tcc_case("modelo_E.yaml"));
    cd.k0 = 1.5;
    const double closure = run_implicit(cd, 0.02, 0.002, 8, 1.0e-4, 0.002);

    REQUIRE(std::isfinite(closure));
    REQUIRE(std::abs(closure) < 200.0);
}
