#include <filesystem>
#include <fstream>
#include <string>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "io/CaseParser.hpp"

namespace {

constexpr const char* kMinimalCasePath = "cases/validation/lot_minimal.yaml";
constexpr const char* kDoubleMechanismCasePath =
    "cases/validation/lot_double_mechanism_reference.yaml";

std::string valid_case_yaml() {
  return R"(metadata:
  name: valid_inline_case
  version: "0.1"
  mode: lot
units:
  length: m
  pressure: Pa
  temperature: degC
  density: ppg
  viscosity: cP
wellbore:
  airgap_m: 0
  water_depth_m: 0
  total_depth_m: 1000
  shoe_depth_m: 900
casings:
  - id: casing
    top_m: 0
    base_m: 900
    di_in: 10
    de_in: 12
    E_Pa: 210000000000.0
    nu: 0.3
cements: []
fluids:
  - id: mud
    mode: constant
    density_ppg: 10
    viscosity_cP: 2
    compressibility_per_Pa: 0.00000000045
rocks:
  - id: rock
    model: elastic_isotropic
    E_Pa: 20000000000.0
    nu: 0.25
    density_kg_m3: 2400
layers:
  - id: layer
    top_m: 0
    base_m: 1000
    rock: rock
annulars:
  - id: annulus
    fluid: mud
    top_m: 0
    base_m: 900
lot:
  enabled: true
  shoe_depth_m: 900
  fracture:
    geometry: circular
    fluid_viscosity_cP: 2
apb:
  enabled: false
  top_packer_m: 0
  leakage_enabled: false
  venting_enabled: false
time:
  total_h: 1
  dt_h: 1
  scheme: explicit
  solver:
    tol_pressure_bar: 1
    tol_eq: 0.00000001
    stabilization_h: 0
)";
}

std::filesystem::path write_temp_case(const std::string& name,
                                      const std::string& contents) {
  const std::filesystem::path path = std::filesystem::temp_directory_path() / name;
  std::ofstream out(path);
  out << contents;
  return path;
}

}  // namespace

TEST_CASE("Minimal LOT validation case loads") {
  const auto data = lss::io::parse_yaml(kMinimalCasePath);

  CHECK(data.name == "lot_minimal_validation");
  CHECK(data.mode == "lot");
  CHECK(data.casings.size() == 1);
  CHECK(data.fluids.size() == 1);
  CHECK(data.layers.size() == 1);
  CHECK(data.lot.enabled);
  CHECK_FALSE(data.apb.enabled);
}

TEST_CASE("Fluid density is converted from PPG to kg/m3") {
  const auto data = lss::io::parse_yaml(kMinimalCasePath);

  REQUIRE(data.fluids.size() == 1);
  CHECK(data.fluids.front().density_kg_m3 == Catch::Approx(1378.0).epsilon(0.001));
}

TEST_CASE("Casing diameters are converted from inches to meters") {
  const auto data = lss::io::parse_yaml(kMinimalCasePath);

  REQUIRE(data.casings.size() == 1);
  CHECK(data.casings.front().di_m == Catch::Approx(0.37465).margin(1e-5));
}

TEST_CASE("Double mechanism e0 keeps FA01 conversion") {
  const auto data = lss::io::parse_yaml(kDoubleMechanismCasePath);

  REQUIRE(data.rocks.size() == 1);
  const auto& rock = data.rocks.front();
  CHECK(rock.e0_per_h == Catch::Approx(1.8792e-6));
  CHECK(rock.e0_per_min == Catch::Approx(3.132e-8));
}

TEST_CASE("Double mechanism T0 keeps FA02 degC and K values") {
  const auto data = lss::io::parse_yaml(kDoubleMechanismCasePath);

  REQUIRE(data.rocks.size() == 1);
  const auto& rock = data.rocks.front();
  CHECK(rock.T0_degC == Catch::Approx(86.0));
  CHECK(rock.T0_K == Catch::Approx(359.15));
}

TEST_CASE("Missing metadata name throws runtime_error") {
  const auto bad_case = write_temp_case("lss_missing_name.yaml", R"(metadata:
  version: "0.1"
  mode: lot
casings: []
cements: []
fluids: []
rocks: []
layers: []
annulars: []
lot:
  enabled: true
  shoe_depth_m: 1
  fracture:
    geometry: circular
    fluid_viscosity_cP: 1
apb:
  enabled: false
  top_packer_m: 0
  leakage_enabled: false
  venting_enabled: false
time:
  total_h: 1
  dt_h: 1
  scheme: explicit
  solver:
    tol_pressure_bar: 1
    tol_eq: 1.0e-8
    stabilization_h: 0
)");

  CHECK_THROWS_AS(lss::io::parse_yaml(bad_case), std::runtime_error);
  std::filesystem::remove(bad_case);
}

TEST_CASE("Unknown annular fluid reference throws runtime_error") {
  auto yaml = valid_case_yaml();
  const auto pos = yaml.find("fluid: mud");
  REQUIRE(pos != std::string::npos);
  yaml.replace(pos, std::string("fluid: mud").size(), "fluid: missing_mud");
  const auto bad_case = write_temp_case("lss_missing_fluid_reference.yaml", yaml);

  CHECK_THROWS_AS(lss::io::parse_yaml(bad_case), std::runtime_error);
  std::filesystem::remove(bad_case);
}

TEST_CASE("Unknown layer rock reference throws runtime_error") {
  auto yaml = valid_case_yaml();
  const auto pos = yaml.find("rock: rock");
  REQUIRE(pos != std::string::npos);
  yaml.replace(pos, std::string("rock: rock").size(), "rock: missing_rock");
  const auto bad_case = write_temp_case("lss_missing_rock_reference.yaml", yaml);

  CHECK_THROWS_AS(lss::io::parse_yaml(bad_case), std::runtime_error);
  std::filesystem::remove(bad_case);
}

TEST_CASE("Required nonempty lists are validated") {
  auto yaml = valid_case_yaml();
  const auto start = yaml.find("casings:");
  const auto end = yaml.find("cements:");
  REQUIRE(start != std::string::npos);
  REQUIRE(end != std::string::npos);
  yaml.replace(start, end - start, "casings: []\n");
  const auto bad_case = write_temp_case("lss_empty_casings.yaml", yaml);

  CHECK_THROWS_AS(lss::io::parse_yaml(bad_case), std::runtime_error);
  std::filesystem::remove(bad_case);
}
