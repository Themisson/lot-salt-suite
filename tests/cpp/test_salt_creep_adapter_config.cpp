#include <limits>
#include <stdexcept>

#include <catch2/catch_test_macros.hpp>

#include "salt/SaltCreepAdapterConfig.hpp"

namespace {

lss::salt::SaltCreepAdapterConfig valid_config() {
  return lss::salt::make_default_salt_creep_adapter_config();
}

}  // namespace

TEST_CASE("SaltCreepAdapterConfig accepts conservative SI defaults") {
  const auto config = valid_config();

  CHECK_NOTHROW(config.validate());
  CHECK(config.geometry.inner_radius_m > 0.0);
  CHECK(config.geometry.outer_radius_m > config.geometry.inner_radius_m);
  CHECK(config.mesh.radial_elements > 0);
  CHECK(config.material.elastic_modulus_Pa > 0.0);
  CHECK(config.thermal.temperature_K > 0.0);
  CHECK(config.time.dt_s > 0.0);
}

TEST_CASE("SaltCreepAdapterConfig rejects invalid geometry") {
  auto config = valid_config();
  config.geometry.inner_radius_m = 0.0;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);

  config = valid_config();
  config.geometry.outer_radius_m = config.geometry.inner_radius_m;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);

  config = valid_config();
  config.geometry.height_m = -1.0;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);
}

TEST_CASE("SaltCreepAdapterConfig rejects invalid mesh") {
  auto config = valid_config();
  config.mesh.radial_elements = 0;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);

  config = valid_config();
  config.mesh.axial_elements = 0;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);
}

TEST_CASE("SaltCreepAdapterConfig rejects invalid material values") {
  auto config = valid_config();
  config.material.elastic_modulus_Pa = 0.0;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);

  config = valid_config();
  config.material.poisson_ratio = 0.5;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);

  config = valid_config();
  config.material.density_kg_m3 = -1.0;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);
}

TEST_CASE("SaltCreepAdapterConfig rejects invalid thermal values") {
  auto config = valid_config();
  config.thermal.temperature_K = 0.0;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);

  config = valid_config();
  config.thermal.reference_temperature_K = -1.0;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);

  config = valid_config();
  config.thermal.alpha_thermal_1_K =
      std::numeric_limits<double>::quiet_NaN();
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);
}

TEST_CASE("SaltCreepAdapterConfig keeps geostatic stresses signed but finite") {
  auto config = valid_config();
  config.geostatic.enabled = true;
  config.geostatic.radial_stress_Pa = -2.0e6;
  config.geostatic.hoop_stress_Pa = -2.0e6;
  config.geostatic.vertical_stress_Pa = -3.0e6;
  CHECK_NOTHROW(config.validate());

  config.geostatic.vertical_stress_Pa =
      std::numeric_limits<double>::infinity();
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);
}

TEST_CASE("SaltCreepAdapterConfig rejects invalid time and wall pressure") {
  auto config = valid_config();
  config.time.initial_time_s = -1.0;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);

  config = valid_config();
  config.time.dt_s = 0.0;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);

  config = valid_config();
  config.time.total_time_s = config.time.initial_time_s - 1.0;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);

  config = valid_config();
  config.time.max_steps = 0;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);

  config = valid_config();
  config.wall_pressure.initial_wall_pressure_Pa = -1.0;
  CHECK_THROWS_AS(config.validate(), std::invalid_argument);
}
