#include <fstream>
#include <iterator>
#include <string>
#include <stdexcept>

#include <catch2/catch_test_macros.hpp>

#include "lot/PostDrillingSigmaThetaProvider.hpp"

namespace {

lss::lot::PostDrillingSigmaThetaProviderInput valid_input(
    lss::lot::PostDrillingSigmaThetaSource source =
        lss::lot::PostDrillingSigmaThetaSource::ExplicitDiagnosticInput) {
  lss::lot::PostDrillingSigmaThetaProviderInput input;
  input.source = source;
  input.sigma_theta_initial_compression_positive_Pa = 5.0e6;
  input.sigma_theta_current_compression_positive_Pa = 4.5e6;
  input.wellbore_pressure_Pa = 6.0e6;
  input.tensile_strength_Pa = 0.0;
  input.physically_validated = false;
  input.legacy_equivalent = false;
  return input;
}

std::string read_text_file(const std::string& path) {
  std::ifstream in(path);
  return {std::istreambuf_iterator<char>(in),
          std::istreambuf_iterator<char>()};
}

bool contains(const std::vector<std::string>& values, const std::string& value) {
  for (const auto& item : values) {
    if (item == value) {
      return true;
    }
  }
  return false;
}

}  // namespace

TEST_CASE("PostDrillingSigmaThetaProvider accepts explicit diagnostic input") {
  const auto result =
      lss::lot::evaluate_post_drilling_sigma_theta(valid_input());

  CHECK(result.available);
  CHECK(result.source == "EXPLICIT_DIAGNOSTIC_INPUT");
  CHECK(result.state_time == "POST_DRILLING_BEFORE_LOT");
  CHECK(result.sign_convention == "COMPRESSION_POSITIVE");
  CHECK(result.reference_frame == "WELLBORE_WALL_TOTAL_STRESS");
  CHECK_FALSE(result.physically_validated);
  CHECK_FALSE(result.legacy_equivalent);
  CHECK(contains(result.caveats, "DIAGNOSTIC_SOURCE_ONLY"));
}

TEST_CASE("PostDrillingSigmaThetaProvider accepts synthetic fixture source") {
  const auto result = lss::lot::evaluate_post_drilling_sigma_theta(
      valid_input(lss::lot::PostDrillingSigmaThetaSource::SyntheticFixture));

  CHECK(result.available);
  CHECK(result.source == "SYNTHETIC_FIXTURE");
  CHECK(contains(result.caveats, "DIAGNOSTIC_SOURCE_ONLY"));
}

TEST_CASE("PostDrillingSigmaThetaProvider marks elastic source as semi physical") {
  const auto result = lss::lot::evaluate_post_drilling_sigma_theta(valid_input(
      lss::lot::PostDrillingSigmaThetaSource::ElasticInitialWellboreState));

  CHECK(result.available);
  CHECK(result.source == "ELASTIC_INITIAL_WELLBORE_STATE");
  CHECK(contains(result.caveats, "SEMI_PHYSICAL_ELASTIC_APPROXIMATION"));
  CHECK(contains(result.caveats, "NOT_PHYSICALLY_VALIDATED"));
  CHECK(contains(result.caveats, "NOT_LEGACY_EQUIVALENT"));
}

TEST_CASE("PostDrillingSigmaThetaProvider rejects unknown source") {
  auto input = valid_input();
  input.source = lss::lot::PostDrillingSigmaThetaSource::Unknown;

  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);
}

TEST_CASE("PostDrillingSigmaThetaProvider rejects invalid sigma theta values") {
  auto input = valid_input();
  input.sigma_theta_initial_compression_positive_Pa = 0.0;
  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);

  input = valid_input();
  input.sigma_theta_current_compression_positive_Pa = -1.0;
  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);
}

TEST_CASE("PostDrillingSigmaThetaProvider rejects invalid pressure values") {
  auto input = valid_input();
  input.wellbore_pressure_Pa = -1.0;
  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);

  input = valid_input();
  input.tensile_strength_Pa = -1.0;
  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);
}

TEST_CASE("PostDrillingSigmaThetaProvider rejects physical validation flags") {
  auto input = valid_input();
  input.physically_validated = true;
  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);

  input = valid_input();
  input.legacy_equivalent = true;
  CHECK_THROWS_AS(lss::lot::evaluate_post_drilling_sigma_theta(input),
                  std::runtime_error);
}

TEST_CASE("PostDrillingSigmaThetaProvider preserves numeric inputs") {
  const auto result =
      lss::lot::evaluate_post_drilling_sigma_theta(valid_input());

  CHECK(result.sigma_theta_initial_compression_positive_Pa == 5.0e6);
  CHECK(result.sigma_theta_current_compression_positive_Pa == 4.5e6);
  CHECK(result.wellbore_pressure_Pa == 6.0e6);
  CHECK(result.tensile_strength_Pa == 0.0);
}

TEST_CASE("PostDrillingSigmaThetaProvider remains isolated from physical dispatch") {
  const auto header = read_text_file("include/lot/PostDrillingSigmaThetaProvider.hpp");
  const auto source = read_text_file("src/lot/PostDrillingSigmaThetaProvider.cpp");

  CHECK(header.find("PknModel") == std::string::npos);
  CHECK(header.find("PknRunner") == std::string::npos);
  CHECK(header.find("PennyShapedDiagnosticAdapter") == std::string::npos);
  CHECK(source.find("PknModel") == std::string::npos);
  CHECK(source.find("PknRunner") == std::string::npos);
  CHECK(source.find("PennyShapedDiagnosticAdapter") == std::string::npos);
}
