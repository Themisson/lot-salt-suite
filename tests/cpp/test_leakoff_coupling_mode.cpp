#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "lot/LeakoffCouplingMode.hpp"

TEST_CASE("Leakoff coupling volume_balance adds leakoff contribution to dV") {
  const auto result = lss::lot::apply_leakoff_coupling(
      lss::lot::LeakoffCouplingMode::VolumeBalance, {10.0, -2.0});

  CHECK(result.coupled_dV_m3 == Catch::Approx(8.0));
  CHECK(result.volume_balance_applied);
  CHECK_FALSE(result.legacy_nodal_force_preserved);
}

TEST_CASE("Leakoff coupling legacy_nodal_force preserves dV") {
  const auto result = lss::lot::apply_leakoff_coupling(
      lss::lot::LeakoffCouplingMode::LegacyNodalForce, {10.0, -2.0});

  CHECK(result.coupled_dV_m3 == Catch::Approx(10.0));
  CHECK(result.legacy_nodal_force_preserved);
  CHECK_FALSE(result.volume_balance_applied);
}

TEST_CASE("Leakoff coupling parser accepts supported modes") {
  CHECK(lss::lot::parse_leakoff_coupling_mode("volume_balance") ==
        lss::lot::LeakoffCouplingMode::VolumeBalance);
  CHECK(lss::lot::parse_leakoff_coupling_mode("legacy_nodal_force") ==
        lss::lot::LeakoffCouplingMode::LegacyNodalForce);
  CHECK(lss::lot::to_string(lss::lot::LeakoffCouplingMode::VolumeBalance) ==
        "volume_balance");
}

TEST_CASE("Leakoff coupling parser rejects invalid mode") {
  CHECK_THROWS_AS(lss::lot::parse_leakoff_coupling_mode("force_and_volume"),
                  std::invalid_argument);
}

TEST_CASE("Leakoff coupling rejects non-finite inputs") {
  CHECK_THROWS_AS(
      lss::lot::apply_leakoff_coupling(
          lss::lot::LeakoffCouplingMode::VolumeBalance,
          {std::numeric_limits<double>::quiet_NaN(), 0.0}),
      std::invalid_argument);
}

TEST_CASE("Leakoff coupling can reduce pressure-driving volume") {
  const auto without_leakoff = lss::lot::apply_leakoff_coupling(
      lss::lot::LeakoffCouplingMode::VolumeBalance, {10.0, 0.0});
  const auto with_leakoff = lss::lot::apply_leakoff_coupling(
      lss::lot::LeakoffCouplingMode::VolumeBalance, {10.0, -3.0});

  CHECK(with_leakoff.coupled_dV_m3 < without_leakoff.coupled_dV_m3);
}
