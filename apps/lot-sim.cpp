#include <cstdlib>
#include <exception>
#include <filesystem>
#include <iostream>
#include <string>

#include "core/types.hpp"
#include "io/CaseParser.hpp"

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

void print_usage() {
  std::cerr << "Uso: lot-sim inspect --case <arquivo.yaml>\n";
}

}  // namespace

int main(int argc, char* argv[]) {
  if (argc != 4 || std::string(argv[1]) != "inspect" ||
      std::string(argv[2]) != "--case") {
    print_usage();
    return EXIT_FAILURE;
  }

  try {
    return inspect_case(argv[3]);
  } catch (const std::exception& ex) {
    std::cerr << "Erro: " << ex.what() << '\n';
    return EXIT_FAILURE;
  }
}
