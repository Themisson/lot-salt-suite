#include "io/ApbLotJsonOutputWriter.hpp"

#include <algorithm>
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

void write_string_array(std::ofstream& out, const std::vector<std::string>& values) {
  out << '[';
  for (std::size_t i = 0; i < values.size(); ++i) {
    if (i != 0U) {
      out << ", ";
    }
    out << '"' << escape_json(values[i]) << '"';
  }
  out << ']';
}

void write_optional_number(std::ofstream& out,
                           const std::optional<double>& value) {
  if (!value.has_value()) {
    out << "null";
    return;
  }
  if (!std::isfinite(*value)) {
    throw std::runtime_error("ApbLotJsonOutputWriter: non-finite summary value");
  }
  out << *value;
}

void require_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::runtime_error("ApbLotJsonOutputWriter: non-finite " + field);
  }
}

void validate_document(const ApbLotOutputDocument& document) {
  if (document.case_id.empty()) {
    throw std::runtime_error("ApbLotJsonOutputWriter: case_id is required");
  }
  if (document.output_file.empty()) {
    throw std::runtime_error("ApbLotJsonOutputWriter: output_file is required");
  }
  require_finite(document.configuration.axisymmetric_angle_rad,
                 "axisymmetric_angle_rad");
  for (const auto& sample : document.time_series) {
    require_finite(sample.time_s, "time_s");
    require_finite(sample.pressure_Pa, "pressure_Pa");
    require_finite(sample.delta_pressure_Pa, "delta_pressure_Pa");
    require_finite(sample.dV_m3, "dV_m3");
    require_finite(sample.dV_leakoff_m3, "dV_leakoff_m3");
    require_finite(sample.salt_displacement_m, "salt_displacement_m");
    if (sample.iteration_count < 0) {
      throw std::runtime_error(
          "ApbLotJsonOutputWriter: iteration_count must be non-negative");
    }
  }
}

}  // namespace

std::filesystem::path derive_apb_lot_output_json_path(
    const std::filesystem::path& input_path) {
  const auto parent = input_path.parent_path();
  const auto stem = input_path.stem().string();
  if (stem.empty()) {
    throw std::runtime_error(
        "ApbLotJsonOutputWriter: input path must have a file stem");
  }
  return parent / (stem + "_out.json");
}

std::filesystem::path resolve_apb_lot_output_json_path(
    const std::filesystem::path& input_path,
    const std::optional<std::filesystem::path>& explicit_output_path) {
  if (explicit_output_path.has_value() && !explicit_output_path->empty()) {
    return *explicit_output_path;
  }
  return derive_apb_lot_output_json_path(input_path);
}

void write_apb_lot_output_json(const ApbLotOutputDocument& document) {
  validate_document(document);
  const auto parent_path = document.output_file.parent_path();
  if (!parent_path.empty()) {
    std::filesystem::create_directories(parent_path);
  }

  std::ofstream out(document.output_file);
  if (!out) {
    throw std::runtime_error("ApbLotJsonOutputWriter: cannot open output file: " +
                             document.output_file.string());
  }
  out << std::setprecision(17);
  out << "{\n";
  out << "  \"metadata\": {\n";
  out << "    \"case_id\": \"" << escape_json(document.case_id) << "\",\n";
  out << "    \"input_file\": \"" << escape_json(document.input_file.string())
      << "\",\n";
  out << "    \"output_file\": \"" << escape_json(document.output_file.string())
      << "\",\n";
  out << "    \"schema_version\": \"apb_lot_output_v1\",\n";
  out << "    \"generated_by\": \"lot-salt-suite\",\n";
  out << "    \"output_format\": \"json\",\n";
  out << "    \"legacy_dat_available\": "
      << (document.legacy_dat_available ? "true" : "false") << "\n";
  out << "  },\n";
  out << "  \"configuration\": {\n";
  out << "    \"output_format\": \""
      << escape_json(document.configuration.output_format) << "\",\n";
  out << "    \"leakoff_coupling_mode\": \""
      << escape_json(document.configuration.leakoff_coupling_mode) << "\",\n";
  out << "    \"salt_displacement_mode\": \""
      << escape_json(document.configuration.salt_displacement_mode) << "\",\n";
  out << "    \"axisymmetric_angle_rad\": "
      << document.configuration.axisymmetric_angle_rad << "\n";
  out << "  },\n";
  out << "  \"time_series\": [\n";
  for (std::size_t i = 0; i < document.time_series.size(); ++i) {
    const auto& sample = document.time_series[i];
    out << "    {\"time_s\": " << sample.time_s
        << ", \"pressure_Pa\": " << sample.pressure_Pa
        << ", \"delta_pressure_Pa\": " << sample.delta_pressure_Pa
        << ", \"dV_m3\": " << sample.dV_m3
        << ", \"dV_leakoff_m3\": " << sample.dV_leakoff_m3
        << ", \"salt_displacement_m\": " << sample.salt_displacement_m
        << ", \"iteration_count\": " << sample.iteration_count
        << ", \"converged\": " << (sample.converged ? "true" : "false")
        << '}';
    out << (i + 1U == document.time_series.size() ? "\n" : ",\n");
  }
  out << "  ],\n";
  out << "  \"layers\": ";
  write_string_array(out, document.layers);
  out << ",\n";
  out << "  \"annulars\": ";
  write_string_array(out, document.annulars);
  out << ",\n";
  out << "  \"summary\": {\n";
  out << "    \"max_pressure_Pa\": ";
  write_optional_number(out, document.summary.max_pressure_Pa);
  out << ",\n";
  out << "    \"max_delta_pressure_Pa\": ";
  write_optional_number(out, document.summary.max_delta_pressure_Pa);
  out << ",\n";
  out << "    \"total_leakoff_volume_m3\": ";
  write_optional_number(out, document.summary.total_leakoff_volume_m3);
  out << ",\n";
  out << "    \"final_time\": ";
  write_optional_number(out, document.summary.final_time_s);
  out << "\n";
  out << "  },\n";
  out << "  \"caveats\": ";
  write_string_array(out, document.caveats);
  out << "\n";
  out << "}\n";
}

}  // namespace lss::io
