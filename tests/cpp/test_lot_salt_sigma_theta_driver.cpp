#include <cmath>
#include <limits>
#include <string>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "coupling/LotSaltBridgeConfigBuilder.hpp"
#include "coupling/LotSaltLithostaticContext.hpp"
#include "coupling/LotSaltSigmaThetaDriver.hpp"
#include "io/CaseParser.hpp"
#include "salt/SaltCreepTimeBridge.hpp"
#include "units/units.hpp"

namespace {

lss::core::CaseData make_case_data() {
  lss::core::CaseData data;
  data.name = "driver_test";
  data.version = "0.1";
  data.mode = "lot-pkn";

  lss::core::FluidData fluid;
  fluid.id = "mud";
  fluid.mode = lss::core::FluidData::Mode::Constant;
  fluid.density_kg_m3 = 1200.0;
  fluid.viscosity_Pa_s = 0.003;
  fluid.compressibility_per_Pa = 4.5e-10;
  data.fluids.push_back(fluid);

  lss::core::AnnularData annular;
  annular.id = "annulus_a";
  annular.fluid_id = "mud";
  annular.top_m = 0.0;
  annular.base_m = 3000.0;
  data.annulars.push_back(annular);

  lss::core::RockData rock;
  rock.id = "halite";
  rock.model = lss::core::RockData::Model::ElasticIsotropic;
  rock.E_Pa = 20.4e9;
  rock.nu = 0.36;
  rock.density_kg_m3 = 2160.0;
  data.rocks.push_back(rock);

  lss::core::LayerData layer;
  layer.id = "salt_interval";
  layer.rock_id = "halite";
  layer.top_m = 2500.0;
  layer.base_m = 3200.0;
  data.layers.push_back(layer);

  data.lot.enabled = true;
  data.lot.shoe_depth_m = 3000.0;
  data.lot.model = "pkn";
  data.lot.fracture_geometry = "pkn";
  data.lot.fracture_fluid_viscosity_Pa_s = 0.003;
  data.lot.injection_rate_m3_s = 5.0e-4;
  data.lot.injection_total_time_s = 120.0;
  data.lot.injection_dt_s = 30.0;
  data.lot.injection_accommodation_time_s = 0.0;
  data.lot.fracture_height_m = 20.0;
  data.lot.fracture_initial_width_m = 0.0;
  data.lot.breakdown_method = "pressure_threshold";
  data.lot.breakdown_pressure_Pa = 45.0e6;
  data.lot.leakoff_enabled = false;
  data.lot.leakoff_model = "none";
  data.lot.detection_method = "derivative_drop";
  return data;
}

lss::salt::SaltCreepTimeBridge make_bridge() {
  lss::salt::SaltCreepTimeBridgeConfig config;
  config.inner_radius_m = 0.1556;
  config.outer_radius_m = 1.556;
  config.height_m = 1.0;
  config.radial_elements = 20;
  config.elastic_modulus_Pa = 25.0e9;
  config.poisson_ratio = 0.30;
  config.temperature_K = 350.0;
  config.reference_temperature_K = 350.0;
  config.alpha_thermal_1_K = 0.0;
  config.wall_pressure_Pa = 0.0;
  config.geostatic_enabled = true;
  config.geostatic_radial_stress_Pa = -2.0e6;
  config.geostatic_hoop_stress_Pa = -2.0e6;
  config.geostatic_vertical_stress_Pa = -2.0e6;
  return lss::salt::SaltCreepTimeBridge(config);
}

struct ScenarioSummary {
  std::size_t compressive_count = 0;
  std::size_t neutral_count = 0;
  std::size_t tensile_count = 0;

  double min_sigma_theta_compression_positive_Pa =
      std::numeric_limits<double>::infinity();
  double max_sigma_theta_compression_positive_Pa =
      -std::numeric_limits<double>::infinity();

