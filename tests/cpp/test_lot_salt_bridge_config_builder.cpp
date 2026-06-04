#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "coupling/LotSaltBridgeConfigBuilder.hpp"
#include "io/CaseParser.hpp"
#include "salt/SaltCreepTimeBridge.hpp"
#include "units/units.hpp"

namespace {

lss::core::CaseData make_case_data() {
  lss::core::CaseData data;
  data.lot.enabled = true;
  data.lot.shoe_depth_m = 3000.0;
  data.lot.fracture_height_m = 25.0;

  lss::core::FluidData fluid;
  fluid.id = "mud";
  fluid.density_kg_m3 = 1200.0;
  data.fluids.push_back(fluid);

  lss::core::AnnularData annular;
  annular.id = "annulus_a";
  annular.fluid_id = "mud";
  annular.top_m = 0.0;
  annular.base_m = 3000.0;
  data.annulars.push_back(annular);

  lss::core::RockData rock;
  rock.id = "halite";
  rock.E_Pa = 20.4e9;
  rock.nu = 0.36;
  rock.density_kg_m3 = 2160.0;
  data.rocks.push_back(rock);

  lss::core::LayerData layer;
  layer.id = "salt";
  layer.rock_id = "halite";
  layer.top_m = 2500.0;
  layer.base_m = 3200.0;
  data.layers.push_back(layer);

  return data;
}

}  // namespace

TEST_CASE("LotSaltBridgeConfigBuilder derives bridge config from minimal case") {
  const auto data = make_case_data();
  lss::coupling::LotSaltBridgeConfigOptions options;
  options.inner_radius_m = 0.20;
  options.outer_radius_m = 2.00;
  options.radial_elements = 24;
  options.temperature_K = 365.0;

  const auto config =
      lss::coupling::make_lot_salt_bridge_config(data, options);

  CHECK(config.elastic_modulus_Pa == Catch::Approx(20.4e9));
  CHECK(config.poisson_ratio == Catch::Approx(0.36));
  CHECK(config.wall_pressure_Pa ==
        Catch::Approx(units::hydrostatic_pressure_Pa(1200.0, 3000.0)));
  CHECK(config.height_m == Catch::Approx(25.0));
  CHECK(config.inner_radius_m == Catch::Approx(0.20));
  CHECK(config.outer_radius_m == Catch::Approx(2.00));
  CHECK(config.radial_elements == 24);
  CHECK(config.temperature_K == Catch::Approx(365.0));
  CHECK(config.reference_temperature_K == Catch::Approx(365.0));
  CHECK(config.geostatic_enabled == false);
  CHECK(config.fix_outer_wall == false);
}

TEST_CASE("LotSaltBridgeConfigBuilder geometry is controlled by options") {
  auto data = make_case_data();
  data.lot.fracture_height_m = 50.0;

  lss::coupling::LotSaltBridgeConfigOptions options;
  options.inner_radius_m = 0.10;
  options.outer_radius_m = 1.10;
  options.radial_elements = 12;

  const auto config =
      lss::coupling::make_lot_salt_bridge_config(data, options);

  CHECK(config.inner_radius_m == Catch::Approx(0.10));
  CHECK(config.outer_radius_m == Catch::Approx(1.10));
  CHECK(config.radial_elements == 12);
  CHECK(config.height_m == Catch::Approx(50.0));
}

TEST_CASE("LotSaltBridgeConfigBuilder output constructs an available bridge") {
  const auto data = make_case_data();
  auto config = lss::coupling::make_lot_salt_bridge_config(data);
  config.radial_elements = 12;

  const lss::salt::SaltCreepTimeBridge bridge(config);

  CHECK(bridge.is_available());
  const auto diagnostics = bridge.wall_stress_diagnostics();
  CHECK(diagnostics.valid);
  CHECK_FALSE(diagnostics.wall_samples.empty());
}

TEST_CASE("LotSaltBridgeConfigBuilder rejects missing layer at shoe") {
  auto data = make_case_data();
  data.layers.front().top_m = 0.0;
  data.layers.front().base_m = 1000.0;

  CHECK_THROWS_AS(lss::coupling::make_lot_salt_bridge_config(data),
                  std::invalid_argument);
}

TEST_CASE("LotSaltBridgeConfigBuilder rejects ambiguous shoe layers") {
  auto data = make_case_data();
  lss::core::LayerData overlap;
  overlap.id = "overlap";
  overlap.rock_id = "halite";
  overlap.top_m = 2900.0;
  overlap.base_m = 3100.0;
  data.layers.push_back(overlap);

  CHECK_THROWS_AS(lss::coupling::make_lot_salt_bridge_config(data),
                  std::invalid_argument);
}

TEST_CASE("LotSaltBridgeConfigBuilder rejects missing rock reference") {
  auto data = make_case_data();
  data.layers.front().rock_id = "missing";

  CHECK_THROWS_AS(lss::coupling::make_lot_salt_bridge_config(data),
                  std::invalid_argument);
}

TEST_CASE("LotSaltBridgeConfigBuilder rejects invalid options and case fields") {
  const double nan = std::numeric_limits<double>::quiet_NaN();
  auto data = make_case_data();
  lss::coupling::LotSaltBridgeConfigOptions options;

  options.inner_radius_m = 0.0;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_bridge_config(data, options),
                  std::invalid_argument);

  options = {};
  options.outer_radius_m = 0.1556;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_bridge_config(data, options),
                  std::invalid_argument);

  options = {};
  options.radial_elements = 0;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_bridge_config(data, options),
                  std::invalid_argument);

  options = {};
  options.temperature_K = 0.0;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_bridge_config(data, options),
                  std::invalid_argument);

  options = {};
  options.temperature_K = nan;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_bridge_config(data, options),
                  std::invalid_argument);

  options = {};
  options.use_lot_fracture_height = false;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_bridge_config(data, options),
                  std::invalid_argument);

  options = {};
  options.geostatic_enabled = true;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_bridge_config(data, options),
                  std::invalid_argument);

  options = {};
  data = make_case_data();
  data.lot.fracture_height_m = 0.0;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_bridge_config(data, options),
                  std::invalid_argument);

  data = make_case_data();
  data.rocks.front().E_Pa = -1.0;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_bridge_config(data, options),
                  std::invalid_argument);

  data = make_case_data();
  data.rocks.front().nu = 0.5;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_bridge_config(data, options),
                  std::invalid_argument);
}

TEST_CASE("LotSaltBridgeConfigBuilder works with real minimal LOT PKN YAML") {
  const auto data =
      lss::io::parse_yaml("cases/validation/lot_pkn_minimal.yaml");
  lss::coupling::LotSaltBridgeConfigOptions options;
  options.radial_elements = 12;

  const auto config =
      lss::coupling::make_lot_salt_bridge_config(data, options);
  const lss::salt::SaltCreepTimeBridge bridge(config);
  const auto diagnostics = bridge.wall_stress_diagnostics();

  CHECK(bridge.is_available());
  CHECK(config.elastic_modulus_Pa == Catch::Approx(20.4e9));
  CHECK(config.poisson_ratio == Catch::Approx(0.36));
  CHECK(config.height_m == Catch::Approx(20.0));
  CHECK(config.wall_pressure_Pa ==
        Catch::Approx(units::hydrostatic_pressure_Pa(
            units::ppg_to_kg_m3(11.5), 3000.0)));
  CHECK(diagnostics.valid);
  CHECK_FALSE(diagnostics.wall_samples.empty());
}
