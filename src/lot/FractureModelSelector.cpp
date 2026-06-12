#include "lot/FractureModelSelector.hpp"

#include <algorithm>
#include <cctype>
#include <stdexcept>
#include <string>

namespace lss::lot {
namespace {

[[nodiscard]] std::string trim(const std::string& value) {
  auto first = value.begin();
  while (first != value.end() &&
         std::isspace(static_cast<unsigned char>(*first)) != 0) {
    ++first;
  }

  auto last = value.end();
  while (last != first &&
         std::isspace(static_cast<unsigned char>(*(last - 1))) != 0) {
    --last;
  }

  return std::string(first, last);
}

[[nodiscard]] std::string uppercase(std::string value) {
  std::transform(value.begin(), value.end(), value.begin(), [](unsigned char c) {
    return static_cast<char>(std::toupper(c));
  });
  return value;
}

[[nodiscard]] std::string normalized_token(const std::string& value) {
  auto token = uppercase(trim(value));
  std::replace(token.begin(), token.end(), '-', '_');
  return token;
}

[[nodiscard]] bool is_pkn_alias(const std::string& token) {
  return token == "PKN" || token == "LOT_PKN";
}

[[nodiscard]] bool is_penny_shaped_alias(const std::string& token) {
  return token == "PENNY_SHAPED" || token == "PENNY";
}

[[nodiscard]] FractureModelSelectionResult pkn_result(
    FractureModelSelectionSource source) {
  FractureModelSelectionResult result;
  result.kind = FractureModelKind::Pkn;
  result.source = source;
  result.canonical_name = "PKN";
  result.route = "lot-pkn";
  result.diagnostic_only = false;
  result.physically_validated = false;
  result.legacy_equivalent = false;
  result.runtime_supported_now = true;
  result.requires_fracture_initiation_gate = true;
  return result;
}

[[nodiscard]] FractureModelSelectionResult penny_shaped_result() {
  FractureModelSelectionResult result;
  result.kind = FractureModelKind::PennyShaped;
  result.source = FractureModelSelectionSource::Explicit;
  result.canonical_name = "PENNY_SHAPED";
  result.route = "unified_lot_fracture_runtime";
  result.diagnostic_only = true;
  result.physically_validated = false;
  result.legacy_equivalent = false;
  result.runtime_supported_now = false;
  result.requires_fracture_initiation_gate = true;
  return result;
}

}  // namespace

FractureModelSelectionResult select_fracture_model(
    const FractureModelSelectionInput& input) {
  if (!input.has_fracture_model_field) {
    return pkn_result(FractureModelSelectionSource::Defaulted);
  }

  const auto token = normalized_token(input.fracture_model_value);
  if (token.empty()) {
    throw std::invalid_argument(
        "FractureModelSelector: "
        "EXPLICIT_EMPTY_FRACTURE_MODEL_NOT_ALLOWED");
  }

  if (is_pkn_alias(token)) {
    return pkn_result(FractureModelSelectionSource::Explicit);
  }

  if (is_penny_shaped_alias(token)) {
    return penny_shaped_result();
  }

  throw std::invalid_argument("FractureModelSelector: "
                              "UNSUPPORTED_FRACTURE_MODEL: " +
                              input.fracture_model_value);
}

std::string to_string(FractureModelKind kind) {
  switch (kind) {
    case FractureModelKind::Pkn:
      return "PKN";
    case FractureModelKind::PennyShaped:
      return "PENNY_SHAPED";
  }
  throw std::invalid_argument("FractureModelSelector: "
                              "UNSUPPORTED_FRACTURE_MODEL_KIND");
}

}  // namespace lss::lot
