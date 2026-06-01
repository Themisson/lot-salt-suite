#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <cmath>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <vector>

#include "constitutive/double_mechanism.hpp"
#include "constitutive/wang_2004.hpp"
#include "elements/axisym_1d_L3.hpp"
#include "io/CaseParser.hpp"
#include "solver/Assembler.hpp"
#include "solver/ImplicitAdaptiveIntegrator.hpp"
#include "thermal/profile_field.hpp"

namespace {
namespace fs = std::filesystem;

fs::path find_case(const std::string& relative) {
    for (const auto& root : {fs::path("."), fs::path(".."), fs::path("../..")}) {
        const fs::path candidate = root / relative;
        if (fs::exists(candidate))
            return candidate;
    }
    throw std::runtime_error("Cannot find case file: " + relative);
}

Stress make_deviatoric(double sigma_ef) {
    return Stress{2.0/3.0*sigma_ef, -1.0/3.0*sigma_ef, -1.0/3.0*sigma_ef, 0.0};
}

std::vector<Stress> build_geostatic(const Mesh& mesh, const Element& elem, const CaseData& cd) {
    const double depth = cd.depths.burial_m + cd.depths.water_depth_m + cd.depths.salt_above_m;
    const double sigma_v = -cd.overburden_grad_Pa_per_m * depth;
    const double sigma_h = cd.k0 * sigma_v;
    const int total_gp = mesh.n_elements * static_cast<int>(elem.gauss_points().size());
    return std::vector<Stress>(total_gp, Stress{sigma_h, sigma_h, sigma_v, 0.0});
}

double run_wang_case(const CaseData& cd) {
    AxisymL3 elem;
    Wang2004 model(cd.dm, cd.wang_2004, cd.E_Pa, cd.nu);
    ProfileField thermal = ProfileField::make_constant(cd.thermal.T_K);
    Mesh1D mesh = build_mesh_L3(cd.geom.Ri, cd.geom.Ri * cd.geom.outer_factor,
                                cd.mesh.n_radial, cd.mesh.ratio);
    auto K = Assembler::assemble_K(mesh, elem, model);
    auto f = Assembler::assemble_neumann(mesh, cd.fluid_Pa, 0.0);
    auto sigma_geo = build_geostatic(mesh, elem, cd);
    std::vector<int> fixed_dofs = {mesh.n_nodes - 1};

    ImplicitAdaptiveOptions options;
    options.tol_local = 1.0e-10;
    options.tol_global = cd.time.tol_global;
    options.dt_min_s = cd.time.dt_min_s;
    options.dt_max_s = cd.time.dt_max_s;

    ImplicitAdaptiveIntegrator integrator(mesh, elem, model, thermal,
                                          K, f, sigma_geo, fixed_dofs, options);
    const fs::path out = fs::temp_directory_path() / "saltcreep_test" / "wang_2004_case";
    integrator.run(cd.time.dt_s, cd.time.total_s, 999999, out);
    return integrator.wall_closure_pct();
}
} // namespace

TEST_CASE("Wang2004: D=0 with no evolution reduces exactly to DM rate",
          "[wang][regression]") {
    CaseData cd = parse_case(find_case("cases/tcc/modelo_A.yaml"));
    cd.wang_2004.A_d = 0.0;
    Wang2004 wang(cd.dm, cd.wang_2004, cd.E_Pa, cd.nu);
    DoubleMechanism dm(cd.dm, cd.E_Pa, cd.nu);

    Stress sigma = make_deviatoric(20.0e6);
    InternalState state;

    const auto wang_result = wang.evaluate(sigma, state, cd.thermal.T_K, 1000.0);
    const auto dm_result = dm.evaluate(sigma, state, cd.thermal.T_K, 1000.0);

    REQUIRE((wang_result.strain_rate_voigt - dm_result.strain_rate_voigt).norm()
            == Catch::Approx(0.0).margin(1.0e-30));
    REQUIRE(wang_result.updated_state.damage_D == Catch::Approx(0.0).margin(1.0e-30));
}

