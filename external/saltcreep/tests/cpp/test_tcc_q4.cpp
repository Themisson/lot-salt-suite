#include <catch2/catch_test_macros.hpp>
#include <filesystem>
#include <vector>

#include "constitutive/double_mechanism.hpp"
#include "elements/axisym_2d_q4.hpp"
#include "io/CaseParser.hpp"
#include "solver/Assembler.hpp"
#include "solver/TimeIntegrator.hpp"
#include "thermal/profile_field.hpp"
#include "q4_test_helpers.hpp"

namespace fs = std::filesystem;

TEST_CASE("TCC Modelo A Q4: closure remains compatible with L3 oracle",
          "[tcc][q4][regression]") {
    fs::path case_path;
    for (const auto& candidate : {
             fs::path("cases/tcc/modelo_A.yaml"),
             fs::path("../cases/tcc/modelo_A.yaml"),
             fs::path("../../cases/tcc/modelo_A.yaml")}) {
        if (fs::exists(candidate)) {
            case_path = candidate;
            break;
        }
    }
    REQUIRE_FALSE(case_path.empty());

    CaseData cd = parse_case(case_path);
    constexpr double l3_oracle_closure = 25.38;
    const double Ri = cd.geom.Ri;
    const double Re = Ri * cd.geom.outer_factor;
    const double height = 1.0;
    const int n_radial = 100;
    const int n_axial = 1;

    AxisymQ4 elem;
    DoubleMechanism model(cd.dm, cd.E_Pa, cd.nu);
    ProfileField thermal = (cd.thermal.mode == "profile")
        ? ProfileField::make_profile(cd.thermal.seabed_temp_C,
                                     cd.depths.burial_m + cd.depths.water_depth_m,
                                     cd.thermal.grad_C_per_m)
        : ProfileField::make_constant(cd.thermal.T_K);

    Mesh2D mesh = build_q4_mesh(Ri, Re, height, n_radial, n_axial, cd.mesh.ratio);
    auto K = Assembler::assemble_K(mesh, elem, model);
    auto f = assemble_inner_pressure_q4(mesh, elem, n_radial, n_axial, cd.fluid_Pa);

    const double depth = cd.depths.burial_m + cd.depths.water_depth_m + cd.depths.salt_above_m;
    const double sigma_v = -cd.overburden_grad_Pa_per_m * depth;
    const double sigma_h = cd.k0 * sigma_v;
    const int total_gp = mesh.n_elements * static_cast<int>(elem.gauss_points().size());
    std::vector<Stress> sigma_geo(total_gp, Stress{sigma_h, sigma_h, sigma_v, 0.0});

    std::vector<int> fixed_dofs;
    for (int n = 0; n < mesh.n_nodes; ++n)
        fixed_dofs.push_back(mesh.dof_index(n, 1));
    for (int iz = 0; iz <= n_axial; ++iz) {
        const int outer_node = iz * (n_radial + 1) + n_radial;
        fixed_dofs.push_back(mesh.dof_index(outer_node, 0));
    }

    TimeIntegrator integrator(mesh, elem, model, thermal, K, f, sigma_geo, fixed_dofs);
    fs::path tmp = fs::temp_directory_path() / "saltcreep_test" / "modelo_A_Q4";
    if (!cd.time.steps.empty())
        integrator.run_schedule(cd.time.steps, cd.time.total_s, 999999, tmp);
    else
        integrator.run(cd.time.dt_s, cd.time.total_s, 999999, tmp);

    const double closure = integrator.wall_closure_pct();
    REQUIRE(closure > l3_oracle_closure - 10.0);
    REQUIRE(closure < l3_oracle_closure + 25.0);
    REQUIRE(std::abs(closure - l3_oracle_closure) / l3_oracle_closure <= 0.15);
}
