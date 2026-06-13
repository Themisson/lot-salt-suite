#include "lot/SaltDisplacementMode.hpp"

#include <stdexcept>

namespace lss::lot {

SaltDisplacementMode parse_salt_displacement_mode(std::string_view value) {
  if (value == "legacy_inside_newton") {
    return SaltDisplacementMode::LegacyInsideNewton;
  }
  if (value == "pre_iterative") {
    return SaltDisplacementMode::PreIterative;
  }
  throw std::invalid_argument(
      "SaltDisplacementMode: expected legacy_inside_newton or pre_iterative");
}

std::string_view to_string(SaltDisplacementMode mode) {
  switch (mode) {
    case SaltDisplacementMode::LegacyInsideNewton:
      return "legacy_inside_newton";
    case SaltDisplacementMode::PreIterative:
      return "pre_iterative";
  }
  return "unknown";
}

SaltDisplacementExecutionResult plan_salt_displacement_execution(
    SaltDisplacementMode mode,
    const SaltDisplacementExecutionInput& input) {
  if (input.layer_count < 0 || input.newton_iteration_count < 0) {
    throw std::invalid_argument(
        "SaltDisplacementMode: layer and iteration counts must be non-negative");
  }

  SaltDisplacementExecutionResult result;
  switch (mode) {
    case SaltDisplacementMode::LegacyInsideNewton:
      result.solve_calls = input.layer_count * input.newton_iteration_count;
      result.legacy_inside_newton_preserved = true;
      result.usage =
          "solveThermalViscoStep is conceptually called inside each Newton iteration";
      return result;
    case SaltDisplacementMode::PreIterative:
      result.solve_calls = input.layer_count;
      result.pre_iterative = true;
      result.usage =
          "solveThermalViscoStep is called once per layer before pressure iterations";
      return result;
  }

  throw std::invalid_argument("SaltDisplacementMode: unsupported mode");
}

}  // namespace lss::lot
