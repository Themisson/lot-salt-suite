#include <cstddef>
#include <stdexcept>

#include <catch2/catch_test_macros.hpp>

#include "coupling/LotSaltCouplingStep.hpp"
#include "io/CaseParser.hpp"
#include "lot/PknRunner.hpp"
#include "salt/SaltCreepInterface.hpp"
#include "salt/SaltCreepTypes.hpp"

namespace {

constexpr const char* kPknMinimalCasePath = "cases/validation/lot_pkn_minimal.yaml";

class SpySaltCreepInterface final : public lss::salt::SaltCreepInterface {
 public:
  [[nodiscard]] bool is_available() const override { return true; }

  [[nodiscard]] lss::salt::SaltCreepResponse evaluate_wall_response(
      const lss::salt::SaltCreepQuery& query) const override {
    (void)query;
    ++call_count_;
    return {};
  }

  [[nodiscard]] int call_count() const { return call_count_; }

 private:
  mutable int call_count_ = 0;
};

}  // namespace

// ---------------------------------------------------------------------------
// Test 1 — central proof: salt interface is actually called from coupling/
// ---------------------------------------------------------------------------
TEST_CASE("evaluate_lot_salt_step calls salt interface exactly once") {
  const auto data = lss::io::parse_yaml(kPknMinimalCasePath);
  const auto pkn_run = lss::lot::run_pkn_case(data);
  REQUIRE_FALSE(pkn_run.result.time_series_s.empty());

  SpySaltCreepInterface spy;
  const lss::coupling::LotSaltCouplingConfig config;

  (void)lss::coupling::evaluate_lot_salt_step(pkn_run.result, 0, config, spy);

  CHECK(spy.call_count() == 1);
}

// ---------------------------------------------------------------------------
// Test 2 — multiple steps accumulate call_count
// ---------------------------------------------------------------------------
TEST_CASE("evaluate_lot_salt_step accumulates call_count across steps") {
  const auto data = lss::io::parse_yaml(kPknMinimalCasePath);
  const auto pkn_run = lss::lot::run_pkn_case(data);
  REQUIRE(pkn_run.result.time_series_s.size() >= 3);

  SpySaltCreepInterface spy;
  const lss::coupling::LotSaltCouplingConfig config;

  (void)lss::coupling::evaluate_lot_salt_step(pkn_run.result, 0, config, spy);
  (void)lss::coupling::evaluate_lot_salt_step(pkn_run.result, 1, config, spy);
  (void)lss::coupling::evaluate_lot_salt_step(pkn_run.result, 2, config, spy);

  CHECK(spy.call_count() == 3);
}

// ---------------------------------------------------------------------------
// Test 3 — query is populated correctly from PknResult
// ---------------------------------------------------------------------------
TEST_CASE("evaluate_lot_salt_step populates query from PknResult time series") {
  const auto data = lss::io::parse_yaml(kPknMinimalCasePath);
  const auto pkn_run = lss::lot::run_pkn_case(data);
  REQUIRE_FALSE(pkn_run.result.time_series_s.empty());

  SpySaltCreepInterface spy;
  lss::coupling::LotSaltCouplingConfig config;
  config.radial_position_m = 0.2;
  config.temperature_K = 400.0;

  constexpr std::size_t kStep = 0;
  const auto step_result =
      lss::coupling::evaluate_lot_salt_step(pkn_run.result, kStep, config, spy);

  CHECK(step_result.query.time_s ==
        pkn_run.result.time_series_s[kStep]);
  CHECK(step_result.query.wall_pressure_Pa ==
        pkn_run.result.net_pressure_series_Pa[kStep]);
  CHECK(step_result.query.temperature_K == config.temperature_K);
  CHECK(step_result.query.radial_position_m == config.radial_position_m);
}

// ---------------------------------------------------------------------------
// Test 4 — out-of-range step_index throws
// ---------------------------------------------------------------------------
TEST_CASE("evaluate_lot_salt_step throws out_of_range for invalid step_index") {
  const auto data = lss::io::parse_yaml(kPknMinimalCasePath);
  const auto pkn_run = lss::lot::run_pkn_case(data);
  REQUIRE_FALSE(pkn_run.result.time_series_s.empty());

  SpySaltCreepInterface spy;
  const lss::coupling::LotSaltCouplingConfig config;

  const std::size_t bad_index = pkn_run.result.time_series_s.size();
  CHECK_THROWS_AS(
      lss::coupling::evaluate_lot_salt_step(pkn_run.result, bad_index, config, spy),
      std::out_of_range);

  // spy was never reached — no call was made
  CHECK(spy.call_count() == 0);
}

// ---------------------------------------------------------------------------
// Test 5 — NullSaltCreepInterface: no crash, neutral response per contract
// ---------------------------------------------------------------------------
TEST_CASE("evaluate_lot_salt_step with NullSaltCreepInterface returns neutral response") {
  const auto data = lss::io::parse_yaml(kPknMinimalCasePath);
  const auto pkn_run = lss::lot::run_pkn_case(data);
  REQUIRE_FALSE(pkn_run.result.time_series_s.empty());

  lss::salt::NullSaltCreepInterface null_salt;
  const lss::coupling::LotSaltCouplingConfig config;

  const auto step_result =
      lss::coupling::evaluate_lot_salt_step(pkn_run.result, 0, config, null_salt);

  // NullSaltCreepInterface contract: valid=true, all fields zero
  CHECK(step_result.response.valid == true);
  CHECK(step_result.response.radial_displacement_m == 0.0);
  CHECK(step_result.response.radial_closure_m == 0.0);
  CHECK(step_result.response.radial_strain == 0.0);
  CHECK(step_result.response.effective_closure_pressure_Pa == 0.0);
}

// ---------------------------------------------------------------------------
// Test 6 — PknResult is not modified by the feedforward coupling call
// ---------------------------------------------------------------------------
TEST_CASE("evaluate_lot_salt_step does not modify PknResult") {
  const auto data = lss::io::parse_yaml(kPknMinimalCasePath);
  const auto pkn_run = lss::lot::run_pkn_case(data);
  REQUIRE_FALSE(pkn_run.result.time_series_s.empty());

  // Snapshot key fields before calling coupling
  const auto snapshot_time = pkn_run.result.time_series_s;
  const auto snapshot_pressure = pkn_run.result.net_pressure_series_Pa;
  const auto snapshot_length = pkn_run.result.fracture_length_series_m;
  const double snapshot_final_length = pkn_run.result.length_m;

  SpySaltCreepInterface spy;
  const lss::coupling::LotSaltCouplingConfig config;

  (void)lss::coupling::evaluate_lot_salt_step(pkn_run.result, 0, config, spy);

  CHECK(spy.call_count() == 1);
  CHECK(pkn_run.result.time_series_s == snapshot_time);
  CHECK(pkn_run.result.net_pressure_series_Pa == snapshot_pressure);
  CHECK(pkn_run.result.fracture_length_series_m == snapshot_length);
  CHECK(pkn_run.result.length_m == snapshot_final_length);
}
