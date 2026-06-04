#include "coupling/LotSaltSigmaThetaDiagnosticWriter.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "coupling/LotSaltCouplingStep.hpp"

namespace lss::coupling {
namespace {

struct ScenarioShape {
  std::size_t n_steps = 0;
  std::size_t n_samples = 0;
  std::size_t n_points = 0;
};

struct ScenarioSummary {
  std::size_t n_points = 0;
  std::size_t n_compressive = 0;
  std::size_t n_neutral = 0;
  std::size_t n_tensile = 0;
  double min_sigma_theta_compression_positive_Pa = 0.0;
  double max_sigma_theta_compression_positive_Pa = 0.0;
  double min_margin_Pa = 0.0;
  double max_margin_Pa = 0.0;
  bool any_opened = false;
  bool any_legacy_algebra_opened = false;
  bool has_first_open = false;
  double first_open_time_s = 0.0;
  double first_open_pressure_Pa = 0.0;
  std::string first_open_layer_id;
};

void require_non_empty(const std::string& value, const char* field) {
  if(value.empty()) {
    throw std::invalid_argument(std::string(field) + " must not be empty");
  }
}

std::string csv_escape(const std::string& value) {
  std::string escaped = "\"";
  for(char ch : value) {
    if(ch == '"') {
      escaped += "\"\"";
    } else {
      escaped += ch;
    }
  }
  escaped += '"';
  return escaped;
}

std::string json_escape(const std::string& value) {
  std::string escaped;
  for(char ch : value) {
    switch(ch) {
      case '"':
        escaped += "\\\"";
        break;
      case '\\':
        escaped += "\\\\";
        break;
      case '\b':
        escaped += "\\b";
        break;
      case '\f':
        escaped += "\\f";
        break;
      case '\n':
        escaped += "\\n";
        break;
      case '\r':
        escaped += "\\r";
        break;
      case '\t':
        escaped += "\\t";
        break;
      default:
        escaped += ch;
        break;
    }
  }
  return escaped;
}

std::string format_double(double value) {
  std::ostringstream out;
  out << std::setprecision(17) << value;
  return out.str();
}

const char* bool_text(bool value) {
  return value ? "true" : "false";
}

ScenarioShape validate_scenario(
    const LotSaltSigmaThetaExportScenario& scenario) {
  require_non_empty(scenario.scenario_id, "scenario_id");
  require_non_empty(scenario.scenario_label, "scenario_label");

  const auto& result = scenario.result;
  if(!result.valid) {
    throw std::invalid_argument("scenario result must be valid");
  }
  if(!result.diagnostic.valid) {
    throw std::invalid_argument("scenario diagnostic must be valid");
  }
  if(!result.wall_stress.valid) {
    throw std::invalid_argument("scenario wall stress must be valid");
  }

  const auto& time = result.pkn_run.result.time_series_s;
  const auto& net_pressure = result.pkn_run.result.net_pressure_series_Pa;
  if(time.empty()) {
    throw std::invalid_argument("scenario PKN time series must not be empty");
  }
  if(net_pressure.empty()) {
    throw std::invalid_argument(
        "scenario PKN net pressure series must not be empty");
  }
  if(time.size() != net_pressure.size()) {
    throw std::invalid_argument(
        "scenario PKN time and net pressure series sizes differ");
  }

  const std::size_t n_samples = result.wall_stress.wall_samples.size();
  if(n_samples == 0) {
    throw std::invalid_argument(
        "scenario wall stress samples must not be empty");
  }

  const std::size_t expected_points = time.size() * n_samples;
  if(result.diagnostic.points.size() != expected_points) {
    throw std::invalid_argument(
        "scenario diagnostic point count must equal PKN steps times wall "
        "stress samples");
  }

  return ScenarioShape{time.size(), n_samples, expected_points};
}

ScenarioSummary summarize_scenario(
    const LotSaltSigmaThetaExportScenario& scenario) {
  const auto& points = scenario.result.diagnostic.points;
  ScenarioSummary summary;
  summary.n_points = points.size();
  summary.min_sigma_theta_compression_positive_Pa =
      std::numeric_limits<double>::infinity();
  summary.max_sigma_theta_compression_positive_Pa =
      -std::numeric_limits<double>::infinity();
  summary.min_margin_Pa = std::numeric_limits<double>::infinity();
  summary.max_margin_Pa = -std::numeric_limits<double>::infinity();

  for(const auto& point : points) {
    switch(point.breakdown.hoop_state) {
      case SigmaThetaHoopState::Compressive:
        ++summary.n_compressive;
        break;
      case SigmaThetaHoopState::Neutral:
        ++summary.n_neutral;
        break;
      case SigmaThetaHoopState::Tensile:
        ++summary.n_tensile;
        break;
    }

    summary.min_sigma_theta_compression_positive_Pa =
        std::min(summary.min_sigma_theta_compression_positive_Pa,
                 point.breakdown.sigma_theta_compression_positive_Pa);
    summary.max_sigma_theta_compression_positive_Pa =
        std::max(summary.max_sigma_theta_compression_positive_Pa,
                 point.breakdown.sigma_theta_compression_positive_Pa);
    summary.min_margin_Pa =
        std::min(summary.min_margin_Pa, point.breakdown.margin_Pa);
    summary.max_margin_Pa =
        std::max(summary.max_margin_Pa, point.breakdown.margin_Pa);

    summary.any_opened = summary.any_opened || point.breakdown.opened;
    summary.any_legacy_algebra_opened =
        summary.any_legacy_algebra_opened ||
        point.breakdown.legacy_algebra_opened;

    if(point.breakdown.opened && !summary.has_first_open) {
      summary.has_first_open = true;
      summary.first_open_time_s = point.breakdown.time_s;
      summary.first_open_pressure_Pa = point.breakdown.pressure_Pa;
      summary.first_open_layer_id = point.breakdown.layer_id;
    }
  }

  return summary;
}

void write_points_csv(
    std::ostream& out,
    const LotSaltSigmaThetaExportOptions& options,
    const std::vector<LotSaltSigmaThetaExportScenario>& scenarios,
    const std::vector<ScenarioShape>& shapes) {
  out << "case_id,scenario_id,scenario_label,step_index,time_s,sample_index,"
         "layer_id,gp_id,element_id,local_gp_id,r_m,z_m,depth_m,"
         "pressure_source,stress_source,pressure_map_method,"
         "pressure_map_label,wall_pressure_Pa,net_pressure_Pa,"
         "hydrostatic_pressure_Pa,surface_pressure_Pa,"
         "absolute_wellbore_pressure_Pa,"
         "sigma_theta_compression_positive_Pa,hoop_state,margin_Pa,opened,"
         "legacy_algebra_opened,tensile_hoop_state,mean_stress_Pa,j2_Pa2,"
         "von_mises_effective_stress_Pa,caveat\n";

  for(std::size_t scenario_index = 0; scenario_index < scenarios.size();
      ++scenario_index) {
    const auto& scenario = scenarios[scenario_index];
    const auto& result = scenario.result;
    const auto& shape = shapes[scenario_index];

    for(std::size_t point_index = 0; point_index < shape.n_points;
        ++point_index) {
      const std::size_t step_index = point_index / shape.n_samples;
      const std::size_t sample_index = point_index % shape.n_samples;
      const auto& point = result.diagnostic.points[point_index];

      out << csv_escape(options.case_id) << ','
          << csv_escape(scenario.scenario_id) << ','
          << csv_escape(scenario.scenario_label) << ',' << step_index << ','
          << format_double(result.pkn_run.result.time_series_s[step_index])
          << ',' << sample_index << ','
          << csv_escape(point.breakdown.layer_id) << ','
          << point.wall_stress_gp_id << ','
          << point.wall_stress_element_id << ','
          << point.wall_stress_local_gp_id << ','
          << format_double(point.wall_stress_r_m) << ','
          << format_double(point.wall_stress_z_m) << ','
          << format_double(point.wall_stress_depth_m) << ','
          << csv_escape(result.diagnostic.pressure_source) << ','
          << csv_escape(result.diagnostic.stress_source) << ','
          << csv_escape(to_string(point.pressure_map.method)) << ','
          << csv_escape(point.pressure_map.method_label) << ','
          << format_double(point.pressure_map.wall_pressure_Pa) << ','
          << format_double(
                 result.pkn_run.result.net_pressure_series_Pa[step_index])
          << ','
          << format_double(result.coupling_config.hydrostatic_pressure_Pa)
          << ','
          << format_double(result.coupling_config.surface_pressure_Pa) << ','
          << format_double(
                 result.coupling_config.absolute_wellbore_pressure_Pa)
          << ','
          << format_double(
                 point.breakdown.sigma_theta_compression_positive_Pa)
          << ',' << csv_escape(to_string(point.breakdown.hoop_state)) << ','
          << format_double(point.breakdown.margin_Pa) << ','
          << bool_text(point.breakdown.opened) << ','
          << bool_text(point.breakdown.legacy_algebra_opened) << ','
          << bool_text(point.breakdown.tensile_hoop_state) << ','
          << format_double(point.mean_stress_Pa) << ','
          << format_double(point.j2_Pa2) << ','
          << format_double(point.von_mises_effective_stress_Pa) << ','
          << csv_escape(point.breakdown.caveat) << '\n';
    }
  }
}

void write_summary_csv(
    std::ostream& out,
    const LotSaltSigmaThetaExportOptions& options,
    const std::vector<LotSaltSigmaThetaExportScenario>& scenarios) {
  out << "case_id,scenario_id,scenario_label,n_points,n_compressive,"
         "n_neutral,n_tensile,min_sigma_theta_compression_positive_Pa,"
         "max_sigma_theta_compression_positive_Pa,min_margin_Pa,"
         "max_margin_Pa,any_opened,any_legacy_algebra_opened,"
         "first_open_time_s,first_open_pressure_Pa,first_open_layer_id\n";

  for(const auto& scenario : scenarios) {
    const ScenarioSummary summary = summarize_scenario(scenario);
    out << csv_escape(options.case_id) << ','
        << csv_escape(scenario.scenario_id) << ','
        << csv_escape(scenario.scenario_label) << ',' << summary.n_points
        << ',' << summary.n_compressive << ',' << summary.n_neutral << ','
        << summary.n_tensile << ','
        << format_double(summary.min_sigma_theta_compression_positive_Pa)
        << ','
        << format_double(summary.max_sigma_theta_compression_positive_Pa)
        << ',' << format_double(summary.min_margin_Pa) << ','
        << format_double(summary.max_margin_Pa) << ','
        << bool_text(summary.any_opened) << ','
        << bool_text(summary.any_legacy_algebra_opened) << ',';

    if(summary.has_first_open) {
      out << format_double(summary.first_open_time_s) << ','
          << format_double(summary.first_open_pressure_Pa) << ','
          << csv_escape(summary.first_open_layer_id);
    } else {
      out << ",,";
    }
    out << '\n';
  }
}

void write_metadata_json(
    std::ostream& out,
    const LotSaltSigmaThetaExportOptions& options,
    const std::vector<LotSaltSigmaThetaExportScenario>& scenarios,
    const std::vector<ScenarioShape>& shapes) {
  out << "{\n";
  out << "  \"case_id\": \"" << json_escape(options.case_id) << "\",\n";
  out << "  \"generated_by\": \"lot-salt-suite\",\n";
  out << "  \"phase\": \"10.9B\",\n";
  out << "  \"format\": \"experimental_sigma_theta_diagnostics\",\n";
  out << "  \"input_case\": \"" << json_escape(options.input_case)
      << "\",\n";
  out << "  \"files\": {\n";
  out << "    \"points_csv\": \"points.csv\",\n";
  out << "    \"summary_csv\": \"summary.csv\"\n";
  out << "  },\n";
  out << "  \"scenarios\": [\n";
  for(std::size_t i = 0; i < scenarios.size(); ++i) {
    const auto& scenario = scenarios[i];
    out << "    {\n";
    out << "      \"id\": \"" << json_escape(scenario.scenario_id)
        << "\",\n";
    out << "      \"label\": \"" << json_escape(scenario.scenario_label)
        << "\",\n";
    out << "      \"valid\": true,\n";
    out << "      \"n_points\": " << shapes[i].n_points << ",\n";
    out << "      \"n_steps\": " << shapes[i].n_steps << ",\n";
    out << "      \"n_wall_samples\": " << shapes[i].n_samples << "\n";
    out << "    }" << (i + 1 == scenarios.size() ? "\n" : ",\n");
  }
  out << "  ],\n";
  out << "  \"caveats\": [\n";
  for(std::size_t i = 0; i < options.caveats.size(); ++i) {
    out << "    \"" << json_escape(options.caveats[i]) << "\""
        << (i + 1 == options.caveats.size() ? "\n" : ",\n");
  }
  out << "  ]\n";
  out << "}\n";
}

void ensure_writable_stream(const std::ofstream& stream,
                            const std::filesystem::path& path) {
  if(!stream) {
    throw std::runtime_error("failed to open output file: " + path.string());
  }
}

}  // namespace

LotSaltSigmaThetaExportResult write_lot_salt_sigma_theta_diagnostics(
    const LotSaltSigmaThetaExportOptions& options,
    const std::vector<LotSaltSigmaThetaExportScenario>& scenarios) {
  require_non_empty(options.case_id, "case_id");
  if(options.output_dir.empty()) {
    throw std::invalid_argument("output_dir must not be empty");
  }
  if(scenarios.empty()) {
    throw std::invalid_argument("scenarios must not be empty");
  }

  std::vector<ScenarioShape> shapes;
  shapes.reserve(scenarios.size());
  for(const auto& scenario : scenarios) {
    shapes.push_back(validate_scenario(scenario));
  }

  std::filesystem::create_directories(options.output_dir);

  LotSaltSigmaThetaExportResult result;
  result.points_csv = options.output_dir / "points.csv";
  result.summary_csv = options.output_dir / "summary.csv";
  result.metadata_json = options.output_dir / "metadata.json";

  {
    std::ofstream out(result.points_csv);
    ensure_writable_stream(out, result.points_csv);
    write_points_csv(out, options, scenarios, shapes);
  }

  {
    std::ofstream out(result.summary_csv);
    ensure_writable_stream(out, result.summary_csv);
    write_summary_csv(out, options, scenarios);
  }

  {
    std::ofstream out(result.metadata_json);
    ensure_writable_stream(out, result.metadata_json);
    write_metadata_json(out, options, scenarios, shapes);
  }

  result.valid = true;
  return result;
}

}  // namespace lss::coupling
