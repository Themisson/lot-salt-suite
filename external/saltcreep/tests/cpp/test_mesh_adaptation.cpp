#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <algorithm>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <numeric>
#include <stdexcept>
#include <vector>

#include "constitutive/elastic_isotropic.hpp"
#include "elements/axisym_2d_aq9.hpp"
#include "elements/axisym_2d_q4.hpp"
#include "elements/axisym_2d_t3.hpp"
#include "io/CaseParser.hpp"
#include "mesh/error_estimator.hpp"
#include "mesh/mesh_refiner.hpp"
#include "solver/Assembler.hpp"

namespace fs = std::filesystem;

namespace {
fs::path find_data_dir() {
    for (const auto& candidate : {
             fs::path("data"),
             fs::path("../data"),
             fs::path("../../data")}) {
        if (fs::exists(candidate / "litologias"))
            return candidate;
    }
    throw std::runtime_error("Cannot find data/litologias");
}

double polygon_area(const Mesh& mesh, int e) {
    const int nne = mesh.nodes_per_element;
    double area2 = 0.0;
    for (int i = 0; i < nne; ++i) {
        const Node& a = mesh.nodes[mesh.elem_nodes[nne * e + i]];
        const Node& b = mesh.nodes[mesh.elem_nodes[nne * e + ((i + 1) % nne)]];
        area2 += a.r * b.z - b.r * a.z;
    }
    return 0.5 * std::abs(area2);
}

double total_area(const Mesh& mesh) {
    double out = 0.0;
    for (int e = 0; e < mesh.n_elements; ++e)
        out += polygon_area(mesh, e);
    return out;
}

TimeState make_constant_stress_state(const Mesh& mesh,
                                     const Element& elem,
                                     const Stress& sigma) {
    const int total_gp = mesh.n_elements *
        static_cast<int>(elem.gauss_points().size());
    TimeState state;
    state.u_total = Eigen::VectorXd::Zero(mesh.total_dofs());
    state.sigma_gp.assign(total_gp, sigma);
    state.eps_v_gp.assign(total_gp, Strain::Zero());
    state.eps_th_gp.assign(total_gp, Strain::Zero());
    state.state_gp.assign(total_gp, InternalState{});
    return state;
}

Eigen::VectorXd linear_displacement(const Mesh& mesh) {
    Eigen::VectorXd u(mesh.total_dofs());
    for (int n = 0; n < mesh.n_nodes; ++n) {
        const double r = mesh.nodes[n].r;
        const double z = mesh.nodes[n].z;
        u[mesh.dof_index(n, 0)] = 1.0 + 0.1 * r + 0.05 * z;
        u[mesh.dof_index(n, 1)] = -0.2 + 0.03 * r - 0.08 * z;
    }
    return u;
}
} // namespace

TEST_CASE("ErrorEstimator: AQ9 constant-stress field is not refined",
          "[adapt][zz][aq9]") {
    Mesh2D mesh = build_mesh_structured_2d("axisym_2d_AQ9", 1.0, 3.0, 1.0, 1, 1, 1.0);
    AxisymAQ9 elem;
    ElasticIsotropic model(20.0e9, 0.30);
    TimeState state = make_constant_stress_state(
        mesh, elem, Stress{1.0e6, 1.0e6, 1.0e6, 0.0});

    ErrorEstimator estimator;
    auto errors = estimator.compute_errors(mesh, elem, model, state);
    auto marked = estimator.mark_for_refinement(errors, ErrorEstimatorOptions{1.0e-12, -1.0});

    REQUIRE(errors.size() == 1);
    REQUIRE(errors[0].eta_rel == Catch::Approx(0.0).margin(1.0e-12));
    REQUIRE(std::none_of(marked.begin(), marked.end(), [](char v) { return v != 0; }));
}

TEST_CASE("ErrorEstimator: stress jump near an interface marks high-error elements",
          "[adapt][zz][interface]") {
    Mesh2D mesh = build_mesh_structured_2d("axisym_2d_Q4", 1.0, 3.0, 1.0, 2, 1, 1.0);
    AxisymQ4 elem;
    ElasticIsotropic model(20.0e9, 0.30);
    TimeState state = make_constant_stress_state(
        mesh, elem, Stress{1.0e6, 0.5e6, 0.25e6, 0.0});
    const int n_gp = static_cast<int>(elem.gauss_points().size());
    for (int g = 0; g < n_gp; ++g)
        state.sigma_gp[n_gp + g] = Stress{10.0e6, 2.0e6, 1.0e6, 0.0};

    ErrorEstimator estimator;
    auto errors = estimator.compute_errors(mesh, elem, model, state);
    auto marked = estimator.mark_for_refinement(errors, ErrorEstimatorOptions{0.01, -1.0});

    REQUIRE(errors.size() == 2);
    REQUIRE(std::any_of(marked.begin(), marked.end(), [](char v) { return v != 0; }));
}

TEST_CASE("ErrorEstimator: damage indicator marks elements above D threshold",
          "[adapt][damage]") {
    Mesh2D mesh = build_mesh_structured_2d("axisym_2d_Q4", 1.0, 2.0, 1.0, 1, 1, 1.0);
    AxisymQ4 elem;
    ElasticIsotropic model(20.0e9, 0.30);
    TimeState state = make_constant_stress_state(
        mesh, elem, Stress{1.0e6, 1.0e6, 1.0e6, 0.0});
    for (auto& gp_state : state.state_gp)
        gp_state.damage_D = 0.35;

    ErrorEstimator estimator;
    auto errors = estimator.compute_errors(mesh, elem, model, state);
    auto marked = estimator.mark_for_refinement(errors, ErrorEstimatorOptions{1.0, 0.30});

    REQUIRE(errors[0].damage_indicator == Catch::Approx(0.35));
    REQUIRE(marked[0] == 1);
}