  double min_margin_Pa = std::numeric_limits<double>::infinity();
  double max_margin_Pa = -std::numeric_limits<double>::infinity();

  bool any_opened = false;
  bool any_legacy_algebra_opened = false;
};

ScenarioSummary summarize_sigma_theta_scenario(
    const lss::coupling::LotSaltSigmaThetaDriverResult& result) {
  ScenarioSummary summary;
  summary.any_opened = result.diagnostic.any_opened;

  for (const auto& point : result.diagnostic.points) {
    switch (point.breakdown.hoop_state) {
      case lss::coupling::SigmaThetaHoopState::Compressive:
        ++summary.compressive_count;
        break;
      case lss::coupling::SigmaThetaHoopState::Neutral:
        ++summary.neutral_count;
        break;
      case lss::coupling::SigmaThetaHoopState::Tensile:
        ++summary.tensile_count;
        break;
    }

    summary.min_sigma_theta_compression_positive_Pa =
        std::min(summary.min_sigma_theta_compression_positive_Pa,
                 point.breakdown.sigma_theta_compression_positive_Pa);
    summary.max_sigma_theta_compression_positive_Pa =
        std::max(summary.max_sigma_theta_compression_positive_Pa,
                 point.breakdown.sigma_theta_compression_positive_Pa);
    summary.min_margin_Pa =
        std::min(summary.min_margin_Pa, point.breakdown.margin_Pa);
    summary.max_margin_Pa =
        std::max(summary.max_margin_Pa, point.breakdown.margin_Pa);
    summary.any_legacy_algebra_opened =
        summary.any_legacy_algebra_opened ||
        point.breakdown.legacy_algebra_opened;
  }

  return summary;
}

void check_valid_scenario_result(
    const lss::coupling::LotSaltSigmaThetaDriverResult& result,
    const ScenarioSummary& summary,
    int step_count_before,
    const lss::salt::SaltCreepTimeBridge& bridge) {
  CHECK(result.valid == true);
  CHECK(result.wall_stress.valid == true);
  CHECK(result.diagnostic.valid == true);
  REQUIRE_FALSE(result.diagnostic.points.empty());
  CHECK(bridge.result().step_count == step_count_before);

  const auto state_count = summary.compressive_count + summary.neutral_count +
                           summary.tensile_count;
  CHECK(state_count == result.diagnostic.points.size());
  CHECK(std::isfinite(summary.min_sigma_theta_compression_positive_Pa));
  CHECK(std::isfinite(summary.max_sigma_theta_compression_positive_Pa));
  CHECK(std::isfinite(summary.min_margin_Pa));
  CHECK(std::isfinite(summary.max_margin_Pa));
  CHECK(summary.any_opened == result.diagnostic.any_opened);
}

}  // namespace

TEST_CASE("LotSaltSigmaThetaDriver executes the experimental chain") {
  const auto data = make_case_data();
  auto bridge = make_bridge();
  const int initial_step_count = bridge.result().step_count;

  const auto result =
      lss::coupling::run_lot_salt_sigma_theta_experimental(data, bridge);

  CHECK(result.valid == true);
  CHECK_FALSE(result.pkn_run.result.time_series_s.empty());
  CHECK(result.wall_stress.valid == true);
  CHECK_FALSE(result.wall_stress.wall_samples.empty());
  CHECK(result.diagnostic.valid == true);
  CHECK_FALSE(result.diagnostic.points.empty());
  CHECK(result.coupling_config.pressure_map_method ==
        lss::coupling::LotSaltPressureMapMethod::HydrostaticPlusNetPressure);
  CHECK(result.coupling_config.hydrostatic_pressure_Pa ==
        Catch::Approx(units::hydrostatic_pressure_Pa(1200.0, 3000.0)));
  CHECK(bridge.result().step_count == initial_step_count);
}

