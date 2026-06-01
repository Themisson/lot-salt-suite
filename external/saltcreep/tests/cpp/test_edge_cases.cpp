#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <cmath>
#include <filesystem>
#include <fstream>
#include <type_traits>

#include "constitutive/ConstitutiveModel.hpp"
#include "constitutive/aubertin_isv_sh_d.hpp"
#include "constitutive/double_mechanism.hpp"
#include "constitutive/edmt.hpp"
#include "constitutive/isv_sh_dm.hpp"
#include "constitutive/motta_v1.hpp"
#include "constitutive/wang_2004.hpp"
#include "elements/Element.hpp"
#include "elements/axisym_1d_L3.hpp"
#include "elements/axisym_2d_aq9.hpp"
#include "io/CaseParser.hpp"
#include "mesh/error_estimator.hpp"
#include "solver/Assembler.hpp"
#include "solver/ElasticSolver.hpp"
#include "thermal/ThermalField.hpp"

namespace {
DMParams halita_dm() {
    DMParams p;
    p.e0_s = 5.5556e-10;
    p.sig0 = 9.762e6;
    p.T0 = 359.15;
    p.n1 = 3.223;
    p.n2 = 7.562;
    p.Q_over_R = 50208.0 / 8.314;
    return p;
}

Stress deviatoric_stress(double sigma_ef) {
    return Stress{2.0 / 3.0 * sigma_ef,
                  -1.0 / 3.0 * sigma_ef,
                  -1.0 / 3.0 * sigma_ef,
                  0.0};
}

bool finite_vec(const Eigen::Vector4d& v) {
    return v.array().isFinite().all();
}

std::filesystem::path find_data_dir() {
    for (const auto& candidate : {
             std::filesystem::path("data"),
             std::filesystem::path("../data"),
             std::filesystem::path("../../data")}) {
        if (std::filesystem::exists(candidate / "litologias"))
            return candidate;
    }
    throw std::runtime_error("Cannot find data/litologias");
}
} // namespace

TEST_CASE("Base interfaces have virtual destructors", "[edge][raii]") {
    REQUIRE(std::has_virtual_destructor_v<Element>);
    REQUIRE(std::has_virtual_destructor_v<ConstitutiveModel>);
    REQUIRE(std::has_virtual_destructor_v<ThermalField>);
}

TEST_CASE("CreepModel: zero stress produces zero finite rate", "[edge][constitutive]") {
    DoubleMechanism dm(halita_dm(), 20.4e9, 0.36);
    InternalState state;

    auto result = dm.evaluate(Stress::Zero(), state, 359.15, 3600.0);

    REQUIRE(finite_vec(result.strain_rate_voigt));
    REQUIRE(result.strain_rate_voigt.norm() == Catch::Approx(0.0).margin(1.0e-30));
}

TEST_CASE("Arrhenius: extreme temperatures stay finite", "[edge][constitutive]") {
    DoubleMechanism dm(halita_dm(), 20.4e9, 0.36);
    InternalState state;
    const Stress sigma = deviatoric_stress(halita_dm().sig0);

    const auto cold = dm.evaluate(sigma, state, 0.1, 1.0);
    const auto hot = dm.evaluate(sigma, state, 1000.0, 1.0);

    REQUIRE(finite_vec(cold.strain_rate_voigt));
    REQUIRE(finite_vec(hot.strain_rate_voigt));
    REQUIRE(cold.strain_rate_voigt.norm() <= hot.strain_rate_voigt.norm());
}

TEST_CASE("EDMT: saturated primary strain returns to DM", "[edge][constitutive]") {
    const DMParams dm_params = halita_dm();
    EdmtParams edmt;
    edmt.K1 = 2.0;
    edmt.K2 = 3.0;
    DoubleMechanism dm(dm_params, 20.4e9, 0.36);
    EDMT edmt_model(dm_params, edmt, 20.4e9, 0.36, true);

    InternalState saturated;
    saturated.eps_v_eff = 1.0e6;
    const Stress sigma = deviatoric_stress(2.0 * dm_params.sig0);

    const auto dm_rate = dm.evaluate(sigma, saturated, dm_params.T0, 1.0).strain_rate_voigt;
    const auto edmt_rate = edmt_model.evaluate(sigma, saturated, dm_params.T0, 1.0).strain_rate_voigt;

    REQUIRE(finite_vec(edmt_rate));
    REQUIRE((edmt_rate - dm_rate).norm() == Catch::Approx(0.0).margin(1.0e-18));
}

