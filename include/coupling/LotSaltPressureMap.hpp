#pragma once

#include <string>

namespace lss::coupling {

enum class LotSaltPressureMapMethod {
  ExperimentalNetPressureProxy,
  AbsoluteWellborePressure,
  HydrostaticPlusNetPressure
};

struct LotSaltPressureMapInput {
  double net_pressure_Pa = 0.0;
  double absolute_wellbore_pressure_Pa = 0.0;
  double hydrostatic_pressure_Pa = 0.0;
  double surface_pressure_Pa = 0.0;
  double depth_m = 0.0;
  LotSaltPressureMapMethod method =
      LotSaltPressureMapMethod::ExperimentalNetPressureProxy;
};

struct LotSaltPressureMapResult {
  double wall_pressure_Pa = 0.0;
  LotSaltPressureMapMethod method =
      LotSaltPressureMapMethod::ExperimentalNetPressureProxy;
  std::string method_label;
  bool physically_absolute = false;
};

[[nodiscard]] const char* to_string(LotSaltPressureMapMethod method);

[[nodiscard]] LotSaltPressureMapResult map_lot_pkn_to_salt_wall_pressure(
    const LotSaltPressureMapInput& input);

}  // namespace lss::coupling
