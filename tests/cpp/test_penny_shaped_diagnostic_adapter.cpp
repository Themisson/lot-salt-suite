#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "lot/PennyShapedDiagnosticAdapter.hpp"
#include "lot/PennyShapedModel.hpp"

namespace {

lss::lot::PennyShapedDiagnosticInput valid_input() {
  lss::lot::PennyShapedDiagnosticInput input;
  input.young_modulus_Pa = 5.71e6;
  input.poisson_ratio = 0.36;
  input.viscosity_Pa_min = 180.0;
  input.flow_rate_m3_min = 0.05;
  input.elapsed_since_opening_min = 1.25;
  input.wellbore_pressure_Pa = 6.7e7;
  input.sigma_theta_compression_positive_Pa = 6.6e7;
  input.volume_multiplier = 10.0;
  input.source = "synthetic_fixture";
  return input;
}

}  // namespace

TEST_CASE("PennyShapedDiagnosticAdapter maps diagnostic input to model input") {
  const auto diagnostic_input = valid_input();

  const auto model_input =
      lss::lot::make_penny_shaped_input(diagnostic_input);

  CHECK(model_input.young_modulus_Pa ==
        Catch::Approx(diagnostic_input.young_modulus_Pa));
  CHECK(model_input.poisson_ratio ==
        Catch::Approx(diagnostic_input.poisson_ratio));
  CHECK(model_input.viscosity_Pa_min ==
        Catch::Approx(diagnostic_input.viscosity_Pa_min));
  CHECK(model_input.flow_rate_m3_min ==
        Catch::Approx(diagnostic_input.flow_rate_m3_min));
  CHECK(model_input.elapsed_since_opening_min ==
        Catch::Approx(diagnostic_input.elapsed_since_opening_min));
  CHECK(model_input.wellbore_pressure_Pa ==
        Catch::Approx(diagnostic_input.wellbore_pressure_Pa));
  CHECK(model_input.sigma_theta_compression_positive_Pa ==
        Catch::Approx(
            diagnostic_input.sigma_theta_compression_positive_Pa));
  CHECK(model_input.volume_multiplier ==
        Catch::Approx(diagnostic_input.volume_multiplier));
}

TEST_CASE("PennyShapedDiagnosticAdapter returns finite diagnostic result") {
  const auto result = lss::lot::run_penny_shaped_diagnostic(valid_input());

  CHECK(result.valid);
  CHECK(result.status == "PENNY_SHAPED_DIAGNOSTIC_ADAPTER_OK");
  CHECK(result.source == "synthetic_fixture");
  CHECK(result.caveat.find("Not BUZ29 validation") != std::string::npos);
  CHECK(result.model_result.opening_m > 0.0);
  CHECK(result.model_result.radius_m > 0.0);
  CHECK(result.model_result.fracture_volume_proxy_m3 > 0.0);
}

TEST_CASE("PennyShapedDiagnosticAdapter preserves direct model result") {
  const auto diagnostic_input = valid_input();
  const auto adapter_result =
      lss::lot::run_penny_shaped_diagnostic(diagnostic_input);
  const auto direct_result = lss::lot::evaluate_penny_shaped_model(
      lss::lot::make_penny_shaped_input(diagnostic_input));

  CHECK(adapter_result.model_result.plane_strain_modulus_Pa ==
        Catch::Approx(direct_result.plane_strain_modulus_Pa));
  CHECK(adapter_result.model_result.opening_m ==
        Catch::Approx(direct_result.opening_m));
  CHECK(adapter_result.model_result.radius_m ==
        Catch::Approx(direct_result.radius_m));
  CHECK(adapter_result.model_result.pressure_factor ==
        Catch::Approx(direct_result.pressure_factor));
  CHECK(adapter_result.model_result.fracture_volume_proxy_m3 ==
        Catch::Approx(direct_result.fracture_volume_proxy_m3));
}

TEST_CASE("PennyShapedDiagnosticAdapter propagates model validation") {
  auto input = valid_input();
  input.young_modulus_Pa = 0.0;
  CHECK_THROWS_AS(lss::lot::run_penny_shaped_diagnostic(input),
                  std::invalid_argument);

  input = valid_input();
  input.poisson_ratio = 0.5;
  CHECK_THROWS_AS(lss::lot::run_penny_shaped_diagnostic(input),
                  std::invalid_argument);

  input = valid_input();
  input.sigma_theta_compression_positive_Pa = 0.0;
  CHECK_THROWS_AS(lss::lot::run_penny_shaped_diagnostic(input),
                  std::invalid_argument);

  input = valid_input();
  input.wellbore_pressure_Pa = std::numeric_limits<double>::infinity();
  CHECK_THROWS_AS(lss::lot::run_penny_shaped_diagnostic(input),
                  std::invalid_argument);
}

TEST_CASE("PennyShapedDiagnosticAdapter stays independent from LOT PKN") {
  const auto result = lss::lot::run_penny_shaped_diagnostic(valid_input());

  CHECK(result.valid);
  CHECK(result.caveat.find("legacy equivalence") != std::string::npos);
}
