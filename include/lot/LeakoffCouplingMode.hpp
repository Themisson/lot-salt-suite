#pragma once

#include <string>
#include <string_view>

namespace lss::lot {

enum class LeakoffCouplingMode {
  LegacyNodalForce,
  VolumeBalance,
};

struct LeakoffCouplingInput {
  double dV_m3 = 0.0;
  double dV_leakoff_m3 = 0.0;
};

struct LeakoffCouplingResult {
  double coupled_dV_m3 = 0.0;
  bool volume_balance_applied = false;
  bool legacy_nodal_force_preserved = false;
  std::string sign_convention;
};

[[nodiscard]] LeakoffCouplingMode parse_leakoff_coupling_mode(
    std::string_view value);

[[nodiscard]] std::string_view to_string(LeakoffCouplingMode mode);

[[nodiscard]] LeakoffCouplingResult apply_leakoff_coupling(
    LeakoffCouplingMode mode,
    const LeakoffCouplingInput& input);

}  // namespace lss::lot