TEST_CASE("Wang2004: damage is monotone under constant deviatoric stress",
          "[wang][damage]") {
    CaseData cd = parse_case(find_case("cases/tcc/modelo_A.yaml"));
    cd.wang_2004.A_d = 1.0e-24;
    Wang2004 wang(cd.dm, cd.wang_2004, cd.E_Pa, cd.nu);
    Stress sigma = make_deviatoric(10.0e6);
    InternalState state;

    for (int i = 0; i < 100; ++i) {
        const double before = state.damage_D;
        state = wang.evaluate(sigma, state, cd.thermal.T_K, 1.0).updated_state;
        REQUIRE(state.damage_D >= before);
    }
    REQUIRE(state.damage_D > 0.0);
}

TEST_CASE("Wang2004: damage clamps at D_max and never reaches one",
          "[wang][damage]") {
    CaseData cd = parse_case(find_case("cases/tcc/modelo_A.yaml"));
    Wang2004 wang(cd.dm, cd.wang_2004, cd.E_Pa, cd.nu);
    Stress sigma = make_deviatoric(20.0e6);
    InternalState state;

    state = wang.evaluate(sigma, state, cd.thermal.T_K, 1.0).updated_state;

    REQUIRE(state.damage_D == Catch::Approx(cd.wang_2004.D_max));
    REQUIRE(state.damage_D < 1.0);
}

TEST_CASE("Wang2004: closure matches DM when damage coefficient is zero",
          "[wang][closure]") {
    CaseData cd = parse_case(find_case("cases/sestsal/caso_wang.yaml"));
    CaseData dm_cd = cd;
    cd.wang_2004.A_d = 0.0;
    dm_cd.creep.tertiary = false;
    dm_cd.creep.damage = false;

    const double wang_closure = run_wang_case(cd);
    AxisymL3 elem;
    DoubleMechanism dm(dm_cd.dm, dm_cd.E_Pa, dm_cd.nu);
    ProfileField thermal = ProfileField::make_constant(dm_cd.thermal.T_K);
    Mesh1D mesh = build_mesh_L3(dm_cd.geom.Ri, dm_cd.geom.Ri * dm_cd.geom.outer_factor,
                                dm_cd.mesh.n_radial, dm_cd.mesh.ratio);
    auto K = Assembler::assemble_K(mesh, elem, dm);
    auto f = Assembler::assemble_neumann(mesh, dm_cd.fluid_Pa, 0.0);
    auto sigma_geo = build_geostatic(mesh, elem, dm_cd);
    ImplicitAdaptiveIntegrator integrator(mesh, elem, dm, thermal, K, f, sigma_geo,
                                          std::vector<int>{mesh.n_nodes - 1});
    const fs::path out = fs::temp_directory_path() / "saltcreep_test" / "wang_dm_closure";
    integrator.run(dm_cd.time.dt_s, dm_cd.time.total_s, 999999, out);

    REQUIRE(wang_closure == Catch::Approx(integrator.wall_closure_pct()).margin(1.0e-10));
}

TEST_CASE("Wang2004: caso_wang regression stays within SESTSAL oracle tolerance",
          "[wang][sestsal]") {
    CaseData cd = parse_case(find_case("cases/sestsal/caso_wang.yaml"));
    const double closure = run_wang_case(cd);
    // No external SESTSAL oracle for Wang exists in the repo yet; this guards the
    // verified CLI regression case and keeps the ±5% acceptance envelope in place.
    constexpr double oracle_closure_pct = 0.115626;

    REQUIRE(std::isfinite(closure));
    REQUIRE(oracle_closure_pct > 0.0);
    REQUIRE(std::abs(closure - oracle_closure_pct) / oracle_closure_pct < 0.05);
}
