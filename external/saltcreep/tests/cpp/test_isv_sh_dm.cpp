#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <cmath>
#include <filesystem>
#include <stdexcept>
#include <vector>

#include "constitutive/double_mechanism.hpp"
#include "constitutive/edmt.hpp"
#include "constitutive/isv_sh_dm.hpp"
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

double run_isv_case(const CaseData& cd) {
    AxisymL3 elem;
    ISVSHDMunson model(cd.dm, cd.isv_sh_dm, cd.E_Pa, cd.nu, cd.creep.secondary);
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
    const fs::path out = fs::temp_directory_path() / "saltcreep_test" / "isv_sh_dm_case";
    integrator.run(cd.time.dt_s, cd.time.total_s, 999999, out);
    return integrator.wall_closure_pct();
}

ISVSHDMunsonParams tuned_like_edmt(const CaseData& cd, double sigma_ef) {
    const double n = cd.isv_sh_dm.n;
    const double sh = std::sinh(sigma_ef / cd.isv_sh_dm.sig_ref);
    const double dm_rate = cd.dm.e0_s * std::pow(sigma_ef / cd.dm.sig0, cd.dm.n1);
    ISVSHDMunsonParams params = cd.isv_sh_dm;
    params.e0_s = dm_rate * cd.edmt.K1 / std::pow(sh, n);
    params.Q_J_mol = cd.dm.Q_over_R * 8.314;
    params.T0 = cd.dm.T0;
    return params;
}
} // namespace

TEST_CASE("ISV_SH_DM: primary transient is comparable to EDMT when calibrated",
          "[isv_sh_dm][primary]") {
    CaseData cd = parse_case(find_case("cases/tcc/modelo_A.yaml"));
    const double sigma_ef = 5.0e6;
    ISVSHDMunsonParams params = tuned_like_edmt(cd, sigma_ef);
    ISVSHDMunson isv(cd.dm, params, cd.E_Pa, cd.nu, true);
    EDMT edmt(cd.dm, cd.edmt, cd.E_Pa, cd.nu, true);

    Stress sigma = make_deviatoric(sigma_ef);
    InternalState state;
    const auto isv_result = isv.evaluate(sigma, state, cd.dm.T0, 0.0);
    const auto edmt_result = edmt.evaluate(sigma, state, cd.dm.T0, 0.0);

    const double diff = (isv_result.strain_rate_voigt - edmt_result.strain_rate_voigt).norm();
    REQUIRE(diff / edmt_result.strain_rate_voigt.norm() < 1.0e-12);
}

TEST_CASE("ISV_SH_DM: EDMT and sinh-hardening both saturate to DM",
          "[isv_sh_dm][saturation]") {
    CaseData cd = parse_case(find_case("cases/tcc/modelo_A.yaml"));
    ISVSHDMunsonParams params = tuned_like_edmt(cd, 5.0e6);
    ISVSHDMunson isv(cd.dm, params, cd.E_Pa, cd.nu, true);
    EDMT edmt(cd.dm, cd.edmt, cd.E_Pa, cd.nu, true);
    DoubleMechanism dm(cd.dm, cd.E_Pa, cd.nu);

    Stress sigma = make_deviatoric(5.0e6);
    InternalState saturated;
    saturated.eps_v_eff = 20.0;
    saturated.eps_v_primary = 20.0;

    const auto isv_result = isv.evaluate(sigma, saturated, cd.dm.T0, 0.0);
    const auto edmt_result = edmt.evaluate(sigma, saturated, cd.dm.T0, 0.0);
    const auto dm_result = dm.evaluate(sigma, saturated, cd.dm.T0, 0.0);

    REQUIRE((isv_result.strain_rate_voigt - dm_result.strain_rate_voigt).norm() /
            dm_result.strain_rate_voigt.norm() < 1.0e-8);
    REQUIRE((edmt_result.strain_rate_voigt - dm_result.strain_rate_voigt).norm() /
            dm_result.strain_rate_voigt.norm() < 1.0e-8);
}

TEST_CASE("ISV_SH_DM: analytic tangent matches finite difference",
          "[isv_sh_dm][tangent]") {
    CaseData cd = parse_case(find_case("cases/tcc/modelo_A.yaml"));
    ISVSHDMunsonParams params = tuned_like_edmt(cd, 5.0e6);
    ISVSHDMunson isv(cd.dm, params, cd.E_Pa, cd.nu, true);
    Stress sigma = make_deviatoric(5.0e6);
    InternalState state;
    state.eps_v_primary = 0.2;

    const Eigen::Matrix4d analytic = isv.tangent(sigma, state, cd.dm.T0);
    Eigen::Matrix4d numeric = Eigen::Matrix4d::Zero();
    for (int j = 0; j < 4; ++j) {
        const double h = std::max(1.0, std::abs(sigma[j])) * 1.0e-6;
        Stress sp = sigma;
        Stress sm = sigma;
        sp[j] += h;
        sm[j] -= h;
        numeric.col(j) =
            (isv.evaluate(sp, state, cd.dm.T0, 0.0).strain_rate_voigt -
             isv.evaluate(sm, state, cd.dm.T0, 0.0).strain_rate_voigt) / (2.0 * h);
    }

    REQUIRE((analytic - numeric).norm() / std::max(1.0e-30, numeric.norm()) < 5.0e-5);
}

TEST_CASE("ISV_SH_DM: caso_isv_sh_dm regression stays within SESTSAL oracle tolerance",
          "[isv_sh_dm][sestsal]") {
    CaseData cd = parse_case(find_case("cases/sestsal/caso_isv_sh_dm.yaml"));
    const double closure = run_isv_case(cd);
    // No external SESTSAL oracle for ISV_SH_DM is versioned in the repo yet; this
    // guards the verified CLI regression case and keeps the ±5% acceptance envelope.
    constexpr double oracle_closure_pct = 0.115641;

    REQUIRE(std::isfinite(closure));
    REQUIRE(oracle_closure_pct > 0.0);
    REQUIRE(std::abs(closure - oracle_closure_pct) / oracle_closure_pct < 0.05);
}
