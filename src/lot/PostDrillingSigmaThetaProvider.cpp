#include "lot/PostDrillingSigmaThetaProvider.hpp"

#include <cmath>
#include <stdexcept>

namespace lss::lot {
namespace {

void require_positive_finite(double value, const char* name) {
  if (!std::isfinite(value) || value <= 0.0) {
    throw std::runtime_error(std::string("PostDrillingSigmaThetaProvider: ") +
                             name + " must be finite and > 0");
  }
}

void require_nonnegative_finite(double value, const char* name) {
  if (!std::isfinite(value) || value < 0.0) {
    throw std::runtime_error(std::string("PostDrillingSigmaThetaProvider: ") +
                             name + " must be finite and >= 0");
  }
}

}  // namespace

const char* to_string(PostDrillingSigmaThetaSource source) {
  switch (source) {
    case PostDrillingSigmaThetaSource::ExplicitDiagnosticInput:
      return "EXPLICIT_DIAGNOSTIC_INPUT";
    case PostDrillingSigmaThetaSource::SyntheticFixture:
      return "SYNTHETIC_FIXTURE";
    case PostDrillingSigmaThetaSource::ElasticInitialWellboreState:
      return "ELASTIC_INITIAL_WELLBORE_STATE";
    case PostDrillingSigmaThetaSource::Unknown:
      return "UNKNOWN";
  }
  return "UNKNOWN";
}

PostDrillingSigmaThetaProviderResult evaluate_post_drilling_sigma_theta(
    const PostDrillingSigmaThetaProviderInput& input) {
  if (input.source == PostDrillingSigmaThetaSource::Unknown) {
    throw std::runtime_error(
        "PostDrillingSigmaThetaProvider: source must not be UNKNOWN");
  }
  if (input.physically_validated) {
    throw std::runtime_error(
        "PostDrillingSigmaThetaProvider: physically_validated must be false");
  }
  if (input.legacy_equivalent) {
    throw std::runtime_error(
        "PostDrillingSigmaThetaProvider: legacy_equivalent must be false");
  }

  require_positive_finite(input.sigma_theta_initial_compression_positive_Pa,
                          "sigma_theta_initial_compression_positive_Pa");
  require_positive_finite(input.sigma_theta_current_compression_positive_Pa,
                          "sigma_theta_current_compression_positive_Pa");
  require_nonnegative_finite(input.wellbore_pressure_Pa,
                             "wellbore_pressure_Pa");
  require_nonnegative_finite(input.tensile_strength_Pa,
                             "tensile_strength_Pa");

  PostDrillingSigmaThetaProviderResult result;
  result.available = true;
  result.sigma_theta_initial_compression_positive_Pa =
      input.sigma_theta_initial_compression_positive_Pa;
  result.sigma_theta_current_compression_positive_Pa =
      input.sigma_theta_current_compression_positive_Pa;
  result.wellbore_pressure_Pa = input.wellbore_pressure_Pa;
  result.tensile_strength_Pa = input.tensile_strength_Pa;
  result.source = to_string(input.source);
  result.state_time = "POST_DRILLING_BEFORE_LOT";
  result.sign_convention = "COMPRESSION_POSITIVE";
  result.reference_frame = "WELLBORE_WALL_TOTAL_STRESS";
  result.physically_validated = false;
  result.legacy_equivalent = false;

  if (input.source == PostDrillingSigmaThetaSource::ElasticInitialWellboreState) {
    result.caveats.push_back("SEMI_PHYSICAL_ELASTIC_APPROXIMATION");
    result.caveats.push_back("NOT_PHYSICALLY_VALIDATED");
    result.caveats.push_back("NOT_LEGACY_EQUIVALENT");
  } else {
    result.caveats.push_back("DIAGNOSTIC_SOURCE_ONLY");
    result.caveats.push_back("NOT_PHYSICALLY_VALIDATED");
    result.caveats.push_back("NOT_LEGACY_EQUIVALENT");
  }

  return result;
}

}  // namespace lss::lot