TEST_CASE("LotSaltSigmaThetaDriver allows experimental pressure map override") {
  const auto data = make_case_data();
  auto bridge = make_bridge();
  lss::coupling::LotSaltCouplingConfigOptions options;
  options.method =
      lss::coupling::LotSaltPressureMapMethod::ExperimentalNetPressureProxy;

  const auto result = lss::coupling::run_lot_salt_sigma_theta_experimental(
      data, bridge, options);

  REQUIRE(result.valid);
  REQUIRE_FALSE(result.diagnostic.points.empty());
  CHECK(result.coupling_config.pressure_map_method ==
        lss::coupling::LotSaltPressureMapMethod::ExperimentalNetPressureProxy);
  CHECK(result.diagnostic.pressure_source ==
        "LotSaltPressureMap:experimental_net_pressure_proxy");
  CHECK(result.diagnostic.points.front().pressure_map.method ==
        lss::coupling::LotSaltPressureMapMethod::ExperimentalNetPressureProxy);
}

TEST_CASE("LotSaltSigmaThetaDriver returns traceable components and caveat") {
  const auto data = make_case_data();
  auto bridge = make_bridge();

  const auto result =
      lss::coupling::run_lot_salt_sigma_theta_experimental(data, bridge);

  CHECK_FALSE(result.pkn_run.result.net_pressure_series_Pa.empty());
  CHECK(result.coupling_config.depth_m == Catch::Approx(3000.0));
  CHECK(result.wall_stress.valid);
  CHECK(result.diagnostic.valid);
  CHECK_FALSE(result.caveat.empty());
  CHECK(result.caveat.find("snapshot") != std::string::npos);
  CHECK(result.caveat.find("not temporally synchronized") !=
        std::string::npos);
}

TEST_CASE("LotSaltSigmaThetaDriver runs after bridge config builder without geostatic") {
  const auto data =
      lss::io::parse_yaml("cases/validation/lot_pkn_minimal.yaml");
  lss::coupling::LotSaltBridgeConfigOptions bridge_options;
  bridge_options.radial_elements = 12;
  auto bridge_config =
      lss::coupling::make_lot_salt_bridge_config(data, bridge_options);
  lss::salt::SaltCreepTimeBridge bridge(bridge_config);
  const int step_count_before = bridge.result().step_count;

  const auto result =
      lss::coupling::run_lot_salt_sigma_theta_experimental(data, bridge);

  CHECK(result.valid == true);
  CHECK(result.wall_stress.valid == true);
  CHECK(result.diagnostic.valid == true);
  CHECK_FALSE(result.diagnostic.points.empty());
  CHECK(result.coupling_config.pressure_map_method ==
        lss::coupling::LotSaltPressureMapMethod::HydrostaticPlusNetPressure);
  CHECK(bridge_config.elastic_modulus_Pa == Catch::Approx(20.4e9));
  CHECK(bridge_config.poisson_ratio == Catch::Approx(0.36));
  CHECK(bridge.result().step_count == step_count_before);
  CHECK_FALSE(result.caveat.empty());
  REQUIRE_FALSE(result.diagnostic.points.empty());
  CHECK(result.diagnostic.points.front().breakdown.hoop_state ==
        lss::coupling::SigmaThetaHoopState::Tensile);
  CHECK(result.diagnostic.points.front().breakdown.tensile_hoop_state);
  CHECK_FALSE(result.diagnostic.points.front().breakdown.caveat.empty());
}

