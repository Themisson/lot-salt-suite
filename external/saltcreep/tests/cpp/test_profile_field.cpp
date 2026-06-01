#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>

#include <filesystem>
#include <fstream>
#include <stdexcept>

#include "io/CaseParser.hpp"
#include "thermal/profile_field.hpp"

namespace fs = std::filesystem;

namespace {
fs::path find_data_dir() {
    for (const auto& candidate : {
             fs::path("data"),
             fs::path("../data"),
             fs::path("../../data")}) {
        if (fs::exists(candidate / "litologias"))
            return candidate;
    }
    throw std::runtime_error("Cannot find data/litologias");
}
}

TEST_CASE("ProfileField: analytical vertical profile evaluates T(z)",
          "[thermal][profile]") {
    ProfileField field = ProfileField::make_profile(
        4.0, 0.0, 0.03, 3.5e-5, 25.0 + 273.15);

    REQUIRE(field.temperature_at(Eigen::Vector2d{0.2, 0.0}, 0.0)
            == Catch::Approx(4.0 + 273.15));
    REQUIRE(field.temperature_at(Eigen::Vector2d{0.2, 1000.0}, 123.0)
            == Catch::Approx(34.0 + 273.15));
}

TEST_CASE("ProfileField: alpha and reference temperature come from construction",
          "[thermal][profile]") {
    ProfileField field = ProfileField::make_profile(
        4.0, 500.0, 0.02, 3.5e-5, 25.0 + 273.15);

    REQUIRE(field.alpha_thermal() == Catch::Approx(3.5e-5));
    REQUIRE(field.T_reference() == Catch::Approx(25.0 + 273.15));
}

TEST_CASE("CaseParser: profile thermal aliases and expansion parameters are accepted",
          "[thermal][parser]") {
    const fs::path dir = fs::temp_directory_path() / "saltcreep_test" / "profile_parser";
    fs::create_directories(dir);
    const fs::path yaml = dir / "case.yaml";

    std::ofstream out(yaml);
    out << R"yaml(
name: profile_parser
geometry:
  well_radius_m: 0.155575
  outer_radius_factor: 10
depths:
  water_depth_m: 1000
  burial_m: 2000
  salt_above_m: 0
lithology:
  primary: halita
fluid:
  weight_lb_per_gal: 10
stress:
  k0: 1.0
thermal:
  enabled: true
  mode: profile
  seabed_temp_C: 4.0
  geothermal_gradient_C_per_m: 0.03
  alpha_thermal: 3.5e-5
  T_reference_C: 25.0
element:
  type: axisym_1d_L3
mesh:
  n_elements_radial: 4
  ratio: 1
creep:
  elastic_only: true
time:
  total_h: 1
  dt_h: 1
)yaml";
    out.close();

    CaseData cd = parse_case(yaml, find_data_dir());
    REQUIRE(cd.thermal.enabled);
    REQUIRE(cd.thermal.grad_C_per_m == Catch::Approx(0.03));
    REQUIRE(cd.thermal.alpha_thermal == Catch::Approx(3.5e-5));
    REQUIRE(cd.thermal.T_reference_K == Catch::Approx(298.15));
    REQUIRE(cd.thermal.T_K == Catch::Approx(4.0 + 0.03 * 3000.0 + 273.15));
}
