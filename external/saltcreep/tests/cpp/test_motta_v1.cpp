#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>
#include <algorithm>
#include <cmath>
#include <filesystem>
#include <stdexcept>
#include <vector>

#include "constitutive/double_mechanism.hpp"
#include "constitutive/motta_v1.hpp"
#include "elements/axisym_1d_L3.hpp"
#include "io/CaseParser.hpp"
#include "solver/Assembler.hpp"
#include "solver/ImplicitAdaptiveIntegrator.hpp"
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

Stress make_deviatoric(double sigma_ef) {
    return Stress{2.0/3.0*sigma_ef, -1.0/3.0*sigma_ef, -1.0/3.0*sigma_ef, 0.0};
}

MottaV1Params motta_params(double A_d = 1.0e-11) {
    MottaV1Params p;
    p.n_d = 2.0;
    p.A_d = A_d;
    p.m_d = 1.0;
    p.p_d = 0.0;
    p.D_max = 0.99;
    return p;
}

SpierParams active_spier() {
    SpierParams p;
    p.a = 0.0;
    p.b_Pa = 0.0;
    return p;
}

ProfileField make_thermal(const CaseData& cd) {
    return (cd.thermal.mode == "profile")
        ? ProfileField::make_profile(cd.thermal.seabed_temp_C,
                                     cd.depths.burial_m + cd.depths.water_depth_m,
                                     cd.thermal.grad_C_per_m)
        : ProfileField::make_constant(cd.thermal.T_K);
}

std::vector<Stress> build_geostatic(const Mesh& mesh, const Element& elem, const CaseData& cd) {
    const double depth = cd.depths.burial_m + cd.depths.water_depth_m + cd.depths.salt_above_m;
    const double sigma_v = -cd.overburden_grad_Pa_per_m * depth;
    const double sigma_h = cd.k0 * sigma_v;
    const int total_gp = mesh.n_elements * static_cast<int>(elem.gauss_points().size());
    return std::vector<Stress>(total_gp, Stress{sigma_h, sigma_h, sigma_v, 0.0});
}
}

TEST_CASE("MottaV1 Spier: code uses tension-positive stress, compression negative",
          "[motta][spier][sign]") {
    CaseData cd = parse_case(find_tcc_case("modelo_A.yaml"));
    MottaV1 model(cd.dm, motta_params(), SpierParams{0.25, 0.0}, cd.E_Pa, cd.nu);

    // Modelo A geostatic stress is hydrostatic compression in the code:
    // sigma_geo = [-119.7, -119.7, -119.7, 0] MPa.
    Stress sigma_geo{-119.7e6, -119.7e6, -119.7e6, 0.0};
    REQUIRE(model.dilatancy_value(sigma_geo) < 0.0);
}

TEST_CASE("MottaV1: D=0 below dilatancy gives exactly DM rate",
          "[motta][regression]") {
    CaseData cd = parse_case(find_tcc_case("modelo_A.yaml"));
    SpierParams safe_envelope{0.0, 100.0e6};
    MottaV1 motta(cd.dm, motta_params(), safe_envelope, cd.E_Pa, cd.nu);
    DoubleMechanism dm(cd.dm, cd.E_Pa, cd.nu);

    Stress sigma = make_deviatoric(20.0e6);
    InternalState state;
    const double T = cd.thermal.T_K;

    auto motta_result = motta.evaluate(sigma, state, T, 1000.0);
    auto dm_result = dm.evaluate(sigma, state, T, 1000.0);

    REQUIRE((motta_result.strain_rate_voigt - dm_result.strain_rate_voigt).norm()
            == Catch::Approx(0.0).margin(1.0e-30));
    REQUIRE(motta_result.updated_state.damage_D == Catch::Approx(0.0).margin(1.0e-30));
}

TEST_CASE("MottaV1: damage does not evolve below Spier envelope",
          "[motta][damage]") {
    CaseData cd = parse_case(find_tcc_case("modelo_A.yaml"));
    MottaV1 motta(cd.dm, motta_params(), SpierParams{0.0, 100.0e6}, cd.E_Pa, cd.nu);
    Stress sigma = make_deviatoric(20.0e6);
    InternalState state;

    for (int i = 0; i < 100; ++i) {
        state = motta.evaluate(sigma, state, cd.thermal.T_K, 1000.0).updated_state;
        REQUIRE(state.damage_D == Catch::Approx(0.0).margin(1.0e-30));
    }
}

TEST_CASE("MottaV1: damage is monotone above Spier envelope",
          "[motta][damage]") {
    CaseData cd = parse_case(find_tcc_case("modelo_A.yaml"));
    MottaV1 motta(cd.dm, motta_params(), active_spier(), cd.E_Pa, cd.nu);
    Stress sigma = make_deviatoric(20.0e6);
    InternalState state;

    for (int i = 0; i < 1000; ++i) {
        const double before = state.damage_D;
        state = motta.evaluate(sigma, state, cd.thermal.T_K, 1.0).updated_state;
        REQUIRE(state.damage_D >= before);
    }
    REQUIRE(state.damage_D > 0.0);
}

