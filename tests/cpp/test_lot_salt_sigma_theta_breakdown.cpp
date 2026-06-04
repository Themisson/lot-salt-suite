#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "coupling/LotSaltSigmaThetaBreakdown.hpp"

namespace {

lss::coupling::SigmaThetaInfluenceLayer make_layer(
    std::string layer_id = "salt",
    double influence_depth_m = 3000.0,
    double sigma_theta_compression_positive_Pa = 45.0e6) {
  lss::coupling::SigmaThetaInfluenceLayer layer;
  layer.layer_id = std::move(layer_id);
  layer.influence_depth_m = influence_depth_m;
  layer.sigma_theta_compression_positive_Pa =
      sigma_theta_compression_positive_Pa;
  return layer;
}

}  // namespace

TEST_CASE("SigmaThetaBreakdown point remains closed below sigma theta") {
  const auto point = lss::coupling::evaluate_sigma_theta_breakdown_point(
      make_layer("salt", 3000.0, 45.0e6), 60.0, 40.0e6);

  CHECK(point.layer_id == "salt");
  CHECK(point.influence_depth_m == Catch::Approx(3000.0));
  CHECK(point.time_s == Catch::Approx(60.0));
  CHECK(point.pressure_Pa == Catch::Approx(40.0e6));
  CHECK(point.sigma_theta_compression_positive_Pa == Catch::Approx(45.0e6));
  CHECK(point.margin_Pa == Catch::Approx(-5.0e6));
  CHECK(point.opened == false);
}

TEST_CASE("SigmaThetaBreakdown point opens above sigma theta") {
  const auto point = lss::coupling::evaluate_sigma_theta_breakdown_point(
      make_layer("salt", 3000.0, 45.0e6), 60.0, 50.0e6);

  CHECK(point.margin_Pa == Catch::Approx(5.0e6));
  CHECK(point.opened == true);
}

TEST_CASE("SigmaThetaBreakdown equality does not open") {
  const auto point = lss::coupling::evaluate_sigma_theta_breakdown_point(
      make_layer("salt", 3000.0, 45.0e6), 60.0, 45.0e6);

  CHECK(point.margin_Pa == Catch::Approx(0.0));
  CHECK(point.opened == false);
}

TEST_CASE("SigmaThetaBreakdown series evaluates multiple layers and times") {
  const std::vector<lss::coupling::SigmaThetaInfluenceLayer> layers = {
      make_layer("salt_top", 2800.0, 45.0e6),
      make_layer("salt_base", 3300.0, 55.0e6),
  };
  const std::vector<double> times_s = {0.0, 30.0, 60.0};
  const std::vector<double> pressures_Pa = {40.0e6, 50.0e6, 60.0e6};

  const auto result = lss::coupling::evaluate_sigma_theta_breakdown_series(
      layers, times_s, pressures_Pa);

  REQUIRE(result.points.size() == 6);
  CHECK(result.any_opened == true);

  CHECK(result.points[0].layer_id == "salt_top");
  CHECK(result.points[0].time_s == Catch::Approx(0.0));
  CHECK(result.points[0].margin_Pa == Catch::Approx(-5.0e6));
  CHECK(result.points[0].opened == false);

  CHECK(result.points[1].layer_id == "salt_base");
  CHECK(result.points[1].time_s == Catch::Approx(0.0));
  CHECK(result.points[1].margin_Pa == Catch::Approx(-15.0e6));
  CHECK(result.points[1].opened == false);

  CHECK(result.points[2].layer_id == "salt_top");
  CHECK(result.points[2].time_s == Catch::Approx(30.0));
  CHECK(result.points[2].margin_Pa == Catch::Approx(5.0e6));
  CHECK(result.points[2].opened == true);

  CHECK(result.points[3].layer_id == "salt_base");
  CHECK(result.points[3].time_s == Catch::Approx(30.0));
  CHECK(result.points[3].margin_Pa == Catch::Approx(-5.0e6));
  CHECK(result.points[3].opened == false);

  CHECK(result.points[4].layer_id == "salt_top");
  CHECK(result.points[4].time_s == Catch::Approx(60.0));
  CHECK(result.points[4].margin_Pa == Catch::Approx(15.0e6));
  CHECK(result.points[4].opened == true);

  CHECK(result.points[5].layer_id == "salt_base");
  CHECK(result.points[5].time_s == Catch::Approx(60.0));
  CHECK(result.points[5].margin_Pa == Catch::Approx(5.0e6));
  CHECK(result.points[5].opened == true);
}

TEST_CASE("SigmaThetaBreakdown series returns points in time-major order") {
  const std::vector<lss::coupling::SigmaThetaInfluenceLayer> layers = {
      make_layer("a", 1000.0, 10.0),
      make_layer("b", 2000.0, 20.0),
  };
  const std::vector<double> times_s = {1.0, 2.0};
  const std::vector<double> pressures_Pa = {15.0, 25.0};

  const auto result = lss::coupling::evaluate_sigma_theta_breakdown_series(
      layers, times_s, pressures_Pa);

  REQUIRE(result.points.size() == 4);
  CHECK(result.points[0].time_s == Catch::Approx(1.0));
  CHECK(result.points[0].layer_id == "a");
  CHECK(result.points[1].time_s == Catch::Approx(1.0));
  CHECK(result.points[1].layer_id == "b");
  CHECK(result.points[2].time_s == Catch::Approx(2.0));
  CHECK(result.points[2].layer_id == "a");
  CHECK(result.points[3].time_s == Catch::Approx(2.0));
  CHECK(result.points[3].layer_id == "b");
}

TEST_CASE("SigmaThetaBreakdown rejects invalid point inputs") {
  const double nan = std::numeric_limits<double>::quiet_NaN();
  const double inf = std::numeric_limits<double>::infinity();

  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_point(
                      make_layer(), 0.0, -1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_point(
                      make_layer(), 0.0, nan),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_point(
                      make_layer(), 0.0, inf),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_point(
                      make_layer("salt", 3000.0, -1.0), 0.0, 1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_point(
                      make_layer("salt", 3000.0, nan), 0.0, 1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_point(
                      make_layer("salt", 3000.0, inf), 0.0, 1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_point(
                      make_layer(), -1.0, 1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_point(
                      make_layer(), nan, 1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_point(
                      make_layer(), inf, 1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_point(
                      make_layer("salt", -1.0, 45.0e6), 0.0, 1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_point(
                      make_layer("salt", nan, 45.0e6), 0.0, 1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_point(
                      make_layer("salt", inf, 45.0e6), 0.0, 1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_point(
                      make_layer("", 3000.0, 45.0e6), 0.0, 1.0),
                  std::invalid_argument);
}

TEST_CASE("SigmaThetaBreakdown rejects invalid series inputs") {
  const std::vector<lss::coupling::SigmaThetaInfluenceLayer> layers = {
      make_layer()};
  const std::vector<double> times_s = {0.0};
  const std::vector<double> pressures_Pa = {1.0};

  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_series(
                      {}, times_s, pressures_Pa),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_series(
                      layers, {}, pressures_Pa),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::coupling::evaluate_sigma_theta_breakdown_series(
                      layers, {0.0, 1.0}, pressures_Pa),
                  std::invalid_argument);
}
