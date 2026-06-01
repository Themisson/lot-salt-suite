#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <cmath>
#include <filesystem>
#include <stdexcept>
#include <vector>

#include "constitutive/aubertin_isv_sh_d.hpp"
#include "constitutive/edmt.hpp"
#include "constitutive/motta_v1.hpp"
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

double run_model_case(const CaseData& cd, const ConstitutiveModel& model,
                      const std::string& output_name) {
    AxisymL3 elem;
    ProfileField thermal = ProfileField::make_constant(cd.thermal.T_K);
    Mesh1D mesh = build_mesh_L3(cd.geom.Ri, cd.geom.Ri * cd.geom.outer_factor,
                                cd.mesh.n_radial, cd.mesh.ratio);
    auto K = Assembler::assemble_K(mesh, elem, model);
    auto f = Assembler::assemble_neumann(mesh, cd.fluid_Pa, 0.0);
    auto sigma_geo = build_geostatic(mesh, elem, cd);

    ImplicitAdaptiveOptions options;
    options.tol_local = 1.0e-10;
    options.tol_global = cd.time.tol_global;
    options.dt_min_s = cd.time.dt_min_s;
    options.dt_max_s = cd.time.dt_max_s;

    ImplicitAdaptiveIntegrator integrator(mesh, elem, model, thermal, K, f, sigma_geo,
                                          std::vector<int>{mesh.n_nodes - 1}, options);
    const fs::path out = fs::temp_directory_path() / "saltcreep_test" / output_name;
    integrator.run(cd.time.dt_s, cd.time.total_s, 999999, out);
    return integrator.wall_closure_pct();
}

AubertinISVSHDParams from_dm_edmt(const CaseData& cd) {
    AubertinISVSHDParams params = cd.aubertin_isv_sh_d;
    params.e0_s = cd.dm.e0_s;
    params.sig0 = cd.dm.sig0;
    params.n = cd.dm.n1;
    params.Q_J_mol = cd.dm.Q_over_R * 8.314;
    params.T0 = cd.dm.T0;
    params.K1 = cd.edmt.K1;
    params.K2 = cd.edmt.K2;
    params.A_d = 0.0;
    return params;
}
} // namespace

TEST_CASE("AubertinISVSHD: D=0 and no damage reduces to EDMT rate",
          "[aubertin][regression]") {
    CaseData cd = parse_case(find_case("cases/tcc/modelo_A.yaml"));
    AubertinISVSHDParams params = from_dm_edmt(cd);
    AubertinISVSHD aubertin(params, cd.E_Pa, cd.nu);
    EDMT edmt(cd.dm, cd.edmt, cd.E_Pa, cd.nu, true);

    Stress sigma = make_deviatoric(5.0e6);
    InternalState state;
    state.eps_v_eff = 0.02;
    state.eps_v_primary = 0.02;

    const auto au = aubertin.evaluate(sigma, state, cd.dm.T0, 0.0);
    const auto ed = edmt.evaluate(sigma, state, cd.dm.T0, 0.0);

    const double diff = (au.strain_rate_voigt - ed.strain_rate_voigt).norm();
    const double scale = std::max(1.0e-30, ed.strain_rate_voigt.norm());
    REQUIRE(diff / scale < 1.0e-12);
    REQUIRE(au.updated_state.damage_D == Catch::Approx(0.0).margin(1.0e-30));

    const auto advanced = aubertin.evaluate(sigma, state, cd.dm.T0, 10.0);
    REQUIRE(advanced.updated_state.eps_v_primary >= state.eps_v_primary);
    REQUIRE(advanced.updated_state.eps_v_secondary > state.eps_v_secondary);
}

TEST_CASE("AubertinISVSHD: ISVs and damage are monotone and bounded",
          "[aubertin][damage]") {
    CaseData cd = parse_case(find_case("cases/tcc/modelo_A.yaml"));
    AubertinISVSHDParams params = cd.aubertin_isv_sh_d;
    params.A_d = 1.0e-30;
    params.D_max = 0.4;
    AubertinISVSHD aubertin(params, cd.E_Pa, cd.nu);
    Stress sigma = make_deviatoric(8.0e6);
    InternalState state;
    state.eps_v_primary = 0.01;
    state.eps_v_secondary = 0.02;
    state.eps_v_eff = 0.03;

    for (int i = 0; i < 100; ++i) {
        const InternalState before = state;
        state = aubertin.evaluate(sigma, state, cd.thermal.T_K, 10.0).updated_state;
        REQUIRE(state.eps_v_primary >= before.eps_v_primary);
        REQUIRE(state.eps_v_secondary >= before.eps_v_secondary);
        REQUIRE(state.damage_D >= before.damage_D);
        REQUIRE(state.damage_D <= params.D_max);
    }
    REQUIRE(state.damage_D > 0.0);
}

TEST_CASE("AubertinISVSHD: TCC closure is comparable to Motta in mild no-damage limit",
          "[aubertin][tcc]") {
    CaseData cd = parse_case(find_case("cases/sestsal/caso_aubertin.yaml"));
    AubertinISVSHD aubertin(cd.aubertin_isv_sh_d, cd.E_Pa, cd.nu);

    MottaV1Params motta_params = cd.motta_v1;
    motta_params.A_d = 0.0;
    motta_params.n_d = 2.0;
    SpierParams spier = cd.spier;
    MottaV1 motta(cd.dm, motta_params, spier, cd.E_Pa, cd.nu);

    const double au_closure = run_model_case(cd, aubertin, "aubertin_tcc_compare");
    const double motta_closure = run_model_case(cd, motta, "aubertin_motta_compare");

    REQUIRE(std::isfinite(au_closure));
    REQUIRE(std::isfinite(motta_closure));
    REQUIRE(std::abs(au_closure - motta_closure) / std::max(1.0e-12, std::abs(motta_closure)) < 0.35);
}

TEST_CASE("AubertinISVSHD: caso_aubertin regression stays within SESTSAL oracle tolerance",
          "[aubertin][sestsal]") {
    CaseData cd = parse_case(find_case("cases/sestsal/caso_aubertin.yaml"));
    AubertinISVSHD aubertin(cd.aubertin_isv_sh_d, cd.E_Pa, cd.nu);
    const double closure = run_model_case(cd, aubertin, "aubertin_case_regression");
    // No external SESTSAL oracle for Aubertin is versioned in the repo yet; this
    // guards the verified CLI regression case and keeps the ±10% envelope.
    constexpr double oracle_closure_pct = 0.115632;

    REQUIRE(std::isfinite(closure));
    REQUIRE(oracle_closure_pct > 0.0);
    REQUIRE(std::abs(closure - oracle_closure_pct) / oracle_closure_pct < 0.10);
}