TEST_CASE("MeshRefiner: Q4 marked element subdivides into four Q4 preserving area",
          "[adapt][refine][q4]") {
    Mesh2D mesh = build_mesh_structured_2d("axisym_2d_Q4", 1.0, 2.0, 1.0, 1, 1, 1.0);
    AxisymQ4 elem;
    MeshRefiner refiner;
    const std::vector<char> marked{1};

    RefinedMesh refined = refiner.refine_elements(mesh, elem, marked);

    REQUIRE(refined.mesh.n_elements == 4);
    REQUIRE(refined.mesh.nodes_per_element == 4);
    REQUIRE(total_area(refined.mesh) == Catch::Approx(total_area(mesh)).epsilon(1.0e-12));
    REQUIRE(refined.parent_element.size() == 4);
}

TEST_CASE("MeshRefiner: T3 marked element subdivides into three T3 preserving area",
          "[adapt][refine][t3]") {
    Mesh2D mesh = build_mesh_structured_2d("axisym_2d_T3", 1.0, 2.0, 1.0, 1, 1, 1.0);
    AxisymT3 elem;
    MeshRefiner refiner;
    const std::vector<char> marked{1, 0};

    RefinedMesh refined = refiner.refine_elements(mesh, elem, marked);

    REQUIRE(refined.mesh.n_elements == 4);
    REQUIRE(refined.mesh.nodes_per_element == 3);
    REQUIRE(total_area(refined.mesh) == Catch::Approx(total_area(mesh)).epsilon(1.0e-12));
}

TEST_CASE("MeshRefiner: linear displacement field transfers exactly to new Q4 nodes",
          "[adapt][transfer]") {
    Mesh2D mesh = build_mesh_structured_2d("axisym_2d_Q4", 1.0, 2.0, 1.0, 1, 1, 1.0);
    AxisymQ4 elem;
    MeshRefiner refiner;
    const std::vector<char> marked{1};
    RefinedMesh refined = refiner.refine_elements(mesh, elem, marked);

    TimeState state = make_constant_stress_state(
        mesh, elem, Stress{1.0e6, 1.0e6, 1.0e6, 0.0});
    Eigen::VectorXd u = linear_displacement(mesh);
    FieldTransferResult transfer = refiner.interpolate_fields(
        mesh, refined.mesh, elem, elem, u, state, refined.parent_element);

    Eigen::VectorXd expected = linear_displacement(refined.mesh);
    REQUIRE((transfer.u - expected).norm() == Catch::Approx(0.0).margin(1.0e-12));
}

TEST_CASE("MeshRefiner: transferred damage and ISVs remain bounded",
          "[adapt][transfer][damage]") {
    Mesh2D mesh = build_mesh_structured_2d("axisym_2d_Q4", 1.0, 2.0, 1.0, 1, 1, 1.0);
    AxisymQ4 elem;
    MeshRefiner refiner;
    const std::vector<char> marked{1};
    RefinedMesh refined = refiner.refine_elements(mesh, elem, marked);
    TimeState state = make_constant_stress_state(
        mesh, elem, Stress{1.0e6, 1.0e6, 1.0e6, 0.0});
    for (auto& gp_state : state.state_gp) {
        gp_state.damage_D = 0.4;
        gp_state.eps_v_primary = 0.02;
        gp_state.eps_v_secondary = 0.03;
    }

    FieldTransferResult transfer = refiner.interpolate_fields(
        mesh, refined.mesh, elem, elem, linear_displacement(mesh), state,
        refined.parent_element);

    for (const auto& gp_state : transfer.state.state_gp) {
        REQUIRE(gp_state.damage_D == Catch::Approx(0.4).margin(1.0e-12));
        REQUIRE(gp_state.damage_D < 0.99);
        REQUIRE(gp_state.eps_v_primary >= 0.0);
        REQUIRE(gp_state.eps_v_secondary >= 0.0);
    }
}

TEST_CASE("CaseParser: mesh adaptive options are accepted",
          "[adapt][parser]") {
    const fs::path dir = fs::temp_directory_path() / "saltcreep_test" / "adapt_parser";
    fs::create_directories(dir);
    const fs::path yaml = dir / "case.yaml";

    std::ofstream out(yaml);
    out << R"yaml(
name: adapt_parser
geometry:
  well_radius_m: 0.155575
  outer_radius_factor: 10
depths:
  water_depth_m: 1000
  burial_m: 2000
  salt_above_m: 0
lithology:
  primary: halita
fluid:
  weight_lb_per_gal: 10
stress:
  k0: 1.0
thermal:
  mode: profile
element:
  type: axisym_2d_Q4
mesh:
  n_elements_radial: 4
  n_elements_axial: 2
  ratio: 1
  adaptive: true
  error_threshold: 0.08
  max_refinement_levels: 2
  damage_refinement_threshold: 0.3
creep:
  elastic_only: true
time:
  total_h: 1
  dt_h: 1
)yaml";
    out.close();

    CaseData cd = parse_case(yaml, find_data_dir());
    REQUIRE(cd.mesh.adaptive);
    REQUIRE(cd.mesh.error_threshold == Catch::Approx(0.08));
    REQUIRE(cd.mesh.max_refinement_levels == 2);
    REQUIRE(cd.mesh.damage_refinement_threshold == Catch::Approx(0.3));
}
