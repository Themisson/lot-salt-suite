#pragma once

#include <string>

namespace lss::lot {

enum class FractureModelKind {
  Pkn,
  PennyShaped,
};

enum class FractureModelSelectionSource {
  Defaulted,
  Explicit,
};

struct FractureModelSelectionInput {
  bool has_fracture_model_field = false;
  std::string fracture_model_value;
};

struct FractureModelSelectionResult {
  FractureModelKind kind = FractureModelKind::Pkn;
  FractureModelSelectionSource source =
      FractureModelSelectionSource::Defaulted;
  std::string canonical_name = "PKN";
  std::string route = "lot-pkn";
  bool diagnostic_only = false;
  bool physically_validated = false;
  bool legacy_equivalent = false;
  bool runtime_supported_now = true;
  bool requires_fracture_initiation_gate = true;
};

[[nodiscard]] FractureModelSelectionResult select_fracture_model(
    const FractureModelSelectionInput& input);

[[nodiscard]] std::string to_string(FractureModelKind kind);

}  // namespace lss::lot
