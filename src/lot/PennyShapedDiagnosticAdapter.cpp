#include "lot/PennyShapedDiagnosticAdapter.hpp"

namespace lss::lot {

PennyShapedInput make_penny_shaped_input(
    const PennyShapedDiagnosticInput& input) {
  PennyShapedInput model_input;
  model_input.young_modulus_Pa = input.young_modulus_Pa;
  model_input.poisson_ratio = input.poisson_ratio;
  model_input.viscosity_Pa_min = input.viscosity_Pa_min;
  model_input.flow_rate_m3_min = input.flow_rate_m3_min;
  model_input.elapsed_since_opening_min = input.elapsed_since_opening_min;
  model_input.wellbore_pressure_Pa = input.wellbore_pressure_Pa;
  model_input.sigma_theta_compression_positive_Pa =
      input.sigma_theta_compression_positive_Pa;
  model_input.volume_multiplier = input.volume_multiplier;
  return model_input;
}

PennyShapedDiagnosticResult run_penny_shaped_diagnostic(
    const PennyShapedDiagnosticInput& input) {
  PennyShapedDiagnosticResult result;
  result.model_result = evaluate_penny_shaped_model(
      make_penny_shaped_input(input));
  result.valid = true;
  result.source = input.source;
  result.caveat = input.caveat;
  result.status = "PENNY_SHAPED_DIAGNOSTIC_ADAPTER_OK";
  return result;
}

}  // namespace lss::lot
