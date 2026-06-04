#include <limits>
#include <stdexcept>
#include <string>

#include <catch2/catch_test_macros.hpp>

#include "coupling/LotSaltPressureMap.hpp"

TEST_CASE("LotSaltPressureMap method labels are stable") {
  using lss::coupling::LotSaltPressureMapMethod;

  CHECK(std::string(lss::coupling::to_string(
            LotSaltPressureMapMethod::ExperimentalNetPressureProxy)) ==
        "experimental_net_pressure_proxy");
  CHECK(std::string(lss::coupling::to_string(
            LotSaltPressureMapMethod::AbsoluteWellborePressure)) ==
        "absolute_wellbore_pressure");
  CHECK(std::string(lss::coupling::to_string(
            LotSaltPressureMapMethod::HydrostaticPlusNetPressure)) ==
        "hydrostatic_plus_net_pressure");
}

TEST_CASE("ExperimentalNetPressureProxy maps net pressure directly") {
  lss::coupling::LotSaltPressureMapInput input;
  input.method =
      lss::coupling::LotSaltPressureMapMethod::ExperimentalNetPressureProxy;
  input.net_pressure_Pa = 12345.0;

  const auto result =
      lss::coupling::map_lot_pkn_to_salt_wall_pressure(input);

  CHECK(result.wall_pressure_Pa == 12345.0);
  CHECK(result.method == input.method);
  CHECK(result.method_label == "experimental_net_pressure_proxy");
  CHECK(result.physically_absolute == false);
}

TEST_CASE("AbsoluteWellborePressure ignores net pressure") {
  lss::coupling::LotSaltPressureMapInput input;
  input.method =
      lss::coupling::LotSaltPressureMapMethod::AbsoluteWellborePressure;
  input.net_pressure_Pa = 999.0;
  input.absolute_wellbore_pressure_Pa = 45.0e6;

  const auto result =
      lss::coupling::map_lot_pkn_to_salt_wall_pressure(input);

  CHECK(result.wall_pressure_Pa == 45.0e6);
  CHECK(result.method == input.method);
  CHECK(result.method_label == "absolute_wellbore_pressure");
  CHECK(result.physically_absolute == true);
}

TEST_CASE("HydrostaticPlusNetPressure sums surface hydrostatic and net pressure") {
  lss::coupling::LotSaltPressureMapInput input;
  input.method =
      lss::coupling::LotSaltPressureMapMethod::HydrostaticPlusNetPressure;
  input.surface_pressure_Pa = 2.0e6;
  input.hydrostatic_pressure_Pa = 30.0e6;
  input.net_pressure_Pa = 4.0e6;
  input.depth_m = 3000.0;

  const auto result =
      lss::coupling::map_lot_pkn_to_salt_wall_pressure(input);

  CHECK(result.wall_pressure_Pa == 36.0e6);
  CHECK(result.method == input.method);
  CHECK(result.method_label == "hydrostatic_plus_net_pressure");
  CHECK(result.physically_absolute == true);
}

TEST_CASE("LotSaltPressureMap rejects NaN and Inf in used fields") {
  const double nan = std::numeric_limits<double>::quiet_NaN();
  const double inf = std::numeric_limits<double>::infinity();

  lss::coupling::LotSaltPressureMapInput experimental;
  experimental.method =
      lss::coupling::LotSaltPressureMapMethod::ExperimentalNetPressureProxy;
  experimental.net_pressure_Pa = nan;
  CHECK_THROWS_AS(lss::coupling::map_lot_pkn_to_salt_wall_pressure(experimental),
                  std::invalid_argument);
  experimental.net_pressure_Pa = inf;
  CHECK_THROWS_AS(lss::coupling::map_lot_pkn_to_salt_wall_pressure(experimental),
                  std::invalid_argument);

  lss::coupling::LotSaltPressureMapInput absolute;
  absolute.method =
      lss::coupling::LotSaltPressureMapMethod::AbsoluteWellborePressure;
  absolute.absolute_wellbore_pressure_Pa = nan;
  CHECK_THROWS_AS(lss::coupling::map_lot_pkn_to_salt_wall_pressure(absolute),
                  std::invalid_argument);
  absolute.absolute_wellbore_pressure_Pa = inf;
  CHECK_THROWS_AS(lss::coupling::map_lot_pkn_to_salt_wall_pressure(absolute),
                  std::invalid_argument);

  lss::coupling::LotSaltPressureMapInput hydrostatic;
  hydrostatic.method =
      lss::coupling::LotSaltPressureMapMethod::HydrostaticPlusNetPressure;
  hydrostatic.surface_pressure_Pa = 1.0;
  hydrostatic.hydrostatic_pressure_Pa = 2.0;
  hydrostatic.net_pressure_Pa = nan;
  CHECK_THROWS_AS(lss::coupling::map_lot_pkn_to_salt_wall_pressure(hydrostatic),
                  std::invalid_argument);
  hydrostatic.net_pressure_Pa = 3.0;
  hydrostatic.hydrostatic_pressure_Pa = inf;
  CHECK_THROWS_AS(lss::coupling::map_lot_pkn_to_salt_wall_pressure(hydrostatic),
                  std::invalid_argument);
}

TEST_CASE("LotSaltPressureMap rejects negative pressure inputs in used fields") {
  lss::coupling::LotSaltPressureMapInput experimental;
  experimental.method =
      lss::coupling::LotSaltPressureMapMethod::ExperimentalNetPressureProxy;
  experimental.net_pressure_Pa = -1.0;
  CHECK_THROWS_AS(lss::coupling::map_lot_pkn_to_salt_wall_pressure(experimental),
                  std::invalid_argument);

  lss::coupling::LotSaltPressureMapInput absolute;
  absolute.method =
      lss::coupling::LotSaltPressureMapMethod::AbsoluteWellborePressure;
  absolute.absolute_wellbore_pressure_Pa = -1.0;
  CHECK_THROWS_AS(lss::coupling::map_lot_pkn_to_salt_wall_pressure(absolute),
                  std::invalid_argument);

  lss::coupling::LotSaltPressureMapInput hydrostatic;
  hydrostatic.method =
      lss::coupling::LotSaltPressureMapMethod::HydrostaticPlusNetPressure;
  hydrostatic.surface_pressure_Pa = 1.0;
  hydrostatic.hydrostatic_pressure_Pa = -2.0;
  hydrostatic.net_pressure_Pa = 3.0;
  CHECK_THROWS_AS(lss::coupling::map_lot_pkn_to_salt_wall_pressure(hydrostatic),
                  std::invalid_argument);
}

TEST_CASE("LotSaltPressureMap rejects unknown methods") {
  const auto unknown_method =
      static_cast<lss::coupling::LotSaltPressureMapMethod>(999);

  CHECK_THROWS_AS(lss::coupling::to_string(unknown_method),
                  std::invalid_argument);

  lss::coupling::LotSaltPressureMapInput input;
  input.method = unknown_method;
  CHECK_THROWS_AS(lss::coupling::map_lot_pkn_to_salt_wall_pressure(input),
                  std::invalid_argument);
}