TEST_CASE("Damage: Motta near D_max stays finite and clamps", "[edge][damage]") {
    MottaV1Params params;
    params.A_d = 1.0e-24;
    params.D_max = 0.99;
    SpierParams spier;
    spier.a = 0.0;
    spier.b_Pa = 0.0;
    MottaV1 model(halita_dm(), params, spier, 20.4e9, 0.36);

    InternalState state;
    state.damage_D = 0.985;
    const Stress sigma = deviatoric_stress(3.0 * halita_dm().sig0);
    const auto result = model.evaluate(sigma, state, halita_dm().T0, 3600.0);

    REQUIRE(finite_vec(result.strain_rate_voigt));
    REQUIRE(result.updated_state.damage_D >= state.damage_D);
    REQUIRE(result.updated_state.damage_D <= params.D_max);
}

TEST_CASE("Damage: Wang near D_max stays finite and below one", "[edge][damage]") {
    Wang2004Params params;
    params.A_d = 1.0e-24;
    params.D_max = 0.99;
    Wang2004 model(halita_dm(), params, 20.4e9, 0.36);

    InternalState state;
    state.damage_D = 0.985;
    const Stress sigma = deviatoric_stress(2.0 * halita_dm().sig0);
    const auto result = model.evaluate(sigma, state, halita_dm().T0, 3600.0);

    REQUIRE(finite_vec(result.strain_rate_voigt));
    REQUIRE(result.updated_state.damage_D >= state.damage_D);
    REQUIRE(result.updated_state.damage_D <= params.D_max);
}

TEST_CASE("ISV_SH_DM: very large primary strain hardens to finite secondary rate",
          "[edge][constitutive]") {
    ISVSHDMunsonParams params;
    ISVSHDMunson model(halita_dm(), params, 20.4e9, 0.36, true);
    InternalState state;
    state.eps_v_primary = 1.0e6;
    const Stress sigma = deviatoric_stress(halita_dm().sig0);

    const auto result = model.evaluate(sigma, state, halita_dm().T0, 3600.0);

    REQUIRE(finite_vec(result.strain_rate_voigt));
    REQUIRE(result.updated_state.eps_v_primary >= state.eps_v_primary);
    REQUIRE(result.updated_state.f_hard >= 0.0);
}

TEST_CASE("AQ9: one element keeps finite B matrices and positive weights", "[edge][element]") {
    AxisymAQ9 elem;
    Mesh2D mesh = build_mesh_structured_2d("axisym_2d_AQ9", 1.0, 3.0, 1.0, 1, 1, 1.0);
    std::vector<Node> coords(elem.n_nodes());
    for (int i = 0; i < elem.n_nodes(); ++i)
        coords[i] = mesh.nodes[mesh.elem_nodes[i]];

    for (const auto& gp : elem.gauss_points()) {
        const auto B = elem.B_matrix(gp, coords);
        REQUIRE(B.array().isFinite().all());
        REQUIRE(elem.jacobian_weight(gp, coords) > 0.0);
    }
}

TEST_CASE("Mesh: single L3 element assembles and solves finite displacement",
          "[edge][mesh]") {
    Mesh1D mesh = build_mesh_L3(1.0, 2.0, 1, 1.0);
    DoubleMechanism model(halita_dm(), 20.4e9, 0.36);
    AxisymL3 elem;

    auto K = Assembler::assemble_K(mesh, elem, model);
    auto f = Assembler::assemble_neumann(mesh, 1.0e6, 0.0);
    ElasticSolver solver;
    auto result = solver.solve(K, f, {mesh.n_nodes - 1});

    REQUIRE(result.u.size() == mesh.total_dofs());
    REQUIRE(result.u.array().isFinite().all());
}

TEST_CASE("Parser: max_refinement_levels zero is accepted", "[edge][parser]") {
    const auto dir = std::filesystem::temp_directory_path() / "saltcreep_edge_parser";
    std::filesystem::create_directories(dir);
    const auto yaml = dir / "case.yaml";
    std::ofstream out(yaml);
    out << R"yaml(
name: edge_parser
geometry:
  well_radius_m: 0.155575
  outer_radius_factor: 10
depths:
  water_depth_m: 1000
  burial_m: 2000
lithology:
  primary: halita
fluid:
  weight_lb_per_gal: 10
stress:
  k0: 1.0
element:
  type: axisym_2d_Q4
mesh:
  n_elements_radial: 2
  n_elements_axial: 1
  ratio: 1
  adaptive: true
  max_refinement_levels: 0
creep:
  elastic_only: true
thermal:
  mode: profile
time:
  total_h: 1
  dt_h: 1
)yaml";
    out.close();

    const CaseData cd = parse_case(yaml, find_data_dir());
    REQUIRE(cd.mesh.adaptive);
    REQUIRE(cd.mesh.max_refinement_levels == 0);
}
