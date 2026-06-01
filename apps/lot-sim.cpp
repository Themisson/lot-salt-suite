#include <cstdlib>
#include <exception>
#include <filesystem>
#include <iostream>
#include <string>

#include "core/types.hpp"
#include "io/CaseParser.hpp"
#include "io/ResultWriter.hpp"
#include "lot/PknRunner.hpp"

namespace {

std::string enabled_text(bool enabled) {
  return enabled ? "enabled" : "disabled";
}

std::string scheme_text(lss::core::TimeConfig::Scheme scheme) {
  switch (scheme) {
    case lss::core::TimeConfig::Scheme::Explicit:
      return "explicit";
    case lss::core::TimeConfig::Scheme::ImplicitAdaptive:
      return "implicit_adaptive";
  }
  return "unknown";
}

bool has_salt(const lss::core::CaseData& data) {
  for (const auto& rock : data.rocks) {
    if (rock.model == lss::core::RockData::Model::DoubleMechanism) {
      return true;
    }
  }
  return false;
}

int inspect_case(const std::filesystem::path& case_path) {
  const auto data = lss::io::parse_yaml(case_path);

  std::cout << "Name     : " << data.name << '\n';
  std::cout << "Mode     : " << data.mode << '\n';
  std::cout << "Casings  : " << data.casings.size() << '\n';
  std::cout << "Fluids   : " << data.fluids.size() << '\n';
  std::cout << "Layers   : " << data.layers.size() << '\n';
  std::cout << "LOT      : " << enabled_text(data.lot.enabled)
            << "  Geometry: " << data.lot.fracture_geometry << '\n';
  std::cout << "APB      : " << enabled_text(data.apb.enabled) << '\n';
  std::cout << "Salt     : " << (has_salt(data) ? "sim" : "nao") << '\n';
  std::cout << "Time     : " << data.time.total_h << "h, dt=" << data.time.dt_h
            << "h, scheme=" << scheme_text(data.time.scheme) << '\n';

  return EXIT_SUCCESS;
}

int validate_case(const std::filesystem::path& case_path) {
  const auto data = lss::io::parse_yaml(case_path);
  std::cout << "OK: " << data.name << '\n';
  return EXIT_SUCCESS;
}

std::string option_value(int argc, char* argv[], const std::string& option) {
  for (int i = 2; i + 1 < argc; ++i) {
    if (std::string(argv[i]) == option) {
      return argv[i + 1];
    }
  }
  return {};
}

int run_case(int argc, char* argv[]) {
  const std::string case_arg = option_value(argc, argv, "--case");
  const std::string mode_arg = option_value(argc, argv, "--mode");
  const std::string output_arg = option_value(argc, argv, "--output");
  if (case_arg.empty() || mode_arg.empty() || output_arg.empty()) {
    throw std::runtime_error("run exige --case, --mode e --output");
  }
  if (mode_arg != "lot-pkn") {
    throw std::runtime_error("run suporta apenas --mode lot-pkn nesta fase");
  }

  const auto data = lss::io::parse_yaml(case_arg);
  const auto run = lss::lot::run_pkn_case(data);
  lss::io::write_pkn_result(output_arg, data.name, run.result);

  std::cout << "OK: " << data.name << '\n';
  std::cout << "Mode: lot-pkn\n";
  std::cout << "Output: " << std::filesystem::path(output_arg).string() << '\n';
  std::cout << "Files: result.json, timeseries.csv\n";
  return EXIT_SUCCESS;
}

void print_usage() {
  std::cerr << "Uso:\n"
            << "  lot-sim inspect --case <arquivo.yaml>\n"
            << "  lot-sim validate --case <arquivo.yaml>\n"
            << "  lot-sim run --case <arquivo.yaml> --mode lot-pkn --output <dir>\n";
}

}  // namespace

int main(int argc, char* argv[]) {
  if (argc < 2) {
    print_usage();
    return EXIT_FAILURE;
  }

  try {
    const std::string command = argv[1];
    if (command == "run") {
      return run_case(argc, argv);
    }

    if (argc != 4 || std::string(argv[2]) != "--case") {
      print_usage();
      return EXIT_FAILURE;
    }
    if (command == "inspect") {
      return inspect_case(argv[3]);
    }
    if (command == "validate") {
      return validate_case(argv[3]);
    }
    print_usage();
    return EXIT_FAILURE;
  } catch (const std::exception& ex) {
    std::cerr << "Erro: " << ex.what() << '\n';
    return EXIT_FAILURE;
  }
}
