#include <algorithm>
#include <string>

#include <catch2/catch_test_macros.hpp>

#include "lot/Buz29PennyDiagnosticRunner.hpp"

namespace {

lss::lot::Buz29PennyDiagnosticRunnerInput complete_input() {
  lss::lot::Buz29PennyDiagnosticRunnerInput input;
  input.case_id = "buz29_penny_synthetic_complete";
  input.fracture_model = "PENNY_SHAPED";
  input.young_modulus_Pa = 5.71e6;
  input.poisson_ratio = 0.36;
  input.viscosity_Pa_min = 180.0;
  input.flow_rate_m3_min = 0.05;
  input.elapsed_since_opening_min = 1.25;
  input.wellbore_pressure_Pa = 6.7e7;
  input.sigma_theta_compression_positive_Pa = 6.6e7;
  input.volume_multiplier = 10.0;
  input.adapter_inputs_complete = true;
  return input;
}

bool has_reason(
    const lss::lot::Buz29PennyDiagnosticRunnerResult& result,
    const std::string& reason) {
  return std::find(result.blocking_reasons.begin(),
                   result.blocking_reasons.end(),
                   reason) != result.blocking_reasons.end();
}

}  // namespace

TEST_CASE("Buz29PennyDiagnosticRunner completes synthetic diagnostic inputs") {
  const auto result =
      lss::lot::run_buz29_penny_diagnostic(complete_input());

  CHECK(result.run_status == "BUZ29_PENNY_DIAGNOSTIC_RUN_COMPLETED");
  CHECK(result.execution_completed);
  CHECK(result.diagnostic_only);
  CHECK_FALSE(result.physically_validated);
  CHECK_FALSE(result.legacy_equivalent);
  CHECK_FALSE(result.runtime_dispatch_enabled);
  CHECK_FALSE(result.penny_shaped_runtime_enabled);
  CHECK_FALSE(result.pkn_behavior_changed);
  CHECK_FALSE(result.physical_validation_claimed);
  CHECK_FALSE(result.legacy_equivalence_claimed);
  CHECK(result.diagnostic_json.find("buz29_penny_synthetic_complete") !=
        std::string::npos);
  CHECK(result.diagnostic_csv.find("Buz29PennyDiagnosticRunner") !=
        std::string::npos);
}

TEST_CASE("Buz29PennyDiagnosticRunner blocks partial BUZ29 inputs") {
  auto input = complete_input();
  input.adapter_inputs_complete = false;
  input.missing_adapter_fields = {"wellbore_pressure_Pa",
                                  "sigma_theta_compression_positive_Pa"};

  const auto result = lss::lot::run_buz29_penny_diagnostic(input);

  CHECK(result.run_status ==
        "BUZ29_PENNY_DIAGNOSTIC_RUN_BLOCKED_BY_PARTIAL_INPUTS");
  CHECK_FALSE(result.execution_completed);
  CHECK(has_reason(result, "BUZ29_PENNY_ADAPTER_INPUTS_PARTIAL"));
  CHECK(has_reason(result, "MISSING_FIELD:wellbore_pressure_Pa"));
}

TEST_CASE("Buz29PennyDiagnosticRunner rejects physically validated flag") {
  auto input = complete_input();
  input.physically_validated = true;

  const auto result = lss::lot::run_buz29_penny_diagnostic(input);

  CHECK(result.run_status ==
        "BUZ29_PENNY_DIAGNOSTIC_RUN_REJECTED_INVALID_FLAGS");
  CHECK_FALSE(result.execution_completed);
  CHECK(has_reason(result, "PHYSICALLY_VALIDATED_FORBIDDEN"));
}

TEST_CASE("Buz29PennyDiagnosticRunner rejects legacy equivalence flag") {
  auto input = complete_input();
  input.legacy_equivalent = true;

  const auto result = lss::lot::run_buz29_penny_diagnostic(input);

  CHECK(result.run_status ==
        "BUZ29_PENNY_DIAGNOSTIC_RUN_REJECTED_INVALID_FLAGS");
  CHECK_FALSE(result.execution_completed);
  CHECK(has_reason(result, "LEGACY_EQUIVALENT_FORBIDDEN"));
}

TEST_CASE("Buz29PennyDiagnosticRunner rejects runtime dispatch") {
  auto input = complete_input();
  input.runtime_dispatch_enabled = true;

  const auto result = lss::lot::run_buz29_penny_diagnostic(input);

  CHECK(result.run_status ==
        "BUZ29_PENNY_DIAGNOSTIC_RUN_REJECTED_INVALID_FLAGS");
  CHECK_FALSE(result.execution_completed);
  CHECK(has_reason(result, "RUNTIME_DISPATCH_FORBIDDEN"));
}

TEST_CASE("Buz29PennyDiagnosticRunner rejects non PennyShaped model") {
  auto input = complete_input();
  input.fracture_model = "PKN";

  const auto result = lss::lot::run_buz29_penny_diagnostic(input);

  CHECK(result.run_status ==
        "BUZ29_PENNY_DIAGNOSTIC_RUN_REJECTED_UNSUPPORTED_MODEL");
  CHECK_FALSE(result.execution_completed);
  CHECK(has_reason(result,
                   "ONLY_PENNY_SHAPED_DIAGNOSTIC_MODEL_SUPPORTED"));
}

TEST_CASE("Buz29PennyDiagnosticRunner rejects non diagnostic-only use") {
  auto input = complete_input();
  input.diagnostic_only = false;

  const auto result = lss::lot::run_buz29_penny_diagnostic(input);

  CHECK(result.run_status ==
        "BUZ29_PENNY_DIAGNOSTIC_RUN_REJECTED_INVALID_FLAGS");
  CHECK_FALSE(result.execution_completed);
  CHECK(has_reason(result, "DIAGNOSTIC_ONLY_REQUIRED"));
}

TEST_CASE("Buz29PennyDiagnosticRunner exposes required caveats") {
  const auto caveats =
      lss::lot::required_buz29_penny_diagnostic_runner_caveats();

  CHECK(std::find(caveats.begin(), caveats.end(), "DIAGNOSTIC_ONLY") !=
        caveats.end());
  CHECK(std::find(caveats.begin(), caveats.end(),
                  "BUZ29_REAL_INPUTS_NOT_IMPROVISED") != caveats.end());
}
