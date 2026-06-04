#include "coupling/LotSaltSigmaThetaDiagnostic.hpp"

#include <cmath>
#include <stdexcept>
#include <string>
#include <utility>

#include "coupling/LotSaltCouplingStep.hpp"

namespace lss::coupling {
namespace {

void require_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("LotSaltSigmaThetaDiagnostic: " + field +
                                " must be finite");
  }
}

void require_non_negative_finite(double value, const std::string& field) {
  require_finite(value, field);
  if (value < 0.0) {
    throw std::invalid_argument("LotSaltSigmaThetaDiagnostic: " + field +
                                " must be non-negative");
  }
}

void validate_pkn_series(const lss::lot::PknResult& pkn_result) {
  if (pkn_result.time_series_s.empty()) {
    throw std::invalid_argument(
        "LotSaltSigmaThetaDiagnostic: time_series_s must not be empty");
  }
  if (pkn_result.time_series_s.size() !=
      pkn_result.net_pressure_series_Pa.size()) {
    throw std::invalid_argument(
        "LotSaltSigmaThetaDiagnostic: time and net pressure series sizes "
        "differ");
  }
}

void validate_wall_sample(const lss::salt::SaltWallStressSample& sample,
                          std::size_t sample_index) {
  const std::string prefix =
      "wall_samples[" + std::to_string(sample_index) + "].";
  require_finite(sample.r_m, prefix + "r_m");
  require_finite(sample.z_m, prefix + "z_m");
  require_finite(sample.depth_m, prefix + "depth_m");
  require_non_negative_finite(sample.sigma_theta_compression_positive_Pa,
                              prefix +
                                  "sigma_theta_compression_positive_Pa");
  require_finite(sample.mean_stress_Pa, prefix + "mean_stress_Pa");
  require_non_negative_finite(sample.j2_Pa2, prefix + "j2_Pa2");
  require_non_negative_finite(sample.von_mises_effective_stress_Pa,
                              prefix + "von_mises_effective_stress_Pa");
}

void validate_wall_stress(
    const lss::salt::SaltWallStressDiagnostics& wall_stress) {
  if (!wall_stress.valid) {
    throw std::invalid_argument(
        "LotSaltSigmaThetaDiagnostic: wall_stress must be valid");
  }
  if (wall_stress.wall_samples.empty()) {
    throw std::invalid_argument(
        "LotSaltSigmaThetaDiagnostic: wall_samples must not be empty");
  }
  for (std::size_t i = 0; i < wall_stress.wall_samples.size(); ++i) {
    validate_wall_sample(wall_stress.wall_samples[i], i);
  }
}

LotSaltPressureMapResult map_pressure_for_step(
    const lss::lot::PknResult& pkn_result,
    std::size_t step_index,
    const LotSaltCouplingConfig& config) {
  LotSaltPressureMapInput input;
  input.net_pressure_Pa = pkn_result.net_pressure_series_Pa[step_index];
  input.absolute_wellbore_pressure_Pa = config.absolute_wellbore_pressure_Pa;
  input.hydrostatic_pressure_Pa = config.hydrostatic_pressure_Pa;
  input.surface_pressure_Pa = config.surface_pressure_Pa;
  input.depth_m = config.depth_m;
  input.method = config.pressure_map_method;
  return map_lot_pkn_to_salt_wall_pressure(input);
}

SigmaThetaInfluenceLayer make_layer(
    const lss::salt::SaltWallStressSample& sample,
    std::size_t sample_index) {
  SigmaThetaInfluenceLayer layer;
  layer.layer_id = "wall_gp_" + std::to_string(sample_index);
  layer.influence_depth_m = sample.depth_m;
  layer.sigma_theta_compression_positive_Pa =
      sample.sigma_theta_compression_positive_Pa;
  return layer;
}

