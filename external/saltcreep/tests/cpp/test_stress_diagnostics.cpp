#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <sstream>

#include "elements/ElementFactory.hpp"
#include "physics/stress_utils.hpp"
#include "solver/Assembler.hpp"
#include "solver/StressSampler.hpp"
#include "solver/TimeState.hpp"

TEST_CASE("Stress utilities expose hoop stress and legacy APB sign convention",
          "[stress][diagnostics]") {
    const Stress hydrostatic_compression{-10.0e6, -10.0e6, -10.0e6, 0.0};

    REQUIRE(stress_utils::sigma_theta(hydrostatic_compression) ==
            Catch::Approx(-10.0e6));
    REQUIRE(stress_utils::sigma_theta_compression_positive(hydrostatic_compression) ==
            Catch::Approx(10.0e6));
    REQUIRE(stress_utils::deviatoric_stress(hydrostatic_compression).norm() ==
            Catch::Approx(0.0).margin(1.0e-10));
    REQUIRE(stress_utils::j2(hydrostatic_compression) ==
            Catch::Approx(0.0).margin(1.0e-10));
    REQUIRE(stress_utils::von_mises_effective_stress(hydrostatic_compression) ==
            Catch::Approx(0.0).margin(1.0e-10));
}

TEST_CASE("Stress utilities compute deviatoric stress and von Mises stress",
          "[stress][diagnostics]") {
    const double sigma_ef = 12.0e6;
    const Stress pure_deviatoric{2.0 / 3.0 * sigma_ef,
                                 -1.0 / 3.0 * sigma_ef,
                                 -1.0 / 3.0 * sigma_ef,
                                 0.0};

    const Stress s = stress_utils::deviatoric_stress(pure_deviatoric);
    REQUIRE(s[0] == Catch::Approx(pure_deviatoric[0]));
    REQUIRE(s[1] == Catch::Approx(pure_deviatoric[1]));
    REQUIRE(s[2] == Catch::Approx(pure_deviatoric[2]));
    REQUIRE(stress_utils::mean_stress(pure_deviatoric) ==
            Catch::Approx(0.0).margin(1.0e-10));
    REQUIRE(stress_utils::von_mises_effective_stress(pure_deviatoric) ==
            Catch::Approx(sigma_ef));
}

TEST_CASE("StressSampler selects the Gauss point closest to the 1D well wall",
          "[stress][diagnostics]") {
    Mesh1D mesh = build_mesh_L3(1.0, 2.0, 1, 1.0);
    auto element = make_element("axisym_1d_L3");

    TimeState state;
    state.sigma_gp = {
        Stress{-11.0e6, -9.0e6, -12.0e6, 0.0},
        Stress{-21.0e6, -19.0e6, -22.0e6, 0.0},
        Stress{-31.0e6, -29.0e6, -32.0e6, 0.0},
    };

    const auto wall = stress_sampler::sample_wall_gauss_points(
        mesh, *element, state, 4000.0);

    REQUIRE(wall.size() == 1);
    REQUIRE(wall.front().gp_id == 0);
    REQUIRE(wall.front().sigma[1] == Catch::Approx(-9.0e6));
    REQUIRE(stress_utils::sigma_theta_compression_positive(wall.front().sigma) ==
            Catch::Approx(9.0e6));
}

TEST_CASE("StressSampler writes a 2D wall stress profile with APB columns",
          "[stress][diagnostics]") {
    Mesh2D mesh = build_mesh_structured_2d("axisym_2d_Q4",
                                           1.0, 2.0, 10.0,
                                           1, 2, 1.0);
    auto element = make_element("axisym_2d_Q4");
    const int total_gp = mesh.n_elements *
        static_cast<int>(element->gauss_points().size());

    TimeState state;
    state.sigma_gp.assign(total_gp, Stress{-5.0e6, -4.0e6, -6.0e6, 1.0e5});

    const auto wall = stress_sampler::sample_wall_gauss_points(
        mesh, *element, state, 3000.0);
    REQUIRE(wall.size() == 4);
    REQUIRE(wall.front().z_m < wall.back().z_m);

    std::ostringstream csv;
    stress_sampler::write_stress_header(csv);
    stress_sampler::write_wall_stress_record(csv, mesh, *element, state, 0.0, 3000.0);
    const std::string text = csv.str();
    REQUIRE(text.find("sigma_theta_comp_Pa") != std::string::npos);
    REQUIRE(text.find("sdev_theta_Pa") != std::string::npos);
}
