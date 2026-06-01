#include <catch2/catch_all.hpp>
#include <test_sestsal_oracle.hpp>
#include <io/CaseParser.hpp>
#include <mesh/Mesh.hpp>
#include <solver/Assembler.hpp>
#include <solver/ElasticSolver.hpp>
#include <solver/TimeIntegrator.hpp>
#include <elements/axisym_1d_L3.hpp>
#include <thermal/profile_field.hpp>
#include <cmath>

using namespace saltcreep;

/* Helper: run a SaltCreep simulation and extract final closure % */
double run_saltcreep_case(const std::string& yaml_path) {
    // Parse case
    CaseData case_data = CaseParser::parse(yaml_path);

    // Build 1D mesh
    Mesh1D mesh = Mesh1D::create_cylindrical(
        case_data.geometry.well_radius_m,
        case_data.geometry.well_radius_m * case_data.geometry.outer_radius_factor,
        case_data.mesh.n_radial,
        case_data.mesh.ratio
    );

    // Create element
    AxisymL3 element;

    // Create constitutive model (for now, assume DM is available)
    // TODO: load from case_data.constitutive
    // For this test, stub with elastic only
    double E_Pa = case_data.material.E_Pa;
    double nu = case_data.material.nu;

    // Create thermal field
    ProfileField thermal;
    if (case_data.thermal.enabled) {
        thermal = ProfileField::make_constant(case_data.thermal.T_K);
    } else {
        thermal = ProfileField::make_constant(case_data.thermal.T_K);
    }

    // Create geostatic stress (1D: radial + hoop = -k0*sigma_v, axial = -sigma_v)
    double sigma_v = case_data.depths.burial_m * 9.81 * 2300; // rough estimate
    Stress sigma_geo;
    sigma_geo(0) = -case_data.stress.k0 * sigma_v;  // rr
    sigma_geo(1) = -case_data.stress.k0 * sigma_v;  // theta
    sigma_geo(2) = -sigma_v;                         // zz
    sigma_geo(3) = 0.0;                              // rz

    // For now: elastic solve only (creep loop not yet implemented)
    // This is a RED test — will be GREEN once TimeIntegrator is implemented
    ElasticSolver elastic_solver(mesh, element, E_Pa, nu);
    Eigen::VectorXd u_elastic = elastic_solver.solve(sigma_geo);

    // Extract wall closure
    double ri = case_data.geometry.well_radius_m;
    double u_radial_at_ri = u_elastic(0);  // first DOF is radial at well
    double closure_pct = -u_radial_at_ri / ri * 100.0;

    return closure_pct;
}

TEST_CASE("SESTSAL verification: base_model", "[sestsal][verification]") {
    double closure_saltcreep = run_saltcreep_case("cases/sestsal/base_model.yaml");

    // Find oracle
    double closure_sestsal = 0.0;
    double tolerance = 5.0;
    for (const auto& oracle : SESTSAL_ORACLES) {
        if (oracle.case_name == "base_model") {
            closure_sestsal = oracle.closure_percent_final;
            tolerance = oracle.tolerance_percent;
            break;
        }
    }

    REQUIRE(closure_sestsal > 0.0);  // oracle must exist
    double error_pct = std::abs(closure_saltcreep - closure_sestsal) / closure_sestsal * 100.0;
    INFO("SaltCreep: " << closure_saltcreep << "%, SESTSAL: " << closure_sestsal << "%, Error: " << error_pct << "%");
    REQUIRE(error_pct < tolerance);
}

TEST_CASE("SESTSAL verification: hello_repasse", "[sestsal][verification]") {
    double closure_saltcreep = run_saltcreep_case("cases/sestsal/hello_repasse.yaml");

    double closure_sestsal = 0.0;
    double tolerance = 5.0;
    for (const auto& oracle : SESTSAL_ORACLES) {
        if (oracle.case_name == "hello_repasse") {
            closure_sestsal = oracle.closure_percent_final;
            tolerance = oracle.tolerance_percent;
            break;
        }
    }

    REQUIRE(closure_sestsal > 0.0);
    double error_pct = std::abs(closure_saltcreep - closure_sestsal) / closure_sestsal * 100.0;
    INFO("SaltCreep: " << closure_saltcreep << "%, SESTSAL: " << closure_sestsal << "%, Error: " << error_pct << "%");
    REQUIRE(error_pct < tolerance);
}

TEST_CASE("SESTSAL verification: base_model2D (1D projection)", "[sestsal][verification]") {
    // 2D case: run as 1D axissym for now
    double closure_saltcreep = run_saltcreep_case("cases/sestsal/base_model2D.yaml");

    double closure_sestsal = 0.0;
    double tolerance = 10.0;  // looser for 2D→1D projection
    for (const auto& oracle : SESTSAL_ORACLES) {
        if (oracle.case_name == "base_model2D") {
            closure_sestsal = oracle.closure_percent_final;
            // use custom tolerance for 2D
            tolerance = 10.0;
            break;
        }
    }

    REQUIRE(closure_sestsal > 0.0);
    double error_pct = std::abs(closure_saltcreep - closure_sestsal) / closure_sestsal * 100.0;
    INFO("SaltCreep: " << closure_saltcreep << "%, SESTSAL: " << closure_sestsal << "%, Error: " << error_pct << "%");
    REQUIRE(error_pct < tolerance);
}
