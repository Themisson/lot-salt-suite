#include "coupling/LotSaltPressureMap.hpp"

#include <cmath>
#include <stdexcept>
#include <string>

namespace lss::coupling {
namespace {

void require_non_negative_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("LotSaltPressureMap: " + field +
                                " must be finite");
  }
  if (value < 0.0) {
    throw std::invalid_argument("LotSaltPressureMap: " + field +
                                " must be non-negative");
  }
}

LotSaltPressureMapResult make_result(double wall_pressure_Pa,
                                     LotSaltPressureMapMethod method,
                                     bool physically_absolute) {
  LotSaltPressureMapResult result;
  result.wall_pressure_Pa = wall_pressure_Pa;
  result.method = method;
  result.method_label = to_string(method);
  result.physically_absolute = physically_absolute;
  return result;
}

}  // namespace

const char* to_string(LotSaltPressureMapMethod method) {
  switch (method) {
    case LotSaltPressureMapMethod::ExperimentalNetPressureProxy:
      return "experimental_net_pressure_proxy";
    case LotSaltPressureMapMethod::AbsoluteWellborePressure:
      return "absolute_wellbore_pressure";
    case LotSaltPressureMapMethod::HydrostaticPlusNetPressure:
      return "hydrostatic_plus_net_pressure";
  }
  throw std::invalid_argument("LotSaltPressureMap: unknown pressure map method");
}

LotSaltPressureMapResult map_lot_pkn_to_salt_wall_pressure(
    const LotSaltPressureMapInput& input) {
  switch (input.method) {
    case LotSaltPressureMapMethod::ExperimentalNetPressureProxy:
      require_non_negative_finite(input.net_pressure_Pa, "net_pressure_Pa");
      return make_result(input.net_pressure_Pa, input.method, false);

    case LotSaltPressureMapMethod::AbsoluteWellborePressure:
      require_non_negative_finite(input.absolute_wellbore_pressure_Pa,
                                  "absolute_wellbore_pressure_Pa");
      return make_result(input.absolute_wellbore_pressure_Pa, input.method,
                         true);

    case LotSaltPressureMapMethod::HydrostaticPlusNetPressure: {
      require_non_negative_finite(input.surface_pressure_Pa,
                                  "surface_pressure_Pa");
      require_non_negative_finite(input.hydrostatic_pressure_Pa,
                                  "hydrostatic_pressure_Pa");
      require_non_negative_finite(input.net_pressure_Pa, "net_pressure_Pa");
      const double wall_pressure_Pa = input.surface_pressure_Pa +
                                      input.hydrostatic_pressure_Pa +
                                      input.net_pressure_Pa;
      require_non_negative_finite(wall_pressure_Pa, "wall_pressure_Pa");
      return make_result(wall_pressure_Pa, input.method, true);
    }
  }
  throw std::invalid_argument("LotSaltPressureMap: unknown pressure map method");
}

}  // namespace lss::coupling
