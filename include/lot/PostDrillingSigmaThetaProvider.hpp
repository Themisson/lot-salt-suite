#pragma once

#include <string>
#include <vector>

namespace lss::lot {

enum class PostDrillingSigmaThetaSource {
  ExplicitDiagnosticInput,
  SyntheticFixture,
  ElasticInitialWellboreState,
  Unknown,
};

struct PostDrillingSigmaThetaProviderInput {
  PostDrillingSigmaThetaSource source =
      PostDrillingSigmaThetaSource::Unknown;
  double sigma_theta_initial_compression_positive_Pa = 0.0;
  double sigma_theta_current_compression_positive_Pa = 0.0;
  double far_field_stress_compression_positive_Pa = 0.0;
  double wellbore_pressure_Pa = 0.0;
  double tensile_strength_Pa = 0.0;
  bool physically_validated = false;
  bool legacy_equivalent = false;
};

struct PostDrillingSigmaThetaProviderResult {
  bool available = false;
  double sigma_theta_initial_compression_positive_Pa = 0.0;
  double sigma_theta_current_compression_positive_Pa = 0.0;
  double far_field_stress_compression_positive_Pa = 0.0;
  double wellbore_pressure_Pa = 0.0;
  double tensile_strength_Pa = 0.0;
  std::string source;
  std::string state_time;
  std::string sign_convention;
  std::string reference_frame;
  bool physically_validated = false;
  bool legacy_equivalent = false;
  std::vector<std::string> caveats;
};

[[nodiscard]] const char* to_string(PostDrillingSigmaThetaSource source);

[[nodiscard]] PostDrillingSigmaThetaProviderResult
evaluate_post_drilling_sigma_theta(
    const PostDrillingSigmaThetaProviderInput& input);

}  // namespace lss::lot
