#include "coupling/LotSaltCouplingConfigBuilder.hpp"

#include <cmath>
#include <stdexcept>
#include <string>

namespace lss::coupling {
namespace {

void require_non_negative_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("LotSaltCouplingConfigBuilder: " + field +
                                " must be finite");
  }
  if (value < 0.0) {
    throw std::invalid_argument("LotSaltCouplingConfigBuilder: " + field +
                                " must be non-negative");
  }
}

void require_positive_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("LotSaltCouplingConfigBuilder: " + field +
                                " must be finite");
  }
  if (value <= 0.0) {
    throw std::invalid_argument("LotSaltCouplingConfigBuilder: " + field +
                                " must be positive");
  }
}

void validate_options(const LotSaltCouplingConfigOptions& options) {
  require_non_negative_finite(options.radial_position_m, "radial_position_m");
  require_positive_finite(options.temperature_K, "temperature_K");
  require_non_negative_finite(options.surface_pressure_Pa,
                              "surface_pressure_Pa");
  (void)to_string(options.method);
}

}  // namespace

LotSaltCouplingConfig
make_lot_salt_coupling_config_from_hydrostatic_context(
    const LotSaltHydrostaticContext& context,
    const LotSaltCouplingConfigOptions& options) {
  validate_options(options);

  LotSaltCouplingConfig config;
  config.radial_position_m = options.radial_position_m;
  config.temperature_K = options.temperature_K;
  config.surface_pressure_Pa = options.surface_pressure_Pa;
  config.pressure_map_method = options.method;
  config.hydrostatic_pressure_Pa = context.hydrostatic_pressure_Pa;
  config.depth_m = context.depth_m;
  return config;
}

LotSaltCouplingConfig make_hydrostatic_lot_salt_coupling_config(
    const lss::core::CaseData& data,
    const LotSaltCouplingConfigOptions& options) {
  const LotSaltHydrostaticContext context =
      make_lot_salt_hydrostatic_context(data);
  return make_lot_salt_coupling_config_from_hydrostatic_context(context,
                                                                options);
}

}  // namespace lss::coupling
