#pragma once

#include <cmath>
#include <stdexcept>
#include <string>

namespace units {

inline constexpr double kKgM3PerPpg = 119.826;
inline constexpr double kMetersPerInch = 0.0254;
inline constexpr double kPaPerPsi = 6894.757;
inline constexpr double kPaPerBar = 100000.0;
inline constexpr double kPaSPerCp = 0.001;
inline constexpr double kKelvinOffset = 273.15;
inline constexpr double kNewtonMeterPerLbfFoot = 14.5939;
inline constexpr double kStandardGravity = 9.80665;

constexpr double ppg_to_kg_m3(double ppg) {
  return ppg * kKgM3PerPpg;
}

constexpr double kg_m3_to_ppg(double kg_m3) {
  return kg_m3 / kKgM3PerPpg;
}

constexpr double in_to_m(double inches) {
  return inches * kMetersPerInch;
}

constexpr double m_to_in(double meters) {
  return meters / kMetersPerInch;
}

constexpr double psi_to_Pa(double psi) {
  return psi * kPaPerPsi;
}

constexpr double Pa_to_psi(double pascal) {
  return pascal / kPaPerPsi;
}

constexpr double bar_to_Pa(double bar) {
  return bar * kPaPerBar;
}

constexpr double Pa_to_bar(double pascal) {
  return pascal / kPaPerBar;
}

constexpr double cP_to_Pa_s(double cP) {
  return cP * kPaSPerCp;
}

constexpr double Pa_s_to_cP(double Pa_s) {
  return Pa_s / kPaSPerCp;
}

constexpr double degC_to_K(double celsius) {
  return celsius + kKelvinOffset;
}

constexpr double K_to_degC(double kelvin) {
  return kelvin - kKelvinOffset;
}

constexpr double degF_to_degC(double fahrenheit) {
  return (fahrenheit - 32.0) * 5.0 / 9.0;
}

constexpr double degC_to_degF(double celsius) {
  return celsius * 9.0 / 5.0 + 32.0;
}

constexpr double lbf_ft_to_N_m(double lbf_ft) {
  return lbf_ft * kNewtonMeterPerLbfFoot;
}

constexpr double ppg_hydrostatic_Pa_per_m(double ppg,
                                          double g = kStandardGravity) {
  return ppg_to_kg_m3(ppg) * g;
}

inline void require_non_negative_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("units: " + field + " must be finite");
  }
  if (value < 0.0) {
    throw std::invalid_argument("units: " + field + " must be non-negative");
  }
}

inline void require_positive_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("units: " + field + " must be finite");
  }
  if (value <= 0.0) {
    throw std::invalid_argument("units: " + field + " must be positive");
  }
}

inline double hydrostatic_pressure_Pa(double density_kg_m3, double depth_m,
                                      double g = kStandardGravity) {
  require_non_negative_finite(density_kg_m3, "density_kg_m3");
  require_non_negative_finite(depth_m, "depth_m");
  require_positive_finite(g, "g");
  return density_kg_m3 * g * depth_m;
}

inline double ppg_hydrostatic_pressure_Pa(double ppg, double depth_m,
                                          double g = kStandardGravity) {
  require_non_negative_finite(ppg, "ppg");
  require_non_negative_finite(depth_m, "depth_m");
  require_positive_finite(g, "g");
  return ppg_hydrostatic_Pa_per_m(ppg, g) * depth_m;
}

inline double surface_plus_hydrostatic_pressure_Pa(
    double surface_pressure_Pa, double density_kg_m3, double depth_m,
    double g = kStandardGravity) {
  require_non_negative_finite(surface_pressure_Pa, "surface_pressure_Pa");
  return surface_pressure_Pa +
         hydrostatic_pressure_Pa(density_kg_m3, depth_m, g);
}

}  // namespace units
