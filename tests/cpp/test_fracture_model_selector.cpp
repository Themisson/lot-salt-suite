#include <stdexcept>
#include <string>

#include <catch2/catch_test_macros.hpp>

#include "lot/FractureModelSelector.hpp"

namespace {

lss::lot::FractureModelSelectionResult select_explicit(
    const std::string& value) {
  lss::lot::FractureModelSelectionInput input;
  input.has_fracture_model_field = true;
  input.fracture_model_value = value;
  return lss::lot::select_fracture_model(input);
}

void require_invalid_with_message(const std::string& value,
                                  const std::string& expected_message) {
  lss::lot::FractureModelSelectionInput input;
  input.has_fracture_model_field = true;
  input.fracture_model_value = value;

  try {
    (void)lss::lot::select_fracture_model(input);
    FAIL("Expected invalid_argument");
  } catch (const std::invalid_argument& error) {
    CHECK(std::string(error.what()).find(expected_message) !=
          std::string::npos);
  }
}

}  // namespace

TEST_CASE("FractureModelSelector defaults missing field to PKN") {
  const auto result = lss::lot::select_fracture_model({});

  CHECK(result.kind == lss::lot::FractureModelKind::Pkn);
  CHECK(result.canonical_name == "PKN");
  CHECK(result.route == "lot-pkn");
}

TEST_CASE("FractureModelSelector marks missing field source as Defaulted") {
  const auto result = lss::lot::select_fracture_model({});

  CHECK(result.source == lss::lot::FractureModelSelectionSource::Defaulted);
}

TEST_CASE("FractureModelSelector accepts explicit PKN") {
  const auto result = select_explicit("PKN");

  CHECK(result.kind == lss::lot::FractureModelKind::Pkn);
  CHECK(result.source == lss::lot::FractureModelSelectionSource::Explicit);
  CHECK(result.canonical_name == "PKN");
}

TEST_CASE("FractureModelSelector normalizes pkn to PKN") {
  CHECK(select_explicit("pkn").canonical_name == "PKN");
}

TEST_CASE("FractureModelSelector normalizes lot-pkn to PKN") {
  CHECK(select_explicit("lot-pkn").canonical_name == "PKN");
}

TEST_CASE("FractureModelSelector normalizes lot_pkn to PKN") {
  CHECK(select_explicit("lot_pkn").canonical_name == "PKN");
}

TEST_CASE("FractureModelSelector accepts explicit PENNY_SHAPED") {
  const auto result = select_explicit("PENNY_SHAPED");

  CHECK(result.kind == lss::lot::FractureModelKind::PennyShaped);
  CHECK(result.source == lss::lot::FractureModelSelectionSource::Explicit);
  CHECK(result.canonical_name == "PENNY_SHAPED");
}

TEST_CASE("FractureModelSelector normalizes penny_shaped to PENNY_SHAPED") {
  CHECK(select_explicit("penny_shaped").canonical_name == "PENNY_SHAPED");
}

TEST_CASE("FractureModelSelector normalizes penny-shaped to PENNY_SHAPED") {
  CHECK(select_explicit("penny-shaped").canonical_name == "PENNY_SHAPED");
}

TEST_CASE("FractureModelSelector normalizes penny to PENNY_SHAPED") {
  CHECK(select_explicit("penny").canonical_name == "PENNY_SHAPED");
}

TEST_CASE("FractureModelSelector rejects explicit empty value") {
  require_invalid_with_message(
      "", "EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED");
}

TEST_CASE("FractureModelSelector rejects KGD") {
  require_invalid_with_message("KGD", "UNSUPPORTED_FRACTURE_MODEL");
}

TEST_CASE("FractureModelSelector rejects RADIAL") {
  require_invalid_with_message("RADIAL", "UNSUPPORTED_FRACTURE_MODEL");
}

TEST_CASE("FractureModelSelector rejects UNKNOWN") {
  require_invalid_with_message("UNKNOWN", "UNSUPPORTED_FRACTURE_MODEL");
}

TEST_CASE("FractureModelSelector marks PENNY_SHAPED diagnostic only") {
  CHECK(select_explicit("PENNY_SHAPED").diagnostic_only);
}

TEST_CASE("FractureModelSelector marks PENNY_SHAPED not physically validated") {
  CHECK_FALSE(select_explicit("PENNY_SHAPED").physically_validated);
}

TEST_CASE("FractureModelSelector marks PENNY_SHAPED not legacy equivalent") {
  CHECK_FALSE(select_explicit("PENNY_SHAPED").legacy_equivalent);
}

TEST_CASE("FractureModelSelector marks PENNY_SHAPED not runtime supported now") {
  CHECK_FALSE(select_explicit("PENNY_SHAPED").runtime_supported_now);
}

TEST_CASE("FractureModelSelector requires initiation gate for both models") {
  CHECK(lss::lot::select_fracture_model({}).requires_fracture_initiation_gate);
  CHECK(select_explicit("PENNY_SHAPED").requires_fracture_initiation_gate);
}

TEST_CASE("FractureModelSelector to_string returns canonical names") {
  CHECK(lss::lot::to_string(lss::lot::FractureModelKind::Pkn) == "PKN");
  CHECK(lss::lot::to_string(lss::lot::FractureModelKind::PennyShaped) ==
        "PENNY_SHAPED");
}
