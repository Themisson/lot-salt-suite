#include <cmath>
#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "coupling/LotSaltCouplingStep.hpp"
#include "coupling/LotSaltSigmaThetaDiagnostic.hpp"

namespace {

constexpr double kMPa = 1.0e6;

lss::lot::PknResult make_pkn_result(std::initializer_list<double> times_s,
                                    std::initializer_list<double> pressures_Pa) {
  lss::lot::PknResult result;
  result.time_series_s.assign(times_s.begin(), times_s.end());
  result.net_pressure_series_Pa.assign(pressures_Pa.begin(),
                                       pressures_Pa.end());
  return result;
}

lss::salt::SaltWallStressSample make_sample(
    double sigma_theta_compression_positive_Pa,
    int gp_id = 7,
    int element_id = 3,
    int local_gp_id = 1,
    double r_m = 0.1556,
    double z_m = 2.5,
    double depth_m = 3000.0) {
  lss::salt::SaltWallStressSample sample;
  sample.gp_id = gp_id;
  sample.element_id = element_id;
  sample.local_gp_id = local_gp_id;
  sample.r_m = r_m;
  sample.z_m = z_m;
  sample.depth_m = depth_m;
  sample.sigma_theta_compression_positive_Pa =
      sigma_theta_compression_positive_Pa;
  sample.mean_stress_Pa = 30.0 * kMPa;
  sample.j2_Pa2 = 4.0;
  sample.von_mises_effective_stress_Pa = std::sqrt(12.0);
  return sample;
}

lss::salt::SaltWallStressDiagnostics make_wall_stress(
    std::initializer_list<lss::salt::SaltWallStressSample> samples) {
  lss::salt::SaltWallStressDiagnostics diagnostics;
  diagnostics.valid = true;
  diagnostics.wall_samples.assign(samples.begin(), samples.end());
  return diagnostics;
}

}  // namespace

TEST_CASE("LotSaltSigmaThetaDiagnostic step uses ExperimentalNetPressureProxy") {
  const auto pkn = make_pkn_result({0.0}, {50.0 * kMPa});
  const lss::coupling::LotSaltCouplingConfig config;
  const auto wall_stress = make_wall_stress({make_sample(45.0 * kMPa)});

  const auto result = lss::coupling::evaluate_lot_salt_sigma_theta_step(
      pkn, 0, config, wall_stress);

  REQUIRE(result.valid);
  REQUIRE(result.points.size() == 1);
  CHECK(result.any_opened);
  CHECK(result.pressure_source ==
        "LotSaltPressureMap:experimental_net_pressure_proxy");
  CHECK(result.stress_source == "SaltWallStressDiagnostics snapshot");
  CHECK(result.points[0].pressure_map.wall_pressure_Pa ==
        Catch::Approx(50.0 * kMPa));
  CHECK(result.points[0].pressure_map.method ==
        lss::coupling::LotSaltPressureMapMethod::ExperimentalNetPressureProxy);
  CHECK(result.points[0].breakdown.opened);
  CHECK(result.points[0].breakdown.margin_Pa == Catch::Approx(5.0 * kMPa));
  CHECK(result.points[0].breakdown.layer_id == "wall_gp_0");
}

TEST_CASE("LotSaltSigmaThetaDiagnostic step uses HydrostaticPlusNetPressure") {
  const auto pkn = make_pkn_result({10.0}, {4.0 * kMPa});
  lss::coupling::LotSaltCouplingConfig config;
  config.pressure_map_method =
      lss::coupling::LotSaltPressureMapMethod::HydrostaticPlusNetPressure;
  config.hydrostatic_pressure_Pa = 40.0 * kMPa;
  config.surface_pressure_Pa = 1.0 * kMPa;
  const auto wall_stress = make_wall_stress({make_sample(44.0 * kMPa)});

  const auto result = lss::coupling::evaluate_lot_salt_sigma_theta_step(
      pkn, 0, config, wall_stress);

  REQUIRE(result.valid);
  REQUIRE(result.points.size() == 1);
  CHECK(result.points[0].pressure_map.wall_pressure_Pa ==
        Catch::Approx(45.0 * kMPa));
  CHECK(result.points[0].pressure_map.method ==
        lss::coupling::LotSaltPressureMapMethod::HydrostaticPlusNetPressure);
  CHECK(result.points[0].pressure_map.physically_absolute);
  CHECK(result.points[0].breakdown.opened);
  CHECK(result.points[0].breakdown.margin_Pa == Catch::Approx(1.0 * kMPa));
}

