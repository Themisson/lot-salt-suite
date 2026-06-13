#pragma once

#include <string>
#include <string_view>

namespace lss::lot {

enum class SaltDisplacementMode {
  LegacyInsideNewton,
  PreIterative,
};

struct SaltDisplacementExecutionInput {
  int layer_count = 0;
  int newton_iteration_count = 0;
};

struct SaltDisplacementExecutionResult {
  int solve_calls = 0;
  bool pre_iterative = false;
  bool legacy_inside_newton_preserved = false;
  std::string usage;
};

[[nodiscard]] SaltDisplacementMode parse_salt_displacement_mode(
    std::string_view value);

[[nodiscard]] std::string_view to_string(SaltDisplacementMode mode);

[[nodiscard]] SaltDisplacementExecutionResult plan_salt_displacement_execution(
    SaltDisplacementMode mode,
    const SaltDisplacementExecutionInput& input);

}  // namespace lss::lot
