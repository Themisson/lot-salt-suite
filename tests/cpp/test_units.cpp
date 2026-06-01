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
