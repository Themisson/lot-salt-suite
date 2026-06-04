#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "coupling/LotSaltCouplingConfigBuilder.hpp"
#include "coupling/LotSaltCouplingStep.hpp"
#include "lot/PknModel.hpp"
#include "salt/SaltCreepInterface.hpp"
#include "salt/SaltCreepTypes.hpp"
#include "units/units.hpp"

namespace {

lss::core::CaseData make_case_data() {
  lss::core::CaseData data;
  data.lot.enabled = true;
  data.lot.shoe_depth_m = 3000.0;

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

  return data;
}

lss::coupling::LotSaltHydrostaticContext make_context() {
  lss::coupling::LotSaltHydrostaticContext context;
  context.depth_m = 3000.0;
  context.density_kg_m3 = 1200.0;
  context.hydrostatic_pressure_Pa =
      units::hydrostatic_pressure_Pa(context.density_kg_m3, context.depth_m);
  context.annular_index = 0;
  context.fluid_id = "mud";
  context.source = "test";
  return context;
}

lss::lot::PknResult make_pkn_result() {
  lss::lot::PknResult result;
  result.time_series_s = {0.0, 30.0};
  result.net_pressure_series_Pa = {1.5e6, 2.0e6};
  return result;
}

class SpySaltCreepInterface final : public lss::salt::SaltCreepInterface {
 public:
  [[nodiscard]] bool is_available() const override { return true; }

  [[nodiscard]] lss::salt::SaltCreepResponse evaluate_wall_response(
      const lss::salt::SaltCreepQuery& query) const override {
    last_query_ = query;
    ++call_count_;
    return {};
  }

  [[nodiscard]] int call_count() const { return call_count_; }
  [[nodiscard]] const lss::salt::SaltCreepQuery& last_query() const {
    return last_query_;
  }

 private:
  mutable int call_count_ = 0;
  mutable lss::salt::SaltCreepQuery last_query_;
};

}  // namespace

TEST_CASE("LotSaltCouplingConfigBuilder creates hydrostatic config from context") {
  const auto context = make_context();

  const auto config =
      lss::coupling::make_lot_salt_coupling_config_from_hydrostatic_context(
          context);

  CHECK(config.hydrostatic_pressure_Pa ==
        Catch::Approx(context.hydrostatic_pressure_Pa));
  CHECK(config.depth_m == Catch::Approx(context.depth_m));
  CHECK(config.pressure_map_method ==
        lss::coupling::LotSaltPressureMapMethod::HydrostaticPlusNetPressure);
  CHECK(config.surface_pressure_Pa == Catch::Approx(0.0));
  CHECK(config.temperature_K == Catch::Approx(350.0));
  CHECK(config.radial_position_m == Catch::Approx(0.1556));
}

TEST_CASE("LotSaltCouplingConfigBuilder applies explicit options") {
  const auto context = make_context();
  lss::coupling::LotSaltCouplingConfigOptions options;
  options.surface_pressure_Pa = 2.0e6;
  options.temperature_K = 410.0;
  options.radial_position_m = 0.25;
  options.method =
      lss::coupling::LotSaltPressureMapMethod::AbsoluteWellborePressure;

  const auto config =
      lss::coupling::make_lot_salt_coupling_config_from_hydrostatic_context(
          context, options);

  CHECK(config.surface_pressure_Pa == Catch::Approx(2.0e6));
  CHECK(config.temperature_K == Catch::Approx(410.0));
  CHECK(config.radial_position_m == Catch::Approx(0.25));
  CHECK(config.pressure_map_method ==
        lss::coupling::LotSaltPressureMapMethod::AbsoluteWellborePressure);
}

TEST_CASE("LotSaltCouplingConfigBuilder creates hydrostatic config from CaseData") {
  const auto data = make_case_data();

  const auto config =
      lss::coupling::make_hydrostatic_lot_salt_coupling_config(data);

  CHECK(config.hydrostatic_pressure_Pa ==
        Catch::Approx(units::hydrostatic_pressure_Pa(1200.0, 3000.0)));
  CHECK(config.depth_m == Catch::Approx(3000.0));
  CHECK(config.pressure_map_method ==
        lss::coupling::LotSaltPressureMapMethod::HydrostaticPlusNetPressure);
}

