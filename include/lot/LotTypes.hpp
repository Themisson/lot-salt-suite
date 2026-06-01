#pragma once

#include <string_view>

namespace lss::lot {

enum class FractureGeometry { Circular, Elliptical, PennyShaped, Pkn };
enum class LeakoffModel { None, ConstantRate, Carter, SyntheticConstant };
enum class BreakdownMethod { PressureThreshold, DerivativeDrop };

constexpr std::string_view to_string(FractureGeometry geometry) {
  switch (geometry) {
    case FractureGeometry::Circular:
      return "circular";
    case FractureGeometry::Elliptical:
      return "elliptical";
    case FractureGeometry::PennyShaped:
      return "penny_shaped";
    case FractureGeometry::Pkn:
      return "pkn";
  }
  return "unknown";
}

constexpr std::string_view to_string(LeakoffModel model) {
  switch (model) {
    case LeakoffModel::None:
      return "none";
    case LeakoffModel::ConstantRate:
      return "constant_rate";
    case LeakoffModel::Carter:
      return "carter";
    case LeakoffModel::SyntheticConstant:
      return "synthetic_constant";
  }
  return "unknown";
}

constexpr std::string_view to_string(BreakdownMethod method) {
  switch (method) {
    case BreakdownMethod::PressureThreshold:
      return "pressure_threshold";
    case BreakdownMethod::DerivativeDrop:
      return "derivative_drop";
  }
  return "unknown";
}

}  // namespace lss::lot
