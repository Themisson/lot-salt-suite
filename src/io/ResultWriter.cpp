#include "io/ResultWriter.hpp"

#include <cstddef>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <string>

namespace lss::io {
namespace {

std::string escape_json(const std::string& value) {
  std::string escaped;
  escaped.reserve(value.size());
  for (const char ch : value) {
    switch (ch) {
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

void ensure_series_sizes(const lss::lot::PknResult& result) {
  const std::size_t size = result.time_series_s.size();
  if (result.injected_volume_series_m3.size() != size ||
      result.fracture_length_series_m.size() != size ||
      result.fracture_width_series_m.size() != size ||
      result.fracture_volume_series_m3.size() != size ||
      result.leakoff_volume_series_m3.size() != size ||
      result.net_pressure_series_Pa.size() != size ||
      result.initial_pressure_series_Pa.size() != size ||
      result.wellbore_pressure_series_Pa.size() != size ||
      result.balance_delta_pressure_series_Pa.size() != size ||
      result.balance_effective_volume_increment_series_m3.size() != size ||
      result.balance_injected_volume_increment_series_m3.size() != size ||
      result.balance_fracture_volume_increment_series_m3.size() != size ||
      result.balance_leakoff_volume_increment_series_m3.size() != size) {
    throw std::runtime_error("ResultWriter: PKN result series have different sizes");
  }
}

void require_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::runtime_error("ResultWriter: non-finite value in " + field);
  }
}

void ensure_finite_values(const lss::lot::PknResult& result) {
  require_finite(result.time_s, "summary.time_s");
  require_finite(result.injected_volume_m3, "summary.injected_volume_m3");
  require_finite(result.length_m, "summary.fracture_length_m");
  require_finite(result.width_m, "summary.fracture_width_m");
  require_finite(result.fracture_volume_m3, "summary.fracture_volume_m3");
  require_finite(result.leakoff_volume_m3, "summary.leakoff_volume_m3");
  require_finite(result.net_pressure_Pa, "summary.net_pressure_Pa");
  require_finite(result.initial_pressure_Pa, "summary.initial_pressure_Pa");
  require_finite(result.wellbore_pressure_Pa, "summary.wellbore_pressure_Pa");
  require_finite(result.fluid_compressibility_per_Pa,
                 "summary.fluid_compressibility_per_Pa");
  require_finite(result.balance_delta_pressure_Pa,
                 "summary.balance_delta_pressure_Pa");
  require_finite(result.balance_effective_volume_increment_m3,
                 "summary.balance_effective_volume_increment_m3");
  require_finite(result.balance_injected_volume_increment_m3,
                 "summary.balance_injected_volume_increment_m3");
  require_finite(result.balance_fracture_volume_increment_m3,
                 "summary.balance_fracture_volume_increment_m3");
  require_finite(result.balance_leakoff_volume_increment_m3,
                 "summary.balance_leakoff_volume_increment_m3");
  require_finite(result.initial_annular_volume_per_radian_m3,
                 "summary.initial_annular_volume_per_radian_m3");
  require_finite(result.initial_annular_volume_m3,
                 "summary.initial_annular_volume_m3");
  require_finite(result.annular_outer_radius_m,
                 "summary.annular_outer_radius_m");
  require_finite(result.annular_inner_radius_m,
                 "summary.annular_inner_radius_m");
  require_finite(result.annular_length_m, "summary.annular_length_m");

  for (std::size_t i = 0; i < result.time_series_s.size(); ++i) {
    require_finite(result.time_series_s[i], "series.time_s");
    require_finite(result.injected_volume_series_m3[i], "series.injected_volume_m3");
    require_finite(result.fracture_length_series_m[i], "series.fracture_length_m");
    require_finite(result.fracture_width_series_m[i], "series.fracture_width_m");
    require_finite(result.fracture_volume_series_m3[i], "series.fracture_volume_m3");
    require_finite(result.leakoff_volume_series_m3[i], "series.leakoff_volume_m3");
    require_finite(result.net_pressure_series_Pa[i], "series.net_pressure_Pa");
    require_finite(result.initial_pressure_series_Pa[i],
                   "series.initial_pressure_Pa");
    require_finite(result.wellbore_pressure_series_Pa[i],
                   "series.wellbore_pressure_Pa");
    require_finite(result.balance_delta_pressure_series_Pa[i],
                   "series.balance_delta_pressure_Pa");
    require_finite(result.balance_effective_volume_increment_series_m3[i],
                   "series.balance_effective_volume_increment_m3");
    require_finite(result.balance_injected_volume_increment_series_m3[i],
                   "series.balance_injected_volume_increment_m3");
    require_finite(result.balance_fracture_volume_increment_series_m3[i],
                   "series.balance_fracture_volume_increment_m3");
    require_finite(result.balance_leakoff_volume_increment_series_m3[i],
                   "series.balance_leakoff_volume_increment_m3");
  }
}

void write_timeseries_csv(const std::filesystem::path& path,
                          const lss::lot::PknResult& result) {
  ensure_series_sizes(result);
  ensure_finite_values(result);

  std::ofstream out(path);
  if (!out) {
    throw std::runtime_error("ResultWriter: cannot open CSV output: " + path.string());
  }
  out << std::setprecision(17);
  out << "time_s,injected_volume_m3,fracture_length_m,fracture_width_m,"
         "fracture_volume_m3,leakoff_volume_m3,net_pressure_Pa,"
         "initial_pressure_Pa,wellbore_pressure_Pa,balance_delta_pressure_Pa,"
         "balance_effective_volume_increment_m3,"
         "balance_injected_volume_increment_m3,"
         "balance_fracture_volume_increment_m3,"
         "balance_leakoff_volume_increment_m3\n";
  for (std::size_t i = 0; i < result.time_series_s.size(); ++i) {
    out << result.time_series_s[i] << ',' << result.injected_volume_series_m3[i] << ','
        << result.fracture_length_series_m[i] << ','
        << result.fracture_width_series_m[i] << ','
        << result.fracture_volume_series_m3[i] << ','
        << result.leakoff_volume_series_m3[i] << ','
        << result.net_pressure_series_Pa[i] << ','
        << result.initial_pressure_series_Pa[i] << ','
        << result.wellbore_pressure_series_Pa[i] << ','
        << result.balance_delta_pressure_series_Pa[i] << ','
        << result.balance_effective_volume_increment_series_m3[i] << ','
        << result.balance_injected_volume_increment_series_m3[i] << ','
        << result.balance_fracture_volume_increment_series_m3[i] << ','
        << result.balance_leakoff_volume_increment_series_m3[i] << '\n';
  }
}

void write_summary_json(const std::filesystem::path& path, const std::string& case_id,
                        const lss::lot::PknResult& result) {
  ensure_series_sizes(result);
  ensure_finite_values(result);

  std::ofstream out(path);
  if (!out) {
    throw std::runtime_error("ResultWriter: cannot open JSON output: " + path.string());
  }

  out << std::setprecision(17);
  out << "{\n";
  out << "  \"metadata\": {\n";
  out << "    \"case_id\": \"" << escape_json(case_id) << "\",\n";
  out << "    \"mode\": \"lot-pkn\",\n";
  out << "    \"validation_status\": \"synthetic_modern_no_legacy_regression\"\n";
  out << "  },\n";
  out << "  \"summary\": {\n";
  out << "    \"final_time_s\": " << result.time_s << ",\n";
  out << "    \"final_injected_volume_m3\": " << result.injected_volume_m3 << ",\n";
  out << "    \"final_fracture_length_m\": " << result.length_m << ",\n";
  out << "    \"final_fracture_width_m\": " << result.width_m << ",\n";
  out << "    \"final_fracture_volume_m3\": " << result.fracture_volume_m3 << ",\n";
  out << "    \"final_leakoff_volume_m3\": " << result.leakoff_volume_m3 << ",\n";
  out << "    \"final_net_pressure_Pa\": " << result.net_pressure_Pa << ",\n";
  out << "    \"pressure_model\": \"" << escape_json(result.pressure_model) << "\",\n";
  out << "    \"initial_pressure_Pa\": " << result.initial_pressure_Pa << ",\n";
  out << "    \"final_wellbore_pressure_Pa\": " << result.wellbore_pressure_Pa << ",\n";
  out << "    \"fluid_compressibility_per_Pa\": "
      << result.fluid_compressibility_per_Pa << ",\n";
  out << "    \"final_balance_delta_pressure_Pa\": "
      << result.balance_delta_pressure_Pa << ",\n";
  out << "    \"final_balance_effective_volume_increment_m3\": "
      << result.balance_effective_volume_increment_m3 << ",\n";
  out << "    \"final_balance_injected_volume_increment_m3\": "
      << result.balance_injected_volume_increment_m3 << ",\n";
  out << "    \"final_balance_fracture_volume_increment_m3\": "
      << result.balance_fracture_volume_increment_m3 << ",\n";
  out << "    \"final_balance_leakoff_volume_increment_m3\": "
      << result.balance_leakoff_volume_increment_m3 << ",\n";
  out << "    \"initial_annular_volume_per_radian_m3\": "
      << result.initial_annular_volume_per_radian_m3 << ",\n";
  out << "    \"initial_annular_volume_m3\": " << result.initial_annular_volume_m3 << ",\n";
  out << "    \"annular_outer_radius_m\": " << result.annular_outer_radius_m << ",\n";
  out << "    \"annular_inner_radius_m\": " << result.annular_inner_radius_m << ",\n";
  out << "    \"annular_length_m\": " << result.annular_length_m << ",\n";
  out << "    \"annular_volume_convention\": \""
      << escape_json(result.annular_volume_convention) << "\",\n";
  out << "    \"annular_volume_source\": \""
      << escape_json(result.annular_volume_source) << "\"\n";
  out << "  },\n";
  out << "  \"warnings\": [\n";
  out << "    \"No numerical regression against legacy was performed.\",\n";
  out << "    \"R09 remains blocker for legacy comparison.\"\n";
  out << "  ]\n";
  out << "}\n";
}

}  // namespace

void write_pkn_result(const std::filesystem::path& output_dir,
                      const std::string& case_id,
                      const lss::lot::PknResult& result) {
  std::filesystem::create_directories(output_dir);
  write_summary_json(output_dir / "result.json", case_id, result);
  write_timeseries_csv(output_dir / "timeseries.csv", result);
}

}  // namespace lss::io
