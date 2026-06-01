#include <filesystem>
#include <fstream>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "io/CaseParser.hpp"

namespace {

constexpr const char* kMinimalCasePath = "cases/validation/lot_minimal.yaml";
constexpr const char* kDoubleMechanismCasePath =
    "cases/validation/lot_double_mechanism_reference.yaml";

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
  const std::filesystem::path bad_case =
      std::filesystem::temp_directory_path() / "lss_missing_name.yaml";
  {
    std::ofstream out(bad_case);
    out << R"(metadata:
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
)";
  }

  CHECK_THROWS_AS(lss::io::parse_yaml(bad_case), std::runtime_error);
  std::filesystem::remove(bad_case);
}
