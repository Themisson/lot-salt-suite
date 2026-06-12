#pragma once

#include <string>

#include "lot/PennyShapedModel.hpp"

namespace lss::lot {

struct PennyShapedDiagnosticInput {
  double young_modulus_Pa = 0.0;
  double poisson_ratio = 0.0;
  double viscosity_Pa_min = 0.0;
  double flow_rate_m3_min = 0.0;
  double elapsed_since_opening_min = 0.0;
  double wellbore_pressure_Pa = 0.0;
  double sigma_theta_compression_positive_Pa = 0.0;
  double volume_multiplier = 10.0;

  std::string source = "synthetic";
  std::string caveat =
      "Diagnostic adapter only. Not BUZ29 validation. Not legacy equivalence.";
};

struct PennyShapedDiagnosticResult {
  PennyShapedResult model_result;
  bool valid = false;
  std::string source;
  std::string caveat;
  std::string status;
};

[[nodiscard]] PennyShapedInput
make_penny_shaped_input(const PennyShapedDiagnosticInput& input);

[[nodiscard]] PennyShapedDiagnosticResult run_penny_shaped_diagnostic(
    const PennyShapedDiagnosticInput& input);

}  // namespace lss::lot