TEST_CASE("LotSaltSigmaThetaDriver runs after bridge config builder with explicit geostatic") {
  const auto data =
      lss::io::parse_yaml("cases/validation/lot_pkn_minimal.yaml");
  lss::coupling::LotSaltBridgeConfigOptions bridge_options;
  bridge_options.radial_elements = 12;
  bridge_options.geostatic_enabled = true;
  bridge_options.geostatic_radial_stress_Pa = -2.0e6;
  bridge_options.geostatic_hoop_stress_Pa = -2.0e6;
  bridge_options.geostatic_vertical_stress_Pa = -2.0e6;
  auto bridge_config =
      lss::coupling::make_lot_salt_bridge_config(data, bridge_options);
  lss::salt::SaltCreepTimeBridge bridge(bridge_config);
  const int step_count_before = bridge.result().step_count;

  const auto result =
      lss::coupling::run_lot_salt_sigma_theta_experimental(data, bridge);

  CHECK(result.valid == true);
  CHECK(result.wall_stress.valid == true);
  CHECK(result.diagnostic.valid == true);
  CHECK_FALSE(result.diagnostic.points.empty());
  CHECK(bridge.result().step_count == step_count_before);
  REQUIRE_FALSE(result.wall_stress.wall_samples.empty());
  REQUIRE_FALSE(result.diagnostic.points.empty());
  CHECK(result.diagnostic.points.front().breakdown.hoop_state ==
        lss::coupling::classify_sigma_theta_hoop_state(
            result.wall_stress.wall_samples.front()
                .sigma_theta_compression_positive_Pa));
}

TEST_CASE("LotSaltSigmaThetaDriver runs full chain with lithostatic geostatic options") {
  const auto data =
      lss::io::parse_yaml("cases/validation/lot_pkn_minimal.yaml");
  lss::coupling::LotSaltBridgeConfigOptions bridge_options;
  bridge_options.radial_elements = 12;
  bridge_options =
      lss::coupling::with_lithostatic_geostatic(bridge_options, data);

  const auto bridge_config =
      lss::coupling::make_lot_salt_bridge_config(data, bridge_options);
  lss::salt::SaltCreepTimeBridge bridge(bridge_config);
  const int step_count_before = bridge.result().step_count;

  const auto result =
      lss::coupling::run_lot_salt_sigma_theta_experimental(data, bridge);

  const double expected_lithostatic_pressure_Pa =
      2160.0 * units::kStandardGravity * 3000.0;
  const double expected_geostatic_stress_Pa =
      -expected_lithostatic_pressure_Pa;

  CHECK(bridge_config.geostatic_enabled == true);
  CHECK(bridge_config.geostatic_radial_stress_Pa ==
        Catch::Approx(expected_geostatic_stress_Pa));
  CHECK(bridge_config.geostatic_hoop_stress_Pa ==
        Catch::Approx(expected_geostatic_stress_Pa));
  CHECK(bridge_config.geostatic_vertical_stress_Pa ==
        Catch::Approx(expected_geostatic_stress_Pa));
  CHECK(bridge_config.geostatic_radial_stress_Pa < 0.0);
  CHECK(bridge_config.geostatic_hoop_stress_Pa < 0.0);
  CHECK(bridge_config.geostatic_vertical_stress_Pa < 0.0);
  CHECK(bridge_config.fix_outer_wall == true);

  CHECK(result.valid == true);
  CHECK(result.wall_stress.valid == true);
  CHECK(result.diagnostic.valid == true);
  CHECK_FALSE(result.diagnostic.points.empty());
  CHECK(bridge.result().step_count == step_count_before);
  CHECK_FALSE(result.caveat.empty());

  bool has_traceable_hoop_state = false;
  bool has_compressive_hoop_state = false;
  for (const auto& point : result.diagnostic.points) {
    switch (point.breakdown.hoop_state) {
      case lss::coupling::SigmaThetaHoopState::Compressive:
        has_traceable_hoop_state = true;
        has_compressive_hoop_state = true;
        break;
      case lss::coupling::SigmaThetaHoopState::Neutral:
      case lss::coupling::SigmaThetaHoopState::Tensile:
        has_traceable_hoop_state = true;
        break;
    }
  }

  CHECK(has_traceable_hoop_state);
  if (!has_compressive_hoop_state) {
    WARN("Lithostatic geostatic options produced no compressive hoop state in "
         "this backend snapshot.");
  }
}

