#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "coupling/LotSaltBridgeConfigBuilder.hpp"
#include "coupling/LotSaltLithostaticContext.hpp"
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

TEST_CASE("LotSaltLithostaticContext derives isotropic lithostatic pressure") {
  const auto data = make_case_data();

  const auto context =
      lss::coupling::make_lot_salt_lithostatic_context(data);

  CHECK(context.depth_m == Catch::Approx(3000.0));
  CHECK(context.rock_density_kg_m3 == Catch::Approx(2160.0));
  CHECK(context.lithostatic_pressure_Pa ==
        Catch::Approx(units::hydrostatic_pressure_Pa(2160.0, 3000.0)));
  CHECK(context.geostatic_stress_Pa ==
        Catch::Approx(-context.lithostatic_pressure_Pa));
  CHECK(context.rock_id == "halite");
  CHECK(context.layer_id == "salt");
  CHECK_FALSE(context.source.empty());
}

TEST_CASE("LotSaltLithostaticContext selects layer and rock at shoe depth") {
  auto data = make_case_data();

  lss::core::RockData shale;
  shale.id = "shale";
  shale.E_Pa = 12.0e9;
  shale.nu = 0.25;
  shale.density_kg_m3 = 2450.0;
  data.rocks.push_back(shale);

  data.layers.front().top_m = 0.0;
  data.layers.front().base_m = 2000.0;
  lss::core::LayerData target;
  target.id = "deep_shale";
  target.rock_id = "shale";
  target.top_m = 2000.0;
  target.base_m = 3500.0;
  data.layers.push_back(target);

  const auto context =
      lss::coupling::make_lot_salt_lithostatic_context(data);

  CHECK(context.layer_id == "deep_shale");
  CHECK(context.rock_id == "shale");
  CHECK(context.rock_density_kg_m3 == Catch::Approx(2450.0));
}

TEST_CASE("LotSaltLithostaticContext rejects missing layer at shoe") {
  auto data = make_case_data();
  data.layers.front().top_m = 0.0;
  data.layers.front().base_m = 1000.0;

  CHECK_THROWS_AS(lss::coupling::make_lot_salt_lithostatic_context(data),
                  std::invalid_argument);
}

TEST_CASE("LotSaltLithostaticContext rejects ambiguous shoe layers") {
  auto data = make_case_data();
  lss::core::LayerData overlap;
  overlap.id = "overlap";
  overlap.rock_id = "halite";
  overlap.top_m = 2900.0;
  overlap.base_m = 3100.0;
  data.layers.push_back(overlap);

  CHECK_THROWS_AS(lss::coupling::make_lot_salt_lithostatic_context(data),
                  std::invalid_argument);
}

TEST_CASE("LotSaltLithostaticContext rejects missing rock reference") {
  auto data = make_case_data();
  data.layers.front().rock_id = "missing";

  CHECK_THROWS_AS(lss::coupling::make_lot_salt_lithostatic_context(data),
                  std::invalid_argument);
}

TEST_CASE("LotSaltLithostaticContext rejects invalid depth and density") {
  const double nan = std::numeric_limits<double>::quiet_NaN();
  const double inf = std::numeric_limits<double>::infinity();
  auto data = make_case_data();

  data.lot.shoe_depth_m = 0.0;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_lithostatic_context(data),
                  std::invalid_argument);

  data = make_case_data();
  data.lot.shoe_depth_m = nan;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_lithostatic_context(data),
                  std::invalid_argument);

  data = make_case_data();
  data.rocks.front().density_kg_m3 = 0.0;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_lithostatic_context(data),
                  std::invalid_argument);

  data = make_case_data();
  data.rocks.front().density_kg_m3 = -1.0;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_lithostatic_context(data),
                  std::invalid_argument);

  data = make_case_data();
  data.rocks.front().density_kg_m3 = inf;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_lithostatic_context(data),
                  std::invalid_argument);
}

TEST_CASE("with_lithostatic_geostatic fills explicit bridge options") {
  const auto data = make_case_data();
  lss::coupling::LotSaltBridgeConfigOptions options;
  options.inner_radius_m = 0.2;
  options.radial_elements = 12;

  const auto result =
      lss::coupling::with_lithostatic_geostatic(options, data);
  const double expected_stress =
      -units::hydrostatic_pressure_Pa(2160.0, 3000.0);

  CHECK(result.inner_radius_m == Catch::Approx(0.2));
  CHECK(result.radial_elements == 12);
  CHECK(result.geostatic_enabled);
  CHECK(result.geostatic_radial_stress_Pa == Catch::Approx(expected_stress));
  CHECK(result.geostatic_hoop_stress_Pa == Catch::Approx(expected_stress));
  CHECK(result.geostatic_vertical_stress_Pa ==
        Catch::Approx(expected_stress));
}

TEST_CASE("lithostatic bridge options construct an available bridge") {
  const auto data = make_case_data();
  auto options =
      lss::coupling::with_lithostatic_geostatic(
          lss::coupling::LotSaltBridgeConfigOptions{}, data);
  options.radial_elements = 12;

  const auto config =
      lss::coupling::make_lot_salt_bridge_config(data, options);
  const lss::salt::SaltCreepTimeBridge bridge(config);
  const auto diagnostics = bridge.wall_stress_diagnostics();

  CHECK(config.geostatic_enabled);
  CHECK(config.fix_outer_wall);
  CHECK(config.geostatic_radial_stress_Pa < 0.0);
  CHECK(bridge.is_available());
  CHECK(diagnostics.valid);
  CHECK_FALSE(diagnostics.wall_samples.empty());
}