TEST_CASE("LotSaltSigmaThetaDiagnostic equality does not open") {
  const auto pkn = make_pkn_result({0.0}, {45.0 * kMPa});
  const lss::coupling::LotSaltCouplingConfig config;
  const auto wall_stress = make_wall_stress({make_sample(45.0 * kMPa)});

  const auto result = lss::coupling::evaluate_lot_salt_sigma_theta_step(
      pkn, 0, config, wall_stress);

  REQUIRE(result.valid);
  REQUIRE(result.points.size() == 1);
  CHECK_FALSE(result.any_opened);
  CHECK_FALSE(result.points[0].breakdown.opened);
  CHECK(result.points[0].breakdown.margin_Pa == Catch::Approx(0.0));
}

TEST_CASE("LotSaltSigmaThetaDiagnostic series is time-major") {
  const auto pkn = make_pkn_result({0.0, 10.0, 20.0},
                                   {10.0 * kMPa, 20.0 * kMPa, 30.0 * kMPa});
  const lss::coupling::LotSaltCouplingConfig config;
  const auto wall_stress = make_wall_stress({
      make_sample(15.0 * kMPa, 1),
      make_sample(25.0 * kMPa, 2),
  });

  const auto result = lss::coupling::evaluate_lot_salt_sigma_theta_series(
      pkn, config, wall_stress);

  REQUIRE(result.valid);
  REQUIRE(result.points.size() == 6);
  CHECK(result.any_opened);

  CHECK(result.points[0].breakdown.time_s == Catch::Approx(0.0));
  CHECK(result.points[0].breakdown.layer_id == "wall_gp_0");
  CHECK(result.points[1].breakdown.time_s == Catch::Approx(0.0));
  CHECK(result.points[1].breakdown.layer_id == "wall_gp_1");
  CHECK(result.points[2].breakdown.time_s == Catch::Approx(10.0));
  CHECK(result.points[2].breakdown.layer_id == "wall_gp_0");
  CHECK(result.points[3].breakdown.time_s == Catch::Approx(10.0));
  CHECK(result.points[3].breakdown.layer_id == "wall_gp_1");
  CHECK(result.points[4].breakdown.time_s == Catch::Approx(20.0));
  CHECK(result.points[4].breakdown.layer_id == "wall_gp_0");
  CHECK(result.points[5].breakdown.time_s == Catch::Approx(20.0));
  CHECK(result.points[5].breakdown.layer_id == "wall_gp_1");

  CHECK_FALSE(result.points[0].breakdown.opened);
  CHECK_FALSE(result.points[1].breakdown.opened);
  CHECK(result.points[2].breakdown.opened);
  CHECK_FALSE(result.points[3].breakdown.opened);
  CHECK(result.points[4].breakdown.opened);
  CHECK(result.points[5].breakdown.opened);
}

TEST_CASE("LotSaltSigmaThetaDiagnostic preserves wall stress metadata") {
  const auto pkn = make_pkn_result({0.0}, {50.0 * kMPa});
  const lss::coupling::LotSaltCouplingConfig config;
  auto sample = make_sample(45.0 * kMPa, 11, 22, 33, 0.20, 9.0, 3100.0);
  sample.mean_stress_Pa = 21.0 * kMPa;
  sample.j2_Pa2 = 16.0;
  sample.von_mises_effective_stress_Pa = std::sqrt(48.0);
  const auto wall_stress = make_wall_stress({sample});

  const auto result = lss::coupling::evaluate_lot_salt_sigma_theta_step(
      pkn, 0, config, wall_stress);

  REQUIRE(result.points.size() == 1);
  const auto& point = result.points[0];
  CHECK(point.wall_stress_gp_id == 11);
  CHECK(point.wall_stress_element_id == 22);
  CHECK(point.wall_stress_local_gp_id == 33);
  CHECK(point.wall_stress_r_m == Catch::Approx(0.20));
  CHECK(point.wall_stress_z_m == Catch::Approx(9.0));
  CHECK(point.wall_stress_depth_m == Catch::Approx(3100.0));
  CHECK(point.mean_stress_Pa == Catch::Approx(21.0 * kMPa));
  CHECK(point.j2_Pa2 == Catch::Approx(16.0));
  CHECK(point.von_mises_effective_stress_Pa == Catch::Approx(std::sqrt(48.0)));
}