TEST_CASE("LotSaltSigmaThetaDriver compares sigma theta confinement scenarios") {
  const auto data =
      lss::io::parse_yaml("cases/validation/lot_pkn_minimal.yaml");

  lss::coupling::LotSaltBridgeConfigOptions no_geostatic_options;
  no_geostatic_options.radial_elements = 12;
  no_geostatic_options.geostatic_enabled = false;
  const auto no_geostatic_config =
      lss::coupling::make_lot_salt_bridge_config(data, no_geostatic_options);
  lss::salt::SaltCreepTimeBridge no_geostatic_bridge(no_geostatic_config);
  const int no_geostatic_step_count =
      no_geostatic_bridge.result().step_count;
  const auto no_geostatic_result =
      lss::coupling::run_lot_salt_sigma_theta_experimental(
          data, no_geostatic_bridge);
  const auto no_geostatic_summary =
      summarize_sigma_theta_scenario(no_geostatic_result);

  lss::coupling::LotSaltBridgeConfigOptions synthetic_options;
  synthetic_options.radial_elements = 12;
  synthetic_options.geostatic_enabled = true;
  synthetic_options.geostatic_radial_stress_Pa = -2.0e6;
  synthetic_options.geostatic_hoop_stress_Pa = -2.0e6;
  synthetic_options.geostatic_vertical_stress_Pa = -2.0e6;
  const auto synthetic_config =
      lss::coupling::make_lot_salt_bridge_config(data, synthetic_options);
  lss::salt::SaltCreepTimeBridge synthetic_bridge(synthetic_config);
  const int synthetic_step_count = synthetic_bridge.result().step_count;
  const auto synthetic_result =
      lss::coupling::run_lot_salt_sigma_theta_experimental(
          data, synthetic_bridge);
  const auto synthetic_summary =
      summarize_sigma_theta_scenario(synthetic_result);

  lss::coupling::LotSaltBridgeConfigOptions lithostatic_options;
  lithostatic_options.radial_elements = 12;
  lithostatic_options =
      lss::coupling::with_lithostatic_geostatic(lithostatic_options, data);
  const auto lithostatic_config =
      lss::coupling::make_lot_salt_bridge_config(data, lithostatic_options);
  lss::salt::SaltCreepTimeBridge lithostatic_bridge(lithostatic_config);
  const int lithostatic_step_count = lithostatic_bridge.result().step_count;
  const auto lithostatic_result =
      lss::coupling::run_lot_salt_sigma_theta_experimental(
          data, lithostatic_bridge);
  const auto lithostatic_summary =
      summarize_sigma_theta_scenario(lithostatic_result);

  check_valid_scenario_result(no_geostatic_result, no_geostatic_summary,
                              no_geostatic_step_count, no_geostatic_bridge);
  check_valid_scenario_result(synthetic_result, synthetic_summary,
                              synthetic_step_count, synthetic_bridge);
  check_valid_scenario_result(lithostatic_result, lithostatic_summary,
                              lithostatic_step_count, lithostatic_bridge);

  CHECK(no_geostatic_config.geostatic_enabled == false);
  CHECK(no_geostatic_config.fix_outer_wall == false);
  CHECK(synthetic_config.geostatic_enabled == true);
  CHECK(synthetic_config.geostatic_hoop_stress_Pa == Catch::Approx(-2.0e6));
  CHECK(synthetic_config.fix_outer_wall == true);
  CHECK(lithostatic_config.geostatic_enabled == true);
  CHECK(lithostatic_config.geostatic_hoop_stress_Pa < 0.0);
  CHECK(lithostatic_config.fix_outer_wall == true);

  CHECK(no_geostatic_summary.tensile_count > 0);
  CHECK(lithostatic_summary.compressive_count > 0);
  CHECK(lithostatic_summary.compressive_count >=
        synthetic_summary.compressive_count);
  CHECK(no_geostatic_summary.tensile_count != lithostatic_summary.tensile_count);
}