LotSaltSigmaThetaDiagnosticPoint make_diagnostic_point(
    const lss::salt::SaltWallStressSample& sample,
    std::size_t sample_index,
    double time_s,
    const LotSaltPressureMapResult& pressure_map) {
  LotSaltSigmaThetaDiagnosticPoint point;
  point.pressure_map = pressure_map;
  point.breakdown = evaluate_sigma_theta_breakdown_point(
      make_layer(sample, sample_index), time_s, pressure_map.wall_pressure_Pa);
  point.wall_stress_gp_id = sample.gp_id;
  point.wall_stress_element_id = sample.element_id;
  point.wall_stress_local_gp_id = sample.local_gp_id;
  point.wall_stress_r_m = sample.r_m;
  point.wall_stress_z_m = sample.z_m;
  point.wall_stress_depth_m = sample.depth_m;
  point.mean_stress_Pa = sample.mean_stress_Pa;
  point.j2_Pa2 = sample.j2_Pa2;
  point.von_mises_effective_stress_Pa =
      sample.von_mises_effective_stress_Pa;
  return point;
}

LotSaltSigmaThetaDiagnosticResult make_empty_result(
    const LotSaltPressureMapResult& pressure_map) {
  LotSaltSigmaThetaDiagnosticResult result;
  result.pressure_source = std::string("LotSaltPressureMap:") +
                           pressure_map.method_label;
  result.stress_source = "SaltWallStressDiagnostics snapshot";
  return result;
}

}  // namespace

LotSaltSigmaThetaDiagnosticResult evaluate_lot_salt_sigma_theta_step(
    const lss::lot::PknResult& pkn_result,
    std::size_t step_index,
    const LotSaltCouplingConfig& config,
    const lss::salt::SaltWallStressDiagnostics& wall_stress) {
  validate_pkn_series(pkn_result);
  if (step_index >= pkn_result.time_series_s.size()) {
    throw std::out_of_range(
        "LotSaltSigmaThetaDiagnostic: step_index out of range");
  }
  validate_wall_stress(wall_stress);

  const auto pressure_map =
      map_pressure_for_step(pkn_result, step_index, config);
  auto result = make_empty_result(pressure_map);
  result.points.reserve(wall_stress.wall_samples.size());

  const double time_s = pkn_result.time_series_s[step_index];
  for (std::size_t sample_index = 0;
       sample_index < wall_stress.wall_samples.size(); ++sample_index) {
    auto point = make_diagnostic_point(wall_stress.wall_samples[sample_index],
                                       sample_index, time_s, pressure_map);
    result.any_opened = result.any_opened || point.breakdown.opened;
    result.points.push_back(std::move(point));
  }

  result.valid = true;
  return result;
}

LotSaltSigmaThetaDiagnosticResult evaluate_lot_salt_sigma_theta_series(
    const lss::lot::PknResult& pkn_result,
    const LotSaltCouplingConfig& config,
    const lss::salt::SaltWallStressDiagnostics& wall_stress) {
  validate_pkn_series(pkn_result);
  validate_wall_stress(wall_stress);

  const auto first_pressure_map = map_pressure_for_step(pkn_result, 0, config);
  auto result = make_empty_result(first_pressure_map);
  result.points.reserve(pkn_result.time_series_s.size() *
                        wall_stress.wall_samples.size());

  for (std::size_t step_index = 0; step_index < pkn_result.time_series_s.size();
       ++step_index) {
    const auto pressure_map =
        map_pressure_for_step(pkn_result, step_index, config);
    const double time_s = pkn_result.time_series_s[step_index];
    for (std::size_t sample_index = 0;
         sample_index < wall_stress.wall_samples.size(); ++sample_index) {
      auto point = make_diagnostic_point(wall_stress.wall_samples[sample_index],
                                         sample_index, time_s, pressure_map);
      result.any_opened = result.any_opened || point.breakdown.opened;
      result.points.push_back(std::move(point));
    }
  }

  result.valid = true;
  return result;
}

}  // namespace lss::coupling
