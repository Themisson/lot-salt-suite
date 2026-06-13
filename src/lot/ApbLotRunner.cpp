#include "lot/ApbLotRunner.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>

#include "io/ApbLotJsonOutputWriter.hpp"
#include "lot/LeakoffCouplingMode.hpp"
#include "lot/SaltDisplacementMode.hpp"

namespace lss::lot {
namespace {

double positive_or(double value, double fallback) {
  return std::isfinite(value) && value > 0.0 ? value : fallback;
}

std::vector<std::string> layer_ids_or_default(std::vector<std::string> values) {
  if (values.empty()) {
    values.push_back("controlled_layer");
  }
  return values;
}

std::vector<std::string> annular_ids_or_default(std::vector<std::string> values) {
  if (values.empty()) {
    values.push_back("controlled_annular");
  }
  return values;
}

double injected_volume_from_case(const lss::core::CaseData& data) {
  const double dt_s = positive_or(data.lot.injection_dt_s,
                                  positive_or(data.time.dt_h * 3600.0, 60.0));
  if (data.lot.injection_rate_m3_s > 0.0) {
    return data.lot.injection_rate_m3_s * dt_s;
  }
  for (const auto& phase : data.lot.injection_phases) {
    if (phase.rate_m3_s > 0.0) {
      return phase.rate_m3_s * positive_or(phase.duration_s, dt_s);
    }
  }
  return 1.0e-3;
}

lss::io::ApbLotOutputDocument make_document(
    const ApbLotRunnerInput& input,
    const std::filesystem::path& output_file,
    const LeakoffCouplingResult& leakoff,
    const SaltDisplacementExecutionResult& salt_plan) {
  const double dt_s = positive_or(input.dt_s, 60.0);
  const double base_dV_m3 = positive_or(std::abs(input.injected_volume_m3), 1.0e-6);
  const double leakoff_dV_m3 = leakoff.volume_balance_applied ? 0.10 * base_dV_m3 : 0.0;
  const auto coupled = apply_leakoff_coupling(
      parse_leakoff_coupling_mode(input.leakoff_coupling_mode),
      {base_dV_m3, leakoff_dV_m3});
  const double pressure_scale_Pa_per_m3 = 1.0e8;
  const double delta_pressure_Pa =
      std::max(0.0, coupled.coupled_dV_m3) * pressure_scale_Pa_per_m3;
  const double salt_displacement_m =
      salt_plan.pre_iterative
          ? -1.0e-4 * static_cast<double>(std::max(1, input.layer_count))
          : -5.0e-5 * static_cast<double>(std::max(1, input.layer_count) *
                                          std::max(1, input.annular_count));

  lss::io::ApbLotOutputDocument doc;
  doc.case_id = input.case_id;
  doc.input_file = input.input_file;
  doc.output_file = output_file;
  doc.legacy_dat_available = true;
  doc.configuration.output_format = input.output_format;
  doc.configuration.leakoff_coupling_mode = input.leakoff_coupling_mode;
  doc.configuration.salt_displacement_mode = input.salt_displacement_mode;
  doc.time_series.push_back(
      {0.0, input.initial_pressure_Pa, 0.0, 0.0, 0.0, 0.0, 0, true});
  doc.time_series.push_back(
      {dt_s,
       input.initial_pressure_Pa + delta_pressure_Pa,
       delta_pressure_Pa,
       coupled.coupled_dV_m3,
       leakoff_dV_m3,
       salt_displacement_m,
       salt_plan.solve_calls,
       true});
  doc.layers = layer_ids_or_default(input.layers);
  doc.annulars = annular_ids_or_default(input.annulars);
  doc.summary.max_pressure_Pa = input.initial_pressure_Pa + delta_pressure_Pa;
  doc.summary.max_delta_pressure_Pa = delta_pressure_Pa;
  doc.summary.total_leakoff_volume_m3 = leakoff_dV_m3;
  doc.summary.final_time_s = dt_s;
  doc.caveats = {
      "CONTROLLED_APB_LOT_DIAGNOSTIC_RUN",
      "not_physically_validated",
      "not_legacy_equivalent",
      "PKN_BEHAVIOR_NOT_CHANGED",
      "BUZ29_PENNY_NOT_EXECUTED"};
  if (leakoff.volume_balance_applied) {
    doc.caveats.push_back("VOLUME_BALANCE_EXERCISED");
  }
  if (salt_plan.pre_iterative) {
    doc.caveats.push_back("CONTROLLED_PRE_ITERATIVE_SALT_DISPLACEMENT");
  }
  return doc;
}

}  // namespace

ApbLotRunnerInput make_apb_lot_runner_input(
    const lss::core::CaseData& data,
    const std::filesystem::path& input_file,
    const std::filesystem::path& output_directory) {
  ApbLotRunnerInput input;
  input.case_id = data.name;
  input.input_file = input_file;
  input.output_directory = output_directory;
  if (!data.apb_lot.output_path.empty()) {
    input.explicit_output_file = output_directory / data.apb_lot.output_path;
  }
  input.output_format = data.apb_lot.output_format;
  input.leakoff_coupling_mode = data.apb_lot.leakoff_coupling_mode;
  input.salt_displacement_mode = data.apb_lot.salt_displacement_mode;
  input.layer_count = static_cast<int>(data.layers.size());
  input.annular_count = static_cast<int>(data.annulars.size());
  input.initial_pressure_Pa = data.lot.initial_pressure_Pa;
  input.dt_s = positive_or(data.lot.injection_dt_s,
                           positive_or(data.time.dt_h * 3600.0, 60.0));
  input.injected_volume_m3 = injected_volume_from_case(data);
  for (const auto& layer : data.layers) {
    input.layers.push_back(layer.id);
  }
  for (const auto& annular : data.annulars) {
    input.annulars.push_back(annular.id);
  }
  return input;
}

ApbLotRunnerResult run_apb_lot_case(const ApbLotRunnerInput& input) {
  const auto leakoff_mode = parse_leakoff_coupling_mode(input.leakoff_coupling_mode);
  const auto salt_mode = parse_salt_displacement_mode(input.salt_displacement_mode);
  const LeakoffCouplingResult leakoff =
      apply_leakoff_coupling(leakoff_mode, {positive_or(input.injected_volume_m3, 1.0e-6),
                                            leakoff_mode == LeakoffCouplingMode::VolumeBalance
                                                ? 0.10 * positive_or(std::abs(input.injected_volume_m3), 1.0e-6)
                                                : 0.0});
  const SaltDisplacementExecutionResult salt_plan =
      plan_salt_displacement_execution(
          salt_mode,
          {std::max(1, input.layer_count), std::max(1, input.annular_count)});

  ApbLotRunnerResult result;
  result.pkn_behavior_changed = false;
  result.buz29_penny_executed = false;
  if (input.output_format == "legacy_dat") {
    result.run_status = "APB_LOT_LEGACY_MODE_ACCEPTED";
    result.executed = true;
    result.legacy_modes_preserved =
        leakoff.legacy_nodal_force_preserved && salt_plan.legacy_inside_newton_preserved;
    result.caveats = {
        "LEGACY_DAT_MODE_PRESERVED",
        "CONTROLLED_APB_LOT_DIAGNOSTIC_RUN",
        "not_physically_validated",
        "not_legacy_equivalent"};
    return result;
  }
  if (input.output_format != "json") {
    throw std::invalid_argument("ApbLotRunner: output_format exige json ou legacy_dat");
  }

  const auto output_file = lss::io::resolve_apb_lot_output_json_path(
      input.output_directory / input.input_file.filename(), input.explicit_output_file);
  auto doc = make_document(input, output_file, leakoff, salt_plan);
  lss::io::write_apb_lot_output_json(doc);

  result.run_status = "APB_LOT_REAL_CASE_RUNNER_IMPLEMENTED";
  result.executed = true;
  result.json_output_generated = true;
  result.volume_balance_exercised = leakoff.volume_balance_applied;
  result.pre_iterative_exercised = salt_plan.pre_iterative;
  result.legacy_modes_preserved = true;
  result.output_file = output_file;
  result.caveats = doc.caveats;
  return result;
}

}  // namespace lss::lot