TEST_CASE("LotSaltSigmaThetaDiagnostic rejects invalid inputs") {
  const auto pkn = make_pkn_result({0.0}, {1.0});
  const lss::coupling::LotSaltCouplingConfig config;
  const auto wall_stress = make_wall_stress({make_sample(1.0)});
  const double nan = std::numeric_limits<double>::quiet_NaN();
  const double inf = std::numeric_limits<double>::infinity();

  CHECK_THROWS_AS(lss::coupling::evaluate_lot_salt_sigma_theta_step(
                      make_pkn_result({}, {}), 0, config, wall_stress),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_lot_salt_sigma_theta_step(
                      make_pkn_result({0.0, 1.0}, {1.0}), 0, config,
                      wall_stress),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_lot_salt_sigma_theta_step(
                      pkn, 1, config, wall_stress),
                  std::out_of_range);

  auto invalid_wall_stress = wall_stress;
  invalid_wall_stress.valid = false;
  CHECK_THROWS_AS(lss::coupling::evaluate_lot_salt_sigma_theta_step(
                      pkn, 0, config, invalid_wall_stress),
                  std::invalid_argument);

  invalid_wall_stress = wall_stress;
  invalid_wall_stress.wall_samples.clear();
  CHECK_THROWS_AS(lss::coupling::evaluate_lot_salt_sigma_theta_step(
                      pkn, 0, config, invalid_wall_stress),
                  std::invalid_argument);

  invalid_wall_stress = make_wall_stress({make_sample(-1.0)});
  CHECK_THROWS_AS(lss::coupling::evaluate_lot_salt_sigma_theta_step(
                      pkn, 0, config, invalid_wall_stress),
                  std::invalid_argument);

  invalid_wall_stress = make_wall_stress({make_sample(nan)});
  CHECK_THROWS_AS(lss::coupling::evaluate_lot_salt_sigma_theta_step(
                      pkn, 0, config, invalid_wall_stress),
                  std::invalid_argument);

  invalid_wall_stress = make_wall_stress({make_sample(inf)});
  CHECK_THROWS_AS(lss::coupling::evaluate_lot_salt_sigma_theta_step(
                      pkn, 0, config, invalid_wall_stress),
                  std::invalid_argument);

  auto invalid_sample = make_sample(1.0);
  invalid_sample.depth_m = nan;
  invalid_wall_stress = make_wall_stress({invalid_sample});
  CHECK_THROWS_AS(lss::coupling::evaluate_lot_salt_sigma_theta_step(
                      pkn, 0, config, invalid_wall_stress),
                  std::invalid_argument);

  invalid_sample = make_sample(1.0);
  invalid_sample.r_m = inf;
  invalid_wall_stress = make_wall_stress({invalid_sample});
  CHECK_THROWS_AS(lss::coupling::evaluate_lot_salt_sigma_theta_step(
                      pkn, 0, config, invalid_wall_stress),
                  std::invalid_argument);

  invalid_sample = make_sample(1.0);
  invalid_sample.z_m = nan;
  invalid_wall_stress = make_wall_stress({invalid_sample});
  CHECK_THROWS_AS(lss::coupling::evaluate_lot_salt_sigma_theta_step(
                      pkn, 0, config, invalid_wall_stress),
                  std::invalid_argument);

  invalid_sample = make_sample(1.0);
  invalid_sample.j2_Pa2 = -1.0;
  invalid_wall_stress = make_wall_stress({invalid_sample});
  CHECK_THROWS_AS(lss::coupling::evaluate_lot_salt_sigma_theta_step(
                      pkn, 0, config, invalid_wall_stress),
                  std::invalid_argument);

  invalid_sample = make_sample(1.0);
  invalid_sample.von_mises_effective_stress_Pa = -1.0;
  invalid_wall_stress = make_wall_stress({invalid_sample});
  CHECK_THROWS_AS(lss::coupling::evaluate_lot_salt_sigma_theta_step(
                      pkn, 0, config, invalid_wall_stress),
                  std::invalid_argument);
}
