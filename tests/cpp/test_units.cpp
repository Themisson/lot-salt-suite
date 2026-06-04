#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "units/units.hpp"

TEST_CASE("PPG converts to density in kg/m3") {
  CHECK(units::ppg_to_kg_m3(8.34) == Catch::Approx(999.7).epsilon(0.001));
  CHECK(units::ppg_to_kg_m3(1.0) == Catch::Approx(119.826));
  CHECK(units::kg_m3_to_ppg(units::ppg_to_kg_m3(10.0)) ==
        Catch::Approx(10.0).margin(1e-10));
}

TEST_CASE("Length conversion between inches and meters") {
  CHECK(units::in_to_m(1.0) == Catch::Approx(0.0254));
  CHECK(units::m_to_in(0.0254) == Catch::Approx(1.0));
}

TEST_CASE("Pressure conversion between psi, bar and Pa") {
  CHECK(units::psi_to_Pa(1.0) == Catch::Approx(6894.757));
  CHECK(units::Pa_to_psi(6894.757) == Catch::Approx(1.0));
  CHECK(units::bar_to_Pa(1.0) == Catch::Approx(100000.0));
  CHECK(units::Pa_to_bar(100000.0) == Catch::Approx(1.0));
}

TEST_CASE("Viscosity conversion between cP and Pa.s") {
  CHECK(units::cP_to_Pa_s(1.0) == Catch::Approx(1e-3));
  CHECK(units::Pa_s_to_cP(1e-3) == Catch::Approx(1.0));
}

TEST_CASE("Temperature conversions") {
  CHECK(units::degC_to_K(86.0) == Catch::Approx(359.15));
  CHECK(units::K_to_degC(359.15) == Catch::Approx(86.0));
  CHECK(units::degF_to_degC(212.0) == Catch::Approx(100.0));
  CHECK(units::degC_to_degF(100.0) == Catch::Approx(212.0));
}

TEST_CASE("Torque and hydrostatic gradient conversions") {
  CHECK(units::lbf_ft_to_N_m(1.0) == Catch::Approx(14.5939));
  CHECK(units::ppg_hydrostatic_Pa_per_m(8.5) == Catch::Approx(9988.8).epsilon(0.001));
}

TEST_CASE("Hydrostatic pressure from SI density and depth") {
  CHECK(units::hydrostatic_pressure_Pa(1000.0, 10.0) ==
        Catch::Approx(1000.0 * units::kStandardGravity * 10.0));
  CHECK(units::hydrostatic_pressure_Pa(1000.0, 0.0) ==
        Catch::Approx(0.0));
}

TEST_CASE("Hydrostatic pressure from PPG and depth") {
  constexpr double ppg = 8.5;
  constexpr double depth_m = 1234.5;

  CHECK(units::ppg_hydrostatic_pressure_Pa(ppg, depth_m) ==
        Catch::Approx(units::ppg_hydrostatic_Pa_per_m(ppg) * depth_m));
}

TEST_CASE("Surface plus hydrostatic pressure combines absolute terms") {
  constexpr double surface_pressure_Pa = 2.0e6;
  constexpr double density_kg_m3 = 1200.0;
  constexpr double depth_m = 2500.0;

  CHECK(units::surface_plus_hydrostatic_pressure_Pa(
            surface_pressure_Pa, density_kg_m3, depth_m) ==
        Catch::Approx(surface_pressure_Pa +
                      density_kg_m3 * units::kStandardGravity * depth_m));
  CHECK(units::surface_plus_hydrostatic_pressure_Pa(0.0, density_kg_m3,
                                                   depth_m) ==
        Catch::Approx(density_kg_m3 * units::kStandardGravity * depth_m));
}

TEST_CASE("Hydrostatic pressure utilities reject invalid inputs") {
  const double nan = std::numeric_limits<double>::quiet_NaN();
  const double inf = std::numeric_limits<double>::infinity();

  CHECK_THROWS_AS(units::hydrostatic_pressure_Pa(-1.0, 10.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(units::hydrostatic_pressure_Pa(1000.0, -1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(units::hydrostatic_pressure_Pa(1000.0, 10.0, 0.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(units::hydrostatic_pressure_Pa(1000.0, 10.0, -1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(units::hydrostatic_pressure_Pa(nan, 10.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(units::hydrostatic_pressure_Pa(1000.0, inf),
                  std::invalid_argument);

  CHECK_THROWS_AS(units::ppg_hydrostatic_pressure_Pa(-1.0, 10.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(units::ppg_hydrostatic_pressure_Pa(8.5, -1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(units::ppg_hydrostatic_pressure_Pa(8.5, 10.0, 0.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(units::ppg_hydrostatic_pressure_Pa(nan, 10.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(units::ppg_hydrostatic_pressure_Pa(8.5, inf),
                  std::invalid_argument);

  CHECK_THROWS_AS(units::surface_plus_hydrostatic_pressure_Pa(-1.0, 1000.0,
                                                              10.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(units::surface_plus_hydrostatic_pressure_Pa(nan, 1000.0,
                                                              10.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(units::surface_plus_hydrostatic_pressure_Pa(inf, 1000.0,
                                                              10.0),
                  std::invalid_argument);
}
