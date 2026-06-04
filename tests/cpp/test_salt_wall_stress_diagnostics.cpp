#include <cmath>
#include <type_traits>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "coupling/LotSaltSigmaThetaBreakdown.hpp"
#include "salt/SaltCreepTimeBridge.hpp"
#include "salt/SaltWallStressDiagnostics.hpp"

#if __has_include("solver/TimeIntegrator.hpp")
#error "SaltCreepTimeBridge public diagnostics test must not expose TimeIntegrator"
#endif

#if __has_include("solver/TimeState.hpp")
#error "SaltCreepTimeBridge public diagnostics test must not expose TimeState"
#endif

#if __has_include("solver/StressSampler.hpp")
#error "SaltCreepTimeBridge public diagnostics test must not expose StressSampler"
#endif

#if __has_include("physics/stress_utils.hpp")
#error "SaltCreepTimeBridge public diagnostics test must not expose stress_utils"
#endif

#if defined(EIGEN_CORE_H) || defined(EIGEN_DENSE_H)
#error "SaltCreepTimeBridge public diagnostics header must not include Eigen"
#endif

namespace {

lss::salt::SaltCreepTimeBridgeConfig bridge_config() {
  lss::salt::SaltCreepTimeBridgeConfig config;
  config.inner_radius_m = 0.1556;
  config.outer_radius_m = 10.0 * config.inner_radius_m;
  config.height_m = 1.0;
  config.radial_elements = 40;
  config.elastic_modulus_Pa = 25.0e9;
  config.poisson_ratio = 0.30;
  config.temperature_K = 350.0;
  config.reference_temperature_K = 350.0;
  config.alpha_thermal_1_K = 0.0;
  config.wall_pressure_Pa = 10.0e6;
  return config;
}

lss::salt::SaltCreepTimeBridgeConfig compressive_bridge_config() {
  auto config = bridge_config();
  config.wall_pressure_Pa = 0.0;
  config.geostatic_enabled = true;
  config.geostatic_radial_stress_Pa = -2.0e6;
  config.geostatic_hoop_stress_Pa = -2.0e6;
  config.geostatic_vertical_stress_Pa = -2.0e6;
  return config;
}

void check_finite_sample(const lss::salt::SaltWallStressSample& sample) {
  CHECK(std::isfinite(sample.r_m));
  CHECK(std::isfinite(sample.z_m));
  CHECK(std::isfinite(sample.depth_m));
  CHECK(std::isfinite(sample.sigma_rr_Pa));
  CHECK(std::isfinite(sample.sigma_theta_Pa));
  CHECK(std::isfinite(sample.sigma_theta_compression_positive_Pa));
  CHECK(std::isfinite(sample.sigma_zz_Pa));
  CHECK(std::isfinite(sample.sigma_rz_Pa));
  CHECK(std::isfinite(sample.mean_stress_Pa));
  CHECK(std::isfinite(sample.j2_Pa2));
  CHECK(std::isfinite(sample.von_mises_effective_stress_Pa));
}

}  // namespace

TEST_CASE("SaltWallStressDiagnostics defaults are safe") {
  const lss::salt::SaltWallStressDiagnostics diagnostics;

  CHECK(diagnostics.wall_samples.empty());
  CHECK(diagnostics.valid == false);
}

TEST_CASE("SaltCreepTimeBridge returns valid wall stress diagnostics") {
  const lss::salt::SaltCreepTimeBridge bridge(bridge_config());

  const auto diagnostics = bridge.wall_stress_diagnostics();

  CHECK(diagnostics.valid == true);
  REQUIRE_FALSE(diagnostics.wall_samples.empty());
}

TEST_CASE("SaltWallStressDiagnostics fields are finite and sign convention is explicit") {
  const lss::salt::SaltCreepTimeBridge bridge(bridge_config());

  const auto diagnostics = bridge.wall_stress_diagnostics();

  REQUIRE(diagnostics.valid);
  REQUIRE_FALSE(diagnostics.wall_samples.empty());

  for (const auto& sample : diagnostics.wall_samples) {
    check_finite_sample(sample);
    CHECK(sample.sigma_theta_compression_positive_Pa ==
          Catch::Approx(-sample.sigma_theta_Pa).margin(1.0e-8));
  }
}

TEST_CASE("SaltWallStressDiagnostics exposes non-negative J2 and von Mises") {
  lss::salt::SaltCreepTimeBridge bridge(bridge_config());
  (void)bridge.advance_to(60.0, 12.0e6);

  const auto diagnostics = bridge.wall_stress_diagnostics();

  REQUIRE(diagnostics.valid);
  REQUIRE_FALSE(diagnostics.wall_samples.empty());

  for (const auto& sample : diagnostics.wall_samples) {
    CHECK(sample.j2_Pa2 >= 0.0);
    CHECK(sample.von_mises_effective_stress_Pa >= 0.0);
    CHECK(sample.von_mises_effective_stress_Pa *
              sample.von_mises_effective_stress_Pa ==
          Catch::Approx(3.0 * sample.j2_Pa2).epsilon(1.0e-12).margin(1.0e-8));
  }
}

TEST_CASE("SaltWallStressDiagnostics can feed SigmaThetaBreakdown explicitly") {
  const lss::salt::SaltCreepTimeBridge bridge(compressive_bridge_config());
  const auto diagnostics = bridge.wall_stress_diagnostics();

  REQUIRE(diagnostics.valid);
  REQUIRE_FALSE(diagnostics.wall_samples.empty());
  const auto& sample = diagnostics.wall_samples.front();

  lss::coupling::SigmaThetaInfluenceLayer layer;
  layer.layer_id = "wall_gp";
  layer.influence_depth_m = sample.depth_m;
  layer.sigma_theta_compression_positive_Pa =
      sample.sigma_theta_compression_positive_Pa;
  REQUIRE(layer.sigma_theta_compression_positive_Pa >= 0.0);

  const double pressure_Pa = layer.sigma_theta_compression_positive_Pa + 1.0;
  const auto point = lss::coupling::evaluate_sigma_theta_breakdown_point(
      layer, 0.0, pressure_Pa);

  CHECK(std::isfinite(point.margin_Pa));
  CHECK(point.margin_Pa == Catch::Approx(1.0));
  CHECK(point.opened == true);
}
