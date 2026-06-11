#include <cmath>
#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "lot/PennyShapedModel.hpp"

namespace {

lss::lot::PennyShapedInput valid_input() {
  lss::lot::PennyShapedInput input;
  input.young_modulus_Pa = 5.71e6;
  input.poisson_ratio = 0.36;
  input.viscosity_Pa_min = 180.0;
  input.flow_rate_m3_min = 0.05;
  input.elapsed_since_opening_min = 1.25;
  input.wellbore_pressure_Pa = 6.7e7;
  input.sigma_theta_compression_positive_Pa = 6.6e7;
  input.volume_multiplier = 10.0;
  return input;
}

}  // namespace

TEST_CASE("PennyShapedModel evaluates audited legacy formulas") {
  const auto input = valid_input();

  const auto result = lss::lot::evaluate_penny_shaped_model(input);

  const double epd =
      input.young_modulus_Pa /
      (1.0 - input.poisson_ratio * input.poisson_ratio);
  const double expected_opening =
      3.65 *
      std::pow((input.viscosity_Pa_min * input.viscosity_Pa_min *
                std::pow(input.flow_rate_m3_min, 3.0)) /
                   (epd * epd),
               1.0 / 9.0) *
      std::pow(input.elapsed_since_opening_min, 1.0 / 9.0);
  const double expected_radius =
      0.572 *
      std::pow((epd * std::pow(input.flow_rate_m3_min, 3.0)) /
                   input.viscosity_Pa_min,
               1.0 / 9.0) *
      std::pow(input.elapsed_since_opening_min, 4.0 / 9.0);
  const double expected_pressure_factor =
      input.wellbore_pressure_Pa /
      input.sigma_theta_compression_positive_Pa;
  const double expected_volume =
      input.volume_multiplier * std::pow(expected_opening / 2.0, 2.0) *
      expected_radius * 3.14159265358979323846 * expected_pressure_factor;

  CHECK(result.plane_strain_modulus_Pa == Catch::Approx(epd));
  CHECK(result.opening_m == Catch::Approx(expected_opening));
  CHECK(result.radius_m == Catch::Approx(expected_radius));
  CHECK(result.pressure_factor == Catch::Approx(expected_pressure_factor));
  CHECK(result.fracture_volume_proxy_m3 == Catch::Approx(expected_volume));
}

TEST_CASE("PennyShapedModel returns zero geometry before flow or elapsed time") {
  auto input = valid_input();
  input.elapsed_since_opening_min = 0.0;

  auto result = lss::lot::evaluate_penny_shaped_model(input);

  CHECK(result.plane_strain_modulus_Pa > 0.0);
  CHECK(result.pressure_factor > 0.0);
  CHECK(result.opening_m == 0.0);
  CHECK(result.radius_m == 0.0);
  CHECK(result.fracture_volume_proxy_m3 == 0.0);

  input = valid_input();
  input.flow_rate_m3_min = 0.0;
  result = lss::lot::evaluate_penny_shaped_model(input);

  CHECK(result.opening_m == 0.0);
  CHECK(result.radius_m == 0.0);
  CHECK(result.fracture_volume_proxy_m3 == 0.0);
}

TEST_CASE("PennyShapedModel validates elastic inputs") {
  auto input = valid_input();
  input.young_modulus_Pa = 0.0;
  CHECK_THROWS_AS(lss::lot::evaluate_penny_shaped_model(input),
                  std::invalid_argument);

  input = valid_input();
  input.poisson_ratio = 0.5;
  CHECK_THROWS_AS(lss::lot::evaluate_penny_shaped_model(input),
                  std::invalid_argument);

  input = valid_input();
  input.poisson_ratio = -0.1;
  CHECK_THROWS_AS(lss::lot::evaluate_penny_shaped_model(input),
                  std::invalid_argument);
}

TEST_CASE("PennyShapedModel validates fluid pressure and time inputs") {
  auto input = valid_input();
  input.viscosity_Pa_min = 0.0;
  CHECK_THROWS_AS(lss::lot::evaluate_penny_shaped_model(input),
                  std::invalid_argument);

  input = valid_input();
  input.elapsed_since_opening_min = -1.0;
  CHECK_THROWS_AS(lss::lot::evaluate_penny_shaped_model(input),
                  std::invalid_argument);

  input = valid_input();
  input.sigma_theta_compression_positive_Pa = 0.0;
  CHECK_THROWS_AS(lss::lot::evaluate_penny_shaped_model(input),
                  std::invalid_argument);
}

TEST_CASE("PennyShapedModel rejects non-finite inputs") {
  auto input = valid_input();
  input.flow_rate_m3_min = std::numeric_limits<double>::quiet_NaN();
  CHECK_THROWS_AS(lss::lot::evaluate_penny_shaped_model(input),
                  std::invalid_argument);

  input = valid_input();
  input.wellbore_pressure_Pa = std::numeric_limits<double>::infinity();
  CHECK_THROWS_AS(lss::lot::evaluate_penny_shaped_model(input),
                  std::invalid_argument);
}
