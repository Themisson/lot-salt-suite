#include "lot/LeakoffCouplingMode.hpp"

#include <cmath>
#include <stdexcept>
#include <string>

namespace lss::lot {
namespace {

void require_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("LeakoffCouplingMode: " + field +
                                " must be finite");
  }
}

}  // namespace

LeakoffCouplingMode parse_leakoff_coupling_mode(std::string_view value) {
  if (value == "legacy_nodal_force") {
    return LeakoffCouplingMode::LegacyNodalForce;
  }
  if (value == "volume_balance") {
    return LeakoffCouplingMode::VolumeBalance;
  }
  throw std::invalid_argument(
      "LeakoffCouplingMode: expected legacy_nodal_force or volume_balance");
}

std::string_view to_string(LeakoffCouplingMode mode) {
  switch (mode) {
    case LeakoffCouplingMode::LegacyNodalForce:
      return "legacy_nodal_force";
    case LeakoffCouplingMode::VolumeBalance:
      return "volume_balance";
  }
  return "unknown";
}

LeakoffCouplingResult apply_leakoff_coupling(
    LeakoffCouplingMode mode,
    const LeakoffCouplingInput& input) {
  require_finite(input.dV_m3, "dV_m3");
  require_finite(input.dV_leakoff_m3, "dV_leakoff_m3");

  LeakoffCouplingResult result;
  result.sign_convention =
      "positive dV_leakoff_m3 is added to dV_m3 by volume_balance";

  switch (mode) {
    case LeakoffCouplingMode::LegacyNodalForce:
      result.coupled_dV_m3 = input.dV_m3;
      result.legacy_nodal_force_preserved = true;
      return result;
    case LeakoffCouplingMode::VolumeBalance:
      result.coupled_dV_m3 = input.dV_m3 + input.dV_leakoff_m3;
      result.volume_balance_applied = true;
      return result;
  }

  throw std::invalid_argument("LeakoffCouplingMode: unsupported mode");
}

}  // namespace lss::lot
