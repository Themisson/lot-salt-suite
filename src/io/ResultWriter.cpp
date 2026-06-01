#include "io/ResultWriter.hpp"

#include <cstddef>
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
      result.net_pressure_series_Pa.size() != size) {
    throw std::runtime_error("ResultWriter: PKN result series have different sizes");
  }
}

void write_timeseries_csv(const std::filesystem::path& path,
                          const lss::lot::PknResult& result) {
  ensure_series_sizes(result);

  std::ofstream out(path);
  if (!out) {
    throw std::runtime_error("ResultWriter: cannot open CSV output: " + path.string());
  }
  out << std::setprecision(17);
  out << "time_s,injected_volume_m3,fracture_length_m,fracture_width_m,"
         "fracture_volume_m3,leakoff_volume_m3,net_pressure_Pa\n";
  for (std::size_t i = 0; i < result.time_series_s.size(); ++i) {
    out << result.time_series_s[i] << ',' << result.injected_volume_series_m3[i] << ','
        << result.fracture_length_series_m[i] << ','
        << result.fracture_width_series_m[i] << ','
        << result.fracture_volume_series_m3[i] << ','
        << result.leakoff_volume_series_m3[i] << ','
        << result.net_pressure_series_Pa[i] << '\n';
  }
}

void write_summary_json(const std::filesystem::path& path, const std::string& case_id,
                        const lss::lot::PknResult& result) {
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
  out << "    \"final_net_pressure_Pa\": " << result.net_pressure_Pa << "\n";
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
