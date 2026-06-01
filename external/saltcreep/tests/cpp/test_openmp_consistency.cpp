#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>

#include <cmath>
#include <filesystem>
#include <stdexcept>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

#include "constitutive/double_mechanism.hpp"
#include "elements/axisym_2d_q8.hpp"
#include "io/CaseParser.hpp"
#include "solver/Assembler.hpp"
#include "solver/TimeIntegrator.hpp"
#include "thermal/profile_field.hpp"
#include "q4_test_helpers.hpp"

namespace fs = std::filesystem;

namespace {

CaseData load_modelo_a() {
    for (const auto& candidate : {
             fs::path("cases/tcc/modelo_A.yaml"),
             fs::path("../cases/tcc/modelo_A.yaml"),
             fs::path("../../cases/tcc/modelo_A.yaml")}) {
        if (fs::exists(candidate))
            return parse_case(candidate);
    }
    throw std::runtime_error("modelo_A.yaml not found");
}

double run_q8_modelo_a_reduced(int threads, const fs::path& out_dir) {
#ifdef _OPENMP
    omp_set_num_threads(threads);
#else
    (void)threads;
#endif

    CaseData cd = load_modelo_a();
    const double Ri = cd.geom.Ri;
    const double Re = Ri * cd.geom.outer_factor;
    constexpr int n_radial = 100;
    constexpr int n_axial = 1;

    AxisymQ8 elem;
    DoubleMechanism model(cd.dm, cd.E_Pa, cd.nu);
    ProfileField thermal = ProfileField::make_profile(
        cd.thermal.seabed_temp_C,
        cd.depths.burial_m + cd.depths.water_depth_m,
        cd.thermal.grad_C_per_m);

    Mesh2D mesh = build_q8_mesh(Ri, Re, 1.0, n_radial, n_axial, cd.mesh.ratio);
    auto K = Assembler::assemble_K(mesh, elem, model);
    auto f = assemble_inner_pressure_q8(mesh, elem, n_radial, n_axial, cd.fluid_Pa);

    const double depth = cd.depths.burial_m + cd.depths.water_depth_m + cd.depths.salt_above_m;
    const double sigma_v = -cd.overburden_grad_Pa_per_m * depth;
    const double sigma_h = cd.k0 * sigma_v;
    const int total_gp = mesh.n_elements * static_cast<int>(elem.gauss_points().size());
    std::vector<Stress> sigma_geo(total_gp, Stress{sigma_h, sigma_h, sigma_v, 0.0});

    std::vector<int> fixed_dofs;
    for (int n = 0; n < mesh.n_nodes; ++n) {
        fixed_dofs.push_back(mesh.dof_index(n, 1));
        if (std::abs(mesh.nodes[n].r - Re) < 1.0e-10)
            fixed_dofs.push_back(mesh.dof_index(n, 0));
    }

    TimeIntegrator integrator(mesh, elem, model, thermal, K, f, sigma_geo, fixed_dofs);
    const std::vector<TimeSegment> schedule = {
        TimeSegment{0.01 * 3600.0, 5.0e-5 * 3600.0},
    };
    integrator.run_schedule(schedule, 0.01 * 3600.0, 999999, out_dir);
    return integrator.wall_closure_pct();
}

} // namespace

TEST_CASE("OpenMP consistency: Q8 Modelo A gives identical closure",
          "[openmp][parallel]") {
    const fs::path base = fs::temp_directory_path() / "saltcreep_test" / "openmp_consistency";
    const double closure_1 = run_q8_modelo_a_reduced(1, base / "threads_1");
    const double closure_2 = run_q8_modelo_a_reduced(2, base / "threads_2");

    REQUIRE(std::isfinite(closure_1));
    REQUIRE(std::isfinite(closure_2));
    REQUIRE(closure_2 == Catch::Approx(closure_1).margin(1.0e-12));
}