TEST_CASE("LotSaltCouplingConfigBuilder enables opt-in hydrostatic coupling step") {
  const auto data = make_case_data();
  const auto config =
      lss::coupling::make_hydrostatic_lot_salt_coupling_config(data);
  const auto pkn_result = make_pkn_result();

  SpySaltCreepInterface spy;
  constexpr std::size_t kStep = 1;

  const auto step_result = lss::coupling::evaluate_lot_salt_step(
      pkn_result, kStep, config, spy);

  const double expected_pressure_Pa = config.surface_pressure_Pa +
                                      config.hydrostatic_pressure_Pa +
                                      pkn_result.net_pressure_series_Pa[kStep];
  CHECK(spy.call_count() == 1);
  CHECK(step_result.pressure_map.method ==
        lss::coupling::LotSaltPressureMapMethod::HydrostaticPlusNetPressure);
  CHECK(step_result.pressure_map.physically_absolute == true);
  CHECK(step_result.query.wall_pressure_Pa ==
        Catch::Approx(expected_pressure_Pa));
  CHECK(spy.last_query().wall_pressure_Pa ==
        Catch::Approx(expected_pressure_Pa));
}

TEST_CASE("LotSaltCouplingConfig default remains experimental without builder") {
  const lss::coupling::LotSaltCouplingConfig config;

  CHECK(config.pressure_map_method ==
        lss::coupling::LotSaltPressureMapMethod::ExperimentalNetPressureProxy);
}

TEST_CASE("LotSaltCouplingConfigBuilder allows explicit experimental method") {
  const auto context = make_context();
  lss::coupling::LotSaltCouplingConfigOptions options;
  options.method =
      lss::coupling::LotSaltPressureMapMethod::ExperimentalNetPressureProxy;

  const auto config =
      lss::coupling::make_lot_salt_coupling_config_from_hydrostatic_context(
          context, options);

  CHECK(config.pressure_map_method ==
        lss::coupling::LotSaltPressureMapMethod::ExperimentalNetPressureProxy);
}

TEST_CASE("LotSaltCouplingConfigBuilder rejects invalid options") {
  const auto context = make_context();
  const double nan = std::numeric_limits<double>::quiet_NaN();
  const double inf = std::numeric_limits<double>::infinity();

  lss::coupling::LotSaltCouplingConfigOptions options;
  options.temperature_K = 0.0;
  CHECK_THROWS_AS(
      lss::coupling::make_lot_salt_coupling_config_from_hydrostatic_context(
          context, options),
      std::invalid_argument);

  options = {};
  options.temperature_K = -1.0;
  CHECK_THROWS_AS(
      lss::coupling::make_lot_salt_coupling_config_from_hydrostatic_context(
          context, options),
      std::invalid_argument);

  options = {};
  options.surface_pressure_Pa = -1.0;
  CHECK_THROWS_AS(
      lss::coupling::make_lot_salt_coupling_config_from_hydrostatic_context(
          context, options),
      std::invalid_argument);

  options = {};
  options.radial_position_m = -1.0;
  CHECK_THROWS_AS(
      lss::coupling::make_lot_salt_coupling_config_from_hydrostatic_context(
          context, options),
      std::invalid_argument);

  options = {};
  options.temperature_K = nan;
  CHECK_THROWS_AS(
      lss::coupling::make_lot_salt_coupling_config_from_hydrostatic_context(
          context, options),
      std::invalid_argument);

  options = {};
  options.surface_pressure_Pa = inf;
  CHECK_THROWS_AS(
      lss::coupling::make_lot_salt_coupling_config_from_hydrostatic_context(
          context, options),
      std::invalid_argument);

  options = {};
  options.radial_position_m = nan;
  CHECK_THROWS_AS(
      lss::coupling::make_lot_salt_coupling_config_from_hydrostatic_context(
          context, options),
      std::invalid_argument);
}