TEST_CASE("MottaV1: damage saturates below one at D_max",
          "[motta][damage]") {
    CaseData cd = parse_case(find_tcc_case("modelo_A.yaml"));
    MottaV1 motta(cd.dm, motta_params(1.0e-5), active_spier(), cd.E_Pa, cd.nu);
    Stress sigma = make_deviatoric(100.0e6);
    InternalState state;

    for (int i = 0; i < 1000; ++i)
        state = motta.evaluate(sigma, state, cd.thermal.T_K, 1000.0).updated_state;

    REQUIRE(state.damage_D == Catch::Approx(0.99));
    REQUIRE(state.damage_D < 1.0);
}

TEST_CASE("MottaV1: tertiary rate accelerates as damage grows",
          "[motta][damage]") {
    CaseData cd = parse_case(find_tcc_case("modelo_A.yaml"));
    MottaV1 motta(cd.dm, motta_params(1.0e-10), active_spier(), cd.E_Pa, cd.nu);
    Stress sigma = make_deviatoric(20.0e6);
    InternalState state;

    const double initial_rate = motta.evaluate(sigma, state, cd.thermal.T_K, 1.0)
        .strain_rate_voigt.norm();
    for (int i = 0; i < 100; ++i)
        state = motta.evaluate(sigma, state, cd.thermal.T_K, 10.0).updated_state;
    const double final_rate = motta.evaluate(sigma, state, cd.thermal.T_K, 1.0)
        .strain_rate_voigt.norm();

    REQUIRE(state.damage_D > 0.0);
    REQUIRE(final_rate > initial_rate);
}

TEST_CASE("MottaV1: simplified analytic tangent matches finite difference at fixed damage",
          "[motta][tangent]") {
    CaseData cd = parse_case(find_tcc_case("modelo_A.yaml"));
    MottaV1 motta(cd.dm, motta_params(), active_spier(), cd.E_Pa, cd.nu);
    Stress sigma = make_deviatoric(20.0e6);
    InternalState state;
    state.damage_D = 0.2;

    Eigen::Matrix4d analytic = motta.tangent(sigma, state, cd.thermal.T_K);
    Eigen::Matrix4d numeric = Eigen::Matrix4d::Zero();
    for (int j = 0; j < 4; ++j) {
        const double h = std::max(1.0, std::abs(sigma[j])) * 1.0e-6;
        Stress sp = sigma;
        Stress sm = sigma;
        sp[j] += h;
        sm[j] -= h;
        const Strain rp = motta.evaluate(sp, state, cd.thermal.T_K, 0.0).strain_rate_voigt;
        const Strain rm = motta.evaluate(sm, state, cd.thermal.T_K, 0.0).strain_rate_voigt;
        numeric.col(j) = (rp - rm) / (2.0 * h);
    }

    REQUIRE((analytic - numeric).norm() / numeric.norm() < 1.0e-5);
}

TEST_CASE("MottaV1: severe implicit adaptive case converges with finite closure",
          "[motta][implicit][severe]") {
    CaseData cd = parse_case(find_tcc_case("modelo_E.yaml"));
    cd.k0 = 1.5;
    cd.mesh.n_radial = 6;
    cd.mesh.ratio = 50.0;

    AxisymL3 elem;
    MottaV1 model(cd.dm, motta_params(1.0e-13), active_spier(), cd.E_Pa, cd.nu);
    ProfileField thermal = make_thermal(cd);
    Mesh1D mesh = build_mesh_L3(cd.geom.Ri, cd.geom.Ri * cd.geom.outer_factor,
                                cd.mesh.n_radial, cd.mesh.ratio);
    auto K = Assembler::assemble_K(mesh, elem, model);
    auto f = Assembler::assemble_neumann(mesh, cd.fluid_Pa, 0.0);
    auto sigma_geo = build_geostatic(mesh, elem, cd);
    std::vector<int> fixed_dofs = {mesh.n_nodes - 1};

    ImplicitAdaptiveOptions options;
    options.tol_local = 1.0e-10;
    options.tol_global = 1.0e-4;
    options.dt_min_s = 1.0e-12 * 3600.0;
    options.dt_max_s = 0.001 * 3600.0;

    ImplicitAdaptiveIntegrator integrator(mesh, elem, model, thermal,
                                          K, f, sigma_geo, fixed_dofs, options);
    const fs::path tmp = fs::temp_directory_path() / "saltcreep_test" / "motta_severe";
    integrator.run(0.001 * 3600.0, 0.005 * 3600.0, 999999, tmp);

    const double closure = integrator.wall_closure_pct();
    REQUIRE(std::isfinite(closure));
    REQUIRE(std::abs(closure) < 200.0);
}
